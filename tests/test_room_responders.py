import importlib
from types import SimpleNamespace


def _module(tmp_path, monkeypatch):
    import core.athos_room as athos_room
    importlib.reload(athos_room)
    athos_room._ROOM_FILE = tmp_path / "athos_conversation.jsonl"
    athos_room._DRIVE_MIRROR = tmp_path / "drive" / "athos_conversation.jsonl"
    import core.room_responders as room_responders
    importlib.reload(room_responders)
    room_responders.athos_room._ROOM_FILE = athos_room._ROOM_FILE
    room_responders.athos_room._DRIVE_MIRROR = athos_room._DRIVE_MIRROR
    return room_responders, athos_room


def test_room_responders_call_claude_and_codex_and_write_room(tmp_path, monkeypatch):
    mod, room = _module(tmp_path, monkeypatch)
    monkeypatch.setattr(mod.shutil, "which", lambda name: f"/fake/{name}" if name == "claude" else None)
    monkeypatch.setattr(mod.engine_router, "chatgpt_plus_path", lambda: "/fake/codex")

    def fake_run(args, **kwargs):
        if args[0].endswith("claude"):
            return SimpleNamespace(returncode=0, stdout="Réponse Claude", stderr="")
        return SimpleNamespace(returncode=0, stdout="Réponse Codex", stderr="")

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    result = mod.respond("Tout le monde est là ?", task_id="room-test", timeout=2)

    assert result["ok"] is True
    thread = room.get_thread(task_id="room-test", limit=10)
    assert [e["actor"] for e in thread] == ["claude", "claude", "codex", "codex"]
    assert [e["type"] for e in thread] == ["action", "result", "action", "result"]
    assert thread[1]["content"] == "Réponse Claude"
    assert thread[3]["content"] == "Réponse Codex"


def test_room_responders_skip_existing_task_entries_unless_forced(tmp_path, monkeypatch):
    mod, room = _module(tmp_path, monkeypatch)
    room.add(
        actor="claude",
        content="claude prépare une réponse Room...",
        msg_type="action",
        task_id="dedupe-task",
        status="running",
        meta={"source": "room_responder"},
    )
    calls = []
    monkeypatch.setattr(mod, "_run_claude", lambda prompt, timeout: calls.append("claude") or "new claude")
    monkeypatch.setattr(mod, "_run_codex", lambda prompt, timeout: calls.append("codex") or "new codex")

    result = mod.respond("ping", task_id="dedupe-task", engines=["claude", "codex"], timeout=1)

    assert result["ok"] is True
    assert result["results"][0]["engine"] == "claude"
    assert result["results"][0]["skipped"] is True
    assert result["results"][1]["engine"] == "codex"
    assert result["results"][1]["ok"] is True
    assert calls == ["codex"]

    forced = mod.respond("ping", task_id="dedupe-task", engines=["claude"], timeout=1, force=True)

    assert forced["ok"] is True
    assert forced["results"][0]["engine"] == "claude"
    assert "skipped" not in forced["results"][0]
    assert calls == ["codex", "claude"]


def test_room_responders_report_engine_errors(tmp_path, monkeypatch):
    mod, room = _module(tmp_path, monkeypatch)
    monkeypatch.setattr(mod.shutil, "which", lambda name: None)
    monkeypatch.setattr(mod, "CLAUDE_CANDIDATES", [])

    result = mod.respond("ping", task_id="room-error", engines=["claude"], timeout=1)

    assert result["ok"] is False
    thread = room.get_thread(task_id="room-error", limit=5)
    assert thread[-1]["actor"] == "claude"
    assert thread[-1]["type"] == "error"
    assert "claude CLI introuvable" in thread[-1]["content"]


def test_room_responders_use_cooldown_for_usage_limit_errors(tmp_path, monkeypatch):
    mod, room = _module(tmp_path, monkeypatch)
    calls = []

    def limited(prompt, timeout):
        calls.append("codex")
        raise RuntimeError("ERROR: You've hit your usage limit. Please try again at 2:40 PM.")

    monkeypatch.setattr(mod, "_run_codex", limited)

    first = mod.respond("ping", task_id="limit-a", engines=["codex"], timeout=1)
    second = mod.respond("ping", task_id="limit-b", engines=["codex"], timeout=1)

    assert first["ok"] is False
    assert "limite de session atteinte" in first["results"][0]["error"]
    assert "2:40 PM" in first["results"][0]["error"]
    assert second["ok"] is False
    assert second["results"][0]["cooldown"] is True
    assert calls == ["codex"]
    assert room.get_thread(task_id="limit-b", limit=3)[-1]["status"] == "cooldown"


