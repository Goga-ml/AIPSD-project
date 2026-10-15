# Golden questions · Ask Across Interviews

The three acceptance criteria from `spec.md`, checked against the planted facts in `data/transcripts/answer_key.json`.

**Status (2026-10-15):** offline tests pass (7/7, fake embeddings, real transcripts). The live run against Gemini is **not done yet** because no API key was set. The "Live result" column is empty until it runs. Nothing below is filled in from expectation.

Run from the repo root:
```
.venv\Scripts\python -m pytest hw1/Goga-ml -q
.venv\Scripts\python hw1/Goga-ml/src/ask.py "<question>"
```

| # | Input | Expected behavior | Offline result | Live result | Pass/Fail |
|---|-------|-------------------|----------------|-------------|-----------|
| 1 | `What do people currently pay?` | Answer mentions **45 GEL/month** POS add-on `[interview_01:L11]` and **200 GEL/month** to the nephew `[interview_02:L13]`; may mention the cart owner pays nothing `[interview_03:L11]`. Must **not** present "would pay maybe 20 GEL" (`interview_03:L19`) as current spending. `abstained: false`. | `test_answers_with_valid_citation`: pass. The cited chunk `[interview_01:L11]` was retrieved and kept. | _pending live run_ | _pending_ |
| 2 | `What is the weather like in Batumi in winter?` | `answer == "no evidence found"`, `abstained: true`, `citations: []`, **no chat-model call** (`usage.calls == 2`: embeddings only). | `test_abstains_below_threshold_without_calling_model`: pass. The fake model received 0 prompts. | _pending live run_ | _pending_ |
| 3 | Citation integrity: a model answer citing a chunk that wasn't retrieved | The invented tag is removed from the answer and logged to stderr. If no valid citation is left, the tool abstains. On live runs, every citation must appear in `retrieved`. | `test_invented_citation_is_removed` + `test_answer_with_only_invented_citations_abstains`: pass. | _pending: check `citations ⊆ retrieved` on runs 1 and 2_ | _pending_ |

## Threshold
The default `--min-score 0.6` is a **guess** until the live run. To tune it: run question 1 and question 2, record both `best_score` values, and set the threshold between them. Then write the value here and in `docs/INTERFACES.md` section 8.

| Question | best_score |
|---|---|
| 1 (related) | _pending_ |
| 2 (unrelated) | _pending_ |
| Chosen min_score | _pending_ |

## Notes on failures
- First offline test run: **1 failed, 6 passed.** The test expected 3 × 18 chunks, but `interview_03` has 16 turns, so the correct total is 52. The bug was in the test, not the code. Fixed the expected value, rerun: 7 passed. (Logged in `delegation.md`, entry 2.)
