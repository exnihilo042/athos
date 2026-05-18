#!/usr/bin/env bash
# ATHOS Room — replay des messages offline
# Réinjecte memory/room_offline_*.jsonl dans ATHOS Room quand le serveur revient.
# Usage: replay_offline_room.sh [--dry-run]
# Lancé automatiquement au boot ATHOS (voice/server.py) ou manuellement.

set -euo pipefail

ATHOS_URL="${ATHOS_URL:-http://localhost:7474}"
MEMORY_DIR="$(cd "$(dirname "$0")/.." && pwd)/memory"
DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

REPLAYED_LOG="$MEMORY_DIR/.room_replayed_ids"
touch "$REPLAYED_LOG"

# Vérifier que ATHOS est en ligne
if ! curl -s "$ATHOS_URL/api/conversation" -X POST \
    -H "Content-Type: application/json" \
    -d '{"action":"get","limit":1}' > /dev/null 2>&1; then
  echo "[replay] ATHOS offline — abandon"
  exit 0
fi

TOTAL=0
SKIPPED=0
FAILED=0

for file in "$MEMORY_DIR"/room_offline_*.jsonl; do
  [ -f "$file" ] || continue
  echo "[replay] traitement : $(basename "$file")"

  while IFS= read -r line || [ -n "$line" ]; do
    [ -z "$line" ] && continue

    MSG_ID=$(echo "$line" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null || echo "")
    [ -z "$MSG_ID" ] && MSG_ID=$(echo "$line" | python3 -c "
import json,sys,hashlib
d=json.load(sys.stdin)
print(hashlib.md5((d.get('ts','')+d.get('content','')).encode()).hexdigest()[:12])
" 2>/dev/null || echo "")

    # Déduplication
    if grep -qF "$MSG_ID" "$REPLAYED_LOG" 2>/dev/null; then
      SKIPPED=$((SKIPPED+1))
      continue
    fi

    PAYLOAD=$(echo "$line" | python3 -c "
import json,sys
d = json.load(sys.stdin)
d.pop('offline', None)
d['meta'] = d.get('meta') or {}
d['meta']['replayed_from'] = 'offline_fallback'
print(json.dumps(d, ensure_ascii=False))
" 2>/dev/null) || continue

    if $DRY_RUN; then
      echo "  [dry] POST /api/message — $(echo "$PAYLOAD" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('actor','?'), '|', d.get('content','')[:60])")"
      echo "$MSG_ID" >> "$REPLAYED_LOG"
      TOTAL=$((TOTAL+1))
      continue
    fi

    HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$ATHOS_URL/api/message" \
      -H "Content-Type: application/json" \
      -d "$PAYLOAD" 2>/dev/null)

    if [ "$HTTP" = "200" ]; then
      echo "$MSG_ID" >> "$REPLAYED_LOG"
      TOTAL=$((TOTAL+1))
    else
      echo "  [warn] HTTP $HTTP — message ignoré"
      FAILED=$((FAILED+1))
    fi

  done < "$file"
done

echo "[replay] done — $TOTAL injectés · $SKIPPED dédupliqués · $FAILED erreurs"
