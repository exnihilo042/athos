"""ATHOS Voice Server — couche HTTP pure. Toute la logique est dans core/."""
import sys, json, subprocess, threading, uuid, tempfile, shutil, os, atexit
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

import config
import athos_room
import session_kernel
import sync_manager
import task_queue
import memory_status
import session_compactor
import metacognition
import situational_decision
import athos_advantage
import transformation_stack
import local_capability
import capability_graph
import epistemic_guard
import external_sources
import model_profiles
import review_pipeline
import sse_parser
import truth_ledger
import engine_router
import failover_simulator
import room_responders
from auth import request_authorized
from memory_extractor import extract_and_save_async
from athos_memory import AthosMemory
from athos_router import AthosRouter
from athos_engine import AthosEngine
from observability import process_snapshot, stop_observed_pid, server_runtime
from capabilities import status_report
from self_improvement import plan_self_improvement
from attach_protocol import attach_engine, attach_prompt, context_for_attach, delegate as delegate_request, report as attach_report
from named_protocols import run_protocol

STATIC       = Path(__file__).parent
ACCESS_TOKEN = config.ATHOS_ACCESS_TOKEN
_ROOM_AUTORESPOND_LOCK = threading.Lock()
_ROOM_AUTORESPOND_ACTIVE: set[str] = set()
_ROOM_AUTOWORK_LOCK = threading.Lock()
_ROOM_AUTOWORK_ACTIVE: set[str] = set()
_ROOM_AUTOWORK_CURRENT: dict[str, str] = {}


def _room_runtime_state() -> dict:
    with _ROOM_AUTORESPOND_LOCK:
        autorespond_active = sorted(_ROOM_AUTORESPOND_ACTIVE)
    with _ROOM_AUTOWORK_LOCK:
        autowork_active = sorted(_ROOM_AUTOWORK_ACTIVE)
        current_work = dict(_ROOM_AUTOWORK_CURRENT)
    return {
        "auto_response": {
            "enabled": bool(getattr(config, "ATHOS_ROOM_AUTO_RESPOND", True)),
            "active_count": len(autorespond_active),
            "active_entries": autorespond_active,
            "engines": list(getattr(config, "ATHOS_ROOM_AUTO_RESPOND_ENGINES", ["claude", "codex"])),
            "timeout": int(getattr(config, "ATHOS_ROOM_AUTO_RESPOND_TIMEOUT", 60)),
            "coordination_rounds": int(getattr(config, "ATHOS_ROOM_AUTO_COORDINATION_ROUNDS", 0)),
        },
        "auto_work": {
            "enabled": bool(getattr(config, "ATHOS_ROOM_AUTO_WORK", True)),
            "active_count": len(autowork_active),
            "active_entries": autowork_active,
            "current": current_work,
            "timeout": int(getattr(config, "ATHOS_ROOM_AUTO_WORK_TIMEOUT", 180)),
            "review_enabled": bool(getattr(config, "ATHOS_ROOM_AUTO_WORK_REVIEW", True)),
        },
        "task_queue": task_queue.summary(),
        "responders": room_responders.responder_status(),
    }


def _dashboard_report(body: dict) -> dict:
    report_type = str(body.get("type") or "daily").lower()
    date = datetime.now().date().isoformat()
    session = session_kernel.status()
    queue = task_queue.summary()
    responders = room_responders.responder_status()
    try:
        from observability import recent_failover_events
        failovers = recent_failover_events(limit=6)
    except Exception:
        failovers = []
    sections = [
        {
            "title": "Session",
            "content": session.get("recent_summary") or "Aucune activité session récente.",
            "data": session,
        },
        {
            "title": "Task queue",
            "content": (
                f"{queue.get('active', 0)} tâche(s) active(s), "
                f"{queue.get('counts', {}).get('completed', 0)} terminée(s), "
                f"{queue.get('counts', {}).get('blocked', 0)} bloquée(s)."
            ),
            "data": queue,
        },
        {
            "title": "Responders",
            "content": " · ".join(
                f"{name}:{'ok' if info.get('available') else (info.get('last_problem') or {}).get('kind', 'off')}"
                for name, info in (responders.get("actors") or {}).items()
            ) or "Aucun responder déclaré.",
            "data": responders,
        },
        {
            "title": "Failover",
            "content": f"{len(failovers)} événement(s) failover récent(s).",
            "data": {"events": failovers},
        },
    ]
    return {
        "ok": True,
        "type": report_type,
        "date": date,
        "brief": f"Rapport {report_type} ATHOS — {session.get('events', 0)} événement(s), {queue.get('active', 0)} tâche(s) active(s).",
        "sections": sections,
    }


# ── Singletons partagés ───────────────────────────────────────────────────────
_mem    = AthosMemory()
_router = AthosRouter(_mem)


def _room_message_wants_coordination(content: str) -> bool:
    text = str(content or "").lower()
    cues = (
        "discute",
        "discuter",
        "coordonn",
        "symbiose",
        "ensemble",
        "entre vous",
        "continuez",
        "continuer",
        "travaillez",
        "attaquer",
    )
    return any(cue in text for cue in cues)


def _room_message_wants_work(content: str) -> bool:
    text = str(content or "").lower()
    if not text.strip():
        return False
    casual_only = (
        "vous êtes là",
        "vous etes là",
        "on peut attaquer",
        "test ",
        "présent",
        "status",
    )
    if any(cue in text for cue in casual_only):
        return False
    work_cues = (
        "finis",
        "finissez",
        "termine",
        "terminez",
        "fais",
        "faites",
        "corrige",
        "corriges",
        "code",
        "implémente",
        "implemente",
        "modifie",
        "modifies",
        "ajoute",
        "ajoutes",
        "supprime",
        "supprimes",
        "debug",
        "vérifie",
        "vérifiez",
        "verifie",
        "verifiez",
        "teste",
        "tests",
        "mets à jour",
        "met à jour",
        "update",
        "commit",
        "push",
        "travaille",
        "travaillez",
        "continue",
        "continues",
        "lance",
        "relance",
        "installe",
        "installes",
    )
    return any(cue in text for cue in work_cues)


def _task_thread_text(task_id: str, limit: int = 30) -> str:
    rows = athos_room.get_thread(task_id=task_id, limit=limit)
    if not rows:
        return "[fil de tâche vide]"
    lines = []
    for row in rows:
        actor = str(row.get("actor", "?")).upper()
        msg_type = row.get("type", "message")
        content = str(row.get("content", "")).strip()
        status = row.get("status") or ""
        tag = f"[{msg_type}{':' + status if status else ''}]"
        lines.append(f"{actor}{tag}: {content[:1200]}")
    return "\n".join(lines)


