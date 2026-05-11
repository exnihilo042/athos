"""Controlled self-improvement workflow for Athos."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

try:
    from . import session_kernel
except ImportError:
    import session_kernel


@dataclass
class ImprovementPlan:
    request: str
    gap: str
    research_sources: list[str] = field(default_factory=list)
    implementation_steps: list[str] = field(default_factory=list)
    validation_steps: list[str] = field(default_factory=list)
    mutation_requires_approval: bool = True

    def as_text(self) -> str:
        lines = [
            "▶ Plan d'auto-amélioration ATHOS :",
            f"• Gap détecté : {self.gap}",
            "• Sources à vérifier : " + ", ".join(self.research_sources),
            "• Implémentation contrôlée : " + " → ".join(self.implementation_steps),
            "• Validation : " + " → ".join(self.validation_steps),
            "Résultat attendu : nouvelle capacité disponible, testée, commit/push, mémoire mise à jour.",
            "— Lance quand tu veux.",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return asdict(self)


def detect_gap(request: str) -> str:
    q = request.lower()
    if any(word in q for word in ("gmail", "email", "mail")):
        return "connecteur email/Gmail opérable avec permissions et tests"
    if any(word in q for word in ("calendar", "agenda", "calendrier")):
        return "connecteur calendrier fiable avec lecture et actions contrôlées"
    if any(word in q for word in ("vision", "écran", "ecran", "image", "photo")):
        return "capacité vision locale/API sans dépense non autorisée"
    if any(word in q for word in ("deploy", "déploie", "deploie", "vps", "cloudflare")):
        return "déploiement permanent observable avec logs et stop method"
    return "capacité manquante à identifier précisément avant mutation"


def plan_self_improvement(request: str) -> ImprovementPlan:
    plan = ImprovementPlan(
        request=request[:500],
        gap=detect_gap(request),
        research_sources=[
            "mémoire Drive ATHOS",
            "documentation officielle du fournisseur",
            "GitHub/source ouverte pertinente",
            "tests locaux existants",
        ],
        implementation_steps=[
            "checkpoint avant mutation",
            "patch minimal",
            "tests ciblés",
            "commit/push",
            "mise à jour mémoire",
        ],
        validation_steps=[
            "pytest -q",
            "compileall",
            "test métier depuis Athos",
        ],
    )
    session_kernel.record_action(
        "self_improvement_plan",
        plan.gap,
        "plan generated",
        engine="athos_kernel",
        meta=plan.to_dict(),
    )
    return plan


def matches_self_improvement_request(msg: str) -> bool:
    q = msg.lower()
    return any(needle in q for needle in (
        "améliore-toi",
        "ameliore-toi",
        "auto-améliore",
        "auto ameliore",
        "installe une compétence",
        "ajoute une compétence",
        "self improvement",
        "self-improvement",
    ))
