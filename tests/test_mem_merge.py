from core.mem_merge import parse, merge, append_unique


def test_parse_filters_invalid_lines():
    result = parse("§proj:athos|status:active\nnot_section\n§rule:test")
    assert result["§proj:athos"] == "§proj:athos|status:active"
    assert result["§rule:test"] == "§rule:test"


def test_merge_keeps_incoming_on_conflict():
    base = "§proj:athos|status:inactive\n§rule:short"
    incoming = "§proj:athos|status:active\n§rule:short|weight:8"
    merged = merge(base, incoming)
    assert "status:active" in merged
    assert "weight:8" in merged


def test_append_unique_adds_new_lines_only():
    base = "§proj:athos|status:active\n"
    incoming = "§proj:athos|status:active\n§rule:new"
    output = append_unique(base, incoming)
    assert "§rule:new" in output
    assert output.count("§proj:athos") == 1
