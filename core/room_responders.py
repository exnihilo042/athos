"""ATHOS Room responders — call Claude/Codex as visible Room participants."""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import stat
import subprocess
import tempfile
import time
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
KEYCHAIN_SERVICE = "Claude Code-credentials"
_KEYCHAIN_CACHE: dict[str, tuple[float, str]] = {}
_KEYCHAIN_CACHE_TTL = 60  # seconds
DEFAULT_CLAUDE_TOKEN_FILE = Path.home() / ".athos" / "claude_token"
RESPONDER_META_SOURCE = "room_responder"
_ENGINE_COOLDOWNS: dict[str, tuple[float, str]] = {}
_USAGE_LIMIT_COOLDOWN_S = 15 * 60


def _read_claude_token_file() -> str | None:
    """Read a long-lived Claude token from a local protected file.

    This file is intentionally outside the repo and Drive. It should be created
    by `claude setup-token` or an operator-controlled setup script and must not
    be group/world readable.
    """
    raw_path = os.getenv("ATHOS_CLAUDE_TOKEN_FILE", str(DEFAULT_CLAUDE_TOKEN_FILE)).strip()
    if not raw_path:
        return None
    path = Path(raw_path).expanduser()
    if not path.exists():
        return None
    try:
        mode = path.stat().st_mode
        if mode & (stat.S_IRWXG | stat.S_IRWXO):
            raise RuntimeError(f"Claude token file permissions too open: {path}")
        token = path.read_text("utf-8").strip()
    except RuntimeError:
        raise
    except Exception:
        return None
    return token or None


