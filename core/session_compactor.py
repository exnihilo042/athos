"""Non-destructive session summary writer for Athos handoffs."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

try:
    from . import config, session_kernel
except ImportError:
    import config
    import session_kernel


SUMMARY_FILE = config.DRIVE / "athos_session_summary.mem"


def build_summary(limit: int = 120) -> dict[str, Any]:
    events = session_kernel.read_events(limit=limit)
    checkpoint = session_kernel.latest_checkpoint() or {}
    exchanges = [e for e in events if e.get("type") == "exchange"][-6:]
    actions = [e for e in events if e.get("type") == "action"][-12:]
    reports = [e for e in events if e.get("type") == "report"][-6:]
    lines = [
        f"§session_summary:updated:{_now()}",
        f"§checkpoint:goal:{checkpoint.get('goal', '')}",
    ]
    for task in (checkpoint.get("tasks") or [])[:6]:
        lines.append(f"§checkpoint:task:{task}")
    for exchange in exchanges:
        lines.append(
            "§exchange:"
            f"{exchange.get('ts', '')}|eng:{exchange.get('engine', '')}"
            f"|u:{_clip(exchange.get('user', ''), 180)}"
            f"|a:{_clip(exchange.get('assistant', ''), 220)}"
        )
    for action in actions:
        lines.append(
            "§action:"
            f"{action.get('ts', '')}|{action.get('name', '')}"
            f"|{_clip(action.get('label', ''), 160)}|{_clip(action.get('result', ''), 160)}"
        )
    for report in reports:
        lines.append(
            "§report:"
            f"{report.get('ts', '')}|{report.get('engine', '')}"
            f"|{report.get('status', '')}|{_clip(report.get('summary', ''), 240)}"
        )
    text = "\n".join(lines) + "\n"
    return {
        "ok": True,
        "file": str(SUMMARY_FILE),
        "events_seen": len(events),
        "lines": len(lines),
        "text": text,
        "checkpoint_goal": checkpoint.get("goal", ""),
    }


def write_summary(limit: int = 120) -> dict[str, Any]:
    summary = build_summary(limit=limit)
    SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_FILE.write_text(summary["text"], "utf-8")
    session_kernel.record_summary(
        f"Session summary written to {SUMMARY_FILE.name}; lines={summary['lines']}",
        source="session_compactor",
    )
    return {k: v for k, v in summary.items() if k != "text"} | {"written": True}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clip(value: str, limit: int) -> str:
    return (value or "").replace("\n", " ").replace("|", "/")[:limit]
