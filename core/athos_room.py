"""
ATHOS Room — fil canonique de conversation multi-moteurs.
Stocke chaque message/action/décision dans memory/athos_conversation.jsonl.
Tous les moteurs (Claude, Codex, ATHOS) lisent et écrivent ce fil.
"""
import json, time, uuid, threading
from pathlib import Path
from typing import Optional

_ROOM_FILE = Path(__file__).parent.parent / "memory" / "athos_conversation.jsonl"
_DRIVE_MIRROR = (
    Path.home()
    / "Library/CloudStorage/GoogleDrive-contact@ex-nihilo.agency"
    / "Mon Drive/CLAUDE AI/memory/athos_conversation.jsonl"
)
_lock = threading.Lock()

ACTORS   = {"clement", "athos", "claude", "codex"}
MSG_TYPES = {"message", "action", "result", "decision", "error", "checkpoint", "delegate", "attach"}
ACTOR_ALIASES = {
    "claude_code": "claude",
    "claude-code": "claude",
    "anthropic": "claude",
    "anthropic_api": "claude",
    "chatgpt": "codex",
    "chatgpt_plus": "codex",
    "chatgpt-plus": "codex",
    "codex_cli": "codex",
    "codex-cli": "codex",
    "openai": "codex",
}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _write_mirror(line: str):
    try:
        _DRIVE_MIRROR.parent.mkdir(parents=True, exist_ok=True)
        with _DRIVE_MIRROR.open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


def _actor(value: str) -> str:
    key = str(value or "athos").strip().lower()
    return ACTOR_ALIASES.get(key, key if key in ACTORS else "athos")


def _msg_type(value: str) -> str:
    key = str(value or "message").strip().lower()
    return key if key in MSG_TYPES else "message"


def _files(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value if str(v)]
    return [str(value)]


def _meta(value) -> dict:
    return value if isinstance(value, dict) else {}


def add(
    actor: str,
    content: str,
    msg_type: str = "message",
    task_id: Optional[str] = None,
    files: Optional[list] = None,
    status: Optional[str] = None,
    meta: Optional[dict] = None,
) -> dict:
    entry = {
        "id":       uuid.uuid4().hex[:12],
        "ts":       _now(),
        "actor":    _actor(actor),
        "type":     _msg_type(msg_type),
        "content":  content,
        "task_id":  task_id or "",
        "files":    _files(files),
        "status":   status or "",
        "meta":     _meta(meta),
    }
    line = json.dumps(entry, ensure_ascii=False) + "\n"
    with _lock:
        _ROOM_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _ROOM_FILE.open("a", encoding="utf-8") as f:
            f.write(line)
        _write_mirror(line)
    return entry


def get_thread(limit: int = 100, task_id: Optional[str] = None) -> list[dict]:
    if not _ROOM_FILE.exists():
        return []
    limit = max(1, min(int(limit or 100), 10_000))
    entries = []
    with _lock:
        with _ROOM_FILE.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if task_id and e.get("task_id") != task_id:
                        continue
                    entries.append(e)
                except Exception:
                    pass
    return entries[-limit:]


def get_context_for_engine(engine: str, limit: int = 40) -> str:
    """Retourne le fil formaté pour injection dans un prompt moteur."""
    thread = get_thread(limit=limit)
    if not thread:
        return "[ATHOS Room — fil vide]"
    lines = [f"=== ATHOS Room — {limit} derniers messages ==="]
    for e in thread:
        actor  = e.get("actor", "?").upper()
        ts     = e.get("ts", "")[-8:]  # HH:MM:SS
        mtype  = e.get("type", "message")
        content = e.get("content", "")
        files  = e.get("files", [])
        tag    = f"[{mtype.upper()}]" if mtype != "message" else ""
        fpart  = f" | fichiers: {', '.join(files)}" if files else ""
        lines.append(f"[{ts}] {actor}{tag}: {content}{fpart}")
    lines.append(f"=== Tu es {engine.upper()}. Réponds dans ce fil. ===")
    return "\n".join(lines)


