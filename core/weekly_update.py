"""
ATHOS weekly skill updater — runs update_skills.sh on first server boot of the week.
Stores last-run timestamp in .last_skill_update to avoid multiple runs per week.
"""
import subprocess, threading
from datetime import datetime, timedelta
from pathlib import Path

_STAMP_FILE = Path(__file__).parent.parent / ".last_skill_update"
_SCRIPT     = Path(__file__).parent.parent / "scripts" / "update_skills.sh"
_LOG        = Path(__file__).parent.parent / "logs" / "weekly_update.log"


def _due() -> bool:
    if not _STAMP_FILE.exists():
        return True
    try:
        last = datetime.fromisoformat(_STAMP_FILE.read_text().strip())
        return datetime.now() - last >= timedelta(days=7)
    except Exception:
        return True


def _run():
    _LOG.parent.mkdir(parents=True, exist_ok=True)
    with _LOG.open("a") as f:
        f.write(f"\n[{datetime.now().isoformat()}] weekly skill update started\n")
        result = subprocess.run(
            ["bash", str(_SCRIPT)],
            stdout=f, stderr=subprocess.STDOUT,
            timeout=300
        )
        status = "OK" if result.returncode == 0 else f"FAILED (exit {result.returncode})"
        f.write(f"[{datetime.now().isoformat()}] {status}\n")
    if result.returncode == 0:
        _STAMP_FILE.write_text(datetime.now().isoformat())


def check_and_run():
    """Call at server boot — runs in background thread if update is due."""
    if not _due():
        return
    if not _SCRIPT.exists():
        return
    t = threading.Thread(target=_run, daemon=True, name="weekly-skill-update")
    t.start()
    print("  [ATHOS] Weekly skill update scheduled (background)")
