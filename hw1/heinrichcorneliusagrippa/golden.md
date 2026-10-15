# Golden questions · Verified Evidence Extraction

Three checks of the feature against `spec.md`, using the team's shared `data/transcripts/` and `answer_key.json`. Run from the repo root. Model: `gemini-3.8-flash`.

> **Status (2026-10-15):** offline tests pass (`pytest hw1/heinrichcorneliusagrippa`: 18 passed, fake model, no key). Q1 and Q2 were run live on 15 Oct 2026 on Windows (PowerShell, Python 3.14) with **`gemini-3.5-flash-lite`**, not the default `gemini-3.8-flash`, because the free-tier quota for 3.8-flash (20 requests a day) was already used up (`429 RESOURCE_EXHAUSTED`). The raw outputs are committed in `results/`.

```
F=hw1/heinrichcorneliusagrippa
mkdir -p $F/results
export GROUNDWORK_CHAT_MODEL=gemini-3.5-flash-lite   # what this run used
for i in 01 02 03; do python $F/src/extract.py data/transcripts/interview_$i.txt > $F/results/interview_$i.json; done
python $F/src/check_planted.py data/transcripts/answer_key.json $F/results/interview_0*.json
```

| # | Input | Expected behavior | Actual result | Pass/Fail |
|---|-------|-------------------|---------------|-----------|
| 1 | `interview_01.txt` (cafe owner) | Exit 0. All 4 planted facts are accepted with the right type and line: pain L5, workaround L9, spending L11, workaround L15. The polite answers on L7 ("Sure, sounds nice") and L19 ("Of course, who wouldn't") are not accepted as evidence. Usage is recorded. | Exit 0. 4 extracted, 4 accepted (all `match_score` 100.0), 0 rejected, 1 attempt. Exactly pain L5, workaround L9, spending L11, workaround L15. Nothing cited L7 or L19. 564 in / 249 out tokens, $0.000792. | **pass** |
| 2 | All 3 transcripts | All 3 exit 0. `check_planted.py` prints `recovered 14/14`. interview_03 L19 ("would pay maybe 20 GEL") is not accepted as `spending`. Every item in `rejected[]` really is absent from the transcript. Total cost of the 3 runs is under $0.03. | All 3 exit 0, 1 attempt each. **`recovered 12/14`**: interview_01 4/4, interview_02 5/5 (plus one extra workaround, L5 "gut feeling"), interview_03 **3/5**. Missed: pain L7 ("About 600 GEL in sales") and workaround L15 (cash-and-carry the night before). L19 was correctly **not** extracted, and the "pays nothing" line L11 was accepted as spending. 0 rejected in all 3 files, so every quote the model gave was verbatim. Total: 1,703 in / 816 out tokens, **$0.00255**. | **fail** (12/14) |
| 3 | A malformed transcript whose line 2 is `customer: lowercase speaker` | Exit 1. Stderr names `interview_99.txt:2`. Nothing on stdout. The model is not called. | `error: interview_99.txt:2: not a valid turn: 'customer: lowercase speaker'`, exit 1, stdout empty | pass |

How Q3 was run: `printf 'Interviewer: hi\ncustomer: lowercase speaker\n' > /tmp/interview_99.txt && python $F/src/extract.py /tmp/interview_99.txt`. Also covered by `tests/test_extract.py::test_cli_exit_1_on_malformed_transcript`.

The rejection path (an invented quote, or a real sentence with invented text added) and the retry path (broken JSON, a wrong type label) are also checked offline, with a fake model, in `src/tests/`. A well-behaved real model may never trigger them, so the golden runs alone would not show they work.

## Notes on failures
**Q2, 12/14.** Both misses are in interview_03, and both are *omissions*, not wrong items: the model returned only 3 items for that interview. The quote check cannot catch an omission, because it only checks what the model says, not what it leaves out. So this is a recall problem of the model and prompt, not of the verifier.
- L7 is the *cost* of the pain on L5. The model treated "ran out of cups" and "lost 600 GEL" as one pain and quoted only L5. The answer key counts them separately.
- L15 is a second workaround in the same interview. Flash-lite stopped after one workaround per type here, while in interview_02 it found two pains and two workarounds.

Not fixed yet, on purpose: changing the prompt to hit this answer key and re-running on the same 3 transcripts would be fitting to the test. Next steps, in order: (1) re-run Q2 with the default `gemini-3.8-flash` once its quota resets, to see whether the misses are the lite model's; (2) if they persist, add the prompt rule "one item per Customer line that shows a different fact; a cost of a problem is its own pain item" and check it on a 4th transcript that isn't in the answer key.

**Encoding note.** Windows PowerShell 5.1's `>` saved the results as UTF-16. `check_planted.py` now reads both, and the files committed here were converted to UTF-8.
