from core import capability_graph


def test_capability_graph_interconnects_engines_memory_tools_and_guardrails(monkeypatch):
    monkeypatch.setattr(
        capability_graph.local_capability,
        "scan",
        lambda: {
            "available_tool_count": 2,
            "network_required": False,
            "tools": {"python3": True, "git": True, "nmap": False},
        },
    )
    monkeypatch.setattr(capability_graph.memory_status, "status", lambda: {
        "ok": True,
        "missing": [],
        "root": "/memory",
        "session_kernel": {"events": 3},
    })
    monkeypatch.setattr(capability_graph.sync_manager, "status", lambda: {"pending": 0, "ready_for_replay": 0})

    graph = capability_graph.build_graph("audit Athos", ["chatgpt_plus", "ollama"])
    node_ids = {node["id"] for node in graph["nodes"]}
    edges = {(edge["source"], edge["target"], edge["relation"]) for edge in graph["edges"]}

    assert graph["principle"] == "capabilities_are_reusable_graph_nodes_not_fixed_per_engine_variables"
    assert "athos_core" in node_ids
    assert "guard.epistemic_integrity" in node_ids
    assert "memory.truth_ledger" in node_ids
    assert "source.garrytan.gbrain" in node_ids
    assert "source.fathah.hermes-desktop" in node_ids
    assert "review.truth_gate" in node_ids
    assert "model_profile.athos.chatgpt_plus" in node_ids
    assert "engine.chatgpt_plus" in node_ids
    assert "tool.python3" in node_ids
    assert ("athos_core", "guard.epistemic_integrity", "must_obey") in edges
    assert ("guard.epistemic_integrity", "memory.truth_ledger", "writes_calibrated_claims_to") in edges
    assert ("local.austere_core", "tool.git", "can_use_without_network") in edges
    assert graph["summary"]["austere_mode_ready"] is True
    assert graph["summary"]["interconnection_score"] > 0
