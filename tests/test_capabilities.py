from core import capabilities


def test_matches_self_knowledge_request():
    assert capabilities.matches_self_knowledge_request("Où en est Athos ?")
    assert capabilities.matches_self_knowledge_request("Que sais-tu faire ?")
    assert not capabilities.matches_self_knowledge_request("Bonjour")
