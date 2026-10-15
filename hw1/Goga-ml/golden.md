# Golden questions · Ask Across Interviews

The three acceptance criteria from `spec.md`, checked against the planted facts in `data/transcripts/answer_key.json`.

**Status (2026-10-15):** offline tests pass 7/7. Live runs used `gemini-3.8-flash` and `gemini-embedding-001`, with `min_score` 0.65. All 3 golden questions pass. Every result below was copied from real output.

Run from the repo root:
```
.venv\Scripts\python -m pytest hw1/Goga-ml -q
.venv\Scripts\python hw1/Goga-ml/src/ask.py "<question>"
```

| # | Input | Expected behavior | Actual result (live) | Pass/Fail |
|---|-------|-------------------|----------------------|-----------|
| 1 | `What do people currently pay?` | Mentions **45 GEL/month** `[interview_01:L11]` and **200 GEL/month** `[interview_02:L13]`. Must **not** present "would pay maybe 20 GEL" (`interview_03:L19`) as current spending. `abstained: false`. | "One customer pays 45 GEL a month for a POS add-on [interview_01:L11]. Another customer pays their nephew 200 GEL a month to keep the ordering spreadsheet up to date [interview_02:L13]." `best_score` 0.704, `abstained: false`, citations `01:L11`, `02:L13`. The 20 GEL trap was not reported. Same answer in 2 runs. | **Pass** |
| 2 | `What is the weather like in Batumi in winter?` | `answer == "no evidence found"`, `abstained: true`, `citations: []`, **no chat-model call**. | `no evidence found`, `abstained: true`, `citations: []`, `best_score` 0.590. stderr: "best score 0.590 < min score 0.65: abstaining without a chat call". Usage: 0 chat calls. | **Pass** |
| 3 | Citation integrity on every answered question | Every citation in `answer` appears in `retrieved`. Invented tags are removed; no valid tag means abstain. | Live: Q1 cited `01:L11`, `02:L13`, both in `retrieved`. "What happens when they run out of stock?" cited `01:L5`, `02:L17`, both in `retrieved`; both match planted pains. Gemini never invented a citation, so the removal path is covered offline only: `test_invented_citation_is_removed` and `test_answer_with_only_invented_citations_abstains` pass. | **Pass** |

## Threshold
The first guess was 0.6. Live scores showed it was too low, so it is now 0.65:

| Question | best_score | At 0.65 |
|---|---|---|
| What do people currently pay? (related) | 0.704 | answers |
| What happens when they run out of stock? (related) | 0.708 | answers |
| How do I bake sourdough at home? (unrelated) | 0.634 | abstains, 0 calls |
| Which football team won the last World Cup? (unrelated) | 0.591 | abstains |
| What is the weather like in Batumi in winter? (unrelated) | 0.590 | abstains, 0 calls |

At 0.6, the sourdough question (0.634) got past retrieval and cost a chat call ($0.00138) before the model itself replied "no evidence found". The gap between related (≥ 0.704) and unrelated (≤ 0.634) questions is small. With more transcripts, this threshold needs re-checking.

## Notes on failures
- **Offline, first run:** 1 failed, 6 passed. The test expected 3 × 18 chunks, but `interview_03` has 16 turns. The bug was in the test. Fixed, 7/7 pass.
- **Live, model retired:** the first live call failed with `404: gemini-2.5-flash is no longer available to new users`. Switched the default to `gemini-3.8-flash` and updated the prices.
- **Live, rate limit:** the second question failed with `429 RESOURCE_EXHAUSTED`. The free tier allows 100 embedding requests per minute, and every run re-embedded all 52 chunks. Fixed by caching embeddings on disk (`src/.embed_cache.json`, git-ignored). After the first run, a question costs 1 embedding call or none.
- **Live, Google outages:** several runs failed with `503 UNAVAILABLE` ("model is currently experiencing high demand"). This happened on Google's side; the tool exits with code 1 and a clear error. There is no automatic retry yet.
- **Cost criterion (spec success criterion 3: under $0.002 per answer): partly fails.** Answered questions cost $0.00160 (Q1, cached) and $0.00247 (stock question). Output tokens (369 and 598) are mostly the model's thinking tokens, far above the 120 assumed in the napkin math. Abstained questions cost $0. Possible fix: lower the model's thinking level.
