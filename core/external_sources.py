"""External source registry for Athos inspirations and imported patterns."""
from __future__ import annotations

from typing import Any


OPEN_SOURCE_SOURCES: list[dict[str, Any]] = [
    {
        "id": "garrytan/gstack",
        "url": "https://github.com/garrytan/gstack",
        "license": "MIT",
        "kind": "workflow_stack",
        "imported_patterns": [
            "role_pipeline",
            "search_before_building",
            "complete_small_lakes",
            "review_test_ship_reflect_loop",
        ],
        "athos_use": "situational review pipeline and capability graph review-stage nodes",
    },
    {
        "id": "garrytan/gbrain",
        "url": "https://github.com/garrytan/gbrain",
        "license": "MIT",
        "kind": "brain_runtime",
        "imported_patterns": [
            "compiled_truth_plus_append_only_timeline",
            "takes_vs_facts",
            "source_attribution",
            "brain_first_lookup_loop",
            "entity_backlinks",
        ],
        "athos_use": "truth ledger, provenance, entity signal scan and memory graph policy",
    },
    {
        "id": "fathah/hermes-desktop",
        "url": "https://github.com/fathah/hermes-desktop",
        "license": "MIT",
        "kind": "desktop_agent_companion",
        "imported_patterns": [
            "sse_stream_parser",
            "tool_progress_events",
            "usage_tracking",
            "profile_session_surfaces",
            "guided_local_or_remote_runtime",
            "provider_model_profile_registry",
            "local_presets_for_ollama_lmstudio_vllm_llamacpp",
        ],
        "athos_use": "robust SSE parser, multi-provider model profiles and future desktop/session UI guidance",
    },
]


ACADEMIC_SOURCES: list[dict[str, Any]] = [
    {
        "id": "hayes-roth-blackboard-control-1985",
        "title": "A blackboard architecture for control",
        "url": "https://www.sciencedirect.com/science/article/abs/pii/0004370285900633",
        "principle": "opportunistic control over shared knowledge sources",
        "athos_use": "capability graph + situational choice instead of fixed mappings",
    },
    {
        "id": "friston-free-energy-2010",
        "title": "The free-energy principle: a unified brain theory?",
        "url": "https://www.nature.com/articles/nrn2787",
        "principle": "perception/action as uncertainty minimization through prediction and correction",
        "athos_use": "local austerity, prediction-error reduction, and low-energy reasoning loops",
    },
    {
        "id": "w3c-prov-2013",
        "title": "PROV-Overview",
        "url": "https://www.w3.org/TR/prov-overview/",
        "principle": "provenance links entities, activities and agents for trust assessment",
        "athos_use": "source attribution for truth ledger and memory claims",
    },
]


def catalog() -> dict[str, Any]:
    return {
        "policy": "use_with_attribution_and_tests; no bulk import of incompatible architecture",
        "open_source": OPEN_SOURCE_SOURCES,
        "academic": ACADEMIC_SOURCES,
        "summary": {
            "open_source_count": len(OPEN_SOURCE_SOURCES),
            "academic_count": len(ACADEMIC_SOURCES),
            "mit_sources": sum(1 for source in OPEN_SOURCE_SOURCES if source["license"] == "MIT"),
        },
    }


def imported_patterns() -> list[str]:
    rows: list[str] = []
    for source in OPEN_SOURCE_SOURCES:
        rows.extend(source["imported_patterns"])
    for source in ACADEMIC_SOURCES:
        rows.append(source["principle"])
    return sorted(set(rows))
