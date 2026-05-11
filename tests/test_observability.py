from core import observability


def test_process_snapshot_contains_visible_runtime_sections(monkeypatch):
    monkeypatch.setattr(observability, "_run", lambda *a, **k: "")
    monkeypatch.setattr(observability, "_shell", lambda *a, **k: "")
    monkeypatch.setattr(observability.memory_status, "status", lambda: {"missing": [], "ok": True})
    monkeypatch.setattr(observability.local_capability, "scan", lambda: {"available_tool_count": 2, "network_required": False})
    monkeypatch.setattr(observability.capability_graph, "compact_summary", lambda: {
        "summary": {"nodes": 4, "edges": 5, "interconnection_score": 0.7},
        "principle": "test",
        "reuse_policy": [],
    })

    snap = observability.process_snapshot([{"pid": 123, "running": True}])

    assert {"git", "drive", "memory", "local_capability", "capability_graph", "failover", "server_runtime", "ports", "launchd", "logs", "agent_processes", "summary"} <= set(snap)
    assert snap["agent_processes"] == [{"pid": 123, "running": True}]
    assert snap["summary"]["agent_processes"] == 1
    assert snap["summary"]["local_tools"] == 2
    assert snap["summary"]["local_capability_network_required"] is False
    assert snap["summary"]["capability_graph_nodes"] == 4
    assert snap["summary"]["capability_graph_score"] == 0.7
    assert snap["server_runtime"]["pid"]
    assert snap["server_runtime"]["port"] == observability.config.ATHOS_PORT


def test_listening_ports_preserves_address_and_stops_only_safe_services(monkeypatch):
    output = "\n".join([
        "COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME",
        "Python  123 clem    5u  IPv4 0      0t0  TCP 127.0.0.1:7474 (LISTEN)",
        "rapportd 488 clem    5u  IPv4 0      0t0  TCP *:49152 (LISTEN)",
        "Python  123 clem    6u  IPv4 0      0t0  TCP 127.0.0.1:7474 (LISTEN)",
    ])
    monkeypatch.setattr(observability, "_shell", lambda *a, **k: output)

    rows = observability.listening_ports()

    assert len(rows) == 2
    assert rows[0]["name"] == "TCP 127.0.0.1:7474 (LISTEN)"
    assert rows[0]["reason"] == "Athos voice/server local"
    assert rows[0]["stoppable"] is True
    assert rows[1]["name"] == "TCP *:49152 (LISTEN)"
    assert rows[1]["stoppable"] is False


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


def test_stop_observed_pid_refuses_non_stoppable_listed_pid(monkeypatch):
    monkeypatch.setattr(observability, "listening_ports", lambda: [{"pid": 111, "stoppable": False}])

    assert "non stoppable" in observability.stop_observed_pid(111)
