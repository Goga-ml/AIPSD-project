# HW1 golden questions · Interview Technique Coach

Run on 15 October 2026 on Windows 10, Python 3.13.7, from the repo root, by Claude Code, with `S=hw1/Ghmertoto/src`.
Transcripts and the answer key are in `src/tests/fixtures/`. They are my own, written before the shared `data/transcripts/` existed.

**Two kinds of check, kept apart:**
- **Deterministic** (talk ratio, parsing, errors, report shape): `pytest hw1/Ghmertoto` (28 passed) plus the CLI commands below. These are fully reproducible.
- **Live model**: `python $S/golden.py`, which calls Gemini (free-tier key, from the `GEMINI_API_KEY` user environment variable) and compares with `answer_key.json`. Model output is **not** reproducible: three runs gave three different results (log below).

Hand counts were done word by word and cross-checked with `awk` (`NF-1` per turn): interview_01 = 58 / 61, interview_02 = 73 / 35.

| # | Input | Expected | Actual | Pass? | How I ran it |
|---|---|---|---|---|---|
| 1 | `interview_01.txt` (cafe owners): leading questions planted on L6, L10, L14; good on L4, L8, L12 | 58 / 61 words, share 0.49, `49:51`. L6, L10, L14 have `leading` and a rewrite; at most 1 good line flagged; exit 0 | **Run 1:** L6 `leading, hypothetical, pitching, compliment_fishing`; L10 `leading`; L14 `leading, compliment_fishing`; good: L4, L8, L12; all 6 checks PASS. **Run 2:** same verdict (L14 only `leading` this time), all 6 checks PASS. **Run 3:** 503, 503, then 429 (free-tier limit of 5 requests/min) → all `unclassified`, exit 1; ratio check PASS. | **pass** (2 of 3 runs classified; both passed) | `python $S/golden.py` |
| 2 | `interview_02.txt` (designers): good L3, L9; hypothetical L5, L13; pitching L7; compliment_fishing L11 | 73 / 35 words, share 0.68, `68:32`. Each expected label present; L3, L9 not flagged; rewrites ≤ 25 words ending "?"; explanations ≤ 20 words | **Run 1:** L5 `hypothetical`; L7 `pitching`; L11 `leading, compliment_fishing`; L13 `hypothetical`; good: L3, L9; all 6 checks PASS (one 503 on the first attempt, recovered on retry). **Runs 2 and 3:** 503 on all 3 attempts → all `unclassified`, exit 1, labels not checked; ratio check PASS. | **pass** in run 1 only; runs 2–3 **fail** (provider unavailable, not a wrong label) | `python $S/golden.py` |
| 3 | `malformed.txt`: line 3 is `The customer then showed me the diary.` | Exit 1; stderr names `malformed.txt:3`; empty stdout; no model call | `error: malformed.txt:3: not a valid turn: 'The customer then showed me the diary.'`, exit 1, empty stdout; the test's fake model recorded 0 calls | **pass** | `python $S/coach.py $S/tests/fixtures/malformed.txt`; `test_malformed_line_exits_1_with_location_and_no_model_call` |

**Example rewrites from run 1 (real model output):**
- L6 "Wouldn't an app that predicts stock be great for you?" became "How have you tried to predict your stock needs in the past?"
- L13 "How much would you pay per month for something like this?" became "How much do you currently spend on tools or services to manage this process?"

**Live run log (all 15 October 2026):**
| Run | Model | Result | Tokens and cost |
|---|---|---|---|
| 0 | `gemini-2.5-flash` (old default) | 404 "no longer available to new users" on every attempt; all unclassified, exit 1. `golden.py` then printed vacuous PASSes for label checks on unclassified questions (bug, fixed). | no tokens |
| 1 | `gemini-3.8-flash` (via env) | all 12 checks PASS, exit 0 | 438 in / 2,763 out and 452 in / 1,868 out. That is **$0.0107 + $0.0073**, recomputed at $0.75 / $3.75 per 1M, because the logged cost used the old 2.5 Flash prices |
| 2 | `gemini-3.8-flash` (new default) | interview_01 PASS; interview_02 503 ×3 → unclassified, exit 1 | 438 in / 2,867 out, $0.0111 (logged) |
| 3 | `gemini-3.8-flash`, with 2 s / 4 s retry wait | 503s and a 429 free-tier quota error → both unclassified, exit 1. Stopped here so the quota would not be burned further. | no tokens |

**What running them changed:**
- With no key, a missing key was retried 3 times. It now stops at once (`ModelUnavailable`), and a 401/403/404 from the API does too.
- The md report for 20 flagged questions was 67 lines, but criterion 3 allows at most 40. It is now one line per flagged question. `"line": true` was accepted as line 1; it is now rejected. Both have tests.
- Run 0: the default model no longer exists for new keys, so the default is now `gemini-3.8-flash` with its list prices. `golden.py` no longer reports PASS on unclassified output.
- Run 1: output tokens were about 2,300 per interview, not the 900 I estimated, so the spec's napkin math was corrected.
- Run 2: immediate retries all hit the same 503 spike, so a 2 s / 4 s wait was added between attempts. The wait was not enough in run 3. Under the free-tier limit of 5 requests per minute, `golden.py`'s 6 possible calls can also exceed the quota.
