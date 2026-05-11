import importlib
import os
from pathlib import Path


def test_config_uses_drive_path_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path / "memory"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test")
    monkeypatch.setenv("OPENAI_ENABLED", "true")
    monkeypatch.delenv("ATHOS_API_SPEND", raising=False)
    monkeypatch.delenv("WHISPER_ENABLED", raising=False)
    monkeypatch.setenv("GROK_API_KEY", "grok-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    monkeypatch.setenv("GROK_MODEL", "grok-test-model")
    monkeypatch.setenv("ATHOS_ACCESS_TOKEN", "access-test")
    import core.config as config
    importlib.reload(config)

    assert config.DRIVE == (tmp_path / "memory").resolve()
    assert config.ANTHROPIC_KEY == "test-key"
    assert config.OPENAI_KEY == "openai-test"
    assert config.OPENAI_ENABLED is True
    assert config.PAID_API_ENABLED is False
    assert config.spend_policy()["mode"] == "zero_paid_api"
    assert config.spend_policy()["openai_enabled"] is False
    assert config.spend_policy()["whisper_enabled"] is False
    assert config.GROK_KEY == "grok-test"
    assert config.OPENAI_MODEL == "gpt-test"
    assert config.GROK_MODEL == "grok-test-model"
    assert config.ATHOS_ENGINE_ORDER == "chatgpt_plus,claude_code,anthropic_api,grok,ollama"
    assert config.ATHOS_ACCESS_TOKEN == "access-test"
    assert config.ATHOS_BIND_HOST == "127.0.0.1"
    assert config.ATHOS_PORT == 7474
    assert str(config.ATHOS_LOG_PATH).endswith("athos_server.log")
    assert str(config.ATHOS_PID_FILE).endswith("athos_server.pid")
    assert config.ATHOS_REQUIRE_TOKEN is False
    assert config.ATHOS_TOKEN_ENFORCED is True
    assert config.server_security_policy()["token_required"] is True
    assert config.server_security_policy()["remote_token_required"] is False
    assert "http://127.0.0.1:7474" in config.ATHOS_ALLOWED_ORIGINS
    assert config.ATHOS_ALLOW_ANY_WRITE is False
    assert config.allowed_write_roots()
    assert config.ENV_PATH == Path(config.ROOT / ".env")
    assert config.LOGS == config.DRIVE / "logs"


def test_config_paid_api_requires_explicit_spend_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path / "memory"))
    monkeypatch.setenv("OPENAI_ENABLED", "true")
    monkeypatch.setenv("WHISPER_ENABLED", "true")
    monkeypatch.setenv("ATHOS_API_SPEND", "allow")

    import core.config as config
    importlib.reload(config)

    assert config.PAID_API_ENABLED is True
    assert config.spend_policy()["openai_enabled"] is True
    assert config.spend_policy()["whisper_enabled"] is True


def test_config_requires_token_for_remote_bind_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path / "memory"))
    monkeypatch.setenv("ATHOS_BIND_HOST", "0.0.0.0")
    monkeypatch.delenv("ATHOS_REQUIRE_TOKEN", raising=False)

    import core.config as config
    importlib.reload(config)

    assert config.ATHOS_REQUIRE_TOKEN is True
    assert config.ATHOS_TOKEN_ENFORCED is True
    assert config.server_security_policy()["token_required"] is True
    assert config.server_security_policy()["remote_token_required"] is True
