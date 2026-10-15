"""The only file that talks to Gemini. Every call logs tokens, cost and latency to stderr.

Key: GEMINI_API_KEY (environment only, never a file).
Model: GROUNDWORK_CHAT_MODEL, default gemini-3.8-flash.
Importing this module needs no key and makes no network call (tests rely on that).
"""
import json
import os
import sys
import time

MODEL = os.environ.get("GROUNDWORK_CHAT_MODEL", "gemini-3.8-flash")

# USD per 1M tokens (input, output). Output includes thinking tokens.
# Checked on ai.google.dev/gemini-api/docs/pricing, 15 Oct 2026 (paid tier, standard).
# gemini-3.8-flash: 0.75 / 3.75 until 31 Dec 2026, then 1.50 / 7.50. Re-check before relying on it.
PRICES = {
    "gemini-3.8-flash": (0.75, 3.75),
    "gemini-3.5-flash-lite": (0.30, 2.50),
}


def price(model: str) -> tuple[float, float]:
    if "GROUNDWORK_PRICE_IN" in os.environ:  # manual override for a model not in the table
        return float(os.environ["GROUNDWORK_PRICE_IN"]), float(os.environ.get("GROUNDWORK_PRICE_OUT", "0"))
    if model not in PRICES:
        raise RuntimeError(f"No price for {model!r}: add it to PRICES or set GROUNDWORK_PRICE_IN/OUT")
    return PRICES[model]


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    p_in, p_out = price(model)
    return round((tokens_in * p_in + tokens_out * p_out) / 1_000_000, 6)


def complete_json(system: str, user: str, schema) -> tuple[str, dict]:
    """One Gemini call that asks for JSON shaped like `schema` (a pydantic model).

    Returns the raw reply text (the caller validates it) and one usage dict.
    """
    from google import genai
    from google.genai import types

    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is not set")
    client = genai.Client()  # reads GEMINI_API_KEY from the environment
    t0 = time.perf_counter()
    resp = client.models.generate_content(
        model=MODEL,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )
    um = resp.usage_metadata
    tokens_in = um.prompt_token_count or 0
    tokens_out = (um.candidates_token_count or 0) + (um.thoughts_token_count or 0)
    usage = {
        "model": MODEL,
        "input_tokens": tokens_in,
        "output_tokens": tokens_out,
        "cost_usd": cost_usd(MODEL, tokens_in, tokens_out),
        "latency_ms": round((time.perf_counter() - t0) * 1000),
    }
    print("model_call " + json.dumps(usage), file=sys.stderr)
    return resp.text or "", usage
