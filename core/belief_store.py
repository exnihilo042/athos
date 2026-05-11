"""Belief Store — structured working memory with confidence scores.

Inspired by MetaGPT's structured knowledge and cognitive architectures.
ATHOS maintains beliefs about the world: facts it has verified, their source,
confidence level, and when they expire. Unlike flat .mem files, beliefs are
queryable, comparable, and can be updated by new evidence.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    from . import config
except ImportError:
    import config

BELIEFS_FILE = config.DRIVE / "athos_beliefs.json"


@dataclass
class Belief:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    subject: str = ""          # what this belief is about
    predicate: str = ""        # the claim
    confidence: float = 0.8    # 0.0 – 1.0
    source: str = "inference"  # user | web_search | observation | inference | memory
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None  # None = permanent
    verified: bool = False

    def is_valid(self) -> bool:
        if self.expires_at and time.time() > self.expires_at:
            return False
        return True

    def to_dict(self) -> dict:
        return asdict(self)

    def __str__(self) -> str:
        conf = f"{int(self.confidence * 100)}%"
        src = self.source
        return f"[{conf}|{src}] {self.subject}: {self.predicate}"


class BeliefStore:
    def __init__(self) -> None:
        self._beliefs: dict[str, Belief] = {}
        self._load()

    def _load(self) -> None:
        if BELIEFS_FILE.exists():
            try:
                data = json.loads(BELIEFS_FILE.read_text("utf-8"))
                self._beliefs = {b["id"]: Belief(**b) for b in data}
            except Exception:
                self._beliefs = {}

    def _save(self) -> None:
        try:
            valid = {k: v for k, v in self._beliefs.items() if v.is_valid()}
            BELIEFS_FILE.write_text(
                json.dumps([b.to_dict() for b in valid.values()], indent=2),
                "utf-8",
            )
            self._beliefs = valid
        except Exception:
            pass

    def add(self, subject: str, predicate: str, confidence: float = 0.8,
            source: str = "inference", tags: list[str] | None = None,
            ttl_seconds: float | None = None, verified: bool = False) -> Belief:
        # Update existing belief if same subject+predicate
        for b in self._beliefs.values():
            if b.subject == subject and b.predicate == predicate:
                b.confidence = max(b.confidence, confidence)
                b.source = source
                b.verified = verified or b.verified
                self._save()
                return b
        b = Belief(
            subject=subject, predicate=predicate, confidence=confidence,
            source=source, tags=tags or [], verified=verified,
            expires_at=time.time() + ttl_seconds if ttl_seconds else None,
        )
        self._beliefs[b.id] = b
        self._save()
        return b

    def query(self, subject: str | None = None, tag: str | None = None,
              min_confidence: float = 0.0) -> list[Belief]:
        results = [b for b in self._beliefs.values()
                   if b.is_valid() and b.confidence >= min_confidence]
        if subject:
            results = [b for b in results if subject.lower() in b.subject.lower()]
        if tag:
            results = [b for b in results if tag in b.tags]
        return sorted(results, key=lambda b: -b.confidence)

    def context_for(self, topic: str, limit: int = 10) -> str:
        """Return beliefs relevant to a topic as a text block for LLM context."""
        relevant = self.query(subject=topic)[:limit]
        if not relevant:
            return ""
        lines = [f"BELIEFS sur '{topic}':"]
        lines += [f"  • {b}" for b in relevant]
        return "\n".join(lines)

    def forget(self, belief_id: str) -> bool:
        if belief_id in self._beliefs:
            del self._beliefs[belief_id]
            self._save()
            return True
        return False

    def forget_by_subject(self, subject: str) -> int:
        before = len(self._beliefs)
        self._beliefs = {k: v for k, v in self._beliefs.items()
                        if v.subject != subject}
        self._save()
        return before - len(self._beliefs)

    def summary(self) -> dict:
        valid = [b for b in self._beliefs.values() if b.is_valid()]
        return {
            "total": len(valid),
            "verified": sum(1 for b in valid if b.verified),
            "high_confidence": sum(1 for b in valid if b.confidence >= 0.8),
            "sources": list({b.source for b in valid}),
        }


_store: BeliefStore | None = None


def get_store() -> BeliefStore:
    global _store
    if _store is None:
        _store = BeliefStore()
    return _store
