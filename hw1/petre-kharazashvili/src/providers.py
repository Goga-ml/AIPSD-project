"""LLM providers behind one interface: an async generator that yields text chunks.

    async for chunk in provider(system_prompt, hypothesis, usage): ...

`usage` is filled in when the stream ends. Failures raise ProviderError with a message
that is safe to show to the founder (never the key, never a stack trace).
"""

import asyncio
import json
import os
from dataclasses import dataclass
from typing import AsyncIterator, Callable

import httpx
from google import genai

MAX_OUTPUT_TOKENS = 300
# USD per 1M tokens (input, output), ai.google.dev/gemini-api/docs/pricing, valid through 2026-12-31.
PRICES = {"gemini-3.8-flash": (0.75, 3.75)}

MOCK_OUTPUT = (
    "VERDICT: VAGUE\n"
    "REASON: \"Farmers\" is not a specific segment, \"want\" is an opinion rather than a behavior, "
    "and there is no threshold that could prove it wrong.\n"
    "REWRITE: At least [6] of [10] [smallholder vegetable farmers in Imereti] we interview will report "
    "[losing part of a harvest to late pest detection] in the past [12 months].\n"
)
MOCK_CHUNK_CHARS = 8
MOCK_DELAY_S = 0.02


class ProviderError(Exception):
    """A provider failed; the message is shown to the founder."""


@dataclass
class Usage:
    model: str
    input_tokens: int = 0
    output_tokens: int = 0  # includes thinking tokens, which are billed as output

    def cost_usd(self) -> float | None:
        if self.model.startswith("mock") or self.model.startswith("ollama:"):
            return 0.0
        if self.model not in PRICES:
            return None
        price_in, price_out = PRICES[self.model]
        return (self.input_tokens * price_in + self.output_tokens * price_out) / 1_000_000


Provider = Callable[[str, str, Usage], AsyncIterator[str]]


async def stream_mock(system: str, hypothesis: str, usage: Usage) -> AsyncIterator[str]:
    for i in range(0, len(MOCK_OUTPUT), MOCK_CHUNK_CHARS):
        await asyncio.sleep(MOCK_DELAY_S)
        yield MOCK_OUTPUT[i : i + MOCK_CHUNK_CHARS]


async def stream_gemini(system: str, hypothesis: str, usage: Usage) -> AsyncIterator[str]:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ProviderError("GEMINI_API_KEY is not set on the server.")
    client = genai.Client(api_key=key)
    try:
        stream = await client.aio.interactions.create(
            model=usage.model,
            system_instruction=system,
            input=hypothesis,
            generation_config={"max_output_tokens": MAX_OUTPUT_TOKENS, "thinking_level": "minimal"},
            stream=True,
        )
        async with stream:
            async for event in stream:
                if event.event_type == "step.delta" and getattr(event.delta, "type", None) == "text":
                    yield event.delta.text
                elif event.event_type == "interaction.completed" and event.interaction.usage:
                    u = event.interaction.usage
                    usage.input_tokens = u.total_input_tokens or 0
                    usage.output_tokens = (u.total_output_tokens or 0) + (u.total_thought_tokens or 0)
                elif event.event_type == "error":
                    message = event.error.message if event.error else "unknown error"
                    raise ProviderError(f"Gemini returned an error: {message}")
    except ProviderError:
        raise
    except httpx.HTTPError as e:
        raise ProviderError(f"Couldn't reach Gemini ({type(e).__name__}). Check the network.") from e
    except Exception as e:
        raise ProviderError(_gemini_message(e)) from e


def _gemini_message(e: Exception) -> str:
    status = getattr(e, "status_code", None)
    # Gemini answers a bad key with 400 INVALID_ARGUMENT "API key not valid", not 401.
    if status in (401, 403) or "API key" in str(e):
        return "Gemini rejected the API key. Check GEMINI_API_KEY on the server."
    if status == 404:
        return "Gemini doesn't know that model. Check GROUNDWORK_CHAT_MODEL."
    if status == 429:
        return "Gemini rate limit or free-tier quota reached. Try again in a minute."
    detail = str(getattr(e, "message", "") or e)[:200]
    return f"Gemini request failed ({status or type(e).__name__}): {detail}"


async def stream_ollama(system: str, hypothesis: str, usage: Usage) -> AsyncIterator[str]:
    base = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    body = {
        "model": usage.model.removeprefix("ollama:"),
        "stream": True,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": hypothesis}],
        "options": {"temperature": 0.1, "num_predict": MAX_OUTPUT_TOKENS},
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, read=120.0)) as client:
            async with client.stream("POST", f"{base}/api/chat", json=body) as resp:
                if resp.status_code != 200:
                    detail = (await resp.aread()).decode(errors="replace")[:200]
                    raise ProviderError(f"Ollama returned HTTP {resp.status_code}: {detail}")
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    if "error" in data:
                        raise ProviderError(f"Ollama returned an error: {data['error']}")
                    if piece := data.get("message", {}).get("content"):
                        yield piece
                    if data.get("done"):
                        usage.input_tokens = data.get("prompt_eval_count", 0)
                        usage.output_tokens = data.get("eval_count", 0)
    except httpx.ConnectError as e:
        raise ProviderError(f"Can't reach Ollama at {base}. Is it running?") from e
    except httpx.HTTPError as e:
        raise ProviderError(f"Ollama request failed ({type(e).__name__}).") from e
    except ValueError as e:
        raise ProviderError("Ollama sent a reply that isn't valid JSON.") from e


def get_provider() -> tuple[Provider, str]:
    """Return (provider, model name) from LLM_PROVIDER. Defaults to the mock, which costs nothing."""
    name = os.environ.get("LLM_PROVIDER", "mock").strip().lower()
    if name == "gemini":
        return stream_gemini, os.environ.get("GROUNDWORK_CHAT_MODEL", "gemini-3.8-flash")
    if name == "ollama":
        return stream_ollama, "ollama:" + os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
    if name == "mock":
        return stream_mock, "mock"
    raise ProviderError(f"LLM_PROVIDER must be gemini, ollama or mock, not {name!r}.")
