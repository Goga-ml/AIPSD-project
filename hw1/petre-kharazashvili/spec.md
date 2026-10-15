# Spec v0 · Groundwork · Hypothesis Linter

*HW1 · Petre Kharazashvili · Task 2 of the Groundwork capstone. Wire format follows `docs/INTERFACES.md` v1, section 9. Course topic: streaming responses.*

## Problem
Founders write hypotheses like "Farmers want better tools". Nothing can prove that wrong, so every interview seems to confirm it. They need to know *before* interviewing whether a hypothesis is testable, and what a testable version would look like.

## Users
Early-stage founders using Groundwork who are writing the hypotheses they'll test in customer interviews. Many self-host and run a slow local model through Ollama.

## Success criteria
1. **Rubric.** `falsifiable` only if the hypothesis has all three: (1) a specific customer segment, (2) observable or past behavior, not opinion ("want", "would use", "love"), (3) a measurable pass/fail threshold. Otherwise `vague`.
2. **Rewrites keep the founder's intent.** Specifics the founder must confirm go in `[square brackets]`. A `falsifiable` input comes back unchanged.
3. **It visibly streams.** The verdict shows up first, while the reason and rewrite are still arriving.
4. Every model call logs its tokens and cost to stderr (AGENTS.md).

## Design
- **Wire format (INTERFACES §9).** `GET /` serves the form. `POST /lint` takes `{"hypothesis": "..."}` and streams `text/plain` as three lines, in order: `VERDICT: falsifiable|vague`, `REASON: <1-3 sentences>`, `REWRITE: <text>`. Default port 8000.
- **Model output** is the same plain text, so it can be parsed while streaming. For a falsifiable input the model writes `REWRITE: UNCHANGED`. An incremental parser on the server lowercases the verdict and swaps `UNCHANGED` for the founder's exact input, so "unchanged" is guaranteed by code, not trusted from the model.
- **Providers.** `LLM_PROVIDER=gemini|ollama|mock` selects one implementation of a single async-generator interface that yields text chunks. Gemini: `GEMINI_API_KEY`, `GROUNDWORK_CHAT_MODEL` (default `gemini-3.8-flash`). Ollama: `OLLAMA_URL`, `OLLAMA_MODEL`. The mock streams a canned answer with small delays, for tests and keyless development. Temperature 0.1 for Ollama. Gemini 3.6+ ignores temperature (Google docs), so Gemini gets the lowest thinking level instead, to get the verdict out quickly and cut cost. Output is capped at 300 tokens.
- **Secrets.** The key stays server-side, in a gitignored `.env` (loaded with `python-dotenv`) or an environment variable that's already set. The repo ships a `.env.example`.
- **Stack.** Python 3.11, FastAPI `StreamingResponse`, one static HTML page (vanilla JS, inline CSS) that reads the stream with `fetch` + `ReadableStream`.

## Context list
| What the model sees | Where it comes from |
|---|---|
| Rubric, output format, rewrite rules (brackets, keep intent) | `src/prompt.txt` (system prompt) |
| Few-shot 1: "Farmers want better tools" → `vague`, bracketed rewrite | `src/prompt.txt` |
| Few-shot 2: "At least 7 of 10 independent coffee shop owners we interview will report spending 3+ hours per week on staff scheduling, and at least 3 will agree to a paid pilot at $20/month." → `falsifiable`, `UNCHANGED` | `src/prompt.txt` |
| The founder's hypothesis (≤ 500 chars) | request body |

Nothing else: no interviews, no history, no other hypotheses.

## Acceptance criteria
1. "Farmers want better tools" → `VERDICT: vague`, plus a rewrite that names a segment, a behavior and a threshold, with bracketed placeholders.
2. The coffee-shop hypothesis above → `VERDICT: falsifiable`, with a `REWRITE` that is byte-identical to the input.
3. In the browser, the verdict badge appears before the reason and rewrite finish streaming. With the mock, the response arrives in more than one chunk.
4. An empty (or whitespace-only) hypothesis, or one over 500 characters, gets HTTP 400 with a readable message, and no provider is called.
5. On provider failure (bad key, Ollama down, network error), the page shows a readable error, never a stack trace or a blank result. Before streaming starts this is a non-200 response; mid-stream it is a final `ERROR: <message>` line.
6. A Stop button aborts the stream (`AbortController`). The page shows it was stopped, and the server stops reading from the provider.

## Napkin math
- **Per request:** ~600 tokens in (system prompt + few-shots + hypothesis) and ~120 out. On `gemini-3.8-flash` ($0.75 in / $3.75 out per 1M through 2026-12-31) that's 600 × 0.75/1M + 120 × 3.75/1M ≈ **$0.0009**. Prices double on 2027-01-01, to ≈ $0.0018.
- **Weekly:** 5 founders × 20 lints = 100 requests ≈ 72k tokens ≈ **$0.09 per week** (≈ $0.18 from 2027). Ollama costs nothing.
- **Why streaming matters more locally:** on a laptop, a 7-8B model generates roughly 10 tokens/s, so 120 tokens take ~12 s after prompt processing. Without streaming, the founder stares at a blank page that whole time. With it, the verdict lands after ~3 tokens and the rest reads in as it's written. On Gemini the whole answer arrives in ~1-2 s, so streaming is a nicety there. *(Assumed speeds; check on real hardware.)*

## Deviations from INTERFACES v1 (to propose on Teams)
- The `ERROR:` line (AC 5) is an additive extension to §9.
- Input limit: 500 characters.

## Out of scope
Saving hypotheses, accounts, editing the rewrite in place, multiple hypotheses per request, linking to interviews or evidence, and languages other than English.
