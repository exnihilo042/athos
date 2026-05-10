import importlib
import os
import sys


def test_voice_server_import_initializes_engine(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test")
    root = os.getcwd()
    voice_path = os.path.join(root, "voice")
    if voice_path not in sys.path:
        sys.path.insert(0, voice_path)
    sys.modules.pop("config", None)
    sys.modules.pop("server", None)

    import voice.server as server
    importlib.reload(server)

    assert server._engine["current"] == "chatgpt"
    assert server._available_engines()[0] == "chatgpt"
