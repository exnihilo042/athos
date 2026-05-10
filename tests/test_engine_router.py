from core.engine_router import available_engines, configured_order, first_available, next_engine


def test_configured_order_defaults_to_chatgpt_first_and_ollama_last(monkeypatch):
    monkeypatch.delenv("ATHOS_ENGINE_ORDER", raising=False)
    assert configured_order() == ["chatgpt", "claude", "grok", "ollama"]


def test_configured_order_preserves_known_custom_order_and_appends_missing():
    assert configured_order("claude,chatgpt") == ["claude", "chatgpt", "grok", "ollama"]


def test_available_engines_respects_priority():
    engines = available_engines(
        anthropic_key="sk-ant-real",
        openai_key="sk-openai",
        grok_key="",
        has_ollama=lambda: True,
    )
    assert engines == ["chatgpt", "claude", "ollama"]
    assert first_available(engines) == "chatgpt"


def test_next_engine_never_wraps_to_current_when_other_available():
    engines = ["chatgpt", "claude", "grok", "ollama"]
    assert next_engine("chatgpt", engines) == "claude"
    assert next_engine("claude", engines) == "grok"
    assert next_engine("grok", engines) == "ollama"
    assert next_engine("ollama", engines) == "chatgpt"
