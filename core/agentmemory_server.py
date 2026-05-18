"""
ATHOS — agentmemory REST server wrapper.
Lance un micro-serveur FastAPI sur :8765 qui expose agentmemory via HTTP.
Utilisé par Claude Code hooks, Codex, et l'UI ATHOS.

Endpoints :
  POST /memories          — créer une mémoire
  GET  /memories          — lister (category optionnelle)
  POST /memories/search   — recherche sémantique
  DELETE /memories/{id}   — supprimer
  GET  /health            — statut
"""
import threading, socket, subprocess, sys, os
from pathlib import Path

PORT      = 8765
_PID_FILE = Path(__file__).parent.parent / ".agentmemory.pid"
_LOG      = Path(__file__).parent.parent / "logs" / "agentmemory.log"
VENV312   = Path(__file__).parent.parent / "venv312"
PYTHON    = VENV312 / "bin" / "python"


def _is_running() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", PORT)) == 0


def _start_server():
    """Lance le serveur FastAPI en subprocess isolé."""
    server_script = Path(__file__).parent / "agentmemory_api.py"
    _LOG.parent.mkdir(parents=True, exist_ok=True)
    with _LOG.open("a") as f:
        proc = subprocess.Popen(
            [str(PYTHON), str(server_script)],
            stdout=f, stderr=subprocess.STDOUT,
            start_new_session=True,
            env={**os.environ, "PYTHONPATH": str(VENV312 / "lib" / "python3.12" / "site-packages")}
        )
        _PID_FILE.write_text(str(proc.pid))
    import time; time.sleep(2)
    if _is_running():
        print(f"  [ATHOS] agentmemory API → localhost:{PORT} (PID {proc.pid})")
    else:
        print(f"  [ATHOS] agentmemory: démarrage en cours… (PID {proc.pid})")


def ensure_running():
    """Appeler au boot ATHOS — démarre le serveur si absent."""
    if not PYTHON.exists():
        print("  [ATHOS] agentmemory: venv312 introuvable, skip")
        return
    if _is_running():
        print(f"  [ATHOS] agentmemory déjà actif sur :{PORT}")
        return
    t = threading.Thread(target=_start_server, daemon=True, name="agentmemory-boot")
    t.start()
    t.join(timeout=6)


def stop():
    if _PID_FILE.exists():
        try:
            pid = int(_PID_FILE.read_text())
            os.kill(pid, 15)
            _PID_FILE.unlink(missing_ok=True)
            print(f"  [ATHOS] agentmemory stoppé (PID {pid})")
        except Exception:
            pass
