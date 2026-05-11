"""Model-neutral Athos session kernel.

The kernel is the handoff layer between engines: it stores conversation turns,
tool events, and checkpoints in Drive as JSONL so any provider can resume the
same work without depending on an in-memory server process.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from . import config
except ImportError:
    import config

SESSION_FILE = config.DRIVE / "athos_session_kernel.jsonl"
MAX_CONTEXT_CHARS = 4_000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_text(value: str, limit: int = 8_000) -> str:
    return (value or "").replace("\x00", "")[:limit]


def _append(event: dict[str, Any]) -> dict[str, Any]:
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    enriched = {
        "id": event.get("id") or uuid.uuid4().hex,
        "ts": event.get("ts") or _now(),
        **event,
    }
    with SESSION_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(enriched, ensure_ascii=False, separators=(",", ":")) + "\n")
    return enriched


def read_events(limit: int | None = None) -> list[dict[str, Any]]:
    if not SESSION_FILE.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in SESSION_FILE.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            events.append({"type": "corrupt", "ts": _now(), "raw": line[:500]})
    return events[-limit:] if limit else events


def record_exchange(user: str, assistant: str, engine: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return _append({
        "type": "exchange",
        "engine": engine,
        "user": _safe_text(user),
        "assistant": _safe_text(assistant),
        "meta": meta or {},
    })


def record_action(name: str, label: str = "", result: str = "", engine: str = "", meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return _append({
        "type": "action",
        "engine": engine,
        "name": _safe_text(name, 200),
        "label": _safe_text(label, 500),
        "result": _safe_text(result, 2_000),
        "meta": meta or {},
    })


def record_summary(summary: str, source: str = "athos") -> dict[str, Any]:
    return _append({
        "type": "summary",
        "source": _safe_text(source, 120),
        "summary": _safe_text(summary, 2_000),
    })


def record_attach(attach_id: str, engine: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return _append({
        "type": "attach",
        "attach_id": _safe_text(attach_id, 120),
        "engine": _safe_text(engine, 160),
        "meta": meta or {},
    })


def record_delegate(attach_id: str, engine: str, request: str, decision: str,
                    meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return _append({
        "type": "delegate",
        "attach_id": _safe_text(attach_id, 120),
        "engine": _safe_text(engine, 160),
        "request": _safe_text(request, 2_000),
        "decision": _safe_text(decision, 500),
        "meta": meta or {},
    })


def record_report(attach_id: str, engine: str, summary: str, status: str = "reported",
                  meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return _append({
        "type": "report",
        "attach_id": _safe_text(attach_id, 120),
        "engine": _safe_text(engine, 160),
        "summary": _safe_text(summary, 2_000),
        "status": _safe_text(status, 120),
        "meta": meta or {},
    })


def summarize_recent(limit: int = 20) -> str:
    events = read_events(limit=limit)
    exchanges = [e for e in events if e.get("type") == "exchange"]
    actions = [e for e in events if e.get("type") == "action"]
    attaches = [e for e in events if e.get("type") == "attach"]
    cp = latest_checkpoint()
    parts = [
        f"échanges récents: {len(exchanges)}",
        f"actions récentes: {len(actions)}",
    ]
    if cp:
        parts.append(f"objectif actif: {cp.get('goal', '')[:180]}")
        tasks = cp.get("tasks") or []
        if tasks:
            parts.append("tâches: " + "; ".join(tasks[:4]))
    if exchanges:
        last = exchanges[-1]
        parts.append(f"dernier échange via {last.get('engine', '')}: {last.get('user', '')[:160]}")
    if attaches:
        parts.append(f"moteur attaché: {attaches[-1].get('engine', '')}")
    return " | ".join(parts)


def checkpoint(goal: str, decisions: list[str] | None = None,
               tasks: list[str] | None = None, files: list[str] | None = None) -> dict[str, Any]:
    """Snapshot current work state — any engine can resume from this."""
    return _append({
        "type": "checkpoint",
        "goal": _safe_text(goal, 500),
        "decisions": [_safe_text(d, 200) for d in (decisions or [])],
        "tasks": [_safe_text(t, 200) for t in (tasks or [])],
        "files": [_safe_text(f, 200) for f in (files or [])],
    })


def latest_checkpoint() -> dict[str, Any] | None:
    """Return the most recent checkpoint event, if any."""
    for event in reversed(read_events()):
        if event.get("type") == "checkpoint":
            return event
    return None


def latest_messages(limit: int = 12) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for event in read_events():
        if event.get("type") != "exchange":
            continue
        user = event.get("user", "")
        assistant = event.get("assistant", "")
        if user:
            messages.append({"role": "user", "content": user})
        if assistant:
            messages.append({"role": "assistant", "content": assistant})
    return messages[-limit:]


def context_pack(max_chars: int = MAX_CONTEXT_CHARS) -> str:
    chunks: list[str] = []

    # Latest checkpoint pinned at top — survives engine switch
    cp = latest_checkpoint()
    if cp:
        chunks.append(f"§goal:{cp.get('goal', '')}")
        for d in (cp.get("decisions") or [])[:3]:
            chunks.append(f"§decision:{d}")
        for t in (cp.get("tasks") or [])[:5]:
            chunks.append(f"§task:{t}")
        for f in (cp.get("files") or [])[:3]:
            chunks.append(f"§file:{f}")

    # Recent exchanges and actions
    for event in read_events(limit=40):
        if event.get("type") == "exchange":
            chunks.append(
                f"§ex:{event.get('ts')}|eng:{event.get('engine', '')}"
                f"|u:{event.get('user', '')[:200]}|a:{event.get('assistant', '')[:400]}"
            )
        elif event.get("type") == "action":
            chunks.append(
                f"§act:{event.get('ts')}|{event.get('name', '')}:{event.get('label', '')[:100]}"
            )
        elif event.get("type") == "summary":
            chunks.append(f"§summary:{event.get('ts')}|{event.get('summary', '')[:400]}")
        elif event.get("type") == "attach":
            chunks.append(
                f"§attach:{event.get('ts')}|id:{event.get('attach_id', '')}"
                f"|engine:{event.get('engine', '')}"
            )
        elif event.get("type") == "delegate":
            chunks.append(
                f"§delegate:{event.get('ts')}|id:{event.get('attach_id', '')}"
                f"|decision:{event.get('decision', '')[:180]}"
            )
        elif event.get("type") == "report":
            chunks.append(
                f"§report:{event.get('ts')}|id:{event.get('attach_id', '')}"
                f"|{event.get('status', '')}:{event.get('summary', '')[:220]}"
            )

    pack = "\n".join(chunks)
    return pack[-max_chars:]


def status() -> dict[str, Any]:
    events = read_events()
    last = events[-1] if events else None
    cp = latest_checkpoint()
    return {
        "file": str(SESSION_FILE),
        "events": len(events),
        "exchanges": sum(1 for e in events if e.get("type") == "exchange"),
        "actions": sum(1 for e in events if e.get("type") == "action"),
        "summaries": sum(1 for e in events if e.get("type") == "summary"),
        "attaches": sum(1 for e in events if e.get("type") == "attach"),
        "delegates": sum(1 for e in events if e.get("type") == "delegate"),
        "reports": sum(1 for e in events if e.get("type") == "report"),
        "recent_summary": summarize_recent(),
        "checkpoint": {
            "goal": cp.get("goal", "") if cp else None,
            "tasks": cp.get("tasks", []) if cp else [],
        },
        "last_event": {
            "id": last.get("id"),
            "ts": last.get("ts"),
            "type": last.get("type"),
            "engine": last.get("engine", ""),
        } if last else None,
    }
