import asyncio
import threading
import time

import httpx
import pytest
from fastapi.testclient import TestClient

import app as app_module
from providers import ProviderError

client = TestClient(app_module.app)
COFFEE = (
    "At least 7 of 10 independent coffee shop owners we interview will report spending 3+ hours per week "
    "on staff scheduling, and at least 3 will agree to a paid pilot at $20/month."
)


# --- streaming (acceptance criterion 3) ---------------------------------------------------------

def test_mock_response_arrives_in_multiple_chunks_over_a_real_socket(live_server):
    chunks, times = [], []
    started = time.monotonic()
    with httpx.stream("POST", f"{live_server}/lint", json={"hypothesis": "Farmers want better tools"}) as res:
        assert res.status_code == 200
        assert res.headers["content-type"].startswith("text/plain")
        for chunk in res.iter_text():
            chunks.append(chunk)
            times.append(time.monotonic() - started)
    body = "".join(chunks)
    assert len(chunks) > 1
    assert chunks[0].startswith("VERDICT: vague\n")       # verdict comes first...
    assert times[-1] - times[0] > 0.2                     # ...well before the rest has finished
    lines = body.splitlines()
    assert [line.split(":")[0] for line in lines] == ["VERDICT", "REASON", "REWRITE"]


def test_closing_the_stream_stops_reading_from_the_provider(live_server, use_provider):
    closed = threading.Event()
    yielded = []

    async def slow_provider(system, hypothesis, usage):
        try:
            yield "VERDICT: VAGUE\nREASON: "
            for i in range(200):
                await asyncio.sleep(0.02)
                yielded.append(i)
                yield "word "
        finally:
            closed.set()

    use_provider(slow_provider)
    with httpx.stream("POST", f"{live_server}/lint", json={"hypothesis": "x"}) as res:
        next(res.iter_text())  # read the verdict, then hang up like the Stop button does
    assert closed.wait(timeout=3), "provider stream was not closed after the client disconnected"
    assert len(yielded) < 200


# --- input validation (acceptance criterion 3) --------------------------------------------------

@pytest.fixture
def spy_provider(use_provider):
    calls = []

    async def spy(system, hypothesis, usage):
        calls.append(hypothesis)
        yield "VERDICT: VAGUE\nREASON: r\nREWRITE: w\n"

    use_provider(spy)
    return calls


@pytest.mark.parametrize("hypothesis", ["", "   \n\t ", "x" * 501])
def test_bad_input_is_rejected_without_calling_the_provider(spy_provider, hypothesis):
    res = client.post("/lint", json={"hypothesis": hypothesis})
    assert res.status_code == 400
    assert res.text.startswith("ERROR: ")
    assert spy_provider == []


@pytest.mark.parametrize("body", [b"not json", b'{"text": "hi"}', b'["a"]'])
def test_malformed_body_is_rejected_without_calling_the_provider(spy_provider, body):
    res = client.post("/lint", content=body, headers={"content-type": "application/json"})
    assert res.status_code == 400
    assert spy_provider == []


def test_exactly_500_characters_is_accepted(spy_provider):
    res = client.post("/lint", json={"hypothesis": "x" * 500})
    assert res.status_code == 200
    assert spy_provider == ["x" * 500]


# --- errors (acceptance criterion 3) ------------------------------------------------------------

def test_provider_failure_before_streaming_is_a_readable_502(use_provider):
    async def broken(system, hypothesis, usage):
        raise ProviderError("Gemini rejected the API key. Check GEMINI_API_KEY on the server.")
        yield  # makes this an async generator

    use_provider(broken)
    res = client.post("/lint", json={"hypothesis": "Farmers want better tools"})
    assert res.status_code == 502
    assert res.text == "ERROR: Gemini rejected the API key. Check GEMINI_API_KEY on the server.\n"


def test_provider_failure_mid_stream_ends_with_an_error_line(use_provider):
    async def dies(system, hypothesis, usage):
        yield "VERDICT: VAGUE\nREASON: Half a sent"
        raise ProviderError("Couldn't reach Gemini (ReadTimeout). Check the network.")

    use_provider(dies)
    res = client.post("/lint", json={"hypothesis": "Farmers want better tools"})
    assert res.status_code == 200
    assert res.text.splitlines()[-1] == "ERROR: Couldn't reach Gemini (ReadTimeout). Check the network."


def test_model_that_ignores_the_format_is_a_readable_502(use_provider):
    async def chatty(system, hypothesis, usage):
        yield "Sure! This hypothesis is pretty vague, here's why..."

    use_provider(chatty)
    res = client.post("/lint", json={"hypothesis": "Farmers want better tools"})
    assert res.status_code == 502
    assert res.text.startswith("ERROR: The model's reply was missing VERDICT")


def test_missing_gemini_key_is_a_readable_502(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    res = client.post("/lint", json={"hypothesis": "Farmers want better tools"})
    assert res.status_code == 502
    assert res.text == "ERROR: GEMINI_API_KEY is not set on the server.\n"


# --- falsifiable passes unchanged (acceptance criterion 2) --------------------------------------

def test_falsifiable_hypothesis_comes_back_byte_identical(use_provider):
    async def passes(system, hypothesis, usage):
        yield "VERDICT: FALSIFIABLE\nREASON: All three criteria are met.\nREWRITE: UNCHANGED\n"

    use_provider(passes)
    res = client.post("/lint", json={"hypothesis": COFFEE})
    assert res.text.splitlines() == ["VERDICT: falsifiable", "REASON: All three criteria are met.", f"REWRITE: {COFFEE}"]


def test_index_serves_the_form():
    res = client.get("/")
    assert res.status_code == 200
    assert 'id="stop"' in res.text and "getReader" in res.text


def test_gemini_bad_key_error_is_readable():
    # Seen live: Gemini answers a bad key with HTTP 400 and a JSON blob, not 401.
    from providers import _gemini_message

    class FakeGenAiError(Exception):
        status_code = 400

    raw = "Error code: 400 - [{'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.'}}]"
    assert _gemini_message(FakeGenAiError(raw)) == "Gemini rejected the API key. Check GEMINI_API_KEY on the server."


def test_gemini_quota_error_keeps_googles_sentence_and_drops_the_json():
    # Seen live on the free tier.
    from providers import _gemini_message

    class FakeGenAiError(Exception):
        status_code = 429

    raw = (
        "Error code: 429 - {'error': {'message': 'Rate limit exceeded for model gemini-3.8-flash "
        "(limit: 20 requests per day on Free Tier). Please retry in 8h42m17s.', 'code': 'too_many_requests'}}"
    )
    assert _gemini_message(FakeGenAiError(raw)) == (
        "Gemini rate limit or free-tier quota reached. Rate limit exceeded for model gemini-3.8-flash "
        "(limit: 20 requests per day on Free Tier). Please retry in 8h42m17s."
    )

