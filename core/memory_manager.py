"""Athos — Memory Manager | Drive R/W + session temp"""
from datetime import datetime

try:
    from . import config
except ImportError:
    import config

DRIVE = config.DRIVE
TEMP = config.TEMP
LOGS = config.LOGS

def _path(f): return DRIVE / f
def read(f):  p = _path(f); return p.read_text("utf-8") if p.exists() else ""
def write(f, c): _path(f).write_text(c, "utf-8")
def append(f, c):
    existing = read(f)
    write(f, existing + ("\n" if existing else "") + c)

def read_session():
    p = TEMP / "session_notes.mem"
    return p.read_text("utf-8") if p.exists() else ""

def write_session(content):
    TEMP.mkdir(exist_ok=True)
    p = TEMP / "session_notes.mem"
    existing = p.read_text("utf-8") if p.exists() else ""
    p.write_text(existing + ("\n" if existing else "") + content, "utf-8")

def clear_session():
    p = TEMP / "session_notes.mem"
    if p.exists(): p.unlink()

def log_today(content):
    LOGS.mkdir(exist_ok=True)
    p = LOGS / f"{datetime.now().strftime('%Y-%m-%d')}.mem"
    ts = datetime.now().strftime("%H%M")
    existing = p.read_text("utf-8") if p.exists() else f"§date:{datetime.now().strftime('%Y-%m-%d')}"
    p.write_text(existing + f"\n§t:{ts}|" + content, "utf-8")

def read_all_core():
    return {k: read(f) for k, f in {
        "id":       "athos_identity.mem",
        "behavior": "athos_behaviors.mem",
        "projects": "athos_projects.mem",
        "feedback": "athos_feedback.mem",
    }.items()}
