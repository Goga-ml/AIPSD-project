"""Every model call goes through here: Gemini client, embedding cache, and usage (tokens, cost, latency).

The key comes only from the GEMINI_API_KEY environment variable. Tests never import make_gemini.
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

CHAT_MODEL = os.environ.get("GROUNDWORK_CHAT_MODEL", "gemini-3.8-flash")
EMBED_MODEL = os.environ.get("GROUNDWORK_EMBED_MODEL", "gemini-embedding-001")
# USD per 1M tokens. Defaults match the napkin math in spec.md; override if the team picks other models.
PRICE_CHAT_IN = float(os.environ.get("GROUNDWORK_CHAT_PRICE_IN", "0.75"))
PRICE_CHAT_OUT = float(os.environ.get("GROUNDWORK_CHAT_PRICE_OUT", "3.75"))
PRICE_EMBED_IN = float(os.environ.get("GROUNDWORK_EMBED_PRICE_IN", "0.15"))

CACHE_FILE = Path(__file__).resolve().parent / ".embed_cache.json"  # git-ignored
EMBED_BATCH = 100  # texts per embedding request
MAX_EMBED_CALLS = 10  # hard cap per run: refuse to embed more than 1,000 chunks


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


class Usage:
    def __init__(self):
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.cost_usd = 0.0
        self.latency_ms = 0

    def add(self, kind: str, tokens_in: int, tokens_out: int, latency_s: float,
            price_in: float, price_out: float = 0.0) -> None:
        cost = (tokens_in * price_in + tokens_out * price_out) / 1_000_000
        self.calls += 1
        self.input_tokens += tokens_in
        self.output_tokens += tokens_out
        self.cost_usd += cost
        self.latency_ms += round(latency_s * 1000)
        log(f"llm {kind}: {tokens_in} in / {tokens_out} out, ${cost:.6f}, {latency_s * 1000:.0f} ms")

    def as_dict(self) -> dict:
        return {
            "model": CHAT_MODEL,
            "embed_model": EMBED_MODEL,
            "calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "latency_ms": self.latency_ms,
        }


def make_gemini(usage: Usage, system_prompt: str):
    """Return (embed, generate) functions that call Gemini and record usage."""
    from google import genai
    from google.genai import types

    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is not set")
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    # Transcripts rarely change, so embeddings are cached on disk and each question
    # only embeds what is new. Without this, every run re-embeds all chunks and hits
    # the free-tier limit of 100 embedding requests per minute after one question.
    cache = json.loads(CACHE_FILE.read_text(encoding="utf-8")) if CACHE_FILE.exists() else {}

    def cache_key(text: str, task_type: str) -> str:
        return hashlib.sha256(f"{EMBED_MODEL}\n{task_type}\n{text}".encode("utf-8")).hexdigest()

    def embed(texts: list[str], task_type: str) -> np.ndarray:
        keys = [cache_key(t, task_type) for t in texts]
        missing = list({k: t for k, t in zip(keys, texts) if k not in cache}.items())
        if len(missing) > EMBED_BATCH * MAX_EMBED_CALLS:
            raise RuntimeError(f"refusing to embed {len(missing)} texts (cap {EMBED_BATCH * MAX_EMBED_CALLS})")
        for start in range(0, len(missing), EMBED_BATCH):
            batch = missing[start:start + EMBED_BATCH]
            t0 = time.perf_counter()
            resp = client.models.embed_content(
                model=EMBED_MODEL, contents=[t for _, t in batch],
                config=types.EmbedContentConfig(task_type=task_type),
            )
            for (k, _), e in zip(batch, resp.embeddings):
                cache[k] = e.values
            # The embedding API returns no token count, so estimate ~4 characters per token.
            usage.add("embed", sum(len(t) for _, t in batch) // 4, 0, time.perf_counter() - t0, PRICE_EMBED_IN)
        if missing:
            CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")
            log(f"embedded {len(missing)} new texts, {len(texts) - len(missing)} from cache")
        return np.array([cache[k] for k in keys])

    def generate(prompt: str) -> str:
        t0 = time.perf_counter()
        resp = client.models.generate_content(
            model=CHAT_MODEL, contents=prompt,
            config=types.GenerateContentConfig(system_instruction=system_prompt, temperature=0),
        )
        meta = resp.usage_metadata
        tokens_out = (meta.candidates_token_count or 0) + (meta.thoughts_token_count or 0)  # thinking bills as output
        usage.add("chat", meta.prompt_token_count or 0, tokens_out, time.perf_counter() - t0,
                  PRICE_CHAT_IN, PRICE_CHAT_OUT)
        return resp.text or ""

    return embed, generate
