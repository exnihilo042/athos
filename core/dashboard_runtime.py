"""Runtime payloads consumed by the ATHOS dashboard.

These helpers expose real local state only. Missing external integrations are
reported as unavailable instead of being replaced with backend mocks.
"""
from __future__ import annotations

import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:
    from . import athos_room, config, memory_status, session_kernel, task_queue
    from . import observability
    from .attach_protocol import attached_engines
    from .autonomous_loop import status as loop_status
except ImportError:
    import athos_room
    import config
    import memory_status
    import session_kernel
    import task_queue
    import observability
    from attach_protocol import attached_engines
    from autonomous_loop import status as loop_status


def conversation_health(base: dict[str, Any]) -> dict[str, Any]:
    """Add dashboard-friendly counters while preserving athos_room.health()."""
    queue = task_queue.summary()
    counts = queue.get("counts", {})
    room_summary = base.get("summary") or athos_room.summary()
    enriched = dict(base)
    enriched.update({
        "active_sessions": queue.get("active", 0),
        "total_messages": room_summary.get("total", base.get("checked_messages", 0)),
        "task_summary": {
            "total": queue.get("total", 0),
            "running": counts.get("running", 0),
            "done": counts.get("completed", 0),
            "blocked": counts.get("blocked", 0),
            "pending": counts.get("queued", 0),
            "paused": counts.get("paused", 0),
            "cancelled": counts.get("cancelled", 0),
        },
    })
    # Frontend handoff asked for a top-level `summary` task shape. Keep the
    # historical room summary under `room_summary` for backward compatibility.
    enriched["room_summary"] = room_summary
    enriched["summary"] = enriched["task_summary"]
    return enriched


def daily_report(report_type: str = "daily") -> dict[str, Any]:
    session = session_kernel.status()
    queue = task_queue.summary()
    room = athos_room.summary()
    responders = _responder_status()
    failovers = observability.recent_failover_events(limit=8)
    sections = [
        {
            "title": "Session",
            "content": session.get("recent_summary") or "Aucune activité session récente.",
            "data": session,
        },
        {
            "title": "Task queue",
            "content": _queue_sentence(queue),
            "data": queue,
        },
        {
            "title": "Responders",
            "content": _responders_sentence(responders),
            "data": responders,
        },
        {
            "title": "Failover",
            "content": f"{len(failovers)} événement(s) failover récent(s).",
            "data": {"events": failovers},
        },
    ]
    summary = {
        "total_sessions": session.get("summaries", 0),
        "total_messages": room.get("total", 0),
        "failovers": len(failovers),
        "actions": session.get("actions", 0),
        "tasks_total": queue.get("total", 0),
        "tasks_active": queue.get("active", 0),
        "tasks_blocked": (queue.get("counts") or {}).get("blocked", 0),
    }
    return {
        "ok": True,
        "type": report_type,
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "brief": (
            f"Rapport ATHOS — {summary['total_messages']} message(s), "
            f"{summary['actions']} action(s), {summary['tasks_active']} tâche(s) active(s)."
        ),
        "sections": sections,
        "summary": summary,
    }


def performance_payload() -> dict[str, Any]:
    runtime = observability.server_runtime()
    memory = memory_status.status()
    ports = observability.listening_ports()
    loop = loop_status()
    attached = attached_engines(limit=20)
    return {
        "ok": True,
        "source": "local_runtime",
        "system": {
            "uptime_seconds": runtime.get("uptime_seconds", 0),
            "listening_ports": len(ports),
            "memory_ok": bool(memory.get("ok", False)),
            "attached_engines": len(attached),
            "loop_running": bool(loop.get("running", False)),
            "server_pid": runtime.get("pid"),
        },
        "api_latencies": _latency_samples(),
        "lighthouse": [],
        "capabilities": {
            "system_metrics": True,
            "latency_sampling": True,
            "lighthouse_configured": False,
        },
    }


