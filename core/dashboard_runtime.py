"""Runtime payloads consumed by the ATHOS dashboard.

These helpers expose real local state only. Missing external integrations are
reported as unavailable instead of being replaced with backend mocks.
"""
from __future__ import annotations

import os
import statistics
import time
from datetime import datetime, timezone
from typing import Any, Callable

try:
    from . import athos_room, config, memory_status, session_kernel, task_queue
    from . import observability
    from .attach_protocol import attached_engines
    from .autonomous_loop import status as loop_status
    from . import project_registry
except ImportError:
    import athos_room
    import config
    import memory_status
    import session_kernel
    import task_queue
    import observability
    from attach_protocol import attached_engines
    from autonomous_loop import status as loop_status
    import project_registry


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
    projects = project_registry.mem_projects()
    clients = [_project_to_client(project) for project in projects.values() if project.get("id") != "athos"]
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


CODEX_SKILL_REGISTRY = [
    {"id": "codex-athos", "engine": "codex", "command": "athos", "category": "ATHOS", "description": "Kernel ATHOS, mémoire, Room et coordination runtime.", "maturity": "available_when_engine_available"},
    {"id": "codex-athos-architects", "engine": "codex", "command": "athos-architects", "category": "ATHOS", "description": "Personas experts Ex-Nihilo pour cadrage et architecture.", "maturity": "available_when_engine_available"},
    {"id": "codex-test-driven-development", "engine": "codex", "command": "test-driven-development", "category": "Développement / Qualité", "description": "Écrire et renforcer les tests avant validation.", "maturity": "available_when_engine_available"},
    {"id": "codex-debugging-and-error-recovery", "engine": "codex", "command": "debugging-and-error-recovery", "category": "Développement / Qualité", "description": "Diagnostiquer les pannes et corriger la cause racine.", "maturity": "available_when_engine_available"},
    {"id": "codex-code-review-and-quality", "engine": "codex", "command": "code-review-and-quality", "category": "Développement / Qualité", "description": "Relire le code avec une posture qualité.", "maturity": "available_when_engine_available"},
    {"id": "codex-code-simplification", "engine": "codex", "command": "code-simplification", "category": "Développement / Qualité", "description": "Simplifier un code existant sans changer le comportement.", "maturity": "available_when_engine_available"},
    {"id": "codex-api-and-interface-design", "engine": "codex", "command": "api-and-interface-design", "category": "Développement / Qualité", "description": "Concevoir des contrats API stables.", "maturity": "available_when_engine_available"},
    {"id": "codex-incremental-implementation", "engine": "codex", "command": "incremental-implementation", "category": "Développement / Qualité", "description": "Livrer par tranches sûres et testables.", "maturity": "available_when_engine_available"},
    {"id": "codex-performance-optimization", "engine": "codex", "command": "performance-optimization", "category": "Développement / Qualité", "description": "Optimiser les perfs et la charge utile.", "maturity": "available_when_engine_available"},
    {"id": "codex-security-and-hardening", "engine": "codex", "command": "security-and-hardening", "category": "Développement / Qualité", "description": "Durcir auth, payloads et intégrations.", "maturity": "available_when_engine_available"},
    {"id": "codex-git-workflow-and-versioning", "engine": "codex", "command": "git-workflow-and-versioning", "category": "Git / CI / Déploiement", "description": "Structurer worktrees, branches, commits et historique.", "maturity": "available_when_engine_available"},
    {"id": "codex-ci-cd-and-automation", "engine": "codex", "command": "ci-cd-and-automation", "category": "Git / CI / Déploiement", "description": "Automatiser CI/CD et tâches récurrentes.", "maturity": "available_when_engine_available"},
    {"id": "codex-gh-fix-ci", "engine": "codex", "command": "gh-fix-ci", "category": "Git / CI / Déploiement", "description": "Diagnostiquer et réparer les checks GitHub Actions.", "maturity": "available_when_engine_available"},
    {"id": "codex-gh-address-comments", "engine": "codex", "command": "gh-address-comments", "category": "Git / CI / Déploiement", "description": "Traiter les retours de review GitHub.", "maturity": "available_when_engine_available"},
    {"id": "codex-github-plugin", "engine": "codex", "command": "plugin GitHub", "category": "Git / CI / Déploiement", "description": "Capacités du plugin GitHub pour repo, PR et issues.", "maturity": "available_when_engine_available"},
    {"id": "codex-vercel-deploy", "engine": "codex", "command": "vercel-deploy", "category": "Git / CI / Déploiement", "description": "Déployer un projet sur Vercel.", "maturity": "available_when_engine_available"},
    {"id": "codex-netlify-deploy", "engine": "codex", "command": "netlify-deploy", "category": "Git / CI / Déploiement", "description": "Déployer un projet sur Netlify.", "maturity": "available_when_engine_available"},
    {"id": "codex-cloudflare-deploy", "engine": "codex", "command": "cloudflare-deploy", "category": "Git / CI / Déploiement", "description": "Déployer un projet sur Cloudflare.", "maturity": "available_when_engine_available"},
    {"id": "codex-render-deploy", "engine": "codex", "command": "render-deploy", "category": "Git / CI / Déploiement", "description": "Déployer un projet sur Render.", "maturity": "available_when_engine_available"},
    {"id": "codex-shopify-liquid", "engine": "codex", "command": "shopify-liquid", "category": "Shopify", "description": "Liquid Shopify, templates, sections et snippets.", "maturity": "available_when_engine_available"},
    {"id": "codex-shopify-liquid-expert", "engine": "codex", "command": "shopify-liquid-expert", "category": "Shopify", "description": "Expert OS 2.0 pour thèmes Shopify.", "maturity": "available_when_engine_available"},
    {"id": "codex-shopify-admin", "engine": "codex", "command": "shopify-admin", "category": "Shopify", "description": "Admin GraphQL Shopify.", "maturity": "available_when_engine_available"},
    {"id": "codex-shopify-storefront-graphql", "engine": "codex", "command": "shopify-storefront-graphql", "category": "Shopify", "description": "Storefront GraphQL pour storefronts custom.", "maturity": "available_when_engine_available"},
    {"id": "codex-shopify-hydrogen", "engine": "codex", "command": "shopify-hydrogen", "category": "Shopify", "description": "Hydrogen storefront implementation.", "maturity": "available_when_engine_available"},
    {"id": "codex-shopify-functions", "engine": "codex", "command": "shopify-functions", "category": "Shopify", "description": "Fonctions backend Shopify.", "maturity": "available_when_engine_available"},
    {"id": "codex-shopify-references", "engine": "codex", "command": "shopify-references", "category": "Shopify", "description": "Références locales Dawn, Polaris et awesome-shopify.", "maturity": "available_when_engine_available"},
    {"id": "codex-shopify-sections-ui-base", "engine": "codex", "command": "shopify-sections-ui-base", "category": "Shopify", "description": "Base UI pour sections storefront Shopify.", "maturity": "available_when_engine_available"},
    {"id": "codex-ui-ux-expert", "engine": "codex", "command": "ui-ux-expert", "category": "UI / UX / Design", "description": "Consulting UI/UX Ex-Nihilo.", "maturity": "available_when_engine_available"},
    {"id": "codex-ui-ux-pro-max", "engine": "codex", "command": "ui-ux-pro-max", "category": "UI / UX / Design", "description": "Référentiel palettes, guidelines et systèmes UI.", "maturity": "available_when_engine_available"},
    {"id": "codex-frontend-ui-engineering", "engine": "codex", "command": "frontend-ui-engineering", "category": "UI / UX / Design", "description": "Implémentation frontend propre et robuste.", "maturity": "available_when_engine_available"},
    {"id": "codex-figma", "engine": "codex", "command": "figma", "category": "UI / UX / Design", "description": "Travail avec le contexte et les assets Figma.", "maturity": "available_when_engine_available"},
    {"id": "codex-figma-use", "engine": "codex", "command": "figma-use", "category": "UI / UX / Design", "description": "Préparation obligatoire avant usage Figma.", "maturity": "available_when_engine_available"},
    {"id": "codex-figma-implement-design", "engine": "codex", "command": "figma-implement-design", "category": "UI / UX / Design", "description": "Implémentation fidèle d'un design Figma.", "maturity": "available_when_engine_available"},
    {"id": "codex-figma-generate-design", "engine": "codex", "command": "figma-generate-design", "category": "UI / UX / Design", "description": "Générer une proposition design structurée.", "maturity": "available_when_engine_available"},
    {"id": "codex-figma-generate-library", "engine": "codex", "command": "figma-generate-library", "category": "UI / UX / Design", "description": "Générer ou mettre à jour une design library.", "maturity": "available_when_engine_available"},
    {"id": "codex-figma-code-connect-components", "engine": "codex", "command": "figma-code-connect-components", "category": "UI / UX / Design", "description": "Mapper composants Figma et code.", "maturity": "available_when_engine_available"},
    {"id": "codex-shadcn", "engine": "codex", "command": "shadcn", "category": "UI / UX / Design", "description": "Gestion des composants shadcn.", "maturity": "available_when_engine_available"},
    {"id": "codex-magic-ui", "engine": "codex", "command": "magic-ui", "category": "UI / UX / Design", "description": "Composants et effets Magic UI.", "maturity": "available_when_engine_available"},
    {"id": "codex-heroui-react", "engine": "codex", "command": "heroui-react", "category": "UI / UX / Design", "description": "Composants HeroUI React.", "maturity": "available_when_engine_available"},
    {"id": "codex-seo-expert", "engine": "codex", "command": "seo-expert", "category": "SEO / Contenu", "description": "SEO technique et sémantique.", "maturity": "available_when_engine_available"},
    {"id": "codex-exnihilo-seo-expert", "engine": "codex", "command": "exnihilo-seo-expert", "category": "SEO / Contenu", "description": "SEO Ex-Nihilo, indexation IA et Google.", "maturity": "available_when_engine_available"},
    {"id": "codex-documentation-and-adrs", "engine": "codex", "command": "documentation-and-adrs", "category": "SEO / Contenu", "description": "Documenter les décisions et contrats techniques.", "maturity": "available_when_engine_available"},
    {"id": "codex-context-engineering", "engine": "codex", "command": "context-engineering", "category": "Automatisation / Agents", "description": "Préparer le bon contexte pour agents et LLMs.", "maturity": "available_when_engine_available"},
    {"id": "codex-planning-and-task-breakdown", "engine": "codex", "command": "planning-and-task-breakdown", "category": "Automatisation / Agents", "description": "Découper un objectif complexe en tâches.", "maturity": "available_when_engine_available"},
    {"id": "codex-spec-driven-development", "engine": "codex", "command": "spec-driven-development", "category": "Automatisation / Agents", "description": "Spécifier avant de construire.", "maturity": "available_when_engine_available"},
    {"id": "claude-agent-elements", "engine": "claude", "command": "agent-elements", "category": "Automatisation / Agents", "description": "Composants UI agents côté Claude.", "maturity": "available_when_engine_available"},
    {"id": "codex-playwright", "engine": "codex", "command": "playwright", "category": "Navigateurs / Tests Visuels", "description": "Automatisation navigateur et QA réelle.", "maturity": "available_when_engine_available"},
    {"id": "codex-playwright-interactive", "engine": "codex", "command": "playwright-interactive", "category": "Navigateurs / Tests Visuels", "description": "Session navigateur itérative persistante.", "maturity": "available_when_engine_available"},
    {"id": "codex-browser-testing-with-devtools", "engine": "codex", "command": "browser-testing-with-devtools", "category": "Navigateurs / Tests Visuels", "description": "Debug navigateur avec DevTools.", "maturity": "available_when_engine_available"},
    {"id": "athos-google-drive-plugin", "engine": "athos", "command": "Plugin Google Drive", "category": "Google Drive / Notion", "description": "Accès Drive, Docs, Sheets et Slides.", "maturity": "native_runtime"},
    {"id": "codex-notion-*", "engine": "codex", "command": "notion-*", "category": "Google Drive / Notion", "description": "Famille Notion pour capture et documentation.", "maturity": "available_when_engine_available"},
    {"id": "codex-pdf", "engine": "codex", "command": "pdf", "category": "Médias", "description": "Lire, produire et vérifier des PDF.", "maturity": "available_when_engine_available"},
    {"id": "codex-transcribe", "engine": "codex", "command": "transcribe", "category": "Médias", "description": "Transcription audio.", "maturity": "available_when_engine_available"},
    {"id": "codex-speech", "engine": "codex", "command": "speech", "category": "Médias", "description": "Synthèse vocale.", "maturity": "available_when_engine_available"},
    {"id": "codex-screenshot", "engine": "codex", "command": "screenshot", "category": "Médias", "description": "Captures écran et système.", "maturity": "available_when_engine_available"},
    {"id": "codex-imagegen", "engine": "codex", "command": "imagegen", "category": "Médias", "description": "Génération et édition bitmap.", "maturity": "available_when_engine_available"},
]


