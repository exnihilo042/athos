from core import situational_decision


def test_decide_selects_best_situational_option_not_fixed_mapping():
    decision = situational_decision.decide("choose tool", [
        {"name": "fast_but_risky", "kind": "tool", "fit": 0.9, "confidence": 0.7, "risk": 0.9},
        {"name": "observable_safe", "kind": "tool", "fit": 0.75, "confidence": 0.85, "risk": 0.1, "observability": 0.9, "reversibility": 0.9},
    ])

    assert decision.chosen.name == "observable_safe"
    assert decision.policy == "situational_not_fixed"
    assert "risk" in decision.to_dict()["axes"]


def test_decide_pauses_for_high_risk_or_approval():
    decision = situational_decision.decide("delete files", [
        {"name": "rm", "kind": "action", "fit": 0.9, "risk": 0.95, "requires_approval": True},
    ])

    assert decision.should_pause is True
    assert decision.pause_reason == "approval_required_for_chosen_option"


def test_engine_option_preserves_identity_context():
    option = situational_decision.option_from_engine("claude_code", current=True)

    assert option["kind"] == "engine"
    assert option["memory_continuity"] >= 0.9
    assert "Athos identity" in option["reasons"][0]
