from core import failover_simulator, session_kernel


def test_failover_simulation_preserves_resume_context(tmp_path):
    session_kernel.SESSION_FILE = tmp_path / "kernel.jsonl"
    session_kernel.checkpoint(
        "continuer Athos",
        decisions=["same identity"],
        tasks=["resume with next engine"],
        files=["core/athos_engine.py"],
    )

    result = failover_simulator.simulate({
        "current": "chatgpt_plus",
        "available": ["chatgpt_plus", "claude_code", "ollama"],
        "request": "continue le travail",
    })

    assert result["ok"] is True
    assert result["no_api_calls"] is True
    assert result["current"] == "chatgpt_plus"
    assert result["next"] == "claude_code"
    assert result["context_preserved"] is True
    assert result["resume_pack"]["identity"] == "A.T.H.O.S."
    assert result["resume_pack"]["request"] == "continue le travail"
    assert result["resume_pack"]["checkpoint_goal"] == "continuer Athos"
    assert result["resume_pack"]["context_hash"]


def test_failover_simulation_respects_configured_order(monkeypatch):
    monkeypatch.setattr(failover_simulator.config, "ATHOS_ENGINE_ORDER", "claude_code,chatgpt_plus,ollama")

    result = failover_simulator.simulate({
        "current": "claude_code",
        "available": ["chatgpt_plus", "claude_code", "ollama"],
    })

    assert result["available"] == ["claude_code", "chatgpt_plus", "ollama"]
    assert result["next"] == "chatgpt_plus"
