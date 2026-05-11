"""Autonomous Loop — AutoGPT/BabyAGI continuous execution.

ATHOS runs this loop to pursue goals without human input.
Each iteration:
  1. Read top goal from GoalManager
  2. Decompose into steps if needed (LLM)
  3. Execute next step using available tools + skills
  4. Observe result → update beliefs
  5. Advance or fail goal
  6. Optionally propose new skills if gap detected

Designed to run as a background thread or subprocess.
Stops cleanly on signal or when idle_stop_after_n_empty is reached.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from typing import Callable

try:
    from . import config, session_kernel
    from .goal_manager import get_manager, Goal
    from .belief_store import get_store
    from .skill_library import get_library
    from .tools.web_search import summarize_search
except ImportError:
    import config
    import session_kernel
    from goal_manager import get_manager, Goal
    from belief_store import get_store
    from skill_library import get_library
    from tools.web_search import summarize_search

logger = logging.getLogger("athos.loop")

LOOP_STATE_FILE = config.DRIVE / "athos_loop_state.json"
LOOP_EVENTS_FILE = config.DRIVE / "athos_loop_events.jsonl"

_running = threading.Event()
_loop_thread: threading.Thread | None = None


class AutonomousLoop:
    """
    Continuous goal execution engine.

    llm_call: callable(prompt: str) -> str  — injected so loop is engine-agnostic
    tick_interval: seconds between iterations when idle
    idle_stop_after: stop after N consecutive idle ticks (0 = never stop)
    on_event: optional callback(event_type: str, data: dict) for UI/WebSocket push
    """

    def __init__(
        self,
        llm_call: Callable[[str], str],
        tick_interval: float = 30.0,
        idle_stop_after: int = 0,
        allow_skill_mutation: bool = False,
        on_event: Callable[[str, dict], None] | None = None,
    ) -> None:
        self.llm = llm_call
        self.tick_interval = max(float(tick_interval), getattr(config, "AUTONOMOUS_LOOP_MIN_TICK", 5.0))
        self.idle_stop_after = idle_stop_after
        self.allow_skill_mutation = allow_skill_mutation
        self.on_event = on_event or (lambda t, d: None)
        self._stop_flag = threading.Event()
        self._idle_ticks = 0
        self._iteration = 0
        self._last_event: dict | None = None

    # ── Public control ────────────────────────────────────────────────────────

    def start(self, daemon: bool = True) -> threading.Thread:
        self._stop_flag.clear()
        t = threading.Thread(target=self._loop, name="athos-autonomous-loop", daemon=daemon)
        t.start()
        return t

    def stop(self) -> None:
        self._stop_flag.set()

    def is_alive(self) -> bool:
        return not self._stop_flag.is_set()

    def status(self) -> dict:
        return {
            "running": self.is_alive(),
            "iterations": self._iteration,
            "idle_ticks": self._idle_ticks,
            "tick_interval": self.tick_interval,
            "idle_stop_after": self.idle_stop_after,
            "allow_skill_mutation": self.allow_skill_mutation,
            "last_event": self._last_event,
            "events_file": str(LOOP_EVENTS_FILE),
            "state_file": str(LOOP_STATE_FILE),
        }

    # ── Main loop ─────────────────────────────────────────────────────────────

    def _loop(self) -> None:
        logger.info("Autonomous loop started")
        self._emit("loop_started", {"policy": loop_policy()})
        while not self._stop_flag.is_set():
            try:
                self._tick()
            except Exception as e:
                logger.error("Loop tick error: %s", e, exc_info=True)
                self._emit("loop_error", {"error": str(e)})
            self._stop_flag.wait(timeout=self.tick_interval)
        logger.info("Autonomous loop stopped after %d iterations", self._iteration)
        self._emit("loop_stopped", {"iterations": self._iteration})

    def _tick(self) -> None:
        self._iteration += 1
        manager = get_manager()
        goal = manager.top()

        if not goal:
            self._idle_ticks += 1
            self._emit("idle", {"idle_ticks": self._idle_ticks})
            if self.idle_stop_after and self._idle_ticks >= self.idle_stop_after:
                logger.info("Idle stop threshold reached")
                self._stop_flag.set()
            return

        self._idle_ticks = 0
        self._emit("goal_picked", {"id": goal.id, "description": goal.description,
                                    "priority": goal.priority, "status": goal.status})

        # Decompose if no steps yet
        if not goal.steps:
            self._decompose(goal)
            manager.update(goal)
            if not goal.steps:
                goal.fail("LLM returned no steps")
                manager.update(goal)
                return

        goal.status = "active"
        manager.update(goal)

        step = goal.next_step()
        if not step:
            goal.status = "done"
            manager.update(goal)
            self._emit("goal_done", {"id": goal.id})
            return

        self._emit("step_start", {"goal_id": goal.id, "step": step,
                                   "step_n": goal.current_step})

        result = self._execute_step(goal, step)
        goal.advance(result)
        manager.update(goal)

        self._emit("step_done", {"goal_id": goal.id, "step": step, "result": result[:300]})

        # Auto-acquire skill if step result signals a gap
        self._maybe_acquire(result)

    # ── Decomposition ─────────────────────────────────────────────────────────

    def _decompose(self, goal: Goal) -> None:
        library = get_library()
        store = get_store()
        skills_ctx = library.context_for_llm(10)
        beliefs_ctx = store.context_for(goal.description, 5)

        prompt = f"""Tu es le planificateur d'ATHOS. Décompose cet objectif en 3-7 étapes concrètes.
