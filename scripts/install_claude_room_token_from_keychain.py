#!/usr/bin/env python3
"""Install the Claude Room token from macOS Keychain into a protected file.

This helper never prints the token. ATHOS HUB can then read the file from a
LaunchAgent context where direct Keychain access is unreliable.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))

    try:
        from core.room_responders import _resolve_claude_oauth_token
    except Exception as exc:
        print(f"import_error:{exc}", file=sys.stderr)
        return 2

    token = _resolve_claude_oauth_token()
    if not token:
        print("missing:keychain_token", file=sys.stderr)
        return 1

    token_file = Path(os.getenv("ATHOS_CLAUDE_TOKEN_FILE", "~/.athos/claude_token")).expanduser()
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.parent.chmod(0o700)

    tmp = token_file.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(token.strip())
            handle.write("\n")
        tmp.chmod(0o600)
        tmp.replace(token_file)
        token_file.chmod(0o600)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass

    print(f"ok:{token_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
