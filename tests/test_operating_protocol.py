from core.agent import BASE_SYSTEM, SYSTEM, _is_authorized, tool_external_sources
from core.operating_protocol import ATHOS_OPERATING_PROTOCOL, build_system_prompt


def test_system_prompt_includes_operating_protocol():
    prompt = build_system_prompt(BASE_SYSTEM)
    assert "PROTOCOLE NOYAU ATHOS" in prompt
    assert "Cycle de travail" in prompt
    assert "Autonomie contrôlée" in prompt
    assert prompt == SYSTEM


def test_authorization_requires_explicit_launch_intent():
    assert _is_authorized("ok") is True
    assert _is_authorized("vas-y") is True
    assert _is_authorized("allons-y") is True
    assert _is_authorized("lance le plan") is True
    assert _is_authorized("ok, c'est quoi le risque ?") is False
    assert _is_authorized("oui mais explique avant") is False


def test_external_sources_tool_lists_athos_sources():
    result = tool_external_sources("ollama")
    assert "codewithbro95/J.A.R.V.I.S" in result
    assert "Ollama" in result
    assert "JARVIS" not in ATHOS_OPERATING_PROTOCOL