def finances_payload() -> dict[str, Any]:
    stripe = _has_any_env("STRIPE_SECRET_KEY", "STRIPE_API_KEY")
    shopify = _has_any_env("SHOPIFY_ADMIN_TOKEN", "SHOPIFY_ACCESS_TOKEN", "SHOPIFY_API_KEY")
    manual_file = _candidate_exists(config.DRIVE / "finances.json", config.DRIVE / "finances.csv")
    budget = _athos_budget_total()
    warnings = []
    if not any((stripe, shopify, manual_file)):
        warnings.append("No Stripe/Shopify/manual finance source configured")
    return {
        "ok": True,
        "summary": {
            "currency": "EUR",
            "revenue_gross": None,
            "revenue_net": None,
            "orders_count": None,
            "agency_result": None,
            "margin_rate": None,
            "athos_budget": budget,
            "spend_policy": "zero_paid_api",
        },
        "sources": {
            "athos_budget": "api_status",
            "business_revenue": None,
            "orders": None,
            "payments": None,
        },
        "projects": [],
        "monthly": [],
        "capabilities": {
            "athos_budget_real": True,
            "stripe_configured": stripe,
            "shopify_configured": shopify,
            "manual_finance_file_found": manual_file,
        },
        "warnings": warnings,
        "data_quality": "partial",
    }


