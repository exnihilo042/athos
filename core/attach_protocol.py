"""Mandatory Athos attach protocol for external LLM engines."""
from __future__ import annotations

import uuid
from typing import Any

try:
    from . import config, session_compactor, session_kernel, sync_manager
    from .athos_advantage import pack as athos_advantage_pack
    from .capabilities import status_report
    from .named_protocols import list_protocols, match_protocol, run_protocol
    from .registries import device_registry, hardware_registry, skill_registry
except ImportError:
    import config
    import session_compactor
    import session_kernel
    import sync_manager
    from athos_advantage import pack as athos_advantage_pack
    from capabilities import status_report
    from named_protocols import list_protocols, match_protocol, run_protocol
    from registries import device_registry, hardware_registry, skill_registry


PROTOCOL_VERSION = "athos-attach-v1"
PROMPT_FILE = config.ATHOS_PATH / "ATHOS_ATTACH_PROMPT.md"
CANONICAL_MEMORY_FILES = [
    "athos_identity.mem",
    "athos_capabilities.mem",
    "athos_cognition.mem",
    "athos_projects.mem",
    "athos_kernel_plan.mem",
    "athos_session_summary.mem",
    "athos_conv.mem",
]


RULES = [
    "Athos est l'identité principale; le LLM attaché est seulement un moteur.",
    "Avant toute réponse/action, appeler /api/attach puis utiliser le context pack reçu.",
    "Toute action, décision, commande ou blocage doit être reporté via /api/report.",
    "Si Athos est indisponible, mode cache lecture seule: aucune mutation, aucun coût API payant.",
    "Mutation système, écriture fichier, installation, shell, commit/push: plan visible + accord utilisateur.",
    "Ne jamais exposer de chaîne de pensée brute; exposer un journal opérationnel vérifiable.",
]


def _engine_name(payload: dict[str, Any]) -> str:
    return str(payload.get("engine") or payload.get("engine_name") or payload.get("client") or "unknown_engine")[:160]


def _capability_pack() -> dict[str, Any]:
    return {
        "named_protocols": list_protocols(),
        "skills": skill_registry(),
        "devices": device_registry(),
        "hardware": hardware_registry(),
        "sync": sync_manager.status(),
    }


