# Spec v1 · Groundwork · Interview Technique Coach

*HW1 · Otar Khunashvili (Ghmertoto) · Task 3 · formats from `docs/INTERFACES.md` v1 §3–5, §7.*
*Run: `pip install -r hw1/Ghmertoto/src/requirements.txt` · `python hw1/Ghmertoto/src/coach.py <transcript> [--format md] [--no-llm]` · Test: `pytest hw1/Ghmertoto` (no key needed)*

**A. Problem.** Founders talk too much in discovery interviews and ask questions that produce politeness, not evidence ("Wouldn't an app that predicts stock be great?" → "Sure"). The coach shows their talk share and flags each biased question with a better one.

**B. Users.** An early-stage founder with a fresh interview transcript in the shared format, preparing for the next interview.

**C. Success criteria**
1. Talk ratio equals an independent count on every golden and shared transcript (5 files) and in every unit test; computed in code only.
2. With the real model, 100 % of planted leading lines get `leading`; at most 1 planted good question per transcript is flagged.
3. `--format md` is ≤ 40 lines for 20 questions; every flagged question has an explanation ≤ 20 words and a rewrite ≤ 25 words ending in "?"; good questions get no rewrite.

**D. Core feature.** (1) Parse with `shared/transcript.py` (copied unchanged); bad lines raise with file:line. (2) Count words per speaker with `Turn.words` (labels, headers, blank lines excluded); `interviewer_share = interviewer / (interviewer + customer)`, 2 decimals, `null` if the total is 0; md also shows percentages and `45:55`. (3) Every Interviewer turn is a question. (4) One batched model call via `llm.py` (logs tokens, cost, latency) returns per line `labels` (≥ 1 of `good`, `leading`, `hypothetical`, `pitching`, `compliment_fishing`), `explanation`, `suggestion`; code validates it (each line once, known labels, `good` alone, suggestion null only for good) and retries up to 3 attempts. (5) Output the §7 JSON (`label` = most severe of `labels`; `labels`, `explanation`, `status` are additive) or a short md report.

**E. Context the model sees.** Only interviewer turns as `L<line>: <text>`, a fixed rubric (label definitions; multiple labels only when justified; hypothetical ≠ leading; mentioning a product ≠ compliment fishing) and the JSON schema with length limits. **Never sent:** customer turns, header metadata, file name, word counts. A bare follow-up ("Why?") is judged on its own words; adding the previous customer turn is a possible v2.

**F. Acceptance criteria**
1. On a golden transcript, every `answer_key.leading_question_lines` entry has `leading` in `labels` and a non-null `suggestion`; exit 0.
2. `--no-llm` makes zero model calls and returns the hand-counted words and share; no Customer turns → share 1.0; empty transcript → share `null`, stderr error, exit 1.
3. A malformed line → exit 1, `<file>:<line>` on stderr, no model call. Invalid model JSON on all 3 attempts (mocked) → exit 1, ratio still printed, every question `label: null`, `status: "unclassified"`.

**G. Napkin math.** Gemini 3.8 Flash, $0.75 in / $3.75 out per 1M tokens (introductory list price, checked 2026-10-15; $1.50 / $7.50 from 2027). Measured in the golden runs: ~450 tokens in and ~2,500 out (1,868–2,867) per 6-question interview. The output includes thinking tokens; the first estimate of 900 was too low. That is **≈ $0.01 per interview**, so 20 founders × 8 interviews = 160/month → **≈ $1.55/month**, ≈ $3.10 at 2027 prices. If every call retries 3×, it is up to 3× that. Transcription and hosting: $0 (text input, local CLI).

**H. Risks.** *Wrong speaker tag* skews the ratio → strict parser, raw counts shown. *Wrong labels* → fixed rubric, validation, golden checks, report says labels are model judgments. *Misleading ratio* (ignores tone, long stories) → raw counts beside the share. *Privacy* → only interviewer questions leave the machine, `--no-llm` is offline, no transcript text in logs. *API failure or cost* → 3-attempt cap, failures shown as unclassified, key only from `GEMINI_API_KEY`, cost logged per call.

**I. Out of scope.** Speech-to-text, evidence extraction, hypothesis linting, cross-interview analysis, any UI, multiple interviewers, non-English transcripts.