def test_room_responders_condense_rate_limit_errors(tmp_path, monkeypatch):
    mod, room = _module(tmp_path, monkeypatch)
    monkeypatch.setattr(
        mod,
        "_run_claude",
        lambda prompt, timeout: (_ for _ in ()).throw(RuntimeError("API Error: Request rejected (429) · rate limit")),
    )

    result = mod.respond("ping", task_id="rate-limit", engines=["claude"], timeout=1)

    assert result["ok"] is False
    assert result["results"][0]["error"] == "claude indisponible: rate limit temporaire. Réessayer plus tard."
    assert room.get_thread(task_id="rate-limit", limit=3)[-1]["content"] == result["results"][0]["error"]

    second = mod.respond("ping", task_id="rate-limit-b", engines=["claude"], timeout=1)

    assert second["ok"] is False
    assert second["results"][0]["cooldown"] is True
    assert second["results"][0]["error"] == result["results"][0]["error"]


def test_room_responders_isolate_claude_529_and_continue_codex(tmp_path, monkeypatch):
    mod, room = _module(tmp_path, monkeypatch)
    calls = []

    def overloaded(prompt, timeout):
        calls.append("claude")
        raise RuntimeError("API Error: 529 overloaded")

    def codex_ok(prompt, timeout):
        calls.append("codex")
        return "Réponse Codex malgré Claude"

    monkeypatch.setattr(mod, "_run_claude", overloaded)
    monkeypatch.setattr(mod, "_run_codex", codex_ok)

    result = mod.respond("ping", task_id="claude-529", engines=["claude", "codex"], timeout=1)

    assert result["ok"] is False
    assert calls == ["claude", "codex"]
    assert result["results"][0]["ok"] is False
    assert "surcharge temporaire 529" in result["results"][0]["error"]
    assert result["results"][1]["ok"] is True
    thread = room.get_thread(task_id="claude-529", limit=10)
    assert [(e["actor"], e["type"], e["status"]) for e in thread] == [
        ("claude", "action", "running"),
        ("claude", "error", "failed"),
        ("codex", "action", "running"),
        ("codex", "result", "completed"),
    ]


def test_room_responders_retries_after_transient_529_without_duplicate_result(tmp_path, monkeypatch):
    mod, room = _module(tmp_path, monkeypatch)
    calls = []

    def claude_flaky(prompt, timeout):
        calls.append("claude")
        if len(calls) == 1:
            raise RuntimeError("529 overloaded")
        return "Claude repris"

    monkeypatch.setattr(mod, "_run_claude", claude_flaky)
    monkeypatch.setattr(mod, "time", SimpleNamespace(time=lambda: 1000))

    first = mod.respond("ping", task_id="retry-529", engines=["claude"], timeout=1)
    second = mod.respond("ping", task_id="retry-529", engines=["claude"], timeout=1)

    assert first["ok"] is False
    assert second["results"][0]["cooldown"] is True
    assert calls == ["claude"]

    monkeypatch.setattr(mod, "time", SimpleNamespace(time=lambda: 2000))
    third = mod.respond("ping", task_id="retry-529", engines=["claude"], timeout=1)
    fourth = mod.respond("ping", task_id="retry-529", engines=["claude"], timeout=1)

    assert third["ok"] is True
    assert fourth["results"][0]["skipped"] is True
    assert calls == ["claude", "claude"]
    thread = room.get_thread(task_id="retry-529", limit=20)
    assert [e["content"] for e in thread if e["actor"] == "claude" and e["type"] == "result"] == ["Claude repris"]


def test_room_responders_run_codex_with_plugins_and_skills_disabled(tmp_path, monkeypatch):
    mod, room = _module(tmp_path, monkeypatch)
    output_file = {}
    monkeypatch.setattr(mod.engine_router, "chatgpt_plus_path", lambda: "/fake/codex")

    class FakeTemp:
        name = str(tmp_path / "codex_last_message.txt")

        def __enter__(self):
            output_file["path"] = self.name
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_tempfile(*args, **kwargs):
        return FakeTemp()

    def fake_run(args, **kwargs):
        output_file["args"] = args
        output_file["stdin"] = kwargs["stdin"]
        output_file["env"] = kwargs["env"]
        (tmp_path / "codex_last_message.txt").write_text("Réponse Codex fichier", "utf-8")
        return SimpleNamespace(returncode=0, stdout="logs bruyants", stderr="")

    monkeypatch.setattr(mod.tempfile, "NamedTemporaryFile", fake_tempfile)
    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    result = mod.respond("ping", task_id="codex-clean", engines=["codex"], timeout=2)

    assert result["ok"] is True
    args = output_file["args"]
    assert args[:2] == ["/fake/codex", "exec"]
    assert "--disable" in args
    assert "plugins" in args
    assert "--cd" in args
    kwargs_env = output_file.get("env")
    assert kwargs_env
    assert kwargs_env["CODEX_HOME"].endswith("runtime/codex_room_home")
    assert output_file["stdin"] == mod.subprocess.DEVNULL
    assert room.get_thread(task_id="codex-clean", limit=5)[-1]["content"] == "Réponse Codex fichier"


