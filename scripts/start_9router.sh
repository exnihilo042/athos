#!/usr/bin/env bash
# ATHOS — 9router proxy manager
# Dashboard OpenAI-compatible sur localhost:20128
# Usage: ./start_9router.sh [--stop] [--status]

PORT=20128
SERVER_JS="/usr/local/lib/node_modules/9router/app/server.js"
PID_FILE="$HOME/Sites/athos/.9router.pid"
LOG_FILE="$HOME/Sites/athos/logs/9router.log"
RUNTIME="node"

mkdir -p "$(dirname "$LOG_FILE")"

stop() {
  if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    kill "$pid" 2>/dev/null && echo "  [9router] stopped (PID $pid)" || echo "  [9router] PID $pid not found"
    rm -f "$PID_FILE"
  else
    lsof -ti:$PORT 2>/dev/null | xargs kill 2>/dev/null && echo "  [9router] stopped" || echo "  [9router] not running"
  fi
}

status() {
  if lsof -ti:$PORT > /dev/null 2>&1; then
    echo "  [9router] RUNNING → http://localhost:$PORT/dashboard"
  else
    echo "  [9router] STOPPED"
  fi
}

case "${1:-}" in
  --stop)   stop; exit 0 ;;
  --status) status; exit 0 ;;
esac

# Déjà en cours ?
if lsof -ti:$PORT > /dev/null 2>&1; then
  echo "  [9router] already running → http://localhost:$PORT/dashboard"
  exit 0
fi

if [ ! -f "$SERVER_JS" ]; then
  echo "  [9router] server.js not found at $SERVER_JS"
  exit 1
fi

# Lancer en background
PORT=$PORT nohup $RUNTIME "$SERVER_JS" >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
sleep 2

if lsof -ti:$PORT > /dev/null 2>&1; then
  echo "  [9router] started → http://localhost:$PORT/dashboard (PID $(cat $PID_FILE))"
else
  echo "  [9router] failed to start — check $LOG_FILE"
  exit 1
fi
