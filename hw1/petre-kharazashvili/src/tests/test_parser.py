import pytest

from parser import LintParser, ParseError

COFFEE = (
    "At least 7 of 10 independent coffee shop owners we interview will report spending 3+ hours per week "
    "on staff scheduling, and at least 3 will agree to a paid pilot at $20/month."
)
VAGUE_MODEL = (
    "VERDICT: VAGUE\n"
    "REASON: No segment, no threshold.\n"
    "REWRITE: At least [6] of [10] [smallholder farmers] will report [losing a harvest].\n"
)
VAGUE_WIRE = (
    "VERDICT: vague\n"
    "REASON: No segment, no threshold.\n"
    "REWRITE: At least [6] of [10] [smallholder farmers] will report [losing a harvest].\n"
)


def feed_char_by_char(model_text: str, hypothesis: str = "Farmers want better tools") -> list[str]:
    """Feed one character at a time; return the output produced after each character, then finish()."""
    parser = LintParser(hypothesis)
    outputs = [parser.feed(ch) for ch in model_text]
    outputs.append(parser.finish())
    return outputs


def test_char_by_char_produces_wire_format():
    assert "".join(feed_char_by_char(VAGUE_MODEL)) == VAGUE_WIRE


def test_verdict_is_emitted_as_soon_as_its_line_ends():
    outputs = feed_char_by_char(VAGUE_MODEL)
    verdict_line_end = VAGUE_MODEL.index("\n")
    assert outputs[verdict_line_end] == "VERDICT: vague\n"
    assert "".join(outputs[:verdict_line_end]) == ""  # nothing before the verdict is decided


def test_reason_streams_before_its_line_ends():
    outputs = feed_char_by_char(VAGUE_MODEL)
    reason_start = VAGUE_MODEL.index("REASON: ") + len("REASON: ")
    sent_mid_reason = "".join(outputs[: reason_start + 5])
    assert sent_mid_reason.endswith("REASON: No se")


def test_chunking_does_not_change_output():
    parser = LintParser("Farmers want better tools")
    whole = parser.feed(VAGUE_MODEL) + parser.finish()
    assert whole == "".join(feed_char_by_char(VAGUE_MODEL)) == VAGUE_WIRE


def test_falsifiable_rewrite_is_byte_identical_to_input():
    model = "VERDICT: FALSIFIABLE\nREASON: Segment, behavior and threshold are all present.\nREWRITE: UNCHANGED\n"
    wire = "".join(feed_char_by_char(model, COFFEE))
    assert wire.splitlines()[2] == f"REWRITE: {COFFEE}"
    assert wire.endswith("\n") and wire.count("\n") == 3


def test_falsifiable_ignores_a_model_that_edits_the_input():
    model = "VERDICT: FALSIFIABLE\nREASON: Fine.\nREWRITE: At least 7 of 10 coffee owners (slightly reworded).\n"
    assert "".join(feed_char_by_char(model, COFFEE)).splitlines()[2] == f"REWRITE: {COFFEE}"


def test_tolerates_markdown_case_preamble_and_wrapped_lines():
    model = (
        "Here is my assessment:\n\n"
        "**VERDICT:** vague\n"
        "**Reason:** No segment.\nAlso no threshold.\n"
        "rewrite: At least [6] of [10] [farmers]\nwill report [X].\n"
    )
    assert "".join(feed_char_by_char(model)) == (
        "VERDICT: vague\nREASON: No segment. Also no threshold.\nREWRITE: At least [6] of [10] [farmers] will report [X].\n"
    )


def test_missing_trailing_newline_is_fine():
    assert "".join(feed_char_by_char(VAGUE_MODEL.rstrip("\n"))) == VAGUE_WIRE


@pytest.mark.parametrize(
    "model, message",
    [
        ("VERDICT: MAYBE\nREASON: x\nREWRITE: y\n", "not FALSIFIABLE or VAGUE"),
        ("REASON: x\nVERDICT: VAGUE\n", "REASON where VERDICT was expected"),
        ("VERDICT: VAGUE\nREASON: x\n", "missing REWRITE"),
        ("I can't help with that.", "missing VERDICT, REASON, REWRITE"),
    ],
)
def test_bad_format_raises_readable_error(model, message):
    with pytest.raises(ParseError, match=message):
        feed_char_by_char(model)
