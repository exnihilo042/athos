#!/bin/bash
# Athos — Install
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
ATHOS="$(cd "$SCRIPT_DIR" >/dev/null 2>&1 && pwd)"
LAUNCH="${HOME}/Library/LaunchAgents"

echo "§athos:install|status:start"

# 1. Python deps
pip3 install -r "$ATHOS/requirements.txt" -q
echo "§deps:ok"

# 2. .env
if [ ! -f "$ATHOS/.env" ]; then
    cp "$ATHOS/.env.example" "$ATHOS/.env"
    echo "§env:created — REMPLIS $ATHOS/.env avec ta clé Anthropic"
else
    echo "§env:exists"
fi

# 3. Permissions scripts
chmod +x "$ATHOS/note"
chmod +x "$ATHOS/routines/run_brief.sh"
chmod +x "$ATHOS/routines/run_weekly.sh"
echo "§chmod:ok"

# 4. Symlink note dans /usr/local/bin pour usage global
ln -sf "$ATHOS/note" /usr/local/bin/athos-note 2>/dev/null || true
echo "§symlink:athos-note"

# 5. LaunchAgents
mkdir -p "$LAUNCH"
cp "$ATHOS/routines/agency.ex-nihilo.athos.daily-brief.plist" "$LAUNCH/"
cp "$ATHOS/routines/agency.ex-nihilo.athos.weekly.plist" "$LAUNCH/"

launchctl load "$LAUNCH/agency.ex-nihilo.athos.daily-brief.plist" 2>/dev/null && echo "§launchd:daily_brief:loaded" || echo "§launchd:daily_brief:already_loaded"
launchctl load "$LAUNCH/agency.ex-nihilo.athos.weekly.plist" 2>/dev/null && echo "§launchd:weekly:loaded" || echo "§launchd:weekly:already_loaded"

echo ""
echo "§athos:install|status:done"
echo "§next: remplis ANTHROPIC_API_KEY dans $ATHOS/.env"
echo "§test_brief: bash $ATHOS/routines/run_brief.sh"
echo "§test_session: python3 $ATHOS/core/session_writer.py"
