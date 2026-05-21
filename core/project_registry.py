"""Project Control Center backend registry.

Merges the canonical §-memory project view with a lightweight JSON registry used
for project creation and safe overrides from the dashboard.
"""
from __future__ import annotations

import json
import re
import threading
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from . import config
except ImportError:
    import config


MEMORY_FILE = config.DRIVE / "athos_projects.mem"
REGISTRY_FILE = config.DRIVE / "athos_project_registry.json"
ALLOWED_PATCH_FIELDS = {
    "name",
    "description",
    "status",
    "priority",
    "next_action",
    "domains",
    "repositories",
    "integrations",
    "social_channels",
    "goals",
    "agents",
}
STATUS_VALUES = {"active", "building", "pending", "done", "paused", "blocked"}
TYPE_VALUES = {"shopify", "saas", "mobile", "site", "agency", "other", "internal", "client_ecommerce"}
_LOCK = threading.Lock()


def list_projects() -> dict[str, Any]:
    merged = _merged_projects()
    projects = [_project_list_item(project) for project in merged.values()]
    projects.sort(key=lambda project: (int(project.get("priority") or "99"), project.get("name") or ""))
    summary = {
        "total": len(projects),
        "active": sum(1 for project in projects if project.get("status") in {"active", "building"}),
        "blocked": sum(1 for project in projects if project.get("blocker")),
        "partial": sum(1 for project in projects if project.get("data_quality") == "partial"),
    }
    return {
        "ok": True,
        "projects": projects,
        "summary": summary,
        "data_quality": "partial",
    }


def project_detail(project_id: str) -> tuple[dict[str, Any], int]:
    slug = slugify(project_id)
    if not slug:
        return {"ok": False, "error": "invalid_project_id"}, 400
    project = _merged_projects().get(slug)
    if not project:
        return {"ok": False, "error": "project_not_found"}, 404
    detail = {
        "id": project["id"],
        "name": project["name"],
        "type": project.get("type", "other"),
        "status": project.get("status", "pending"),
        "priority": project.get("priority", "5"),
        "priority_label": project.get("priority_label", "P5"),
        "description": project.get("description"),
        "health_score": project.get("health_score", 50),
        "next_action": project.get("next_action") or "",
        "blockers": [project["blocker"]] if project.get("blocker") else [],
        "domains": project.get("domains", []),
        "repositories": project.get("repositories", []),
        "integrations": project.get("integrations", []),
        "social_channels": project.get("social_channels", []),
        "agents": project.get("agents", []),
        "goals": project.get("goals", []),
        "recent_activity": project.get("recent_activity", []),
        "memory": {
            "source": project.get("source", "athos_projects.mem"),
            "data_quality": project.get("data_quality", "partial"),
        },
    }
    return {"ok": True, "project": detail, "data_quality": "partial"}, 200


def create_project(payload: Any) -> tuple[dict[str, Any], int]:
    if not isinstance(payload, dict):
        return {"ok": False, "error": "invalid_project_payload"}, 400
    validated, error = _validate_project_payload(payload, creating=True)
    if error:
        return {"ok": False, "error": error}, 400
    slug = validated["id"]
    merged = _merged_projects()
    if slug in merged:
        return {"ok": False, "error": "project_already_exists", "project_id": slug}, 409
    now = _now()
    project = {
        **validated,
        "created_at": now,
        "updated_at": now,
        "source": "json_registry",
    }
    with _LOCK:
        registry = _read_registry_unlocked()
        projects = registry.setdefault("projects", {})
        projects[slug] = project
        _write_registry_unlocked(registry)
    return {
        "ok": True,
        "project_id": slug,
        "project": _project_list_item(_decorate(project)),
        "storage": {"type": "json_registry", "path": "memory/athos_project_registry.json"},
        "warnings": [],
    }, 200


