# Golden questions · Hypothesis Linter

**Run:** 2026-10-15, one call each, through the real `POST /lint` endpoint (uvicorn on :8000), `LLM_PROVIDER=gemini`.
**Model:** `gemini-3.6-flash`, not the spec's `gemini-3.8-flash`. The first G1 attempt on 3.8 got `429: limit: 20 requests per day on Free Tier ... retry in 8h42m17s`. The quota had already been used up before this session (the key was created by someone else). 3.6 has the same price and its own quota.
**Measured with:** a small httpx client that records time to first byte (TTFB), chunk count and the full body. The cost comes from the server's stderr log line.

## Results

| # | Input | Expected behavior | Actual result (verbatim stream) | Pass/fail |
|---|---|---|---|---|
| G1 | `Farmers want better tools` | `VERDICT: vague`; rewrite has a segment, a behavior and a threshold, with `[brackets]` (AC1) | `VERDICT: vague`<br>`REASON: The target customer "Farmers" is too broad, "want" measures an opinion rather than an observable behavior, and there is no measurable pass/fail threshold.`<br>`REWRITE: At least [6] of [10] [smallholder vegetable farmers in Imereti] we interview will report [losing part of a harvest to late pest detection] in the past [12 months], and at least [3] will agree to [a paid pilot at 15 GEL/month].` | **PASS** (see caveat 1) |
| G2 | `At least 7 of 10 independent coffee shop owners we interview will report spending 3+ hours per week on staff scheduling, and at least 3 will agree to a paid pilot at $20/month.` | `VERDICT: falsifiable`; `REWRITE` byte-identical to the input (AC2) | `VERDICT: falsifiable`<br>`REASON: It specifies a distinct customer segment (independent coffee shop owners), focuses on observable past behaviors and commitments (hours spent scheduling, agreeing to a paid pilot), and establishes clear numerical pass/fail thresholds (7 of 10, and 3 pilots).`<br>`REWRITE: At least 7 of 10 independent coffee shop owners we interview will report spending 3+ hours per week on staff scheduling, and at least 3 will agree to a paid pilot at $20/month.` | **PASS**: byte-identical, 176/176 bytes, checked in Python |
| G3 | `Small coffee shop owners would love an app that handles scheduling` | `VERDICT: vague`: it has a segment, but relies on an opinion ("would love") and has no threshold (AC1) | `VERDICT: vague`<br>`REASON: The hypothesis relies on an unobservable feeling ("would love") rather than a past or observable behavior, and it lacks a measurable pass/fail threshold.`<br>`REWRITE: At least [7] out of [10] [independent small coffee shop owners] we interview will report [spending 3+ hours per week manually creating staff schedules], and at least [3] will [sign up for a paid pilot at $29/month].` | **PASS** |

**Verdicts: 3 of 3 correct** (success criterion 1, on 3.6 instead of 3.8).

## Streaming, latency and cost (success criteria 2 and 3)

| # | TTFB | Total | Chunks | Tokens in / out | Cost |
|---|---|---|---|---|---|
| G1 | 25.10 s | 26.61 s | 6 | 569 / 110 | $0.000839 |
| G2 | 26.60 s | 27.79 s | 3 | 610 / 220 | $0.001283 |
| G3 | 4.56 s | 6.03 s | 6 | 576 / 285 | $0.001501 |

- **Success criterion 2 (verdict in under 2 s): FAIL, 0 of 3.** TTFB was 4.6 to 26.6 s. The response did stream: each first chunk held the verdict plus the start of the reason, and the rest followed over about 1.5 s. Almost all the wait is before Gemini's first token, though, so streaming can't hide it. I don't know the cause. Candidates: free-tier queueing (G3 took 4.6 s, minutes after two 25 s runs), and thinking tokens (output was 110 to 285 tokens, versus ~80 visible).
  *Suggested fixes, not yet tried:* time G1 again on a paid key or at a quiet hour, to separate queueing from model time; log Gemini's first-event time separately from our own verdict buffering; check how many output tokens are `total_thought_tokens`.
- **Success criterion 3 (under $0.002 and logged): PASS.** $0.00084 to $0.0015 per lint, with one log line per request. The napkin math assumed ~120 output tokens; the real figure is up to 285 (thinking tokens are billed as output), so the real cost is up to ~1.7× the estimate. That's still under budget.

## Caveats (honest)
1. **G1 and G2 are the two few-shot examples in `prompt.txt`.** G1's rewrite is the few-shot rewrite, copied word for word. So G1 and G2 mostly test that the model copies its examples, plus our code for G2's unchanged rewrite. **G3 is the only true generalization test.** A better golden set would use hypotheses that aren't in the prompt.
2. The G2 "unchanged" result is guaranteed by `parser.py` (the server substitutes the exact input), not by the model. The model's own REWRITE text for G2 isn't shown to the user or logged.
3. G3's rewrite borrows numbers from few-shot 2 (7 of 10, 3+ hours per week) and makes up "$29/month" without brackets. The rubric is met, but not every specific is bracketed as the spec asks.
4. **Browser check (by me, 2026-10-15, mock provider):** the badge appears before the reason and rewrite finish, and Stop freezes the stream with "Stopped.". These are also covered by tests and curl (`src/tests/test_app.py`). The browser check used the mock, not Gemini.

## Before these runs: failures found and fixed
- **Hang on 429:** the SDK's default retry slept for Gemini's `Retry-After: 31443` (~8.7 h). Fixed in `5e2ac98`: never retry 429, and a 30 s cap. The page now shows Google's message ("...20 requests per day...retry in 8h42m17s") in about 1 s.
- **`thinking_level: "minimal"`** was rejected by the model (400). Changed to `"low"` in `5e2ac98`.
- These attempts were all rejected by the API (429/400), so none were billed or produced output.
