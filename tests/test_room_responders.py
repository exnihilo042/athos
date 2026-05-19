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
        if args[0] == "claude":
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


def test_room_responders_report_engine_errors(tmp_path, monkeypatch):
    mod, room = _module(tmp_path, monkeypatch)
    monkeypatch.setattr(mod.shutil, "which", lambda name: None)

    result = mod.respond("ping", task_id="room-error", engines=["claude"], timeout=1)

    assert result["ok"] is False
    thread = room.get_thread(task_id="room-error", limit=5)
    assert thread[-1]["actor"] == "claude"
    assert thread[-1]["type"] == "error"
    assert "claude CLI introuvable" in thread[-1]["content"]
