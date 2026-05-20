import importlib


def _queue(tmp_path, monkeypatch):
    import core.task_queue as task_queue

    importlib.reload(task_queue)
    task_queue.TASK_QUEUE_FILE = tmp_path / "athos_task_queue.json"
    task_queue.session_kernel.SESSION_FILE = tmp_path / "athos_session_kernel.jsonl"
    return task_queue


def test_task_queue_lifecycle_persists_and_summarizes(tmp_path, monkeypatch):
    queue = _queue(tmp_path, monkeypatch)

    created = queue.create(
        "Finish Room objective",
        content="finissez ce mini objectif",
        task_id="room-a",
        source="room",
        kind="room_auto_work",
    )

    assert created["status"] == "queued"
    assert created["task_id"] == "room-a"
    assert queue.summary()["counts"]["queued"] == 1

    running = queue.start(task_id="room-a")
    assert running["ok"] is True
    assert running["task"]["status"] == "running"
    assert running["task"]["started_at"]

    blocked = queue.block(task_id="room-a", reason="claude invalid_credentials")
    assert blocked["task"]["status"] == "blocked"
    assert blocked["task"]["blocked_reason"] == "claude invalid_credentials"

    retried = queue.retry(task_id="room-a")
    assert retried["task"]["status"] == "queued"
    assert retried["task"]["retry_count"] == 1
    assert retried["task"]["blocked_reason"] == ""

    queue.start(task_id="room-a")
    completed = queue.complete(task_id="room-a", result="tests passed")
    assert completed["task"]["status"] == "completed"
    assert completed["task"]["result"] == "tests passed"
    assert queue.summary()["counts"]["completed"] == 1


def test_task_queue_api_helpers_filter_and_cancel(tmp_path, monkeypatch):
    queue = _queue(tmp_path, monkeypatch)
    first = queue.create("First", task_id="first")
    queue.create("Second", task_id="second")
    queue.pause(item_id=first["id"], reason="manual pause")
    queue.cancel(task_id="second", reason="not needed")

    paused = queue.list_tasks(status="paused")
    assert [item["task_id"] for item in paused] == ["first"]
    assert queue.get(item_id=first["id"])["status"] == "paused"
    assert queue.summary()["counts"]["cancelled"] == 1


def test_task_queue_rejects_illegal_terminal_transitions(tmp_path, monkeypatch):
    queue = _queue(tmp_path, monkeypatch)
    queue.create("Terminal", task_id="terminal")
    queue.start(task_id="terminal")
    queue.complete(task_id="terminal", result="done")

    retry = queue.retry(task_id="terminal")
    assert retry["ok"] is False
    assert retry["error"] == "illegal_transition"

    pause = queue.pause(task_id="terminal")
    assert pause["ok"] is False
    assert pause["error"] == "illegal_transition"
    assert queue.get(task_id="terminal")["status"] == "completed"


def test_task_queue_requires_start_before_complete(tmp_path, monkeypatch):
    queue = _queue(tmp_path, monkeypatch)
    queue.create("Queued", task_id="queued")

    result = queue.complete(task_id="queued", result="too early")

    assert result["ok"] is False
    assert result["error"] == "illegal_transition"
    assert result["from"] == "queued"
    assert result["to"] == "completed"


def test_task_queue_sweeps_stale_running_tasks(tmp_path, monkeypatch):
    queue = _queue(tmp_path, monkeypatch)
    queue.create("Stale", task_id="stale")
    queue.start(task_id="stale")

    items = queue._read_unlocked()
    items[0]["started_at"] = "2020-01-01T00:00:00+00:00"
    queue._write_unlocked(items)

    swept = queue.sweep_stale(stale_after_seconds=1)

    assert swept["ok"] is True
    assert swept["changed"] == 1
    task = queue.get(task_id="stale")
    assert task["status"] == "blocked"
    assert task["blocked_reason"] == "stale_timeout"
    assert queue.summary()["counts"]["blocked"] == 1
