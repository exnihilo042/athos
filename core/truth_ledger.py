"""Truth ledger primitives for Athos memory.

Inspired by garrytan/gbrain's compiled-truth/timeline model, takes-vs-facts
split, and provenance-first memory policy. This is intentionally small and
local-first: Athos can use it without a database, network, or paid model call.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
import re
from typing import Any


COMPILED_MARKERS = ("## Compiled Truth", "=== COMPILED TRUTH ===")
TIMELINE_MARKERS = ("## Timeline", "=== TIMELINE ===")
CLAIM_KINDS = {"fact", "take", "belief", "hunch", "bet", "preference", "decision", "correction"}
SOURCE_TYPES = {
    "user_correction",
    "observed",
    "official",
    "repo",
    "academic",
    "direct_user",
    "self_described",
    "memory",
    "web",
    "inferred",
    "unknown",
}
SOURCE_PRIORITY = {
    "user_correction": 1.0,
    "observed": 0.95,
    "official": 0.9,
    "repo": 0.85,
    "academic": 0.82,
    "direct_user": 0.8,
    "self_described": 0.72,
    "memory": 0.65,
    "web": 0.55,
    "inferred": 0.35,
    "unknown": 0.2,
}


@dataclass(frozen=True)
class ProvenanceSource:
    source: str
    source_type: str = "unknown"
    actor: str = ""
    url: str = ""
    observed_at: str = ""
    context: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["priority"] = SOURCE_PRIORITY.get(self.source_type, SOURCE_PRIORITY["unknown"])
        return data


@dataclass
class TruthClaim:
    holder: str
    claim: str
    kind: str = "fact"
    confidence: float = 0.5
    source: ProvenanceSource | dict[str, Any] = field(default_factory=lambda: ProvenanceSource("unknown"))
    status: str = "active"
    valid_from: str = ""
    valid_until: str = ""

    def __post_init__(self) -> None:
        if self.kind not in CLAIM_KINDS:
            self.kind = "take"
        self.confidence = calibrate_confidence(self.confidence)
        if isinstance(self.source, dict):
            self.source = ProvenanceSource(
                source=str(self.source.get("source") or self.source.get("id") or "unknown"),
                source_type=str(self.source.get("source_type") or self.source.get("type") or "unknown"),
                actor=str(self.source.get("actor") or ""),
                url=str(self.source.get("url") or ""),
                observed_at=str(self.source.get("observed_at") or self.source.get("date") or ""),
                context=str(self.source.get("context") or ""),
            )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if isinstance(self.source, ProvenanceSource):
            data["source"] = self.source.to_dict()
        return data


def policy() -> dict[str, Any]:
    return {
        "principle": "facts_takes_and_beliefs_must_not_be_conflated",
        "rules": [
            "compiled truth is the current synthesis; timeline is append-only evidence",
            "every durable claim needs provenance, source type, holder, and confidence",
            "facts are not takes; takes are attributed beliefs with confidence and time",
            "conflicts remain visible as conflicting sourced claims, not silent overwrite",
            "user corrections are high-priority evidence but still recorded as evidence",
        ],
        "claim_kinds": sorted(CLAIM_KINDS),
        "source_priority": SOURCE_PRIORITY,
    }


def calibrate_confidence(value: float | int | str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.5
    number = max(0.0, min(1.0, number))
    return round(round(number * 20) / 20, 2)


def format_source(source: ProvenanceSource | dict[str, Any] | str) -> str:
    if isinstance(source, str):
        return source[:240]
    if isinstance(source, dict):
        source = ProvenanceSource(
            source=str(source.get("source") or source.get("id") or "unknown"),
            source_type=str(source.get("source_type") or source.get("type") or "unknown"),
            actor=str(source.get("actor") or ""),
            url=str(source.get("url") or ""),
            observed_at=str(source.get("observed_at") or source.get("date") or ""),
            context=str(source.get("context") or ""),
        )
    parts = [source.source_type, source.source]
    if source.actor:
        parts.append(f"actor={source.actor}")
    if source.observed_at:
        parts.append(f"date={source.observed_at}")
    if source.url:
        parts.append(f"url={source.url}")
    return " | ".join(part for part in parts if part)[:500]


def split_compiled_truth(page: str) -> dict[str, Any]:
    """Split a brain page into current synthesis and evidence timeline."""
    text = page or ""
    timeline_idx, timeline_marker = _find_marker(text, TIMELINE_MARKERS)
    compiled_idx, compiled_marker = _find_marker(text, COMPILED_MARKERS)
    if timeline_idx == -1:
        compiled = _strip_marker(text, compiled_marker).strip() if compiled_idx != -1 else text.strip()
        return {"compiled_truth": compiled, "timeline": "", "has_timeline": False}
    before = text[:timeline_idx]
    after = text[timeline_idx + len(timeline_marker):]
    compiled = _strip_marker(before, compiled_marker).strip() if compiled_idx != -1 else before.strip()
    return {"compiled_truth": compiled, "timeline": after.strip(), "has_timeline": True}


def append_timeline_entry(page: str, summary: str, source: ProvenanceSource | dict[str, Any] | str,
                          entry_date: str | None = None) -> str:
    """Append evidence without rewriting compiled truth."""
    entry_date = entry_date or date.today().isoformat()
    entry = f"- {entry_date} | {format_source(source)} | {summary.strip()}"
    text = (page or "").rstrip()
    timeline_idx, _timeline_marker = _find_marker(text, TIMELINE_MARKERS)
    if timeline_idx == -1:
        if not text:
            text = "## Compiled Truth\n\n"
        return f"{text}\n\n## Timeline\n{entry}\n"
    return f"{text}\n{entry}\n"


def detect_entities(text: str, limit: int = 24) -> list[dict[str, Any]]:
    """Small deterministic entity detector for local/offline signal scans."""
    candidates = re.findall(r"\b(?:[A-Z][A-Za-z0-9]*\.?)(?:[\s.-]+[A-Z][A-Za-z0-9]*\.?){0,3}\b", text or "")
    known = re.findall(r"\b(?:ATHOS|A\.T\.H\.O\.S\.|JARVIS|Codex|Claude|GBrain|GStack|Hermes)\b", text or "")
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for raw in known + candidates:
        name = raw.strip(" .,-")
        if len(name) < 2:
            continue
        slug = _slug(name)
        if slug in seen:
            continue
        seen.add(slug)
        rows.append({"text": name, "slug": slug, "confidence": 0.75 if name in known else 0.55})
        if len(rows) >= limit:
            break
    return rows


def signal_scan(text: str, source: ProvenanceSource | dict[str, Any] | str | None = None) -> dict[str, Any]:
    q = text or ""
    entities = detect_entities(q)
    first_person = bool(re.search(r"\b(je|j'|moi|mon|ma|mes|notre|nous)\b", q, re.IGNORECASE))
    reflective = bool(re.search(r"\b(id[ée]e|idee|vision|intuition|hypoth[eè]se|je pense|je crois|j'ai compris|angle mort)\b", q, re.IGNORECASE))
    durable = len(q.strip()) > 180 or bool(entities)
    recommended: list[str] = []
    if entities:
        recommended.append("link_entities")
    if first_person and reflective:
        recommended.append("preserve_exact_user_thought")
    if durable:
        recommended.append("append_timeline_evidence")
    if source:
        recommended.append("attach_provenance")
    return {
        "entities": entities,
        "original_thought": first_person and reflective,
        "durable_signal": durable,
        "boring": len(q.strip()) < 12 and not entities,
        "recommended_writes": recommended,
        "source": format_source(source) if source else "",
        "policy": policy(),
    }


def _find_marker(text: str, markers: tuple[str, ...]) -> tuple[int, str]:
    lowered = text.lower()
    for marker in markers:
        idx = lowered.find(marker.lower())
        if idx != -1:
            return idx, text[idx:idx + len(marker)]
    return -1, ""


def _strip_marker(text: str, marker: str) -> str:
    if not marker:
        return text
    idx = text.lower().find(marker.lower())
    if idx == -1:
        return text
    return text[:idx] + text[idx + len(marker):]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "entity"
