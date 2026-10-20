# Confidence policy · Groundwork

*The low-confidence routes every Groundwork feature already implements. The model's own confidence is never a signal; every check below runs in code. Change a threshold only through a decision record in `docs/decisions/`.*

## 1 · Routes

| Route | What it means | What the founder sees | Where in code |
|---|---|---|---|
| `accepted` | the claim passed every code check | the claim with its `[interview_NN:LNN]` citation | all four features |
| `rejected` | extract: quote not found in any Customer turn | the item in `rejected[]` with `best_line`, `match_score` and `reason` | `hw1/heinrichcorneliusagrippa/src/extract.py` |
| `abstained` | ask: nothing in the transcripts is close enough, or the answer had no valid citation | exactly `no evidence found`, no citations | `hw1/Goga-ml/src/ask.py` |
| `unclassified` | coach: the model failed or broke the format 3 times | the question with `label: null`; the talk ratio is still shown | `hw1/Ghmertoto/src/classifier.py` |
| `error` / placeholder | lint: the model broke the format, or the provider failed; specifics the founder must confirm | a readable error (HTTP 502 before streaming, or a final `ERROR:` line mid-stream); `[bracketed]` values in the rewrite | `hw1/petre-kharazashvili/src/parser.py`, `app.py` |

## 2 · Signals

| Feature | Signal | Condition | Route | Hard or soft |
|---|---|---|---|---|
| extract | quote evidence | `partial_ratio(quote, Customer turn) < 90` (or `ratio` when the quote is longer than the turn) | rejected | hard |
| extract | reply shape | not JSON, wrong shape or unknown type, after 3 attempts | exit 1, nothing printed | hard |
| ask | retrieval score | best cosine `< 0.65` | abstained, no chat call | hard |
| ask | citation evidence | a cited tag is not one of the retrieved turns | tag removed; if none left, abstained | hard |
| coach | reply validity | a line missing or repeated, an unknown label, `good` mixed with other labels, after 3 attempts | unclassified | hard |
| lint | format | a `VERDICT`, `REASON` or `REWRITE` line missing | readable error, nothing passed off as a verdict | hard |
| lint | "unchanged" rewrite | verdict `falsifiable` | the server substitutes the exact input | n/a (guaranteed in code) |

## 3 · Tests (no API calls)

- extract: invented quote and quote-plus-invented-text are rejected; 3 bad replies exit 1 (`hw1/heinrichcorneliusagrippa/src/tests/`).
- ask: below-threshold question makes zero chat calls; invented citation is stripped; only-invented citations abstain (`hw1/Goga-ml/src/tests/test_ask.py`).
- coach: invalid JSON 3 times gives `unclassified` and still prints the ratio (`hw1/Ghmertoto/src/tests/test_coach.py`).
- lint: falsifiable rewrite is byte-identical; a model that ignores the format, and a provider failure before or mid-stream, give a readable error (`hw1/petre-kharazashvili/src/tests/`).

## 4 · What we measure once it runs

- Share of answers per route on real interviews. If most questions abstain, `min_score` is too high; if unrelated ones get answered, too low.
- Wrong accepts found later (the expensive mistake): a citation that does not support its claim. Missed evidence (12/14 recall today) is not caught by any route yet.