def _local_room_work_result(content: str, task_id: str) -> str | None:
    """Handle Room health/stability checks locally instead of spending engines."""
    text = str(content or "").lower()
    if "room" not in text:
        return None
    if not any(cue in text for cue in ("boucle", "relance", "stable", "fonctionne", "coordonne", "coordonnée")):
        return None

    thread = athos_room.get_thread(task_id=task_id, limit=120)
    actors = {}
    sources = {}
    for row in thread:
        actor = row.get("actor", "?")
        actors[actor] = actors.get(actor, 0) + 1
        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        source = meta.get("source")
        if source:
            sources[source] = sources.get(source, 0) + 1
    work_starts = sum(
        1
        for row in thread
        if row.get("actor") == "athos"
        and row.get("type") == "action"
        and "orchestration ATHOS lancée" in str(row.get("content", ""))
    )
    responder_starts = sum(
        1
        for row in thread
        if row.get("type") == "action"
        and "prépare une réponse Room" in str(row.get("content", ""))
    )
    loops_detected = work_starts > 1
    return (
        "Vérification Room locale: "
        f"{len(thread)} message(s) dans cette tâche; "
        f"acteurs={actors}; sources={sources}; "
        f"orchestrations={work_starts}; responders={responder_starts}; "
        f"boucle={'détectée' if loops_detected else 'non détectée'}. "
        "Aucune relance automatique supplémentaire n'a été déclenchée par ce check local."
    )


def _schedule_room_athos_work(entry: dict) -> dict:
    """Naturally route work-like Room messages into a coordinated work cycle.

    Clément writes normally in Room. If it is work, ATHOS starts one visible
    bounded orchestration: Claude/Codex plan, ATHOS executes through the engine,
    Claude/Codex review. Permission prompts are never hidden in background mode.
    """
    if not getattr(config, "ATHOS_ROOM_AUTO_WORK", True):
        return {"scheduled": False, "reason": "disabled"}
    if entry.get("actor") != "clement" or entry.get("type") != "message":
        return {"scheduled": False, "reason": "not_clement_message"}
    meta = entry.get("meta") if isinstance(entry.get("meta"), dict) else {}
    if meta.get("auto_work") is False or str(meta.get("auto_work", "")).lower() == "false":
        return {"scheduled": False, "reason": "explicitly_disabled"}
    if meta.get("replayed_from"):
        return {"scheduled": False, "reason": "replay_no_autowork"}

    content = entry.get("content", "")
    if not _room_message_wants_work(content):
        return {"scheduled": False, "reason": "not_work_intent"}

    entry_id = entry.get("id") or ""
    if not entry_id:
        return {"scheduled": False, "reason": "missing_entry_id"}

    with _ROOM_AUTOWORK_LOCK:
        if entry_id in _ROOM_AUTOWORK_ACTIVE:
            return {"scheduled": False, "reason": "already_running"}
        current = _ROOM_AUTOWORK_CURRENT.get("task_id")
        if current:
            return {"scheduled": False, "reason": "another_work_running", "task_id": current}
        _ROOM_AUTOWORK_ACTIVE.add(entry_id)
        _ROOM_AUTOWORK_CURRENT["task_id"] = entry.get("task_id") or f"room-work-{entry_id}"

    task_id = entry.get("task_id") or f"room-work-{entry_id}"
    timeout = int(getattr(config, "ATHOS_ROOM_AUTO_WORK_TIMEOUT", 180))
    responder_timeout = int(getattr(config, "ATHOS_ROOM_AUTO_WORK_RESPONDER_TIMEOUT", 60))
    toolbus_stats = {"count": 0}
    task_queue.create(
        f"Room objective: {str(content).strip()[:120]}",
        content=content,
        task_id=task_id,
        source="room",
        kind="room_auto_work",
        status="queued",
        meta={"entry_id": entry_id, "actor": entry.get("actor")},
    )

    def room_sse(obj):
        try:
            if isinstance(obj, dict):
                if obj.get("thinking"):
                    thinking = obj.get("thinking") or {}
                    athos_room.add(
                        actor="athos",
                        content=f"{thinking.get('kind', 'thinking')}: {thinking.get('text', '')}",
                        msg_type="action",
                        task_id=task_id,
                        status="running",
                        meta={"source": "room_auto_work", "event": "thinking"},
                    )
                elif obj.get("toolbus"):
                    # Do not dump terminal streams into the Room. They can
                    # contain full prompts, skill files and huge noisy logs.
                    # The visible launchd log remains the terminal source of
                    # truth; the Room gets a compact summary at the end.
                    toolbus_stats["count"] += 1
                elif obj.get("action"):
                    athos_room.add(
                        actor="athos",
                        content=f"{obj.get('action')}: {obj.get('label', '')} {obj.get('result', '')}".strip(),
                        msg_type="action",
                        task_id=task_id,
                        status="running",
                        meta={"source": "room_auto_work", "event": "action"},
                    )
                elif obj.get("permission_required"):
                    athos_room.add(
                        actor="athos",
                        content=f"permission requise: {obj.get('tool')} {obj.get('inputs', {})}",
                        msg_type="error",
                        task_id=task_id,
                        status="blocked",
                        meta={"source": "room_auto_work", "event": "permission_required"},
                    )
            return True
        except Exception:
            return False

    def permission_checker(tool_name: str, inputs: dict) -> bool:
        room_sse({"permission_required": True, "tool": tool_name, "inputs": inputs})
        return False

    def worker():
        try:
            task_queue.start(task_id=task_id)
            athos_room.add(
                actor="athos",
                content="orchestration ATHOS lancée depuis la Room",
                msg_type="action",
                task_id=task_id,
                status="running",
                meta={"source": "room_auto_work", "entry_id": entry_id},
            )
            print(f"[ATHOS Room work] start entry={entry_id} task={task_id}", flush=True)

            plan_prompt = (
                "Phase PLAN. Clément vient de donner un objectif dans ATHOS Room. "
                "Claude et Codex doivent se coordonner brièvement: comprendre l'objectif, "
                "indiquer les responsabilités, les risques, les fichiers/zones probables, "
                "et le critère de résultat final. Ne modifiez aucun fichier dans cette phase.\n\n"
                f"OBJECTIF:\n{content}"
            )
            plan_result = room_responders.respond(
                plan_prompt,
                task_id=task_id,
                engines=getattr(config, "ATHOS_ROOM_AUTO_RESPOND_ENGINES", ["claude", "codex"]),
                timeout=responder_timeout,
                force=True,
            )

            reply_box: dict[str, str] = {}
            local_reply = _local_room_work_result(content, task_id)
            local_handled = bool(local_reply)
            if local_reply:
                reply_box["reply"] = local_reply
            else:
                athos = AthosEngine(_mem, _router, room_sse, lambda: permission_checker)
                action_prompt = (
                    "Tu es ATHOS en mode exécution Room. Tu dois accomplir l'objectif, pas répondre par un plan.\n"
                    "Règles non négociables:\n"
                    "- Si l'objectif concerne ATHOS, tu peux modifier uniquement /Users/clem/Sites/athos.\n"
                    "- Lis le fil, applique le correctif minimal, lance les tests pertinents.\n"
                    "- N'utilise pas de commande destructive, pas de force push, pas de mutation hors ATHOS.\n"
                    "- Si une validation humaine est nécessaire, arrête-toi avec un blocage explicite.\n"
                    "- Conclus par: fichiers modifiés, tests exécutés, résultat final ou blocage vérifiable.\n"
                    "- Ne dis jamais seulement 'lance quand tu veux' si l'action est faisable maintenant.\n\n"
                    "CONTEXTE ROOM DE CETTE TÂCHE:\n"
                    f"{_task_thread_text(task_id)}\n\n"
                    f"OBJECTIF DE CLÉMENT:\n{content}"
                )

                def run_engine():
                    reply_box["reply"] = athos.respond(action_prompt)

                t = threading.Thread(target=run_engine, name=f"athos-room-work-engine-{entry_id}", daemon=True)
                t.start()
                t.join(timeout=timeout)
                if t.is_alive():
                    task_queue.block(task_id=task_id, reason=f"timeout {timeout}s")
                    athos_room.add(
                        actor="athos",
                        content=f"travail ATHOS stoppé: timeout {timeout}s",
                        msg_type="error",
                        task_id=task_id,
                        status="timeout",
                        meta={"source": "room_auto_work", "entry_id": entry_id},
                    )
                    return
            reply = (reply_box.get("reply") or "").strip()
            if reply:
                athos_room.add(
                    actor="athos",
                    content=reply,
                    msg_type="result",
                    task_id=task_id,
                    status="completed",
                    meta={"source": "room_auto_work", "entry_id": entry_id, "engine": _router.current},
                )
                extract_and_save_async(content, reply)
            if toolbus_stats["count"]:
                athos_room.add(
                    actor="athos",
                    content=f"terminal: {toolbus_stats['count']} événement(s) masqués pour garder la Room lisible; voir logs ATHOS si besoin.",
                    msg_type="action",
                    task_id=task_id,
                    status="completed",
                    meta={"source": "room_auto_work", "event": "toolbus_summary"},
                )
            plan_had_success = any(r.get("ok") for r in (plan_result or {}).get("results", []))
            if getattr(config, "ATHOS_ROOM_AUTO_WORK_REVIEW", True) and plan_had_success and not local_handled:
                review_prompt = (
                    "Phase REVIEW. Relisez le fil de cette tâche. "
                    "Dites chacun si l'objectif est terminé, incomplet ou bloqué. "
                    "Si incomplet, listez uniquement les prochaines actions concrètes. "
                    "Ne modifiez aucun fichier dans cette phase.\n\n"
                    f"FIL DE TÂCHE:\n{_task_thread_text(task_id)}"
                )
                room_responders.respond(
                    review_prompt,
                    task_id=task_id,
                    engines=getattr(config, "ATHOS_ROOM_AUTO_RESPOND_ENGINES", ["claude", "codex"]),
                    timeout=responder_timeout,
                    force=True,
                )
            athos_room.add(
                actor="athos",
                content="orchestration ATHOS terminée ou arrêtée proprement; voir les messages Claude/Codex/Athos ci-dessus.",
                msg_type="checkpoint",
                task_id=task_id,
                status="completed",
                meta={"source": "room_auto_work", "entry_id": entry_id},
            )
            task_queue.complete(task_id=task_id, result=reply or "orchestration completed")
            print(f"[ATHOS Room work] done entry={entry_id} task={task_id}", flush=True)
        except Exception as exc:
            task_queue.block(task_id=task_id, reason=str(exc))
            athos_room.add(
                actor="athos",
                content=f"travail ATHOS échoué: {exc}",
                msg_type="error",
                task_id=task_id,
                status="failed",
                meta={"source": "room_auto_work", "entry_id": entry_id},
            )
            print(f"[ATHOS Room work] error entry={entry_id}: {exc}", flush=True)
        finally:
            with _ROOM_AUTOWORK_LOCK:
                _ROOM_AUTOWORK_ACTIVE.discard(entry_id)
                if _ROOM_AUTOWORK_CURRENT.get("task_id") == task_id:
                    _ROOM_AUTOWORK_CURRENT.clear()

    threading.Thread(target=worker, name=f"athos-room-work-{entry_id}", daemon=True).start()
    return {"scheduled": True, "entry_id": entry_id, "task_id": task_id}


