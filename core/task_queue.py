"""Persistent ATHOS task queue.

The queue is the operator-facing state between a Room objective and the actual
work cycle. It intentionally stores compact, auditable task records instead of
trying to become a hidden scheduler.
"""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from . import config, session_kernel
except ImportError:
    import config
    import session_kernel


TASK_QUEUE_FILE = config.DRIVE / "athos_task_queue.json"
STATUSES = {"queued", "running", "paused", "blocked", "completed", "cancelled"}
TERMINAL_STATUSES = {"completed", "cancelled"}
_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_text(value: Any, limit: int = 2_000) -> str:
    return str(value or "").replace("\x00", "")[:limit]


def _safe_meta(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        str(k)[:120]: v
        for k, v in value.items()
        if isinstance(v, (str, int, float, bool, type(None), list, dict))
    }


def _read_unlocked() -> list[dict[str, Any]]:
    if not TASK_QUEUE_FILE.exists():
        return []
    try:
        data = json.loads(TASK_QUEUE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _write_unlocked(items: list[dict[str, Any]]) -> None:
    TASK_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    TASK_QUEUE_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _find_index(items: list[dict[str, Any]], *, task_id: str = "", item_id: str = "") -> int | None:
    for index, item in enumerate(items):
        if item_id and item.get("id") == item_id:
            return index
        if task_id and item.get("task_id") == task_id:
            return index
    return None


def _record_transition(action: str, task: dict[str, Any], result: str = "") -> None:
    try:
        session_kernel.record_action(
            "task_queue",
            action,
            result or task.get("status", ""),
            engine="athos_kernel",
            meta={"task_id": task.get("task_id"), "queue_id": task.get("id")},
        )
    except Exception:
        pass


def create(
    title: str,
    *,
    content: str = "",
    task_id: str = "",
    source: str = "room",
    kind: str = "room_work",
    priority: int = 5,
    status: str = "queued",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a task, idempotently updating an existing task_id if provided."""
    status = status if status in STATUSES else "queued"
    now = _now()
    task_id = _safe_text(task_id, 160) or f"task-{uuid.uuid4().hex[:10]}"
    with _lock:
        items = _read_unlocked()
        existing = _find_index(items, task_id=task_id)
        if existing is not None:
            task = dict(items[existing])
            task.update({
                "title": _safe_text(title, 240) or task.get("title", ""),
                "content": _safe_text(content, 4_000) or task.get("content", ""),
                "source": _safe_text(source, 80) or task.get("source", "room"),
                "kind": _safe_text(kind, 80) or task.get("kind", "room_work"),
                "priority": int(priority),
                "updated_at": now,
                "meta": {**_safe_meta(task.get("meta")), **_safe_meta(meta)},
            })
            if task.get("status") not in TERMINAL_STATUSES:
                task["status"] = status
            items[existing] = task
        else:
            task = {
                "id": uuid.uuid4().hex[:12],
                "task_id": task_id,
                "title": _safe_text(title, 240),
                "content": _safe_text(content, 4_000),
                "source": _safe_text(source, 80),
                "kind": _safe_text(kind, 80),
                "priority": int(priority),
                "status": status,
                "created_at": now,
                "updated_at": now,
                "started_at": "",
                "completed_at": "",
                "blocked_reason": "",
                "retry_count": 0,
                "meta": _safe_meta(meta),
            }
            items.append(task)
        _write_unlocked(items)
    _record_transition("create", task)
    return task


def transition(
    *,
    task_id: str = "",
    item_id: str = "",
    status: str,
    reason: str = "",
    result: str = "",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if status not in STATUSES:
        return {"ok": False, "error": "invalid_status", "status": status}
    now = _now()
    with _lock:
        items = _read_unlocked()
        index = _find_index(items, task_id=_safe_text(task_id, 160), item_id=_safe_text(item_id, 80))
        if index is None:
            return {"ok": False, "error": "not_found"}
        task = dict(items[index])
        task["status"] = status
        task["updated_at"] = now
        if status == "running" and not task.get("started_at"):
            task["started_at"] = now
        if status in TERMINAL_STATUSES:
            task["completed_at"] = now
        if status == "blocked":
            task["blocked_reason"] = _safe_text(reason or result, 1_000)
        elif status in {"queued", "running", "completed", "cancelled"}:
            task["blocked_reason"] = _safe_text(reason, 1_000) if status == "cancelled" else ""
        if result:
            task["result"] = _safe_text(result, 2_000)
        if meta:
            task["meta"] = {**_safe_meta(task.get("meta")), **_safe_meta(meta)}
        items[index] = task
        _write_unlocked(items)
    _record_transition(status, task, result or reason)
    return {"ok": True, "task": task}


def start(*, task_id: str = "", item_id: str = "") -> dict[str, Any]:
    return transition(task_id=task_id, item_id=item_id, status="running")


def complete(*, task_id: str = "", item_id: str = "", result: str = "") -> dict[str, Any]:
    return transition(task_id=task_id, item_id=item_id, status="completed", result=result)


def block(*, task_id: str = "", item_id: str = "", reason: str = "") -> dict[str, Any]:
    return transition(task_id=task_id, item_id=item_id, status="blocked", reason=reason)


def pause(*, task_id: str = "", item_id: str = "", reason: str = "") -> dict[str, Any]:
    return transition(task_id=task_id, item_id=item_id, status="paused", reason=reason)


def resume(*, task_id: str = "", item_id: str = "") -> dict[str, Any]:
    return transition(task_id=task_id, item_id=item_id, status="queued")


def cancel(*, task_id: str = "", item_id: str = "", reason: str = "") -> dict[str, Any]:
    return transition(task_id=task_id, item_id=item_id, status="cancelled", reason=reason)


def retry(*, task_id: str = "", item_id: str = "") -> dict[str, Any]:
    now = _now()
    with _lock:
        items = _read_unlocked()
        index = _find_index(items, task_id=_safe_text(task_id, 160), item_id=_safe_text(item_id, 80))
        if index is None:
            return {"ok": False, "error": "not_found"}
        task = dict(items[index])
        task["status"] = "queued"
        task["updated_at"] = now
        task["completed_at"] = ""
        task["blocked_reason"] = ""
        task["retry_count"] = int(task.get("retry_count", 0)) + 1
        items[index] = task
        _write_unlocked(items)
    _record_transition("retry", task)
    return {"ok": True, "task": task}


def list_tasks(status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    with _lock:
        items = _read_unlocked()
    if status:
        wanted = {part.strip() for part in str(status).split(",") if part.strip()}
        items = [item for item in items if item.get("status") in wanted]
    items = sorted(items, key=lambda item: item.get("created_at", ""), reverse=True)
    return items[: max(1, min(int(limit), 500))]


def get(*, task_id: str = "", item_id: str = "") -> dict[str, Any] | None:
    with _lock:
        items = _read_unlocked()
    index = _find_index(items, task_id=_safe_text(task_id, 160), item_id=_safe_text(item_id, 80))
    return items[index] if index is not None else None


def summary() -> dict[str, Any]:
    with _lock:
        items = _read_unlocked()
    counts: dict[str, int] = {status: 0 for status in sorted(STATUSES)}
    for item in items:
        status = item.get("status", "queued")
        counts[status] = counts.get(status, 0) + 1
    active = [item for item in items if item.get("status") in {"queued", "running", "paused", "blocked"}]
    active_sorted = sorted(active, key=lambda item: item.get("updated_at", ""), reverse=True)
    return {
        "file": str(TASK_QUEUE_FILE),
        "exists": TASK_QUEUE_FILE.exists(),
        "total": len(items),
        "counts": counts,
        "active": len(active),
        "recent": active_sorted[:8],
    }