def _drive_memory_pack(max_chars: int = 6_000) -> dict[str, Any]:
    """Small canonical Drive memory pack for newly attached engines."""
    files: dict[str, list[str]] = {}
    remaining = max_chars
    per_file = max(400, max_chars // max(1, len(CANONICAL_MEMORY_FILES)))
    for name in CANONICAL_MEMORY_FILES:
        path = config.DRIVE / name
        if not path.exists() or remaining <= 0:
            continue
        lines = [line for line in path.read_text("utf-8", errors="ignore").splitlines() if line.strip()]
        if name == "athos_conv.mem":
            selected = lines[-12:]
        else:
            selected = [
                line for line in lines
                if line.startswith("§") or any(token in line for token in ("§done:", "§todo:", "§blocker:", "§checkpoint:"))
            ][-18:]
        clipped: list[str] = []
        file_remaining = min(per_file, remaining)
        for line in selected:
            if remaining <= 0 or file_remaining <= 0:
                break
            item = line[:600]
            clipped.append(item)
            consumed = len(item) + 1
            remaining -= consumed
            file_remaining -= consumed
        if clipped:
            files[name] = clipped
    return {
        "source": str(config.DRIVE),
        "files": files,
        "truncated": remaining <= 0,
        "max_chars": max_chars,
    }


def context_for_attach(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    max_chars = int(payload.get("max_chars") or session_kernel.MAX_CONTEXT_CHARS)
    memory_chars = int(payload.get("memory_chars") or 6_000)
    engine = _engine_name(payload)
    objective = str(payload.get("purpose") or payload.get("objective") or payload.get("scope") or "")
    return {
        "identity": "A.T.H.O.S.",
        "role": "sovereign_layer_for_memory_context_cognition_and_skills",
        "rules": RULES,
        "session": session_kernel.status(),
        "context_pack": session_kernel.context_pack(max_chars=max_chars),
        "drive_memory": _drive_memory_pack(max_chars=memory_chars),
        "athos_advantage": athos_advantage_pack(engine=engine, objective=objective),
        "latest_checkpoint": session_kernel.latest_checkpoint(),
        "recent_messages": session_kernel.latest_messages(limit=12),
        "capabilities_text": status_report(),
        "capabilities": _capability_pack(),
        "cost_policy": config.spend_policy(),
        "endpoints": {
            "attach": "/api/attach",
            "context_pack": "/api/context_pack",
            "delegate": "/api/delegate",
            "report": "/api/report",
            "checkpoint": "/api/checkpoint",
            "sync_status": "/api/sync/status",
        },
    }


def attach_engine(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    attach_id = str(payload.get("attach_id") or uuid.uuid4().hex)
    engine = _engine_name(payload)
    event = session_kernel.record_attach(
        attach_id,
        engine,
        meta={
            "protocol_version": PROTOCOL_VERSION,
            "client": payload.get("client", ""),
            "scope": payload.get("scope", "default"),
            "declared_user": payload.get("user", ""),
        },
    )
    return {
        "ok": True,
        "protocol_version": PROTOCOL_VERSION,
        "attach_id": attach_id,
        "engine": engine,
        "identity": "Athos",
        "must_report": True,
        "offline_policy": "read_only_cache_no_mutation",
        "event": event,
        **context_for_attach(payload),
    }


def delegate(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    attach_id = str(payload.get("attach_id") or "")
    engine = _engine_name(payload)
    request = str(payload.get("request") or payload.get("message") or "")
    protocol = match_protocol(request)
    if protocol:
        result = run_protocol(protocol, payload)
        decision = f"named_protocol:{protocol}"
        text = result.get("text", "")
        requires_confirmation = bool(result.get("protocol", {}).get("requires_approval", True))
    else:
        decision = "athos_context_first"
        text = (
            "Athos a reçu la délégation. Réponds en tant que moteur Athos avec le context pack, "
            "puis reporte les actions via /api/report. Toute mutation reste permissionnée."
        )
        requires_confirmation = _looks_risky(request)
    event = session_kernel.record_delegate(
        attach_id,
        engine,
        request,
        decision,
        meta={"requires_confirmation": requires_confirmation, "protocol": protocol or ""},
    )
    return {
        "ok": True,
        "attach_id": attach_id,
        "decision": decision,
        "recommended_engine": "athos_kernel",
        "requires_confirmation": requires_confirmation,
        "response_or_plan": text,
        "context": context_for_attach({"max_chars": 2_000}),
        "event": event,
    }


def report(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    attach_id = str(payload.get("attach_id") or "")
    engine = _engine_name(payload)
    summary = str(payload.get("summary") or payload.get("message") or "report received")
    status = str(payload.get("status") or "reported")
    event = session_kernel.record_report(attach_id, engine, summary, status=status, meta=payload.get("meta") or {})
    checkpoint_event = None
    session_summary = None
    if payload.get("checkpoint"):
        cp = payload["checkpoint"] if isinstance(payload["checkpoint"], dict) else {}
        checkpoint_event = session_kernel.checkpoint(
            cp.get("goal", summary),
            decisions=cp.get("decisions", []),
            tasks=cp.get("tasks", []),
            files=cp.get("files", []),
        )
    elif str(payload.get("event") or "").lower() == "checkpoint":
        checkpoint_event = session_kernel.checkpoint(
            payload.get("goal", summary),
            decisions=payload.get("decisions", []),
            tasks=payload.get("tasks", []),
            files=payload.get("files", []),
        )
    if checkpoint_event:
        session_summary = _write_session_summary_safely()
    warnings = []
    if not attach_id:
        warnings.append("attach_id manquant: report accepté mais non relié à une IA attachée")
    return {"ok": True, "event": event, "checkpoint": checkpoint_event, "session_summary": session_summary, "warnings": warnings}


def _write_session_summary_safely() -> dict[str, Any] | None:
    try:
        return session_compactor.write_summary()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def attach_prompt() -> str:
    if PROMPT_FILE.exists():
        return PROMPT_FILE.read_text("utf-8")
    return "\n".join([
        "# ATHOS attach prompt",
        "Tu es un moteur d'Athos, pas l'identité principale.",
        "Avant de répondre, appelle /api/attach et utilise le context pack.",
        "Reporte actions et blocages via /api/report.",
    ])


def attached_engines(limit: int = 20) -> list[dict[str, Any]]:
    rows = []
    for event in session_kernel.read_events(limit=limit * 4):
        if event.get("type") == "attach":
            rows.append({
                "attach_id": event.get("attach_id", ""),
                "engine": event.get("engine", ""),
                "ts": event.get("ts", ""),
                "meta": event.get("meta", {}),
            })
    return rows[-limit:]


def _looks_risky(text: str) -> bool:
    q = (text or "").lower()
    return any(token in q for token in (
        "install", "installe", "supprime", "delete", "kill", "commit", "push",
        "écris", "ecris", "modifie", "shell", "terminal", "scan", "sécurise", "securise",
    ))
