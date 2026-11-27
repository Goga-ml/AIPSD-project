"""The only file that talks to a model. Every call writes one line to logs/usage.jsonl.

one_call(messages, tools, timeout=..., model=...) is the shape Lab 8's router expects:

    -> {"content": str | None,
        "tool_calls": [{"id", "name", "arguments"}],     # arguments is a JSON string
        "usage": {"tokens_in", "tokens_out", "cost_usd"}}

Provider (decision 0003 keeps Gemini as the default):
  * OPENROUTER_API_KEY set -> OpenRouter, model ids like "google/gemini-3.8-flash".
    Needed for a fallback chain across two companies (Lab 8).
  * otherwise GEMINI_API_KEY -> Gemini's OpenAI-compatible endpoint, model ids like "gemini-3.8-flash".

The model only ASKS for tools; src/act.py decides whether anything runs.
The client is built lazily: importing this module needs no key, so tests run offline.
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

CHAT_MODEL = os.environ.get("GROUNDWORK_CHAT_MODEL", "gemini-3.8-flash")
# USD per 1M tokens, used when the provider does not report cost (Gemini direct). Decision 0003.
PRICE_IN = float(os.environ.get("GROUNDWORK_CHAT_PRICE_IN", "0.75"))
PRICE_OUT = float(os.environ.get("GROUNDWORK_CHAT_PRICE_OUT", "3.75"))

_client = None


def _log_path() -> Path:
    return Path(os.environ.get("GROUNDWORK_USAGE_LOG", "logs/usage.jsonl"))


def _get_client():
    """Build the client once, on first use. Raises if no key is set."""
    global _client
    if _client is None:
        from openai import OpenAI

        if os.environ.get("OPENROUTER_API_KEY"):
            _client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=os.environ["OPENROUTER_API_KEY"])
        elif os.environ.get("GEMINI_API_KEY"):
            _client = OpenAI(base_url=GEMINI_BASE_URL, api_key=os.environ["GEMINI_API_KEY"])
        else:
            raise RuntimeError("Set OPENROUTER_API_KEY or GEMINI_API_KEY in your environment (never in a file)")
    return _client


def log_usage(feature: str, model: str, tokens_in: int, tokens_out: int, cost_usd: float, latency_ms: int) -> None:
    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    line = {
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "feature": feature,
        "model": model,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": round(cost_usd, 6),
        "latency_ms": latency_ms,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")


def one_call(messages: list[dict], tools: list[dict] | None = None, timeout: float | None = None,
             model: str | None = None, feature: str = "chat") -> dict:
    """One model turn. With a timeout, the SDK's own retries are off: the caller (router) owns retrying."""
    model = model or CHAT_MODEL
    api = _get_client()
    if timeout is not None:
        api = api.with_options(timeout=timeout, max_retries=0)

    t0 = time.perf_counter()
    reply = api.chat.completions.create(model=model, messages=messages, **({"tools": tools} if tools else {}))
    latency_ms = round((time.perf_counter() - t0) * 1000)

    message = reply.choices[0].message
    calls = [{"id": c.id, "name": c.function.name, "arguments": c.function.arguments or "{}"}
             for c in (message.tool_calls or [])]

    usage = reply.usage
    tokens_in = getattr(usage, "prompt_tokens", 0) or 0
    tokens_out = getattr(usage, "completion_tokens", 0) or 0
    cost = getattr(usage, "cost", None)  # OpenRouter reports dollars; Gemini direct does not
    if cost is None:
        cost = (tokens_in * PRICE_IN + tokens_out * PRICE_OUT) / 1_000_000

    log_usage(feature, model, tokens_in, tokens_out, cost, latency_ms)
    return {"content": message.content, "tool_calls": calls,
            "usage": {"tokens_in": tokens_in, "tokens_out": tokens_out, "cost_usd": cost}}