Chaque étape doit être une action atomique et vérifiable.
Réponds UNIQUEMENT avec un JSON array de strings. Exemple: ["étape1", "étape2"]

OBJECTIF: {goal.description}

{beliefs_ctx}
{skills_ctx}

JSON:"""

        try:
            raw = self.llm(prompt).strip()
            # Extract JSON array even if wrapped in markdown
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start >= 0 and end > start:
                steps = json.loads(raw[start:end])
                if isinstance(steps, list) and steps:
                    goal.steps = [str(s) for s in steps]
                    return
        except Exception as e:
            logger.warning("Decompose failed: %s", e)

        # Fallback: single step = the goal itself
        goal.steps = [f"Accomplir: {goal.description}"]

    # ── Step execution ─────────────────────────────────────────────────────────

    def _execute_step(self, goal: Goal, step: str) -> str:
        store = get_store()
        library = get_library()

        # Check if a skill matches
        skills = library.search(step, limit=3)
        skill_ctx = ""
        if skills:
            skill_ctx = "Skills disponibles:\n" + "\n".join(
                f"  • {s.name}: {s.description}" for s in skills
            )

        # Build web context if step mentions research/search
        web_ctx = ""
        if any(kw in step.lower() for kw in ["recherche", "search", "trouve", "find", "check"]):
            web_ctx = summarize_search(step, max_results=3)

        beliefs_ctx = store.context_for(goal.description, 5)

        prompt = f"""Tu es ATHOS en mode autonome. Exécute cette étape et rapporte le résultat.
Sois concis. Décris ce que tu as fait/trouvé/calculé.

OBJECTIF GLOBAL: {goal.description}
ÉTAPE: {step}

{beliefs_ctx}
{web_ctx}
{skill_ctx}

