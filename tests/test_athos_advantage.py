from core import athos_advantage


def test_advantage_pack_explains_functional_delta():
    pack = athos_advantage.pack(engine="codex", objective="work on Athos")

    assert pack["identity"] == "A.T.H.O.S."
    assert pack["engine"] == "codex"
    assert "not a prompt mask" in pack["claim"]
    assert any(item["name"] == "situational_decision_kernel" for item in pack["athos_delta"])
    assert any(item["name"] == "llm_gap_compensation" for item in pack["athos_delta"])
    assert any(item["name"] == "austere_local_capability" for item in pack["athos_delta"])
    assert any(item["name"] == "physical_world_bridge" for item in pack["athos_delta"])
    assert pack["cognitive_base"]["non_immutable"] is True
    assert pack["local_capability"]["base"] == "capability_under_resource_austerity"
    assert pack["transformation_stack"]["primary_form"]["name"]
    assert "cannot override" in pack["honest_boundary"]
