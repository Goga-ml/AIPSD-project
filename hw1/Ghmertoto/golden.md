# HW1 golden questions · Interview Technique Coach

Run on 15 October 2026 on Windows 10, Python 3.13.7, from the repo root, by Claude Code. Commands are written with `S=hw1/Ghmertoto/src`.
Transcripts and the answer key are in `src/tests/fixtures/`. The shared `data/transcripts/` did not exist yet (Task 0 not pushed), so these are my own.

**Two kinds of check, kept apart:**
- **Deterministic** (talk ratio, parsing, error handling, report shape): run for real, results below.
- **Live model** (does Gemini actually flag the planted questions?): `python "$S/golden.py"`. **Not run yet.** `GEMINI_API_KEY` was not set in this environment, so no real model call has been made. Until it is run, cases 1 and 2 are **pending**, not passed.

Hand counts were done word by word and cross-checked with an independent `awk` count (`NF-1` per turn): interview_01 = 58 / 61, interview_02 = 73 / 35. Both match.

| # | Input | Expected | Actual | Pass? | How I ran it |
|---|---|---|---|---|---|
| 1 | `interview_01.txt` (cafe owners) with leading questions planted on L6, L10, L14 and good questions on L4, L8, L12 | Talk: 58 interviewer / 61 customer words, `interviewer_share` 0.49, report `49:51`. With the model: L6, L10, L14 have `leading` in `labels` and a non-null `suggestion`; at most 1 of L4/L8/L12 flagged; exit 0 | **Deterministic:** `--no-llm` returned 58 / 61 / 0.49, zero model calls, exit 0. With the mock classifier the pipeline produced 3 rewrites (L6, L10, L14), none for good lines (`- Good: L4, L8, L12`), report says `ratio 49:51`. **Live model:** not run (no API key). | Ratio: **pass** · Leading detection: **pending** | `python "$S/coach.py" "$S/tests/fixtures/interview_01.txt" --no-llm`; `pytest` tests `test_talk_ratio_matches_hand_count[interview_01]`, `test_planted_leading_questions_flagged_with_mock_classifier`, `test_markdown_report_is_short_and_has_rewrites`. Live: `python "$S/golden.py"` |
| 2 | `interview_02.txt` (freelance designers): good L3, L9; hypothetical L5, L13; pitching L7; compliment_fishing L11 | Talk: 73 / 35, share 0.68, `68:32`. With the model: each expected label present in `labels`; L3 and L9 not flagged (at most 1); every rewrite ≤ 25 words ending in "?"; explanations ≤ 20 words | **Deterministic:** `--no-llm` returned 73 / 35 / 0.68, zero model calls, exit 0. Mock pipeline report: `ratio 68:32`, 4 to rewrite. **Live model:** not run (no API key). | Ratio: **pass** · Classification: **pending** | `python "$S/coach.py" "$S/tests/fixtures/interview_02.txt" --no-llm`; `test_talk_ratio_matches_hand_count[interview_02]`, `test_no_llm_cli_makes_no_model_call`. Live: `python "$S/golden.py"` |
| 3 | `malformed.txt`: line 3 is `The customer then showed me the diary.` (no speaker label) | Exit 1; stderr names `malformed.txt:3`; nothing on stdout; no model call | `error: malformed.txt:3: not a valid turn: 'The customer then showed me the diary.'`, exit 1, empty stdout. The test's fake model recorded 0 calls. | **pass** | `python "$S/coach.py" "$S/tests/fixtures/malformed.txt"`; `test_malformed_line_exits_1_with_location_and_no_model_call` |

**Related edge cases, run too (unit tests, not golden):** an empty transcript gives `interviewer_share: null`, an error on stderr and exit 1 (`empty.txt`, real CLI output: `error: empty has no Interviewer or Customer turns`, report `no words spoken`). A transcript with no Customer turns gives share 1.0. If the model returns invalid JSON 3 times, the result is exit 1, the ratio is still printed and all 6 questions are `unclassified`. With no API key, the real CLI printed `classify: model unavailable, not retrying: GEMINI_API_KEY is not set`, marked all 6 questions `not classified` and exited 1.

**What running them changed:**
- The first no-key run retried a missing API key 3 times before giving up. Retrying cannot fix a missing key, so the classifier now stops after one attempt on `ModelUnavailable`. A test asserts that no second attempt happens.
- A review pass measured the md report for 20 flagged questions at **67 lines**, which breaks success criterion 3 (at most 40). The report now uses one line per flagged question and one line listing all good ones. `test_report_for_20_flagged_questions_fits_in_40_lines` now passes. The same pass found that `"line": true` was accepted as line 1; it is now rejected and tested.

**To finish cases 1 and 2:** set `GEMINI_API_KEY` in your shell, run `python "$S/golden.py"`, and paste its PASS/FAIL lines and report into the Actual column above. A FAIL stays recorded as a FAIL.
