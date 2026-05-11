"""Named Athos protocols.

These are visible, callable routines. V1 returns plans and safe local actions;
anything risky remains permission-gated by the caller/UI.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

try:
    from . import session_kernel
except ImportError:
    import session_kernel


@dataclass
class NamedProtocol:
    name: str
    purpose: str
    steps: list[str] = field(default_factory=list)
    requires_approval: bool = True
    risk: str = "medium"
    status: str = "planned"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_text(self) -> str:
        approval = "accord requis" if self.requires_approval else "executable localement"
        lines = [f"▶ {self.name} — {self.purpose}", f"Statut: {self.status}; risque: {self.risk}; {approval}."]
        lines.extend(f"• {step}" for step in self.steps)
        return "\n".join(lines)


PROTOCOLS: dict[str, dict[str, Any]] = {
    "ATHOS_STATUS": {
        "purpose": "résumer l'état système, mémoire, moteurs, coûts, jobs et blocages",
        "steps": ["lire session kernel", "lire observabilité", "résumer risques et prochaines actions"],
        "requires_approval": False,
        "risk": "low",
    },
    "ATHOS_SECURE_DEVICE": {
        "purpose": "sécuriser un appareil explicitement autorisé",
        "steps": [
            "vérifier l'autorisation et le scope de l'appareil",
            "inventorier ports, agents, permissions et logs",
            "proposer corrections défensives avant mutation",
            "appliquer seulement après accord visible",
        ],
        "risk": "high",
    },
    "ATHOS_SCAN_NETWORK": {
        "purpose": "scan défensif d'un réseau explicitement autorisé",
        "steps": [
            "confirmer le réseau et l'autorisation",
            "choisir un scan non intrusif",
            "journaliser commandes, cibles et résultats",
            "rapporter risques sans action cachée",
        ],
        "risk": "high",
    },
    "ATHOS_SELF_IMPROVE": {
        "purpose": "détecter un gap, proposer une compétence, tester, commit/push et mémoriser",
        "steps": [
            "décrire le gap",
            "chercher sources fiables",
            "préparer patch minimal",
            "demander accord pour mutations",
            "tester, commit/push, checkpoint",
        ],
        "risk": "medium",
    },
    "ATHOS_SYNC": {
        "purpose": "synchroniser mémoire locale, Drive, GitHub et jobs différés",
        "steps": ["lire outbox locale", "repérer conflits", "proposer replay contrôlé", "écrire récap"],
        "risk": "medium",
    },
    "ATHOS_FAILOVER_TEST": {
        "purpose": "vérifier sans dépense que la bascule moteur conserve requête, checkpoint et contexte",
        "steps": [
            "lire les moteurs disponibles",
            "simuler une limite/session sur le moteur courant",
            "calculer le moteur suivant selon l'ordre configuré",
            "retourner un resume_pack avec requête, checkpoint et hash de contexte",
        ],
        "requires_approval": False,
        "risk": "low",
    },
    "ATHOS_CLEAN_ROOM": {
        "purpose": "ramener l'environnement local à un état lisible et minimal",
        "steps": [
            "lister process/ports/jobs",
            "identifier ce qui appartient à Athos",
            "proposer stop/cleanup",
            "ne rien tuer sans méthode visible et scope clair",
        ],
        "risk": "medium",
    },
}


def list_protocols() -> list[dict[str, Any]]:
    return [
        NamedProtocol(name=name, **spec).to_dict()
        for name, spec in sorted(PROTOCOLS.items())
    ]


def match_protocol(text: str) -> str | None:
    q = (text or "").upper()
    for name in PROTOCOLS:
        if name in q:
            return name
    aliases = {
        "STATUS ATHOS": "ATHOS_STATUS",
        "CE QUI TOURNE": "ATHOS_STATUS",
        "SYNCHRONISE": "ATHOS_SYNC",
        "FAILOVER": "ATHOS_FAILOVER_TEST",
        "BASCULE MOTEUR": "ATHOS_FAILOVER_TEST",
        "AUTO AMELIORE": "ATHOS_SELF_IMPROVE",
        "AUTO-AMELIORE": "ATHOS_SELF_IMPROVE",
        "SECURISE": "ATHOS_SECURE_DEVICE",
        "SCAN NETWORK": "ATHOS_SCAN_NETWORK",
        "NETTOIE": "ATHOS_CLEAN_ROOM",
    }
    normalized = q.replace("É", "E").replace("È", "E")
    for alias, name in aliases.items():
        if alias in normalized:
            return name
    return None


def run_protocol(name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    protocol_name = (name or "").upper()
    if protocol_name not in PROTOCOLS:
        return {
            "ok": False,
            "error": f"protocole inconnu: {name}",
            "available": sorted(PROTOCOLS),
        }
    plan = NamedProtocol(name=protocol_name, **PROTOCOLS[protocol_name])
    event = session_kernel.record_action(
        "named_protocol",
        protocol_name,
        plan.status,
        engine="athos_kernel",
        meta={"protocol": plan.to_dict(), "payload": payload or {}},
    )
    return {"ok": True, "protocol": plan.to_dict(), "text": plan.as_text(), "event": event}
