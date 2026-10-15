# Spec v1 · Groundwork · Interview Technique Coach

*HW1 · Otar Khunashvili · Task 3 of the Groundwork capstone. Shared formats follow `docs/INTERFACES.md` v1 (sections 3, 4, 5, 7).*
*Run: `pip install -r "hw1/Otar Khunashvili/src/requirements.txt"` · `python "hw1/Otar Khunashvili/src/coach.py" <transcript.txt> [--format md] [--no-llm]` · Test: `pytest "hw1/Otar Khunashvili"` (no API key needed)*

## A. Problem
Founders running discovery interviews talk too much and ask questions that cannot produce evidence: "Wouldn't an app that predicts stock be great?" gets a polite "sure" that feels like validation but is not. They rarely notice it in their own transcripts. The coach shows how much of the interview the founder spent talking, and which questions were leading, hypothetical, pitching or fishing for compliments, with a better question for each.

## B. Users
An early-stage founder who has just finished a customer interview, has it as a text transcript in the shared format, and wants feedback on their technique before the next interview.

## C. Success criteria
1. **Talk ratio is exact.** Word counts match a hand count on 3 of 3 golden transcripts and in every unit test (100 %). Computed in code, never by the model.
2. **Planted leading questions are caught.** With the real model, 100 % of the leading-question lines listed in the golden answer key get `leading` among their labels, and at most 1 planted *good* question per transcript is flagged as problematic.
3. **The report is short and actionable.** `--format md` output is at most 40 lines for a 20-question interview; every non-`good` question has an explanation of at most 20 words and a rewrite of at most 25 words that ends in "?"; `good` questions have no rewrite.

## D. Core feature
CLI `coach.py <transcript>`:
1. **Parse** with the shared parser (`shared/transcript.py`, copied unchanged into `src/`). Malformed lines raise with file and line number.
2. **Count** words per speaker with `Turn.words` (whitespace split of the turn text; speaker labels, `#` headers and blank lines are never counted). `interviewer_share = interviewer_words / (interviewer_words + customer_words)`, rounded to 2 decimals; percentages and a ratio like `45:55` are shown in the md report. If the combined total is zero, the share is `null`: no division by zero.
3. **Extract** every Interviewer turn as a question (INTERFACES §7), with its line number.
4. **Classify** in one batched model call through `llm.py` (logs tokens, cost, latency). The model returns JSON: per line, `labels` (one or more of `good`, `leading`, `hypothetical`, `pitching`, `compliment_fishing`), `explanation`, `suggestion`. Code validates it: every sent line answered once, known labels only, `good` never combined with another label, `suggestion` null if and only if `good`. Invalid output is retried, up to 3 attempts in total.
5. **Report** the coach JSON (INTERFACES §7) on stdout, or a short markdown report with `--format md`. `label` holds the most severe label (leading > pitching > compliment_fishing > hypothetical > good); `labels` and `explanation` are additive fields (allowed by INTERFACES §11).

## E. Context list (what the model sees)
| Sent | Why |
|---|---|
| Each interviewer turn, as `L<line>: <text>` | the thing being judged |
| Fixed rubric: five label definitions, "multiple labels allowed when justified", "a hypothetical is not automatically leading", "asking about the product is not automatically compliment fishing" | consistent, evidence-based labels |
| JSON output schema plus length limits | parseable, short output |

**Not sent:** customer turns (INTERFACES §7), header metadata (segment, date), the file name, word counts. A follow-up like "Why?" is judged on its own words and is labelled `good` unless its wording is biased; adding the preceding customer turn as context is a possible v2 change, recorded as a decision if ever needed.

## F. Acceptance criteria
1. On a golden transcript with planted leading questions, `coach.py` exits 0, and every line in `answer_key.leading_question_lines` has `leading` in `labels` and a non-null `suggestion`.
2. `coach.py <file> --no-llm` makes zero model calls and returns `interviewer_words`, `customer_words` and `interviewer_share` equal to the hand-counted values in `golden.md`. A transcript with no Customer turns returns `customer_words: 0` and `interviewer_share: 1.0`; an empty transcript returns `interviewer_share: null`, an error on stderr, and exit 1.
3. A malformed line exits 1 with `<file>:<line>` on stderr and no model call. If the model returns invalid JSON on all 3 attempts (mocked in a test), the tool exits 1, still prints the talk ratio, and every question has `label: null` and `status: "unclassified"`. It never reports a question as classified.

## G. Napkin math (estimates, not verified prices)
Assumed model: Gemini 2.5 Flash at $0.30 in / $2.50 out per 1M tokens (same assumption as the team; *check ai.google.dev pricing and fill INTERFACES §1 before submitting*).
Per interview: 15 questions × ~25 tokens + ~600 tokens rubric ≈ **1,000 input**; 15 × ~60 tokens ≈ **900 output**.
Cost: 1,000 × $0.30/1M + 900 × $2.50/1M ≈ **$0.0026 per interview** (up to 3× with retries; thinking tokens, if enabled, are billed as output).
**20 founders × 8 interviews/month = 160 interviews ≈ $0.42/month** (worst case with retries about $1.25).
Other costs: transcription $0 (founders bring text; speech-to-text is out of scope), hosting $0 (local CLI).

## H. Risks
- **Wrong speaker attribution:** a customer line tagged `Interviewer:` skews the ratio and gets coached. Mitigation: strict parser, per-speaker counts shown so the founder can spot it.
- **Wrong labels:** the model can over-flag or miss. Mitigation: fixed rubric, schema validation, golden checks against the answer key; the report says the labels are model judgments, not facts.
- **Misleading ratio:** word counts ignore pauses and tone, and a long customer story inflates their share. Mitigation: show raw word counts next to the share.
- **Privacy:** interviewer questions leave the machine. Mitigation: customer turns and metadata are never sent; `--no-llm` runs fully offline; transcripts are never written to logs.
- **API failure or cost:** retries are capped at 3, failures are reported as `unclassified`, the key comes only from `GEMINI_API_KEY`, and every call logs its cost.

## I. Out of scope
Speech-to-text, evidence extraction (Task 1), hypothesis linting (Task 2), cross-interview questions (Task 4), trends across interviews, any web UI, multiple interviewers per file, languages other than English.
