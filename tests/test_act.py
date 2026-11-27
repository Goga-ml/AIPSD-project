"""The three gates in call_tool(): offered? valid? identity from the session? All offline."""
import json
import os

from src import tools
from src.act import call_tool
from src.tools import TOOLS, tools_for

FOUNDER = "founder-test"


def call(name, **args):
    return {"id": "c1", "name": name, "arguments": json.dumps(args)}


def run(name, _as=FOUNDER, **args):
    return call_tool(call(name, **args), tools_for(_as), _as)


def test_valid_call_runs_and_cites_physical_lines():
    out = run("get_transcript", interview_id="interview_01", speaker="Customer", max_turns=1)
    assert out["ok"], out["error"]
    first = out["result"]["turns"][0]
    assert first == {"line": 5, "speaker": "Customer",
                     "text": "Last Saturday we ran out of oat milk by 11, lost maybe twenty orders."}
    assert out["result"]["truncated"] is True and out["result"]["meta"]["date"] == "2026-10-10"


def test_invalid_arguments_never_reach_the_tool(monkeypatch):
    def must_not_run(*a, **k):
        raise AssertionError("the tool ran")
    monkeypatch.setattr(tools, "parse_transcript", must_not_run)
    for bad in ({"interview_id": "../../.env"}, {"interview_id": "answer_key"},
                {"interview_id": "interview_01", "max_turns": 10_000},
                {"interview_id": "interview_01", "speaker": "System"}):
        out = run("get_transcript", **bad)
        assert not out["ok"] and out["error"].startswith("invalid arguments"), bad


def test_a_tool_not_offered_never_runs():
    out = run("get_transcript", _as=None, interview_id="interview_01")
    assert not out["ok"] and "no tool named 'get_transcript'" in out["error"] and out["result"] is None


def test_a_tool_that_does_not_exist_never_runs():
    out = run("delete_transcript", interview_id="interview_01")
    assert not out["ok"] and out["result"] is None


def test_the_model_cannot_set_identity():
    for field in ("founder", "user_id", "caller"):
        out = run("get_transcript", interview_id="interview_01", **{field: "someone-else"})
        assert not out["ok"] and field in out["error"] and "extra" in out["error"].lower()
    for t in TOOLS.values():
        props = t.schema()["function"]["parameters"]["properties"]
        assert not {"founder", "user", "user_id", "student", "account", "caller"} & set(props)


def test_identity_is_required_even_if_a_tool_is_handed_over():
    out = call_tool(call("get_transcript", interview_id="interview_01"), TOOLS, None)
    assert not out["ok"] and "not signed in" in out["error"]


def test_expected_failures_tell_the_model_what_to_do_and_leak_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("GROUNDWORK_TRANSCRIPTS", str(tmp_path))
    (tmp_path / "interview_07.txt").write_text("Founder: hi\n", encoding="utf-8")
    missing = run("get_transcript", interview_id="interview_99")
    broken = run("get_transcript", interview_id="interview_07")
    assert "There is no interview interview_99" in missing["error"] and "Ask the founder" in missing["error"]
    assert "not in the transcript format" in broken["error"]
    for e in (missing["error"], broken["error"]):
        assert str(tmp_path) not in e and ".txt" not in e and "Traceback" not in e


def test_a_bug_becomes_an_error_not_a_crash(monkeypatch):
    monkeypatch.setattr(tools, "parse_transcript", lambda p: 1 / 0)
    out = run("get_transcript", interview_id="interview_01")
    assert not out["ok"] and "unexpectedly" in out["error"] and "ZeroDivision" not in out["error"]


def test_every_call_writes_one_log_line_without_the_caller_id():
    log = os.environ["GROUNDWORK_TOOL_LOG"]
    before = open(log).read().count("\n") if os.path.exists(log) else 0
    run("get_transcript", interview_id="interview_02")
    run("get_transcript", interview_id="not-an-id")
    lines = [json.loads(x) for x in open(log).read().splitlines()]
    assert len(lines) == before + 2
    assert lines[-2]["ok"] and not lines[-1]["ok"]
    assert all(x["caller"] != FOUNDER and len(x["caller"]) == 12 for x in lines[-2:])
