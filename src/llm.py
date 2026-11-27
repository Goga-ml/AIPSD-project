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
    # Gemini 3 through OpenRouter sends reasoning_details with a tool turn and rejects the next call
    # unless they are echoed back unchanged (src/act.py, as_assistant). Absent elsewhere: None.
    reasoning = getattr(message, "reasoning_details", None) or (getattr(message, "model_extra", None) or {}).get("reasoning_details")
    return {"content": message.content, "tool_calls": calls, "reasoning_details": reasoning,
            "usage": {"tokens_in": tokens_in, "tokens_out": tokens_out, "cost_usd": cost}}


# ---------------------------------------------------------------- embeddings (Task 4)
# Through google-genai, as in HW1, because the OpenAI-compatible endpoint has no task_type and
# decision 0002's 0.65 threshold was measured with RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY.
# The router (src/router.py) has chat jobs only, so embeddings are the one model call that does not
# go through complete(); they still log one line per request to logs/usage.jsonl.

EMBED_MODEL = os.environ.get("GROUNDWORK_EMBED_MODEL", "gemini-embedding-001")
PRICE_EMBED_IN = float(os.environ.get("GROUNDWORK_EMBED_PRICE_IN", "0.15"))
EMBED_BATCH = 100      # texts per request
MAX_EMBED_CALLS = 10   # hard cap per call: refuse to embed more than 1,000 new texts


def _cache_file() -> Path:
    return Path(os.environ.get("GROUNDWORK_EMBED_CACHE", ".cache/embeddings.json"))  # git-ignored


def embed(texts: list[str], task_type: str) -> list[list[float]]:
    """Embed texts, reusing a disk cache: transcripts rarely change, and the free tier allows 100 requests a minute."""
    import hashlib

    path = _cache_file()
    cache = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    keys = [hashlib.sha256(f"{EMBED_MODEL}\n{task_type}\n{t}".encode("utf-8")).hexdigest() for t in texts]
    missing = list({k: t for k, t in zip(keys, texts) if k not in cache}.items())
    if len(missing) > EMBED_BATCH * MAX_EMBED_CALLS:
        raise RuntimeError(f"refusing to embed {len(missing)} texts (cap {EMBED_BATCH * MAX_EMBED_CALLS})")
    if missing:
        from google import genai
        from google.genai import types

        if not os.environ.get("GEMINI_API_KEY"):
            raise RuntimeError("Embeddings need GEMINI_API_KEY in your environment (never in a file)")
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        for start in range(0, len(missing), EMBED_BATCH):
            batch = missing[start:start + EMBED_BATCH]
            t0 = time.perf_counter()
            resp = client.models.embed_content(model=EMBED_MODEL, contents=[t for _, t in batch],
                                               config=types.EmbedContentConfig(task_type=task_type))
            for (k, _), e in zip(batch, resp.embeddings):
                cache[k] = e.values
            tokens_in = sum(len(t) for _, t in batch) // 4   # the API returns no count: ~4 characters per token
            log_usage("embed", EMBED_MODEL, tokens_in, 0, tokens_in * PRICE_EMBED_IN / 1_000_000,
                      round((time.perf_counter() - t0) * 1000))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cache), encoding="utf-8")
    return [cache[k] for k in keys]
