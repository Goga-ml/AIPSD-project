# Spec v1 · Groundwork · Hypothesis Linter

*HW1 · Petre Kharazashvili · Task 2 of the Groundwork capstone. Wire format follows `docs/INTERFACES.md` v1, section 9. Course topic: streaming responses.*

**Run from a fresh clone, at the repo root:** `python3.11 -m venv .venv && .venv/bin/pip install -r hw1/petre-kharazashvili/src/requirements.txt` · **Test** (mock provider, no key): `.venv/bin/pytest hw1/petre-kharazashvili` · **Try it:** `LLM_PROVIDER=mock .venv/bin/uvicorn app:app --app-dir hw1/petre-kharazashvili/src --port 8000`, then open http://localhost:8000. For the real model, set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY`.

## Problem
Founders write hypotheses like "Farmers want better tools". Nothing can prove that wrong, so every interview seems to confirm it. They need to know *before* interviewing whether a hypothesis is testable, and what a testable version would look like.

## Users
Early-stage founders using Groundwork, before they run their first customer interviews. Many self-host and run a slow local model through Ollama, so they wait a long time for any answer.

## Success criteria
1. **Correct verdicts:** 3 of 3 golden hypotheses get the expected verdict on `gemini-3.8-flash`. *(Golden runs used `gemini-3.6-flash`, same price: the 3.8 free tier of 20 requests/day was already used up. See golden.md.)*
2. **Fast first signal:** on Gemini the verdict line arrives in under 2 s (time to first byte, measured with `curl -N`), while the rest is still streaming.
3. **Cheap and visible:** each lint costs under $0.002, and every request logs its tokens and cost to stderr.

## Core feature
A single-page web form. The founder types a hypothesis and the server streams back a verdict, a reason and a rewrite.
- **Rubric:** `falsifiable` only with (1) a specific customer segment, (2) observable or past behavior, not opinion ("want", "would use", "love"), and (3) a measurable pass/fail threshold. Otherwise `vague`.
- **Rewrites** keep the founder's intent. Specifics the founder must confirm go in `[square brackets]`.
- **Wire format (INTERFACES §9):** `GET /` serves the form. `POST /lint` takes `{"hypothesis": "..."}` and streams `text/plain` lines: `VERDICT: falsifiable|vague`, `REASON: ...`, `REWRITE: ...`. The model writes `REWRITE: UNCHANGED` for a passing hypothesis, and an incremental parser on the server replaces it with the exact input, so "unchanged" is guaranteed in code.
- **Stack:** Python 3.11, FastAPI `StreamingResponse`, one static HTML page (vanilla JS, inline CSS) that reads the stream with `fetch` + `ReadableStream`.
- **Providers (`src/llm.py`, the only place a model is called):** `LLM_PROVIDER=gemini|ollama|mock` selects one async-generator interface that yields text chunks. Gemini: `GEMINI_API_KEY`, `GROUNDWORK_CHAT_MODEL`, minimal thinking (Gemini 3.6+ ignores temperature). Ollama: `OLLAMA_URL`, `OLLAMA_MODEL`, temperature 0.1. Mock: a canned answer with small delays. Output capped at 300 tokens. The key stays server-side (env var or gitignored `.env`), and the repo ships `.env.example`.

## Context list
| What the model sees | Where it comes from |
|---|---|
| Rubric, output format, rewrite rules | `src/prompt.txt` (system prompt) |
| Few-shot: "Farmers want better tools" → VAGUE + bracketed rewrite | `src/prompt.txt` |
| Few-shot: "At least 7 of 10 independent coffee shop owners we interview will report spending 3+ hours per week on staff scheduling, and at least 3 will agree to a paid pilot at $20/month." → FALSIFIABLE, UNCHANGED | `src/prompt.txt` |
| The founder's hypothesis (≤ 500 chars) | request body |

Nothing else: no interviews, no history (Context as Budget).

## Acceptance criteria
1. **Vague gets flagged and rewritten.** "Farmers want better tools" and "Small coffee shop owners would love an app that handles scheduling" each return `VERDICT: vague`, plus a rewrite with a segment, a behavior and a threshold, using bracketed placeholders.
2. **Well-formed passes unchanged.** The coffee-shop hypothesis above returns `VERDICT: falsifiable`, with a `REWRITE` that is byte-identical to the input.
3. **It streams and fails safely.** The verdict badge appears before the reason and rewrite finish (with the mock, the response arrives in more than one chunk). A Stop button aborts the stream and the server stops reading from the provider. Empty or >500-character input gets HTTP 400 with no provider call. A provider failure shows a readable `ERROR:` message: a non-200 response before streaming starts, or a final `ERROR:` line mid-stream.

## Napkin math
Per lint: ~600 tokens in (prompt + few-shots + hypothesis) and ~120 out. On `gemini-3.8-flash` ($0.75 in / $3.75 out per 1M through 2026-12-31): 600 × 0.75/1M + 120 × 3.75/1M ≈ **$0.0009**.
**10 founders × 20 lints/week × 4.3 weeks ≈ 860 lints/month ≈ $0.78/month**, or ≈ $1.55 after prices double on 2027-01-01. Ollama costs nothing. Streaming matters most there: at ~10 tokens/s on a laptop, 120 tokens take ~12 s. Streaming shows the verdict after ~3 tokens, where a blocking call would leave a blank page that whole time.

## Risks
- **Wrong verdict** (the model passes an opinion-based hypothesis). Mitigation: explicit rubric, two few-shots, golden questions.
- **Model breaks the format** (markdown, preamble, wrapped lines). Mitigation: the parser tolerates these, and returns `ERROR:` rather than garbage when a label is missing.
- **"Unchanged" isn't really unchanged.** Mitigation: the server substitutes the exact input, and a test checks it byte for byte.
- **Key leak or runaway cost.** Mitigation: the key stays server-side, never logged; a 300-token output cap; tests use the mock.
- **Prompt injection in the hypothesis.** Mitigation: the prompt says to treat the input as text to judge. Worst case is a bad lint, since nothing else is at stake.

## Out of scope
Saving hypotheses, accounts, editing the rewrite in place, batching, linking to interviews or evidence, non-English input. The `ERROR:` line and the 500-char limit are additions to INTERFACES §9, to propose on Teams.
