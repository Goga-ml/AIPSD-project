import json

import check_planted
from conftest import DATA

KEY = json.loads((DATA / "answer_key.json").read_text(encoding="utf-8"))


def _result(items):
    return {"interview_id": "interview_01", "evidence": items,
            "stats": {"accepted": len(items), "rejected": 0}}


def test_found_needs_same_type_and_line():
    # interview_01 planted: pain L5, workaround L9, spending L11, workaround L15
    items = [{"type": "pain", "citation": {"line": 5}},
             {"type": "spending", "citation": {"line": 9}}]  # right line of a workaround, wrong type
    assert [ok for _, ok in check_planted.check(KEY, _result(items))] == [True, False, False, False]


def test_answer_key_lines_point_at_the_right_speaker():
    from transcript import parse_transcript
    for iid, entry in KEY.items():
        if iid.startswith("_"):   # "_notes" is commentary, not an interview
            continue
        speaker = {t.line: t.speaker for t in parse_transcript(DATA / f"{iid}.txt").turns}
        assert all(speaker[p["line"]] == "Customer" for p in entry["planted"])
        assert all(speaker[n] == "Interviewer" for n in entry["leading_question_lines"])


def test_reads_utf16_file_from_powershell(tmp_path):
    f = tmp_path / "interview_01.json"
    f.write_bytes(json.dumps(_result([])).encode("utf-16"))  # what PowerShell 5.1 `>` produces
    assert check_planted.load(str(f))["interview_id"] == "interview_01"


def test_empty_result_file_is_a_clean_error(tmp_path, capsys):
    f = tmp_path / "interview_01.json"
    f.write_text("")
    assert check_planted.main([str(DATA / "answer_key.json"), str(f)]) == 1
    assert "is empty" in capsys.readouterr().err
