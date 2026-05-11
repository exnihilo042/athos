from core import capabilities


def test_matches_self_knowledge_request():
    assert capabilities.matches_self_knowledge_request("Où en est Athos ?")
    assert capabilities.matches_self_knowledge_request("Que sais-tu faire ?")
    assert capabilities.matches_self_knowledge_request("fais moi un topo sur ce que tu es actuellement")
    assert not capabilities.matches_self_knowledge_request("Bonjour")


def test_compact_status_intent():
    assert capabilities.wants_compact_status("où en est Athos ? statut court")
    assert capabilities.wants_compact_status("résumé rapide")
    assert not capabilities.wants_compact_status("statut complet")


def test_compact_status_mentions_cognition():
    text = capabilities.status_report(compact=True)
    assert "Cognition:" in text
    assert "Anti-LLM delta:" in text
