"""Hypothesis linter: GET / serves the form, POST /lint streams VERDICT / REASON / REWRITE (INTERFACES.md section 9)."""

import time
from contextlib import aclosing
from pathlib import Path
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")  # variables already set in the environment win

from llm import Provider, ProviderError, Usage, get_provider, log_usage  # noqa: E402
from parser import LintParser, ParseError  # noqa: E402

MAX_CHARS = 500
SYSTEM_PROMPT = (HERE / "prompt.txt").read_text(encoding="utf-8")

app = FastAPI(title="Groundwork hypothesis linter")


def error_response(status: int, message: str) -> PlainTextResponse:
    return PlainTextResponse(f"ERROR: {message}\n", status_code=status)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(HERE / "static" / "index.html")


@app.post("/lint")
async def lint(request: Request):
    try:
        body = await request.json()
    except ValueError:
        return error_response(400, 'Send JSON like {"hypothesis": "..."}.')
    hypothesis = body.get("hypothesis") if isinstance(body, dict) else None
    if not isinstance(hypothesis, str):
        return error_response(400, 'Send JSON like {"hypothesis": "..."}.')
    # The wire format is one line per field, so the hypothesis is collapsed onto one line.
    hypothesis = " ".join(hypothesis.split())
    if not hypothesis:
        return error_response(400, "Please enter a hypothesis.")
    if len(hypothesis) > MAX_CHARS:
        return error_response(400, f"The hypothesis is {len(hypothesis)} characters; the limit is {MAX_CHARS}.")

    try:
        provider, model = get_provider()
    except ProviderError as e:
        return error_response(500, str(e))
    chunks = lint_stream(provider, hypothesis, Usage(model))
    # Wait for the verdict line before answering, so an early failure is a proper non-200 response.
    try:
        first = await anext(chunks)
    except (ProviderError, ParseError) as e:
        await chunks.aclose()
        return error_response(502, str(e))
    except StopAsyncIteration:
        return error_response(502, "The model returned nothing.")
    return StreamingResponse(with_error_line(first, chunks), media_type="text/plain; charset=utf-8")


async def lint_stream(provider: Provider, hypothesis: str, usage: Usage) -> AsyncIterator[str]:
    """Provider chunks in, wire-format text out. Logs usage and cost however the stream ends."""
    parser = LintParser(hypothesis)
    started = time.monotonic()
    outcome = "stopped early (client disconnected)"
    try:
        async with aclosing(provider(SYSTEM_PROMPT, hypothesis, usage)) as model_chunks:
            async for chunk in model_chunks:
                if out := parser.feed(chunk):
                    yield out
        if out := parser.finish():
            yield out
        outcome = "ok"
    except (ProviderError, ParseError) as e:
        outcome = f"error: {e}"
        raise
    finally:
        log_usage(usage, outcome, parser.verdict, time.monotonic() - started)


async def with_error_line(first: str, rest: AsyncIterator[str]) -> AsyncIterator[str]:
    """Stream the rest after the first chunk; a mid-stream failure becomes a final ERROR line."""
    last = first
    yield first
    async with aclosing(rest):
        try:
            async for last in rest:
                yield last
        except (ProviderError, ParseError) as e:
            yield ("" if last.endswith("\n") else "\n") + f"ERROR: {e}\n"