def update_project(project_id: str, patch: Any) -> tuple[dict[str, Any], int]:
    slug = slugify(project_id)
    if not slug:
        return {"ok": False, "error": "invalid_project_id"}, 400
    if not isinstance(patch, dict) or not patch:
        return {"ok": False, "error": "invalid_patch"}, 400
    unknown = sorted(set(patch) - ALLOWED_PATCH_FIELDS)
    if unknown:
        return {"ok": False, "error": "forbidden_patch_field", "fields": unknown}, 400
    merged = _merged_projects()
    current = merged.get(slug)
    if not current:
        return {"ok": False, "error": "project_not_found"}, 404
    validated_patch, error = _validate_project_patch(patch)
    if error:
        return {"ok": False, "error": error}, 400
    with _LOCK:
        registry = _read_registry_unlocked()
        projects = registry.setdefault("projects", {})
        base = dict(projects.get(slug) or {})
        if not base:
            base = {
                "id": current["id"],
                "name": current["name"],
                "type": current.get("type", "other"),
                "status": current.get("status", "pending"),
                "priority": current.get("priority", "5"),
                "description": current.get("description"),
                "domains": list(current.get("domains", [])),
                "repositories": list(current.get("repositories", [])),
                "integrations": list(current.get("integrations", [])),
                "social_channels": list(current.get("social_channels", [])),
                "goals": list(current.get("goals", [])),
                "agents": list(current.get("agents", [])),
                "next_action": current.get("next_action") or "",
                "created_at": current.get("created_at") or _now(),
                "source": "json_registry_override",
            }
        base.update(validated_patch)
        base["updated_at"] = _now()
        projects[slug] = base
        _write_registry_unlocked(registry)
    refreshed = _merged_projects().get(slug) or _decorate(base)
    return {
        "ok": True,
        "project": refreshed,
        "storage": {"type": "json_registry", "path": "memory/athos_project_registry.json"},
    }, 200


