"""Tests for the Interview Technique Coach. No test calls a real model."""

import json
from pathlib import Path

import pytest

from classifier import InvalidModelOutput, build_prompt, classify, primary_label, validate
from coach import main, run, to_markdown
from talk_ratio import percentages, talk_ratio
from transcript import parse_transcript

FIXTURES = Path(__file__).parent / "fixtures"
KEY = json.loads((FIXTURES / "answer_key.json").read_text(encoding="utf-8"))


def write(tmp_path, text, name="interview_99.txt"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def fake_model(expected_labels: dict[str, list[str]]):
    """A deterministic stand-in for the model: answers from a fixed label table and counts calls."""
    calls = []

    def call(prompt: str) -> str:
        calls.append(prompt)
        questions = []
        for line, labels in expected_labels.items():
            good = labels == ["good"]
            questions.append({"line": int(line), "labels": labels,
                              "explanation": "Open question about past behaviour." if good else "Suggests the answer.",
                              "suggestion": None if good else "When did that last happen?"})
        return json.dumps({"questions": questions})

    call.calls = calls
    return call


# --- deterministic: word counts and talk ratio ---------------------------------

@pytest.mark.parametrize("interview", ["interview_01", "interview_02"])
def test_talk_ratio_matches_hand_count(interview):
    assert talk_ratio(parse_transcript(FIXTURES / f"{interview}.txt")) == KEY[interview]["hand_count"]


def test_speaker_labels_headers_and_blank_lines_are_not_counted(tmp_path):
    path = write(tmp_path, "# segment: lots of header words here\n\nInterviewer: one two three\n\nCustomer: one\n")
    assert talk_ratio(parse_transcript(path)) == {"interviewer_words": 3, "customer_words": 1, "interviewer_share": 0.75}


def test_no_customer_turns_gives_share_one(tmp_path):
    ratio = talk_ratio(parse_transcript(write(tmp_path, "Interviewer: Anyone there?\n")))
    assert ratio == {"interviewer_words": 2, "customer_words": 0, "interviewer_share": 1.0}
    assert percentages(ratio) == (100, 0)


def test_zero_words_gives_null_share_not_division_error():
    tr = parse_transcript(FIXTURES / "empty.txt")
    assert talk_ratio(tr)["interviewer_share"] is None
    assert percentages(talk_ratio(tr)) is None


def test_percentages_always_add_to_100():
    assert percentages({"interviewer_words": 1, "customer_words": 2}) == (33, 67)
    assert sum(percentages({"interviewer_words": 58, "customer_words": 61})) == 100


# --- model boundary: prompt contents and output validation ---------------------

def test_prompt_contains_only_interviewer_questions():
    tr = parse_transcript(FIXTURES / "interview_01.txt")
    prompt = build_prompt(tr.by("Interviewer"))
    assert "L6: Wouldn't an app that predicts stock be great for you?" in prompt
    for customer_turn in tr.by("Customer"):
        assert customer_turn.text not in prompt
    assert "independent cafe owners" not in prompt  # header metadata is not sent


def test_planted_leading_questions_flagged_with_mock_classifier():
    labels = KEY["interview_01"]["expected_labels"]
    result, code = run(str(FIXTURES / "interview_01.txt"), fake_model(labels))
    assert code == 0
    by_line = {q["citation"]["line"]: q for q in result["questions"]}
    for line in KEY["interview_01"]["leading_question_lines"]:
        assert "leading" in by_line[line]["labels"] and by_line[line]["suggestion"]
    for line in KEY["interview_01"]["good_question_lines"]:
        assert by_line[line]["label"] == "good" and by_line[line]["suggestion"] is None


def test_validate_accepts_code_fenced_json():
    raw = '```json\n{"questions": [{"line": 4, "labels": ["good"], "explanation": "Open.", "suggestion": null}]}\n```'
    assert validate(raw, [4])[4]["labels"] == ["good"]


@pytest.mark.parametrize("raw, reason", [
    ("not json at all", "not valid JSON"),
    ('{"answers": []}', "missing"),
    ('{"questions": [{"line": 4, "labels": ["rude"], "explanation": "x", "suggestion": "y?"}]}', "unknown labels"),
    ('{"questions": [{"line": 4, "labels": ["good", "leading"], "explanation": "x", "suggestion": "y?"}]}', "combined"),
    ('{"questions": [{"line": 4, "labels": ["leading"], "explanation": "x", "suggestion": null}]}', "needs a suggestion"),
    ('{"questions": [{"line": 4, "labels": ["good"], "explanation": "", "suggestion": null}]}', "missing explanation"),
    ('{"questions": [{"line": 5, "labels": ["good"], "explanation": "x", "suggestion": null}]}', "unexpected line"),
    ('{"questions": []}', "not answered"),
])
def test_validate_rejects_bad_model_output(raw, reason):
    with pytest.raises(InvalidModelOutput, match=reason):
        validate(raw, [4])


def test_multiple_labels_kept_and_primary_is_most_severe():
    assert primary_label(["hypothetical", "leading"]) == "leading"
    assert primary_label(["hypothetical", "pitching"]) == "pitching"


# --- failure handling: never claim success ---------------------------------------

def test_invalid_json_three_times_marks_everything_unclassified(capsys):
    calls = []

    def broken(prompt):
        calls.append(prompt)
        return "Sure! Here are the labels you asked for."

    result, code = run(str(FIXTURES / "interview_01.txt"), broken)
    assert code == 1 and len(calls) == 3
    assert result["talk_ratio"] == KEY["interview_01"]["hand_count"]  # ratio still reported
    assert all(q["status"] == "unclassified" and q["label"] is None for q in result["questions"])
    assert "failed" in capsys.readouterr().err


def test_api_error_is_retried_then_reported():
    def down(prompt):
        raise ConnectionError("503 service unavailable")

    entries, ok = classify(parse_transcript(FIXTURES / "interview_01.txt").by("Interviewer"), down)
    assert not ok and all(e["status"] == "unclassified" for e in entries)


def test_recovers_when_second_attempt_is_valid():
    good = fake_model(KEY["interview_01"]["expected_labels"])
    answers = iter(["{broken", None])

    def flaky(prompt):
        return next(answers) or good(prompt)

    result, code = run(str(FIXTURES / "interview_01.txt"), flaky)
    assert code == 0 and all(q["status"] == "classified" for q in result["questions"])


# --- invalid and empty input -----------------------------------------------------

def test_malformed_line_exits_1_with_location_and_no_model_call(capsys):
    model = fake_model({})
    result, code = run(str(FIXTURES / "malformed.txt"), model)
    assert (result, code) == (None, 1)
    assert "malformed.txt:3" in capsys.readouterr().err
    assert model.calls == []


def test_empty_transcript_exits_1_with_null_share(capsys):
    model = fake_model({})
    result, code = run(str(FIXTURES / "empty.txt"), model)
    assert code == 1 and result["talk_ratio"]["interviewer_share"] is None
    assert model.calls == [] and "no Interviewer or Customer turns" in capsys.readouterr().err


def test_no_llm_cli_makes_no_model_call(capsys, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert main([str(FIXTURES / "interview_02.txt"), "--no-llm"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["talk_ratio"] == KEY["interview_02"]["hand_count"]
    assert out["usage"]["calls"] == 0 and out["questions"] == []


def test_missing_api_key_reports_unclassified_not_success(capsys, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert main([str(FIXTURES / "interview_01.txt")]) == 1
    captured = capsys.readouterr()
    out = json.loads(captured.out)
    assert all(q["status"] == "unclassified" for q in out["questions"])
    assert "not retrying" in captured.err and "attempt 2" not in captured.err


# --- report ----------------------------------------------------------------------

def test_markdown_report_is_short_and_has_rewrites():
    result, _ = run(str(FIXTURES / "interview_01.txt"), fake_model(KEY["interview_01"]["expected_labels"]))
    report = to_markdown(result)
    assert "ratio 49:51" in report
    assert report.count("Try:") == 3  # one rewrite per leading question, none for good ones
    assert "- Good: L4, L8, L12" in report


def test_report_for_20_flagged_questions_fits_in_40_lines(tmp_path):
    text = "".join(f"Interviewer: Wouldn't an app for this be great?\nCustomer: Maybe.\n" for _ in range(20))
    lines = range(1, 41, 2)  # interviewer turns are on the odd lines
    result, code = run(str(write(tmp_path, text)), fake_model({str(l): ["leading", "hypothetical"] for l in lines}))
    assert code == 0 and len(to_markdown(result).splitlines()) <= 40


def test_validate_rejects_boolean_line_number():
    raw = '{"questions": [{"line": true, "labels": ["good"], "explanation": "x", "suggestion": null}]}'
    with pytest.raises(InvalidModelOutput, match="unexpected line"):
        validate(raw, [1])
