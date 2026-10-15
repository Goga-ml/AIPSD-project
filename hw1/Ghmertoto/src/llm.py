"""The only place that talks to a model provider (Gemini via google-genai).

Every call logs tokens, cost and latency to stderr (never the prompt text) and adds
to `usage`, which coach.py puts in its output (INTERFACES section 5).
Prices are assumptions until INTERFACES section 1 is filled; override them by env.
"""

import os
import sys
import time

from classifier import ModelUnavailable


class LLMConfigError(ModelUnavailable):
    pass


class GeminiClient:
    def __init__(self) -> None:
        self.model = os.environ.get("GROUNDWORK_CHAT_MODEL", "gemini-2.5-flash")
        self.price_in = float(os.environ.get("GROUNDWORK_PRICE_IN", "0.30"))    # USD per 1M tokens
        self.price_out = float(os.environ.get("GROUNDWORK_PRICE_OUT", "2.50"))  # USD per 1M tokens
        self.usage = {"model": self.model, "calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
        self._client = None

    def _connect(self):
        if self._client is None:
            key = os.environ.get("GEMINI_API_KEY")
            if not key:
                raise LLMConfigError("GEMINI_API_KEY is not set")
            from google import genai  # lazy: tests and --no-llm runs never need it
            self._client = genai.Client(api_key=key)
        return self._client

    def generate(self, prompt: str) -> str:
        from google.genai import types

        client = self._connect()
        start = time.perf_counter()
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(thinking_budget=0),  # predictable cost
            ),
        )
        latency_ms = (time.perf_counter() - start) * 1000

        meta = response.usage_metadata
        tokens_in = meta.prompt_token_count or 0
        tokens_out = (meta.candidates_token_count or 0) + (meta.thoughts_token_count or 0)
        cost = (tokens_in * self.price_in + tokens_out * self.price_out) / 1_000_000
        self.usage["calls"] += 1
        self.usage["input_tokens"] += tokens_in
        self.usage["output_tokens"] += tokens_out
        self.usage["cost_usd"] = round(self.usage["cost_usd"] + cost, 6)
        print(f"llm: {self.model} in={tokens_in} out={tokens_out} cost=${cost:.5f} "
              f"latency={latency_ms:.0f}ms", file=sys.stderr)
        return response.text or ""
