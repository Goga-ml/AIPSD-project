"""One conversational turn (Lab 6): remembered context in, streamed answer out, state written back.

  1. context: the system prompt with this founder's focus segment, the last few turns of THIS session,
     then the new question. Six turns at most (memory.MAX_TURNS).
  2. stream the reply through the router (src/router.py, stream()) as it arrives.
  3. if the model asked for a tool, run it through call_tool() (offered? valid? identity from us), then
     stream one more round with the result. One round: a chat turn is a conversation, not a plan.
  4. write back the two turns, and only the two turns. The focus is written only by the remember_focus
     tool, which the founder has to ask for.

Yields events the endpoint turns into Server-Sent Events: ("token", text), ("tool", outcome), ("done", summary).
"""
from __future__ import annotations

import json
from typing import Iterator

from . import memory
from .act import as_assistant, call_tool
from .tools import tools_for

SYSTEM = """You are Groundwork, a customer-discovery assistant for an early-stage founder.
Answer in two or three short sentences. Use a tool when the question needs the founder's interviews.
Cite transcript lines exactly as the tools return them, like [interview_01:L11]. Never invent a quote.
If the founder asks you to remember the segment they are focusing on and you have the remember_focus tool,
call it once; never remember anything they did not ask you to.
The founder's focus segment: {focus}"""


def build_messages(session: str | None, founder: str | None, question: str) -> list[dict]:
    seg = memory.focus(founder) if founder else None
    msgs = [{"role": "system", "content": SYSTEM.format(focus=seg or "none set")}]
    if session:
        msgs += memory.recent_turns(session)                 # scope: this session only
    msgs.append({"role": "user", "content": question})
    return msgs


def chat_turn(question: str, session: str | None = None, founder: str | None = None,
              open_stream=None) -> Iterator[tuple[str, object]]:
    from .router import stream as router_stream
    open_stream = open_stream or router_stream
    allowed = tools_for(founder)
    schemas = [t.schema() for t in allowed.values()]
    messages = build_messages(session, founder, question)
    s = open_stream(messages, schemas)
    for piece in s:
        yield "token", piece
    streams, calls = [s], []
    if s.tool_calls:                                          # the model asked; our code decides
        messages.append(as_assistant({"content": s.text or None, "tool_calls": s.tool_calls,
                                      "reasoning_details": s.reasoning_details}))
        for call in s.tool_calls:
            outcome = call_tool(call, allowed, founder)
            calls.append(outcome)
            yield "tool", {"tool": outcome["tool"], "ok": outcome["ok"], "error": outcome["error"]}
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "content": json.dumps(outcome["result"] if outcome["ok"] else {"error": outcome["error"]})})
        s2 = open_stream(messages, schemas)
        for piece in s2:
            yield "token", piece
        streams.append(s2)
    answer = streams[-1].text
    if session and not any(x.degraded for x in streams):     # the sorry sentence is not a turn worth keeping
        memory.add_turn(session, "user", question)
        memory.add_turn(session, "assistant", answer)
    yield "done", {"ttft_ms": s.ttft_ms, "calls": len(calls),
                   "tokens_in": sum(x.tokens_in for x in streams), "tokens_out": sum(x.tokens_out for x in streams),
                   "cost_usd": round(sum(x.cost_usd for x in streams), 6),
                   "degraded": any(x.degraded for x in streams)}
