"""Skill Library — Voyager-inspired autonomous skill acquisition.

ATHOS builds a library of callable Python skills over time.
Each skill is:
  - A named Python function stored as source code
  - Tested before being added
  - Retrieved by semantic description match
  - Composable: skills can call other skills

Acquisition loop (run by autonomous_loop or on demand):
  gap_detected → generate_code(LLM) → sandbox_test → integrate → commit → notify
"""
from __future__ import annotations

import importlib
import inspect
import json
import subprocess
import sys
import textwrap
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    from . import config
except ImportError:
    import config

SKILLS_DIR = config.ATHOS_PATH / "core" / "skills"
SKILLS_MANIFEST = SKILLS_DIR / "manifest.json"
SKILLS_DIR.mkdir(exist_ok=True)


@dataclass
class Skill:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    description: str = ""
    code: str = ""             # full Python source of the function
    dependencies: list[str] = field(default_factory=list)  # pip packages
    tags: list[str] = field(default_factory=list)
    test_code: str = ""        # minimal test that must pass
    status: str = "pending"    # pending | tested | active | deprecated
    created_at: float = field(default_factory=time.time)
    last_used: float | None = None
    use_count: int = 0
    source_repo: str = ""      # if borrowed from a public repo

    def to_dict(self) -> dict:
        return asdict(self)

    def file_path(self) -> Path:
        safe = self.name.lower().replace(" ", "_").replace("-", "_")
        return SKILLS_DIR / f"{safe}.py"


class SkillLibrary:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self._load()

    def _load(self) -> None:
        if SKILLS_MANIFEST.exists():
            try:
                data = json.loads(SKILLS_MANIFEST.read_text("utf-8"))
                self._skills = {s["id"]: Skill(**s) for s in data}
            except Exception:
                self._skills = {}

    def _save(self) -> None:
        try:
            SKILLS_MANIFEST.write_text(
                json.dumps([s.to_dict() for s in self._skills.values()], indent=2),
                "utf-8",
            )
        except Exception:
            pass

    # ── Acquisition ──────────────────────────────────────────────────────────

    def propose(self, name: str, description: str, code: str,
                dependencies: list[str] | None = None, tags: list[str] | None = None,
                test_code: str = "", source_repo: str = "") -> Skill:
        """Propose a new skill. Status = pending until tested."""
        skill = Skill(
            name=name, description=description, code=code,
            dependencies=dependencies or [], tags=tags or [],
            test_code=test_code, source_repo=source_repo,
            status="pending",
        )
        self._skills[skill.id] = skill
        self._save()
        return skill

    def test_and_integrate(self, skill_id: str) -> tuple[bool, str]:
        """Run test_code in subprocess. If passes, write file and mark active."""
        skill = self._skills.get(skill_id)
        if not skill:
            return False, "skill not found"

        # Write skill file
        skill.file_path().write_text(skill.code, "utf-8")

        # Install dependencies if needed
        if skill.dependencies:
            for dep in skill.dependencies:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep, "-q"],
                    capture_output=True,
                )

        # Run test
        if skill.test_code:
            test_src = skill.code + "\n\n" + skill.test_code
            result = subprocess.run(
                [sys.executable, "-c", test_src],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                skill.status = "pending"
                self._save()
                return False, result.stderr[:400]

        skill.status = "active"
        self._save()
        return True, "ok"

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def search(self, query: str, limit: int = 5) -> list[Skill]:
        """Simple keyword match on name + description + tags."""
        q = query.lower()
        scored: list[tuple[int, Skill]] = []
        for s in self._skills.values():
            if s.status != "active":
                continue
            score = 0
            if q in s.name.lower():
                score += 3
            if q in s.description.lower():
                score += 2
            if any(q in t.lower() for t in s.tags):
                score += 1
            if score:
                scored.append((score, s))
        scored.sort(key=lambda x: -x[0])
        return [s for _, s in scored[:limit]]

    def get_by_name(self, name: str) -> Skill | None:
        for s in self._skills.values():
            if s.name.lower() == name.lower() and s.status == "active":
                return s
        return None

    def call(self, skill_name: str, **kwargs) -> any:
        """Load and execute a skill by name."""
        skill = self.get_by_name(skill_name)
        if not skill:
            raise ValueError(f"Skill '{skill_name}' not found or not active")
        # Dynamic import from file
        spec = importlib.util.spec_from_file_location(skill_name, skill.file_path())
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fn = getattr(mod, skill_name, None)
        if not fn:
            raise AttributeError(f"Function '{skill_name}' not found in skill file")
        skill.last_used = time.time()
        skill.use_count += 1
        self._save()
        return fn(**kwargs)

    # ── Introspection ─────────────────────────────────────────────────────────

    def list_active(self) -> list[Skill]:
        return [s for s in self._skills.values() if s.status == "active"]

    def summary(self) -> dict:
        counts: dict[str, int] = {}
        for s in self._skills.values():
            counts[s.status] = counts.get(s.status, 0) + 1
        top = sorted(
            [s for s in self._skills.values() if s.status == "active"],
            key=lambda s: -(s.use_count or 0),
        )[:5]
        return {
            "total": len(self._skills),
            **counts,
            "most_used": [s.name for s in top],
        }

    def context_for_llm(self, limit: int = 20) -> str:
        """Return active skill list as text for LLM context."""
        active = self.list_active()[:limit]
        if not active:
            return "Aucun skill acquis."
        lines = ["SKILLS ATHOS disponibles:"]
        for s in active:
            lines.append(f"  • {s.name}: {s.description}")
        return "\n".join(lines)


_library: SkillLibrary | None = None


def get_library() -> SkillLibrary:
    global _library
    if _library is None:
        _library = SkillLibrary()
    return _library
