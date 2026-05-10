"""Engine routing for Athos.

The router keeps provider priority independent from the HTTP server so the
fallback strategy can evolve without scattering hard-coded order lists.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Callable

DEFAULT_ENGINE_ORDER = ["chatgpt_plus", "claude_code", "anthropic_api", "grok", "ollama"]


def configured_order(raw: str | None = None) -> list[str]:
    value = raw if raw is not None else os.getenv("ATHOS_ENGINE_ORDER", "")
    requested = [item.strip().lower() for item in value.split(",") if item.strip()]
    ordered: list[str] = []
    for engine in requested + DEFAULT_ENGINE_ORDER:
        if engine in DEFAULT_ENGINE_ORDER and engine not in ordered:
            ordered.append(engine)
    return ordered


def available_engines(
    anthropic_key: str = "",
    openai_key: str = "",
    openai_enabled: bool = True,
    grok_key: str = "",
    has_ollama: Callable[[], bool] | None = None,
    has_chatgpt_plus: Callable[[], bool] | None = None,
    has_claude_code: Callable[[], bool] | None = None,
    order: list[str] | None = None,
) -> list[str]:
    checks = {
        "chatgpt_plus": bool(has_chatgpt_plus and has_chatgpt_plus()),
        "claude_code": bool(has_claude_code and has_claude_code()),
        "anthropic_api": bool(anthropic_key and not anthropic_key.startswith("sk-ant-...")),
        "chatgpt": bool(openai_enabled and openai_key),
        "claude": bool(anthropic_key and not anthropic_key.startswith("sk-ant-...")),
        "grok": bool(grok_key),
        "ollama": bool(has_ollama and has_ollama()),
    }
    return [engine for engine in (order or configured_order()) if checks.get(engine)]


def chatgpt_plus_available() -> bool:
    return shutil.which("codex") is not None


def claude_code_available() -> bool:
    if shutil.which("claude") is None:
        return False
    try:
        result = subprocess.run(["claude", "auth", "status"], capture_output=True, text=True, timeout=5)
    except Exception:
        return False
    return result.returncode == 0 and '"loggedIn": true' in result.stdout


def first_available(available: list[str]) -> str:
    return available[0] if available else "none"


def next_engine(current: str, available: list[str], order: list[str] | None = None) -> str:
    if not available:
        return "none"
    priority = order or configured_order()
    current_idx = priority.index(current) if current in priority else -1
    rotated = priority[current_idx + 1:] + priority[:current_idx + 1]
    return next((engine for engine in rotated if engine in available and engine != current), available[0])
