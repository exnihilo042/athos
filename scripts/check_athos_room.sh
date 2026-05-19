#!/usr/bin/env bash
# Print a concise operator status for ATHOS Room.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ATHOS_URL="${ATHOS_URL:-http://localhost:7474}"
ENV_FILE="$ROOT/.env"
TOKEN="${ATHOS_TOKEN:-}"

if [ -z "$TOKEN" ] && [ -f "$ENV_FILE" ]; then
  TOKEN=$(grep "^ATHOS_ACCESS_TOKEN=" "$ENV_FILE" | cut -d= -f2 | tr -d '"' | tr -d "'" || true)
fi

curl_json() {
  local payload="$1"
  if [ -n "$TOKEN" ]; then
    curl -s -X POST "$ATHOS_URL/api/conversation" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d "$payload"
  else
    curl -s -X POST "$ATHOS_URL/api/conversation" \
      -H "Content-Type: application/json" \
      -d "$payload"
  fi
}

health="$(curl_json '{"action":"health"}')"
runtime="$(curl_json '{"action":"runtime"}')"

python3 - "$health" "$runtime" <<'PY'
import json
import sys

health = json.loads(sys.argv[1])
runtime = json.loads(sys.argv[2])
responders = runtime.get("responders", {}).get("actors", {})
summary = health.get("summary", {})

print("ATHOS Room")
print(f"  health     : {health.get('status')} · issues={len(health.get('issues', []))} · messages={summary.get('total', 0)}")
print(f"  auto-work  : enabled={runtime.get('auto_work', {}).get('enabled')} · active={runtime.get('auto_work', {}).get('active_count')}")
print(f"  responders : enabled={runtime.get('auto_response', {}).get('enabled')} · active={runtime.get('auto_response', {}).get('active_count')}")
for actor, info in responders.items():
    problem = info.get("last_problem") or {}
    state = "ok" if info.get("available") else "blocked"
    print(f"  {actor:<10}: {state} · path={info.get('path') or '-'}")
    if info.get("cooldown"):
        print(f"              cooldown={info['cooldown']}")
    if problem:
        print(f"              last={problem.get('kind')} · {problem.get('content')}")
PY
