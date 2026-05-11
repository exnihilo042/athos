"""Visible reasoning journal for Athos.

This module does not expose hidden chain-of-thought. It creates an operational
trace: facts, uncertainty, planned checks, selected engine, and guardrails.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

try:
    import config
except ModuleNotFoundError:
    from core import config


@dataclass
class ReasoningFrame:
    goal: str
    known_facts: list[str] = field(default_factory=list)
    uncertainty: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    acquisition: list[str] = field(default_factory=list)
    selected_engine: str = "none"
    action_policy: str = "visible_approval_required_for_mutations"
    cost_policy: str = "zero_paid_api"

    def events(self) -> list[dict[str, Any]]:
        rows = [
            ("goal", self.goal),
            ("policy", f"coût={self.cost_policy}; action={self.action_policy}"),
            ("engine", f"Athos via {self.selected_engine}"),
        ]
        rows += [("fact", item) for item in self.known_facts]
        rows += [("uncertainty", item) for item in self.uncertainty]
        rows += [("gap", item) for item in self.gaps]
        rows += [("acquire", item) for item in self.acquisition]
        return [{"thinking": {"kind": kind, "text": text}} for kind, text in rows if text]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _looks_like_mutation(msg: str) -> bool:
    q = msg.lower()
    needles = [
        "installe", "install", "supprime", "delete", "écris", "ecris",
        "modifie", "commit", "push", "lance", "run", "corrige", "fix",
        "déploie", "deploie", "kill", "stop", "start",
    ]
    return any(word in q for word in needles)


def _looks_like_research(msg: str) -> bool:
    q = msg.lower()
    return any(word in q for word in ("cherche", "recherche", "doc", "github", "source", "apprendre", "universitaire"))


def build_frame(msg: str, available_engines: list[str], current_engine: str) -> ReasoningFrame:
    goal = msg.strip()[:240] or "Traiter la demande utilisateur."
    facts = [
        "Athos est l'identité unique; les LLMs sont des moteurs interchangeables.",
        f"Moteurs disponibles: {', '.join(available_engines) if available_engines else 'aucun'}.",
    ]
    uncertainty: list[str] = []
    gaps: list[str] = []
    acquisition: list[str] = []

    if _looks_like_mutation(msg):
        facts.append("La demande peut modifier le système; validation visible requise avant action risquée.")
    else:
        facts.append("La demande peut être traitée sans mutation directe si aucune action outil n'est nécessaire.")

    if _looks_like_research(msg):
        gaps.append("Sources externes à vérifier avant d'intégrer une nouvelle capacité.")
        acquisition.append("Chercher documentation officielle, GitHub ou source académique selon le besoin.")

    if not available_engines:
        uncertainty.append("Aucun moteur disponible détecté; Athos devra répondre via état local ou signaler le blocage.")

    selected = current_engine if current_engine in available_engines else (available_engines[0] if available_engines else "none")
    return ReasoningFrame(
        goal=goal,
        known_facts=facts,
        uncertainty=uncertainty,
        gaps=gaps,
        acquisition=acquisition,
        selected_engine=selected,
        cost_policy=config.spend_policy()["mode"],
    )