def mem_projects() -> dict[str, dict[str, Any]]:
    projects: dict[str, dict[str, Any]] = {}
    if not MEMORY_FILE.exists():
        return projects
    for raw_line in MEMORY_FILE.read_text("utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line.startswith("§proj:"):
            continue
        rest = line[len("§proj:"):]
        name, _, fields_str = rest.partition("|")
        slug = slugify(name)
        if not slug:
            continue
        fields = projects.setdefault(slug, {"id": slug, "raw_name": name, "raw": []})
        fields["raw"].append(line)
        for field in fields_str.split("|"):
            if ":" in field:
                key, _, value = field.partition(":")
                fields[key] = value
            elif field.startswith("blocker"):
                fields["blocker"] = field
            elif field.startswith("todo"):
                fields["todo"] = field
    return {slug: _decorate(_from_memory_fields(slug, fields)) for slug, fields in projects.items()}


def slugify(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text


def _from_memory_fields(slug: str, fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": slug,
        "name": _display_name(fields.get("raw_name") or slug),
        "type": _infer_type(fields),
        "description": None,
        "status": _normalize_status(fields.get("status"), default="pending"),
        "priority": _normalize_priority(fields.get("priority"), default="5"),
        "next_action": _safe_text(fields.get("next") or fields.get("todo")),
        "blocker": _safe_text(fields.get("blocker")),
        "domains": _extract_domains(fields),
        "repositories": _extract_repositories(fields),
        "integrations": _extract_integrations(fields),
        "social_channels": [],
        "goals": [],
        "agents": [],
        "created_at": "",
        "updated_at": "",
        "memory": fields.get("memory"),
        "stack": fields.get("stack"),
        "local": fields.get("local"),
        "state": fields.get("state"),
        "next": fields.get("next"),
        "todo": fields.get("todo"),
        "store": fields.get("store"),
        "repo": fields.get("repo"),
        "branch": fields.get("branch"),
        "source": "athos_projects.mem",
        "raw": fields.get("raw", []),
    }


def _merged_projects() -> dict[str, dict[str, Any]]:
    merged = mem_projects()
    for slug, project in _registry_projects().items():
        if slug in merged:
            base = dict(merged[slug])
            base.update(project)
            merged[slug] = _decorate(base)
        else:
            merged[slug] = _decorate(project)
    return merged


def _registry_projects() -> dict[str, dict[str, Any]]:
    with _LOCK:
        registry = _read_registry_unlocked()
    projects = registry.get("projects")
    if not isinstance(projects, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for slug, project in projects.items():
        if isinstance(project, dict):
            clean_slug = slugify(slug or project.get("id"))
            if clean_slug:
                result[clean_slug] = _decorate({
                    **project,
                    "id": clean_slug,
                    "source": project.get("source", "json_registry"),
                })
    return result


def _read_registry_unlocked() -> dict[str, Any]:
    if not REGISTRY_FILE.exists():
        return {"projects": {}}
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"projects": {}}
    return data if isinstance(data, dict) else {"projects": {}}


def _write_registry_unlocked(data: dict[str, Any]) -> None:
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _validate_project_payload(payload: dict[str, Any], *, creating: bool) -> tuple[dict[str, Any], str | None]:
    name = _safe_text(payload.get("name"), 160)
    if creating and not name:
        return {}, "name_required"
    project_type = _normalize_type(payload.get("type"), default="other")
    status = _normalize_status(payload.get("status"), default="pending")
    priority = _normalize_priority(payload.get("priority"), default="5")
    try:
        project = {
            "id": slugify(name),
            "name": name or _display_name(payload.get("id") or ""),
            "type": project_type,
            "description": _safe_nullable_text(payload.get("description"), 1000),
            "status": status,
            "priority": priority,
            "next_action": _safe_text(payload.get("next_action"), 400),
            "domains": _normalize_string_list(payload.get("domains")),
            "repositories": _normalize_string_list(payload.get("repositories")),
            "integrations": _normalize_string_list(payload.get("integrations")),
            "social_channels": _normalize_string_list(payload.get("social_channels")),
            "goals": _normalize_string_list(payload.get("goals")),
            "agents": _normalize_string_list(payload.get("agents")),
        }
    except ValueError:
        return {}, "invalid_array_field"
    if creating and not project["id"]:
        return {}, "invalid_project_name"
    return project, None


def _validate_project_patch(patch: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    validated: dict[str, Any] = {}
    try:
        for key, value in patch.items():
            if key == "name":
                name = _safe_text(value, 160)
                if not name:
                    return {}, "invalid_name"
                validated["name"] = name
            elif key == "description":
                validated["description"] = _safe_nullable_text(value, 1000)
            elif key == "status":
                validated["status"] = _normalize_status(value, default="pending")
            elif key == "priority":
                validated["priority"] = _normalize_priority(value, default="5")
            elif key == "next_action":
                validated["next_action"] = _safe_text(value, 400)
            elif key in {"domains", "repositories", "integrations", "social_channels", "goals", "agents"}:
                validated[key] = _normalize_string_list(value)
    except ValueError:
        return {}, "invalid_array_field"
    return validated, None


def _project_list_item(project: dict[str, Any]) -> dict[str, Any]:
    item = {
        "id": project["id"],
        "name": project["name"],
        "type": project.get("type", "other"),
        "status": project.get("status", "pending"),
        "priority": project.get("priority", "5"),
        "priority_label": project.get("priority_label", "P5"),
        "stack": project.get("stack"),
        "local": project.get("local"),
        "state": project.get("state"),
        "next": project.get("next") or project.get("next_action") or "",
        "next_action": project.get("next_action") or project.get("next") or "",
        "blocker": project.get("blocker") or "",
        "memory": project.get("memory"),
        "store": project.get("store"),
        "repo": project.get("repo"),
        "branch": project.get("branch"),
        "description": project.get("description"),
        "health_score": project.get("health_score", 50),
        "integrations_count": len(project.get("integrations", [])),
        "social_channels_count": len(project.get("social_channels", [])),
        "agents_count": len(project.get("agents", [])),
        "goals_count": len(project.get("goals", [])),
        "alerts_count": 1 if project.get("blocker") else 0,
        "data_quality": project.get("data_quality", "partial"),
        "source": project.get("source", "athos_projects.mem"),
        "domains": project.get("domains", []),
        "repositories": project.get("repositories", []),
        "integrations": project.get("integrations", []),
        "social_channels": project.get("social_channels", []),
        "agents": project.get("agents", []),
        "goals": project.get("goals", []),
    }
    return item


def _decorate(project: dict[str, Any]) -> dict[str, Any]:
    item = dict(project)
    item["priority"] = _normalize_priority(item.get("priority"), default="5")
    item["priority_label"] = f"P{item['priority']}"
    item["status"] = _normalize_status(item.get("status"), default="pending")
    item["name"] = _safe_text(item.get("name") or _display_name(item.get("id")), 160)
    item["id"] = slugify(item.get("id") or item["name"])
    item["domains"] = _normalize_string_list(item.get("domains"))
    item["repositories"] = _normalize_string_list(item.get("repositories"))
    item["integrations"] = _normalize_string_list(item.get("integrations"))
    item["social_channels"] = _normalize_string_list(item.get("social_channels"))
    item["goals"] = _normalize_string_list(item.get("goals"))
    item["agents"] = _normalize_string_list(item.get("agents"))
    item["next_action"] = _safe_text(item.get("next_action") or item.get("next"), 400)
    item["blocker"] = _safe_text(item.get("blocker"), 400)
    item["health_score"] = _health_score(item)
    item["data_quality"] = "partial"
    item["recent_activity"] = [line for line in item.get("raw", [])[-5:]]
    return item


def _health_score(project: dict[str, Any]) -> int:
    score = 50
    if project.get("next_action"):
        score += 10
    if project.get("blocker"):
        score -= 15
    if project.get("status") in {"active", "building"}:
        score += 10
    if project.get("integrations"):
        score += 5
    if project.get("domains"):
        score += 5
    return max(0, min(100, score))


def _extract_domains(fields: dict[str, Any]) -> list[str]:
    values = []
    for key in ("domain", "domains", "site", "url", "store"):
        value = fields.get(key)
        if value:
            values.extend(_split_candidates(value))
    domains = []
    for value in values:
        candidate = str(value).replace("https://", "").replace("http://", "").strip("/")
        if "." in candidate and " " not in candidate and candidate not in domains:
            domains.append(candidate)
    return domains


def _extract_repositories(fields: dict[str, Any]) -> list[str]:
    values = []
    for key in ("repo", "repos", "repository"):
        value = fields.get(key)
        if value:
            values.extend(_split_candidates(value))
    repos = []
    for value in values:
        cleaned = _safe_text(value, 160)
        if cleaned and cleaned not in repos:
            repos.append(cleaned)
    return repos


def _extract_integrations(fields: dict[str, Any]) -> list[str]:
    values = []
    if fields.get("store"):
        values.append("shopify")
    if fields.get("repo"):
        values.append("github")
    if fields.get("memory"):
        values.append("memory")
    return values


def _split_candidates(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").replace("[", ",").replace("]", ",")
    return [chunk.strip() for chunk in re.split(r"[,\s]+", text) if chunk.strip()]


def _normalize_string_list(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise ValueError("invalid_array_field")
    result = []
    for item in value:
        text = _safe_text(item, 240)
        if text:
            result.append(text)
    return result[:100]


def _normalize_status(value: Any, *, default: str) -> str:
    text = _safe_text(value or default, 32).lower().replace(" ", "_")
    if text not in STATUS_VALUES:
        return default
    return text


def _normalize_type(value: Any, *, default: str) -> str:
    text = _safe_text(value or default, 48).lower().replace(" ", "_")
    if text not in TYPE_VALUES:
        return default
    return text


def _normalize_priority(value: Any, *, default: str) -> str:
    text = _safe_text(value or default, 16).upper().replace("P", "")
    if not text.isdigit():
        return default
    number = max(0, min(9, int(text)))
    return str(number)


def _infer_type(fields: dict[str, Any]) -> str:
    haystack = " ".join(str(v).lower() for v in fields.values())
    if fields.get("raw_name") == "athos" or "agency" in haystack:
        return "agency"
    if fields.get("store") or "shopify" in haystack or "theme" in haystack:
        return "shopify"
    if "expo/rn" in haystack or "react native" in haystack or "expo" in haystack:
        return "mobile"
    if "saas" in haystack:
        return "saas"
    if fields.get("repo") or fields.get("domain") or fields.get("site"):
        return "site"
    return "other"


def _display_name(value: Any) -> str:
    text = str(value or "").replace("-", " ").replace("_", " ").strip()
    return text.title()


def _safe_text(value: Any, limit: int = 400) -> str:
    return str(value or "").replace("\x00", "").strip()[:limit]


def _safe_nullable_text(value: Any, limit: int = 1000) -> str | None:
    text = _safe_text(value, limit)
    return text or None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