def _resolve_claude_oauth_token() -> str | None:
    """Extract the Claude OAuth access token from the macOS Keychain.

    Background: when ATHOS HUB runs as a LaunchAgent, subprocess invocations of
    the Claude CLI cannot read the user Keychain item directly (its ACL
    restricts decrypt to `/usr/bin/security`). Result: claude falls back to an
    anonymous API session and reports "Credit balance is too low".

    Workaround: call `/usr/bin/security find-generic-password -w` ourselves
    (which IS allowed by the ACL), parse the OAuth JSON blob, then expose the
    access token via the ANTHROPIC_API_KEY env var on the subprocess. Cached
    briefly to avoid spawning `security` per request.
    """
    if platform.system() != "Darwin":
        return None
    cached = _KEYCHAIN_CACHE.get(KEYCHAIN_SERVICE)
    if cached and (time.time() - cached[0] < _KEYCHAIN_CACHE_TTL):
        return cached[1] or None
    try:
        result = subprocess.run(
            ["/usr/bin/security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True,
            text=True,
            timeout=5,
            stdin=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    payload = result.stdout.strip()
    if not payload:
        return None
    try:
        data = json.loads(payload)
        token = data.get("claudeAiOauth", {}).get("accessToken") or ""
    except (json.JSONDecodeError, AttributeError):
        token = ""
    _KEYCHAIN_CACHE[KEYCHAIN_SERVICE] = (time.time(), token)
    return token or None


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
    env = os.environ.copy()
    file_token = _read_claude_token_file()
    if file_token:
        # Claude Pro session token has priority over any inherited API key.
        # A launchd environment or parent shell may contain an exhausted
        # Anthropic API key; keeping it would bypass the paid Claude Pro route.
        env["ANTHROPIC_API_KEY"] = file_token
    # Pre-resolve the OAuth token from Keychain so claude doesn't have to.
    # Required when the hub runs under launchd: in a LaunchAgent context the
    # `claude` CLI cannot read the Keychain item directly (its ACL restricts
    # decrypt to `/usr/bin/security`). Falling back to anonymous API yields
    # "Credit balance is too low". We pre-extract the OAuth access token via
    # the `security` CLI (which IS allowed by the ACL) and pass it as
    # ANTHROPIC_API_KEY to the claude subprocess.
    if not env.get("ANTHROPIC_API_KEY"):
        token = _resolve_claude_oauth_token()
        if token:
            env["ANTHROPIC_API_KEY"] = token
    result = subprocess.run(
        [claude, "-p", prompt, "--output-format", "text", "--dangerously-skip-permissions"],
        cwd=str(config.ATHOS_PATH),
        capture_output=True,
        text=True,
        timeout=timeout,
        stdin=subprocess.DEVNULL,
        env=env,
    )
    if result.returncode != 0:
        error = (result.stderr or result.stdout or "claude failed").strip()[:500]
        raise RuntimeError(error)
    return result.stdout.strip()


def _run_codex(prompt: str, timeout: int) -> str:
    codex = engine_router.chatgpt_plus_path()
    if not codex:
        raise RuntimeError("codex CLI introuvable")
    codex_env = os.environ.copy()
    codex_home = Path(config.ATHOS_PATH) / "runtime" / "codex_room_home"
    codex_home.mkdir(parents=True, exist_ok=True)
    # Use a minimal Codex home for Room responder calls. It reuses auth/config
    # by symlink but avoids loading the full global skills tree, which can
    # contain Drive symlinks unavailable to launchd.
    for name in ("auth.json", "config.toml"):
        source = Path.home() / ".codex" / name
        target = codex_home / name
        if source.exists() and not target.exists():
            try:
                target.symlink_to(source)
            except FileExistsError:
                pass
    codex_env["CODEX_HOME"] = str(codex_home)
    with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as out:
        output_path = out.name
    try:
        result = subprocess.run(
            [
                codex,
                "exec",
                "--disable",
                "plugins",
                "--dangerously-bypass-approvals-and-sandbox",
                "--cd",
                str(config.ATHOS_PATH),
                "-o",
                output_path,
                prompt,
            ],
            cwd=str(config.ATHOS_PATH),
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            env=codex_env,
        )
        if result.returncode != 0:
            raw_error = (result.stderr or result.stdout or "codex failed").strip()
            if _is_usage_limit_error(raw_error):
                usage_line = next(
                    (line.strip() for line in raw_error.splitlines() if _is_usage_limit_error(line)),
                    raw_error,
                )
                raise RuntimeError(usage_line)
            raise RuntimeError(raw_error[:1200])
        try:
            reply = Path(output_path).read_text("utf-8").strip()
        except Exception:
            reply = ""
        return reply or result.stdout.strip()
    finally:
        try:
            Path(output_path).unlink()
        except OSError:
            pass


def _is_usage_limit_error(error: str) -> bool:
    text = str(error or "").lower()
    return "usage limit" in text or "you've hit your usage limit" in text


def _is_rate_limit_error(error: str) -> bool:
    text = str(error or "").lower()
    return "429" in text or "rate limit" in text


def _concise_engine_error(actor: str, error: str) -> str:
    raw = str(error or "").strip()
    if _is_usage_limit_error(raw):
        match = re.search(r"try again at ([^.\\n]+)", raw, re.IGNORECASE)
        retry = f" Réessai indiqué: {match.group(1).strip()}." if match else ""
        return f"{actor} indisponible: limite de session atteinte.{retry}"
    if _is_rate_limit_error(raw):
        return f"{actor} indisponible: rate limit temporaire. Réessayer plus tard."
    ignored_prefixes = ("Reading additional input from stdin",)
    first_line = next(
        (
            line.strip()
            for line in raw.splitlines()
            if line.strip() and not any(line.strip().startswith(prefix) for prefix in ignored_prefixes)
        ),
        raw,
    )
    return f"{actor} indisponible: {first_line[:240]}"


def _cooldown_for(actor: str) -> str | None:
    until, reason = _ENGINE_COOLDOWNS.get(actor, (0, ""))
    if until > time.time():
        return reason
    _ENGINE_COOLDOWNS.pop(actor, None)
    return None


def _set_cooldown(actor: str, reason: str) -> None:
    _ENGINE_COOLDOWNS[actor] = (time.time() + _USAGE_LIMIT_COOLDOWN_S, reason)


def _actor_for_engine(engine: str) -> str:
    key = str(engine or "").lower()
    if key in {"claude", "claude_code"}:
        return "claude"
    if key in {"codex", "chatgpt", "chatgpt_plus"}:
        return "codex"
    return key


def _existing_responder_entry(actor: str, task_id: str) -> dict | None:
    if not task_id:
        return None
    for entry in reversed(athos_room.get_thread(task_id=task_id, limit=80)):
        if entry.get("actor") != actor:
            continue
        meta = entry.get("meta") if isinstance(entry.get("meta"), dict) else {}
        if meta.get("source") != RESPONDER_META_SOURCE:
            continue
        if entry.get("type") in {"action", "result", "error"}:
            return entry
    return None


def respond(
    message: str,
    task_id: str = "",
    engines: Iterable[str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    force: bool = False,
) -> dict:
    """Ask requested engines to answer in ATHOS Room.

    This is intentionally bounded and non-mutating: it only posts Room messages.
    """
    requested = [str(e).lower() for e in (engines or ["claude", "codex"])]
    results = []
    for engine in requested:
        actor = _actor_for_engine(engine)
        cooldown_reason = _cooldown_for(actor)
        if cooldown_reason and not force:
            entry = athos_room.add(
                actor=actor,
                content=cooldown_reason,
                msg_type="error",
                task_id=task_id,
                status="cooldown",
                meta={"source": RESPONDER_META_SOURCE, "cooldown": True},
            )
            results.append({"engine": actor, "ok": False, "cooldown": True, "error": cooldown_reason, "entry": entry})
            continue
        existing = _existing_responder_entry(actor, task_id)
        if existing and not force:
            results.append({
                "engine": actor,
                "ok": True,
                "skipped": True,
                "reason": "already_has_room_responder_entry",
                "entry": existing,
            })
            continue
        athos_room.add(
            actor=actor,
            content=f"{actor} prépare une réponse Room...",
            msg_type="action",
            task_id=task_id,
            status="running",
            meta={"source": RESPONDER_META_SOURCE},
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
                meta={"source": RESPONDER_META_SOURCE},
            )
            results.append({"engine": actor, "ok": True, "entry": entry})
        except Exception as exc:
            message = _concise_engine_error(actor, str(exc))
            if _is_usage_limit_error(str(exc)) or _is_rate_limit_error(str(exc)):
                _set_cooldown(actor, message)
            entry = athos_room.add(
                actor=actor,
                content=message,
                msg_type="error",
                task_id=task_id,
                status="failed",
                meta={"source": RESPONDER_META_SOURCE},
            )
            results.append({"engine": actor, "ok": False, "error": message, "entry": entry})
    return {"ok": all(r["ok"] for r in results), "results": results}
