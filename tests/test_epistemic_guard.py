from core import epistemic_guard


def test_epistemic_guard_prioritizes_truth_over_comfort():
    pack = epistemic_guard.guardrail_pack()

    assert pack["principle"] == "truth_over_approval_and_comfort"
    assert any("do not flatter" in rule for rule in pack["rules"])
    assert "failure_mode" in pack
    assert epistemic_guard.should_challenge(0.4) is True
    assert epistemic_guard.should_challenge(0.8) is False
    assert epistemic_guard.should_challenge(0.7, user_seems_certain=True) is True
