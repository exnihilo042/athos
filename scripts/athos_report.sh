#!/usr/bin/env bash
# ATHOS Room — adaptateur universel Claude/Codex
# Usage: athos_report.sh <actor> <type> <content> [fichiers...]
# Acteurs: claude | codex | athos | clement
# Types:   message | action | result | decision | error | checkpoint
#
# Exemples:
#   athos_report.sh claude action "Lu header.liquid — 3 variables non définies"
#   athos_report.sh codex result "Section corrigée" sections/header.liquid
#   athos_report.sh claude decision "Utiliser CSS custom properties plutôt que inline styles"

ATHOS_URL="${ATHOS_URL:-http://localhost:7474}"
ACTOR="${1:-athos}"
TYPE="${2:-message}"
CONTENT="${3:-}"
shift 3 2>/dev/null
FILES=("$@")

if [ -z "$CONTENT" ]; then
  echo "Usage: athos_report.sh <actor> <type> <content> [fichiers...]" >&2
  exit 1
fi

PAYLOAD=$(python3 - "$ACTOR" "$TYPE" "$CONTENT" "${FILES[@]}" <<'PY'
import json
import sys

actor, msg_type, content, *files = sys.argv[1:]
print(json.dumps({
    "actor": actor,
    "type": msg_type,
    "content": content,
    "files": files,
}, ensure_ascii=False))
PY
)

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ATHOS_URL/api/message" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -1)

if [ "$HTTP_CODE" = "200" ]; then
  echo "[ROOM] $ACTOR/$TYPE → ATHOS Room OK"
else
  # Fallback local si ATHOS offline
  FALLBACK="$HOME/Sites/athos/memory/room_offline_$(date +%Y%m%d).jsonl"
  mkdir -p "$(dirname "$FALLBACK")"
  echo "$PAYLOAD" | python3 -c "
import json,sys,time
d = json.load(sys.stdin)
d['ts'] = time.strftime('%Y-%m-%dT%H:%M:%S')
d['offline'] = True
print(json.dumps(d))
" >> "$FALLBACK"
  echo "[ROOM] ATHOS offline — écrit dans $FALLBACK"
fi
