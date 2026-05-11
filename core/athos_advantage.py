"""What an engine gains by passing through Athos.

This is the anti-LLM delta: Athos does not merely rename a model. It augments
the model with persistent cognition, memory, observability, local austerity,
tools, optional physical-world interfaces, and a situational decision layer.
"""
from __future__ import annotations

from typing import Any

try:
    from . import config, session_kernel, memory_status, metacognition, local_capability
    from .transformation_stack import transformation_pack
except ImportError:
    import config
    import session_kernel
    import memory_status
    import metacognition
    import local_capability
    from transformation_stack import transformation_pack


CORE_AUGMENTATIONS = [
    {
        "name": "persistent_identity_and_memory",
        "gain": "same Athos identity, Drive memory, session summary, checkpoint, and context pack across engines",
    },
    {
        "name": "situational_decision_kernel",
        "gain": "engine, skill, tool, action, protocol, acquisition and autonomy are chosen by context, not fixed mappings",
    },
    {
        "name": "metacognition",
        "gain": "Athos frames known facts, precise uncertainty, gap strategy, adaptation rules and stop conditions before acting",
    },
    {
        "name": "epistemic_integrity",
        "gain": "truth, calibration and bias correction override flattery, comfort and pleasing the user",
    },
    {
        "name": "llm_gap_compensation",
        "gain": "scope limits, context limits, provider rigidity and missing tools become routing, memory, queue or protocol problems",
    },
    {
        "name": "observable_runtime",
        "gain": "ports, PIDs, logs, launchd jobs, memory health, failover and pending work are visible and stoppable",
    },
    {
        "name": "controlled_self_extension",
        "gain": "missing capabilities become named gaps, proposed skills, tests, rollback, commit/push and memory updates",
    },
    {
        "name": "austere_local_capability",
        "gain": "even with no cloud, sensors or new installs, Athos scans local resources, compresses context, reasons from memory, simulates, and queues deferred work",
    },
    {
        "name": "physical_world_bridge",
        "gain": "authorized devices, sensors, hardware tools and local OS actions amplify Athos with scopes and logs, but are not prerequisites",
    },
    {
        "name": "cost_and_risk_governor",
        "gain": "zero paid API by default; risky mutations require visible plan, approval, tests and checkpoint",
    },
]


def pack(engine: str = "unknown_engine", objective: str = "") -> dict[str, Any]:
    memory = memory_status.status()
    cognition = metacognition.status()
    checkpoint = session_kernel.latest_checkpoint() or {}
    return {
        "identity": "A.T.H.O.S.",
        "engine": engine,
        "objective": objective[:500],
        "claim": "Athos is not a prompt mask; it is a functional cognitive/runtime layer added to the engine.",
        "native_engine_limit": "A model alone is bounded by its current context, tools, memory, provider policy, and session lifetime.",
        "athos_delta": CORE_AUGMENTATIONS,
        "runtime_state": {
            "memory_ok": memory.get("ok", False),
            "memory_missing": memory.get("missing", []),
            "checkpoint_goal": checkpoint.get("goal", ""),
            "session_events": session_kernel.status().get("events", 0),
            "cost_policy": config.spend_policy()["mode"],
        },
        "cognitive_base": {
            "non_immutable": cognition["non_immutable_base"],
            "applies_to_all_engines": cognition["applies_to_all_engines"],
            "decision_axes": cognition.get("decision_axes", []),
            "core_loop": cognition["core_loop"],
        },
        "local_capability": local_capability.austerity_pack(objective),
        "transformation_stack": transformation_pack(engine=engine, objective=objective),
        "honest_boundary": (
            "Athos cannot override a provider's system instructions from outside, "
            "but it can make the engine operate as an attached Athos motor with extra memory, "
            "decisioning, tools, observability, and continuity."
        ),
    }
