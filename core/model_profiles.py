"""Model and runtime profile registry for A.T.H.O.S.

Hermes Desktop exposes provider/model/profile surfaces that make many engines
selectable from one companion UI. Athos keeps the same useful idea, but routes
it through the Athos identity, cost policy, attach protocol, memory, and
capability graph.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import os
import shutil
import urllib.request
from typing import Any

try:
    from . import config, engine_router
except ImportError:
    import config
    import engine_router


@dataclass(frozen=True)
class ProviderProfile:
    id: str
    label: str
    config_provider: str
    group: str
    env_key: str = ""
    base_url: str = ""
    needs_key: bool = False
    spend_tier: str = "unknown"
    executable: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["key_configured"] = bool(self.env_key and os.getenv(self.env_key, "").strip())
        data["enabled_by_cost_policy"] = _enabled_by_cost_policy(self)
        data["status"] = provider_status(self)
        return data


@dataclass(frozen=True)
class ModelSeed:
    name: str
    provider: str
    model: str
    base_url: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeProfile:
    id: str
    label: str
    provider: str
    engine: str
    status: str
    cost: str
    local_first: bool
    preserves_athos_identity: bool = True
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PROVIDERS: tuple[ProviderProfile, ...] = (
    ProviderProfile("auto", "Auto detect", "auto", "routing", spend_tier="policy", notes="Athos chooses by situation."),
    ProviderProfile("chatgpt_plus", "ChatGPT Plus CLI", "codex", "subscription_cli", spend_tier="subscription", executable=True),
    ProviderProfile("claude_code", "Claude Code Pro", "claude", "subscription_cli", spend_tier="subscription", executable=True),
    ProviderProfile("anthropic", "Anthropic API", "anthropic", "direct_api", "ANTHROPIC_API_KEY", needs_key=True, spend_tier="paid_api", executable=True),
    ProviderProfile("openai", "OpenAI API", "openai", "direct_api", "OPENAI_API_KEY", needs_key=True, spend_tier="paid_api", notes="Disabled unless OPENAI_ENABLED and ATHOS_API_SPEND allow."),
    ProviderProfile("xai", "xAI / Grok", "xai", "direct_api", "GROK_API_KEY", needs_key=True, spend_tier="api_or_credit", executable=True),
    ProviderProfile("openrouter", "OpenRouter", "openrouter", "router_api", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1", True, "api_or_free_tier", notes="Connector planned; zero-spend gate required."),
    ProviderProfile("google", "Google AI Studio", "google", "direct_api", "GOOGLE_API_KEY", needs_key=True, spend_tier="api_or_free_tier", notes="Connector planned."),
    ProviderProfile("nous", "Nous", "nous", "remote_or_gateway", spend_tier="unknown", notes="Hermes-supported provider; connector planned."),
    ProviderProfile("qwen", "Qwen", "qwen", "direct_api", "QWEN_API_KEY", needs_key=True, spend_tier="api_or_free_tier", notes="Connector planned."),
    ProviderProfile("minimax", "MiniMax", "minimax", "direct_api", "MINIMAX_API_KEY", needs_key=True, spend_tier="api_or_free_tier", notes="Connector planned."),
    ProviderProfile("ollama", "Ollama", "ollama", "local", base_url="http://localhost:11434/v1", spend_tier="local", executable=True),
    ProviderProfile("lmstudio", "LM Studio", "custom", "local", base_url="http://localhost:1234/v1", spend_tier="local", notes="OpenAI-compatible local endpoint."),
    ProviderProfile("vllm", "vLLM", "custom", "local", base_url="http://localhost:8000/v1", spend_tier="local", notes="OpenAI-compatible local endpoint."),
    ProviderProfile("llamacpp", "llama.cpp server", "custom", "local", base_url="http://localhost:8080/v1", spend_tier="local", notes="OpenAI-compatible local endpoint."),
    ProviderProfile("groq", "Groq", "openai_compatible", "remote_api", "GROQ_API_KEY", "https://api.groq.com/openai/v1", True, "api_or_free_tier", notes="Connector planned; zero-spend gate required."),
    ProviderProfile("deepseek", "DeepSeek", "openai_compatible", "remote_api", "DEEPSEEK_API_KEY", "https://api.deepseek.com/v1", True, "api_or_free_tier", notes="Connector planned; zero-spend gate required."),
    ProviderProfile("together", "Together", "openai_compatible", "remote_api", "TOGETHER_API_KEY", "https://api.together.xyz/v1", True, "api_or_free_tier", notes="Connector planned; zero-spend gate required."),
    ProviderProfile("fireworks", "Fireworks", "openai_compatible", "remote_api", "FIREWORKS_API_KEY", "https://api.fireworks.ai/inference/v1", True, "api_or_free_tier", notes="Connector planned; zero-spend gate required."),
    ProviderProfile("cerebras", "Cerebras", "openai_compatible", "remote_api", "CEREBRAS_API_KEY", "https://api.cerebras.ai/v1", True, "api_or_free_tier", notes="Connector planned; zero-spend gate required."),
    ProviderProfile("mistral", "Mistral", "openai_compatible", "remote_api", "MISTRAL_API_KEY", "https://api.mistral.ai/v1", True, "api_or_free_tier", notes="Connector planned; zero-spend gate required."),
    ProviderProfile("custom", "Custom OpenAI-compatible", "custom", "custom", "CUSTOM_API_KEY", needs_key=False, spend_tier="custom", notes="Requires explicit base URL and scope."),
)

DEFAULT_MODELS: tuple[ModelSeed, ...] = (
    ModelSeed("Claude Sonnet 4", "openrouter", "anthropic/claude-sonnet-4-20250514"),
    ModelSeed("Claude Sonnet 4", "anthropic", "claude-sonnet-4-20250514"),
    ModelSeed("GPT-4.1", "openai", "gpt-4.1"),
)


def catalog(available_engines: list[str] | None = None) -> dict[str, Any]:
    available = set(available_engines or [])
    return {
        "source": "hermes_desktop_provider_model_profile_pattern_adapted_for_athos",
        "policy": [
            "Athos identity stays above the selected model/provider.",
            "Subscription/local engines can be used without API spend.",
            "Paid or ambiguous API routes remain blocked unless ATHOS_API_SPEND allows them.",
            "Planned providers are visible so missing connectors become exact gaps, not hidden limitations.",
        ],
        "providers": [provider.to_dict() for provider in PROVIDERS],
        "default_models": [model.to_dict() for model in DEFAULT_MODELS],
        "runtime_profiles": [profile.to_dict() for profile in runtime_profiles(available)],
        "summary": summary(available),
    }


def runtime_profiles(available_engines: set[str] | list[str] | None = None) -> list[RuntimeProfile]:
    available = set(available_engines or [])
    rows = [
        RuntimeProfile("athos.chatgpt_plus", "Athos via ChatGPT Plus CLI", "chatgpt_plus", "chatgpt_plus", _engine_status("chatgpt_plus", available), "subscription", False),
        RuntimeProfile("athos.claude_code", "Athos via Claude Code Pro", "claude_code", "claude_code", _engine_status("claude_code", available), "subscription", False),
        RuntimeProfile("athos.anthropic_api", "Athos via Anthropic API", "anthropic", "anthropic_api", _engine_status("anthropic_api", available), "paid_api", False),
        RuntimeProfile("athos.grok", "Athos via Grok/xAI", "xai", "grok", _engine_status("grok", available), "api_or_credit", False),
        RuntimeProfile("athos.ollama", "Athos via Ollama local", "ollama", "ollama", _engine_status("ollama", available), "local", True),
    ]
    for provider in PROVIDERS:
        if provider.group == "local" and provider.id not in {"ollama"}:
            rows.append(RuntimeProfile(
                f"athos.{provider.id}",
                f"Athos via {provider.label}",
                provider.id,
                provider.id,
                "available" if local_endpoint_reachable(provider.base_url) else "planned",
                "local",
                True,
                notes=provider.notes,
            ))
    return rows


def choose_profile(objective: str, available_engines: list[str] | None = None) -> dict[str, Any]:
    q = (objective or "").lower()
    available = set(available_engines or engine_router.available_engines(
        anthropic_key=config.ANTHROPIC_KEY,
        openai_key=config.OPENAI_KEY,
        openai_enabled=config.OPENAI_ENABLED and config.paid_api_allowed("openai"),
        anthropic_enabled=config.paid_api_allowed("anthropic"),
        grok_key=config.GROK_KEY,
        has_ollama=lambda: local_endpoint_reachable("http://localhost:11434"),
        has_chatgpt_plus=engine_router.chatgpt_plus_available,
        has_claude_code=engine_router.claude_code_available,
    ))
    candidates = [profile for profile in runtime_profiles(available) if profile.status == "available"]
    reason = "default_order"
    preferred = ["chatgpt_plus", "claude_code", "anthropic_api", "grok", "ollama"]
    if any(token in q for token in ("local", "offline", "hors ligne", "hors reseau", "sans rien")):
        preferred = ["ollama", "lmstudio", "vllm", "llamacpp", "chatgpt_plus", "claude_code"]
        reason = "local_austerity"
    elif any(token in q for token in ("code", "repo", "test", "debug", "impl", "fichier")):
        preferred = ["chatgpt_plus", "claude_code", "ollama"]
        reason = "code_work"
    elif any(token in q for token in ("recherche", "source", "web", "doc", "universitaire", "paper")):
        preferred = ["chatgpt_plus", "claude_code", "grok", "ollama"]
        reason = "research_with_zero_spend_bias"
    by_engine = {profile.engine: profile for profile in candidates}
    selected = next((by_engine[item] for item in preferred if item in by_engine), candidates[0] if candidates else None)
    return {
        "objective": (objective or "")[:500],
        "selected": selected.to_dict() if selected else None,
        "reason": reason,
        "available_runtime_count": len(candidates),
        "cost_policy": config.spend_policy(),
    }


def summary(available_engines: set[str] | list[str] | None = None) -> dict[str, Any]:
    provider_rows = [provider.to_dict() for provider in PROVIDERS]
    runtime_rows = [profile.to_dict() for profile in runtime_profiles(available_engines or [])]
    return {
        "providers": len(provider_rows),
        "runtime_profiles": len(runtime_rows),
        "available_runtime_profiles": sum(1 for profile in runtime_rows if profile["status"] == "available"),
        "local_presets": sum(1 for provider in provider_rows if provider["group"] == "local"),
        "blocked_by_zero_spend": sum(1 for provider in provider_rows if provider["status"] == "blocked_by_zero_spend"),
        "planned_connectors": sum(1 for provider in provider_rows if provider["status"] == "planned_connector"),
    }


def provider_status(provider: ProviderProfile) -> str:
    if provider.id == "chatgpt_plus":
        return "available" if engine_router.chatgpt_plus_available() else "missing_cli"
    if provider.id == "claude_code":
        return "available" if engine_router.claude_code_available() else "missing_cli_or_auth"
    if provider.id == "ollama":
        return "available" if local_endpoint_reachable("http://localhost:11434") or shutil.which("ollama") else "local_missing"
    if provider.group == "local":
        return "available" if local_endpoint_reachable(provider.base_url) else "local_missing"
    if not _enabled_by_cost_policy(provider):
        return "blocked_by_zero_spend"
    if provider.needs_key and not os.getenv(provider.env_key, "").strip():
        return "missing_key"
    return "available" if provider.executable else "planned_connector"


def local_endpoint_reachable(base_url: str) -> bool:
    if not base_url or not base_url.startswith("http://localhost") and not base_url.startswith("http://127.0.0.1"):
        return False
    try:
        target = base_url.rstrip("/") + "/models" if base_url.rstrip("/").endswith("/v1") else base_url.rstrip("/")
        with urllib.request.urlopen(target, timeout=0.35) as response:
            return response.status < 500
    except Exception:
        return False


def _engine_status(engine: str, available: set[str]) -> str:
    if engine in available:
        return "available"
    if engine in {"anthropic_api", "grok"} and not config.PAID_API_ENABLED:
        return "blocked_by_zero_spend"
    return "configured"


def _enabled_by_cost_policy(provider: ProviderProfile) -> bool:
    if provider.spend_tier in {"subscription", "local", "policy"}:
        return True
    if provider.spend_tier in {"paid_api", "api_or_credit", "api_or_free_tier"}:
        return config.PAID_API_ENABLED
    return True
