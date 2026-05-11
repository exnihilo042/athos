"""Tests for skill_acquisition module."""
from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

CORE_DIR = Path(__file__).parent.parent / "core"
REPO_DIR = Path(__file__).parent.parent
for p in (str(REPO_DIR), str(CORE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)


def _load_mod(tmp_path):
    import importlib, types
    # Minimal config mock
    cfg = types.ModuleType("config")
    cfg.DRIVE = tmp_path
    cfg.ATHOS_PATH = tmp_path
    (tmp_path / "core" / "skills").mkdir(parents=True, exist_ok=True)

    # Reload dependencies with tmp config
    with patch.dict(sys.modules, {"config": cfg}):
        import importlib as il
        import skill_library as sl_mod
        il.reload(sl_mod)
        sl_mod.SKILLS_DIR = tmp_path / "core" / "skills"
        sl_mod.SKILLS_MANIFEST = sl_mod.SKILLS_DIR / "manifest.json"
        sl_mod.SKILLS_DIR.mkdir(parents=True, exist_ok=True)

        import belief_store as bs_mod
        il.reload(bs_mod)

        import skill_acquisition as sa_mod
        il.reload(sa_mod)
        # Point the module at reloaded singletons
        sa_mod.get_library = sl_mod.SkillLibrary
        sa_mod.get_store = bs_mod.BeliefStore

    return sa_mod, sl_mod.SkillLibrary(), bs_mod.BeliefStore()


class TestDetectGap:
    def _mod(self, tmp_path):
        mod, *_ = _load_mod(tmp_path)
        return mod

    def test_detects_gap_signal(self, tmp_path):
        mod = self._mod(tmp_path)
        result = mod.detect_gap("Désolé, je ne sais pas comment envoyer des emails.")
        assert result is not None
        assert len(result) > 5

    def test_no_gap_signal(self, tmp_path):
        mod = self._mod(tmp_path)
        result = mod.detect_gap("La météo est ensoleillée aujourd'hui.")
        assert result is None

    def test_multiple_signals(self, tmp_path):
        mod = self._mod(tmp_path)
        result = mod.detect_gap("Je suis incapable de lire les fichiers PDF.")
        assert result is not None


class TestExtractPython:
    def _mod(self, tmp_path):
        import importlib
        import skill_acquisition as sa
        importlib.reload(sa)
        return sa

    def test_extracts_fenced_block(self, tmp_path):
        mod = self._mod(tmp_path)
        raw = 'Voici le code:\n```python\ndef hello():\n    return "hi"\n```'
        code = mod._extract_python(raw)
        assert "def hello" in code

    def test_extracts_unfenced_def(self, tmp_path):
        mod = self._mod(tmp_path)
        raw = 'def my_fn(x):\n    return x * 2'
        code = mod._extract_python(raw)
        assert "def my_fn" in code

    def test_empty_on_no_code(self, tmp_path):
        mod = self._mod(tmp_path)
        code = mod._extract_python("Voici une réponse sans code.")
        assert code == ""


class TestGenerateSkill:
    def test_parses_valid_json_response(self, tmp_path):
        import importlib
        import skill_acquisition as sa
        importlib.reload(sa)

        llm_response = '''{
  "name": "send_email",
  "description": "envoie un email SMTP",
  "code": "def send_email(to, subject, body):\\n    return True",
  "test_code": "assert send_email('a@b.com', 'test', 'body') == True"
}'''
        name, code, test = sa.generate_skill("send email", lambda p: llm_response)
        assert name == "send_email"
        assert "def send_email" in code
        assert "assert" in test

    def test_handles_malformed_response(self, tmp_path):
        import importlib
        import skill_acquisition as sa
        importlib.reload(sa)
        name, code, test = sa.generate_skill("something", lambda p: "not json at all")
        assert name == ""
        assert code == ""


class TestAcquire:
    def test_full_pipeline_success(self, tmp_path):
        import importlib, types
        cfg = types.ModuleType("config")
        cfg.DRIVE = tmp_path
        cfg.ATHOS_PATH = tmp_path
        (tmp_path / "core" / "skills").mkdir(parents=True, exist_ok=True)

        with patch.dict(sys.modules, {"config": cfg}):
            import skill_library as sl_mod
            importlib.reload(sl_mod)
            sl_mod.SKILLS_DIR = tmp_path / "core" / "skills"
            sl_mod.SKILLS_MANIFEST = sl_mod.SKILLS_DIR / "manifest.json"
            sl_mod.SKILLS_DIR.mkdir(parents=True, exist_ok=True)

            import belief_store as bs_mod
            importlib.reload(bs_mod)

            import skill_acquisition as sa_mod
            importlib.reload(sa_mod)

        lib = sl_mod.SkillLibrary()
        store = bs_mod.BeliefStore()

        llm_resp = '''{
  "name": "reverse_string",
  "description": "inverse une chaine",
  "code": "def reverse_string(s):\\n    return s[::-1]\\n",
  "test_code": "assert reverse_string('abc') == 'cba'"
}'''

        with (
            patch.object(sa_mod, "get_library", return_value=lib),
            patch.object(sa_mod, "get_store", return_value=store),
            patch.object(sa_mod, "search_github", return_value=[]),
            patch.object(sa_mod, "summarize_search", return_value=""),
        ):
            skill = sa_mod.acquire("reverse a string", lambda p: llm_resp, allow_mutation=True)

        assert skill is not None
        assert skill.name == "reverse_string"
        assert skill.status == "active"

    def test_acquire_proposes_skill_without_mutation_by_default(self, tmp_path):
        import importlib, types
        cfg = types.ModuleType("config")
        cfg.DRIVE = tmp_path
        cfg.ATHOS_PATH = tmp_path
        (tmp_path / "core" / "skills").mkdir(parents=True, exist_ok=True)

        with patch.dict(sys.modules, {"config": cfg}):
            import skill_library as sl_mod
            importlib.reload(sl_mod)
            sl_mod.SKILLS_DIR = tmp_path / "core" / "skills"
            sl_mod.SKILLS_MANIFEST = sl_mod.SKILLS_DIR / "manifest.json"
            sl_mod.SKILLS_DIR.mkdir(parents=True, exist_ok=True)
            import belief_store as bs_mod
            importlib.reload(bs_mod)
            import skill_acquisition as sa_mod
            importlib.reload(sa_mod)

        lib = sl_mod.SkillLibrary()
        store = bs_mod.BeliefStore()
        llm_resp = '{"name":"safe_plan","description":"plan only","code":"def safe_plan():\\n    return True","test_code":"assert safe_plan() == True"}'

        with (
            patch.object(sa_mod, "get_library", return_value=lib),
            patch.object(sa_mod, "get_store", return_value=store),
            patch.object(sa_mod, "search_github", return_value=[]),
            patch.object(sa_mod, "summarize_search", return_value=""),
        ):
            skill = sa_mod.acquire("make a plan", lambda p: llm_resp)

        assert skill is not None
        assert skill.status == "pending"
        assert not skill.file_path().exists()

    def test_returns_none_on_bad_code(self, tmp_path):
        import importlib, types
        cfg = types.ModuleType("config")
        cfg.DRIVE = tmp_path
        cfg.ATHOS_PATH = tmp_path
        (tmp_path / "core" / "skills").mkdir(parents=True, exist_ok=True)

        with patch.dict(sys.modules, {"config": cfg}):
            import skill_library as sl_mod
            importlib.reload(sl_mod)
            sl_mod.SKILLS_DIR = tmp_path / "core" / "skills"
            sl_mod.SKILLS_MANIFEST = sl_mod.SKILLS_DIR / "manifest.json"
            sl_mod.SKILLS_DIR.mkdir(parents=True, exist_ok=True)

            import belief_store as bs_mod
            importlib.reload(bs_mod)

            import skill_acquisition as sa_mod
            importlib.reload(sa_mod)

        lib = sl_mod.SkillLibrary()
        store = bs_mod.BeliefStore()

        with (
            patch.object(sa_mod, "get_library", return_value=lib),
            patch.object(sa_mod, "get_store", return_value=store),
            patch.object(sa_mod, "search_github", return_value=[]),
            patch.object(sa_mod, "summarize_search", return_value=""),
        ):
            # LLM returns broken code that will fail the test
            skill = sa_mod.acquire(
                "do something",
                lambda p: '{"name":"bad","description":"x","code":"def bad(): pass","test_code":"assert bad() == 999"}',
                max_attempts=1,
                allow_mutation=True,
            )

        assert skill is None


class TestScanAndAcquire:
    def test_no_gap_returns_none(self, tmp_path):
        import importlib
        import skill_acquisition as sa
        importlib.reload(sa)
        result = sa.scan_and_acquire("La réponse est 42.", lambda p: "")
        assert result is None

    def test_gap_triggers_acquire(self, tmp_path):
        import importlib, types
        cfg = types.ModuleType("config")
        cfg.DRIVE = tmp_path
        cfg.ATHOS_PATH = tmp_path
        (tmp_path / "core" / "skills").mkdir(parents=True, exist_ok=True)

        with patch.dict(sys.modules, {"config": cfg}):
            import skill_library as sl_mod
            importlib.reload(sl_mod)
            sl_mod.SKILLS_DIR = tmp_path / "core" / "skills"
            sl_mod.SKILLS_MANIFEST = sl_mod.SKILLS_DIR / "manifest.json"
            sl_mod.SKILLS_DIR.mkdir(parents=True, exist_ok=True)

            import belief_store as bs_mod
            importlib.reload(bs_mod)

            import skill_acquisition as sa_mod
            importlib.reload(sa_mod)

        lib = sl_mod.SkillLibrary()
        store = bs_mod.BeliefStore()

        acquired = []

        def _fake_acquire(gap, llm, **kw):
            acquired.append(gap)
            return None  # don't need real skill for this test

        with (
            patch.object(sa_mod, "get_library", return_value=lib),
            patch.object(sa_mod, "get_store", return_value=store),
            patch.object(sa_mod, "acquire", side_effect=_fake_acquire),
        ):
            sa_mod.scan_and_acquire("Je ne peux pas accéder aux fichiers PDF.", lambda p: "")

        assert len(acquired) == 1
