import importlib
import json
import os
import sys
import threading
import urllib.error
import urllib.request


def _load_server(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path))
    monkeypatch.setenv("ATHOS_BIND_HOST", "127.0.0.1")
    monkeypatch.delenv("ATHOS_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("ATHOS_REQUIRE_TOKEN", raising=False)
    root = os.getcwd()
    voice_path = os.path.join(root, "voice")
    core_path = os.path.join(root, "core")
    for path in (voice_path, core_path):
        if path not in sys.path:
            sys.path.insert(0, path)
    for name in ("config", "session_kernel", "sync_manager", "session_compactor", "athos_room", "attach_protocol", "server"):
        sys.modules.pop(name, None)
    import voice.server as server
    importlib.reload(server)
    server.config.ATHOS_TOKEN_ENFORCED = False
    server.ACCESS_TOKEN = ""
    server.athos_room._ROOM_FILE = tmp_path / "athos_conversation.jsonl"
    server.athos_room._DRIVE_MIRROR = tmp_path / "drive" / "athos_conversation.jsonl"
    server.session_kernel.SESSION_FILE = tmp_path / "athos_session_kernel.jsonl"
    server.sync_manager.OUTBOX_FILE = tmp_path / "athos_sync_outbox.jsonl"
    server.session_compactor.SUMMARY_FILE = tmp_path / "athos_session_summary.mem"

    # The route handlers call functions imported from attach_protocol at import
    # time. Keep that module pointed at the same temporary files.
    import attach_protocol
    attach_protocol.athos_room._ROOM_FILE = server.athos_room._ROOM_FILE
    attach_protocol.athos_room._DRIVE_MIRROR = server.athos_room._DRIVE_MIRROR
    attach_protocol.session_kernel.SESSION_FILE = server.session_kernel.SESSION_FILE
    return server


class _RunningServer:
    def __init__(self, server_module):
        self.httpd = server_module.ThreadingHTTPServer(("127.0.0.1", 0), server_module.Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def post(self, path, body):
        req = urllib.request.Request(
            self.base + path,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)


def _server(tmp_path, monkeypatch):
    module = _load_server(tmp_path, monkeypatch)
    running = _RunningServer(module)
    return module, running


def test_message_and_conversation_endpoints_roundtrip(tmp_path, monkeypatch):
    _, srv = _server(tmp_path, monkeypatch)
    try:
        status, body = srv.post("/api/message", {
            "actor": "clement",
            "content": "hello room",
            "task_id": "endpoint-a",
        })
        assert status == 200
        assert body["ok"] is True
        assert body["entry"]["actor"] == "clement"

        status, body = srv.post("/api/conversation", {"action": "get", "task_id": "endpoint-a"})
        assert status == 200
        assert [row["content"] for row in body["thread"]] == ["hello room"]

        status, body = srv.post("/api/conversation", {"action": "context", "engine": "codex", "limit": 5})
        assert status == 200
        assert "CLEMENT: hello room" in body["context"]
    finally:
        srv.close()


def test_message_endpoint_requires_content(tmp_path, monkeypatch):
    _, srv = _server(tmp_path, monkeypatch)
    try:
        status, body = srv.post("/api/message", {"actor": "codex"})
        assert status == 400
        assert body["ok"] is False
        assert "content" in body["error"]
    finally:
        srv.close()


def test_conversation_clear_only_removes_task_id(tmp_path, monkeypatch):
    _, srv = _server(tmp_path, monkeypatch)
    try:
        srv.post("/api/message", {"actor": "codex", "content": "keep", "task_id": "keep"})
        srv.post("/api/message", {"actor": "claude", "content": "drop", "task_id": "drop"})

        status, body = srv.post("/api/conversation", {"action": "clear", "task_id": "drop"})
        assert status == 200
        assert body["ok"] is True

        status, body = srv.post("/api/conversation", {"action": "get", "limit": 10})
        assert status == 200
        assert [row["content"] for row in body["thread"]] == ["keep"]
    finally:
        srv.close()


def test_attach_delegate_report_checkpoint_endpoints_write_room(tmp_path, monkeypatch):
    _, srv = _server(tmp_path, monkeypatch)
    try:
        status, attach = srv.post("/api/attach", {"engine": "codex", "scope": "endpoint-test"})
        assert status == 200
        assert attach["ok"] is True

        status, delegate = srv.post("/api/delegate", {
            "attach_id": attach["attach_id"],
            "engine": "codex",
            "request": "ATHOS_STATUS",
        })
        assert status == 200
        assert delegate["decision"] == "named_protocol:ATHOS_STATUS"

        status, report = srv.post("/api/report", {
            "attach_id": attach["attach_id"],
            "engine": "codex",
            "summary": "endpoint report done",
            "status": "completed",
            "files": ["tests/test_voice_room_endpoints.py"],
        })
        assert status == 200
        assert report["ok"] is True

        status, checkpoint = srv.post("/api/checkpoint", {
            "actor": "codex",
            "goal": "endpoint checkpoint",
            "decisions": ["room endpoint verified"],
            "tasks": ["message", "conversation", "attach", "delegate", "report"],
            "files": ["tests/test_voice_room_endpoints.py"],
        })
        assert status == 200
        assert checkpoint["goal"] == "endpoint checkpoint"

        status, body = srv.post("/api/conversation", {"action": "get", "limit": 20})
        assert status == 200
        types = [row["type"] for row in body["thread"]]
        contents = [row["content"] for row in body["thread"]]
        assert "attach" in types
        assert "delegate" in types
        assert "result" in types
        assert "checkpoint" in types
        assert "endpoint report done" in contents
        assert "endpoint checkpoint" in contents
    finally:
        srv.close()
