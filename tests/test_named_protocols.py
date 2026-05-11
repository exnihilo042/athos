import importlib


def test_named_protocols_are_listed_and_match_aliases(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path))
    import core.config as config
    importlib.reload(config)
    import core.session_kernel as session_kernel
    importlib.reload(session_kernel)
    import core.named_protocols as named_protocols
    importlib.reload(named_protocols)
    session_kernel.SESSION_FILE = tmp_path / "athos_session_kernel.jsonl"

    names = {item["name"] for item in named_protocols.list_protocols()}

    assert "ATHOS_STATUS" in names
    assert "ATHOS_FAILOVER_TEST" in names
    assert named_protocols.match_protocol("dis moi ce qui tourne") == "ATHOS_STATUS"
    assert named_protocols.match_protocol("test failover") == "ATHOS_FAILOVER_TEST"
    assert named_protocols.match_protocol("ATHOS_SCAN_NETWORK") == "ATHOS_SCAN_NETWORK"


def test_named_protocol_returns_visible_plan(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path))
    import core.config as config
    importlib.reload(config)
    import core.session_kernel as session_kernel
    importlib.reload(session_kernel)
    import core.named_protocols as named_protocols
    importlib.reload(named_protocols)
    session_kernel.SESSION_FILE = tmp_path / "athos_session_kernel.jsonl"

    result = named_protocols.run_protocol("ATHOS_SECURE_DEVICE", {"device": "mac"})

    assert result["ok"] is True
    assert result["protocol"]["requires_approval"] is True
    assert "accord" in result["text"]
    assert session_kernel.status()["actions"] == 1
