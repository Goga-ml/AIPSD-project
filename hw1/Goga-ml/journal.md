# Pattern Journal · Goga Jintcharadze

*One entry per teaching week, 2 to 3 sentences. Graded inside HW1 (W1-4), HW2 (W5-7), and the Repository Review (W10-14). Honest beats polished.*

Format per entry:
**W# · [Pattern name]** · Where I applied it · What I delegated to AI · How I verified it

---

**W1 · Context as Budget** · In Ask Across Interviews, the model sees only the top 5 retrieved turns, not the whole transcripts, which keeps one question around 500 input tokens. I delegated the chunking and cost tracking to Claude Code. I checked in the offline tests that the prompt is built only from the retrieved excerpts. The per-query `cost:` line still needs to be confirmed on the first live run.

**W2 · Spec Before Code** · I wrote `spec.md` for Task 4 and pushed it before any code existed (commit `bcd7974`). Our team also agreed on `docs/INTERFACES.md` first, so four people could build in parallel. I delegated drafting both to Claude Code and checked the agreement by running its example parser on its example transcript, which caught wrong numbers.

**W3 · Uncertainty-Aware UX** · When the best match is below the threshold, the tool says exactly "no evidence found" and doesn't call the chat model at all. It also abstains if the model's answer has no valid citation. I delegated the abstain logic and verified it with a test that confirms the fake model receives zero prompts.

**W4 · Grounded Generation** · Answers may use only the retrieved chunks, and every claim has to cite `[interview_NN:LNN]`. The code removes any citation that wasn't retrieved, instead of trusting the model. I delegated the citation check and verified it with a test where the model invents `[interview_02:L99]` and the tag gets stripped.
