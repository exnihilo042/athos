#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." >/dev/null 2>&1 && pwd)"
source "$ROOT/.env"
export ANTHROPIC_API_KEY
export DRIVE_PATH
"$ROOT/venv/bin/python3" "$ROOT/core/daily_brief.py"
