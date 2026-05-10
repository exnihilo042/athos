import importlib
import os
from pathlib import Path


def test_config_uses_drive_path_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path / "memory"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    import core.config as config
    importlib.reload(config)

    assert config.DRIVE == (tmp_path / "memory").resolve()
    assert config.ANTHROPIC_KEY == "test-key"
    assert config.ENV_PATH == Path(config.ROOT / ".env")
    assert config.LOGS == config.DRIVE / "logs"
