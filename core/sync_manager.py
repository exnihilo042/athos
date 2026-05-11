"""Local-first sync queue for Athos.

V1 deliberately does not perform hidden network writes. It records pending work,
reports what can be replayed, and leaves mutating replay to an explicit,
observable executor.
"""
from __future__ import annotations

import json
import socket
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from . import config, session_kernel
except ImportError:
    import config
    import session_kernel


OUTBOX_FILE = config.DRIVE / "athos_sync_outbox.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _append(job: dict[str, Any]) -> dict[str, Any]:
    OUTBOX_FILE.parent.mkdir(parents=True, exist_ok=True)
    enriched = {"id": job.get("id") or uuid.uuid4().hex, "ts": job.get("ts") or _now(), **job}
    with OUTBOX_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(enriched, ensure_ascii=False, separators=(",", ":")) + "\n")
    return enriched


def _read() -> list[dict[str, Any]]:
    if not OUTBOX_FILE.exists():
        return []
    jobs: list[dict[str, Any]] = []
    for line in OUTBOX_FILE.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        try:
            jobs.append(json.loads(line))
        except json.JSONDecodeError:
            jobs.append({"id": uuid.uuid4().hex, "ts": _now(), "status": "corrupt", "raw": line[:500]})
    return jobs


def _write_all(jobs: list[dict[str, Any]]) -> None:
    OUTBOX_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTBOX_FILE.write_text(
        "\n".join(json.dumps(job, ensure_ascii=False, separators=(",", ":")) for job in jobs) + ("\n" if jobs else ""),
        encoding="utf-8",
    )


def network_available(timeout: float = 1.0) -> bool:
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=timeout).close()
        return True
    except OSError:
        return False


def queue_job(kind: str, payload: dict[str, Any] | None = None,
              requires_network: bool = True, source: str = "athos") -> dict[str, Any]:
    job = _append({
        "kind": kind[:160],
        "payload": payload or {},
        "requires_network": requires_network,
        "source": source[:160],
        "status": "pending",
        "attempts": 0,
    })
    session_kernel.record_action("sync_queue", kind, "pending", engine="athos_kernel", meta={"job_id": job["id"]})
    return job


def status() -> dict[str, Any]:
    jobs = _read()
    pending = [job for job in jobs if job.get("status") in {"pending", "ready_for_replay"}]
    return {
        "file": str(OUTBOX_FILE),
        "exists": OUTBOX_FILE.exists(),
        "network_available": network_available(),
        "jobs": len(jobs),
        "pending": len(pending),
        "ready_for_replay": sum(1 for job in jobs if job.get("status") == "ready_for_replay"),
        "blocked_network": sum(1 for job in pending if job.get("requires_network")),
        "recent": jobs[-8:],
    }


def run_once(force_network_available: bool | None = None) -> dict[str, Any]:
    jobs = _read()
    online = network_available() if force_network_available is None else force_network_available
    changed = 0
    for job in jobs:
        if job.get("status") not in {"pending", "ready_for_replay"}:
            continue
        job["attempts"] = int(job.get("attempts", 0)) + 1
        job["last_attempt_at"] = _now()
        if job.get("requires_network") and not online:
            job["status"] = "pending"
            job["blocked_reason"] = "network_unavailable"
        else:
            job["status"] = "ready_for_replay"
            job["blocked_reason"] = "explicit_executor_required"
        changed += 1
    if changed:
        _write_all(jobs)
    session_kernel.record_action(
        "sync_run",
        "online" if online else "offline",
        f"{changed} job(s) inspected",
        engine="athos_kernel",
    )
    return {"ok": True, "network_available": online, "changed": changed, "status": status()}
