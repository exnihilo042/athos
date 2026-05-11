"""Local Athos self-knowledge from repo and Drive memory."""
from __future__ import annotations

from pathlib import Path

try:
    from . import config, session_kernel, sync_manager
    from .autonomous_loop import status as loop_status
    from .named_protocols import list_protocols
    from .registries import device_registry, hardware_registry, skill_registry
except ImportError:
    import config
    import session_kernel
    import sync_manager
    from autonomous_loop import status as loop_status
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


def status_report() -> str:
    lines = [
        "A.T.H.O.S. — statut local",
        f"Repo: {config.ATHOS_PATH}",
        f"Mémoire: {config.DRIVE}",
        f"Politique coût: {config.spend_policy()['mode']}",
        f"Sécurité serveur: host={config.server_security_policy()['bind_host']}; token_required={config.server_security_policy()['token_required']}; token_configured={config.server_security_policy()['token_configured']}",
        f"Session: {session_kernel.summarize_recent()}",
        f"Attach protocol: /api/attach → /api/context_pack → /api/report",
        f"Sync: {sync_manager.status()['pending']} job(s) pending",
        f"Loop autonome: {'running' if loop_status()['running'] else 'off'}; skill mutation: {loop_status()['policy']['skill_mutation_enabled']}",
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
