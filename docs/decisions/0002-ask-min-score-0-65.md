# 0002 · Ask abstains below a cosine score of 0.65

**Date:** Week 4 (15 October 2026) · **Decided by:** Goga Jintcharadze

**Context.** Ask Across Interviews must say exactly "no evidence found", with no chat call, when the transcripts do not answer a question (`docs/INTERFACES.md` section 8). The first guess for `min_score` was 0.6. On live runs with `gemini-embedding-001`, the unrelated question "How do I bake sourdough at home?" scored 0.634, passed retrieval and cost a chat call ($0.00138) before the model itself declined.

**Decision.** `min_score` defaults to 0.65 (`hw1/Goga-ml/src/ask.py`).

| Question | best_score | At 0.65 |
|---|---|---|
| What do people currently pay? (related) | 0.704 | answers |
| What happens when they run out of stock? (related) | 0.708 | answers |
| How do I bake sourdough at home? (unrelated) | 0.634 | abstains |
| Which football team won the last World Cup? (unrelated) | 0.591 | abstains |
| What is the weather like in Batumi in winter? (unrelated) | 0.590 | abstains |

Evidence: `hw1/Goga-ml/golden.md`, threshold section.

**Alternatives.** Keep 0.6 and let the model refuse: works on these questions, but pays for a chat call on every off-topic question and trusts the model to refuse. 0.70: too close to the related questions (0.704), so real questions would abstain.

**Consequences.** Off-topic questions cost $0. The margin between related (≥ 0.704) and unrelated (≤ 0.634) questions is only 0.07, measured on 5 questions over 3 transcripts. Re-tune on the 10-question golden set by Week 11, and re-check whenever the corpus or embedding model changes.
