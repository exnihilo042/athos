import importlib
import os
import sys


def _handler(monkeypatch, skill_enabled: str = "false"):
    monkeypatch.setenv("ATHOS_SKILL_INSTALL_ENABLED", skill_enabled)
    root = os.getcwd()
    voice_path = os.path.join(root, "voice")
    if voice_path not in sys.path:
        sys.path.insert(0, voice_path)
    for name in ("config", "server"):
        sys.modules.pop(name, None)
    import voice.server as server
    importlib.reload(server)
    h = object.__new__(server.Handler)
    sent = []
    h._body = lambda: {}
    h._json = lambda data, status=200: sent.append((status, data))
    return server, h, sent


def test_skills_propose_blocks_when_skill_install_disabled(monkeypatch):
    server, h, sent = _handler(monkeypatch, "false")
    h.path = "/api/skills"
    h._auth = lambda: True
    h._body = lambda: {"action": "propose", "name": "x", "allow_mutation": True}

    h.do_POST()

    assert sent[-1][1]["ok"] is False
    assert sent[-1][1]["requires_confirmation"] is True
    assert "blocked" in sent[-1][1]["msg"]


def test_skills_integrate_blocks_when_skill_install_disabled(monkeypatch):
    server, h, sent = _handler(monkeypatch, "false")
    h.path = "/api/skills"
    h._auth = lambda: True
    h._body = lambda: {"action": "integrate", "id": "missing", "allow_mutation": True}

    h.do_POST()

    assert sent[-1][1]["ok"] is False
    assert sent[-1][1]["requires_confirmation"] is True
    assert "ATHOS_SKILL_INSTALL_ENABLED=false" in sent[-1][1]["msg"]
