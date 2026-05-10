import core.memory_manager as mm


def test_read_write_append_and_session(tmp_path):
    mm.DRIVE = tmp_path
    mm.TEMP = tmp_path / "temp"
    mm.LOGS = tmp_path / "logs"

    mm.write("test.mem", "hello")
    assert mm.read("test.mem") == "hello"

    mm.append("test.mem", "world")
    assert "world" in mm.read("test.mem")

    mm.write_session("session1")
    assert "session1" in mm.read_session()

    mm.clear_session()
    assert mm.read_session() == ""

    mm.log_today("§test:action")
    today_file = mm.LOGS / f"{mm.datetime.now().strftime('%Y-%m-%d')}.mem"
    assert today_file.exists()
    assert "§test:action" in today_file.read_text()


def test_read_all_core_returns_required_keys(tmp_path):
    mm.DRIVE = tmp_path
    result = mm.read_all_core()
    assert set(result.keys()) == {"id", "behavior", "projects", "feedback"}