def test_room_responders_use_protected_claude_token_file(tmp_path, monkeypatch):
    mod, room = _module(tmp_path, monkeypatch)
    token_file = tmp_path / "claude_token"
    token_file.write_text("local-long-lived-token", "utf-8")
    token_file.chmod(0o600)
    monkeypatch.setenv("ATHOS_CLAUDE_TOKEN_FILE", str(token_file))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(mod.shutil, "which", lambda name: "/fake/claude" if name == "claude" else None)
    monkeypatch.setattr(mod, "_resolve_claude_oauth_token", lambda: None)
    seen = {}

    def fake_run(args, **kwargs):
        seen["api_key"] = kwargs["env"].get("ANTHROPIC_API_KEY")
        return SimpleNamespace(returncode=0, stdout="Réponse Claude fichier", stderr="")

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    result = mod.respond("ping", task_id="room-token", engines=["claude"], timeout=2)

    assert result["ok"] is True
    assert seen["api_key"] == "local-long-lived-token"
    assert room.get_thread(task_id="room-token", limit=5)[-1]["content"] == "Réponse Claude fichier"


def test_room_responders_token_file_overrides_inherited_api_key(tmp_path, monkeypatch):
    mod, room = _module(tmp_path, monkeypatch)
    token_file = tmp_path / "claude_token"
    token_file.write_text("local-pro-token", "utf-8")
    token_file.chmod(0o600)
    monkeypatch.setenv("ATHOS_CLAUDE_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "exhausted-api-key")
    monkeypatch.setattr(mod.shutil, "which", lambda name: "/fake/claude" if name == "claude" else None)
    monkeypatch.setattr(mod, "_resolve_claude_oauth_token", lambda: None)
    seen = {}

    def fake_run(args, **kwargs):
        seen["api_key"] = kwargs["env"].get("ANTHROPIC_API_KEY")
        return SimpleNamespace(returncode=0, stdout="Réponse Claude Pro", stderr="")

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    result = mod.respond("ping", task_id="room-token-priority", engines=["claude"], timeout=2)

    assert result["ok"] is True
    assert seen["api_key"] == "local-pro-token"
    assert room.get_thread(task_id="room-token-priority", limit=5)[-1]["content"] == "Réponse Claude Pro"


def test_room_responders_reject_world_readable_claude_token_file(tmp_path, monkeypatch):
    mod, room = _module(tmp_path, monkeypatch)
    token_file = tmp_path / "claude_token"
    token_file.write_text("local-long-lived-token", "utf-8")
    token_file.chmod(0o644)
    monkeypatch.setenv("ATHOS_CLAUDE_TOKEN_FILE", str(token_file))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(mod.shutil, "which", lambda name: "/fake/claude" if name == "claude" else None)

    result = mod.respond("ping", task_id="room-bad-token", engines=["claude"], timeout=2)

    assert result["ok"] is False
    assert "permissions too open" in room.get_thread(task_id="room-bad-token", limit=5)[-1]["content"]


def test_room_responders_status_is_non_invasive(tmp_path, monkeypatch):
    mod, _ = _module(tmp_path, monkeypatch)
    token_file = tmp_path / "claude_token"
    token_file.write_text("token-not-exposed", "utf-8")
    token_file.chmod(0o600)
    monkeypatch.setenv("ATHOS_CLAUDE_TOKEN_FILE", str(token_file))
    monkeypatch.setattr(mod.shutil, "which", lambda name: "/fake/claude" if name == "claude" else None)
    monkeypatch.setattr(mod.engine_router, "chatgpt_plus_path", lambda: "/fake/codex")

    status = mod.responder_status()

    assert status["ok"] is True
    assert status["actors"]["claude"]["available"] is True
    assert status["actors"]["codex"]["available"] is True
    assert status["actors"]["claude"]["token_file"]["status"] == "protected"
    assert "token-not-exposed" not in str(status)