RÉSULTAT:"""

        try:
            result = self.llm(prompt).strip()
        except Exception as e:
            result = f"[erreur] {e}"

        # Auto-add belief from result
        if result and not result.startswith("[erreur]"):
            store.add(
                subject=goal.description,
                predicate=f"step '{step[:60]}': {result[:200]}",
                confidence=0.7,
                source="autonomous_loop",
            )

        return result

    # ── Skill acquisition ─────────────────────────────────────────────────────

    def _maybe_acquire(self, text: str) -> None:
        try:
            from skill_acquisition import scan_and_acquire
        except ImportError:
            try:
                from .skill_acquisition import scan_and_acquire
            except ImportError:
                return
        try:
            skill = scan_and_acquire(
                text,
                self.llm,
                allow_mutation=self.allow_skill_mutation,
                allow_dependency_install=self.allow_skill_mutation,
            )
            if skill:
                event_type = "skill_acquired" if skill.status == "active" else "skill_proposed"
                self._emit(event_type, {"name": skill.name, "description": skill.description, "status": skill.status})
        except Exception as e:
            logger.debug("skill acquisition skipped: %s", e)

    # ── Events ────────────────────────────────────────────────────────────────

    def _emit(self, event_type: str, data: dict) -> None:
        event = {"type": event_type, "ts": time.time(), **data}
        self._last_event = event
        _append_event(event)
        _write_state(self.status())
        try:
            self.on_event(event_type, event)
        except Exception:
            pass


# ── Module-level singleton helpers ─────────────────────────────────────────────

_loop_instance: AutonomousLoop | None = None


def get_loop() -> AutonomousLoop | None:
    return _loop_instance


def start_loop(
    llm_call: Callable[[str], str],
    tick_interval: float = 30.0,
    idle_stop_after: int = 0,
    allow_autonomous: bool = False,
    allow_skill_mutation: bool = False,
    on_event: Callable[[str, dict], None] | None = None,
) -> AutonomousLoop:
    global _loop_instance
    if _loop_instance and _loop_instance.is_alive():
        return _loop_instance
    if not (allow_autonomous or getattr(config, "AUTONOMOUS_LOOP_ENABLED", False)):
        raise PermissionError("autonomous loop start requires explicit allow_autonomous=true or ATHOS_AUTONOMOUS_LOOP_ENABLED=true")
    _loop_instance = AutonomousLoop(
        llm_call=llm_call,
        tick_interval=tick_interval,
        idle_stop_after=idle_stop_after,
        allow_skill_mutation=allow_skill_mutation and getattr(config, "SKILL_INSTALL_ENABLED", False),
        on_event=on_event,
    )
    _loop_instance.start()
    session_kernel.record_action(
        "autonomous_loop_start",
        f"tick={tick_interval}",
        "running",
        engine="athos_kernel",
        meta={"allow_skill_mutation": _loop_instance.allow_skill_mutation},
    )
    return _loop_instance


def stop_loop() -> None:
    global _loop_instance
    if _loop_instance:
        _loop_instance.stop()
        session_kernel.record_action("autonomous_loop_stop", "manual", "stopping", engine="athos_kernel")


def loop_policy() -> dict:
    return {
        "env_enabled": getattr(config, "AUTONOMOUS_LOOP_ENABLED", False),
        "default_tick": getattr(config, "AUTONOMOUS_LOOP_DEFAULT_TICK", 30.0),
        "min_tick": getattr(config, "AUTONOMOUS_LOOP_MIN_TICK", 5.0),
        "skill_mutation_enabled": getattr(config, "SKILL_INSTALL_ENABLED", False),
        "events_file": str(LOOP_EVENTS_FILE),
        "state_file": str(LOOP_STATE_FILE),
    }


def status() -> dict:
    loop = get_loop()
    if loop:
        return {**loop.status(), "policy": loop_policy()}
    return {
        "running": False,
        "iterations": 0,
        "idle_ticks": 0,
        "last_event": _read_last_event(),
        "events_file": str(LOOP_EVENTS_FILE),
        "state_file": str(LOOP_STATE_FILE),
        "policy": loop_policy(),
    }


def recent_events(limit: int = 20) -> list[dict]:
    if not LOOP_EVENTS_FILE.exists():
        return []
    rows = []
    for line in LOOP_EVENTS_FILE.read_text("utf-8").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"type": "corrupt", "raw": line[:300]})
    return rows


def _append_event(event: dict) -> None:
    try:
        LOOP_EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOOP_EVENTS_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
    except Exception:
        pass


def _read_last_event() -> dict | None:
    events = recent_events(limit=1)
    return events[-1] if events else None


def _write_state(data: dict) -> None:
    try:
        LOOP_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOOP_STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    except Exception:
        pass
