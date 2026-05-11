"""Athos transformation stack.

An attached engine is the base vehicle. Athos can reconfigure it into a more
capable operational form depending on the situation: code operator, research
lab, self-improver, device operator, offline agent, and so on.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

try:
    from .situational_decision import decide
except ImportError:
    from situational_decision import decide


@dataclass(frozen=True)
class TransformationForm:
    name: str
    purpose: str
    triggers: tuple[str, ...] = ()
    modules: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    requires_approval: bool = False
    risk: float = 0.25

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


FORM_CATALOG = [
    TransformationForm(
        name="conversation_core",
        purpose="answer, synthesize, remember, and keep continuity across engines",
        triggers=("explique", "résume", "resume", "statut", "topo", "question"),
        modules=("memory_pack", "session_summary", "metacognition", "situational_decision"),
        constraints=("no hidden chain-of-thought", "persist useful summaries"),
        risk=0.1,
    ),
    TransformationForm(
        name="code_workbench",
        purpose="inspect, edit, test, commit and push code with repo memory",
        triggers=("code", "repo", "test", "corrige", "fix", "implémente", "implemente", "commit", "push"),
        modules=("repo_context", "test_runner", "git_sync", "rollback_awareness", "observability"),
        constraints=("read before edit", "tests before push", "never revert user changes"),
        requires_approval=False,
        risk=0.45,
    ),
    TransformationForm(
        name="research_lab",
        purpose="learn missing methods from official docs, GitHub, papers or reliable sources",
        triggers=("cherche", "recherche", "apprendre", "docs", "github", "paper", "universitaire"),
        modules=("source_triage", "gap_naming", "skill_proposal", "citation_memory"),
        constraints=("use primary sources for technical claims", "no paid API unless explicitly enabled"),
        risk=0.25,
    ),
    TransformationForm(
        name="self_improver",
        purpose="turn capability gaps into proposed, tested and checkpointed Athos skills",
        triggers=("auto-améliore", "auto ameliore", "compétence", "competence", "skill", "capacité", "capacite"),
        modules=("gap_detector", "pending_skill_registry", "sandbox_tests", "rollback", "checkpoint"),
        constraints=("plan first", "mutation requires approval", "rollback failed tests"),
        requires_approval=True,
        risk=0.55,
    ),
    TransformationForm(
        name="device_operator",
        purpose="operate authorized local devices, OS surfaces and future hardware interfaces",
        triggers=("appareil", "mac", "télé", "telephone", "téléphone", "camera", "lidar", "flipper", "wifi"),
        modules=("device_registry", "permission_scopes", "runtime_logs", "stop_methods", "hardware_plugins"),
        constraints=("authorized devices only", "defensive use only", "revocable control"),
        requires_approval=True,
        risk=0.8,
    ),
    TransformationForm(
        name="offline_survival",
        purpose="continue locally with memory, installed skills and queued sync work while offline",
        triggers=("offline", "hors ligne", "sans réseau", "sans reseau", "sync"),
        modules=("local_memory", "installed_skills", "ollama_fallback", "sync_outbox", "replay_plan"),
        constraints=("queue network actions", "no silent conflict overwrite"),
        risk=0.25,
    ),
]


def transformation_pack(engine: str = "unknown_engine", objective: str = "") -> dict[str, Any]:
    scored_options = []
    for form in FORM_CATALOG:
        fit = _fit(objective, form.triggers)
        scored_options.append({
            "name": form.name,
            "kind": "transformation_form",
            "fit": fit,
            "confidence": 0.7 if fit >= 0.5 else 0.45,
            "risk": form.risk,
            "reversibility": 0.85,
            "cost": 0.0,
            "latency": 0.2,
            "observability": 0.9,
            "memory_continuity": 0.95,
            "requires_approval": form.requires_approval,
            "reasons": [form.purpose],
        })
    decision = decide(objective or "general Athos operation", scored_options)
    primary_name = decision.chosen.name if decision.chosen else "conversation_core"
    primary = next((form for form in FORM_CATALOG if form.name == primary_name), FORM_CATALOG[0])
    secondary = [
        form for form in FORM_CATALOG
        if form.name != primary.name and _fit(objective, form.triggers) >= 0.55
    ][:3]
    return {
        "engine": engine,
        "objective": objective[:500],
        "primary_form": primary.to_dict(),
        "secondary_forms": [form.to_dict() for form in secondary],
        "decision": decision.to_dict(),
        "enabled_modules": sorted({*primary.modules, *(module for form in secondary for module in form.modules)}),
        "operational_gain": (
            "The attached engine is reconfigured from a stateless text model into a situational Athos operator "
            "with memory, decisioning, tools, observability, safety constraints and optional physical-world interfaces."
        ),
    }


def _fit(objective: str, triggers: tuple[str, ...]) -> float:
    q = (objective or "").lower()
    if not q:
        return 0.5
    hits = sum(1 for trigger in triggers if trigger in q)
    if hits == 0:
        return 0.35
    return min(1.0, 0.55 + hits * 0.15)
