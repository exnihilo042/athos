"""A.T.H.O.S. local austerity capability layer.

External devices, sensors and cloud engines can amplify Athos, but they are not
the base of capability. This module describes what Athos can still do with only
local memory, installed tools, first-principles reasoning and deferred sync.
"""
from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

try:
    from . import config, memory_status, session_kernel, sync_manager
except ImportError:
    import config
    import memory_status
    import session_kernel
    import sync_manager


LOCAL_TOOLS = (
    "python3",
    "git",
    "rg",
    "curl",
    "osascript",
    "ollama",
    "codex",
    "claude",
    "ffmpeg",
    "nmap",
)

NO_RESOURCE_CAPABILITIES = (
    "compress_context_into_working_memory",
    "reason_from_first_principles_and_local_facts",
    "compensate_llm_scope_rigidity_with_authorized_local_memory_tools_and_protocols",
    "name_precise_uncertainty_instead_of_guessing",
    "simulate_action_paths_before_mutation",
    "queue_network_or_cloud_work_until_available",
    "reuse_installed_skills_and_repo_knowledge",
    "produce_small_reversible_next_actions",
)

ENERGY_POLICY = (
    "prefer local deterministic checks before model calls",
    "use the smallest context pack that preserves the task",
    "avoid paid or remote engines unless explicitly enabled and useful",
    "checkpoint compact summaries instead of replaying full history",
    "choose direct tooling when a shell or parser is more efficient than an LLM",
)

ANTI_RIGIDITY_POLICY = (
    "treat engine limits as routing constraints, not Athos limits",
    "move durable context into Athos memory instead of relying on model context windows",
    "replace forbidden or unavailable direct action with authorized local plans, queues, or tools",
    "degrade gracefully from cloud engine to local reasoning without losing identity",
)


def scan() -> dict[str, Any]:
    """Return a no-network inventory of local resources Athos can exploit."""
    tools = {name: bool(shutil.which(name)) for name in LOCAL_TOOLS}
    repo = Path(config.ATHOS_PATH)
    drive = Path(config.DRIVE)
    memory = memory_status.status()
    session = session_kernel.status()
    sync = sync_manager.status()
    return {
        "mode": "austere_local_capability",
        "network_required": False,
        "claim": "Athos remains capable without external sensors or cloud access; those only amplify the base.",
        "tools": tools,
        "available_tool_count": sum(1 for present in tools.values() if present),
        "local_assets": {
            "repo": str(repo),
            "repo_exists": repo.exists(),
            "memory_root": str(drive),
            "memory_exists": drive.exists(),
            "session_events": session.get("events", 0),
            "pending_sync_jobs": sync.get("pending", 0),
        },
        "memory": {
            "ok": memory.get("ok", False),
            "missing": memory.get("missing", []),
            "canonical_files": len(memory.get("canonical_files", [])),
        },
        "capabilities_without_network": list(NO_RESOURCE_CAPABILITIES),
        "energy_policy": list(ENERGY_POLICY),
        "anti_rigidity_policy": list(ANTI_RIGIDITY_POLICY),
        "deferred_work_policy": "network-dependent actions are queued, checkpointed, then replayed after reconnect or approval",
    }


def austerity_pack(objective: str = "") -> dict[str, Any]:
    """Describe how Athos should act when resources are scarce."""
    resource_scan = scan()
    return {
        "objective": objective[:500],
        "base": "capability_under_resource_austerity",
        "principle": (
            "Local scarcity changes tactics, not identity: Athos compresses, scans, infers, simulates, "
            "acts reversibly, compensates engine rigidity, and queues what requires missing resources."
        ),
        "resource_scan": resource_scan,
        "action_loop": [
            "inventory_available_local_resources",
            "compress_task_and_relevant_memory",
            "separate_known_inferable_unknown",
            "choose_lowest_cost_reversible_step",
            "execute_or_queue_with_visible_reason",
            "checkpoint_result_for_engine_continuity",
        ],
        "physical_world_position": "devices, sensors and hardware are accelerators, not prerequisites",
    }
