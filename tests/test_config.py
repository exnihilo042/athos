import importlib
import os
from pathlib import Path


def test_config_uses_drive_path_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path / "memory"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test")
    monkeypatch.setenv("GROK_API_KEY", "grok-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    monkeypatch.setenv("GROK_MODEL", "grok-test-model")
    monkeypatch.setenv("ATHOS_ACCESS_TOKEN", "access-test")
    import core.config as config
    importlib.reload(config)

    assert config.DRIVE == (tmp_path / "memory").resolve()
    assert config.ANTHROPIC_KEY == "test-key"
    assert config.OPENAI_KEY == "openai-test"
    assert config.GROK_KEY == "grok-test"
    assert config.OPENAI_MODEL == "gpt-test"
    assert config.GROK_MODEL == "grok-test-model"
    assert config.ATHOS_ENGINE_ORDER == "chatgpt,claude,grok,ollama"
    assert config.ATHOS_ACCESS_TOKEN == "access-test"
    assert config.ENV_PATH == Path(config.ROOT / ".env")
    assert config.LOGS == config.DRIVE / "logs"
