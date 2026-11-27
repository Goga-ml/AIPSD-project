"""talk_ratio (HW2 · Ghmertoto): the numbers are right, the failures are readable, both doors agree."""
import asyncio
import json
from pathlib import Path

import pytest
from mcp import Client

from src.act import call_tool
from src.contracts import TalkRatio
from src.mcp_server import mcp
from src.tools import tools_for

ROOT = Path(__file__).resolve().parents[1]
FOUNDER = "founder-1"


def call(args, caller=FOUNDER):
    return call_tool({"id": "t", "name": "talk_ratio", "arguments": json.dumps(args)}, tools_for(caller), caller)


def count_by_hand(interview_id: str) -> tuple[int, int]:
    """A second, independent count straight from the file, without the shared parser."""
    words = {"Interviewer": 0, "Customer": 0}
    for line in (ROOT / "data" / "transcripts" / f"{interview_id}.txt").read_text(encoding="utf-8").splitlines():
        speaker, sep, text = line.partition(": ")
        if sep and speaker in words:
            words[speaker] += len(text.split())
    return words["Interviewer"], words["Customer"]


@pytest.mark.parametrize("interview_id", ["interview_01", "interview_02", "interview_03"])
def test_counts_match_an_independent_count_of_the_file(interview_id):
    interviewer, customer = count_by_hand(interview_id)
    result = call({"interview_id": interview_id})["result"]
    assert (result["interviewer_words"], result["customer_words"]) == (interviewer, customer)
    assert result["interviewer_share"] == round(interviewer / (interviewer + customer), 2)


def test_ratio_is_whole_percent_and_adds_up_to_100():
    left, right = call({"interview_id": "interview_03"})["result"]["ratio"].split(":")
    assert int(left) + int(right) == 100


def test_the_second_identical_call_returns_the_same_result():
    first, second = call({"interview_id": "interview_01"}), call({"interview_id": "interview_01"})
    assert first["ok"] and first["result"] == second["result"]


def test_the_contract_has_one_argument_and_forbids_the_rest():
    schema = TalkRatio.model_json_schema()
    assert list(schema["properties"]) == ["interview_id"] and schema["additionalProperties"] is False
    assert schema["properties"]["interview_id"]["pattern"] == "^interview_[0-9]{2}$"


@pytest.mark.parametrize("bad_id", ["interview_01\n", " interview_01", "interview_001", "INTERVIEW_01",
                                    "interview_٠١"])          # the last one: Arabic-Indic digits
def test_ids_that_only_look_right_are_refused(bad_id):
    out = call({"interview_id": bad_id})
    assert not out["ok"] and "invalid arguments" in out["error"]


def test_a_transcript_with_no_turns_is_refused_with_what_to_do(tmp_path, monkeypatch):
    (tmp_path / "interview_01.txt").write_text("# segment: nobody\n\n", encoding="utf-8")
    monkeypatch.setenv("GROUNDWORK_TRANSCRIPTS", str(tmp_path))
    out = call({"interview_id": "interview_01"})
    assert not out["ok"] and "no spoken turns" in out["error"] and "do not estimate" in out["error"]


def test_a_broken_transcript_is_refused_without_a_path_or_a_stack_trace(tmp_path, monkeypatch):
    (tmp_path / "interview_01.txt").write_text("Interviewer: hi\nnot a turn\n", encoding="utf-8")
    monkeypatch.setenv("GROUNDWORK_TRANSCRIPTS", str(tmp_path))
    out = call({"interview_id": "interview_01"})
    assert not out["ok"] and "not in the transcript format" in out["error"]
    assert str(tmp_path) not in out["error"] and "Traceback" not in out["error"]


def test_one_speaker_only_still_gives_a_ratio(tmp_path, monkeypatch):
    (tmp_path / "interview_01.txt").write_text("Interviewer: So tell me everything.\n", encoding="utf-8")
    monkeypatch.setenv("GROUNDWORK_TRANSCRIPTS", str(tmp_path))
    result = call({"interview_id": "interview_01"})["result"]
    assert result["interviewer_share"] == 1.0 and result["ratio"] == "100:0"


def test_a_visitor_is_not_offered_the_tool():
    out = call({"interview_id": "interview_01"}, caller=None)
    assert not out["ok"] and "no tool named" in out["error"]


def test_the_mcp_door_returns_the_same_numbers(monkeypatch):
    monkeypatch.setenv("GROUNDWORK_FOUNDER", FOUNDER)

    async def through_mcp():
        async with Client(mcp) as c:
            return await c.call_tool("talk_ratio", {"interview_id": "interview_02"})
    r = asyncio.run(through_mcp())
    assert not r.is_error and r.structured_content == call({"interview_id": "interview_02"})["result"]
