from core.skills.reference_led_reproduction_workflow import reference_led_reproduction_workflow


def test_reference_led_reproduction_workflow_encodes_operator_loop():
    plan = reference_led_reproduction_workflow(
        target="shopify_theme",
        references=["claude_design", "live_theme", "lumin"],
        constraints=["no_wipe", "schema_editable"],
    )

    joined = " ".join(plan["principles"] + plan["section_loop"] + plan["quality_gates"])
    assert plan["copy_mode"] == "faithful"
    assert "two_surfaces_open" in joined
    assert "reuse_before_create" in joined
    assert "schema" in joined
    assert "preview_actual_render" in joined
    assert "checkpoint_written" in joined
