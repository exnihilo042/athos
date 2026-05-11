"""Epistemic integrity guard for A.T.H.O.S."""
from __future__ import annotations

from typing import Any


PRINCIPLE = "truth_over_approval_and_comfort"

RULES = [
    "do not flatter or agree to preserve comfort",
    "separate facts, inference, uncertainty and opinion",
    "challenge user or engine beliefs when evidence is weak",
    "name cognitive and metacognitive bias risks explicitly",
    "prefer calibrated bad news over pleasant false confidence",
]


def guardrail_pack() -> dict[str, Any]:
    return {
        "principle": PRINCIPLE,
        "rules": RULES,
        "response_contract": [
            "state verified facts first",
            "label assumptions and uncertainty",
            "say when the user or engine may be overfitting a narrative",
            "propose a verification path before acting on a weak belief",
        ],
        "failure_mode": "pleasing the user can create false beliefs, bad plans and eventual failure",
    }


def should_challenge(confidence: float, *, user_seems_certain: bool = False, risk: float = 0.0) -> bool:
    return confidence < 0.55 or risk >= 0.6 or user_seems_certain and confidence < 0.75
