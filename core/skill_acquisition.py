"""Skill Acquisition — Voyager/SWE-agent inspired autonomous skill generation.

When ATHOS detects a capability gap:
  1. Search for existing implementations (GitHub, web)
  2. Generate Python code via LLM
  3. Test in subprocess
  4. Integrate into SkillLibrary

Called by the autonomous loop or on demand from detect_and_acquire().
"""
from __future__ import annotations

import logging
import re
import textwrap
from typing import Callable

try:
    from .skill_library import get_library, Skill
    from .tools.web_search import search_github, summarize_search
    from .belief_store import get_store
except ImportError:
    from skill_library import get_library, Skill
    from tools.web_search import search_github, summarize_search
    from belief_store import get_store

logger = logging.getLogger("athos.skill_acquisition")

# Keywords that signal a missing capability
GAP_SIGNALS = [
    "je ne sais pas", "je ne peux pas", "pas de skill", "aucun skill",
    "pas de capacité", "je suis incapable", "not found", "unavailable",
    "cannot", "je ne dispose pas", "fonctionnalité manquante",
]


def detect_gap(text: str) -> str | None:
    """Return a short gap description if text signals a missing capability, else None."""
    t = text.lower()
    for sig in GAP_SIGNALS:
        if sig in t:
            # Extract the subject around the gap signal
            idx = t.find(sig)
            snippet = text[max(0, idx - 40): idx + len(sig) + 60].strip()
            return snippet
    return None


def _extract_python(raw: str) -> str:
    """Extract the first Python code block from a markdown-fenced LLM response."""
    # ```python ... ``` blocks
    m = re.search(r"```(?:python)?\n(.*?)```", raw, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Fallback: return stripped raw if it looks like code
    if "def " in raw:
        return raw.strip()
    return ""


def generate_skill(
    gap_description: str,
    llm_call: Callable[[str], str],
    search_results: str = "",
) -> tuple[str, str, str]:
    """
    Ask the LLM to generate a Python skill for the gap.
    Returns (name, code, test_code).
    """
    context = f"\nRéférences trouvées:\n{search_results}" if search_results else ""

    prompt = f"""Tu es ATHOS en mode acquisition de skill. Génère une fonction Python autonome pour combler ce gap:

GAP: {gap_description}
{context}

Règles:
- Fonction autonome, imports inclus dans le corps si nécessaire
- Nom snake_case court et descriptif
- Pas de dépendances externes sauf stdlib + requests si réseau
- Docstring une ligne max
- Code minimal qui fonctionne

Réponds avec EXACTEMENT ce format JSON (rien d'autre):
{{
  "name": "nom_fonction",
  "description": "ce que fait la skill en une phrase",
  "code": "def nom_fonction(...):\\n    ...",
  "test_code": "assert nom_fonction(...) == ..."
}}"""

    try:
        raw = llm_call(prompt).strip()
        # Extract JSON
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            import json
            data = json.loads(raw[start:end])
            name = data.get("name", "").strip()
            code = data.get("code", "").strip()
            test = data.get("test_code", "").strip()
            if name and code and "def " in code:
                return name, code, test
    except Exception as e:
        logger.warning("generate_skill parse failed: %s", e)

    return "", "", ""


def acquire(
    gap_description: str,
    llm_call: Callable[[str], str],
    max_attempts: int = 2,
    allow_mutation: bool = False,
    allow_dependency_install: bool = False,
) -> Skill | None:
    """
    Full acquisition pipeline for a gap.
    Returns the integrated Skill or None if failed.
    """
    lib = get_library()
    store = get_store()

    # Check if skill already exists
    existing = lib.search(gap_description, limit=1)
    if existing:
        logger.info("Skill already exists for gap: %s", gap_description)
        return existing[0]

    # Search for inspiration
    github_results = search_github(gap_description, max_results=3)
    web_results = summarize_search(gap_description, max_results=3)
    search_ctx = web_results + "\n" + "\n".join(
        f"  • {r['title']}: {r['snippet'][:150]}" for r in github_results
    )

    for attempt in range(max_attempts):
        name, code, test_code = generate_skill(gap_description, llm_call, search_ctx)
        if not name or not code:
            logger.warning("Acquisition attempt %d: LLM returned empty code", attempt + 1)
            continue

        # Check for name collision
        if lib.get_by_name(name):
            name = f"{name}_v{attempt + 2}"

        skill = lib.propose(
            name=name,
            description=gap_description[:200],
            code=code,
            test_code=test_code,
            tags=["auto_acquired"],
        )

        if not allow_mutation:
            store.add(
                subject="skill_library",
                predicate=f"skill proposal '{name}' pending approval for gap: {gap_description[:80]}",
                confidence=0.8,
                source="skill_acquisition",
                tags=["pending_approval"],
            )
            return skill

        ok, msg = lib.test_and_integrate(
            skill.id,
            allow_mutation=allow_mutation,
            allow_dependency_install=allow_dependency_install,
        )
        if ok:
            logger.info("Skill acquired: %s", name)
            store.add(
                subject="skill_library",
                predicate=f"new skill '{name}' acquired for gap: {gap_description[:80]}",
                confidence=0.9,
                source="skill_acquisition",
            )
            return skill

        logger.warning("Skill test failed (attempt %d): %s", attempt + 1, msg[:200])

    store.add(
        subject="skill_library",
        predicate=f"failed to acquire skill for: {gap_description[:80]}",
        confidence=0.6,
        source="skill_acquisition",
    )
    return None


def scan_and_acquire(
    text: str,
    llm_call: Callable[[str], str],
    allow_mutation: bool = False,
    allow_dependency_install: bool = False,
) -> Skill | None:
    """
    Scan text for a gap signal and auto-acquire if found.
    Returns the Skill if acquired, None otherwise.
    """
    gap = detect_gap(text)
    if not gap:
        return None
    logger.info("Gap detected: %s", gap[:80])
    return acquire(
        gap,
        llm_call,
        allow_mutation=allow_mutation,
        allow_dependency_install=allow_dependency_install,
    )
