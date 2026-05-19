#!/usr/bin/env bash
# Restart ATHOS HUB LaunchAgent deterministically and print visible state.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="agency.athos.hub"
DOMAIN="gui/$(id -u)"
PLIST_SRC="$ROOT/launchd/$LABEL.plist"
PLIST_DST="$HOME/Library/LaunchAgents/$LABEL.plist"
PORT="${ATHOS_PORT:-7474}"

mkdir -p "$HOME/Library/LaunchAgents" "$ROOT/logs"
cp "$PLIST_SRC" "$PLIST_DST"

if launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
  launchctl bootout "$DOMAIN/$LABEL" >/dev/null 2>&1 || true
fi

if lsof -tiTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[athos] stopping stray listener(s) on :$PORT"
  lsof -tiTCP:"$PORT" -sTCP:LISTEN | xargs kill 2>/dev/null || true
  sleep 1
fi

launchctl bootstrap "$DOMAIN" "$PLIST_DST"
launchctl kickstart -k "$DOMAIN/$LABEL" >/dev/null 2>&1 || true

for _ in {1..20}; do
  if lsof -tiTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

echo "[athos] launchd:"
launchctl print "$DOMAIN/$LABEL" 2>/dev/null | awk '
  /state =|pid =|last exit code|stdout path|stderr path/ { print "  " $0 }
'

echo "[athos] port:"
if lsof -iTCP:"$PORT" -sTCP:LISTEN -n -P; then
  :
else
  echo "  not listening on :$PORT"
  exit 1
fi

echo "[athos] logs:"
echo "  out: $ROOT/logs/athos_launchd.out.log"
echo "  err: $ROOT/logs/athos_launchd.err.log"
