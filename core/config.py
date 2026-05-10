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
ATHOS_ACCESS_TOKEN = os.getenv("ATHOS_ACCESS_TOKEN", "").strip()
TEMP = ROOT / "temp"
LOGS = DRIVE / "logs"

# Ensure common directories exist if needed
DRIVE.mkdir(parents=True, exist_ok=True)
TEMP.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)