def clear(task_id: Optional[str] = None):
    _ROOM_FILE.parent.mkdir(parents=True, exist_ok=True)
    if task_id:
        thread = get_thread(limit=10_000)
        kept = [e for e in thread if e.get("task_id") != task_id]
        with _lock:
            with _ROOM_FILE.open("w", encoding="utf-8") as f:
                for e in kept:
                    f.write(json.dumps(e, ensure_ascii=False) + "\n")
    else:
        with _lock:
            _ROOM_FILE.write_text("", encoding="utf-8")


def summary() -> dict:
    thread = get_thread(limit=10_000)
    actors = {}
    for e in thread:
        a = e.get("actor", "?")
        actors[a] = actors.get(a, 0) + 1
    return {
        "total":   len(thread),
        "actors":  actors,
        "last_ts": thread[-1]["ts"] if thread else None,
        "file":    str(_ROOM_FILE),
        "mirror":  str(_DRIVE_MIRROR) if _DRIVE_MIRROR.parent.exists() else "drive_offline",
    }


def health(limit: int = 100) -> dict:
    """Return a deterministic Room health report.

    This is intentionally local and engine-free: it lets ATHOS diagnose the
    Room without asking Claude/Codex and accidentally creating more messages.
    """
    thread = get_thread(limit=limit)
    actors: dict[str, int] = {}
    sources: dict[str, int] = {}
    tasks: dict[str, dict] = {}
    issues: list[dict] = []

    for entry in thread:
        actor = entry.get("actor", "?")
        actors[actor] = actors.get(actor, 0) + 1
        meta = entry.get("meta") if isinstance(entry.get("meta"), dict) else {}
        source = meta.get("source") or "manual"
        sources[source] = sources.get(source, 0) + 1
        task_id = entry.get("task_id") or "_no_task"
        task = tasks.setdefault(
            task_id,
            {
                "messages": 0,
                "actors": {},
                "auto_work_starts": 0,
                "auto_respond_starts": 0,
                "toolbus_events": 0,
                "errors": 0,
                "completed": 0,
                "last_ts": "",
            },
        )
        task["messages"] += 1
        task["actors"][actor] = task["actors"].get(actor, 0) + 1
        task["last_ts"] = entry.get("ts") or task["last_ts"]
        if entry.get("type") == "error":
            task["errors"] += 1
        if entry.get("status") == "completed" or entry.get("type") == "checkpoint":
            task["completed"] += 1
        if meta.get("source") == "room_auto_work" and "orchestration ATHOS lancée" in str(entry.get("content", "")):
            task["auto_work_starts"] += 1
        if meta.get("source") == "room_auto_respond" or "prépare une réponse Room" in str(entry.get("content", "")):
            task["auto_respond_starts"] += 1
        if meta.get("event") == "toolbus":
            task["toolbus_events"] += 1

    for task_id, task in tasks.items():
        if task_id == "_no_task":
            continue
        if task["auto_work_starts"] > 1:
            issues.append({
                "severity": "error",
                "task_id": task_id,
                "kind": "auto_work_loop",
                "detail": f"{task['auto_work_starts']} auto-work starts in one task",
            })
        if task["toolbus_events"] > 20:
            issues.append({
                "severity": "warning",
                "task_id": task_id,
                "kind": "toolbus_noise",
                "detail": f"{task['toolbus_events']} raw toolbus events in Room",
            })
        if task["messages"] > 80 and task["completed"] == 0:
            issues.append({
                "severity": "warning",
                "task_id": task_id,
                "kind": "large_uncompleted_task",
                "detail": f"{task['messages']} messages without checkpoint/completion",
            })

    recent_tasks = [
        {"task_id": task_id, **task}
        for task_id, task in tasks.items()
        if task_id != "_no_task"
    ][-20:]
    ok = not any(issue["severity"] == "error" for issue in issues)
    return {
        "ok": ok,
        "status": "healthy" if ok else "unhealthy",
        "checked_messages": len(thread),
        "actors": actors,
        "sources": sources,
        "issues": issues,
        "recent_tasks": recent_tasks,
        "summary": summary(),
    }
