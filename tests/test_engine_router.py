from core.engine_router import available_engines, configured_order, first_available, next_engine


def test_configured_order_defaults_to_chatgpt_first_and_ollama_last(monkeypatch):
    monkeypatch.delenv("ATHOS_ENGINE_ORDER", raising=False)
    assert configured_order() == ["chatgpt_plus", "claude_code", "anthropic_api", "grok", "lmstudio", "vllm", "llamacpp", "ollama"]


def test_configured_order_preserves_known_custom_order_and_appends_missing():
    assert configured_order("anthropic_api,chatgpt_plus") == ["anthropic_api", "chatgpt_plus", "claude_code", "grok", "lmstudio", "vllm", "llamacpp", "ollama"]


def test_available_engines_respects_priority():
    engines = available_engines(
        anthropic_key="sk-ant-real",
        anthropic_enabled=True,
        openai_key="sk-openai",
        openai_enabled=True,
        grok_key="",
        has_ollama=lambda: True,
        has_chatgpt_plus=lambda: True,
        has_claude_code=lambda: True,
    )
    assert engines == ["chatgpt_plus", "claude_code", "anthropic_api", "ollama"]
    assert first_available(engines) == "chatgpt_plus"


def test_available_engines_includes_local_openai_runtimes_when_detected():
    engines = available_engines(
        has_lmstudio=lambda: True,
        has_vllm=lambda: False,
        has_llamacpp=lambda: True,
        has_ollama=lambda: True,
    )

    assert engines == ["lmstudio", "llamacpp", "ollama"]


def test_paid_api_keys_are_ignored_when_disabled():
    engines = available_engines(
        anthropic_key="sk-ant-real",
        anthropic_enabled=False,
        openai_key="sk-openai",
        openai_enabled=False,
        grok_key="",
        has_ollama=lambda: False,
    )
    assert engines == []


def test_next_engine_never_wraps_to_current_when_other_available():
    engines = ["chatgpt_plus", "claude_code", "anthropic_api", "grok", "lmstudio", "vllm", "llamacpp", "ollama"]
    assert next_engine("chatgpt_plus", engines) == "claude_code"
    assert next_engine("claude_code", engines) == "anthropic_api"
    assert next_engine("anthropic_api", engines) == "grok"
    assert next_engine("grok", engines) == "lmstudio"
    assert next_engine("llamacpp", engines) == "ollama"
    assert next_engine("ollama", engines) == "chatgpt_plus"
