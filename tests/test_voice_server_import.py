import importlib
import os
import sys


def test_voice_server_import_initializes_engine(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test")
    monkeypatch.setenv("OPENAI_ENABLED", "true")
    root = os.getcwd()
    voice_path = os.path.join(root, "voice")
    if voice_path not in sys.path:
        sys.path.insert(0, voice_path)
    sys.modules.pop("config", None)
    sys.modules.pop("server", None)

    import voice.server as server
    importlib.reload(server)

    assert "anthropic_api" in server._router.available()
