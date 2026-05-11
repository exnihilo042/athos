import io
import subprocess
import sys
from pathlib import Path

CORE_DIR = Path(__file__).parent.parent / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from core.athos_engine import AthosEngine


class FakeMem:
    def __init__(self):
        self.history = []
        self.exchanges = []

    def context(self):
        return "ctx"

    def get_history(self):
        return list(self.history)

    def push(self, role, content):
        self.history.append({"role": role, "content": content})

    def save_exchange(self, user, reply):
        self.exchanges.append((user, reply))

    def log_exchange(self, user, reply, engine):
        self.engine = engine


class FakeRouter:
    current = "chatgpt_plus"
    degraded = False

    def available(self):
        return ["chatgpt_plus", "claude_code"]

    def best_for(self, msg):
        return self.current

    def degrade(self, reason):
        self.current = "claude_code"
        self.degraded = True
        return self.current


def test_engine_failover_keeps_same_message_and_records_claude(monkeypatch, tmp_path):
    from core import session_kernel
    session_kernel.SESSION_FILE = tmp_path / "kernel.jsonl"
    events = []
    engine = AthosEngine(FakeMem(), FakeRouter(), events.append, lambda: (lambda *_: True))

    monkeypatch.setattr(engine, "_chatgpt_plus", lambda msg: (_ for _ in ()).throw(RuntimeError("limit")))
    monkeypatch.setattr(engine, "_claude_code", lambda msg: f"repris:{msg}")

    reply = engine.respond("continue le travail")

    assert reply == "repris:continue le travail"
    assert any(e.get("action") == "failover" for e in events)
    assert session_kernel.latest_checkpoint()["tasks"] == ["reprendre la même demande avec le même contexte"]


def test_local_status_reply_emits_sse_text_and_records(monkeypatch):
    import core.athos_engine as athos_engine

    events = []
    mem = FakeMem()
    engine = AthosEngine(mem, FakeRouter(), events.append, lambda: (lambda *_: True))
    monkeypatch.setattr(athos_engine, "matches_self_knowledge_request", lambda msg: True)
    monkeypatch.setattr(athos_engine, "wants_compact_status", lambda msg: True)
    monkeypatch.setattr(athos_engine, "status_report", lambda compact=False: "A.T.H.O.S. compact")

    reply = engine.respond("où en est Athos ? statut court")

    assert reply == "A.T.H.O.S. compact"
    assert {"t": "A.T.H.O.S. compact"} in events
    assert mem.exchanges == [("où en est Athos ? statut court", "A.T.H.O.S. compact")]


def test_chatgpt_plus_cli_closes_stdin(monkeypatch):
    import core.athos_engine as athos_engine

    events = []
    engine = AthosEngine(FakeMem(), FakeRouter(), events.append, lambda: (lambda *_: True))
    monkeypatch.setattr(athos_engine.engine_router, "chatgpt_plus_path", lambda: "/usr/local/bin/codex")
    seen = {}

    def fake_run(*args, **kwargs):
        seen.update(kwargs)
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(athos_engine.subprocess, "run", fake_run)

    assert engine._chatgpt_plus("hello") == "ok"
    assert seen["stdin"] is subprocess.DEVNULL


def test_claude_code_cli_closes_stdin(monkeypatch):
    import core.athos_engine as athos_engine

    events = []
    engine = AthosEngine(FakeMem(), FakeRouter(), events.append, lambda: (lambda *_: True))
    seen = {}

    class FakeProc:
        def __init__(self):
            self.stdout = io.StringIO("ok")
            self.stderr = io.StringIO("")
            self.returncode = 0

        def wait(self, timeout=None):
            return 0

    def fake_popen(*args, **kwargs):
        seen.update(kwargs)
        return FakeProc()

    monkeypatch.setattr(athos_engine.subprocess, "Popen", fake_popen)

    assert engine._claude_code("hello") == "ok"
    assert seen["stdin"] is subprocess.DEVNULL
