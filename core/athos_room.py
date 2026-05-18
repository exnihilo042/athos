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


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _write_mirror(line: str):
    try:
        if _DRIVE_MIRROR.parent.exists():
            with _DRIVE_MIRROR.open("a", encoding="utf-8") as f:
                f.write(line)
    except Exception:
        pass


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
        "actor":    actor if actor in ACTORS else "athos",
        "type":     msg_type if msg_type in MSG_TYPES else "message",
        "content":  content,
        "task_id":  task_id or "",
        "files":    files or [],
        "status":   status or "",
        "meta":     meta or {},
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
