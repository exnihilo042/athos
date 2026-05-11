"""Static and local registries surfaced by Athos observability."""
from __future__ import annotations

from typing import Any

try:
    from . import skill_manager
except ImportError:
    import skill_manager


def skill_registry() -> list[dict[str, Any]]:
    installed = skill_manager.load_manifest()
    rows: list[dict[str, Any]] = []
    for name, spec in sorted(skill_manager.KNOWN_SKILLS.items()):
        info = installed.get(name, {})
        rows.append({
            "name": name,
            "description": info.get("description") or spec.get("description", ""),
            "installed": name in installed,
            "permissions": _permissions_for_skill(name),
            "dependencies": spec.get("pip", []),
            "tests": ["import connector", "capability smoke test"],
            "offline": name in {"vision", "pdf"},
            "compatible_devices": ["mac", "server"] if name not in {"homekit"} else ["mac", "phone", "home"],
        })
    return rows


def device_registry() -> list[dict[str, Any]]:
    return [
        {
            "id": "local-mac",
            "label": "Mac local Clement",
            "status": "active",
            "scopes": ["repo", "voice_server", "local_observability"],
            "heartbeat": "via /api/observability",
            "offline_queue": True,
            "revocable": True,
        },
        {
            "id": "phone",
            "label": "Telephone Clement",
            "status": "planned",
            "scopes": ["pwa", "voice", "notifications"],
            "heartbeat": "not_configured",
            "offline_queue": True,
            "revocable": True,
        },
        {
            "id": "private-server",
            "label": "Serveur prive Athos",
            "status": "planned",
            "scopes": ["always_on", "sync", "remote_access"],
            "heartbeat": "not_configured",
            "offline_queue": True,
            "revocable": True,
        },
    ]


def hardware_registry() -> list[dict[str, Any]]:
    return [
        {"name": "LiDAR", "status": "planned", "mode": "sensor", "permission": "explicit_device_scope"},
        {"name": "Flipper Zero", "status": "planned", "mode": "defensive_authorized_lab", "permission": "explicit_scope_required"},
        {"name": "Wi-Fi tools", "status": "planned", "mode": "defensive_scan_only", "permission": "authorized_network_only"},
        {"name": "Cameras", "status": "planned", "mode": "vision_input", "permission": "explicit_device_scope"},
    ]


def _permissions_for_skill(name: str) -> list[str]:
    mapping = {
        "gmail": ["gmail.read", "gmail.send.confirmed"],
        "calendar": ["calendar.read", "calendar.write.confirmed"],
        "homekit": ["home.device.control.confirmed"],
        "spotify": ["media.control"],
        "vision": ["screen_or_camera.consent"],
        "notion": ["notion.read", "notion.write.confirmed"],
        "whatsapp": ["message.send.confirmed"],
    }
    return mapping.get(name, ["local.read"])
