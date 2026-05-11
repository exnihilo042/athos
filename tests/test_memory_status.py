from core import memory_status


def test_memory_status_reports_canonical_files(tmp_path, monkeypatch):
    monkeypatch.setattr(memory_status.config, "DRIVE", tmp_path)
    monkeypatch.setattr(memory_status.session_kernel, "SESSION_FILE", tmp_path / "athos_session_kernel.jsonl")
    (tmp_path / "athos_identity.mem").write_text("§id:athos\n", "utf-8")

    result = memory_status.status()

    assert result["root"] == str(tmp_path)
    assert result["exists"] is True
    assert result["canonical_files"][0]["name"] == "athos_identity.mem"
    assert result["canonical_files"][0]["last_line"] == "§id:athos"
    assert "athos_capabilities.mem" in result["missing"]
    assert "athos_session_summary.mem" in result["missing"]
    assert result["ok"] is False
