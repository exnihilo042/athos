import importlib
import json
import os
import sys
import threading
import socket
import urllib.error
import urllib.request


def _load_server(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path))
    monkeypatch.setenv("ATHOS_BIND_HOST", "127.0.0.1")
    monkeypatch.setenv("ATHOS_ROOM_AUTO_RESPOND", "false")
    monkeypatch.setenv("ATHOS_ROOM_AUTO_WORK", "false")
    monkeypatch.delenv("ATHOS_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("ATHOS_REQUIRE_TOKEN", raising=False)
    root = os.getcwd()
    voice_path = os.path.join(root, "voice")
    core_path = os.path.join(root, "core")
    for path in (voice_path, core_path):
        if path not in sys.path:
            sys.path.insert(0, path)
    for name in ("config", "session_kernel", "sync_manager", "task_queue", "session_compactor", "athos_room", "attach_protocol", "server"):
        sys.modules.pop(name, None)
    import voice.server as server
    importlib.reload(server)
    server.config.ATHOS_TOKEN_ENFORCED = False
    server.ACCESS_TOKEN = ""
    server.athos_room._ROOM_FILE = tmp_path / "athos_conversation.jsonl"
    server.athos_room._DRIVE_MIRROR = tmp_path / "drive" / "athos_conversation.jsonl"
    server.session_kernel.SESSION_FILE = tmp_path / "athos_session_kernel.jsonl"
    server.sync_manager.OUTBOX_FILE = tmp_path / "athos_sync_outbox.jsonl"
    server.task_queue.TASK_QUEUE_FILE = tmp_path / "athos_task_queue.json"
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

        status, body = srv.post("/api/conversation", {"action": "health", "limit": 50})
        assert status == 200
        assert body["status"] == "healthy"
        assert body["checked_messages"] == 1

        status, body = srv.post("/api/conversation", {"action": "runtime"})
        assert status == 200
        assert body["ok"] is True
        assert body["auto_response"]["enabled"] is False
        assert body["auto_response"]["active_count"] == 0
        assert body["auto_work"]["enabled"] is False
        assert body["auto_work"]["active_count"] == 0
        assert body["task_queue"]["total"] == 0
        assert "responders" in body
        assert set(body["responders"]["actors"]) == {"claude", "codex"}
    finally:
        srv.close()


def test_tasks_endpoint_lifecycle(tmp_path, monkeypatch):
    _, srv = _server(tmp_path, monkeypatch)
    try:
        status, body = srv.post("/api/tasks", {
            "action": "create",
            "task_id": "api-task",
            "title": "API task",
            "content": "queue pilotable",
        })
        assert status == 200
        assert body["ok"] is True
        assert body["task"]["status"] == "queued"

        status, body = srv.post("/api/tasks", {"action": "pause", "task_id": "api-task", "reason": "operator"})
        assert status == 200
        assert body["task"]["status"] == "paused"

        status, body = srv.post("/api/tasks", {"action": "retry", "task_id": "api-task"})
        assert status == 200
        assert body["task"]["status"] == "queued"
        assert body["task"]["retry_count"] == 1

        status, body = srv.post("/api/tasks", {"action": "cancel", "task_id": "api-task", "reason": "done elsewhere"})
        assert status == 200
        assert body["task"]["status"] == "cancelled"

        status, body = srv.post("/api/tasks", {"action": "list"})
        assert status == 200
        assert body["summary"]["counts"]["cancelled"] == 1
    finally:
        srv.close()


def test_memory_note_endpoint_writes_session_note(tmp_path, monkeypatch):
    _, srv = _server(tmp_path, monkeypatch)
    import memory_manager
    memory_manager.TEMP = tmp_path / "temp"
    try:
        status, body = srv.post("/api/memory/note", {
            "note": "§session:2026-05-20|engine=codex|result=note_endpoint_ok",
        })
        assert status == 200
        assert body["ok"] is True
        assert "note_endpoint_ok" in (tmp_path / "temp" / "session_notes.mem").read_text("utf-8")

        status, body = srv.post("/api/memory/note", {"note": ""})
        assert status == 400
        assert body["ok"] is False
    finally:
        srv.close()


def test_report_endpoint_daily_payload_is_dashboard_ready(tmp_path, monkeypatch):
    _, srv = _server(tmp_path, monkeypatch)
    try:
        status, body = srv.post("/api/report", {"type": "daily"})
        assert status == 200
        assert body["ok"] is True
        assert body["type"] == "daily"
        assert body["date"]
        assert body["brief"]
        assert isinstance(body["sections"], list)
        assert {section["title"] for section in body["sections"]} >= {"Session", "Task queue", "Responders"}
    finally:
        srv.close()


def test_autonomous_loop_alias_status_and_stop_are_idempotent(tmp_path, monkeypatch):
    _, srv = _server(tmp_path, monkeypatch)
    try:
        status, body = srv.post("/api/autonomous_loop", {"action": "status"})
        assert status == 200
        assert body["running"] is False
        assert "policy" in body

        status, body = srv.post("/api/autonomous_loop", {"action": "stop"})
        assert status == 200
        assert body["ok"] is True
        assert body["running"] is False
    finally:
        srv.close()


def test_events_endpoint_emits_status_seed_event(tmp_path, monkeypatch):
    _, srv = _server(tmp_path, monkeypatch)
    req = urllib.request.Request(
        srv.base + "/api/events",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            assert response.status == 200
            assert response.headers.get("Content-Type") == "text/event-stream"
            first = response.readline().decode("utf-8")
            second = response.readline().decode("utf-8")
            assert first == "event: status\n"
            assert second.startswith("data: ")
            payload = json.loads(second.removeprefix("data: "))
            assert "session" in payload
            assert "capability_graph" in payload
    except socket.timeout:
        raise AssertionError("SSE seed event was not emitted before timeout")
    finally:
        srv.close()


def test_message_endpoint_auto_triggers_room_responders(tmp_path, monkeypatch):
    module, srv = _server(tmp_path, monkeypatch)
    calls = []

    class ImmediateThread:
        def __init__(self, target, args=(), kwargs=None, name=None, daemon=None):
            self.target = target
            self.args = args
            self.kwargs = kwargs or {}
            self.name = name
            self.daemon = daemon

        def start(self):
            self.target(*self.args, **self.kwargs)

    def fake_respond(message, task_id="", engines=None, timeout=45):
        calls.append({
            "message": message,
            "task_id": task_id,
            "engines": engines,
            "timeout": timeout,
        })
        module.athos_room.add(
            actor="claude",
            content="auto claude",
            msg_type="result",
            task_id=task_id,
            status="completed",
            meta={"source": "test"},
        )
        module.athos_room.add(
            actor="codex",
            content="auto codex",
            msg_type="result",
            task_id=task_id,
            status="completed",
            meta={"source": "test"},
        )
        return {"ok": True, "results": [{"engine": "claude", "ok": True}, {"engine": "codex", "ok": True}]}

    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_RESPOND", True)
    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_RESPOND_ENGINES", ["claude", "codex"])
    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_RESPOND_TIMEOUT", 7)
    monkeypatch.setattr(module.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(module.room_responders, "respond", fake_respond)

    try:
        status, body = srv.post("/api/message", {
            "actor": "clement",
            "content": "répondez sans relance",
            "task_id": "auto-room",
        })
        assert status == 200
        assert body["ok"] is True
        assert body["auto_response"]["scheduled"] is True
        assert calls == [{
            "message": "répondez sans relance",
            "task_id": "auto-room",
            "engines": ["claude", "codex"],
            "timeout": 7,
        }]

        status, thread = srv.post("/api/conversation", {"action": "get", "task_id": "auto-room", "limit": 5})
        assert status == 200
        assert [(row["actor"], row["content"]) for row in thread["thread"]] == [
            ("clement", "répondez sans relance"),
            ("claude", "auto claude"),
            ("codex", "auto codex"),
        ]
    finally:
        srv.close()


def test_message_endpoint_runs_bounded_coordination_round_when_requested(tmp_path, monkeypatch):
    module, srv = _server(tmp_path, monkeypatch)
    calls = []

    class ImmediateThread:
        def __init__(self, target, args=(), kwargs=None, name=None, daemon=None):
            self.target = target
            self.args = args
            self.kwargs = kwargs or {}

        def start(self):
            self.target(*self.args, **self.kwargs)

    def fake_respond(message, task_id="", engines=None, timeout=45, force=False):
        calls.append({"message": message, "task_id": task_id, "force": force})
        module.athos_room.add(
            actor="claude",
            content="coord claude" if force else "initial claude",
            msg_type="result",
            task_id=task_id,
            status="completed",
            meta={"source": "room_responder"},
        )
        module.athos_room.add(
            actor="codex",
            content="coord codex" if force else "initial codex",
            msg_type="result",
            task_id=task_id,
            status="completed",
            meta={"source": "room_responder"},
        )
        return {"ok": True, "results": [{"engine": "claude", "ok": True}, {"engine": "codex", "ok": True}]}

    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_RESPOND", True)
    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_COORDINATION_ROUNDS", 1)
    monkeypatch.setattr(module.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(module.room_responders, "respond", fake_respond)

    try:
        status, body = srv.post("/api/message", {
            "actor": "clement",
            "content": "continuez à discuter entre vous",
            "task_id": "coord-room",
        })

        assert status == 200
        assert body["auto_response"]["scheduled"] is True
        assert len(calls) == 2
        assert calls[0]["force"] is False
        assert calls[1]["force"] is True
        assert "Coordination autonome Room" in calls[1]["message"]

        status, thread = srv.post("/api/conversation", {"action": "get", "task_id": "coord-room", "limit": 10})
        assert status == 200
        assert [row["content"] for row in thread["thread"]] == [
            "continuez à discuter entre vous",
            "initial claude",
            "initial codex",
            "coordination Room tour 1/1",
            "coord claude",
            "coord codex",
        ]
    finally:
        srv.close()


def test_message_endpoint_runs_coordinated_work_cycle_for_work_intent(tmp_path, monkeypatch):
    module, srv = _server(tmp_path, monkeypatch)
    responder_calls = []
    engine_prompts = []

    class ImmediateThread:
        def __init__(self, target, args=(), kwargs=None, name=None, daemon=None):
            self.target = target
            self.args = args
            self.kwargs = kwargs or {}
            self._alive = False

        def start(self):
            self._alive = True
            try:
                self.target(*self.args, **self.kwargs)
            finally:
                self._alive = False

        def join(self, timeout=None):
            return None

        def is_alive(self):
            return self._alive

    class FakeAthosEngine:
        def __init__(self, mem, router, sse, permission_checker):
            self.sse = sse

        def respond(self, message):
            engine_prompts.append(message)
            self.sse({"thinking": {"kind": "routing", "text": "objectif transformé en action"}})
            self.sse({"action": "fake_edit", "label": "tests", "result": "ok"})
            return "travail concret terminé"

    def fake_respond(message, task_id="", engines=None, timeout=45, force=False):
        responder_calls.append({
            "message": message,
            "task_id": task_id,
            "engines": engines,
            "timeout": timeout,
            "force": force,
        })
        actor = "claude" if len(responder_calls) == 1 else "codex"
        module.athos_room.add(
            actor=actor,
            content="plan reçu" if len(responder_calls) == 1 else "review terminé",
            msg_type="result",
            task_id=task_id,
            status="completed",
            meta={"source": "test_responder"},
        )
        return {"ok": True, "results": [{"engine": actor, "ok": True}]}

    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_WORK", True)
    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_WORK_TIMEOUT", 5)
    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_WORK_REVIEW", True)
    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_WORK_RESPONDER_TIMEOUT", 3)
    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_RESPOND_ENGINES", ["claude", "codex"])
    monkeypatch.setattr(module.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(module, "AthosEngine", FakeAthosEngine)
    monkeypatch.setattr(module.room_responders, "respond", fake_respond)
    monkeypatch.setattr(module, "extract_and_save_async", lambda *args, **kwargs: None)

    try:
        status, body = srv.post("/api/message", {
            "actor": "clement",
            "content": "finissez moi ce projet",
            "task_id": "natural-work",
        })
        assert status == 200
        assert body["auto_work"]["scheduled"] is True
        assert body["auto_response"]["reason"] == "handled_by_auto_work"
        assert len(responder_calls) == 2
        assert responder_calls[0]["force"] is True
        assert responder_calls[1]["force"] is True
        assert "Phase PLAN" in responder_calls[0]["message"]
        assert "Phase REVIEW" in responder_calls[1]["message"]
        assert "mode exécution Room" in engine_prompts[0]
        assert "Ne dis jamais seulement 'lance quand tu veux'" in engine_prompts[0]

        status, thread = srv.post("/api/conversation", {"action": "get", "task_id": "natural-work", "limit": 20})
        assert status == 200
        contents = [row["content"] for row in thread["thread"]]
        assert "finissez moi ce projet" in contents
        assert "orchestration ATHOS lancée depuis la Room" in contents
        assert "routing: objectif transformé en action" in contents
        assert "fake_edit: tests ok" in contents
        assert "travail concret terminé" in contents
        assert contents[-1].startswith("orchestration ATHOS terminée")

        status, tasks = srv.post("/api/tasks", {"action": "get", "task_id": "natural-work"})
        assert status == 200
        assert tasks["ok"] is True
        assert tasks["task"]["status"] == "completed"
        assert tasks["task"]["kind"] == "room_auto_work"
        assert tasks["task"]["result"] == "travail concret terminé"
    finally:
        srv.close()


def test_message_endpoint_does_not_auto_work_for_presence_check(tmp_path, monkeypatch):
    module, srv = _server(tmp_path, monkeypatch)
    called = {"engine": False}

    class FakeAthosEngine:
        def __init__(self, *args, **kwargs):
            called["engine"] = True

    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_WORK", True)
    monkeypatch.setattr(module, "AthosEngine", FakeAthosEngine)

    try:
        status, body = srv.post("/api/message", {
            "actor": "clement",
            "content": "vous êtes là ?",
            "task_id": "presence",
        })
        assert status == 200
        assert body["auto_work"]["reason"] == "not_work_intent"
        assert called["engine"] is False
    finally:
        srv.close()


def test_message_endpoint_does_not_autorun_replayed_messages(tmp_path, monkeypatch):
    module, srv = _server(tmp_path, monkeypatch)
    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_WORK", True)
    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_RESPOND", True)

    try:
        status, body = srv.post("/api/message", {
            "actor": "clement",
            "content": "finissez ce replay",
            "task_id": "replayed",
            "meta": {"replayed_from": "offline_fallback"},
        })
        assert status == 200
        assert body["auto_work"]["reason"] == "replay_no_autowork"
        assert body["auto_response"]["reason"] == "replay_no_autorespond"
    finally:
        srv.close()


def test_message_endpoint_limits_room_toolbus_noise(tmp_path, monkeypatch):
    module, srv = _server(tmp_path, monkeypatch)

    class ImmediateThread:
        def __init__(self, target, args=(), kwargs=None, name=None, daemon=None):
            self.target = target
            self.args = args
            self.kwargs = kwargs or {}
            self._alive = False

        def start(self):
            self._alive = True
            try:
                self.target(*self.args, **self.kwargs)
            finally:
                self._alive = False

        def join(self, timeout=None):
            return None

        def is_alive(self):
            return self._alive

    class FakeAthosEngine:
        def __init__(self, mem, router, sse, permission_checker):
            self.sse = sse

        def respond(self, message):
            for i in range(10):
                self.sse({"toolbus": "stderr", "chunk": f"noisy line {i}"})
            return "done"

    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_WORK", True)
    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_WORK_REVIEW", False)
    monkeypatch.setattr(module.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(module, "AthosEngine", FakeAthosEngine)
    monkeypatch.setattr(module.room_responders, "respond", lambda *args, **kwargs: {"ok": True, "results": []})
    monkeypatch.setattr(module, "extract_and_save_async", lambda *args, **kwargs: None)

    try:
        status, body = srv.post("/api/message", {
            "actor": "clement",
            "content": "faites ce test",
            "task_id": "quiet-toolbus",
        })
        assert status == 200
        assert body["auto_work"]["scheduled"] is True

        status, thread = srv.post("/api/conversation", {"action": "get", "task_id": "quiet-toolbus", "limit": 20})
        assert status == 200
        contents = [row["content"] for row in thread["thread"]]
        assert not any("noisy line" in content for content in contents)
        assert any("10 événement(s) masqués" in content for content in contents)
    finally:
        srv.close()


def test_room_health_work_uses_local_kernel_without_engine_failover(tmp_path, monkeypatch):
    module, srv = _server(tmp_path, monkeypatch)
    called = {"engine": False}

    class ImmediateThread:
        def __init__(self, target, args=(), kwargs=None, name=None, daemon=None):
            self.target = target
            self.args = args
            self.kwargs = kwargs or {}
            self._alive = False

        def start(self):
            self._alive = True
            try:
                self.target(*self.args, **self.kwargs)
            finally:
                self._alive = False

        def join(self, timeout=None):
            return None

        def is_alive(self):
            return self._alive

    class FakeAthosEngine:
        def __init__(self, *args, **kwargs):
            called["engine"] = True

    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_WORK", True)
    monkeypatch.setattr(module.config, "ATHOS_ROOM_AUTO_WORK_REVIEW", False)
    monkeypatch.setattr(module.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(module, "AthosEngine", FakeAthosEngine)
    monkeypatch.setattr(module.room_responders, "respond", lambda *args, **kwargs: {"ok": True, "results": []})
    monkeypatch.setattr(module, "extract_and_save_async", lambda *args, **kwargs: None)

    try:
        status, body = srv.post("/api/message", {
            "actor": "clement",
            "content": "vérifiez que la Room fonctionne sans boucle",
            "task_id": "room-local-health",
        })
        assert status == 200
        assert body["auto_work"]["scheduled"] is True
        assert called["engine"] is False

        status, thread = srv.post("/api/conversation", {"action": "get", "task_id": "room-local-health", "limit": 20})
        assert status == 200
        assert any("Vérification Room locale" in row["content"] for row in thread["thread"])
        assert any("boucle=non détectée" in row["content"] for row in thread["thread"])
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


def test_boot_replay_helper_passes_token_and_runs_once(tmp_path, monkeypatch):
    module = _load_server(tmp_path, monkeypatch)
    calls = []

    class ImmediateThread:
        def __init__(self, target, name=None, daemon=None):
            self.target = target

        def start(self):
            self.target()

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))

        class Result:
            stdout = "[replay] done"
            stderr = ""

        return Result()

    monkeypatch.setattr(module.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module.config, "ATHOS_ACCESS_TOKEN", "boot-token")
    monkeypatch.setattr(module.config, "ATHOS_BIND_HOST", "127.0.0.1")
    monkeypatch.setattr(module.config, "ATHOS_PORT", 7474)
    monkeypatch.setattr(module.config, "ATHOS_PATH", tmp_path)

    module._replay_offline_room_after_boot(delay_s=0)

    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args[0] == "bash"
    assert args[1].endswith("scripts/replay_offline_room.sh")
    assert kwargs["env"]["ATHOS_TOKEN"] == "boot-token"
    assert kwargs["env"]["ATHOS_URL"] == "http://127.0.0.1:7474"
    assert kwargs["stdin"] == module.subprocess.DEVNULL


def test_stream_endpoint_writes_prompt_and_reply_to_room(tmp_path, monkeypatch):
    module, srv = _server(tmp_path, monkeypatch)

    class FakeAthosEngine:
        def __init__(self, mem, router, sse, permission_checker):
            self.sse = sse

        def respond(self, message):
            self.sse({"t": "room reply"})
            return f"reply to {message}"

    monkeypatch.setattr(module, "AthosEngine", FakeAthosEngine)
    monkeypatch.setattr(module, "extract_and_save_async", lambda *args, **kwargs: None)

    try:
        req = urllib.request.Request(
            srv.base + "/api/stream",
            data=json.dumps({"message": "main prompt visible", "task_id": "stream-room"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            payload = response.read().decode("utf-8")
        assert "room reply" in payload

        status, body = srv.post("/api/conversation", {"action": "get", "task_id": "stream-room", "limit": 5})
        assert status == 200
        assert [(row["actor"], row["type"], row["content"]) for row in body["thread"]] == [
            ("clement", "message", "main prompt visible"),
            ("athos", "result", "reply to main prompt visible"),
        ]
    finally:
        srv.close()


def test_room_respond_endpoint_calls_claude_and_codex(tmp_path, monkeypatch):
    module, srv = _server(tmp_path, monkeypatch)
    called = {}

    def fake_respond(message, task_id="", engines=None, timeout=45, force=False):
        called["payload"] = {
            "message": message,
            "task_id": task_id,
            "engines": engines,
            "timeout": timeout,
            "force": force,
        }
        return {"ok": True, "results": [{"engine": "claude", "ok": True}, {"engine": "codex", "ok": True}]}

    monkeypatch.setattr(module.room_responders, "respond", fake_respond)

    try:
        status, body = srv.post("/api/room/respond", {
            "message": "Tout le monde est là ?",
            "task_id": "room-http",
            "engines": ["claude", "codex"],
            "timeout": 2,
        })
        assert status == 200
        assert body["ok"] is True
        assert called["payload"] == {
            "message": "Tout le monde est là ?",
            "task_id": "room-http",
            "engines": ["claude", "codex"],
            "timeout": 2,
            "force": False,
        }
    finally:
        srv.close()
