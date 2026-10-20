# Design Review · Groundwork · AIPSD-project team

Members: Otar Khunashvili · Ghmertoto · [role] · Goga Jintcharadze · Goga-ml · [role] · Dachi Khelashvili · heinrichcorneliusagrippa · [role] · Petre Kharazashvili · petre-kharazashvili · [role]
Repo: https://github.com/Goga-ml/AIPSD-project · Graded commit: tag `design-review`

## 1 · Problem, users, success criteria

**Problem.** Founders validate ideas by interviewing potential customers, then decide from memory and notes, and memory keeps the flattering parts. Three things go wrong. Hypotheses like "farmers want better tools" can never be proved wrong, so every interview seems to confirm them. Interview questions lead the customer ("Wouldn't an app that predicts stock be great?"), so a polite "sure" is recorded as validation. And after ten interviews nobody can say who actually said what, so a hypothetical "would pay maybe 20 GEL" gets remembered as real spending. Today founders reread transcripts by hand or trust their notes; neither separates evidence from compliments, and neither can be checked by someone else.

**Groundwork** is an open-source, privacy-first customer-discovery tool. It separates real evidence (pains, workarounds, current spending, commitments) from polite answers and assumptions, and ties every claim to a line in a transcript, in the form `[interview_01:L11]`. Its rule is that the model proposes and the code decides: counting, quote matching, line numbers and validation are done in code, and the model is only used for judgment.

**Users.** Early-stage founders and student teams running customer-discovery interviews. They have their interviews as text transcripts, usually 3 to 10 per segment, and need to decide what to build next. Some self-host and run a slow local model, so they need fast first feedback.

Specs: shared contract `docs/INTERFACES.md` v1 (transcript format, parser, JSON shapes); one spec per feature in `hw1/heinrichcorneliusagrippa/spec.md`, `hw1/petre-kharazashvili/spec.md`, `hw1/Ghmertoto/spec.md`, `hw1/Goga-ml/spec.md`. Shared test data with planted facts: `data/transcripts/` and `answer_key.json`.

| # | Success criterion | Measured by | Today |
|---|---|---|---|
| S1 | **No invented evidence.** Every accepted quote matches a Customer line in code (RapidFuzz ≥ 90), and at least 13 of the 14 planted facts are recovered with the right type and line | `hw1/heinrichcorneliusagrippa/src/check_planted.py` over the committed `results/*.json` | 12/14 recovered, 0 invented quotes accepted; the "would pay maybe 20 GEL" trap was not counted as spending ([golden](../hw1/heinrichcorneliusagrippa/golden.md)) |
| S2 | **Every answer is cited or refused.** Questions answered in the transcripts cite the right `interview:line`; unrelated questions return exactly `no evidence found` with zero chat-model calls | `hw1/Goga-ml/golden.md` (3 golden questions) and `pytest hw1/Goga-ml` | 3/3 live pass; abstained with 0 chat calls at `min_score` 0.65 ([golden](../hw1/Goga-ml/golden.md)) |
| S3 | **Hypotheses are judged before interviews.** The linter gives the expected `falsifiable`/`vague` verdict on all golden hypotheses, and a falsifiable one is returned byte-identical | `hw1/petre-kharazashvili/golden.md` (3 hypotheses through `POST /lint`) | 3/3 verdicts correct; rewrite byte-identical (176/176 bytes). Run on `gemini-3.6-flash` because the 3.8 free quota was used up ([golden](../hw1/petre-kharazashvili/golden.md)) |
| S4 | **Biased interview questions are caught.** The talk ratio equals an independent word count, and every planted leading question gets the `leading` label with a rewrite | `pytest hw1/Ghmertoto` (28 tests) and `hw1/Ghmertoto/src/golden.py` against its answer key | Ratio exact on all 5 transcripts; planted leading questions flagged in every run the model answered (3/3 on interview_01, 1/1 on interview_02); the other runs failed on 503 or quota, reported as unclassified ([golden](../hw1/Ghmertoto/golden.md)) |

## 2 · Architecture and data flow

*To be filled.*

## 3 · Risks and safety threats

*To be filled.*

## 4 · Evaluation plan

*To be filled.*

## 5 · Token budget

*To be filled.*

## 6 · Team, roles and decisions

*To be filled.*
