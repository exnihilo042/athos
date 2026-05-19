#!/usr/bin/env bash
# Check whether ATHOS can use a local Claude long-lived token file.
# Does not print the token.
set -euo pipefail

TOKEN_FILE="${ATHOS_CLAUDE_TOKEN_FILE:-$HOME/.athos/claude_token}"

if [ ! -f "$TOKEN_FILE" ]; then
  echo "missing:$TOKEN_FILE"
  exit 1
fi

PERMS="$(stat -f "%Lp" "$TOKEN_FILE" 2>/dev/null || stat -c "%a" "$TOKEN_FILE")"
case "$PERMS" in
  600|400) ;;
  *)
    echo "bad_permissions:$PERMS:$TOKEN_FILE"
    exit 2
    ;;
esac

BYTES="$(wc -c < "$TOKEN_FILE" | tr -d ' ')"
if [ "$BYTES" -lt 20 ]; then
  echo "too_short:$TOKEN_FILE"
  exit 3
fi

echo "ok:$TOKEN_FILE"
