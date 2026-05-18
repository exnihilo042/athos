"""
ATHOS — agentmemory server manager.
Starts agentmemory serve in background at ATHOS boot if not already running.
Port default: 8765 (agentmemory default).
"""
import subprocess, threading, socket, os, time
from pathlib import Path

VENV312   = Path(__file__).parent.parent / "venv312"
PYTHON    = VENV312 / "bin" / "python"
PORT      = 8765
_LOG      = Path(__file__).parent.parent / "logs" / "agentmemory.log"
_PID_FILE = Path(__file__).parent.parent / ".agentmemory.pid"


def _is_running() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", PORT)) == 0


def _start():
    _LOG.parent.mkdir(parents=True, exist_ok=True)
    with _LOG.open("a") as f:
        proc = subprocess.Popen(
            [str(PYTHON), "-m", "agentmemory", "serve", "--port", str(PORT)],
            stdout=f, stderr=subprocess.STDOUT,
            start_new_session=True
        )
        _PID_FILE.write_text(str(proc.pid))
        time.sleep(1.5)
        if _is_running():
            print(f"  [ATHOS] agentmemory serve → localhost:{PORT} (PID {proc.pid})")
        else:
            print(f"  [ATHOS] agentmemory serve started (PID {proc.pid}), warming up...")


def ensure_running():
    """Call at server boot — starts agentmemory if not already listening."""
    if not PYTHON.exists():
        print("  [ATHOS] agentmemory: venv312 not found, skipping")
        return
    if _is_running():
        print(f"  [ATHOS] agentmemory already running on :{PORT}")
        return
    t = threading.Thread(target=_start, daemon=True, name="agentmemory-server")
    t.start()
    t.join(timeout=5)


def stop():
    """Gracefully stop agentmemory if we started it."""
    if _PID_FILE.exists():
        try:
            pid = int(_PID_FILE.read_text())
            os.kill(pid, 15)
            _PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass
