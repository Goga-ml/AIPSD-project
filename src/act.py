"""call_tool(): the model asks for a tool, our code decides whether it runs. Spec: docs/tool-contracts.md.

Three gates, in order:
  1. offered?   the tool is in the set this caller was given by tools_for(caller)
  2. valid?     the arguments pass the contract (extra="forbid", patterns, bounds)
  3. identity   the caller comes from the session and is passed in here, never from the arguments

call_tool() never raises. It returns {ok, error, result, ...} and writes one line to logs/tools.jsonl.
The model loop is not here: every model call goes through complete() in src/router.py.
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from .tools import Tool, ToolFailure, caller_key

FREE_TEXT: set[str] = {"hypothesis", "rewrite"}     # customers' or founders' words: logged as a length, never as text


def _log_path() -> Path:
    return Path(os.environ.get("GROUNDWORK_TOOL_LOG", "logs/tools.jsonl"))


def brief(e: ValidationError) -> str:
    """Which field and what was wrong, for the model. No stack trace, no input echoed back."""
    return "; ".join(f"{'.'.join(map(str, x['loc'])) or 'arguments'}: {x['msg']}" for x in e.errors())


def call_tool(call: dict, allowed: dict[str, Tool], caller: str | None) -> dict:
    t0 = time.perf_counter()
    tool = allowed.get(call.get("name"))
    if tool is None:                                                          # gate 1 · offered?
        return _log(call, caller, t0, error=f"no tool named {call.get('name')!r} is available")
    try:
        args = tool.args.model_validate_json(call.get("arguments") or "{}")    # gate 2 · valid?
    except ValidationError as e:
        return _log(call, caller, t0, error=f"invalid arguments: {brief(e)}")
    if tool.needs_caller and not caller:                                      # gate 3 · identity from the session
        return _log(call, caller, t0, error="not signed in: ask the founder to sign in first")
    try:
        out = tool.run(args, caller=caller) if tool.needs_caller else tool.run(args)
    except ToolFailure as e:
        return _log(call, caller, t0, error=str(e))
    except Exception:                                                         # a bug: logged, nothing leaked
        return _log(call, caller, t0, error="the tool failed unexpectedly; tell the founder and do not retry")
    return _log(call, caller, t0, result=out.model_dump(mode="json"))


def _safe_args(raw) -> dict | str:
    try:
        args = json.loads(raw or "{}")
    except (TypeError, ValueError):
        return f"<unparseable, {len(str(raw))} chars>"
    if not isinstance(args, dict):
        return "<not a JSON object>"
    return {k: (f"<{len(str(v))} chars>" if k in FREE_TEXT else v) for k, v in args.items()}


def _log(call: dict, caller: str | None, t0: float, result: dict | None = None, error: str | None = None) -> dict:
    line = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tool": call.get("name"),
            "arguments": _safe_args(call.get("arguments")), "ok": error is None, "error": error,
            "caller": caller_key(caller) if caller else None,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1)}
    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
    return {**line, "result": result}
