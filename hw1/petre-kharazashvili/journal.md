# Pattern Journal · Petre Kharazashvili

*Drafted with Claude Code from this assignment's work; reviewed and checked by me.*

## W1 · Context as Budget
In the linter, the model sees only four things: the rubric, the output format, two few-shot examples and the founder's hypothesis (500 characters at most). There's no history and no interview data, which keeps each request around 600 tokens and $0.001. I delegated writing the prompt to the AI and checked the budget against the real token counts in the server log (569 to 610 in). I also learned that few-shots spend budget in a non-obvious way: the model copied example 1 word for word when the input matched it.

## W2 · Spec Before Code
I committed the spec before any code, and the build followed its acceptance criteria. The spec still needed two revisions: one when the Gemini docs contradicted it (temperature is ignored now), and one when I noticed it didn't follow the course template. The AI drafted it; I checked it against the template and the team's INTERFACES.md. Having that contract written down is how the AI spotted that my own prompt contradicted the team agreement.

## W3 · Uncertainty-Aware UX
The linter is honest about what it doesn't know. Details the founder must confirm go in `[brackets]`; failures show a readable message such as "free-tier quota reached... retry in 8h42m17s" instead of a spinner; and the Stop button gives control back to the user. The worst UX bug wasn't in my code: the SDK silently retried a 429 for about 9 hours, so the page looked like it was "thinking" forever. We only caught it with a live run and an HTTP trace.

## W4 · Grounded Generation
For a falsifiable hypothesis, the rewrite must be the founder's exact words, so the server substitutes the input itself instead of trusting the model to copy it. G2 came back byte-identical (176 of 176 bytes). I delegated the parser and the golden runs, and verified them with a test that feeds the parser one character at a time and with a byte-for-byte check. The golden set exposed a grounding gap: G3's rewrite borrowed numbers from the few-shot example and invented an unbracketed price.
