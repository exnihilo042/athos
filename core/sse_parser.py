"""SSE parsing primitives for A.T.H.O.S.

Ported and adapted from fathah/hermes-desktop `src/main/sse-parser.ts`
(MIT License, copyright 2026 github.com/fathah). The Python version returns
structured events instead of calling UI callbacks, so it can be used by tests,
HTTP endpoints, and future desktop/mobile surfaces.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from typing import Any


TOOL_PROGRESS_RE = re.compile(r"^`([^\s`]+)\s+([^`]+)`$")
TOOL_PROGRESS_EVENTS = {"hermes.tool.progress", "athos.tool.progress"}


@dataclass
class SseState:
    has_content: bool = False
    last_error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_sse_block(block: str) -> dict[str, str] | None:
    """Parse one SSE block into event type and data payload."""
    event_type = ""
    data_lines: list[str] = []
    for raw_line in (block or "").splitlines():
        line = raw_line.rstrip("\r")
        if line.startswith("event:"):
            event_type = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    if not data_lines:
        return None
    return {"event_type": event_type, "data": "\n".join(data_lines)}


def process_custom_event(event_type: str, data: str) -> dict[str, Any]:
    """Handle tool-progress custom events without depending on the UI layer."""
    if event_type not in TOOL_PROGRESS_EVENTS:
        return {"handled": False, "events": []}
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        return {"handled": False, "events": [], "error": "malformed_json"}
    if not isinstance(payload, dict):
        return {"handled": False, "events": [], "error": "payload_not_object"}
    label = str(payload.get("label") or payload.get("tool") or "").strip()
    emoji = str(payload.get("emoji") or "").strip()
    if not label:
        return {"handled": False, "events": [], "error": "missing_label"}
    display = f"{emoji} {label}".strip()
    return {
        "handled": True,
        "events": [{
            "type": "tool_progress",
            "label": display,
            "tool": str(payload.get("tool") or label),
            "source_event": event_type,
        }],
    }


def process_sse_data(data: str, state: SseState | dict[str, Any] | None = None) -> dict[str, Any]:
    """Process one SSE data payload and return normalized events."""
    current = _coerce_state(state)
    events: list[dict[str, Any]] = []

    if data == "[DONE]":
        if current.has_content:
            events.append({"type": "done"})
        return {
            "done": True,
            "has_content": current.has_content,
            "error": current.last_error or None,
            "events": events,
            "state": current.to_dict(),
        }

    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        return {
            "done": False,
            "has_content": current.has_content,
            "events": [{"type": "malformed", "preview": (data or "")[:160]}],
            "state": current.to_dict(),
        }

    if isinstance(parsed, dict) and parsed.get("error"):
        error = parsed["error"]
        current.last_error = error.get("message") if isinstance(error, dict) else json.dumps(error)
        events.append({"type": "error", "message": current.last_error})

    if isinstance(parsed, dict) and parsed.get("usage"):
        events.append({"type": "usage", "usage": _usage(parsed.get("usage") or {})})

    delta = _delta(parsed)
    content = delta.get("content") if isinstance(delta, dict) else None
    if isinstance(content, str) and content:
        match = TOOL_PROGRESS_RE.match(content.strip())
        if match:
            events.append({"type": "tool_progress", "label": f"{match.group(1)} {match.group(2)}"})
        else:
            current.has_content = True
            events.append({"type": "chunk", "text": content})

    return {
        "done": False,
        "has_content": current.has_content,
        "error": current.last_error or None,
        "events": events,
        "state": current.to_dict(),
    }


def process_sse_block(block: str, state: SseState | dict[str, Any] | None = None) -> dict[str, Any]:
    """Parse and process one full SSE block."""
    parsed = parse_sse_block(block)
    if not parsed:
        return {"ok": False, "error": "no_data", "events": []}
    custom = process_custom_event(parsed["event_type"], parsed["data"])
    if custom.get("handled"):
        return {"ok": True, **custom, "parsed": parsed}
    data_result = process_sse_data(parsed["data"], state)
    return {"ok": True, "handled": False, "parsed": parsed, **data_result}


def _coerce_state(state: SseState | dict[str, Any] | None) -> SseState:
    if isinstance(state, SseState):
        return state
    if isinstance(state, dict):
        return SseState(
            has_content=bool(state.get("has_content") or state.get("hasContent")),
            last_error=str(state.get("last_error") or state.get("lastError") or ""),
        )
    return SseState()


def _delta(parsed: Any) -> dict[str, Any]:
    try:
        choices = parsed.get("choices") or []
        if not choices:
            return {}
        return choices[0].get("delta") or {}
    except AttributeError:
        return {}


def _usage(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "promptTokens": int(raw.get("prompt_tokens") or raw.get("promptTokens") or 0),
        "completionTokens": int(raw.get("completion_tokens") or raw.get("completionTokens") or 0),
        "totalTokens": int(raw.get("total_tokens") or raw.get("totalTokens") or 0),
        "cost": raw.get("cost"),
        "rateLimitRemaining": raw.get("rate_limit_remaining") or raw.get("rateLimitRemaining"),
        "rateLimitReset": raw.get("rate_limit_reset") or raw.get("rateLimitReset"),
    }
