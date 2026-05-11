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
GROK_KEY = os.getenv("GROK_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1").strip()
GROK_MODEL = os.getenv("GROK_MODEL", "grok-beta").strip()
ATHOS_ENGINE_ORDER = os.getenv("ATHOS_ENGINE_ORDER", "chatgpt_plus,claude_code,anthropic_api,grok,ollama").strip()
ATHOS_ACCESS_TOKEN = os.getenv("ATHOS_ACCESS_TOKEN", "").strip()
TEMP = ROOT / "temp"
LOGS = DRIVE / "logs"


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
    }

# Ensure common directories exist if needed
DRIVE.mkdir(parents=True, exist_ok=True)
TEMP.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)
