"""Tests for AGI cognition modules: goal_manager, belief_store, web_search, skill_library, autonomous_loop."""
from __future__ import annotations

import sys
import time
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add core to path so relative imports resolve
CORE_DIR = Path(__file__).parent.parent / "core"
REPO_DIR = Path(__file__).parent.parent
for p in (str(REPO_DIR), str(CORE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)


def _mock_config(tmp_path: Path) -> types.ModuleType:
    cfg = types.ModuleType("config")
    cfg.DRIVE = tmp_path
    cfg.ATHOS_PATH = tmp_path
    cfg.AUTONOMOUS_LOOP_ENABLED = False
    cfg.AUTONOMOUS_LOOP_DEFAULT_TICK = 0.01
    cfg.AUTONOMOUS_LOOP_MIN_TICK = 0.001
    cfg.SKILL_INSTALL_ENABLED = False
    (tmp_path / "core" / "skills").mkdir(parents=True, exist_ok=True)
    return cfg


# ══════════════════════════════════════════════════════════════════════════════
# GoalManager
# ══════════════════════════════════════════════════════════════════════════════

class TestGoalManager:
    def _gm(self, tmp_path):
        cfg = _mock_config(tmp_path)
        with patch.dict(sys.modules, {"config": cfg}):
            import importlib
            import goal_manager as gm_mod
            importlib.reload(gm_mod)
            return gm_mod.GoalManager()

    def test_add_and_top(self, tmp_path):
        gm = self._gm(tmp_path)
        g = gm.add("Do X", priority=3)
        assert gm.top().id == g.id

    def test_priority_order(self, tmp_path):
        gm = self._gm(tmp_path)
        gm.add("Low", priority=9)
        g_high = gm.add("High", priority=1)
        assert gm.top().id == g_high.id

    def test_advance_to_done(self, tmp_path):
        gm = self._gm(tmp_path)
        g = gm.add("Task", steps=["s1", "s2"])
        assert g.next_step() == "s1"
        g.advance("result1")
        assert g.next_step() == "s2"
        g.advance("result2")
        assert g.status == "done"

    def test_fail(self, tmp_path):
        gm = self._gm(tmp_path)
        g = gm.add("Task")
        g.fail("boom")
        assert g.status == "failed"
        assert "boom" in g.result

    def test_persistence(self, tmp_path):
        cfg = _mock_config(tmp_path)
        with patch.dict(sys.modules, {"config": cfg}):
            import importlib
            import goal_manager as gm_mod
            importlib.reload(gm_mod)
            gm1 = gm_mod.GoalManager()
            g = gm1.add("Persist me", priority=2)
            gm2 = gm_mod.GoalManager()
            assert gm2.get(g.id) is not None
            assert gm2.get(g.id).description == "Persist me"

    def test_status_summary(self, tmp_path):
        gm = self._gm(tmp_path)
        gm.add("A")
        gm.add("B")
        s = gm.status_summary()
        assert s["total"] == 2
        assert s.get("pending", 0) == 2

    def test_clear_done(self, tmp_path):
        gm = self._gm(tmp_path)
        g = gm.add("Done", steps=["x"])
        g.advance()
        gm.update(g)
        removed = gm.clear_done()
        assert removed == 1
        assert gm.top() is None


class TestSkillLibraryRollback:
    def test_failed_test_rolls_back_new_skill_file(self, tmp_path):
        cfg = _mock_config(tmp_path)
        with patch.dict(sys.modules, {"config": cfg}):
            import importlib
            import skill_library as sl_mod
            importlib.reload(sl_mod)
            sl_mod.SKILLS_DIR = tmp_path / "core" / "skills"
            sl_mod.SKILLS_MANIFEST = sl_mod.SKILLS_DIR / "manifest.json"
            sl_mod.SKILLS_DIR.mkdir(parents=True, exist_ok=True)
            lib = sl_mod.SkillLibrary()

            skill = lib.propose(
                name="bad_skill",
                description="bad",
                code="def bad_skill():\n    return 'bad'\n",
                test_code="assert bad_skill() == 'ok'",
            )
            ok, msg = lib.test_and_integrate(skill.id, allow_mutation=True)

        assert ok is False
        assert msg
        assert not (tmp_path / "core" / "skills" / "bad_skill.py").exists()

    def test_failed_test_restores_existing_skill_file(self, tmp_path):
        cfg = _mock_config(tmp_path)
        with patch.dict(sys.modules, {"config": cfg}):
            import importlib
            import skill_library as sl_mod
            importlib.reload(sl_mod)
            sl_mod.SKILLS_DIR = tmp_path / "core" / "skills"
            sl_mod.SKILLS_MANIFEST = sl_mod.SKILLS_DIR / "manifest.json"
            sl_mod.SKILLS_DIR.mkdir(parents=True, exist_ok=True)
            existing = sl_mod.SKILLS_DIR / "bad_skill.py"
            existing.write_text("def old():\n    return 'old'\n", "utf-8")
            lib = sl_mod.SkillLibrary()

            skill = lib.propose(
                name="bad_skill",
                description="bad",
                code="def bad_skill():\n    return 'bad'\n",
                test_code="assert bad_skill() == 'ok'",
            )
            ok, _ = lib.test_and_integrate(skill.id, allow_mutation=True)

        assert ok is False
        assert (tmp_path / "core" / "skills" / "bad_skill.py").read_text("utf-8") == "def old():\n    return 'old'\n"


# ══════════════════════════════════════════════════════════════════════════════
# BeliefStore
# ══════════════════════════════════════════════════════════════════════════════

class TestBeliefStore:
    def _bs(self, tmp_path):
        cfg = _mock_config(tmp_path)
        with patch.dict(sys.modules, {"config": cfg}):
            import importlib
            import belief_store as bs_mod
            importlib.reload(bs_mod)
            return bs_mod.BeliefStore()

    def test_add_and_query(self, tmp_path):
        bs = self._bs(tmp_path)
        bs.add("weather", "it is sunny", confidence=0.9, source="user")
        results = bs.query(subject="weather")
        assert len(results) == 1
        assert results[0].predicate == "it is sunny"

    def test_dedup_updates_confidence(self, tmp_path):
        bs = self._bs(tmp_path)
        bs.add("sky", "is blue", confidence=0.5)
        bs.add("sky", "is blue", confidence=0.9)
        results = bs.query(subject="sky")
        assert len(results) == 1
        assert results[0].confidence == 0.9

    def test_expiry(self, tmp_path):
        bs = self._bs(tmp_path)
        bs.add("temp", "cold", ttl_seconds=0.01)
        time.sleep(0.05)
        results = bs.query(subject="temp")
        assert len(results) == 0

    def test_forget(self, tmp_path):
        bs = self._bs(tmp_path)
        b = bs.add("thing", "exists")
        assert bs.forget(b.id) is True
        assert len(bs.query(subject="thing")) == 0

    def test_forget_by_subject(self, tmp_path):
        bs = self._bs(tmp_path)
        bs.add("cat", "is alive")
        bs.add("cat", "is orange")
        removed = bs.forget_by_subject("cat")
        assert removed == 2

    def test_min_confidence_filter(self, tmp_path):
        bs = self._bs(tmp_path)
        bs.add("A", "high", confidence=0.9)
        bs.add("B", "low", confidence=0.3)
        results = bs.query(min_confidence=0.7)
        assert all(b.confidence >= 0.7 for b in results)

    def test_context_for_llm(self, tmp_path):
        bs = self._bs(tmp_path)
        bs.add("projet", "en cours", confidence=0.8)
        ctx = bs.context_for("projet")
        assert "projet" in ctx
        assert "en cours" in ctx

    def test_persistence(self, tmp_path):
        cfg = _mock_config(tmp_path)
        with patch.dict(sys.modules, {"config": cfg}):
            import importlib
            import belief_store as bs_mod
            importlib.reload(bs_mod)
            bs1 = bs_mod.BeliefStore()
            bs1.add("memory", "persists", confidence=0.8)
            bs2 = bs_mod.BeliefStore()
            results = bs2.query(subject="memory")
            assert len(results) == 1


# ══════════════════════════════════════════════════════════════════════════════
# WebSearch
# ══════════════════════════════════════════════════════════════════════════════

class TestWebSearch:
    def _mod(self):
        import tools.web_search as ws
        return ws

    def test_search_returns_list(self):
        ws = self._mod()
        results = ws.search("Python programming", max_results=3)
        assert isinstance(results, list)
        for r in results:
            assert "title" in r and "url" in r and "snippet" in r

    def test_search_error_handled(self):
        ws = self._mod()
        with patch("urllib.request.urlopen", side_effect=Exception("network down")):
            results = ws.search("anything")
        assert len(results) == 1
        assert results[0]["title"] == "search_error"

    def test_summarize_search_returns_string(self):
        ws = self._mod()
        with patch.object(ws, "search", return_value=[
            {"title": "Test", "url": "http://example.com", "snippet": "A test snippet"},
        ]):
            summary = ws.summarize_search("test query")
        assert "test query" in summary
        assert "Test" in summary

    def test_fetch_raw_error_handled(self):
        ws = self._mod()
        with patch("urllib.request.urlopen", side_effect=Exception("timeout")):
            result = ws.fetch_raw("http://example.com")
        assert "fetch_error" in result

    def test_search_github_returns_list(self):
        ws = self._mod()
        results = ws.search_github("athos agent", max_results=2)
        assert isinstance(results, list)


# ══════════════════════════════════════════════════════════════════════════════
# SkillLibrary
# ══════════════════════════════════════════════════════════════════════════════

class TestSkillLibrary:
    def _lib(self, tmp_path):
        cfg = _mock_config(tmp_path)
        with patch.dict(sys.modules, {"config": cfg}):
            import importlib
            import skill_library as sl_mod
            importlib.reload(sl_mod)
            sl_mod.SKILLS_DIR = tmp_path / "core" / "skills"
            sl_mod.SKILLS_MANIFEST = sl_mod.SKILLS_DIR / "manifest.json"
            sl_mod.SKILLS_DIR.mkdir(parents=True, exist_ok=True)
            return sl_mod.SkillLibrary()

    def test_propose_creates_pending_skill(self, tmp_path):
        lib = self._lib(tmp_path)
        skill = lib.propose("my_skill", "does something", "def my_skill(): pass")
        assert skill.status == "pending"

    def test_search_finds_by_name(self, tmp_path):
        lib = self._lib(tmp_path)
        s = lib.propose("weather_fetch", "fetches weather", "def weather_fetch(): pass")
        s.status = "active"
        lib._save()
        results = lib.search("weather")
        assert any(r.name == "weather_fetch" for r in results)

    def test_test_and_integrate_success(self, tmp_path):
        lib = self._lib(tmp_path)
        code = "def add_numbers(a, b):\n    return a + b\n"
        test = "assert add_numbers(2, 3) == 5"
        skill = lib.propose("add_numbers", "adds two numbers", code, test_code=test)
        ok, msg = lib.test_and_integrate(skill.id, allow_mutation=True)
        assert ok is True
        assert lib._skills[skill.id].status == "active"

    def test_test_and_integrate_blocks_without_visible_approval(self, tmp_path):
        lib = self._lib(tmp_path)
        skill = lib.propose("needs_review", "requires approval", "def needs_review(): return True")

        ok, msg = lib.test_and_integrate(skill.id)

        assert ok is False
        assert "approval" in msg
        assert lib._skills[skill.id].status == "pending_review"

    def test_test_and_integrate_failure(self, tmp_path):
        lib = self._lib(tmp_path)
        code = "def broken(): pass\n"
        test = "assert broken() == 999"
        skill = lib.propose("broken", "broken skill", code, test_code=test)
        ok, msg = lib.test_and_integrate(skill.id, allow_mutation=True)
        assert ok is False

    def test_call_executes_function(self, tmp_path):
        lib = self._lib(tmp_path)
        code = "def double(n):\n    return n * 2\n"
        skill = lib.propose("double", "doubles a number", code, test_code="assert double(3)==6")
        lib.test_and_integrate(skill.id, allow_mutation=True)
        result = lib.call("double", n=5)
        assert result == 10

    def test_context_for_llm(self, tmp_path):
        lib = self._lib(tmp_path)
        code = "def greet(name):\n    return f'Hello {name}'\n"
        skill = lib.propose("greet", "greets by name", code)
        skill.status = "active"
        lib._save()
        ctx = lib.context_for_llm()
        assert "greet" in ctx

    def test_summary(self, tmp_path):
        lib = self._lib(tmp_path)
        s = lib.propose("ping", "pings", "def ping(): return 'pong'")
        s.status = "active"
        lib._save()
        summary = lib.summary()
        assert summary["total"] >= 1


# ══════════════════════════════════════════════════════════════════════════════
# AutonomousLoop
# ══════════════════════════════════════════════════════════════════════════════

class TestAutonomousLoop:
    def _loop_mod(self, tmp_path):
        cfg = _mock_config(tmp_path)
        gm_mock = MagicMock()
        gm_mock.top.return_value = None
        bs_mock = MagicMock()
        bs_mock.context_for.return_value = ""
        sl_mock = MagicMock()
        sl_mock.search.return_value = []
        sl_mock.context_for_llm.return_value = ""

        mocks = {
            "config": cfg,
            "goal_manager": MagicMock(get_manager=lambda: gm_mock),
            "belief_store": MagicMock(get_store=lambda: bs_mock),
            "skill_library": MagicMock(get_library=lambda: sl_mock),
            "tools.web_search": MagicMock(summarize_search=lambda q, **kw: ""),
        }
        with patch.dict(sys.modules, mocks):
            import importlib
            import autonomous_loop as al_mod
            importlib.reload(al_mod)
        return al_mod, gm_mock, bs_mock, sl_mock

    def test_idle_loop_stops_after_threshold(self, tmp_path):
        mod, gm_mock, *_ = self._loop_mod(tmp_path)
        gm_mock.top.return_value = None
        events = []
        loop = mod.AutonomousLoop(
            llm_call=lambda p: "[]",
            tick_interval=0.01,
            idle_stop_after=3,
            on_event=lambda t, d: events.append(t),
        )
        t = loop.start(daemon=True)
        t.join(timeout=2.0)
        assert not loop.is_alive()
        assert "loop_stopped" in events

    def test_goal_decompose_called(self, tmp_path):
        mod, gm_mock, *_ = self._loop_mod(tmp_path)

        goal = MagicMock()
        goal.id = "g1"
        goal.description = "Do something"
        goal.priority = 5
        goal.status = "pending"
        goal.steps = []
        goal.current_step = 0
        goal.result = ""
        goal.next_step.return_value = None

        call_n = [0]
        def top_side():
            call_n[0] += 1
            return goal if call_n[0] == 1 else None

        gm_mock.top.side_effect = top_side

        events = []
        loop = mod.AutonomousLoop(
            llm_call=lambda p: '["step one", "step two"]',
            tick_interval=0.01,
            idle_stop_after=2,
            on_event=lambda t, d: events.append(t),
        )
        t = loop.start(daemon=True)
        t.join(timeout=2.0)
        assert "goal_picked" in events

    def test_start_loop_requires_explicit_allow(self, tmp_path):
        mod, *_ = self._loop_mod(tmp_path)

        try:
            mod.start_loop(lambda p: "[]", tick_interval=0.01)
        except PermissionError as exc:
            assert "allow_autonomous" in str(exc)
        else:
            raise AssertionError("start_loop should require explicit authorization")

    def test_loop_does_not_acquire_skill_from_engine_error(self, tmp_path, monkeypatch):
        mod, *_ = self._loop_mod(tmp_path)
        called = []
        monkeypatch.setitem(sys.modules, "skill_acquisition", MagicMock(scan_and_acquire=lambda *a, **k: called.append(a)))
        events = []
        loop = mod.AutonomousLoop(lambda p: "[]", on_event=lambda t, d: events.append(t))

        loop._maybe_acquire("[loop_llm_unavailable] claude limit")

        assert called == []
        assert "skill_acquisition_skipped" in events
