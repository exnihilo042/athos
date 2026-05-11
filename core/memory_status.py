"""Operational status for Athos long-term memory files."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from . import config, session_kernel
except ImportError:
    import config
    import session_kernel


CANONICAL_MEMORY_FILES = [
    "athos_identity.mem",
    "athos_capabilities.mem",
    "athos_cognition.mem",
    "athos_projects.mem",
    "athos_kernel_plan.mem",
    "athos_conv.mem",
]


def _file_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"name": path.name, "exists": False, "size": 0, "lines": 0, "last_line": "", "updated_at": ""}
    text = path.read_text("utf-8", errors="ignore")
    lines = [line for line in text.splitlines() if line.strip()]
    stat = path.stat()
    return {
        "name": path.name,
        "exists": True,
        "size": stat.st_size,
        "lines": len(lines),
        "last_line": lines[-1][:240] if lines else "",
        "updated_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds"),
    }


def status() -> dict[str, Any]:
    files = [_file_status(config.DRIVE / name) for name in CANONICAL_MEMORY_FILES]
    missing = [item["name"] for item in files if not item["exists"]]
    session = session_kernel.status()
    return {
        "root": str(config.DRIVE),
        "exists": config.DRIVE.exists(),
        "canonical_files": files,
        "missing": missing,
        "session_kernel": {
            "file": session.get("file"),
            "events": session.get("events", 0),
            "exchanges": session.get("exchanges", 0),
            "reports": session.get("reports", 0),
            "checkpoint": session.get("checkpoint", {}),
        },
        "ok": config.DRIVE.exists() and not missing,
    }
