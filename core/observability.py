"""Athos observability: visible, named, traceable, stoppable runtime state."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from . import config, session_kernel, sync_manager, memory_status, local_capability, capability_graph
    from .registries import device_registry, hardware_registry, skill_registry
except ImportError:
    import config
    import session_kernel
    import sync_manager
    import memory_status
    import local_capability
    import capability_graph
    from registries import device_registry, hardware_registry, skill_registry


ROOT = config.ATHOS_PATH
SERVER_STARTED_AT = datetime.now(timezone.utc)
SERVER_STARTED_MONOTONIC = time.monotonic()


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
    seen: set[tuple[str, str, str]] = set()
    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 9:
            continue
        name = " ".join(parts[7:])
        key = (parts[0], parts[1], name)
        if key in seen:
            continue
        seen.add(key)
        reason = _reason_for_port(parts[0], name)
        pid = int(parts[1]) if parts[1].isdigit() else parts[1]
        stoppable = isinstance(pid, int) and _port_is_safe_stoppable(parts[0], name, reason)
        rows.append({
            "command": parts[0],
            "pid": pid,
            "user": parts[2],
            "name": name,
            "reason": reason,
            "log": _log_for_command(parts[0], name),
            "stop_method": f"kill {parts[1]}" if stoppable else "",
            "stoppable": stoppable,
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


def _port_is_safe_stoppable(command: str, name: str, reason: str) -> bool:
    value = f"{command} {name} {reason}".lower()
    return any(token in value for token in (
        "athos voice/server",
        "ollama local model backend",
        "cloudflare tunnel",
        "mongodb local service",
    ))


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
        config.ATHOS_LOG_PATH,
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


def server_runtime() -> dict[str, Any]:
    return {
        "pid": os.getpid(),
        "started_at": SERVER_STARTED_AT.isoformat(timespec="seconds"),
        "uptime_seconds": round(time.monotonic() - SERVER_STARTED_MONOTONIC, 1),
        "host": config.ATHOS_BIND_HOST,
        "port": config.ATHOS_PORT,
        "log": str(config.ATHOS_LOG_PATH),
        "pid_file": str(config.ATHOS_PID_FILE),
        "pid_file_exists": config.ATHOS_PID_FILE.exists(),
        "stop_method": f"kill {os.getpid()}",
        "visible_runtime_rule": "server must be launched in a visible terminal tab, not as a hidden background daemon",
    }


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
    loop = _loop_status()
    attached = _attached_engines()
    skills = skill_registry()
    devices = device_registry()
    hardware = hardware_registry()
    memory = memory_status.status()
    local = local_capability.scan()
    graph = capability_graph.compact_summary()
    failover = recent_failover_events()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git": git_status(),
        "drive": drive_status(),
        "server_runtime": server_runtime(),
        "ports": ports,
        "launchd": jobs,
        "logs": athos_logs(),
        "agent_processes": agent_processes or [],
        "attached_engines": attached,
        "sync": sync,
        "memory": memory,
        "local_capability": local,
        "capability_graph": graph,
        "failover": failover,
        "loop": loop,
        "skills": skills,
        "devices": devices,
        "hardware": hardware,
        "permissions": _permission_summary(skills, devices, hardware),
        "cost_policy": config.spend_policy(),
        "server_security": config.server_security_policy(),
        "summary": {
            "listening_ports": len(ports),
            "launchd_jobs": len(jobs),
            "agent_processes": len(agent_processes or []),
            "attached_engines": len(attached),
            "sync_pending": sync.get("pending", 0),
            "memory_missing": len(memory.get("missing", [])),
            "local_tools": local.get("available_tool_count", 0),
            "local_capability_network_required": local.get("network_required", False),
            "capability_graph_nodes": graph.get("summary", {}).get("nodes", 0),
            "capability_graph_edges": graph.get("summary", {}).get("edges", 0),
            "capability_graph_score": graph.get("summary", {}).get("interconnection_score", 0.0),
            "failover_events": len(failover),
            "loop_running": loop.get("running", False),
            "installed_skills": sum(1 for skill in skills if skill.get("installed")),
            "devices": len(devices),
            "server_pid": os.getpid(),
        },
    }


def compact_snapshot(agent_processes: list[dict[str, Any]] | None = None) -> str:
    snap = process_snapshot(agent_processes)
    return json.dumps(snap["summary"], ensure_ascii=False, separators=(",", ":"))


def stop_observed_pid(pid: int) -> str:
    allowed = {row["pid"] for row in listening_ports() if isinstance(row.get("pid"), int) and row.get("stoppable")}
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


def _loop_status() -> dict[str, Any]:
    try:
        from .autonomous_loop import status as loop_status
    except ImportError:
        try:
            from autonomous_loop import status as loop_status
        except ImportError:
            return {"running": False, "error": "autonomous_loop unavailable"}
    try:
        return loop_status()
    except Exception as exc:
        return {"running": False, "error": str(exc)}


def recent_failover_events(limit: int = 8) -> list[dict[str, Any]]:
    rows = []
    for event in session_kernel.read_events(limit=120):
        if event.get("type") != "action":
            continue
        if event.get("name") not in {"failover", "failover_simulation"}:
            continue
        meta = event.get("meta") or {}
        rows.append({
            "ts": event.get("ts", ""),
            "name": event.get("name", ""),
            "label": event.get("label", ""),
            "result": event.get("result", ""),
            "engine": event.get("engine", ""),
            "context_hash": meta.get("context_hash", ""),
        })
    return rows[-limit:]
