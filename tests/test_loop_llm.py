import importlib
from types import SimpleNamespace


def test_loop_llm_falls_back_to_codex_when_claude_limited(monkeypatch):
    import voice.server as server
    importlib.reload(server)

    monkeypatch.setattr(server.config, "ANTHROPIC_KEY", "")
    monkeypatch.setattr(server.config, "paid_api_allowed", lambda provider="": False)
    monkeypatch.setattr(server.engine_router, "chatgpt_plus_path", lambda: "/fake/codex")

    calls = []

    def fake_run(args, **kwargs):
        calls.append(args[0])
        if args[0] == "claude":
            return SimpleNamespace(returncode=1, stdout="You've hit your limit", stderr="")
        return SimpleNamespace(returncode=0, stdout="OK_LOOP\n", stderr="warnings")

    monkeypatch.setattr(server.subprocess, "run", fake_run)

    assert server._make_loop_llm()("prompt") == "OK_LOOP"
    assert calls == ["claude", "/fake/codex"]


def test_loop_llm_closes_cli_stdin(monkeypatch):
    import voice.server as server
    importlib.reload(server)

    seen = []
    monkeypatch.setattr(server.config, "ANTHROPIC_KEY", "")
    monkeypatch.setattr(server.config, "paid_api_allowed", lambda provider="": False)
    monkeypatch.setattr(server.engine_router, "chatgpt_plus_path", lambda: "/fake/codex")

    def fake_run(args, **kwargs):
        seen.append(kwargs.get("stdin"))
        if args[0] == "claude":
            return SimpleNamespace(returncode=1, stdout="limit", stderr="")
        return SimpleNamespace(returncode=0, stdout="OK_LOOP\n", stderr="")

    monkeypatch.setattr(server.subprocess, "run", fake_run)

    assert server._make_loop_llm()("prompt") == "OK_LOOP"
    assert seen == [server.subprocess.DEVNULL, server.subprocess.DEVNULL]


def test_loop_llm_records_failures_when_all_providers_fail(monkeypatch):
    import voice.server as server
    importlib.reload(server)

    recorded = []
    monkeypatch.setattr(server.config, "ANTHROPIC_KEY", "")
    monkeypatch.setattr(server.config, "paid_api_allowed", lambda provider="": False)
    monkeypatch.setattr(server.engine_router, "chatgpt_plus_path", lambda: "")
    monkeypatch.setattr(
        server.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="limit", stderr=""),
    )
    monkeypatch.setattr(server.session_kernel, "record_action", lambda *a, **k: recorded.append((a, k)))

    reply = server._make_loop_llm()("prompt")

    assert reply.startswith("[loop_llm_unavailable]")
    assert recorded
