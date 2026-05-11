"""Generic situational decision layer for Athos.

Athos should not rely on fixed mappings like "code -> Claude" or
"email -> Gmail skill". It evaluates the current situation across risk,
confidence, cost, reversibility, observability, and fit, then chooses the best
available option or asks for more evidence/approval.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


AXES = [
    "fit",
    "confidence",
    "risk",
    "reversibility",
    "cost",
    "latency",
    "observability",
    "memory_continuity",
]


@dataclass
class DecisionOption:
    name: str
    kind: str = "option"  # engine | skill | tool | action | protocol | unknown
    fit: float = 0.5
    confidence: float = 0.5
    risk: float = 0.5
    reversibility: float = 0.5
    cost: float = 0.0
    latency: float = 0.5
    observability: float = 0.5
    memory_continuity: float = 0.5
    requires_approval: bool = False
    reasons: list[str] = field(default_factory=list)

    def score(self) -> float:
        positive = (
            self.fit * 0.24
            + self.confidence * 0.18
            + self.reversibility * 0.12
            + self.observability * 0.16
            + self.memory_continuity * 0.14
        )
        negative = self.risk * 0.11 + self.cost * 0.03 + self.latency * 0.02
        approval_penalty = 0.05 if self.requires_approval else 0.0
        return round(positive - negative - approval_penalty, 4)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"score": self.score()}


@dataclass
class Decision:
    objective: str
    chosen: DecisionOption | None
    options: list[DecisionOption] = field(default_factory=list)
    policy: str = "situational_not_fixed"
    should_pause: bool = False
    pause_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "policy": self.policy,
            "chosen": self.chosen.to_dict() if self.chosen else None,
            "options": [option.to_dict() for option in self.options],
            "should_pause": self.should_pause,
            "pause_reason": self.pause_reason,
            "axes": AXES,
        }

    def events(self) -> list[dict[str, Any]]:
        rows = [
            ("decision", f"objective={self.objective[:160]}; policy={self.policy}"),
        ]
        if self.chosen:
            rows.append(("decision_choice", f"{self.chosen.kind}:{self.chosen.name}; score={self.chosen.score()}"))
        if self.should_pause:
            rows.append(("decision_pause", self.pause_reason))
        for option in self.options[:5]:
            rows.append(("decision_option", f"{option.kind}:{option.name}; score={option.score()}; risk={option.risk}; fit={option.fit}"))
        return [{"thinking": {"kind": kind, "text": text}} for kind, text in rows if text]


def decide(objective: str, raw_options: list[dict[str, Any]] | None = None) -> Decision:
    options = [_coerce_option(item) for item in (raw_options or [])]
    if not options:
        return Decision(
            objective=objective[:500],
            chosen=None,
            options=[],
            should_pause=True,
            pause_reason="no_available_option: acquire capability, ask for scope, or use local memory only",
        )
    ranked = sorted(options, key=lambda item: item.score(), reverse=True)
    chosen = ranked[0]
    should_pause = chosen.requires_approval or chosen.risk >= 0.75 or chosen.confidence < 0.35
    if chosen.requires_approval:
        pause = "approval_required_for_chosen_option"
    elif chosen.risk >= 0.75:
        pause = "risk_too_high_without_visible_plan"
    elif chosen.confidence < 0.35:
        pause = "confidence_too_low: reduce uncertainty before action"
    else:
        pause = ""
    return Decision(
        objective=objective[:500],
        chosen=chosen,
        options=ranked,
        should_pause=should_pause,
        pause_reason=pause,
    )


def option_from_engine(name: str, *, current: bool = False, available: bool = True) -> dict[str, Any]:
    return {
        "name": name,
        "kind": "engine",
        "fit": 0.65 + (0.1 if current else 0.0),
        "confidence": 0.75 if available else 0.1,
        "risk": 0.25,
        "reversibility": 0.9,
        "cost": 0.0 if name in {"chatgpt_plus", "claude_code", "ollama"} else 0.6,
        "latency": 0.35 if name != "ollama" else 0.15,
        "observability": 0.8,
        "memory_continuity": 0.9,
        "reasons": ["engine choice is situational; preserves Athos identity via attach/session kernel"],
    }


def _coerce_option(item: dict[str, Any]) -> DecisionOption:
    return DecisionOption(
        name=str(item.get("name") or item.get("id") or "unknown"),
        kind=str(item.get("kind") or "option"),
        fit=_num(item.get("fit"), 0.5),
        confidence=_num(item.get("confidence"), 0.5),
        risk=_num(item.get("risk"), 0.5),
        reversibility=_num(item.get("reversibility"), 0.5),
        cost=_num(item.get("cost"), 0.0),
        latency=_num(item.get("latency"), 0.5),
        observability=_num(item.get("observability"), 0.5),
        memory_continuity=_num(item.get("memory_continuity"), 0.5),
        requires_approval=bool(item.get("requires_approval", False)),
        reasons=[str(reason) for reason in item.get("reasons", [])],
    )


def _num(value: Any, default: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default
