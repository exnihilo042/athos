from core import observability


def test_process_snapshot_contains_visible_runtime_sections(monkeypatch):
    monkeypatch.setattr(observability, "_run", lambda *a, **k: "")
    monkeypatch.setattr(observability, "_shell", lambda *a, **k: "")

    snap = observability.process_snapshot([{"pid": 123, "running": True}])

    assert {"git", "drive", "ports", "launchd", "logs", "agent_processes", "summary"} <= set(snap)
    assert snap["agent_processes"] == [{"pid": 123, "running": True}]
    assert snap["summary"]["agent_processes"] == 1


def test_stop_observed_pid_refuses_unlisted_pid(monkeypatch):
    monkeypatch.setattr(observability, "listening_ports", lambda: [{"pid": 111, "stoppable": True}])

    assert "non stoppable" in observability.stop_observed_pid(222)
