"""Lab 7: the supervised loop, from the course starter (Lab-7/templates/agent_starter.py). Contract: docs/agent-contract.md.

Three ideas, and nothing else:
  the loop    ask the model "what next?", run the read-only tool it asks for, show it the result, repeat
  the stop    at most MAX_STEPS model turns, then the loop ends and says so
  the yes     a tool in NEEDS_YES is never run by the loop. It is parked. confirm() runs it when the
              founder says yes, and no model is involved in that.

Ours, beyond the starter: every model call goes through complete() (src/router.py); a proposal whose
arguments fail the contract is not parked (the model reads why); NEEDS_YES tools live in PROPOSE_ONLY,
outside TOOLS, so no other door can run them.
"""
from __future__ import annotations

import json

from pydantic import ValidationError

from . import memory
from .act import as_assistant, brief, call_tool
from .tools import PROPOSE_ONLY, tools_for

GOAL_PROMPT = """You help a founder collect evidence for or against their hypothesis from their customer interviews.
Work in steps: search the interviews (ask_interviews, get_transcript), check each quote (verify_quote),
then propose saving the strongest verified Customer quotes with save_evidence, at most five.
A proposed save is NOT done: the founder must confirm it. Never say it is saved.
Finish with two or three sentences: what you proposed and why."""

LOOP_TOOLS = ("ask_interviews", "get_transcript", "verify_quote", "save_evidence")   # only what the goal needs
NEEDS_YES = {"save_evidence"}            # it writes to the founder's evidence board: they decide what counts
MAX_STEPS = 6                            # the stop

PENDING: dict[str, list[dict]] = {}      # founder -> parked actions. In memory: a plan dies with the process.


def facts(user: str) -> str:
    """Facts our code already knows go into the prompt; the model is not asked to guess them."""
    seg = memory.focus(user)
    return f"The founder's focus segment: {seg}." if seg else "The founder has not set a focus segment."


def describe(call: dict) -> str:
    """One line the founder reads before saying yes."""
    try:
        a = json.loads(call["arguments"])
        return f"Save as {a['kind']}: \"{a['quote']}\" ({a['interview_id']})"
    except (ValueError, KeyError, TypeError):
        return f"{call['name']} {call['arguments']}"


def run(goal: str, user: str, llm=None, max_steps: int = MAX_STEPS) -> dict:
    if llm is None:
        from .router import complete
        llm = complete
    allowed = {name: tool for name, tool in {**tools_for(user), **PROPOSE_ONLY}.items() if name in LOOP_TOOLS}
    schemas = [tool.schema() for tool in allowed.values()]
    messages = [{"role": "system", "content": GOAL_PROMPT + "\n" + facts(user)}, {"role": "user", "content": goal}]
    proposed, trace = [], []
    for step in range(1, max_steps + 1):
        msg = llm(messages, schemas)                                  # REASON: what next?
        if msg.get("degraded"):                                       # every model down: stop, nothing parked
            return finish("stopped", msg["content"], user, [], trace)
        if not msg.get("tool_calls"):                                 # the model says it is done
            return finish("needs_confirmation" if proposed else "answered", msg.get("content") or "", user, proposed, trace)
        messages.append(as_assistant(msg))
        for call in msg["tool_calls"]:
            parked = False
            if call["name"] in NEEDS_YES and call["name"] in allowed:  # ACT, needs a yes: check, then park
                try:
                    allowed[call["name"]].args.model_validate_json(call["arguments"] or "{}")
                except ValidationError as e:
                    observation = {"error": f"invalid arguments: {brief(e)}. Not added to the plan."}
                else:
                    action = {"id": f"a{len(proposed) + 1}", "tool": call["name"],
                              "arguments": call["arguments"], "summary": describe(call)}
                    proposed.append(action)
                    parked = True
                    observation = {"status": "added to the plan; NOT done. The founder will confirm.",
                                   "summary": action["summary"]}
            else:                                                     # ACT, a read: run it through the gates
                outcome = call_tool(call, allowed, user)
                observation = outcome["result"] if outcome["ok"] else {"error": outcome["error"]}
            trace.append({"step": step, "tool": call["name"], "parked": parked})
            messages.append({"role": "tool", "tool_call_id": call["id"],              # OBSERVE
                             "content": json.dumps(observation)})
    return finish("stopped", f"I stopped after {max_steps} steps. Nothing was saved.", user, proposed, trace)


def finish(status: str, text: str, user: str, proposed: list[dict], trace: list[dict]) -> dict:
    PENDING[user] = proposed                                          # parked until the founder answers
    return {"status": status, "text": text, "proposed": proposed, "trace": trace}


def confirm(user: str, approved_ids: list[str]) -> list[dict]:
    """The founder said yes. Run exactly what was parked for THIS founder, once. No model here."""
    actions = PENDING.pop(user, [])                                   # pop: a plan works once
    return [{"id": a["id"], **call_tool({"id": a["id"], "name": a["tool"], "arguments": a["arguments"]}, PROPOSE_ONLY, user)}
            for a in actions if a["id"] in approved_ids]