def seo_payload() -> dict[str, Any]:
    projects = project_registry.mem_projects()
    sites = []
    for project in projects.values():
        domains = list(project.get("domains") or [])
        if not domains and project.get("id") == "athos":
            continue
        domain = domains[0] if domains else None
        if not domain:
            continue
        sites.append({
            "id": project["id"],
            "domain": domain,
            "source": "athos_projects.mem",
            "gsc_configured": _has_any_env("GOOGLE_SEARCH_CONSOLE_PROPERTY", "GSC_PROPERTY"),
            "pagespeed_configured": _has_any_env("PAGESPEED_API_KEY"),
            "metrics": {
                "organic_clicks": None,
                "organic_impressions": None,
                "avg_position": None,
                "ctr": None,
                "seo_score": None,
            },
            "issues": [],
            "opportunities": [],
            "data_quality": "metadata_only",
        })
    gsc = _has_any_env("GOOGLE_SEARCH_CONSOLE_PROPERTY", "GSC_PROPERTY", "GOOGLE_SEARCH_CONSOLE_TOKEN")
    pagespeed = _has_any_env("PAGESPEED_API_KEY")
    return {
        "ok": True,
        "sites": sites,
        "summary": {
            "tracked_sites": len(sites) if gsc else 0,
            "gsc_connected": gsc,
            "pagespeed_connected": pagespeed,
            "real_metrics_available": False,
        },
        "capabilities": {
            "metadata_from_projects": True,
            "google_search_console": gsc,
            "pagespeed_insights": pagespeed,
            "rank_tracker": False,
        },
        "warnings": ["Google Search Console not configured"] if not gsc else [],
        "data_quality": "partial",
    }


