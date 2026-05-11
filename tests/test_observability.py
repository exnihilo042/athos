from core import observability


def test_process_snapshot_contains_visible_runtime_sections(monkeypatch):
    monkeypatch.setattr(observability, "_run", lambda *a, **k: "")
    monkeypatch.setattr(observability, "_shell", lambda *a, **k: "")

    snap = observability.process_snapshot([{"pid": 123, "running": True}])

    assert {"git", "drive", "ports", "launchd", "logs", "agent_processes", "summary"} <= set(snap)
    assert snap["agent_processes"] == [{"pid": 123, "running": True}]
    assert snap["summary"]["agent_processes"] == 1
