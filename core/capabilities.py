"""Local Athos self-knowledge from repo and Drive memory."""
from __future__ import annotations

from pathlib import Path

try:
    from . import config, session_kernel
except ImportError:
    import config
    import session_kernel


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
        f"Session: {session_kernel.summarize_recent()}",
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
        "capacités athos",
        "capabilities",
    ))