def crm_payload() -> dict[str, Any]:
    projects = _parse_projects(config.DRIVE / "athos_projects.mem")
    clients = [_project_to_client(name, fields) for name, fields in projects.items() if name != "athos"]
    active = sum(1 for client in clients if client.get("status") == "active")
    blocked = sum(1 for client in clients if client.get("blocked"))
    urgent = sum(1 for client in clients if client.get("attention") == "high")
    return {
        "ok": True,
        "source": "athos_projects.mem",
        "data_quality": "partial",
        "clients": clients,
        "active": active,
        "urgent": urgent,
        "blocked": blocked,
        "pipeline_total": None,
        "missing_sources": ["CRM dédié", "valeur mensuelle client", "historique relationnel structuré"],
    }


def _latency_samples() -> list[dict[str, Any]]:
    checks: list[tuple[str, Callable[[], Any]]] = [
        ("/api/status", lambda: session_kernel.status()),
        ("/api/conversation health", lambda: athos_room.health(limit=50)),
        ("/api/tasks", lambda: task_queue.summary()),
        ("/api/observability", lambda: observability.server_runtime()),
    ]
    rows: list[dict[str, Any]] = []
    for endpoint, fn in checks:
        samples: list[float] = []
        ok = True
        error = ""
        for _ in range(5):
            start = time.perf_counter()
            try:
                fn()
            except Exception as exc:
                ok = False
                error = str(exc)[:240]
            samples.append((time.perf_counter() - start) * 1000)
        rows.append({
            "endpoint": endpoint,
            "p50": round(statistics.median(samples), 2),
            "p95": round(max(samples), 2),
            "ok": ok,
            **({"error": error} if error else {}),
        })
    return rows


def _parse_projects(path: Path) -> dict[str, dict[str, Any]]:
    projects: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return projects
    for raw_line in path.read_text("utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line.startswith("§proj:"):
            continue
        rest = line[len("§proj:"):]
        name, _, fields_str = rest.partition("|")
        if not name:
            continue
        fields = projects.setdefault(name, {"raw": []})
        fields["raw"].append(line)
        for field in fields_str.split("|"):
            if ":" in field:
                key, _, value = field.partition(":")
                fields[key] = value
            elif field.startswith("blocker[") or field.startswith("blocker"):
                fields["blocker"] = field
            elif field.startswith("todo"):
                fields["todo"] = field
    return projects


def _project_to_client(name: str, fields: dict[str, Any]) -> dict[str, Any]:
    blocker = str(fields.get("blocker", "") or fields.get("blocker[", ""))
    status = str(fields.get("status", "unknown"))
    attention = "high" if blocker or status in {"pending", "blocked"} else ("medium" if fields.get("todo") else "normal")
    tags = _tags_for(fields)
    return {
        "id": name,
        "name": _display_name(name),
        "status": status,
        "attention": attention,
        "project": fields.get("store") or fields.get("stack") or fields.get("state") or "Projet ATHOS",
        "monthly_value": None,
        "next_action": fields.get("next") or fields.get("todo") or blocker or "",
        "tags": tags,
        "blocked": bool(blocker),
        "data_quality": "partial",
    }


def _tags_for(fields: dict[str, Any]) -> list[str]:
    haystack = " ".join(str(v).lower() for v in fields.values())
    tags = []
    for token in ("shopify", "next.js", "expo", "seo", "prospection", "theme"):
        if token in haystack:
            tags.append(token)
    return tags


def _display_name(name: str) -> str:
    return name.replace("-", " ").replace("_", " ").title()


def _queue_sentence(queue: dict[str, Any]) -> str:
    counts = queue.get("counts") or {}
    return (
        f"{queue.get('active', 0)} tâche(s) active(s), "
        f"{counts.get('completed', 0)} terminée(s), "
        f"{counts.get('blocked', 0)} bloquée(s), "
        f"{counts.get('queued', 0)} en attente."
    )


def _responders_sentence(responders: dict[str, Any]) -> str:
    actors = responders.get("actors") or {}
    if not actors:
        return "Aucun responder déclaré."
    return " · ".join(
        f"{name}:{'ok' if info.get('available') else (info.get('last_problem') or {}).get('kind', 'off')}"
        for name, info in actors.items()
    )


def _responder_status() -> dict[str, Any]:
    try:
        from . import room_responders
    except ImportError:
        import room_responders
    return room_responders.responder_status()
