from core.self_improvement import matches_self_improvement_request, plan_self_improvement


def test_self_improvement_plan_is_controlled(monkeypatch, tmp_path):
    from core import session_kernel
    session_kernel.SESSION_FILE = tmp_path / "kernel.jsonl"

    plan = plan_self_improvement("améliore-toi avec Gmail")

    assert plan.mutation_requires_approval is True
    assert "email" in plan.gap.lower() or "gmail" in plan.gap.lower()
    assert "Lance quand tu veux" in plan.as_text()


def test_matches_self_improvement_request():
    assert matches_self_improvement_request("auto-améliore toi")
    assert not matches_self_improvement_request("bonjour")