def commandes_payload(payload: dict[str, Any] | None = None) -> tuple[dict[str, Any], int]:
    payload = payload or {}
    project_id = project_registry.slugify(payload.get("project_id") or payload.get("store"))
    limit_raw = payload.get("limit", 50)
    try:
        limit = int(limit_raw)
    except (TypeError, ValueError):
        return {"ok": False, "error": "invalid_limit"}, 400
    if limit < 1 or limit > 200:
        return {"ok": False, "error": "invalid_limit"}, 400
    known_projects = project_registry.mem_projects()
    if project_id and project_id not in known_projects:
        # Unknown project_id should not break. Keep the request honest.
        project_id = ""
    shopify = _has_any_env("SHOPIFY_ADMIN_TOKEN", "SHOPIFY_ACCESS_TOKEN", "SHOPIFY_API_KEY")
    stripe = _has_any_env("STRIPE_SECRET_KEY", "STRIPE_API_KEY")
    manual = _candidate_exists(config.DRIVE / "orders.json", config.DRIVE / "orders.csv")
    data_quality = "config_only" if any((shopify, stripe, manual)) else "empty_no_source"
    warnings = []
    if data_quality == "empty_no_source":
        warnings.append("No orders source configured")
    return {
        "ok": True,
        "orders": [],
        "summary": {
            "total_orders": 0,
            "gross_total": None,
            "net_total": None,
            "currency": "EUR",
            "pending": 0,
            "paid": 0,
            "refunded": 0,
        },
        "sources": {"shopify": shopify, "stripe": stripe, "manual": manual},
        "capabilities": {
            "shopify_admin_configured": shopify,
            "stripe_configured": stripe,
            "manual_orders_file_found": manual,
        },
        "warnings": warnings,
        "data_quality": data_quality,
        "project_id": project_id or None,
        "limit": limit,
    }, 200


