# Pattern Journal · Petre Kharazashvili

*Drafted with Claude Code from this assignment's work; reviewed and checked by me.*

## W1 · Context as Budget · 2026-10-15
In the linter, the model sees only four things: the rubric, the output format, two few-shot examples and the founder's hypothesis (500 characters at most). There's no history and no interview data, which keeps each request around 600 tokens and $0.001. I delegated writing the prompt to the AI and checked the budget against the real token counts in the server log (569 to 610 in). I also learned that few-shots spend budget in a non-obvious way: the model copied example 1 word for word when the input matched it.
**Do differently:** keep the golden inputs out of the few-shot examples, and budget for thinking tokens: the napkin math assumed 120 output tokens, but the log showed up to 285.

## W2 · Spec Before Code · 2026-10-15
I committed the spec before any code, and the build followed its acceptance criteria. The spec still needed two revisions: one when the Gemini docs contradicted it (temperature is ignored now), and one when I noticed it didn't follow the course template. The AI drafted it; I checked it against the template and the team's INTERFACES.md. Having that contract written down is how the AI spotted that my own prompt contradicted the team agreement.
**Do differently:** hand the agent the course template and the current model docs before it drafts the spec, not after; both revisions came from skipping that.

## W3 · Uncertainty-Aware UX · 2026-10-15
The linter is honest about what it doesn't know. Details the founder must confirm go in `[brackets]`; failures show a readable message such as "free-tier quota reached... retry in 8h42m17s" instead of a spinner; and the Stop button gives control back to the user. The worst UX bug wasn't in my code: the SDK silently retried a 429 for about 9 hours, so the page looked like it was "thinking" forever. We only caught it with a live run and an HTTP trace.
**Do differently:** make one live call against the real provider, even with a fake key, before writing the error handling. Every failure we hit (a 400 for a bad key, a 429 with a 9-hour Retry-After) was different from what we assumed.

## W4 · Grounded Generation · 2026-10-15
For a falsifiable hypothesis, the rewrite must be the founder's exact words, so the server substitutes the input itself instead of trusting the model to copy it. G2 came back byte-identical (176 of 176 bytes). I delegated the parser and the golden runs, and verified them with a test that feeds the parser one character at a time and with a byte-for-byte check. The golden set exposed a grounding gap: G3's rewrite borrowed numbers from the few-shot example and invented an unbracketed price.
**Do differently:** test grounding with hypotheses that aren't in the prompt, and check in code that every specific in a rewrite either comes from the input or sits in `[brackets]`.
