from core.engine_router import available_engines, configured_order, first_available, next_engine


def test_configured_order_defaults_to_chatgpt_first_and_ollama_last(monkeypatch):
    monkeypatch.delenv("ATHOS_ENGINE_ORDER", raising=False)
    assert configured_order() == ["chatgpt_plus", "claude_code", "anthropic_api", "grok", "ollama"]


def test_configured_order_preserves_known_custom_order_and_appends_missing():
    assert configured_order("anthropic_api,chatgpt_plus") == ["anthropic_api", "chatgpt_plus", "claude_code", "grok", "ollama"]


def test_available_engines_respects_priority():
    engines = available_engines(
        anthropic_key="sk-ant-real",
        openai_key="sk-openai",
        openai_enabled=True,
        grok_key="",
        has_ollama=lambda: True,
        has_chatgpt_plus=lambda: True,
        has_claude_code=lambda: True,
    )
    assert engines == ["chatgpt_plus", "claude_code", "anthropic_api", "ollama"]
    assert first_available(engines) == "chatgpt_plus"


def test_openai_key_is_ignored_when_openai_disabled():
    engines = available_engines(
        anthropic_key="sk-ant-real",
        openai_key="sk-openai",
        openai_enabled=False,
        grok_key="",
        has_ollama=lambda: False,
    )
    assert engines == ["anthropic_api"]


def test_next_engine_never_wraps_to_current_when_other_available():
    engines = ["chatgpt_plus", "claude_code", "anthropic_api", "grok", "ollama"]
    assert next_engine("chatgpt_plus", engines) == "claude_code"
    assert next_engine("claude_code", engines) == "anthropic_api"
    assert next_engine("anthropic_api", engines) == "grok"
    assert next_engine("grok", engines) == "ollama"
    assert next_engine("ollama", engines) == "chatgpt_plus"
