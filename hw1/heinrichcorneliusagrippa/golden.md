# Golden questions · Verified Evidence Extraction

Three checks of the feature against `spec.md`, using the team's shared `data/transcripts/` and `answer_key.json`. Run from the repo root. Model: `gemini-3.8-flash`.

> **Status (2026-10-15):** offline tests pass (`pytest hw1/heinrichcorneliusagrippa`: 15 passed, fake model, no key). **Q1 and Q2 have not been run against the real model yet**, so their "Actual" cells stay empty until real output is pasted in. Q3 needs no model and was run.

```
F=hw1/heinrichcorneliusagrippa
mkdir -p $F/results
for i in 01 02 03; do python $F/src/extract.py data/transcripts/interview_$i.txt > $F/results/interview_$i.json; done
python $F/src/check_planted.py data/transcripts/answer_key.json $F/results/interview_0*.json
```

| # | Input | Expected behavior | Actual result | Pass/Fail |
|---|-------|-------------------|---------------|-----------|
| 1 | `interview_01.txt` (cafe owner) | Exit 0. All 4 planted facts are accepted with the right type and line: pain L5, workaround L9, spending L11, workaround L15. The polite answers on L7 ("Sure, sounds nice") and L19 ("Of course, who wouldn't") are not accepted as evidence. Stderr prints `accepted N, rejected M` and one `model_call` usage line. | _pending real run_ | _pending_ |
| 2 | All 3 transcripts | All 3 exit 0. `check_planted.py` prints `recovered 14/14`. interview_03 L19 ("would pay maybe 20 GEL") is not accepted as `spending`. Every item in `rejected[]` really is absent from the transcript (checked by hand). Total cost of the 3 runs is under $0.03. | _pending real run_ | _pending_ |
| 3 | A malformed transcript whose line 2 is `customer: lowercase speaker` | Exit 1. Stderr names `interview_99.txt:2`. Nothing on stdout. The model is not called. | `error: interview_99.txt:2: not a valid turn: 'customer: lowercase speaker'`, exit 1, stdout empty | pass |

How Q3 was run: `printf 'Interviewer: hi\ncustomer: lowercase speaker\n' > /tmp/interview_99.txt && python $F/src/extract.py /tmp/interview_99.txt`. Also covered by `tests/test_extract.py::test_cli_exit_1_on_malformed_transcript`.

The rejection path (an invented quote, or a real sentence with invented text added) and the retry path (broken JSON, a wrong type label) are also checked offline, with a fake model, in `src/tests/`. A well-behaved real model may never trigger them, so the golden runs alone would not show they work.

## Notes on failures
_None yet. Q1 and Q2 will be filled in after the real run, pass or fail._
