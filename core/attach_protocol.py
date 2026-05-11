"""Mandatory Athos attach protocol for external LLM engines."""
from __future__ import annotations

import uuid
from typing import Any

try:
    from . import config, session_kernel, sync_manager
    from .capabilities import status_report
    from .named_protocols import list_protocols, match_protocol, run_protocol
    from .registries import device_registry, hardware_registry, skill_registry
except ImportError:
    import config
    import session_kernel
    import sync_manager
    from capabilities import status_report
    from named_protocols import list_protocols, match_protocol, run_protocol
    from registries import device_registry, hardware_registry, skill_registry


PROTOCOL_VERSION = "athos-attach-v1"
PROMPT_FILE = config.ATHOS_PATH / "ATHOS_ATTACH_PROMPT.md"


RULES = [
    "Athos est l'identité principale; le LLM attaché est seulement un moteur.",
    "Avant toute réponse/action, appeler /api/attach puis utiliser le context pack reçu.",
    "Toute action, décision, commande ou blocage doit être reporté via /api/report.",
    "Si Athos est indisponible, mode cache lecture seule: aucune mutation, aucun coût API payant.",
    "Mutation système, écriture fichier, installation, shell, commit/push: plan visible + accord utilisateur.",
    "Ne jamais exposer de chaîne de pensée brute; exposer un journal opérationnel vérifiable.",
]


def _engine_name(payload: dict[str, Any]) -> str:
    return str(payload.get("engine") or payload.get("engine_name") or payload.get("client") or "unknown_engine")[:160]


def _capability_pack() -> dict[str, Any]:
    return {
        "named_protocols": list_protocols(),
        "skills": skill_registry(),
        "devices": device_registry(),
        "hardware": hardware_registry(),
        "sync": sync_manager.status(),
    }


def context_for_attach(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    max_chars = int(payload.get("max_chars") or session_kernel.MAX_CONTEXT_CHARS)
    return {
        "identity": "A.T.H.O.S.",
        "role": "sovereign_layer_for_memory_context_cognition_and_skills",
        "rules": RULES,
        "session": session_kernel.status(),
        "context_pack": session_kernel.context_pack(max_chars=max_chars),
        "latest_checkpoint": session_kernel.latest_checkpoint(),
        "recent_messages": session_kernel.latest_messages(limit=12),
        "capabilities_text": status_report(),
        "capabilities": _capability_pack(),
        "cost_policy": config.spend_policy(),
        "endpoints": {
            "attach": "/api/attach",
            "context_pack": "/api/context_pack",
            "delegate": "/api/delegate",
            "report": "/api/report",
            "checkpoint": "/api/checkpoint",
            "sync_status": "/api/sync/status",
        },
    }


def attach_engine(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    attach_id = str(payload.get("attach_id") or uuid.uuid4().hex)
    engine = _engine_name(payload)
    event = session_kernel.record_attach(
        attach_id,
        engine,
        meta={
            "protocol_version": PROTOCOL_VERSION,
            "client": payload.get("client", ""),
            "scope": payload.get("scope", "default"),
            "declared_user": payload.get("user", ""),
        },
    )
    return {
        "ok": True,
        "protocol_version": PROTOCOL_VERSION,
        "attach_id": attach_id,
        "engine": engine,
        "identity": "Athos",
        "must_report": True,
        "offline_policy": "read_only_cache_no_mutation",
        "event": event,
        **context_for_attach(payload),
    }


def delegate(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    attach_id = str(payload.get("attach_id") or "")
    engine = _engine_name(payload)
    request = str(payload.get("request") or payload.get("message") or "")
    protocol = match_protocol(request)
    if protocol:
        result = run_protocol(protocol, payload)
        decision = f"named_protocol:{protocol}"
        text = result.get("text", "")
        requires_confirmation = bool(result.get("protocol", {}).get("requires_approval", True))
    else:
        decision = "athos_context_first"
        text = (
            "Athos a reçu la délégation. Réponds en tant que moteur Athos avec le context pack, "
            "puis reporte les actions via /api/report. Toute mutation reste permissionnée."
        )
        requires_confirmation = _looks_risky(request)
    event = session_kernel.record_delegate(
        attach_id,
        engine,
        request,
        decision,
        meta={"requires_confirmation": requires_confirmation, "protocol": protocol or ""},
    )
    return {
        "ok": True,
        "attach_id": attach_id,
        "decision": decision,
        "recommended_engine": "athos_kernel",
        "requires_confirmation": requires_confirmation,
        "response_or_plan": text,
        "context": context_for_attach({"max_chars": 2_000}),
        "event": event,
    }


def report(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    attach_id = str(payload.get("attach_id") or "")
    engine = _engine_name(payload)
    summary = str(payload.get("summary") or payload.get("message") or "report received")
    status = str(payload.get("status") or "reported")
    event = session_kernel.record_report(attach_id, engine, summary, status=status, meta=payload.get("meta") or {})
    checkpoint_event = None
    if payload.get("checkpoint"):
        cp = payload["checkpoint"] if isinstance(payload["checkpoint"], dict) else {}
        checkpoint_event = session_kernel.checkpoint(
            cp.get("goal", summary),
            decisions=cp.get("decisions", []),
            tasks=cp.get("tasks", []),
            files=cp.get("files", []),
        )
    warnings = []
    if not attach_id:
        warnings.append("attach_id manquant: report accepté mais non relié à une IA attachée")
    return {"ok": True, "event": event, "checkpoint": checkpoint_event, "warnings": warnings}


def attach_prompt() -> str:
    if PROMPT_FILE.exists():
        return PROMPT_FILE.read_text("utf-8")
    return "\n".join([
        "# ATHOS attach prompt",
        "Tu es un moteur d'Athos, pas l'identité principale.",
        "Avant de répondre, appelle /api/attach et utilise le context pack.",
        "Reporte actions et blocages via /api/report.",
    ])


def attached_engines(limit: int = 20) -> list[dict[str, Any]]:
    rows = []
    for event in session_kernel.read_events(limit=limit * 4):
        if event.get("type") == "attach":
            rows.append({
                "attach_id": event.get("attach_id", ""),
                "engine": event.get("engine", ""),
                "ts": event.get("ts", ""),
                "meta": event.get("meta", {}),
            })
    return rows[-limit:]


def _looks_risky(text: str) -> bool:
    q = (text or "").lower()
    return any(token in q for token in (
        "install", "installe", "supprime", "delete", "kill", "commit", "push",
        "écris", "ecris", "modifie", "shell", "terminal", "scan", "sécurise", "securise",
    ))
