from core.reasoning_kernel import build_frame


def test_reasoning_frame_exposes_visible_journal_not_hidden_thought():
    frame = build_frame(
        "corrige le bug puis cherche la doc officielle",
        ["chatgpt_plus", "claude_code"],
        "chatgpt_plus",
    )

    events = frame.events()
    texts = [event["thinking"]["text"] for event in events]

    assert frame.selected_engine == "chatgpt_plus"
    assert any("Athos est l'identité unique" in text for text in texts)
    assert any("validation visible requise" in text for text in texts)
    assert any("Sources externes" in text for text in texts)
    assert all("chain-of-thought" not in text.lower() for text in texts)
