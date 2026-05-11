import importlib


def _reload_for_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path))
    import core.config as config
    importlib.reload(config)
    import core.session_kernel as session_kernel
    importlib.reload(session_kernel)
    import core.sync_manager as sync_manager
    importlib.reload(sync_manager)
    import core.session_compactor as session_compactor
    importlib.reload(session_compactor)
    import core.attach_protocol as attach_protocol
    importlib.reload(attach_protocol)
    session_kernel.SESSION_FILE = tmp_path / "athos_session_kernel.jsonl"
    sync_manager.OUTBOX_FILE = tmp_path / "athos_sync_outbox.jsonl"
    session_compactor.SUMMARY_FILE = tmp_path / "athos_session_summary.mem"
    return session_kernel, attach_protocol


def test_attach_engine_returns_context_and_records_event(tmp_path, monkeypatch):
    session_kernel, attach_protocol = _reload_for_tmp(tmp_path, monkeypatch)
    (tmp_path / "athos_identity.mem").write_text("§id:athos|identity:A.T.H.O.S.\n", "utf-8")
    (tmp_path / "athos_capabilities.mem").write_text("§done:today|thing:attach_pack\n", "utf-8")
    (tmp_path / "athos_projects.mem").write_text("§project:athos|status:active\n", "utf-8")
    (tmp_path / "athos_session_summary.mem").write_text("§session_summary:updated:now\n", "utf-8")
    (tmp_path / "athos_conv.mem").write_text("§conv:now|u:test|a:ok\n", "utf-8")

    response = attach_protocol.attach_engine({"engine": "codex", "scope": "repo_work"})

    assert response["ok"] is True
    assert response["identity"] == "A.T.H.O.S."
    assert response["attach_id"]
    assert response["must_report"] is True
    assert response["cost_policy"]["paid_api_enabled"] is False
    assert response["drive_memory"]["files"]["athos_identity.mem"][0].startswith("§id:")
    assert "athos_capabilities.mem" in response["drive_memory"]["files"]
    assert "athos_projects.mem" in response["drive_memory"]["files"]
    assert "athos_session_summary.mem" in response["drive_memory"]["files"]
    assert "athos_conv.mem" in response["drive_memory"]["files"]
    assert session_kernel.status()["attaches"] == 1
    assert "§attach:" in session_kernel.context_pack()


def test_drive_memory_pack_keeps_later_files_when_identity_is_large(tmp_path, monkeypatch):
    _, attach_protocol = _reload_for_tmp(tmp_path, monkeypatch)
    large_identity = "\n".join(f"§id:{i}|{'x' * 120}" for i in range(80))
    (tmp_path / "athos_identity.mem").write_text(large_identity + "\n", "utf-8")
    (tmp_path / "athos_projects.mem").write_text("§project:athos|status:active\n", "utf-8")
    (tmp_path / "athos_conv.mem").write_text("§conv:now|u:last|a:ok\n", "utf-8")

    response = attach_protocol.context_for_attach({"memory_chars": 1_200})

    assert "athos_identity.mem" in response["drive_memory"]["files"]
    assert "athos_projects.mem" in response["drive_memory"]["files"]
    assert "athos_conv.mem" in response["drive_memory"]["files"]


def test_delegate_named_protocol_and_report_are_traced(tmp_path, monkeypatch):
    session_kernel, attach_protocol = _reload_for_tmp(tmp_path, monkeypatch)
    attach = attach_protocol.attach_engine({"engine": "claude_code"})

    delegated = attach_protocol.delegate({
        "attach_id": attach["attach_id"],
        "engine": "claude_code",
        "request": "ATHOS_STATUS",
    })
    reported = attach_protocol.report({
        "attach_id": attach["attach_id"],
        "engine": "claude_code",
        "summary": "status delivered",
        "status": "completed",
    })

    assert delegated["decision"] == "named_protocol:ATHOS_STATUS"
    assert delegated["requires_confirmation"] is False
    assert reported["warnings"] == []
    status = session_kernel.status()
    assert status["delegates"] == 1
    assert status["reports"] == 1


def test_report_without_attach_id_is_readable_but_warns(tmp_path, monkeypatch):
    session_kernel, attach_protocol = _reload_for_tmp(tmp_path, monkeypatch)

    response = attach_protocol.report({"engine": "grok", "summary": "offline cache only"})

    assert response["ok"] is True
    assert response["warnings"]
    assert session_kernel.status()["reports"] == 1


def test_checkpoint_report_writes_session_checkpoint(tmp_path, monkeypatch):
    session_kernel, attach_protocol = _reload_for_tmp(tmp_path, monkeypatch)
    attach = attach_protocol.attach_engine({"engine": "codex"})

    response = attach_protocol.report({
        "attach_id": attach["attach_id"],
        "engine": "codex",
        "event": "checkpoint",
        "goal": "publish Athos checkpoint",
        "summary": "done",
        "tasks": ["tests passed"],
        "files": ["core/attach_protocol.py"],
    })

    assert response["checkpoint"]["goal"] == "publish Athos checkpoint"
    assert response["session_summary"]["written"] is True
    assert session_kernel.latest_checkpoint()["goal"] == "publish Athos checkpoint"
    assert (tmp_path / "athos_session_summary.mem").exists()
