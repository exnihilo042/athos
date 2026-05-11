"""ATHOS configuration partagée — chemins, env et clés."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.resolve()
ENV_PATH = ROOT / ".env"
load_dotenv(ENV_PATH)

DRIVE = Path(os.getenv("DRIVE_PATH", ROOT / "memory")).expanduser().resolve()
ATHOS_PATH = Path(os.getenv("ATHOS_PATH", ROOT)).expanduser().resolve()
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_ENABLED = os.getenv("OPENAI_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
ATHOS_API_SPEND = os.getenv("ATHOS_API_SPEND", "off").strip().lower()
PAID_API_ENABLED = ATHOS_API_SPEND in {"1", "true", "yes", "on", "allow", "enabled"}
WHISPER_ENABLED = os.getenv("WHISPER_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
SKILL_INSTALL_ENABLED = os.getenv("ATHOS_SKILL_INSTALL_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
AUTONOMOUS_LOOP_ENABLED = os.getenv("ATHOS_AUTONOMOUS_LOOP_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
AUTONOMOUS_LOOP_DEFAULT_TICK = float(os.getenv("ATHOS_AUTONOMOUS_LOOP_DEFAULT_TICK", "30"))
AUTONOMOUS_LOOP_MIN_TICK = float(os.getenv("ATHOS_AUTONOMOUS_LOOP_MIN_TICK", "5"))
FAILOVER_TEST_ENGINES = {
    item.strip()
    for item in os.getenv("ATHOS_FAILOVER_TEST_ENGINES", "").split(",")
    if item.strip()
}
GROK_KEY = os.getenv("GROK_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1").strip()
GROK_MODEL = os.getenv("GROK_MODEL", "grok-beta").strip()
ATHOS_ENGINE_ORDER = os.getenv("ATHOS_ENGINE_ORDER", "chatgpt_plus,claude_code,anthropic_api,grok,ollama").strip()
ATHOS_ACCESS_TOKEN = os.getenv("ATHOS_ACCESS_TOKEN", "").strip()
ATHOS_BIND_HOST = os.getenv("ATHOS_BIND_HOST", "127.0.0.1").strip() or "127.0.0.1"
_REQUIRE_TOKEN_RAW = os.getenv("ATHOS_REQUIRE_TOKEN", "").strip().lower()
if _REQUIRE_TOKEN_RAW:
    ATHOS_REQUIRE_TOKEN = _REQUIRE_TOKEN_RAW in {"1", "true", "yes", "on", "required"}
else:
    ATHOS_REQUIRE_TOKEN = ATHOS_BIND_HOST not in {"127.0.0.1", "localhost", "::1"}
ATHOS_TOKEN_ENFORCED = ATHOS_REQUIRE_TOKEN or bool(ATHOS_ACCESS_TOKEN)
ATHOS_ALLOWED_ORIGINS = [
    item.strip()
    for item in os.getenv(
        "ATHOS_ALLOWED_ORIGINS",
        "http://127.0.0.1:7474,http://localhost:7474",
    ).split(",")
    if item.strip()
]
TEMP = ROOT / "temp"
LOGS = DRIVE / "logs"
ATHOS_ALLOW_ANY_WRITE = os.getenv("ATHOS_ALLOW_ANY_WRITE", "false").strip().lower() in {"1", "true", "yes", "on"}
_WRITE_ROOTS_RAW = os.getenv("ATHOS_ALLOWED_WRITE_ROOTS", "").strip()
ATHOS_ALLOWED_WRITE_ROOTS = [
    Path(item).expanduser().resolve()
    for item in _WRITE_ROOTS_RAW.split(",")
    if item.strip()
] if _WRITE_ROOTS_RAW else []


def paid_api_allowed(provider: str = "") -> bool:
    """Single source of truth for paid API calls."""
    return PAID_API_ENABLED


def spend_policy() -> dict:
    return {
        "mode": "paid_api_allowed" if PAID_API_ENABLED else "zero_paid_api",
        "paid_api_enabled": PAID_API_ENABLED,
        "openai_enabled": OPENAI_ENABLED and PAID_API_ENABLED,
        "whisper_enabled": WHISPER_ENABLED and OPENAI_ENABLED and PAID_API_ENABLED,
        "skill_install_enabled": SKILL_INSTALL_ENABLED,
        "autonomous_loop_enabled": AUTONOMOUS_LOOP_ENABLED,
    }


def server_security_policy() -> dict:
    return {
        "bind_host": ATHOS_BIND_HOST,
        "allowed_origins": ATHOS_ALLOWED_ORIGINS,
        "token_required": ATHOS_TOKEN_ENFORCED,
        "remote_token_required": ATHOS_REQUIRE_TOKEN,
        "token_configured": bool(ATHOS_ACCESS_TOKEN),
        "token_enforced_reason": "remote_bind" if ATHOS_REQUIRE_TOKEN else ("token_configured" if ATHOS_ACCESS_TOKEN else "not_required_local"),
        "remote_exposure_guard": "token_required_when_bind_host_is_not_localhost",
        "allow_any_write": ATHOS_ALLOW_ANY_WRITE,
        "allowed_write_roots": [str(p) for p in allowed_write_roots()],
    }


def allowed_write_roots() -> list[Path]:
    roots = ATHOS_ALLOWED_WRITE_ROOTS or [ATHOS_PATH, DRIVE, TEMP]
    return [Path(root).expanduser().resolve() for root in roots]

# Ensure common directories exist if needed
DRIVE.mkdir(parents=True, exist_ok=True)
TEMP.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)
