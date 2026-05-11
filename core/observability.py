"""Athos observability: visible, named, traceable, stoppable runtime state."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import config
except ModuleNotFoundError:
    from core import config


ROOT = config.ATHOS_PATH


def _run(args: list[str], timeout: int = 5) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except Exception as exc:
        return f"ERROR: {exc}"
    return (result.stdout + result.stderr).strip()


def _shell(command: str, timeout: int = 5) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
    except Exception as exc:
        return f"ERROR: {exc}"
    return (result.stdout + result.stderr).strip()


def git_status() -> dict[str, Any]:
    return {
        "root": str(ROOT),
        "branch": _run(["git", "branch", "--show-current"], 3),
        "head": _run(["git", "rev-parse", "--short", "HEAD"], 3),
        "dirty": _run(["git", "status", "--short"], 3).splitlines(),
        "remote": _run(["git", "remote", "get-url", "origin"], 3),
    }


def listening_ports() -> list[dict[str, Any]]:
    output = _shell("lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null", 5)
    rows: list[dict[str, Any]] = []
    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 9:
            continue
        rows.append({
            "command": parts[0],
            "pid": int(parts[1]) if parts[1].isdigit() else parts[1],
            "user": parts[2],
            "name": parts[-1],
            "stop_method": f"kill {parts[1]}" if parts[1].isdigit() else "",
        })
    return rows


def launchd_jobs() -> list[dict[str, Any]]:
    output = _run(["launchctl", "list"], 5)
    rows: list[dict[str, Any]] = []
    for line in output.splitlines():
        if not any(token in line for token in ("athos", "agency.", "nearby", "mongodb", "codex")):
            continue
        parts = line.split(None, 2)
        if len(parts) != 3:
            continue
        pid, status, label = parts
        rows.append({
            "label": label,
            "pid": None if pid == "-" else int(pid),
            "status": int(status) if status.lstrip("-").isdigit() else status,
            "stop_method": f"launchctl bootout gui/$(id -u) {label}",
        })
    return rows


def athos_logs() -> list[dict[str, Any]]:
    candidates = [
        Path("/tmp/athos_server.log"),
        Path("/tmp/athos_brief.log"),
        Path("/tmp/athos_weekly.log"),
        Path("/tmp/athos_evening.log"),
    ]
    rows = []
    for path in candidates:
        rows.append({
            "path": str(path),
            "exists": path.exists(),
            "size": path.stat().st_size if path.exists() else 0,
        })
    return rows


def drive_status() -> dict[str, Any]:
    session = config.DRIVE / "athos_session_kernel.jsonl"
    return {
        "path": str(config.DRIVE),
        "exists": config.DRIVE.exists(),
        "session_kernel": str(session),
        "session_kernel_exists": session.exists(),
        "memory_files": sorted(p.name for p in config.DRIVE.glob("athos*.mem"))[:30] if config.DRIVE.exists() else [],
    }


def process_snapshot(agent_processes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    ports = listening_ports()
    jobs = launchd_jobs()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git": git_status(),
        "drive": drive_status(),
        "ports": ports,
        "launchd": jobs,
        "logs": athos_logs(),
        "agent_processes": agent_processes or [],
        "summary": {
            "listening_ports": len(ports),
            "launchd_jobs": len(jobs),
            "agent_processes": len(agent_processes or []),
        },
    }


def compact_snapshot(agent_processes: list[dict[str, Any]] | None = None) -> str:
    snap = process_snapshot(agent_processes)
    return json.dumps(snap["summary"], ensure_ascii=False, separators=(",", ":"))
