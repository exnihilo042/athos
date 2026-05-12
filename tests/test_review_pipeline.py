from core import review_pipeline


def test_review_pipeline_selects_stages_by_situation():
    result = review_pipeline.plan(
        "Implémente depuis GitHub une capacité avec tests puis commit push",
        changed_files=["core/example.py"],
    )
    stage_ids = {stage["id"] for stage in result["selected"]}

    assert "truth_gate" in stage_ids
    assert "external_research" in stage_ids
    assert "engineering_review" in stage_ids
    assert "qa_review" in stage_ids
    assert "release_review" in stage_ids
    assert result["requires_approval"] is True


def test_review_pipeline_minimal_request_still_has_truth_and_retro():
    result = review_pipeline.plan("fais un point rapide")
    stage_ids = [stage["id"] for stage in result["selected"]]

    assert stage_ids == ["truth_gate", "retro_checkpoint"]
    assert result["operating_rule"] == "select_review_stages_by_situation_not_by_engine_identity"
