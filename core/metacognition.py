"""Athos metacognition: adaptive, non-immutable cognitive base.

This layer is model-neutral. It does not try to be another LLM prompt; it
describes how Athos should frame a situation before any engine answers.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

try:
    from . import config, session_kernel
    from .situational_decision import AXES
except ImportError:
    import config
    import session_kernel
    from situational_decision import AXES


PRINCIPLES = [
    "identity_invariant_engines_interchangeable",
    "non_immutable_rules_adapt_to_context",
    "exact_result_from_incomplete_or_noisy_data",
    "no_hallucination_precise_gap_naming",
    "intuition_pause_verify_conclude_act",
    "visible_observable_background_work",
    "controlled_self_extension",
    "situational_decision_for_engine_skill_tool_action_and_protocol",
]


@dataclass
class CognitiveAssessment:
    request: str
    mode: str = "situational_resolution"
    known_state: list[str] = field(default_factory=list)
    uncertainty_model: list[str] = field(default_factory=list)
    gap_strategy: list[str] = field(default_factory=list)
    adaptation_rules: list[str] = field(default_factory=list)
    engine_criteria: list[str] = field(default_factory=list)
    stop_conditions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"principles": PRINCIPLES}

    def events(self) -> list[dict[str, Any]]:
        rows = [
            ("metacognition", f"mode={self.mode}; principles={','.join(PRINCIPLES[:3])}"),
        ]
        rows += [("known", item) for item in self.known_state]
        rows += [("uncertainty", item) for item in self.uncertainty_model]
        rows += [("gap_strategy", item) for item in self.gap_strategy]
        rows += [("adaptation", item) for item in self.adaptation_rules]
        rows += [("engine_criteria", item) for item in self.engine_criteria]
        rows += [("stop_condition", item) for item in self.stop_conditions]
        return [{"thinking": {"kind": kind, "text": text}} for kind, text in rows if text]


def assess(request: str, available_engines: list[str] | None = None) -> CognitiveAssessment:
    q = (request or "").lower()
    available_engines = available_engines or []
    assessment = CognitiveAssessment(
        request=(request or "")[:500],
        known_state=[
            "Athos is the stable identity; the active model is a replaceable engine.",
            f"Available engines: {', '.join(available_engines) if available_engines else 'none detected'}.",
            f"Cost policy: {config.spend_policy()['mode']}.",
        ],
        uncertainty_model=[
            "Missing data must become named gaps, not guesses.",
            "No rule is immutable; routing and process adapt to context, risk, evidence, and available tools.",
        ],
        gap_strategy=[
            "If enough evidence exists: solve directly.",
            "If evidence is partial: infer from first principles, analogies, and verified local memory.",
            "If capability is missing: identify exact missing capability, then propose controlled acquisition.",
        ],
        adaptation_rules=[
            "Pause before action; verify existing state before mutation.",
            "Prefer the smallest action that increases certainty or capability.",
            "Persist decisions and checkpoints so another engine can resume.",
        ],
        engine_criteria=[
            "Choose any X by situation: engine, skill, tool, action, protocol, autonomy level, and acquisition method.",
            f"Decision axes: {', '.join(AXES)}.",
            "Never hardcode permanent mappings; use current objective, risk, evidence, reversibility, cost, and observability.",
            "Failover must preserve identity, request, checkpoint, and memory pack.",
        ],
        stop_conditions=[
            "Stop or ask when mutation is risky, authorization is missing, or uncertainty cannot be reduced safely.",
        ],
    )
    if any(word in q for word in ("installe", "modifie", "supprime", "commit", "push", "run", "lance")):
        assessment.mode = "controlled_action"
        assessment.stop_conditions.append("User-visible approval required before mutation or external side effect.")
    if any(word in q for word in ("apprendre", "capacité", "competence", "compétence", "self", "améliore", "ameliore")):
        assessment.mode = "self_extension"
        assessment.gap_strategy.append("Skill acquisition must remain plan-first, tested, rollbackable, and checkpointed.")
    if any(word in q for word in ("pourquoi", "réfléchis", "raisonne", "cognition", "meta", "métacognition")):
        assessment.mode = "metacognitive_analysis"
        assessment.adaptation_rules.append("Expose operational reasoning journal, not hidden chain-of-thought.")
    return assessment


def status() -> dict[str, Any]:
    checkpoint = session_kernel.latest_checkpoint() or {}
    return {
        "principles": PRINCIPLES,
        "current_checkpoint": checkpoint.get("goal", ""),
        "session_summary": session_kernel.summarize_recent(),
        "non_immutable_base": True,
        "applies_to_all_engines": True,
        "core_loop": [
            "map_known_unknown_inferable",
            "attempt_direct_resolution",
            "situationally_choose_engine_skill_tool_action_or_acquisition",
            "name_precise_gap",
            "acquire_or_route_if_needed",
            "integrate_test_checkpoint",
            "resolve_one_shot_when_ready",
        ],
        "decision_axes": AXES,
    }
