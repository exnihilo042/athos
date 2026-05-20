#!/usr/bin/env bash
# Write a compact Codex session note into ATHOS memory.
#
# Usage:
#   scripts/codex_session_note.sh '§session:2026-05-20|engine=codex|result=...'
#   printf '§session:...' | scripts/codex_session_note.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ATHOS_URL="${ATHOS_URL:-http://localhost:7474}"
ENV_FILE="${ATHOS_ENV_FILE:-$ROOT/.env}"

if [ "$#" -gt 0 ]; then
  NOTE="$*"
else
  NOTE="$(cat)"
fi

NOTE="$(printf "%s" "$NOTE" | tr -d '\000')"
if [ -z "${NOTE//[[:space:]]/}" ]; then
  echo "usage: codex_session_note.sh '§session:...|engine=codex|result=...'" >&2
  exit 64
fi

ATHOS_TOKEN="${ATHOS_TOKEN:-${ATHOS_ACCESS_TOKEN:-}}"
if [ -z "$ATHOS_TOKEN" ] && [ -f "$ENV_FILE" ]; then
  ATHOS_TOKEN="$(grep '^ATHOS_ACCESS_TOKEN=' "$ENV_FILE" | cut -d= -f2 | tr -d '"' | tr -d "'" || true)"
fi

PAYLOAD="$(python3 - "$NOTE" <<'PY'
import json
import sys
print(json.dumps({"note": sys.argv[1]}, ensure_ascii=False))
PY
)"

headers=(-H "Content-Type: application/json")
if [ -n "$ATHOS_TOKEN" ]; then
  headers+=(-H "Authorization: Bearer $ATHOS_TOKEN")
fi

response="$(curl -s -w "\n%{http_code}" -X POST "$ATHOS_URL/api/memory/note" "${headers[@]}" -d "$PAYLOAD" 2>/dev/null || true)"
code="$(printf "%s" "$response" | tail -1)"
body="$(printf "%s" "$response" | sed '$d')"

if [ "$code" = "200" ]; then
  echo "$body"
  exit 0
fi

mkdir -p "$ROOT/temp"
target="$ROOT/temp/session_notes.mem"
printf "%s\n" "$NOTE" >> "$target"
echo "{\"ok\":true,\"mode\":\"offline\",\"file\":\"$target\",\"http_code\":\"$code\"}"
