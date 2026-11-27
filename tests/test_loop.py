"""Lab 5: the tool loop and POST /act, offline. The "model" is a scripted function, so each test decides
exactly what it asks for. No key, no network."""
import json

from fastapi.testclient import TestClient

from src import act as act_module
from src.act import MAX_ROUNDS, act, as_assistant
from src.app import app

FOUNDER = "founder-1"


def scripted(*turns, seen=None):
    """Each turn is a list of (tool, arguments) calls, or the final text. `seen` collects every
    messages list the model was sent, so a test can read what came back from a tool."""
    left = list(turns)

    def model(messages, schemas):
        if seen is not None:
            seen.append({"messages": [dict(m) for m in messages], "tools": [s["function"]["name"] for s in schemas]})
        turn = left.pop(0)
        if isinstance(turn, str):
            return {"content": turn, "tool_calls": []}
        return {"content": None, "reasoning_details": [{"type": "reasoning.encrypted", "data": "opaque"}],
                "tool_calls": [{"id": f"c{len(messages)}-{i}", "name": n, "arguments": json.dumps(a)}
                               for i, (n, a) in enumerate(turn)]}
    return model


def test_no_tool_call_means_that_is_the_answer():
    reply = act("Hello?", FOUNDER, llm=scripted("Hi. Ask me about your interviews."))
    assert reply.status == "answered" and reply.calls == []


def test_a_tool_call_runs_through_the_gates_and_its_result_goes_back():
    seen = []
    reply = act("Who talks most in interview 1?", FOUNDER,
                llm=scripted([("talk_ratio", {"interview_id": "interview_01"})], "The customer: 60%.", seen=seen))
    assert reply.status == "answered" and reply.calls[0]["ok"]
    tool_msg = seen[1]["messages"][-1]
    assert tool_msg["role"] == "tool" and json.loads(tool_msg["content"])["ratio"] == "40:60"


def test_invalid_arguments_go_back_as_an_error_and_the_model_can_repair():
    seen = []
    reply = act("Ratio for interview 1?", FOUNDER, llm=scripted(
        [("talk_ratio", {"interview_id": "../../.env"})],
        [("talk_ratio", {"interview_id": "interview_01"})],
        "40:60.", seen=seen))
    assert [c["ok"] for c in reply.calls] == [False, True]
    assert "invalid arguments" in json.loads(seen[1]["messages"][-1]["content"])["error"]


def test_the_round_budget_stops_a_model_that_never_finishes():
    forever = scripted(*[[("talk_ratio", {"interview_id": "interview_01"})]] * 10)
    reply = act("Loop forever", FOUNDER, llm=forever)
    assert reply.status == "stopped" and f"{MAX_ROUNDS} steps" in reply.text
    assert len(reply.calls) == MAX_ROUNDS


def test_a_visitor_is_offered_no_tool_that_needs_a_caller():
    seen = []
    act("Hello?", None, llm=scripted("Hi.", seen=seen))
    assert "talk_ratio" not in seen[0]["tools"] and "get_transcript" not in seen[0]["tools"]


def test_reasoning_details_are_echoed_back_unchanged():
    seen = []
    act("Ratio?", FOUNDER, llm=scripted([("talk_ratio", {"interview_id": "interview_01"})], "Done.", seen=seen))
    assistant = seen[1]["messages"][-2]
    assert assistant["role"] == "assistant"
    assert assistant["reasoning_details"] == [{"type": "reasoning.encrypted", "data": "opaque"}]


def test_every_model_down_returns_the_routers_sentence_and_runs_nothing():
    down = lambda messages, schemas: {"content": "Groundwork cannot reach its models right now.",  # noqa: E731
                                      "tool_calls": [], "degraded": True}
    reply = act("Anything", FOUNDER, llm=down)
    assert reply.status == "stopped" and reply.calls == [] and "cannot reach" in reply.text


def test_as_assistant_without_reasoning_details_adds_no_key():
    msg = as_assistant({"content": None, "tool_calls": [{"id": "x", "name": "talk_ratio", "arguments": "{}"}]})
    assert "reasoning_details" not in msg


# ---------------------------------------------------------------- POST /act

def test_the_endpoint_takes_the_caller_from_the_header_not_the_model(monkeypatch):
    from src import app as app_module
    seen_callers = []
    real_call_tool = act_module.call_tool
    monkeypatch.setattr(act_module, "call_tool",
                        lambda call, allowed, caller: seen_callers.append(caller) or real_call_tool(call, allowed, caller))
    model = scripted([("talk_ratio", {"interview_id": "interview_01", "founder": "founder-2"})],
                     [("talk_ratio", {"interview_id": "interview_01"})], "40:60.")
    monkeypatch.setattr(app_module, "act", lambda q, caller=None: act(q, caller, llm=model))
    r = TestClient(app).post("/act", json={"question": "Ratio for interview 1?"}, headers={"X-Founder": FOUNDER})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "answered" and seen_callers == [FOUNDER, FOUNDER]
    assert not body["calls"][0]["ok"] and "founder" in body["calls"][0]["error"]   # identity in the args: refused
    assert body["calls"][1]["ok"] and body["calls"][1]["result"]["ratio"] == "40:60"


def test_the_endpoint_refuses_a_bad_body():
    client = TestClient(app)
    assert client.post("/act", json={"question": "hi"}).status_code == 422
    assert client.post("/act", json={"question": "Hello there", "founder": "x"}).status_code == 422
