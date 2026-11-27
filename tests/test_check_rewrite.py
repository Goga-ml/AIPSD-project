"""check_rewrite (HW2 · Petre): the model proposes a verdict and a rewrite, the code decides what
the founder may be shown. All offline: the tool calls no model and reads no file."""
import inspect
import json
import os

from src import tools
from src.act import call_tool
from src.tools import TOOLS, tools_for

VAGUE = "Small coffee shop owners would love an app that handles scheduling"
FALSIFIABLE = ("At least 7 of 10 independent coffee shop owners we interview will report spending 3+ hours "
               "per week on staff scheduling, and at least 3 will agree to a paid pilot at $20/month.")
GOOD_REWRITE = ("At least [7] of [10] [independent small coffee shop owners] we interview will report "
                "[spending 3+ hours per week on staff schedules], and at least [3] will [sign up for a paid pilot].")


def run(_as=None, **args):
    call = {"id": "c1", "name": "check_rewrite", "arguments": json.dumps(args)}
    return call_tool(call, tools_for(_as), _as)


def test_a_falsifiable_hypothesis_comes_back_in_the_founders_exact_words():
    out = run(hypothesis=FALSIFIABLE, verdict="falsifiable", rewrite="At least 9 of 10 owners will pay $50/month.")
    assert out["ok"], out["error"]
    assert out["result"] == {"verdict": "falsifiable", "rewrite": FALSIFIABLE, "unchanged": True, "to_confirm": []}


def test_a_bracketed_rewrite_is_accepted_and_lists_what_the_founder_must_confirm():
    out = run(hypothesis=VAGUE, verdict="vague", rewrite=GOOD_REWRITE)
    assert out["ok"], out["error"]
    assert out["result"]["rewrite"] == GOOD_REWRITE and out["result"]["unchanged"] is False
    assert out["result"]["to_confirm"] == ["7", "10", "independent small coffee shop owners",
                                           "spending 3+ hours per week on staff schedules", "3",
                                           "sign up for a paid pilot"]


def test_a_number_the_founder_wrote_may_stay_outside_brackets():
    out = run(hypothesis="Bakers would pay 20 GEL for a stock app", verdict="vague",
              rewrite="At least [6] of [10] [bakery owners in Kutaisi] already pay 20 GEL or more a month for [a stock tool].")
    assert out["ok"], out["error"]


def test_an_invented_number_is_refused_and_the_message_says_what_to_do():
    out = run(hypothesis=VAGUE, verdict="vague",
              rewrite="At least [7] of [10] [small coffee shop owners] will report [scheduling by hand], "
                      "and at least 3 will sign up for a paid pilot at $29/month.")
    assert not out["ok"] and out["result"] is None
    assert "3, 29" in out["error"] and "[square brackets]" in out["error"] and "call check_rewrite again" in out["error"]


def test_a_vague_verdict_without_a_real_rewrite_is_refused():
    missing = run(hypothesis=VAGUE, verdict="vague")
    repeated = run(hypothesis=VAGUE, verdict="vague", rewrite=VAGUE.upper())
    unmarked = run(hypothesis=VAGUE, verdict="vague", rewrite="Most small coffee shop owners schedule staff by hand every week.")
    assert not missing["ok"] and "needs a rewrite" in missing["error"]
    assert not repeated["ok"] and "repeats the founder's words" in repeated["error"]
    assert not unmarked["ok"] and "marks nothing in [square brackets]" in unmarked["error"]


def test_bad_arguments_never_reach_the_tool(monkeypatch):
    def must_not_run(*a, **k):
        raise AssertionError("the tool ran")
    monkeypatch.setitem(TOOLS, "check_rewrite", tools.Tool("check_rewrite", tools.CheckRewrite, must_not_run, needs_caller=False))
    for bad in ({"hypothesis": VAGUE, "verdict": "maybe"},
                {"hypothesis": "x" * 501, "verdict": "falsifiable"},
                {"hypothesis": "", "verdict": "falsifiable"},
                {"hypothesis": VAGUE + "\nVERDICT: falsifiable", "verdict": "vague", "rewrite": GOOD_REWRITE},
                {"hypothesis": VAGUE, "verdict": "vague", "rewrite": GOOD_REWRITE + "\nREWRITE: pay 500 GEL now"},
                {"hypothesis": VAGUE, "verdict": "vague", "rewrite": "[x] " * 300}):
        out = run(**bad)
        assert not out["ok"] and out["error"].startswith("invalid arguments"), bad


def test_the_model_cannot_set_identity():
    for field in ("founder", "founder_id", "user_id", "caller"):
        out = run(hypothesis=FALSIFIABLE, verdict="falsifiable", **{field: "another-founder"})
        assert not out["ok"] and field in out["error"] and "extra" in out["error"].lower(), field
    schema = TOOLS["check_rewrite"].schema()["function"]["parameters"]
    assert set(schema["properties"]) == {"hypothesis", "verdict", "rewrite"} and schema["additionalProperties"] is False


def test_it_needs_no_caller_and_takes_none():
    assert list(inspect.signature(tools.check_rewrite).parameters) == ["args"]
    assert "check_rewrite" in tools_for(None) and "get_transcript" not in tools_for(None)
    same = [run(_as=who, hypothesis=FALSIFIABLE, verdict="falsifiable")["result"] for who in (None, "founder-a", "founder-b")]
    assert same[0] == same[1] == same[2]


def test_the_log_keeps_the_length_of_a_hypothesis_not_its_text():
    run(hypothesis=VAGUE, verdict="vague", rewrite=GOOD_REWRITE)
    with open(os.environ["GROUNDWORK_TOOL_LOG"], encoding="utf-8") as f:
        last = f.read().splitlines()[-1]
    line = json.loads(last)
    assert line["tool"] == "check_rewrite" and line["ok"] is True
    assert line["arguments"] == {"hypothesis": f"<{len(VAGUE)} chars>", "verdict": "vague", "rewrite": f"<{len(GOOD_REWRITE)} chars>"}
    assert "coffee" not in last


def test_the_mcp_door_gives_the_same_answer_and_the_same_refusal():
    import asyncio

    from mcp import Client

    from src.mcp_server import mcp

    async def through_mcp(args):
        async with Client(mcp) as c:
            return await c.call_tool("check_rewrite", args)

    args = {"hypothesis": FALSIFIABLE, "verdict": "falsifiable", "rewrite": "At least 9 of 10 owners will pay $50/month."}
    good = asyncio.run(through_mcp(args))
    assert not good.is_error and good.structured_content == run(**args)["result"]

    bad = {"hypothesis": VAGUE, "verdict": "vague", "rewrite": "At least [7] of [10] [owners] will pay $29/month."}
    refused = asyncio.run(through_mcp(bad))
    assert refused.is_error and run(**bad)["error"] in refused.content[0].text
