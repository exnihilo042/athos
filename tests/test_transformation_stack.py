from core import transformation_stack


def test_code_objective_transforms_engine_into_code_workbench():
    pack = transformation_stack.transformation_pack("codex", "corrige le repo, run les tests, commit et push")

    assert pack["primary_form"]["name"] == "code_workbench"
    assert "test_runner" in pack["enabled_modules"]
    assert pack["decision"]["policy"] == "situational_not_fixed"


def test_device_objective_requires_approval_and_physical_modules():
    pack = transformation_stack.transformation_pack("claude_code", "prends le controle de mon mac et de la camera")

    assert pack["primary_form"]["name"] == "device_operator"
    assert pack["primary_form"]["requires_approval"] is True
    assert "device_registry" in pack["enabled_modules"]
    assert pack["decision"]["should_pause"] is True


def test_unknown_objective_defaults_to_conversation_core():
    pack = transformation_stack.transformation_pack("grok", "bonjour")

    assert pack["primary_form"]["name"] == "conversation_core"
    assert "metacognition" in pack["enabled_modules"]
