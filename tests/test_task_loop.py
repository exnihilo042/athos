import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from core.task_loop import RoomReporter, command_is_risky, resolve_athos_token, run_task_loop


def _reporter(tmp_path):
    return RoomReporter(
        actor="codex",
        athos_url="http://127.0.0.1:9",
        memory_dir=tmp_path / "memory",
        timeout=0.05,
    )


def _offline_rows(tmp_path):
    files = list((tmp_path / "memory").glob("room_offline_*.jsonl"))
    assert files
    return [json.loads(line) for line in files[0].read_text("utf-8").splitlines()]


def test_task_loop_runs_commands_and_reports_offline(tmp_path):
    result = run_task_loop(
        "verify loop",
        [f"{sys.executable} -c \"print('ok-loop')\""],
        task_id="task-test",
        cwd=tmp_path,
        reporter=_reporter(tmp_path),
        timeout=5,
    )

    assert result.status == "completed"
    rows = _offline_rows(tmp_path)
    assert rows[0]["type"] == "action"
    assert rows[0]["task_id"] == "task-test"
    assert any("ok-loop" in row["content"] for row in rows)
    assert rows[-1]["type"] == "checkpoint"
    assert rows[-1]["status"] == "completed"


def test_task_loop_blocks_risky_command_without_allow_mutation(tmp_path):
    result = run_task_loop(
        "avoid danger",
        ["git push origin main"],
        task_id="task-risk",
        cwd=tmp_path,
        reporter=_reporter(tmp_path),
    )

    assert result.status == "blocked"
    assert result.stop_reason == "risky_command_requires_allow_mutation"
    rows = _offline_rows(tmp_path)
    assert any(row["status"] == "blocked" for row in rows)


def test_task_loop_stops_on_command_failure(tmp_path):
    result = run_task_loop(
        "fail fast",
        [
            f"{sys.executable} -c \"print('before-fail')\"",
            f"{sys.executable} -c \"import sys; print('bad'); sys.exit(3)\"",
            f"{sys.executable} -c \"print('must-not-run')\"",
        ],
        task_id="task-fail",
        cwd=tmp_path,
        reporter=_reporter(tmp_path),
        timeout=5,
    )

    assert result.status == "failed"
    assert result.stop_reason == "command_failed:2"
    rows = _offline_rows(tmp_path)
    assert any("before-fail" in row["content"] for row in rows)
    assert any("bad" in row["content"] for row in rows)
    assert not any("must-not-run" in row["content"] for row in rows)


def test_task_loop_blocks_empty_plan(tmp_path):
    result = run_task_loop(
        "nothing",
        [],
        task_id="task-empty",
        reporter=_reporter(tmp_path),
    )

    assert result.status == "blocked"
    assert result.stop_reason == "no_commands"


def test_command_is_risky_normalizes_spaces_and_case():
    assert command_is_risky("GIT   PUSH origin main")
    assert command_is_risky("shopify theme push --store x")
    assert not command_is_risky("pytest -q")


def test_room_reporter_sends_auth_token_for_live_room(tmp_path, monkeypatch):
    seen = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            seen["path"] = self.path
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
        monkeypatch.setenv("ATHOS_TOKEN", "task-token")
        reporter = RoomReporter(
            actor="codex",
            athos_url=f"http://127.0.0.1:{server.server_address[1]}",
            memory_dir=tmp_path / "memory",
        )
        result = reporter.post("result", "live task result", "task-live", status="completed")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result["mode"] == "live"
    assert seen["path"] == "/api/message"
    assert seen["auth"] == "Bearer task-token"
    assert seen["body"]["task_id"] == "task-live"
    assert not list((tmp_path / "memory").glob("room_offline_*.jsonl"))


def test_resolve_athos_token_reads_env_file_when_env_absent(tmp_path, monkeypatch):
    monkeypatch.delenv("ATHOS_TOKEN", raising=False)
    monkeypatch.delenv("ATHOS_ACCESS_TOKEN", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("OTHER=x\nATHOS_ACCESS_TOKEN='file-token'\n", encoding="utf-8")

    assert resolve_athos_token(env_file) == "file-token"
