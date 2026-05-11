"""Deterministic failover contract checks for Athos.

No external LLM is called here. This proves that a failing engine can be
replaced while preserving the request, checkpoint, and context pack used to
resume work.
"""
from __future__ import annotations

import hashlib
from typing import Any

try:
    from . import config, engine_router, session_kernel
except ImportError:
    import config
    import engine_router
    import session_kernel


def simulate(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    available = _available_from_payload(payload)
    current = str(payload.get("current") or payload.get("failed_engine") or (available[0] if available else "none"))
    request = str(payload.get("request") or "reprendre la même demande avec le même contexte")
    reason = str(payload.get("reason") or "simulated_limit")
    context = session_kernel.context_pack(max_chars=int(payload.get("max_chars") or 4_000))
    checkpoint = session_kernel.latest_checkpoint() or {}
    order = engine_router.configured_order(config.ATHOS_ENGINE_ORDER)
    next_engine = engine_router.next_engine(current, available, order=order)
    context_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()[:16]
    result = {
        "ok": bool(available) and next_engine != "none",
        "no_api_calls": True,
        "current": current,
        "next": next_engine,
        "available": available,
        "reason": reason,
        "context_preserved": True,
        "resume_pack": {
            "identity": "A.T.H.O.S.",
            "request": request,
            "checkpoint_goal": checkpoint.get("goal", ""),
            "checkpoint_tasks": checkpoint.get("tasks", []),
            "context_hash": context_hash,
            "context_chars": len(context),
        },
    }
    session_kernel.record_action(
        "failover_simulation",
        f"{current}→{next_engine}",
        reason,
        engine="athos_kernel",
        meta={"context_hash": context_hash, "request": request[:300]},
    )
    return result


def _available_from_payload(payload: dict[str, Any]) -> list[str]:
    raw = payload.get("available")
    if isinstance(raw, list):
        requested = [str(item).strip() for item in raw if str(item).strip()]
        order = engine_router.configured_order(config.ATHOS_ENGINE_ORDER)
        return [engine for engine in order if engine in requested]
    return engine_router.configured_order(config.ATHOS_ENGINE_ORDER)
