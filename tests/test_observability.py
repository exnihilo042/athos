from core import observability


def test_process_snapshot_contains_visible_runtime_sections(monkeypatch):
    monkeypatch.setattr(observability, "_run", lambda *a, **k: "")
    monkeypatch.setattr(observability, "_shell", lambda *a, **k: "")
    monkeypatch.setattr(observability.memory_status, "status", lambda: {"missing": [], "ok": True})
    monkeypatch.setattr(observability.local_capability, "scan", lambda: {"available_tool_count": 2, "network_required": False})

    snap = observability.process_snapshot([{"pid": 123, "running": True}])

    assert {"git", "drive", "memory", "local_capability", "failover", "server_runtime", "ports", "launchd", "logs", "agent_processes", "summary"} <= set(snap)
    assert snap["agent_processes"] == [{"pid": 123, "running": True}]
    assert snap["summary"]["agent_processes"] == 1
    assert snap["summary"]["local_tools"] == 2
    assert snap["summary"]["local_capability_network_required"] is False
    assert snap["server_runtime"]["pid"]
    assert snap["server_runtime"]["port"] == observability.config.ATHOS_PORT


def test_recent_failover_events_reads_session_actions(tmp_path, monkeypatch):
    monkeypatch.setattr(observability.session_kernel, "SESSION_FILE", tmp_path / "kernel.jsonl")
    observability.session_kernel.record_action(
        "failover_simulation",
        "chatgpt_plus→claude_code",
        "simulated_limit",
        engine="athos_kernel",
        meta={"context_hash": "abc123"},
    )

    rows = observability.recent_failover_events()

    assert rows[-1]["label"] == "chatgpt_plus→claude_code"
    assert rows[-1]["context_hash"] == "abc123"


def test_stop_observed_pid_refuses_unlisted_pid(monkeypatch):
    monkeypatch.setattr(observability, "listening_ports", lambda: [{"pid": 111, "stoppable": True}])

    assert "non stoppable" in observability.stop_observed_pid(222)
