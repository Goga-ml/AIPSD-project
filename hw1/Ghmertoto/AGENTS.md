# AGENTS.md · Groundwork · Interview Technique Coach (HW1, Otar Khunashvili)

*Instructions for AI coding agents working in this folder. Read `spec.md` first; it is the contract. Shared formats come from `docs/INTERFACES.md` v1.*

## What this is
Groundwork is a privacy-first, open-source customer discovery tool for early-stage founders. This folder is Task 3, the **Interview Technique Coach**: given one interview transcript, it computes the interviewer/customer talk ratio in code and asks a model to label each interviewer question as `good`, `leading`, `hypothetical`, `pitching` or `compliment_fishing`, with a short explanation and a better question.

## Stack
- Python 3.11+ (tested on 3.13), standard library only for the deterministic parts.
- Model access: `google-genai` (Gemini), only inside `src/llm.py`. Imported lazily, so tests and `--no-llm` runs work without it.
- Tests: `pytest`, never calling a real model.

## Layout (`src/`)
| File | Kind | Job |
|---|---|---|
| `transcript.py` | deterministic | Shared parser, a byte-for-byte copy of `shared/transcript.py`. Do not edit here; fix `shared/` and copy again. |
| `talk_ratio.py` | deterministic | Word counts per speaker and `interviewer_share`. |
| `classifier.py` | LLM boundary | Builds the prompt, validates the model JSON, retries (3 attempts), marks failures `unclassified`. Takes any `call_model(prompt) -> str`. |
| `llm.py` | LLM provider | Gemini call; logs tokens, cost and latency to stderr; keeps the `usage` totals. |
| `coach.py` | CLI | Ties it together, writes JSON (default) or `--format md`. |
| `golden.py` | live check | Runs the golden transcripts against the real model and compares with `answer_key.json`. Not a test. |
| `tests/` | pytest | Unit tests plus fixtures (`tests/fixtures/*.txt`, `answer_key.json`). |

## How to run (from the repo root)
```
pip install -r hw1/Ghmertoto/src/requirements.txt
python hw1/Ghmertoto/src/coach.py hw1/Ghmertoto/src/tests/fixtures/interview_01.txt --format md
python hw1/Ghmertoto/src/coach.py <transcript.txt> --no-llm      # offline, talk ratio only
pytest hw1/Ghmertoto                                              # no API key needed
python hw1/Ghmertoto/src/golden.py                                # live model, needs GEMINI_API_KEY
```

## Configuration (environment only)
- `GEMINI_API_KEY`: required for model calls. **Never hardcode it, never write it to a file, never commit `.env`.**
- `GROUNDWORK_CHAT_MODEL`: default `gemini-3.8-flash`. (`gemini-2.5-flash` returned 404 "no longer available to new users" on 2026-10-15.)
- `GROUNDWORK_PRICE_IN`, `GROUNDWORK_PRICE_OUT`: USD per 1M tokens, defaults `0.75` and `3.75`. These are the Gemini 3.8 Flash introductory prices, checked 2026-10-15 on ai.google.dev/gemini-api/docs/pricing. They become $1.50 / $7.50 on 2027-01-01.
- A 401, 403, 404 or 429 from the API (bad key, unknown model, exhausted quota) is not retried. Other errors, such as a 503, get 3 attempts with a 2 s / 4 s wait. A free-tier key allows about 5 requests per minute and 20 per day for this model.

## Input and output
- Input: one transcript in the INTERFACES §3 format (`Interviewer: ` / `Customer: ` lines, optional `# key: value` headers, blank lines allowed).
- Output: the coach JSON from INTERFACES §7 on stdout, plus the additive fields `labels`, `explanation` and `status` per question. Logs and errors go to stderr. Exit `0` on success, `1` on any error (malformed file, empty transcript, model failure).

## Deterministic vs model: the rule of this feature
- **Code decides:** parsing, speaker attribution, word counts, `interviewer_share`, percentages, which lines are questions, which label is the primary `label`, whether the model output is valid.
- **The model decides only:** labels, explanation and suggestion per question.
- The model never sees word counts and never computes or overrides the ratio. Customer turns and header metadata are never sent.

## Conventions and error handling
- Small functions, type hints, no new dependencies without asking.
- Bad input fails loudly: the parser raises with `<file>:<line>`; the CLI prints it to stderr and exits 1.
- Never report a question as classified when the model failed: failed questions get `status: "unclassified"` and `label: null`, and the talk ratio is still printed.
- Never log transcript text; logs carry token counts, cost and latency only.

## You may not
- Delete, skip or weaken tests to make them pass.
- Call the real model from a test, or in a loop without the 3-attempt cap.
- Edit files outside `hw1/Ghmertoto/` (shared files change through a PR, INTERFACES §11).
