# Spec v1 · Groundwork · Verified Evidence Extraction

*HW1 · Dachi Khelashvili (@heinrichcorneliusagrippa) · Task 1 of the Groundwork capstone. Shared formats follow `docs/INTERFACES.md` v1, section 6.*

All commands run from the repo root. **Setup:** `pip install -r hw1/heinrichcorneliusagrippa/src/requirements.txt` · **Test:** `pytest hw1/heinrichcorneliusagrippa` (no key needed)
**Run:** `export GEMINI_API_KEY=...` then `python hw1/heinrichcorneliusagrippa/src/extract.py data/transcripts/interview_01.txt > hw1/heinrichcorneliusagrippa/results/interview_01.json`
**Check planted facts:** `python hw1/heinrichcorneliusagrippa/src/check_planted.py data/transcripts/answer_key.json hw1/heinrichcorneliusagrippa/results/interview_0*.json`

## Problem
After an interview, a founder writes down what they *think* the customer said. Memory keeps the flattering parts and drops the numbers. An LLM can pull the evidence out faster, but an LLM also paraphrases and sometimes invents quotes. Evidence that cannot be traced to the transcript is worse than no evidence.

## Users
Early-stage founders who run customer-discovery interviews, have the transcript as text, and want a list of evidence they can cite in a product decision.

## Core feature
A CLI that reads one transcript and prints a JSON list of evidence items: `type` (`pain`, `workaround`, `spending`, `commitment`), a one-sentence `summary`, and an exact `quote`. The model proposes the items. Code decides which ones are real: pydantic checks the reply's shape, and RapidFuzz checks that each quote appears in a Customer turn. Items that fail are moved to `rejected` and logged, never silently dropped.

## Context list
| What the model sees | Where it comes from |
|---|---|
| Instructions: the four types, "quote character for character from one Customer line", "never invent" | `SYSTEM` in `src/extract.py` |
| The whole transcript, `Speaker: text` per turn, no line numbers | file argument (`data/transcripts/`, shared), parsed by `src/transcript.py` (copy of `shared/transcript.py`) |
| On a retry only: the validator's error message | previous attempt |

Line numbers are not shown to the model, and it is never asked for one. The citation line comes from the turn that the quote matched in code.

## Acceptance criteria (each one is checked by a test or a golden question)
1. Output matches INTERFACES section 6: `interview_id`, `evidence[]` (`id` = `<interview_id>-e<n>`, `type`, `summary`, `quote`, `citation{interview_id,line}`, `match_score`), `rejected[]` (with `best_line`, `match_score`, `reason: "quote_not_found"`), `stats`, `usage`.
2. A quote is accepted only if `fuzz.partial_ratio(quote, turn.text) >= 90` for some **Customer** turn. If the quote is longer than the turn, `fuzz.ratio` is used instead, so a real sentence with invented text added does not pass.
3. An invalid reply (not JSON, wrong shape, type outside the four values) is retried with the error message attached, up to **3 attempts** in total. After 3 failures: exit code `1` and nothing on stdout.
4. A malformed transcript gives exit code `1` with `file:line` in the error message, and the model is not called.
5. Stderr shows `accepted N, rejected M` and one `model_call {...}` usage line per call (tokens, cost, latency).
6. On the 3 shared transcripts, every planted fact in `data/transcripts/answer_key.json` (14 in total) is recovered: an accepted item with the same type that cites the same line. The hypothetical "would pay maybe 20 GEL" (interview_03 L19) is not accepted as `spending`.
7. `pytest hw1/heinrichcorneliusagrippa` passes with no API key and no network.

## Napkin math
Model `gemini-3.8-flash`: $0.75 in / $3.75 out per 1M tokens (thinking is billed as output). Price checked on ai.google.dev on 15 Oct 2026; it doubles on 1 Jan 2027.
One shared transcript (~20 turns) ≈ 900 input tokens (incl. instructions) + 400–1,500 output tokens, depending on thinking ≈ **$0.002–$0.006 per transcript**. A founder with 10 interviews a week spends under $0.07 a week. A retry multiplies the cost of that interview by the number of attempts. Measured numbers: `golden.md`.

## Risks
- **Model tidies a quote** (fixes grammar, drops "um"), so a true quote gets rejected. This fails safe. It is visible in `rejected[]`, and the threshold of 90 tolerates small edits.
- **Wrong type** (a hypothetical "maybe I'd pay" labelled as spending). The quote check cannot catch this. The prompt rule and the planted trap (interview_03 line 19) test for it in the golden run.
- **Citation points at the wrong turn** when two turns say similar things. The best score wins, and ties go to the earlier line.

## Out of scope
Audio, speaker detection, more than one interviewer, deduplicating items, a web UI, storing results, evidence-strength scores.
