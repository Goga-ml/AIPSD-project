"""Lab 7: the supervised loop, offline. The first two tests are the course template (Lab-7/templates/test_agent.py)
with our three ADAPT lines; the rest attack the gate from other directions."""
import json

from fastapi.testclient import TestClient

from src import memory
from src.agent import PENDING, confirm, run
from src.app import app
from src.tools import PROPOSE_ONLY, TOOLS, tools_for

USER = "founder-1"                                                    # ADAPT 1
NEEDS_A_YES = ("save_evidence", {"interview_id": "interview_01", "kind": "spending",
                                 "quote": "We pay 45 GEL a month for a POS add-on"})   # ADAPT 2


def what_changed():
    """ADAPT 3: what save_evidence changes: this founder's evidence board."""
    return memory.evidence(USER)


def scripted(*turns):
    """A fake model: each turn is a list of (tool, arguments) calls, or the final text."""
    left = list(turns)

    def model(messages, schemas):
        turn = left.pop(0)
        if isinstance(turn, str):
            return {"content": turn, "tool_calls": []}
        return {"content": None, "tool_calls": [
            {"id": f"c{len(messages)}-{i}", "name": name, "arguments": json.dumps(args)} for i, (name, args) in enumerate(turn)]}
    return model


# ---------------------------------------------------------------- the course template

def test_the_gate_blocks_until_a_person_says_yes():
    PENDING.clear()
    before = what_changed()
    plan = run("collect evidence for me", USER, llm=scripted([NEEDS_A_YES], "I proposed one quote."))
    assert plan["status"] == "needs_confirmation" and len(plan["proposed"]) == 1
    assert what_changed() == before                         # proposed is not done
    done = confirm(USER, [plan["proposed"][0]["id"]])
    assert done[0]["ok"] and what_changed() != before       # the yes is what did it
    assert confirm(USER, [plan["proposed"][0]["id"]]) == [] # and a plan works once


def test_the_loop_stops_after_max_steps():
    PENDING.clear()
    before = what_changed()
    forever = scripted(*[[NEEDS_A_YES]] * 10)               # a model that never says "done"
    plan = run("collect evidence for me", USER, llm=forever, max_steps=4)
    assert plan["status"] == "stopped" and "4 steps" in plan["text"]
    assert what_changed() == before                         # stopping early does nothing, either


# ---------------------------------------------------------------- the gate, from other directions

def test_reads_run_in_the_loop_and_the_founder_sees_one_line_per_proposal():
    PENDING.clear()
    plan = run("collect evidence", USER, llm=scripted(
        [("verify_quote", {"interview_id": "interview_01", "quote": "We pay 45 GEL a month for a POS add-on"})],
        [NEEDS_A_YES], "Proposed one."))
    assert [t["tool"] for t in plan["trace"]] == ["verify_quote", "save_evidence"]
    assert [t["parked"] for t in plan["trace"]] == [False, True]
    assert plan["proposed"][0]["summary"] == 'Save as spending: "We pay 45 GEL a month for a POS add-on" (interview_01)'


def test_save_evidence_is_in_no_other_door():
    assert "save_evidence" not in TOOLS and "save_evidence" in PROPOSE_ONLY
    assert "save_evidence" not in tools_for(USER)            # so /act, /chat and MCP never offer it


def test_a_proposal_that_breaks_the_contract_is_not_parked():
    PENDING.clear()
    bad = ("save_evidence", {"interview_id": "interview_01", "kind": "spending",
                             "quote": "We pay 45 GEL", "founder": "founder-2"})
    plan = run("collect", USER, llm=scripted([bad], "Done."))
    assert plan["status"] == "answered" and plan["proposed"] == []


def test_the_yes_re_checks_the_quote_before_saving():
    PENDING.clear()
    invented = ("save_evidence", {"interview_id": "interview_01", "kind": "spending",
                                  "quote": "We would happily pay 300 GEL a month for a stock app"})
    plan = run("collect", USER, llm=scripted([invented], "Proposed one."))
    done = confirm(USER, ["a1"])
    assert not done[0]["ok"] and "not in a Customer turn" in done[0]["error"] and what_changed() == []


def test_another_founder_cannot_confirm_my_plan():
    PENDING.clear()
    run("collect", USER, llm=scripted([NEEDS_A_YES], "Proposed."))
    assert confirm("founder-2", ["a1"]) == [] and memory.evidence("founder-2") == []
    assert what_changed() == []


def test_only_the_approved_ids_run():
    PENDING.clear()
    second = ("save_evidence", {"interview_id": "interview_02", "kind": "spending",
                                "quote": "I pay my nephew 200 GEL a month to keep the ordering spreadsheet up to date"})
    run("collect", USER, llm=scripted([NEEDS_A_YES, second], "Proposed two."))
    done = confirm(USER, ["a2"])
    assert [d["id"] for d in done] == ["a2"]
    assert [e["interview_id"] for e in what_changed()] == ["interview_02"]


def test_every_model_down_parks_nothing():
    PENDING.clear()
    down = lambda m, s: {"content": "Groundwork cannot reach its models right now.", "tool_calls": [], "degraded": True}  # noqa: E731
    plan = run("collect", USER, llm=down)
    assert plan["status"] == "stopped" and plan["proposed"] == [] and PENDING[USER] == []


# ---------------------------------------------------------------- the endpoints

def test_plan_and_confirm_through_http(monkeypatch):
    PENDING.clear()
    from src import app as app_module
    monkeypatch.setattr(app_module, "run", lambda goal, user: run(goal, user, llm=scripted([NEEDS_A_YES], "Proposed one.")))
    client = TestClient(app)
    headers = {"X-Founder": USER}
    plan = client.post("/plan", json={"goal": "Collect evidence on what people pay"}, headers=headers).json()
    assert plan["status"] == "needs_confirmation" and what_changed() == []
    done = client.post("/plan/confirm", json={"ids": ["a1"]}, headers=headers).json()["done"]
    assert done[0]["id"] == "a1" and done[0]["ok"] and done[0]["result"]["citation"]["line"] == 11
    assert client.get("/me/memory", headers=headers).json()["evidence"][0]["line"] == 11
    assert client.delete("/me/memory", headers=headers).json()["evidence"] == 1


def test_confirm_takes_ids_only_and_needs_a_founder():
    client = TestClient(app)
    assert client.post("/plan/confirm", json={"ids": ["a1"]}).status_code == 401
    assert client.post("/plan", json={"goal": "Collect evidence"}).status_code == 401
    bad_bodies = [{"ids": []}, {"ids": ["save_evidence"]},
                  {"ids": ["a1"], "arguments": {"quote": "anything"}}]
    for body in bad_bodies:
        assert client.post("/plan/confirm", json=body, headers={"X-Founder": USER}).status_code == 422
