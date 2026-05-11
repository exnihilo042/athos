"""Goal Manager — BabyAGI-inspired priority task queue.

ATHOS maintains persistent goals it pursues autonomously.
Goals survive restarts (stored in Drive). The autonomous loop picks the top-priority
goal, decomposes it into steps, executes, observes, updates.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

try:
    from . import config
except ImportError:
    import config

GOALS_FILE = config.DRIVE / "athos_goals.json"

Status = Literal["pending", "active", "done", "failed", "blocked"]


@dataclass
class Goal:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    description: str = ""
    priority: int = 5          # 0 = highest
    status: Status = "pending"
    steps: list[str] = field(default_factory=list)
    current_step: int = 0
    result: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    source: str = "user"       # user | athos | autonomous_loop

    def to_dict(self) -> dict:
        return asdict(self)

    def next_step(self) -> str | None:
        if self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None

    def advance(self, result: str = "") -> None:
        if result:
            self.result += f"\n[step {self.current_step}] {result}"
        self.current_step += 1
        self.updated_at = time.time()
        if self.current_step >= len(self.steps):
            self.status = "done"

    def fail(self, reason: str) -> None:
        self.status = "failed"
        self.result += f"\n[failed] {reason}"
        self.updated_at = time.time()


class GoalManager:
    def __init__(self) -> None:
        self._goals: dict[str, Goal] = {}
        self._load()

    def _load(self) -> None:
        if GOALS_FILE.exists():
            try:
                data = json.loads(GOALS_FILE.read_text("utf-8"))
                self._goals = {g["id"]: Goal(**g) for g in data}
            except Exception:
                self._goals = {}

    def _save(self) -> None:
        try:
            GOALS_FILE.write_text(
                json.dumps([g.to_dict() for g in self._goals.values()], indent=2),
                "utf-8",
            )
        except Exception:
            pass

    def add(self, description: str, priority: int = 5, steps: list[str] | None = None,
            source: str = "user") -> Goal:
        g = Goal(description=description, priority=priority,
                 steps=steps or [], source=source)
        self._goals[g.id] = g
        self._save()
        return g

    def top(self) -> Goal | None:
        """Highest-priority pending or active goal."""
        candidates = [g for g in self._goals.values() if g.status in ("pending", "active")]
        if not candidates:
            return None
        return min(candidates, key=lambda g: (g.priority, g.created_at))

    def get(self, goal_id: str) -> Goal | None:
        return self._goals.get(goal_id)

    def update(self, goal: Goal) -> None:
        goal.updated_at = time.time()
        self._goals[goal.id] = goal
        self._save()

    def list_all(self) -> list[Goal]:
        return sorted(self._goals.values(), key=lambda g: (g.priority, g.created_at))

    def pending(self) -> list[Goal]:
        return [g for g in self.list_all() if g.status == "pending"]

    def done(self) -> list[Goal]:
        return [g for g in self.list_all() if g.status == "done"]

    def clear_done(self) -> int:
        before = len(self._goals)
        self._goals = {k: v for k, v in self._goals.items() if v.status != "done"}
        self._save()
        return before - len(self._goals)

    def status_summary(self) -> dict:
        counts: dict[str, int] = {}
        for g in self._goals.values():
            counts[g.status] = counts.get(g.status, 0) + 1
        return {"total": len(self._goals), **counts}


_manager: GoalManager | None = None


def get_manager() -> GoalManager:
    global _manager
    if _manager is None:
        _manager = GoalManager()
    return _manager
