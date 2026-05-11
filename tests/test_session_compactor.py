from core import session_compactor, session_kernel


def test_build_summary_contains_checkpoint_exchange_action_and_report(tmp_path, monkeypatch):
    monkeypatch.setattr(session_compactor, "SUMMARY_FILE", tmp_path / "athos_session_summary.mem")
    session_kernel.SESSION_FILE = tmp_path / "kernel.jsonl"
    session_kernel.checkpoint("continue Athos", tasks=["test"])
    session_kernel.record_exchange("hello", "bonjour", "athos_kernel")
    session_kernel.record_action("failover_simulation", "chatgpt→claude", "ok", engine="athos_kernel")
    session_kernel.record_report("a1", "codex", "done", status="completed")

    summary = session_compactor.build_summary()

    assert "§checkpoint:goal:continue Athos" in summary["text"]
    assert "§exchange:" in summary["text"]
    assert "§action:" in summary["text"]
    assert "§report:" in summary["text"]


def test_write_summary_is_non_destructive(tmp_path, monkeypatch):
    monkeypatch.setattr(session_compactor, "SUMMARY_FILE", tmp_path / "athos_session_summary.mem")
    session_kernel.SESSION_FILE = tmp_path / "kernel.jsonl"
    session_kernel.record_exchange("u", "a", "engine")

    result = session_compactor.write_summary()

    assert result["written"] is True
    assert (tmp_path / "athos_session_summary.mem").exists()
    assert session_kernel.status()["exchanges"] == 1
    assert session_kernel.status()["summaries"] == 1
