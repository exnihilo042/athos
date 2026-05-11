from core import metacognition


def test_assess_defines_non_immutable_engine_neutral_base():
    assessment = metacognition.assess("travaille sur ta cognition", ["chatgpt_plus", "claude_code"])

    data = assessment.to_dict()

    assert data["mode"] == "metacognitive_analysis"
    assert "non_immutable_rules_adapt_to_context" in data["principles"]
    assert "llm_limitations_are_routing_inputs_not_identity_limits" in data["principles"]
    assert any("replaceable engine" in item for item in data["known_state"])
    assert any("No rule is immutable" in item for item in data["uncertainty_model"])
    assert any("engine, skill, tool" in item for item in data["engine_criteria"])


def test_assess_self_extension_adds_controlled_acquisition():
    assessment = metacognition.assess("auto-améliore ta compétence calendrier", ["claude_code"])

    assert assessment.mode == "self_extension"
    assert any("rollbackable" in item for item in assessment.gap_strategy)


def test_status_is_engine_neutral_and_checkpoint_aware(tmp_path, monkeypatch):
    monkeypatch.setattr(metacognition.session_kernel, "SESSION_FILE", tmp_path / "kernel.jsonl")
    metacognition.session_kernel.checkpoint("cognition Athos")

    status = metacognition.status()

    assert status["non_immutable_base"] is True
    assert status["applies_to_all_engines"] is True
    assert status["current_checkpoint"] == "cognition Athos"
    assert "situationally_choose_engine_skill_tool_action_or_acquisition" in status["core_loop"]
    assert "scan_and_repurpose_available_local_resources" in status["core_loop"]


def test_assess_local_austerity_mode():
    assessment = metacognition.assess("hors ligne, sans rien, reste capable en local", ["ollama"])

    assert assessment.mode == "local_austerity"
    assert any("amplifiers" in item for item in assessment.known_state)
    assert any("local resource inventory" in item for item in assessment.gap_strategy)