def skills_registry_payload() -> dict[str, Any]:
    engines = skills_engine_availability_payload()["engines"]
    skills = []
    for skill in CODEX_SKILL_REGISTRY:
        engine = skill["engine"]
        available = bool(engines.get(engine, {}).get("available", False)) if engine in {"codex", "claude"} else True
        skills.append({**skill, "available": available})
    summary = {
        "total": len(skills),
        "claude": sum(1 for skill in skills if skill["engine"] == "claude"),
        "codex": sum(1 for skill in skills if skill["engine"] == "codex"),
        "athos": sum(1 for skill in skills if skill["engine"] == "athos"),
    }
    return {
        "ok": True,
        "skills": skills,
        "summary": summary,
        "data_quality": "static_registry",
    }


def skills_engine_availability_payload() -> dict[str, Any]:
    responders = _responder_status().get("actors") or {}
    claude = _engine_info(responders.get("claude"), source="room_responders")
    codex = _engine_info(responders.get("codex"), source="room_responders")
    return {
        "ok": True,
        "engines": {
            "claude": claude,
            "codex": codex,
            "athos": {"available": True, "reason": "core_runtime"},
        },
        "data_quality": "runtime_observed",
    }


def skills_recommend_payload(payload: dict[str, Any] | None = None) -> tuple[dict[str, Any], int]:
    payload = payload or {}
    context = payload.get("context")
    if context is not None and not isinstance(context, dict):
        return {"ok": False, "error": "invalid_context"}, 400
    context = context or {}
    page = str(context.get("page", "")).lower()
    task = str(context.get("task", "")).lower()
    phase = str(context.get("phase", "")).lower()
    recommendations = []
    if "automations" in page or "qa" in phase or "qa" in task:
        recommendations.append({
            "skill_id": "claude-agent-elements" if "frontend" in task else "codex-playwright",
            "engine": "claude" if "frontend" in task else "codex",
            "reason": "Frontend QA phase" if "frontend" in task else "Browser validation phase",
            "confidence": 0.7,
            "human_approval_required": True,
        })
    if "seo" in page or "seo" in task:
        recommendations.append({
            "skill_id": "codex-exnihilo-seo-expert",
            "engine": "codex",
            "reason": "SEO analysis requested",
            "confidence": 0.76,
            "human_approval_required": True,
        })
    if not recommendations:
        recommendations.append({
            "skill_id": "codex-planning-and-task-breakdown",
            "engine": "codex",
            "reason": "Default planning recommendation",
            "confidence": 0.55,
            "human_approval_required": True,
        })
    return {
        "ok": True,
        "recommendations": recommendations,
        "mode": "static_rules",
        "data_quality": "heuristic",
    }, 200


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


def _project_to_client(project: dict[str, Any]) -> dict[str, Any]:
    blocker = str(project.get("blocker", ""))
    status = str(project.get("status", "unknown"))
    attention = "high" if blocker or status in {"pending", "blocked"} else ("medium" if project.get("todo") else "normal")
    tags = _tags_for(project)
    return {
        "id": project["id"],
        "name": project["name"],
        "status": status,
        "attention": attention,
        "project": project.get("store") or project.get("stack") or project.get("state") or "Projet ATHOS",
        "monthly_value": None,
        "next_action": project.get("next_action") or project.get("todo") or blocker or "",
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


def _athos_budget_total() -> float:
    try:
        from .athos_memory import AthosMemory
    except ImportError:
        from athos_memory import AthosMemory
    try:
        budget = AthosMemory().load_budget()
        return float(budget.get("spent", 0.0))
    except Exception:
        return 0.0


def _has_any_env(*names: str) -> bool:
    return any(bool(os.getenv(name, "").strip()) for name in names)


def _candidate_exists(*paths) -> bool:
    return any(path.exists() for path in paths)


def _engine_info(info: dict[str, Any] | None, *, source: str) -> dict[str, Any]:
    problem = ((info or {}).get("last_problem") or {}) if isinstance(info, dict) else {}
    reason = problem.get("kind")
    detail = problem.get("detail")
    payload = {
        "available": bool((info or {}).get("available", False)),
        "reason": reason or None,
        "source": source,
    }
    if detail:
        payload["detail"] = detail
    return payload


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
