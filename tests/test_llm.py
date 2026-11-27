"""one_call() returns the shape the router expects and logs one usage line, with a fake client."""
import json
import os
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from src import llm


class FakeClient:
    def __init__(self, reply):
        self.reply = reply
        self.sent = None
        self.options = None
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, **kwargs):
        self.sent = kwargs
        return self.reply

    def with_options(self, **kwargs):
        self.options = kwargs
        return self


def make_reply(content="hi", tool_calls=None, cost=None):
    usage = NS(prompt_tokens=100, completion_tokens=20)
    if cost is not None:
        usage.cost = cost
    return NS(choices=[NS(message=NS(content=content, tool_calls=tool_calls))], usage=usage)


@pytest.fixture
def fake(monkeypatch):
    def install(reply):
        client = FakeClient(reply)
        monkeypatch.setattr(llm, "_client", client)
        return client
    return install


def last_log_line() -> dict:
    lines = Path(os.environ["GROUNDWORK_USAGE_LOG"]).read_text(encoding="utf-8").splitlines()
    return json.loads(lines[-1])


def test_importing_needs_no_key_and_calling_without_one_fails_loudly(monkeypatch):
    monkeypatch.setattr(llm, "_client", None)
    with pytest.raises(RuntimeError, match="API_KEY"):
        llm.one_call([{"role": "user", "content": "hi"}])


def test_plain_answer_has_router_shape_and_logs_one_line(fake):
    fake(make_reply("hello"))
    out = llm.one_call([{"role": "user", "content": "hi"}], model="m1", feature="ask")
    assert out["content"] == "hello"
    assert out["tool_calls"] == []
    assert out["usage"]["tokens_in"] == 100 and out["usage"]["tokens_out"] == 20
    line = last_log_line()
    assert line["feature"] == "ask" and line["model"] == "m1"
    assert line["cost_usd"] == pytest.approx((100 * llm.PRICE_IN + 20 * llm.PRICE_OUT) / 1_000_000, abs=1e-6)


def test_provider_reported_cost_wins(fake):
    fake(make_reply(cost=0.0042))
    out = llm.one_call([{"role": "user", "content": "hi"}])
    assert out["usage"]["cost_usd"] == 0.0042


def test_tool_calls_come_back_as_plain_dicts(fake):
    call = NS(id="c1", function=NS(name="get_transcript", arguments='{"interview_id": "i01"}'))
    client = fake(make_reply(content=None, tool_calls=[call]))
    tools = [{"type": "function", "function": {"name": "get_transcript"}}]
    out = llm.one_call([{"role": "user", "content": "x"}], tools)
    assert out["tool_calls"] == [{"id": "c1", "name": "get_transcript", "arguments": '{"interview_id": "i01"}'}]
    assert client.sent["tools"] == tools


def test_timeout_turns_sdk_retries_off(fake):
    client = fake(make_reply())
    llm.one_call([{"role": "user", "content": "hi"}], timeout=7)
    assert client.options == {"timeout": 7, "max_retries": 0}
    assert "tools" not in client.sent
