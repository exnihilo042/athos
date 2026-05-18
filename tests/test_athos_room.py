import importlib
import json
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


def _room(tmp_path, monkeypatch):
    import core.athos_room as athos_room
    importlib.reload(athos_room)
    athos_room._ROOM_FILE = tmp_path / "memory" / "athos_conversation.jsonl"
    athos_room._DRIVE_MIRROR = tmp_path / "drive" / "athos_conversation.jsonl"
    return athos_room


def test_room_adds_reads_context_and_mirrors(tmp_path, monkeypatch):
    room = _room(tmp_path, monkeypatch)

    first = room.add("clement", "go", task_id="task-a")
    second = room.add(
        "claude_code",
        "patch done",
        msg_type="result",
        task_id="task-a",
        files="core/athos_room.py",
        meta="ignored",
    )

    assert first["actor"] == "clement"
    assert second["actor"] == "claude"
    assert second["files"] == ["core/athos_room.py"]
    assert second["meta"] == {}
    assert [e["content"] for e in room.get_thread(limit=10)] == ["go", "patch done"]
    assert room.get_thread(task_id="task-a")[-1]["content"] == "patch done"
    assert "CLAUDE[RESULT]: patch done" in room.get_context_for_engine("codex")
    assert room.summary()["actors"] == {"clement": 1, "claude": 1}
    assert room._DRIVE_MIRROR.exists()
    assert room._DRIVE_MIRROR.read_text("utf-8").count("\n") == 2


def test_room_ignores_bad_lines_and_clears_one_task(tmp_path, monkeypatch):
    room = _room(tmp_path, monkeypatch)
    room.add("codex", "keep", task_id="keep")
    room.add("athos", "drop", task_id="drop")
    with room._ROOM_FILE.open("a", encoding="utf-8") as f:
        f.write("{bad json}\n")

    room.clear(task_id="drop")

    thread = room.get_thread(limit=10)
    assert len(thread) == 1
    assert thread[0]["content"] == "keep"


def test_room_clear_before_file_exists_is_safe(tmp_path, monkeypatch):
    room = _room(tmp_path, monkeypatch)

    room.clear()

    assert room.get_thread() == []
    assert room._ROOM_FILE.exists()


def test_athos_report_offline_fallback_writes_jsonl(tmp_path):
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["ATHOS_URL"] = "http://127.0.0.1:9"
    script = os.path.join(os.getcwd(), "scripts", "athos_report.sh")

    result = subprocess.run(
        [script, "codex", "result", "done", "file with spaces.liquid", "quote\"file"],
        cwd=os.getcwd(),
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0
    fallback_dir = tmp_path / "Sites" / "athos" / "memory"
    files = list(fallback_dir.glob("room_offline_*.jsonl"))
    assert files
    payload = json.loads(files[0].read_text("utf-8").strip())
    assert payload["actor"] == "codex"
    assert payload["type"] == "result"
    assert payload["files"] == ["file with spaces.liquid", 'quote"file']
    assert payload["offline"] is True


def test_athos_report_sends_auth_token_when_configured(tmp_path):
    seen = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            seen["auth"] = self.headers.get("Authorization")
            seen["body"] = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = os.environ.copy()
        env["ATHOS_URL"] = f"http://127.0.0.1:{server.server_address[1]}"
        env["ATHOS_TOKEN"] = "test-token"
        script = os.path.join(os.getcwd(), "scripts", "athos_report.sh")

        result = subprocess.run(
            [script, "codex", "result", "live auth ok", "core/athos_room.py"],
            cwd=os.getcwd(),
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result.returncode == 0
    assert "ATHOS Room OK" in result.stdout
    assert seen["auth"] == "Bearer test-token"
    assert seen["body"]["actor"] == "codex"
    assert seen["body"]["files"] == ["core/athos_room.py"]
