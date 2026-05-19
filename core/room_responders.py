"""ATHOS Room responders — call Claude/Codex as visible Room participants."""
from __future__ import annotations

import shutil
import subprocess
from typing import Iterable
from pathlib import Path

try:
    from . import athos_room, config, engine_router
except ImportError:
    import athos_room
    import config
    import engine_router


DEFAULT_TIMEOUT = 45
CLAUDE_CANDIDATES = [
    "/usr/local/bin/claude",
    "/opt/homebrew/bin/claude",
]


def _prompt(engine: str, message: str) -> str:
    context = athos_room.get_context_for_engine(engine, limit=30)
    return f"""Tu es {engine.upper()} attaché à ATHOS Room.
ATHOS est l'identité principale. Tu es un moteur participant.
Réponds brièvement au dernier message de Clément.
Ne modifie aucun fichier, ne lance aucune commande, ne propose pas de mutation.
Si tu n'as rien à ajouter, dis-le clairement en une phrase.

{context}

MESSAGE DE CLÉMENT:
{message}
"""


def _run_claude(prompt: str, timeout: int) -> str:
    claude = shutil.which("claude") or next((path for path in CLAUDE_CANDIDATES if Path(path).exists()), "")
    if not claude:
        raise RuntimeError("claude CLI introuvable")
    result = subprocess.run(
        [claude, "-p", prompt, "--output-format", "text", "--dangerously-skip-permissions"],
        cwd=str(config.ATHOS_PATH),
        capture_output=True,
        text=True,
        timeout=timeout,
        stdin=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "claude failed").strip()[:500])
    return result.stdout.strip()


def _run_codex(prompt: str, timeout: int) -> str:
    codex = engine_router.chatgpt_plus_path()
    if not codex:
        raise RuntimeError("codex CLI introuvable")
    result = subprocess.run(
        [codex, "exec", "--dangerously-bypass-approvals-and-sandbox", prompt],
        cwd=str(config.ATHOS_PATH),
        capture_output=True,
        text=True,
        timeout=timeout,
        stdin=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "codex failed").strip()[:500])
    return result.stdout.strip()


def respond(
    message: str,
    task_id: str = "",
    engines: Iterable[str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Ask requested engines to answer in ATHOS Room.

    This is intentionally bounded and non-mutating: it only posts Room messages.
    """
    requested = [str(e).lower() for e in (engines or ["claude", "codex"])]
    results = []
    for engine in requested:
        actor = "claude" if engine in {"claude", "claude_code"} else "codex" if engine in {"codex", "chatgpt", "chatgpt_plus"} else engine
        athos_room.add(
            actor=actor,
            content=f"{actor} prépare une réponse Room...",
            msg_type="action",
            task_id=task_id,
            status="running",
            meta={"source": "room_responder"},
        )
        try:
            prompt = _prompt(actor, message)
            if actor == "claude":
                reply = _run_claude(prompt, timeout)
            elif actor == "codex":
                reply = _run_codex(prompt, timeout)
            else:
                raise RuntimeError(f"engine unsupported: {engine}")
            if not reply:
                reply = "Je suis présent, rien à ajouter pour l'instant."
            entry = athos_room.add(
                actor=actor,
                content=reply,
                msg_type="result",
                task_id=task_id,
                status="completed",
                meta={"source": "room_responder"},
            )
            results.append({"engine": actor, "ok": True, "entry": entry})
        except Exception as exc:
            entry = athos_room.add(
                actor=actor,
                content=f"{actor} indisponible: {exc}",
                msg_type="error",
                task_id=task_id,
                status="failed",
                meta={"source": "room_responder"},
            )
            results.append({"engine": actor, "ok": False, "error": str(exc), "entry": entry})
    return {"ok": all(r["ok"] for r in results), "results": results}
