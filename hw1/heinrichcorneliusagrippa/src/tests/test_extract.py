"""Extraction with a fake model: shape, retry, rejection, CLI exit codes. No API key needed."""
import json

import pytest

import extract
import llm
from conftest import DATA, FakeModel

GOOD = {"evidence": [
    {"type": "pain", "summary": "Ran out of oat milk, lost orders.",
     "quote": "we ran out of oat milk by 11, lost maybe twenty orders"},
    {"type": "workaround", "summary": "Buys at retail from the supermarket.",
     "quote": "I sent my barista to the supermarket and we paid retail"},
    {"type": "spending", "summary": "Invented by the model.",
     "quote": "we pay 200 lari a month for a weather app"},
]}


def test_output_shape_and_rejection(tr01):
    out = extract.extract(tr01, FakeModel(GOOD))
    assert [e["id"] for e in out["evidence"]] == ["interview_01-e1", "interview_01-e2"]
    assert [e["citation"]["line"] for e in out["evidence"]] == [5, 15]
    assert out["rejected"][0]["reason"] == "quote_not_found"
    assert out["stats"] == {"extracted": 3, "accepted": 2, "rejected": 1, "attempts": 1}
    assert out["usage"]["calls"] == 1


def test_retry_after_invalid_json_then_success(tr01):
    fake = FakeModel("```json\n{not json", GOOD)
    out = extract.extract(tr01, fake)
    assert out["stats"]["attempts"] == 2
    assert out["usage"]["calls"] == 2 and out["usage"]["input_tokens"] == 200
    assert "rejected by the validator" in fake.prompts[1]  # the error is fed back


def test_wrong_type_label_is_retried(tr01):
    bad = {"evidence": [{"type": "Complaint", "summary": "x", "quote": "y"}]}
    out = extract.extract(tr01, FakeModel(bad, GOOD))
    assert out["stats"]["attempts"] == 2


def test_three_bad_replies_fail(tr01):
    with pytest.raises(extract.ExtractionFailed):
        extract.extract(tr01, FakeModel("nope", "{}", '{"evidence": "x"}'))


def test_cli_prints_json_and_counts(capsys):
    code = extract.main([str(DATA / "interview_01.txt")], call=FakeModel(GOOD))
    out, err = capsys.readouterr()
    assert code == 0
    assert json.loads(out)["stats"]["accepted"] == 2
    assert "accepted 2, rejected 1" in err


def test_cli_exit_1_after_three_bad_replies(capsys):
    code = extract.main([str(DATA / "interview_01.txt")], call=FakeModel("x", "x", "x"))
    assert code == 1 and capsys.readouterr().out == ""


def test_cli_exit_1_on_malformed_transcript(tmp_path, capsys):
    bad = tmp_path / "interview_99.txt"
    bad.write_text("Interviewer: hi\ncustomer: lowercase speaker\n", encoding="utf-8")
    code = extract.main([str(bad)], call=FakeModel())  # FakeModel with no replies: must not be called
    assert code == 1 and "interview_99.txt:2" in capsys.readouterr().err


def test_cost_formula():
    assert llm.cost_usd("gemini-3.8-flash", 1_000_000, 0) == 0.75
    assert llm.cost_usd("gemini-3.8-flash", 2000, 400) == round((2000 * 0.75 + 400 * 3.75) / 1e6, 6)
