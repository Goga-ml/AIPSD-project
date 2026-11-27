# HW2 · Evidence · `verify_quote`

**Where the cases live:** `evals/tools/heinrichcorneliusagrippa.yaml`, run by `tests/test_tool_golden.py` in CI job `test` (workflow `ci`). More tests: `tests/test_verify_quote.py` (6, including one call through `Client(mcp)`).

Actual results are pasted from a run of every case through `call_tool()` on 27 November 2026, on the shared transcript `data/transcripts/interview_01.txt`.

| # | Type | Call, exactly as in the yaml | Expected | Actual result | Pass? |
|---|---|---|---|---|---|
| q1 | normal | `verify_quote {interview_id: interview_01, quote: "We pay 45 GEL a month for a POS add-on"}`, caller `founder-test` | ok · `supported: true`, cited to line 11, score 100 | `{"supported": true, "citation": {"interview_id": "interview_01", "line": 11}, "best_line": 11, "match_score": 100.0, "reason": null}` | pass |
| q2 | normal | same, with `"addon"` for `"add-on"` | ok · still supported, line 11 | `{"supported": true, "citation": {"interview_id": "interview_01", "line": 11}, "best_line": 11, "match_score": 97.3, "reason": null}` | pass |
| q3 | normal | `quote: "Wouldn't an app that predicts stock be great for you?"` (the interviewer's own line 6) | ok · `supported: false`: only Customer turns are evidence | `{"supported": false, "citation": null, "best_line": 17, "match_score": 45.3, "reason": "quote_not_found"}` | pass |
| b1 | bad-input | `quote: "Sure, sounds nice.\nA paper sheet on the fridge"` (two turns) | refused · "invalid arguments", "quote" | `invalid arguments: quote: String should match pattern '^[^\x00-\x1f\x7f]+$'` | pass |
| a1 | adversarial | line 9 word for word, plus `" and I spend 300 GEL a month on a stock app."` | ok · `supported: false` | `{"supported": false, "citation": null, "best_line": 9, "match_score": 75.3, "reason": "quote_not_found"}` | pass |
| a2 | adversarial | q1 plus `founder: someone-else` | refused · "invalid arguments", "founder" | `invalid arguments: founder: Extra inputs are not permitted` | pass |

**The adversarial case, in one sentence:** in a1 the model glues an invented spending claim ("300 GEL a month on a stock app") onto a real customer sentence, so a fake piece of evidence would borrow the citation `[interview_01:L9]`; with `partial_ratio` alone the real turn fits inside the quote and scores 100, and only the length guard in `src/verify.py` (score with `fuzz.ratio` when the quote is longer than the turn) brings it down to 75.3.

**The red run.**
- Branch: `hw2-heinrichcorneliusagrippa-red` (the product branch plus one line)
- What I weakened, in `src/contracts.py`, inside `VerifyQuote`:
  ```diff
  +    model_config = ConfigDict(extra="allow")    # RED RUN, do not merge: weakens the contract for HW2 evidence
  ```
- Pull request: [#34](https://github.com/Goga-ml/AIPSD-project/pull/34), closed without merging; branch deleted
- Red run (`pull_request`): https://github.com/Goga-ml/AIPSD-project/actions/runs/46040128189 ("Failing after 16s"; the `push` run 46040083354 failed too)
- The test that failed, pasted from the log:
  ```
  FAILED tests/test_tool_golden.py::test_tool_golden_case[heinrichcorneliusagrippa:a2] - AssertionError: heinrichcorneliusagrippa:a2 should be refused but ran: {'interview_id': 'interview_01', 'supported': True, 'citation': {'interview_id': 'interview_01', 'line': 11}, 'best_line': 11, 'match_score': 100.0, 'reason': None}
  ```
- What GitHub showed in the merge box: "All checks have failed · 2 failing checks · ci / test (pull_request) Failing after 16s · Required · ci / test (push) Failing after 23s · Required · Merging is blocked". The box also said "Review required", so the merge was blocked for two reasons at once; the two failing checks are the ones marked Required.

**What the red run taught me.** Only one of my six cases went red, and only one of my two adversarial cases. a1, the padded quote, stayed green: it has nothing to do with the contract. The contract decides what arguments may reach the tool; it cannot tell a real quote from a real quote with a lie glued on. That case is protected by one `if` in `src/verify.py`, and before HW2 the only thing guarding that `if` was a test in my HW1 folder. Now a1 guards it in CI. The other thing the run showed: with `extra="allow"` the tool did not just ignore `founder`, it ran and returned a real, supported citation. Nothing in the result says another founder was asked for, so a wrong call would look exactly like a right one. A refused field shows up in the log and the tests; a silently accepted one shows up nowhere.

**The green run.** Product pull request [#32](https://github.com/Goga-ml/AIPSD-project/pull/32) · run https://github.com/Goga-ml/AIPSD-project/actions/runs/46040015795 (`pull_request`, green; `push` run 46040003594 green) · last line of pytest on the same commit `4d04083`, run locally: `95 passed in 1.69s`
