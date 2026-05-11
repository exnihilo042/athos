"""Local Athos self-knowledge from repo and Drive memory."""
from __future__ import annotations

from pathlib import Path

try:
    from . import config, session_kernel, sync_manager, local_capability, capability_graph, epistemic_guard
    from .athos_advantage import CORE_AUGMENTATIONS
    from .autonomous_loop import status as loop_status
    from .metacognition import status as cognition_status
    from .named_protocols import list_protocols
    from .registries import device_registry, hardware_registry, skill_registry
except ImportError:
    import config
    import session_kernel
    import sync_manager
    import local_capability
    import capability_graph
    import epistemic_guard
    from athos_advantage import CORE_AUGMENTATIONS
    from autonomous_loop import status as loop_status
    from metacognition import status as cognition_status
    from named_protocols import list_protocols
    from registries import device_registry, hardware_registry, skill_registry


MEM_FILES = [
    "athos_identity.mem",
    "athos_capabilities.mem",
    "athos_cognition.mem",
    "athos_projects.mem",
    "athos_kernel_plan.mem",
]


def _selected_lines(path: Path, prefixes: tuple[str, ...], limit: int = 12) -> list[str]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text("utf-8", errors="ignore").splitlines():
        if line.startswith(prefixes) or any(token in line for token in ("§local:", "§routing:", "§todo:", "§done:", "§blocker:", "§cost:", "§observability:", "§thinking:")):
            rows.append(line)
    return rows[-limit:]


def status_report(compact: bool = False) -> str:
    security = config.server_security_policy()
    local_scan = local_capability.scan()
    graph_summary = capability_graph.compact_summary()["summary"]
    loop = loop_status()
    loop_policy = loop.get("policy", {})
    if compact:
        latest_done = []
        cap_file = config.DRIVE / "athos_capabilities.mem"
        if cap_file.exists():
            latest_done = [
                line for line in cap_file.read_text("utf-8", errors="ignore").splitlines()
                if line.startswith("§done:")
            ][-5:]
        parts = [
            "A.T.H.O.S. — statut court",
            f"Repo: {config.ATHOS_PATH.name}@{_git_head()}",
            f"Mémoire: {'ok' if config.DRIVE.exists() else 'missing'}",
            f"Coût: {config.spend_policy()['mode']}",
            f"Sécurité: host={security['bind_host']}; token={security['token_required']}; write_any={security['allow_any_write']}",
            f"Session: {session_kernel.summarize_recent()}",
            f"Sync: {sync_manager.status()['pending']} job(s) pending",
            f"Loop: {'running' if loop.get('running') else 'off'}",
            f"Cognition: non_immutable={cognition_status()['non_immutable_base']}; all_engines={cognition_status()['applies_to_all_engines']}",
            f"Anti-LLM delta: {len(CORE_AUGMENTATIONS)} augmentations runtime",
            f"Austérité locale: {local_scan['available_tool_count']} outils détectés sans réseau",
            f"Graphe capacités: {graph_summary['nodes']} noeuds; score={graph_summary['interconnection_score']}",
            f"Vérité: {epistemic_guard.PRINCIPLE}",
        ]
        if latest_done:
            parts.append("Derniers done:")
            parts.extend(latest_done)
        return "\n".join(parts)[:1_500]

    lines = [
        "A.T.H.O.S. — statut local",
        f"Repo: {config.ATHOS_PATH}",
        f"Mémoire: {config.DRIVE}",
        f"Politique coût: {config.spend_policy()['mode']}",
        f"Sécurité serveur: host={config.server_security_policy()['bind_host']}; token_required={config.server_security_policy()['token_required']}; token_configured={config.server_security_policy()['token_configured']}",
        f"Session: {session_kernel.summarize_recent()}",
        f"Attach protocol: /api/attach → /api/context_pack → /api/report",
        f"Sync: {sync_manager.status()['pending']} job(s) pending",
        f"Loop autonome: {'running' if loop.get('running') else 'off'}; skill mutation: {loop_policy.get('skill_mutation_enabled', False)}",
        f"Cognition: non_immutable={cognition_status()['non_immutable_base']}; principles={len(cognition_status()['principles'])}",
        f"Anti-LLM delta: {', '.join(item['name'] for item in CORE_AUGMENTATIONS[:4])}",
        f"Austérité locale: {local_scan['available_tool_count']} outils détectés; réseau requis={local_scan['network_required']}",
        f"Graphe capacités: nodes={graph_summary['nodes']}; edges={graph_summary['edges']}; score={graph_summary['interconnection_score']}",
        f"Garde-fou vérité: {epistemic_guard.PRINCIPLE}",
        f"Protocoles nommés: {', '.join(p['name'] for p in list_protocols())}",
        f"Skills installés: {sum(1 for s in skill_registry() if s['installed'])}/{len(skill_registry())}",
        f"Devices: {', '.join(d['id'] + ':' + d['status'] for d in device_registry())}",
        f"Hardware planned: {', '.join(h['name'] for h in hardware_registry())}",
    ]
    for fname in MEM_FILES:
        rows = _selected_lines(config.DRIVE / fname, ("§",), 8)
        if rows:
            lines.append(f"\n[{fname}]")
            lines.extend(rows)
    return "\n".join(lines)[:5_000]


def _git_head() -> str:
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(config.ATHOS_PATH),
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def matches_self_knowledge_request(msg: str) -> bool:
    q = msg.lower()
    return any(needle in q for needle in (
        "que sais-tu faire",
        "tu sais faire quoi",
        "où en est athos",
        "ou en est athos",
        "statut athos",
        "topo sur ce que tu es",
        "topo sur athos",
        "ce que tu es actuellement",
        "état actuel",
        "etat actuel",
        "capacités athos",
        "capabilities",
    ))


def wants_compact_status(msg: str) -> bool:
    q = msg.lower()
    return any(token in q for token in (
        "court",
        "rapide",
        "synthèse",
        "synthese",
        "résumé",
        "resume",
        "bref",
    ))
