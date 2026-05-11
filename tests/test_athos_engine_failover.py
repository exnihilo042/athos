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
