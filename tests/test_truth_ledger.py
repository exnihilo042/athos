from core import truth_ledger


def test_truth_claim_calibrates_confidence_and_source_priority():
    claim = truth_ledger.TruthClaim(
        holder="Athos",
        claim="API spend is disabled by default",
        confidence=0.83,
        source={"source": ".env", "source_type": "repo"},
    )

    data = claim.to_dict()
    assert data["confidence"] == 0.85
    assert data["source"]["priority"] == truth_ledger.SOURCE_PRIORITY["repo"]


def test_split_compiled_truth_and_append_timeline():
    page = "## Compiled Truth\nAthos is local-first.\n\n## Timeline\n- old"
    split = truth_ledger.split_compiled_truth(page)
    updated = truth_ledger.append_timeline_entry(page, "Added truth ledger", "repo", "2026-05-12")

    assert split["compiled_truth"] == "Athos is local-first."
    assert split["timeline"] == "- old"
    assert "Athos is local-first." in updated
    assert "2026-05-12 | repo | Added truth ledger" in updated


def test_signal_scan_detects_entities_and_original_thought():
    result = truth_ledger.signal_scan(
        "Je pense que ATHOS doit utiliser GBrain et GStack pour sa mémoire et sa cognition.",
        source={"source": "conversation", "source_type": "direct_user"},
    )

    slugs = {entity["slug"] for entity in result["entities"]}
    assert "athos" in slugs
    assert result["original_thought"] is True
    assert "attach_provenance" in result["recommended_writes"]


def test_policy_keeps_facts_and_takes_separate():
    policy = truth_ledger.policy()

    assert policy["principle"] == "facts_takes_and_beliefs_must_not_be_conflated"
    assert "fact" in policy["claim_kinds"]
    assert "take" in policy["claim_kinds"]
