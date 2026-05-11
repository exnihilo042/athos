import importlib


def test_sync_queue_keeps_network_jobs_pending_when_offline(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path))
    import core.config as config
    importlib.reload(config)
    import core.session_kernel as session_kernel
    importlib.reload(session_kernel)
    import core.sync_manager as sync_manager
    importlib.reload(sync_manager)
    session_kernel.SESSION_FILE = tmp_path / "athos_session_kernel.jsonl"
    sync_manager.OUTBOX_FILE = tmp_path / "athos_sync_outbox.jsonl"

    job = sync_manager.queue_job("drive_checkpoint", {"file": "athos_kernel_plan.mem"}, requires_network=True)
    result = sync_manager.run_once(force_network_available=False)

    assert job["status"] == "pending"
    assert result["network_available"] is False
    assert result["status"]["pending"] == 1
    assert result["status"]["recent"][-1]["blocked_reason"] == "network_unavailable"


def test_sync_run_marks_jobs_ready_but_does_not_execute_hidden_network_write(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path))
    import core.config as config
    importlib.reload(config)
    import core.session_kernel as session_kernel
    importlib.reload(session_kernel)
    import core.sync_manager as sync_manager
    importlib.reload(sync_manager)
    session_kernel.SESSION_FILE = tmp_path / "athos_session_kernel.jsonl"
    sync_manager.OUTBOX_FILE = tmp_path / "athos_sync_outbox.jsonl"

    sync_manager.queue_job("github_push", {"branch": "main"}, requires_network=True)
    result = sync_manager.run_once(force_network_available=True)

    assert result["status"]["ready_for_replay"] == 1
    assert result["status"]["recent"][-1]["blocked_reason"] == "explicit_executor_required"
