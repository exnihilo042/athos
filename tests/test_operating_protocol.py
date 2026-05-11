from core.agent import BASE_SYSTEM, SYSTEM, _is_authorized
from core.operating_protocol import ATHOS_OPERATING_PROTOCOL, build_system_prompt


def test_system_prompt_includes_operating_protocol():
    prompt = build_system_prompt(BASE_SYSTEM)
    assert "A.T.H.O.S." in prompt
    assert "KERNEL ACTIF" in prompt
    assert "CYCLE DE TRAVAIL" in prompt or "Cycle de travail" in prompt
    assert "boîte noire" in prompt
    assert "GREETING OBLIGATOIRE" in prompt
    assert prompt == SYSTEM


def test_authorization_requires_explicit_launch_intent():
    assert _is_authorized("ok") is True
    assert _is_authorized("vas-y") is True
    assert _is_authorized("allons-y") is True
    assert _is_authorized("lance le plan") is True
    assert _is_authorized("oui") is True
    # "ok" seul dans une phrase d'hésitation contient quand même le mot-clé
    assert _is_authorized("ok, c'est quoi le risque ?") is False
    # Non-autorisés purs
    assert _is_authorized("bonjour") is False
    assert _is_authorized("explique-moi d'abord") is False


def test_no_legacy_names_in_protocol():
    assert "JARVIS" not in ATHOS_OPERATING_PROTOCOL
    assert "jarvis" not in ATHOS_OPERATING_PROTOCOL
