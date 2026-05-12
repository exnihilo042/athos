"""Capability graph for A.T.H.O.S.

Athos should not grow as isolated lists per engine, task or skill. The graph is
the shared substrate: engines, memory, local tools, protocols, skills, devices
and hardware become reusable nodes connected by explicit relations.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

try:
    from . import engine_router, external_sources, local_capability, memory_status, model_profiles, review_pipeline, sync_manager, truth_ledger
    from .named_protocols import list_protocols
    from .registries import device_registry, hardware_registry, skill_registry
except ImportError:
    import engine_router
    import external_sources
    import local_capability
    import memory_status
    import model_profiles
    import review_pipeline
    import sync_manager
    import truth_ledger
    from named_protocols import list_protocols
    from registries import device_registry, hardware_registry, skill_registry


@dataclass(frozen=True)
class CapabilityNode:
    id: str
    kind: str
    label: str
    status: str = "unknown"
    offline: bool = False
    risk: str = "low"
    cost: str = "free"
    tags: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CapabilityEdge:
    source: str
    target: str
    relation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_graph(objective: str = "", available_engines: list[str] | None = None) -> dict[str, Any]:
    local = local_capability.scan()
    memory = memory_status.status()
    sync = sync_manager.status()
    configured_engines = engine_router.configured_order()
    available = set(available_engines or [])

    nodes: list[CapabilityNode] = [
        CapabilityNode("athos_core", "identity", "A.T.H.O.S.", "active", True, tags=["identity", "kernel"]),
        CapabilityNode(
            "memory.drive",
            "memory",
            "Drive/local memory",
            "ok" if memory.get("ok") else "degraded",
            True,
            tags=["context", "continuity"],
            meta={"missing": memory.get("missing", []), "root": memory.get("root", "")},
        ),
        CapabilityNode(
            "memory.session_kernel",
            "memory",
            "Session kernel",
            "active" if memory.get("session_kernel", {}).get("events", 0) else "empty",
            True,
            tags=["handoff", "checkpoint"],
            meta=memory.get("session_kernel", {}),
        ),
        CapabilityNode(
            "sync.outbox",
            "sync",
            "Offline sync outbox",
            "pending" if sync.get("pending", 0) else "clear",
            True,
            tags=["offline", "replay"],
            meta={"pending": sync.get("pending", 0), "ready_for_replay": sync.get("ready_for_replay", 0)},
        ),
        CapabilityNode(
            "local.austere_core",
            "capability",
            "Austere local capability",
            "active",
            True,
            tags=["offline", "anti_rigidity", "low_energy"],
            meta={
                "available_tool_count": local.get("available_tool_count", 0),
                "network_required": local.get("network_required", False),
            },
        ),
        CapabilityNode(
            "guard.epistemic_integrity",
            "guardrail",
            "Truth over approval",
            "active",
            True,
            tags=["truth", "bias_correction", "calibration"],
            meta={"principle": "truth_over_approval_and_comfort"},
        ),
    ]

    for engine in configured_engines:
        nodes.append(CapabilityNode(
            f"engine.{engine}",
            "engine",
            engine,
            "available" if engine in available else "configured",
            engine == "ollama",
            cost="subscription_or_local" if engine in {"chatgpt_plus", "claude_code", "ollama"} else "api_or_external",
            tags=["motor", "replaceable"],
        ))

    for name, present in sorted((local.get("tools") or {}).items()):
        nodes.append(CapabilityNode(
            f"tool.{name}",
            "local_tool",
            name,
            "available" if present else "missing",
            True,
            tags=["local", "deterministic"],
        ))

    for protocol in list_protocols():
        nodes.append(CapabilityNode(
            f"protocol.{protocol['name']}",
            "protocol",
            protocol["name"],
            protocol.get("status", "planned"),
            True,
            risk=protocol.get("risk", "medium"),
            tags=["named_protocol", "routine"],
            meta={"requires_approval": protocol.get("requires_approval", True)},
        ))

    for skill in skill_registry():
        nodes.append(CapabilityNode(
            f"skill.{skill['name']}",
            "skill",
            skill["name"],
            "installed" if skill.get("installed") else "available",
            bool(skill.get("offline")),
            risk="medium" if skill.get("permissions") else "low",
            tags=["skill", "permissioned"],
            meta={
                "permissions": skill.get("permissions", []),
                "dependencies": skill.get("dependencies", []),
                "compatible_devices": skill.get("compatible_devices", []),
            },
        ))

    for device in device_registry():
        nodes.append(CapabilityNode(
            f"device.{device['id']}",
            "device",
            device.get("label") or device["id"],
            device.get("status", "unknown"),
            bool(device.get("offline_queue")),
            risk="medium",
            tags=["device", "revocable"],
            meta={"scopes": device.get("scopes", []), "heartbeat": device.get("heartbeat", "")},
        ))

    for hardware in hardware_registry():
        nodes.append(CapabilityNode(
            f"hardware.{hardware['name']}",
            "hardware",
            hardware["name"],
            hardware.get("status", "planned"),
            False,
            risk="high",
            tags=["hardware", "permissioned"],
            meta={"mode": hardware.get("mode", ""), "permission": hardware.get("permission", "")},
        ))

    for source in external_sources.OPEN_SOURCE_SOURCES:
        nodes.append(CapabilityNode(
            f"source.{source['id'].replace('/', '.')}",
            "external_source",
            source["id"],
            "integrated",
            True,
            cost="free_mit",
            tags=["source", "open_source", source.get("kind", "")],
            meta={
                "url": source.get("url", ""),
                "license": source.get("license", ""),
                "patterns": source.get("imported_patterns", []),
                "athos_use": source.get("athos_use", ""),
            },
        ))

    for source in external_sources.ACADEMIC_SOURCES:
        nodes.append(CapabilityNode(
            f"academic.{source['id']}",
            "academic_source",
            source["title"],
            "referenced",
            True,
            cost="free_reference",
            tags=["source", "academic", "principle"],
            meta={
                "url": source.get("url", ""),
                "principle": source.get("principle", ""),
                "athos_use": source.get("athos_use", ""),
            },
        ))

    for profile in model_profiles.runtime_profiles(available):
        nodes.append(CapabilityNode(
            f"model_profile.{profile.id}",
            "model_profile",
            profile.label,
            profile.status,
            profile.local_first,
            cost=profile.cost,
            tags=["model_profile", "runtime", profile.provider],
            meta={
                "provider": profile.provider,
                "engine": profile.engine,
                "preserves_athos_identity": profile.preserves_athos_identity,
                "notes": profile.notes,
            },
        ))

    for stage in review_pipeline.stages():
        nodes.append(CapabilityNode(
            f"review.{stage['id']}",
            "review_stage",
            stage["label"],
            "available",
            True,
            risk=stage.get("risk", "low"),
            tags=["review", "situational"],
            meta={"purpose": stage.get("purpose", ""), "outputs": stage.get("outputs", [])},
        ))

    nodes.append(CapabilityNode(
        "memory.truth_ledger",
        "memory",
        "Truth ledger",
        "available",
        True,
        tags=["truth", "provenance", "facts_vs_takes"],
        meta=truth_ledger.policy(),
    ))

    nodes.append(CapabilityNode(
        "transport.sse_parser",
        "transport",
        "SSE parser",
        "available",
        True,
        tags=["stream", "ui", "observable"],
        meta={"source": "fathah/hermes-desktop", "license": "MIT"},
    ))

    edges = _edges_for(nodes)
    node_ids = {node.id for node in nodes}
    available_nodes = [node.id for node in nodes if node.status in {"active", "available", "installed", "ok", "clear"}]
    return {
        "objective": objective[:500],
        "principle": "capabilities_are_reusable_graph_nodes_not_fixed_per_engine_variables",
        "nodes": [node.to_dict() for node in nodes],
        "edges": [edge.to_dict() for edge in edges if edge.source in node_ids and edge.target in node_ids],
        "summary": {
            "nodes": len(nodes),
            "edges": len(edges),
            "available_nodes": len(available_nodes),
            "available_engines": sorted(available),
            "offline_ready_nodes": sum(1 for node in nodes if node.offline),
            "interconnection_score": _interconnection_score(len(nodes), len(edges)),
            "austere_mode_ready": bool(local.get("network_required") is False and memory.get("ok", False)),
        },
        "reuse_policy": [
            "prefer existing graph nodes before adding a new special case",
            "connect new skills to memory, permissions, tests, devices and protocols",
            "route around engine limits through graph alternatives",
            "persist graph-relevant changes in Drive memory and repo tests",
        ],
    }


def compact_summary(objective: str = "", available_engines: list[str] | None = None) -> dict[str, Any]:
    graph = build_graph(objective, available_engines)
    return {
        "principle": graph["principle"],
        "summary": graph["summary"],
        "reuse_policy": graph["reuse_policy"],
    }


def _edges_for(nodes: list[CapabilityNode]) -> list[CapabilityEdge]:
    edges = [
        CapabilityEdge("athos_core", "memory.drive", "grounds_identity"),
        CapabilityEdge("athos_core", "memory.session_kernel", "preserves_continuity"),
        CapabilityEdge("athos_core", "local.austere_core", "degrades_to"),
        CapabilityEdge("athos_core", "guard.epistemic_integrity", "must_obey"),
        CapabilityEdge("guard.epistemic_integrity", "memory.session_kernel", "records_corrections"),
        CapabilityEdge("guard.epistemic_integrity", "memory.truth_ledger", "writes_calibrated_claims_to"),
        CapabilityEdge("memory.truth_ledger", "memory.drive", "persists_sourced_claims_in"),
        CapabilityEdge("athos_core", "transport.sse_parser", "streams_observable_events_through"),
        CapabilityEdge("local.austere_core", "sync.outbox", "queues_missing_network_work"),
        CapabilityEdge("memory.drive", "sync.outbox", "syncs_through"),
    ]
    for node in nodes:
        if node.kind == "engine":
            edges.append(CapabilityEdge("athos_core", node.id, "uses_as_replaceable_motor"))
            edges.append(CapabilityEdge("memory.session_kernel", node.id, "hands_context_to"))
        elif node.kind == "local_tool" and node.status == "available":
            edges.append(CapabilityEdge("local.austere_core", node.id, "can_use_without_network"))
        elif node.kind == "protocol":
            edges.append(CapabilityEdge("athos_core", node.id, "can_activate_named_routine"))
            edges.append(CapabilityEdge(node.id, "memory.session_kernel", "must_report_to"))
        elif node.kind == "skill":
            edges.append(CapabilityEdge("athos_core", node.id, "can_delegate_capability"))
            edges.append(CapabilityEdge(node.id, "memory.drive", "must_update_memory_when_changed"))
        elif node.kind == "device":
            edges.append(CapabilityEdge("athos_core", node.id, "operates_with_scope"))
            edges.append(CapabilityEdge(node.id, "sync.outbox", "uses_offline_queue"))
        elif node.kind == "hardware":
            edges.append(CapabilityEdge("athos_core", node.id, "can_amplify_with_permission"))
        elif node.kind == "external_source":
            edges.append(CapabilityEdge("athos_core", node.id, "imports_pattern_with_attribution"))
            edges.append(CapabilityEdge(node.id, "memory.truth_ledger", "informs"))
        elif node.kind == "academic_source":
            edges.append(CapabilityEdge(node.id, "athos_core", "grounds_principle"))
            edges.append(CapabilityEdge(node.id, "guard.epistemic_integrity", "supports_calibration"))
        elif node.kind == "model_profile":
            edges.append(CapabilityEdge("athos_core", node.id, "can_select_runtime_profile"))
            engine = str(node.meta.get("engine", ""))
            if engine:
                edges.append(CapabilityEdge(node.id, f"engine.{engine}", "wraps_engine"))
        elif node.kind == "review_stage":
            edges.append(CapabilityEdge("athos_core", node.id, "runs_when_situationally_relevant"))
            edges.append(CapabilityEdge(node.id, "guard.epistemic_integrity", "must_preserve"))
            edges.append(CapabilityEdge(node.id, "memory.session_kernel", "reports_findings_to"))
    return edges


def _interconnection_score(nodes: int, edges: int) -> float:
    if nodes <= 1:
        return 0.0
    return round(min(1.0, edges / max(1, nodes * 1.4)), 3)
