import importlib
import json


def test_session_kernel_records_exchange_and_context(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path))
    import core.config as config
    importlib.reload(config)

    import core.session_kernel as kernel
    importlib.reload(kernel)
    kernel.SESSION_FILE = tmp_path / "athos_session_kernel.jsonl"

    event = kernel.record_exchange("bonjour", "salut Clement", "claude")

    assert event["type"] == "exchange"
    assert event["engine"] == "claude"
    assert kernel.status()["exchanges"] == 1
    assert kernel.latest_messages() == [
        {"role": "user", "content": "bonjour"},
        {"role": "assistant", "content": "salut Clement"},
    ]
    assert "§kernel:" in kernel.context_pack()
    assert "bonjour" in kernel.context_pack()

    line = kernel.SESSION_FILE.read_text("utf-8").strip()
    assert json.loads(line)["assistant"] == "salut Clement"


def test_session_kernel_records_actions(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path))
    import core.config as config
    importlib.reload(config)

    import core.session_kernel as kernel
    importlib.reload(kernel)
    kernel.SESSION_FILE = tmp_path / "athos_session_kernel.jsonl"

    kernel.record_action("failover", "claude -> grok", "HTTP 429", engine="claude")

    status = kernel.status()
    assert status["events"] == 1
    assert status["actions"] == 1
    assert "failover" in kernel.context_pack()