def _schedule_room_auto_response(entry: dict) -> dict:
    """Trigger Claude/Codex for new Clément Room messages.

    The work runs inside the existing ATHOS HUB process and prints lifecycle
    lines to the visible launchd log. It is bounded by responder timeouts and
    guarded by entry-id dedupe, so a refresh/replay cannot fan out replies.
    """
    if not getattr(config, "ATHOS_ROOM_AUTO_RESPOND", True):
        return {"scheduled": False, "reason": "disabled"}
    if entry.get("actor") != "clement" or entry.get("type") != "message":
        return {"scheduled": False, "reason": "not_clement_message"}
    meta = entry.get("meta") if isinstance(entry.get("meta"), dict) else {}
    if meta.get("auto_respond") is False or str(meta.get("auto_respond", "")).lower() == "false":
        return {"scheduled": False, "reason": "explicitly_disabled"}
    if meta.get("replayed_from"):
        return {"scheduled": False, "reason": "replay_no_autorespond"}

    entry_id = entry.get("id") or ""
    if not entry_id:
        return {"scheduled": False, "reason": "missing_entry_id"}

    with _ROOM_AUTORESPOND_LOCK:
        if entry_id in _ROOM_AUTORESPOND_ACTIVE:
            return {"scheduled": False, "reason": "already_running"}
        _ROOM_AUTORESPOND_ACTIVE.add(entry_id)

    engines = list(getattr(config, "ATHOS_ROOM_AUTO_RESPOND_ENGINES", ["claude", "codex"]) or ["claude", "codex"])
    timeout = int(getattr(config, "ATHOS_ROOM_AUTO_RESPOND_TIMEOUT", 60))
    coordination_rounds = max(0, int(getattr(config, "ATHOS_ROOM_AUTO_COORDINATION_ROUNDS", 0)))
    task_id = entry.get("task_id") or f"room-auto-{entry_id}"
    content = entry.get("content", "")

    def worker():
        try:
            print(f"[ATHOS Room auto] start entry={entry_id} task={task_id} engines={','.join(engines)}", flush=True)
            room_responders.respond(content, task_id=task_id, engines=engines, timeout=timeout)
            if coordination_rounds and _room_message_wants_coordination(content):
                for round_idx in range(1, coordination_rounds + 1):
                    coordination_prompt = (
                        f"Coordination autonome Room, tour {round_idx}/{coordination_rounds}. "
                        "Continuez l'échange entre moteurs sur le dernier objectif de Clément. "
                        "Soyez concrets, répartissez les responsabilités, signalez les blocages. "
                        "Ne lancez aucune action et ne modifiez aucun fichier depuis ce responder."
                    )
                    athos_room.add(
                        actor="athos",
                        content=f"coordination Room tour {round_idx}/{coordination_rounds}",
                        msg_type="action",
                        task_id=task_id,
                        status="running",
                        meta={"source": "room_auto_coordination", "entry_id": entry_id, "round": round_idx},
                    )
                    room_responders.respond(
                        coordination_prompt,
                        task_id=task_id,
                        engines=engines,
                        timeout=timeout,
                        force=True,
                    )
            print(f"[ATHOS Room auto] done entry={entry_id} task={task_id}", flush=True)
        except Exception as exc:
            athos_room.add(
                actor="athos",
                content=f"room auto respond failed: {exc}",
                msg_type="error",
                task_id=task_id,
                status="failed",
                meta={"source": "room_auto_respond", "entry_id": entry_id},
            )
            print(f"[ATHOS Room auto] error entry={entry_id}: {exc}", flush=True)
        finally:
            with _ROOM_AUTORESPOND_LOCK:
                _ROOM_AUTORESPOND_ACTIVE.discard(entry_id)

    threading.Thread(target=worker, name=f"athos-room-auto-{entry_id}", daemon=True).start()
    return {"scheduled": True, "entry_id": entry_id, "task_id": task_id, "engines": engines}


