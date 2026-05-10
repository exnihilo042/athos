"""Model-neutral Athos session kernel.

The kernel is the handoff layer between engines: it stores conversation turns
and operational events in Drive as JSONL so any provider can resume the same
work without depending on an in-memory server process.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import config
except ModuleNotFoundError:
    from core import config

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
    for event in read_events(limit=40):
        if event.get("type") == "exchange":
            chunks.append(
                f"§kernel:{event.get('ts')}|engine:{event.get('engine','')}"
                f"|u:{event.get('user','')[:300]}|a:{event.get('assistant','')[:500]}"
            )
        elif event.get("type") == "action":
            chunks.append(
                f"§kernel_action:{event.get('ts')}|engine:{event.get('engine','')}"
                f"|name:{event.get('name','')}|label:{event.get('label','')[:200]}"
            )
    pack = "\n".join(chunks)
    return pack[-max_chars:]


def status() -> dict[str, Any]:
    events = read_events()
    last = events[-1] if events else None
    exchanges = sum(1 for event in events if event.get("type") == "exchange")
    actions = sum(1 for event in events if event.get("type") == "action")
    return {
        "file": str(SESSION_FILE),
        "events": len(events),
        "exchanges": exchanges,
        "actions": actions,
        "last_event": {
            "id": last.get("id"),
            "ts": last.get("ts"),
            "type": last.get("type"),
            "engine": last.get("engine", ""),
            "name": last.get("name", ""),
        } if last else None,
    }
