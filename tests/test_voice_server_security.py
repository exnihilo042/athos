import importlib
import os
import sys


def _load_server(monkeypatch, origins: str = "http://allowed.test"):
    monkeypatch.setenv("ATHOS_ALLOWED_ORIGINS", origins)
    monkeypatch.setenv("ATHOS_BIND_HOST", "127.0.0.1")
    root = os.getcwd()
    voice_path = os.path.join(root, "voice")
    if voice_path not in sys.path:
        sys.path.insert(0, voice_path)
    for name in ("config", "server"):
        sys.modules.pop(name, None)
    import voice.server as server
    importlib.reload(server)
    return server


def test_cors_uses_allowlist_origin(monkeypatch):
    server = _load_server(monkeypatch, "http://allowed.test")
    handler = object.__new__(server.Handler)
    sent = []
    handler.headers = {"Origin": "http://allowed.test"}
    handler.send_header = lambda k, v: sent.append((k, v))

    handler.cors()

    assert ("Access-Control-Allow-Origin", "http://allowed.test") in sent
    assert ("Vary", "Origin") in sent


def test_cors_rejects_unknown_origin_by_not_echoing_it(monkeypatch):
    server = _load_server(monkeypatch, "http://allowed.test")
    handler = object.__new__(server.Handler)
    sent = []
    handler.headers = {"Origin": "http://evil.test"}
    handler.send_header = lambda k, v: sent.append((k, v))

    handler.cors()

    assert ("Access-Control-Allow-Origin", "http://evil.test") not in sent
    assert ("Access-Control-Allow-Origin", "http://allowed.test") in sent