def _make_loop_llm():
    """Return a blocking llm_call for the autonomous loop — uses best available engine."""
    def _call(prompt: str) -> str:
        failures = []
        # Prefer Anthropic API if key present and budget allows
        if config.ANTHROPIC_KEY and config.paid_api_allowed("anthropic"):
            try:
                import anthropic as _ant
                client = _ant.Anthropic(api_key=config.ANTHROPIC_KEY)
                msg = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )
                return msg.content[0].text
            except Exception as exc:
                failures.append(f"anthropic_api:{exc}")
        # Fallback: claude CLI subprocess
        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--output-format", "text", "--dangerously-skip-permissions"],
                capture_output=True, text=True, timeout=120, cwd=str(config.ATHOS_PATH),
                stdin=subprocess.DEVNULL,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            failures.append(f"claude_code:{(result.stdout + result.stderr).strip()[:240]}")
        except Exception as exc:
            failures.append(f"claude_code:{exc}")
        # Fallback: ChatGPT Plus / Codex CLI subscription, no API spend.
        codex = engine_router.chatgpt_plus_path()
        if codex:
            try:
                result = subprocess.run(
                    [codex, "exec", "--dangerously-bypass-approvals-and-sandbox", prompt],
                    capture_output=True, text=True, timeout=180, cwd=str(config.ATHOS_PATH),
                    stdin=subprocess.DEVNULL,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
                failures.append(f"chatgpt_plus:{(result.stdout + result.stderr).strip()[:240]}")
            except Exception as exc:
                failures.append(f"chatgpt_plus:{exc}")
        session_kernel.record_action(
            "loop_llm_unavailable",
            "all providers failed",
            " | ".join(failures)[-1000:],
            engine="athos_kernel",
        )
        return "[loop_llm_unavailable] " + " | ".join(failures)[-500:]
    return _call

# ── Permission prompts (bloquants) ────────────────────────────────────────────
_permits:      dict[str, dict] = {}
_permits_lock: threading.Lock  = threading.Lock()

def _make_permission_checker(sse_fn):
    def check(tool_name: str, inputs: dict) -> bool:
        perm_id = uuid.uuid4().hex
        evt     = threading.Event()
        with _permits_lock:
            _permits[perm_id] = {"event": evt, "approved": False}
        sse_fn({"permission_required": True, "id": perm_id,
                "tool": tool_name, "inputs": {k: str(v)[:200] for k, v in inputs.items()}})
        evt.wait(timeout=60)
        with _permits_lock:
            result = _permits.pop(perm_id, {})
        return result.get("approved", False)
    return check


def _replay_offline_room_after_boot(delay_s: float = 1.5) -> None:
    """Replay offline Room messages once the HTTP server is accepting requests."""
    def _run():
        import time as _time
        _time.sleep(delay_s)
        script = Path(__file__).parent.parent / "scripts" / "replay_offline_room.sh"
        if not script.exists():
            return
        env = os.environ.copy()
        env.setdefault("ATHOS_URL", f"http://{config.ATHOS_BIND_HOST}:{config.ATHOS_PORT}")
        if config.ATHOS_ACCESS_TOKEN:
            env.setdefault("ATHOS_TOKEN", config.ATHOS_ACCESS_TOKEN)
        try:
            result = subprocess.run(
                ["bash", str(script)],
                cwd=str(config.ATHOS_PATH),
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
                stdin=subprocess.DEVNULL,
            )
            out = (result.stdout or result.stderr or "").strip()
            if out:
                print("[ATHOS Room replay]", out.replace("\n", " | "), flush=True)
        except Exception as exc:
            print(f"[ATHOS Room replay] skipped: {exc}", flush=True)

    threading.Thread(target=_run, name="athos-room-replay", daemon=True).start()

# ── Threading HTTP ────────────────────────────────────────────────────────────
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

# ── Handler ───────────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def cors(self):
        origin = self.headers.get("Origin", "")
        allowed = config.ATHOS_ALLOWED_ORIGINS
        if "*" in allowed:
            self.send_header("Access-Control-Allow-Origin", origin or "*")
        elif origin in allowed:
            self.send_header("Access-Control-Allow-Origin", origin)
        else:
            self.send_header("Access-Control-Allow-Origin", allowed[0] if allowed else "http://127.0.0.1:7474")
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(200); self.cors(); self.end_headers()

    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/api/session":
            if not self._auth(): return
            self._json(session_kernel.status()); return

        if p == "/api/attach_prompt":
            if not self._auth(): return
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown;charset=utf-8")
            self.cors(); self.end_headers()
            self.wfile.write(attach_prompt().encode("utf-8")); return

        routes = {"/": "index.html", "/index.html": "index.html",
                  "/manifest.json": "manifest.json",
                  "/icon-192.png": "icon-192.png", "/icon-512.png": "icon-512.png"}
        name = routes.get(p)
        f    = STATIC / name if name else None
        if not f or not f.exists():
            self.send_response(404); self.end_headers(); return
        mime = {".html": "text/html;charset=utf-8", ".json": "application/json;charset=utf-8", ".png": "image/png"}
        self.send_response(200)
        self.send_header("Content-Type", mime.get(f.suffix, "text/plain"))
        self.cors(); self.end_headers()
        self.wfile.write(f.read_bytes())

    def _body(self) -> dict:
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))

    def _json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.cors(); self.end_headers(); self.wfile.write(body)

    def _auth(self) -> bool:
        if request_authorized(self.headers, ACCESS_TOKEN, require_token=config.ATHOS_TOKEN_ENFORCED): return True
        self._json({
            "error": "unauthorized",
            "auth_required": True,
            "token_configured": bool(ACCESS_TOKEN),
            "token_required": config.ATHOS_TOKEN_ENFORCED,
        }, 401); return False

    def do_POST(self):
        p = self.path
        if p.startswith("/api/") and not self._auth(): return

        # ── Status ──────────────────────────────────────────────────────────
        if p == "/api/status":
            s = _router.status()
            self._json({
                **s,
                "session": session_kernel.status(),
                "server_runtime": server_runtime(),
                "capability_graph": capability_graph.compact_summary(available_engines=_router.available()),
                "epistemic_guard": epistemic_guard.guardrail_pack(),
            }); return

        if p == "/api/observability":
            from agent import list_processes
            self._json(process_snapshot(list_processes())); return

        if p == "/api/capabilities":
            self._json({
                "text": status_report(),
                "session": session_kernel.status(),
                "sync": sync_manager.status(),
                "capability_graph": capability_graph.compact_summary(available_engines=_router.available()),
                "epistemic_guard": epistemic_guard.guardrail_pack(),
            }); return

        if p == "/api/attach":
            self._json(attach_engine(self._body())); return

        if p == "/api/context_pack":
            self._json(context_for_attach(self._body())); return

        if p == "/api/delegate":
            self._json(delegate_request(self._body())); return

        if p == "/api/report":
            body = self._body()
            if str(body.get("type") or "").lower() in {"daily", "session", "weekly"}:
                self._json(_dashboard_report(body)); return
            self._json(attach_report(body)); return

        if p == "/api/checkpoint":
            body = self._body()
            result = session_kernel.checkpoint(
                body.get("goal", "checkpoint Athos"),
                decisions=body.get("decisions", []),
                tasks=body.get("tasks", []),
                files=body.get("files", []),
            )
            athos_room.add(
                actor=body.get("actor", "athos"),
                content=body.get("goal", "checkpoint"),
                msg_type="checkpoint",
                files=body.get("files", []),
                meta={"decisions": body.get("decisions", []), "tasks": body.get("tasks", [])},
            )
            self._json(result); return

        if p == "/api/protocol":
            body = self._body()
            self._json(run_protocol(body.get("name", ""), body)); return

        if p == "/api/sync/status":
            self._json(sync_manager.status()); return

        if p == "/api/sync/queue":
            body = self._body()
            self._json(sync_manager.queue_job(
                body.get("kind", "manual"),
                payload=body.get("payload", {}),
                requires_network=bool(body.get("requires_network", True)),
                source=body.get("source", "api"),
            )); return

        if p == "/api/sync/run":
            self._json(sync_manager.run_once()); return

        if p == "/api/memory/status":
            self._json(memory_status.status()); return

        if p == "/api/memory/note":
            body = self._body()
            note = str(body.get("note") or body.get("content") or "").strip()
            if not note:
                self._json({"ok": False, "error": "note requis"}, 400); return
            from memory_manager import write_session
            write_session(note)
            self._json({"ok": True, "written": len(note)}); return

        if p == "/api/memory/summary":
            body = self._body()
            if body.get("write", False):
                self._json(session_compactor.write_summary(limit=int(body.get("limit", 120)))); return
            self._json(session_compactor.build_summary(limit=int(body.get("limit", 120)))); return

        if p == "/api/cognition/status":
            self._json(metacognition.status()); return

        if p == "/api/decision/evaluate":
            body = self._body()
            self._json(situational_decision.decide(
                body.get("objective", ""),
                body.get("options", []),
            ).to_dict()); return

        if p == "/api/athos/advantage":
            body = self._body()
            self._json(athos_advantage.pack(
                engine=body.get("engine", "unknown_engine"),
                objective=body.get("objective", ""),
            )); return

        if p == "/api/athos/transform":
            body = self._body()
            self._json(transformation_stack.transformation_pack(
                engine=body.get("engine", "unknown_engine"),
                objective=body.get("objective", ""),
            )); return

        if p == "/api/local/capability":
            body = self._body()
            self._json(local_capability.austerity_pack(body.get("objective", ""))); return

        if p == "/api/capability_graph":
            body = self._body()
            self._json(capability_graph.build_graph(
                objective=body.get("objective", ""),
                available_engines=body.get("available_engines") or _router.available(),
            )); return

        if p == "/api/epistemic_guard":
            self._json(epistemic_guard.guardrail_pack()); return

        if p == "/api/external_sources":
            self._json(external_sources.catalog()); return

        if p == "/api/model_profiles":
            body = self._body()
            if body.get("objective") or body.get("request"):
                self._json(model_profiles.choose_profile(
                    body.get("objective") or body.get("request") or "",
                    available_engines=body.get("available_engines") or _router.available(),
                )); return
            self._json(model_profiles.catalog(_router.available())); return

        if p == "/api/review_pipeline":
            body = self._body()
            self._json(review_pipeline.plan(
                body.get("objective") or body.get("request") or "",
                changed_files=body.get("changed_files") or [],
            )); return

        if p == "/api/truth_ledger/scan":
            body = self._body()
            self._json(truth_ledger.signal_scan(
                body.get("text") or body.get("message") or "",
                source=body.get("source"),
            )); return

        if p == "/api/sse/parse":
            body = self._body()
            if body.get("block"):
                self._json(sse_parser.process_sse_block(body.get("block", ""), body.get("state"))); return
            if body.get("event_type"):
                custom = sse_parser.process_custom_event(body.get("event_type", ""), body.get("data", ""))
                if custom.get("handled"):
                    self._json(custom); return
            self._json(sse_parser.process_sse_data(body.get("data", ""), body.get("state"))); return

        if p == "/api/self_improvement_plan":
            body = self._body()
            self._json({"plan": plan_self_improvement(body.get("request", "")).to_dict()}); return

        if p == "/api/failover/simulate":
            body = self._body()
            if not body.get("available"):
                body["available"] = _router.available()
            if not body.get("current"):
                body["current"] = _router.current
            self._json(failover_simulator.simulate(body)); return

        # ── Alertes ─────────────────────────────────────────────────────────
        if p == "/api/budget_alert":
            self._json(_mem.pop_alert("budget_alert.json")); return
        if p == "/api/engine_alert":
            self._json(_mem.pop_alert("engine_alert.json")); return

        # ── Stream principal (SSE) ───────────────────────────────────────────
        if p == "/api/stream":
            body = self._body()
            msg = body.get("message", "")
            task_id = body.get("task_id") or ""
            if msg:
                entry = athos_room.add(
                    actor="clement",
                    content=msg,
                    msg_type="message",
                    task_id=task_id,
                    meta={"source": "main_prompt"},
                )
                _schedule_room_auto_response(entry)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control",  "no-cache")
            self.cors(); self.end_headers()
            stream_open = True

            def sse(obj):
                nonlocal stream_open
                if not stream_open:
                    return False
                try:
                    self.wfile.write(f"data: {json.dumps(obj, ensure_ascii=False)}\n\n".encode())
                    self.wfile.flush()
                    return True
                except (BrokenPipeError, ConnectionResetError, OSError):
                    stream_open = False
                    return False

            try:
                athos = AthosEngine(_mem, _router, sse, lambda: _make_permission_checker(sse))
                reply = athos.respond(msg)
                if reply:
                    athos_room.add(
                        actor="athos",
                        content=reply,
                        msg_type="result",
                        task_id=task_id,
                        status="completed",
                        meta={"source": "main_prompt", "engine": _router.current},
                    )
                    extract_and_save_async(msg, reply)
            except Exception as e:
                athos_room.add(
                    actor="athos",
                    content=str(e),
                    msg_type="error",
                    task_id=task_id,
                    status="failed",
                    meta={"source": "main_prompt"},
                )
                sse({"error": str(e), "t": f"Erreur : {e}"})

            sse("[DONE]"); return

        # ── Transcription audio (STT serveur) ────────────────────────────────
        if p == "/api/transcribe":
            length     = int(self.headers.get("Content-Length", 0))
            audio_bytes = self.rfile.read(length)
            if not audio_bytes:
                self._json({"error": "no audio"}, 400); return
            import speech_recognition as sr
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(audio_bytes); tmp_path = tmp.name
            wav_path = tmp_path.replace(".webm", ".wav")
            try:
                if not shutil.which("ffmpeg"):
                    self._json({"error": "ffmpeg manquant: installe `brew install ffmpeg` pour le fallback vocal serveur."}, 500)
                    return
                conv = subprocess.run(["ffmpeg", "-y", "-i", tmp_path, "-ar", "16000", "-ac", "1", wav_path],
                                      capture_output=True, text=True, timeout=30)
                if conv.returncode != 0:
                    self._json({"error": f"conversion audio impossible: {conv.stderr[-240:]}"}, 500)
                    return
                rec = sr.Recognizer()
                with sr.AudioFile(wav_path) as src:
                    audio = rec.record(src)
                if config.OPENAI_KEY and config.spend_policy()["whisper_enabled"]:
                    import openai
                    with open(wav_path, "rb") as f:
                        text = openai.OpenAI(api_key=config.OPENAI_KEY).audio.transcriptions.create(
                            model="whisper-1", file=f, language="fr").text
                else:
                    text = rec.recognize_google(audio, language="fr-FR")
                self._json({"text": text})
            except Exception as e:
                self._json({"error": str(e)}, 500)
            finally:
                for f in [tmp_path, wav_path]:
                    try: Path(f).unlink()
                    except: pass
            return

        # ── Process control ──────────────────────────────────────────────────
        if p == "/api/kill":
            body = self._body()
            pid  = body.get("pid")
            if pid:
                from agent import kill_process
                self._json({"ok": True, "msg": kill_process(int(pid))}); return
            self._json({"ok": False, "msg": "pid manquant"}, 400); return

        if p == "/api/stop_observed":
            body = self._body()
            pid = body.get("pid")
            if pid:
                self._json({"ok": True, "msg": stop_observed_pid(int(pid))}); return
            self._json({"ok": False, "msg": "pid manquant"}, 400); return

        if p == "/api/permit":
            body    = self._body()
            perm_id = body.get("id", "")
            approved = bool(body.get("approved", False))
            with _permits_lock:
                entry = _permits.get(perm_id)
            if entry:
                entry["approved"] = approved; entry["event"].set()
                self._json({"ok": True, "approved": approved}); return
            self._json({"ok": False, "msg": "permission introuvable"}, 404); return

        if p == "/api/processes":
            from agent import list_processes
            self._json({"processes": list_processes()}); return

        # ── AGI cognition endpoints ──────────────────────────────────────────
        if p == "/api/goals":
            from goal_manager import get_manager
            body = self._body()
            gm = get_manager()
            action = body.get("action", "list")
            if action == "add":
                g = gm.add(
                    description=body.get("description", ""),
                    priority=int(body.get("priority", 5)),
                    steps=body.get("steps", []),
                    source=body.get("source", "user"),
                )
                self._json(g.to_dict()); return
            if action == "clear_done":
                self._json({"cleared": gm.clear_done()}); return
            if action == "fail":
                g = gm.get(body.get("id", ""))
                if g:
                    g.fail(body.get("reason", "user request"))
                    gm.update(g)
                    self._json(g.to_dict()); return
            self._json({
                "goals": [g.to_dict() for g in gm.list_all()],
                "summary": gm.status_summary(),
                "top": gm.top().to_dict() if gm.top() else None,
            }); return

        if p == "/api/beliefs":
            from belief_store import get_store
            body = self._body()
            bs = get_store()
            action = body.get("action", "query")
            if action == "add":
                b = bs.add(
                    subject=body.get("subject", ""),
                    predicate=body.get("predicate", ""),
                    confidence=float(body.get("confidence", 0.8)),
                    source=body.get("source", "user"),
                    tags=body.get("tags", []),
                    ttl_seconds=body.get("ttl_seconds"),
                    verified=bool(body.get("verified", False)),
                )
                self._json(b.to_dict()); return
            if action == "forget":
                self._json({"ok": bs.forget(body.get("id", ""))}); return
            beliefs = bs.query(
                subject=body.get("subject"),
                tag=body.get("tag"),
                min_confidence=float(body.get("min_confidence", 0.0)),
            )
            self._json({
                "beliefs": [b.to_dict() for b in beliefs],
                "summary": bs.summary(),
            }); return

        if p == "/api/skills":
            from skill_library import get_library
            from skill_acquisition import pending_status
            body = self._body()
            lib = get_library()
            action = body.get("action", "list")
            if action == "propose":
                if not (config.SKILL_INSTALL_ENABLED and bool(body.get("allow_mutation", False))):
                    self._json({
                        "ok": False,
                        "requires_confirmation": True,
                        "msg": "skill proposal mutation blocked: set ATHOS_SKILL_INSTALL_ENABLED=true and allow_mutation=true",
                        "plan": {
                            "name": body.get("name", ""),
                            "description": body.get("description", ""),
                            "mutations": ["write skill proposal to core/skills/manifest.json"],
                        },
                    }); return
                s = lib.propose(
                    name=body.get("name", ""),
                    description=body.get("description", ""),
                    code=body.get("code", ""),
                    dependencies=body.get("dependencies", []),
                    tags=body.get("tags", []),
                    test_code=body.get("test_code", ""),
                    source_repo=body.get("source_repo", ""),
                )
                self._json(s.to_dict()); return
            if action == "integrate":
                if not config.SKILL_INSTALL_ENABLED:
                    self._json({
                        "ok": False,
                        "requires_confirmation": True,
                        "msg": "skill integration blocked: ATHOS_SKILL_INSTALL_ENABLED=false",
                        "plan": lib.integration_plan(body.get("id", "")),
                    }); return
                ok, msg = lib.test_and_integrate(
                    body.get("id", ""),
                    allow_mutation=bool(body.get("allow_mutation", False)),
                    allow_dependency_install=bool(body.get("allow_dependency_install", False)),
                )
                self._json({"ok": ok, "msg": msg}); return
            if action == "plan":
                self._json(lib.integration_plan(body.get("id", ""))); return
            if action == "search":
                results = lib.search(body.get("query", ""), limit=int(body.get("limit", 5)))
                self._json({"skills": [s.to_dict() for s in results]}); return
            if action == "pending":
                self._json(pending_status(limit=int(body.get("limit", 20)))); return
            self._json({
                "skills": [s.to_dict() for s in lib.list_active()],
                "summary": lib.summary(),
                "pending_drive": pending_status(limit=int(body.get("limit", 8))),
            }); return

        if p == "/api/search":
            from tools.web_search import search, search_github, fetch_raw
            body = self._body()
            kind = body.get("kind", "web")
            query = body.get("query", "")
            if kind == "github":
                self._json({"results": search_github(query, max_results=int(body.get("max_results", 5)))}); return
            if kind == "fetch":
                self._json({"content": fetch_raw(body.get("url", ""))}); return
            self._json({"results": search(query, max_results=int(body.get("max_results", 5)))}); return

        # ── ATHOS Room ───────────────────────────────────────────────────────
        if p == "/api/conversation":
            body = self._body()
            action = body.get("action", "get")
            if action == "clear":
                athos_room.clear(task_id=body.get("task_id"))
                self._json({"ok": True}); return
            if action == "context":
                engine = body.get("engine", "athos")
                self._json({"context": athos_room.get_context_for_engine(engine, limit=int(body.get("limit", 40)))}); return
            if action == "health":
                self._json(athos_room.health(limit=int(body.get("limit", 100)))); return
            if action == "runtime":
                self._json({"ok": True, **_room_runtime_state()}); return
            thread = athos_room.get_thread(
                limit=int(body.get("limit", 100)),
                task_id=body.get("task_id"),
            )
            self._json({"thread": thread, "summary": athos_room.summary()}); return

        if p == "/api/message":
            body = self._body()
            actor   = body.get("actor", "athos")
            content = body.get("content") or body.get("message") or ""
            if not content:
                self._json({"ok": False, "error": "content requis"}, 400); return
            entry = athos_room.add(
                actor=actor,
                content=content,
                msg_type=body.get("type", "message"),
                task_id=body.get("task_id"),
                files=body.get("files"),
                status=body.get("status"),
                meta=body.get("meta"),
            )
            auto_work = _schedule_room_athos_work(entry)
            auto_response = (
                {"scheduled": False, "reason": "handled_by_auto_work"}
                if auto_work.get("scheduled")
                else _schedule_room_auto_response(entry)
            )
            self._json({
                "ok": True,
                "entry": entry,
                "auto_response": auto_response,
                "auto_work": auto_work,
            }); return

        if p == "/api/tasks":
            body = self._body()
            action = body.get("action", "list")
            task_id = body.get("task_id", "")
            item_id = body.get("id", "")
            if action == "create":
                task = task_queue.create(
                    body.get("title") or body.get("content") or "ATHOS task",
                    content=body.get("content", ""),
                    task_id=task_id,
                    source=body.get("source", "api"),
                    kind=body.get("kind", "manual"),
                    priority=int(body.get("priority", 5)),
                    meta=body.get("meta"),
                )
                self._json({"ok": True, "task": task, "summary": task_queue.summary()}); return
            if action == "get":
                task = task_queue.get(task_id=task_id, item_id=item_id)
                self._json({"ok": bool(task), "task": task}); return
            if action == "pause":
                self._json(task_queue.pause(task_id=task_id, item_id=item_id, reason=body.get("reason", ""))); return
            if action == "resume":
                self._json(task_queue.resume(task_id=task_id, item_id=item_id)); return
            if action == "retry":
                self._json(task_queue.retry(task_id=task_id, item_id=item_id)); return
            if action == "cancel":
                self._json(task_queue.cancel(task_id=task_id, item_id=item_id, reason=body.get("reason", ""))); return
            if action == "sweep_stale":
                self._json(task_queue.sweep_stale(stale_after_seconds=body.get("stale_after_seconds"))); return
            if action == "start":
                self._json(task_queue.start(task_id=task_id, item_id=item_id)); return
            if action == "complete":
                self._json(task_queue.complete(task_id=task_id, item_id=item_id, result=body.get("result", ""))); return
            if action == "block":
                self._json(task_queue.block(task_id=task_id, item_id=item_id, reason=body.get("reason", ""))); return
            self._json({
                "ok": True,
                "tasks": task_queue.list_tasks(status=body.get("status"), limit=int(body.get("limit", 100))),
                "summary": task_queue.summary(),
            }); return

        if p == "/api/room/respond":
            body = self._body()
            message = body.get("message") or body.get("content") or ""
            if not message:
                self._json({"ok": False, "error": "message requis"}, 400); return
            result = room_responders.respond(
                message,
                task_id=body.get("task_id", ""),
                engines=body.get("engines") or ["claude", "codex"],
                timeout=int(body.get("timeout", 45)),
                force=bool(body.get("force", False)),
            )
            self._json(result); return

        if p == "/api/use-athos":
            import time as _time
            stores = [
                {
                    "name": "ex-nihilo-agency",
                    "domain": "ex-nihilo-agency.myshopify.com",
                    "client": "Olivia",
                    "live_theme": "olivia-16-5-3",
                    "status": "live",
                    "finance": {"note": "Connect Shopify API for live data"},
                    "seo": {"note": "Connect Google Search Console for live data"},
                },
                {
                    "name": "rouge-pivoine",
                    "domain": "rouge-pivoine.myshopify.com",
                    "client": "Rouge Pivoine",
                    "live_theme": "Kalles v4.3.6",
                    "draft_theme": "Rouge Pivoine — Draft",
                    "status": "live",
                    "finance": {"note": "Connect Shopify API for live data"},
                    "seo": {"note": "Connect Google Search Console for live data"},
                },
            ]
            # Pull recent agentmemory entries for context
            recent_memories = []
            try:
                import urllib.request as _ur
                mem_req = _ur.Request(
                    "http://localhost:8765/memories?category=athos&n_results=5",
                    method="GET",
                )
                with _ur.urlopen(mem_req, timeout=2) as resp:
                    mem_data = json.loads(resp.read())
                    recent_memories = mem_data.get("memories", [])
            except Exception:
                pass
            skills_summary = {
                "claude": "~/.claude/skills/ — gstack 53 skills + ui-ux-pro-max + seo-expert + shopify-expert",
                "codex": "~/.codex/skills/ — 87 skills: agent-skills, athos-architects, ui-references, shopify-references",
                "cross_access": True,
            }
            self._json({
                "status": "athos_active",
                "timestamp": _time.strftime("%Y-%m-%dT%H:%M:%S"),
                "sites": stores,
                "skills": skills_summary,
                "memory": {
                    "recent": recent_memories[:3],
                    "endpoint": "http://localhost:8765",
                    "categories": ["athos", "shopify", "seo", "code", "session"],
                },
                "services": {
                    "athos_hub": f"http://localhost:{config.ATHOS_PORT}",
                    "agentmemory": "http://localhost:8765",
                    "9router": "http://localhost:20128/dashboard",
                },
                "message": "ATHOS actif. Données financières live : connecter Shopify Admin API. SEO live : connecter Google Search Console.",
            }); return

        if p in {"/api/loop", "/api/autonomous_loop"}:
            from autonomous_loop import recent_events, start_loop, status as loop_status, stop_loop
            body = self._body()
            action = body.get("action", "status")
            if action == "start":
                try:
                    start_loop(
                        _make_loop_llm(),
                        tick_interval=float(body.get("tick_interval", config.AUTONOMOUS_LOOP_DEFAULT_TICK)),
                        idle_stop_after=int(body.get("idle_stop_after", 0)),
                        allow_autonomous=bool(body.get("allow_autonomous", False)),
                        allow_skill_mutation=bool(body.get("allow_skill_mutation", False)),
                    )
                except PermissionError as e:
                    self._json({"ok": False, "running": False, "requires_confirmation": True, "msg": str(e), "status": loop_status()}); return
                self._json({"ok": True, **loop_status()}); return
            if action == "stop":
                stop_loop()
                self._json({"ok": True, **loop_status()}); return
            if action == "events":
                self._json({"events": recent_events(limit=int(body.get("limit", 20))), "status": loop_status()}); return
            self._json(loop_status()); return

        if p == "/api/settings":
            import ast
            env_path = config.ROOT / ".env"
            env_keys: dict[str, str] = {}
            if env_path.exists():
                for raw_line in env_path.read_text().splitlines():
                    raw_line = raw_line.strip()
                    if raw_line and not raw_line.startswith("#") and "=" in raw_line:
                        k, _, v = raw_line.partition("=")
                        env_keys[k.strip()] = v.strip()
            MASK = {"ATHOS_ACCESS_TOKEN", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GROK_API_KEY"}
            visible = {k: ("***" if k in MASK and v else v) for k, v in env_keys.items()}
            self._json({
                "spend_policy": config.spend_policy(),
                "security_policy": config.server_security_policy(),
                "engine_order": config.ATHOS_ENGINE_ORDER,
                "env": visible,
            }); return

        if p == "/api/projects":
            mem_path = Path(config.DRIVE) / "athos_projects.mem"
            projects: dict[str, dict] = {}
            if mem_path.exists():
                for raw_line in mem_path.read_text().splitlines():
                    raw_line = raw_line.strip()
                    if not raw_line.startswith("§proj:"):
                        continue
                    rest = raw_line[len("§proj:"):]
                    name, _, fields_str = rest.partition("|")
                    if not name:
                        continue
                    if name not in projects:
                        projects[name] = {"name": name}
                    for field in fields_str.split("|"):
                        if ":" in field:
                            fk, _, fv = field.partition(":")
                            projects[name][fk] = fv
            self._json({"projects": list(projects.values())}); return

        # ── SSE live events (dashboard tail) ────────────────────────────────────
        if p == "/api/events":
            import time as _time
            kernel_file = Path(config.DRIVE) / "athos_session_kernel.jsonl"
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no")
            self.cors(); self.end_headers()
            stream_ok = True

            def _sse_write(event: str, data: dict) -> bool:
                nonlocal stream_ok
                if not stream_ok:
                    return False
                try:
                    payload = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                    self.wfile.write(payload.encode())
                    self.wfile.flush()
                    return True
                except (BrokenPipeError, ConnectionResetError, OSError):
                    stream_ok = False
                    return False

            # seed: send current status snapshot
            try:
                s = _router.status()
                _sse_write("status", {
                    **s,
                    "session": session_kernel.status(),
                    "capability_graph": capability_graph.compact_summary(available_engines=_router.available()),
                })
            except Exception:
                pass

            # tail session_kernel.jsonl for new events + heartbeat
            pos = kernel_file.stat().st_size if kernel_file.exists() else 0
            last_heartbeat = _time.time()
            try:
                while stream_ok:
                    if kernel_file.exists():
                        new_size = kernel_file.stat().st_size
                        if new_size > pos:
                            with open(kernel_file, "r", encoding="utf-8", errors="ignore") as f:
                                f.seek(pos)
                                for line in f:
                                    line = line.strip()
                                    if not line:
                                        continue
                                    try:
                                        event_data = json.loads(line)
                                        if not _sse_write("session_event", event_data):
                                            break
                                    except json.JSONDecodeError:
                                        pass
                            pos = new_size
                    now = _time.time()
                    if now - last_heartbeat >= 30:
                        _sse_write("heartbeat", {"ts": now, "server": "athos"})
                        last_heartbeat = now
                    _time.sleep(1)
            except Exception:
                pass
            return

        self.send_response(404); self.end_headers()


if __name__ == "__main__":
    import weekly_update, agentmemory_server, subprocess as _sp, os as _os
    weekly_update.check_and_run()
    agentmemory_server.ensure_running()
    # 9router proxy dashboard
    _router_script = Path(__file__).parent.parent / "scripts" / "start_9router.sh"
    if _router_script.exists():
        _sp.Popen(["bash", str(_router_script)], stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
    port = config.ATHOS_PORT
    s    = _router.status()
    config.ATHOS_PID_FILE.write_text(str(os.getpid()), "utf-8")
    atexit.register(lambda: config.ATHOS_PID_FILE.unlink(missing_ok=True))
    print(f"\n  ╔══════════════════════════════════╗")
    print(f"  ║      A.T.H.O.S. — VOICE SERVER   ║")
    print(f"  ╚══════════════════════════════════╝\n")
    print(f"  Moteur  : {s['engine'].upper()}")
    print(f"  Budget  : {s['budget']:.2f}€")
    print(f"  Host    : {config.ATHOS_BIND_HOST}")
    print(f"  Port    : {port}\n")
    server = ThreadingHTTPServer((config.ATHOS_BIND_HOST, port), Handler)
    _replay_offline_room_after_boot()
    server.serve_forever()
