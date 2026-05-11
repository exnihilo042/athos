import importlib


def test_write_file_allows_repo_root(tmp_path, monkeypatch):
    monkeypatch.setenv("ATHOS_PATH", str(tmp_path / "repo"))
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path / "drive"))
    import core.config as config
    importlib.reload(config)
    import core.agent as agent
    importlib.reload(agent)

    target = config.ATHOS_PATH / "note.txt"
    result = agent.tool_write_file(str(target), "ok")

    assert "Fichier écrit" in result
    assert target.read_text() == "ok"


def test_write_file_blocks_outside_allowed_roots(tmp_path, monkeypatch):
    monkeypatch.setenv("ATHOS_PATH", str(tmp_path / "repo"))
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path / "drive"))
    import core.config as config
    importlib.reload(config)
    import core.agent as agent
    importlib.reload(agent)

    target = tmp_path / "outside.txt"
    result = agent.tool_write_file(str(target), "nope")

    assert "REFUSÉ" in result
    assert not target.exists()


def test_write_file_override_allows_any_path(tmp_path, monkeypatch):
    monkeypatch.setenv("ATHOS_PATH", str(tmp_path / "repo"))
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path / "drive"))
    monkeypatch.setenv("ATHOS_ALLOW_ANY_WRITE", "true")
    import core.config as config
    importlib.reload(config)
    import core.agent as agent
    importlib.reload(agent)

    target = tmp_path / "outside.txt"
    result = agent.tool_write_file(str(target), "ok")

    assert "Fichier écrit" in result
    assert target.read_text() == "ok"
