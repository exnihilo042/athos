"""Athos observability: visible, named, traceable, stoppable runtime state."""
from __future__ import annotations

import json
import os
import signal
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from . import config, session_kernel, sync_manager
    from .registries import device_registry, hardware_registry, skill_registry
except ImportError:
    import config
    import session_kernel
    import sync_manager
    from registries import device_registry, hardware_registry, skill_registry


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
            "reason": _reason_for_port(parts[0], parts[-1]),
            "log": _log_for_command(parts[0], parts[-1]),
            "stop_method": f"kill {parts[1]}" if parts[1].isdigit() else "",
            "stoppable": parts[1].isdigit(),
        })
    return rows


def _reason_for_port(command: str, name: str) -> str:
    value = f"{command} {name}".lower()
    if "7474" in value:
        return "Athos voice/server local"
    if "11434" in value or "ollama" in value:
        return "Ollama local model backend"
    if "mongodb" in value or "mongod" in value:
        return "MongoDB local service"
    if "cloudflared" in value:
        return "Cloudflare tunnel"
    return "Service local en écoute"


def _log_for_command(command: str, name: str) -> str:
    value = f"{command} {name}".lower()
    if "7474" in value:
        return "/tmp/athos_server.log"
    if "mongodb" in value or "mongod" in value:
        return "$(brew --prefix)/var/log/mongodb/mongo.log"
    return ""


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
            "reason": _reason_for_job(label),
            "log": _log_for_job(label),
            "stop_method": f"launchctl bootout gui/$(id -u) {label}",
            "stoppable": True,
        })
    return rows


def _reason_for_job(label: str) -> str:
    if "daily-brief" in label:
        return "Brief quotidien Athos"
    if "evening-recap" in label:
        return "Récapitulatif soir Athos"
    if "weekly" in label:
        return "Consolidation mémoire hebdomadaire"
    if "nearby" in label:
        return "Heartbeat Nearby/Codex docs"
    if "mongodb" in label:
        return "MongoDB Homebrew"
    return "Tâche planifiée locale"


def _log_for_job(label: str) -> str:
    if "daily-brief" in label:
        return "/tmp/athos_brief.log"
    if "evening-recap" in label:
        return "/tmp/athos_evening.log"
    if "weekly" in label:
        return "/tmp/athos_weekly.log"
    return ""


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
    sync = sync_manager.status()
    attached = _attached_engines()
    skills = skill_registry()
    devices = device_registry()
    hardware = hardware_registry()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git": git_status(),
        "drive": drive_status(),
        "ports": ports,
        "launchd": jobs,
        "logs": athos_logs(),
        "agent_processes": agent_processes or [],
        "attached_engines": attached,
        "sync": sync,
        "skills": skills,
        "devices": devices,
        "hardware": hardware,
        "permissions": _permission_summary(skills, devices, hardware),
        "cost_policy": config.spend_policy(),
        "summary": {
            "listening_ports": len(ports),
            "launchd_jobs": len(jobs),
            "agent_processes": len(agent_processes or []),
            "attached_engines": len(attached),
            "sync_pending": sync.get("pending", 0),
            "installed_skills": sum(1 for skill in skills if skill.get("installed")),
            "devices": len(devices),
        },
    }


def compact_snapshot(agent_processes: list[dict[str, Any]] | None = None) -> str:
    snap = process_snapshot(agent_processes)
    return json.dumps(snap["summary"], ensure_ascii=False, separators=(",", ":"))


def stop_observed_pid(pid: int) -> str:
    allowed = {row["pid"] for row in listening_ports() if isinstance(row.get("pid"), int)}
    if pid not in allowed:
        return f"PID {pid} non stoppable par Athos: absent des ports observés."
    os.kill(pid, signal.SIGTERM)
    return f"SIGTERM envoyé au PID {pid}."


def _attached_engines(limit: int = 12) -> list[dict[str, Any]]:
    rows = []
    for event in session_kernel.read_events(limit=limit * 4):
        if event.get("type") != "attach":
            continue
        rows.append({
            "attach_id": event.get("attach_id", ""),
            "engine": event.get("engine", ""),
            "ts": event.get("ts", ""),
            "scope": (event.get("meta") or {}).get("scope", ""),
        })
    return rows[-limit:]


def _permission_summary(skills: list[dict[str, Any]], devices: list[dict[str, Any]],
                        hardware: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "active_device_scopes": [
            {"device": device["id"], "scopes": device.get("scopes", [])}
            for device in devices if device.get("status") == "active"
        ],
        "installed_skill_permissions": [
            {"skill": skill["name"], "permissions": skill.get("permissions", [])}
            for skill in skills if skill.get("installed")
        ],
        "hardware_requires_explicit_scope": [item["name"] for item in hardware],
    }
