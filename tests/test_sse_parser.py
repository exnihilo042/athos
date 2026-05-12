from core import sse_parser


def test_parse_sse_block_with_event_and_data():
    block = 'event: hermes.tool.progress\ndata: {"tool":"search"}'
    assert sse_parser.parse_sse_block(block) == {
        "event_type": "hermes.tool.progress",
        "data": '{"tool":"search"}',
    }


def test_parse_sse_block_returns_none_without_data():
    assert sse_parser.parse_sse_block("event: only") is None
    assert sse_parser.parse_sse_block(": comment") is None


def test_custom_tool_progress_event_is_normalized():
    result = sse_parser.process_custom_event(
        "hermes.tool.progress",
        '{"tool":"search_web","emoji":"S","label":"Searching"}',
    )

    assert result["handled"] is True
    assert result["events"][0]["label"] == "S Searching"


def test_process_sse_data_extracts_chunk_usage_error_and_done():
    state = sse_parser.SseState()
    chunk = sse_parser.process_sse_data('{"choices":[{"delta":{"content":"Hello"}}]}', state)
    usage = sse_parser.process_sse_data('{"usage":{"prompt_tokens":10,"completion_tokens":5,"total_tokens":15}}', state)
    error = sse_parser.process_sse_data('{"error":{"message":"Rate limit"}}', state)
    done = sse_parser.process_sse_data("[DONE]", state)

    assert chunk["events"] == [{"type": "chunk", "text": "Hello"}]
    assert usage["events"][0]["usage"]["totalTokens"] == 15
    assert error["error"] == "Rate limit"
    assert done["done"] is True
    assert done["events"] == [{"type": "done"}]


def test_legacy_inline_tool_progress_does_not_become_content():
    result = sse_parser.process_sse_data('{"choices":[{"delta":{"content":"`S search_web`"}}]}')

    assert result["has_content"] is False
    assert result["events"][0]["type"] == "tool_progress"


def test_malformed_data_is_visible_but_nonfatal():
    result = sse_parser.process_sse_data("not-json{")

    assert result["done"] is False
    assert result["events"][0]["type"] == "malformed"
