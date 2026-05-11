from core import skill_manager


def test_install_skill_defaults_to_visible_plan_without_mutation(monkeypatch):
    monkeypatch.setattr(skill_manager.config, "SKILL_INSTALL_ENABLED", False)

    ok, msg = skill_manager.install_skill("gmail", allow_mutation=False)

    assert ok is False
    assert "Plan installation compétence ATHOS 'gmail'" in msg
    assert "en attente d'autorisation explicite" in msg
