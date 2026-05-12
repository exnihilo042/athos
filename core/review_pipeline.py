"""Situational review pipeline for Athos.

Inspired by garrytan/gstack's specialist review stack. Athos keeps this as a
small graph-native policy: stages are selected by objective, risk, and current
work, not by a fixed per-model checklist.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any


@dataclass(frozen=True)
class ReviewStage:
    id: str
    label: str
    purpose: str
    triggers: tuple[str, ...] = field(default_factory=tuple)
    outputs: tuple[str, ...] = field(default_factory=tuple)
    risk: str = "low"
    always: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


STAGES = (
    ReviewStage(
        "truth_gate",
        "Truth gate",
        "Separate facts, inference, uncertainty, assumptions, and comfort-seeking.",
        outputs=("verified_facts", "uncertainties", "bias_risks"),
        always=True,
    ),
    ReviewStage(
        "context_restore",
        "Context restore",
        "Read Athos memory/session before acting so engines do not cold-start.",
        triggers=("reprends", "continue", "contexte", "memory", "memoire", "checkpoint", "resume"),
        outputs=("context_pack", "last_checkpoint"),
    ),
    ReviewStage(
        "external_research",
        "Source research",
        "Ground new skills or beliefs in source code, official docs, or academic sources.",
        triggers=("github", "source", "doc", "paper", "universitaire", "research", "recherche"),
        outputs=("sources", "attribution", "import_decision"),
    ),
    ReviewStage(
        "product_review",
        "Product review",
        "Challenge whether the requested capability actually advances the Jarvis/Athos objective.",
        triggers=("objectif", "produit", "roadmap", "vision", "jarvis", "ux", "workflow"),
        outputs=("scope_decision", "user_value", "non_goals"),
    ),
    ReviewStage(
        "engineering_review",
        "Engineering review",
        "Lock architecture, data flow, interfaces, edge cases, and tests before implementation.",
        triggers=("code", "impl", "architecture", "module", "endpoint", "api", "refactor", "bug"),
        outputs=("files", "interfaces", "tests"),
    ),
    ReviewStage(
        "security_review",
        "Security review",
        "Scope permissions and reversibility for shell, devices, network, secrets, installs, and process control.",
        triggers=("security", "secur", "device", "reseau", "network", "shell", "install", "token", "secret", "pid", "kill"),
        outputs=("permission_scope", "rollback", "observable_stop_method"),
        risk="high",
    ),
    ReviewStage(
        "austerity_review",
        "Local austerity review",
        "Find the useful local/offline path before spending context, cloud, network, or hardware.",
        triggers=("offline", "local", "sans rien", "hors ligne", "hors reseau", "austerite", "austere"),
        outputs=("local_path", "deferred_queue", "energy_minimization"),
    ),
    ReviewStage(
        "qa_review",
        "QA review",
        "Run focused tests, business scenarios, regression checks, and smoke endpoints.",
        triggers=("test", "bug", "corrige", "prod", "preprod", "regression", "smoke"),
        outputs=("test_plan", "results", "remaining_risk"),
    ),
    ReviewStage(
        "release_review",
        "Release review",
        "Verify diff scope, commit, push, memory checkpoint, and post-change observability.",
        triggers=("commit", "push", "release", "ship", "deploy", "publie"),
        outputs=("diff_scope", "commit", "push", "drive_memory"),
        risk="medium",
    ),
    ReviewStage(
        "retro_checkpoint",
        "Retro checkpoint",
        "Persist what changed, why, evidence, tests, and next useful gap.",
        triggers=("checkpoint", "memoire", "memory", "done", "rapport"),
        outputs=("session_report", "memory_update"),
        always=True,
    ),
)


def stages() -> list[dict[str, Any]]:
    return [stage.to_dict() for stage in STAGES]


def plan(objective: str, changed_files: list[str] | None = None) -> dict[str, Any]:
    q = (objective or "").lower()
    changed_files = changed_files or []
    selected: list[ReviewStage] = []
    for stage in STAGES:
        if stage.always or any(_has_trigger(q, trigger) for trigger in stage.triggers):
            selected.append(stage)
    if changed_files and not any(stage.id == "engineering_review" for stage in selected):
        selected.append(_stage("engineering_review"))
    if changed_files and not any(stage.id == "qa_review" for stage in selected):
        selected.append(_stage("qa_review"))
    requires_approval = any(stage.risk == "high" for stage in selected) or _looks_mutating(q)
    return {
        "source": "gstack_inspired_athos_native_review_pipeline",
        "objective": (objective or "")[:500],
        "selected": [stage.to_dict() for stage in _dedupe(selected)],
        "requires_approval": requires_approval,
        "changed_files": changed_files,
        "operating_rule": "select_review_stages_by_situation_not_by_engine_identity",
        "next": "run_selected_reviews_then_execute_smallest_reversible_step",
    }


def _stage(stage_id: str) -> ReviewStage:
    for stage in STAGES:
        if stage.id == stage_id:
            return stage
    raise KeyError(stage_id)


def _dedupe(rows: list[ReviewStage]) -> list[ReviewStage]:
    seen: set[str] = set()
    result: list[ReviewStage] = []
    for row in rows:
        if row.id in seen:
            continue
        seen.add(row.id)
        result.append(row)
    return result


def _looks_mutating(q: str) -> bool:
    return any(_has_trigger(q, token) for token in (
        "modifie", "ecris", "ecris", "supprime", "delete", "install", "commit", "push",
        "deploy", "lance", "kill", "stop", "scan", "controle", "controle",
    ))


def _has_trigger(text: str, trigger: str) -> bool:
    trigger = trigger.strip().lower()
    if not trigger:
        return False
    if " " in trigger:
        return trigger in text
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(trigger)}(?![a-z0-9])", text))
