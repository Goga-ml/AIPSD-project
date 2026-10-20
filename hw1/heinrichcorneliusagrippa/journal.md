# Pattern Journal · Dachi Khelashvili (@heinrichcorneliusagrippa) · Weeks 1 to 4

*Written on 20 Oct 2026, looking back on Weeks 1 to 4 through my HW1 (Groundwork Task 1: verified evidence extraction). Drafted with Claude from the work we did together and checked by me (AI use logged, as the course asks). One entry per week: the pattern, where I used it, what I noticed, what I would do differently.*

## Week 1 · Context as Budget

**Where I used it:** the extractor sends the model only the rules and the transcript as `Speaker: text` lines, with no line numbers, because code finds the citation line itself. On the live run one shared interview was 556 to 583 input tokens and 186 to 381 output tokens with `gemini-3.5-flash-lite`: $0.00255 for all three. **What I noticed:** my napkin math guessed about 900 input tokens, but the real number was lower, and output tokens were about 80% of the cost, not input. **Do differently:** make one real call first and write the napkin math from its usage log, not from a guess.

## Week 2 · Spec Before Code

**Where I used it:** the acceptance criteria were written before any code: a quote is accepted only at a score of 90 or more against a Customer turn, an invalid reply is retried up to 3 attempts and then the tool exits 1, and a malformed transcript exits 1 without calling the model. Each one became a test. **What I noticed:** the spec itself was the bug. It said nothing about the API failing, so when my free quota ran out (429) the tool printed a 60-line traceback instead of the one-line error the spec promised. Reading the team rule closely also showed that `partial_ratio` alone accepts a real sentence with invented text added. **Do differently:** write the error criteria first, including "the provider is down or out of quota".

## Week 3 · Uncertainty-Aware UX

**Where I used it:** the tool never hides a doubtful item. A quote it can't find goes to `rejected[]` with its best score and closest line, and stderr prints `accepted N, rejected M`, so a founder sees what the model claimed and why it was refused. **What I noticed:** in the live run 0 of 13 quotes were rejected, so the tool looked fully confident, yet it had missed 2 of 14 planted facts. I only saw that through the answer key. **Do differently:** also show coverage, for example the Customer lines that produced no evidence, so a founder knows which lines to check by hand.

## Week 4 · Grounded Generation

**Where I used it:** an evidence item counts only if code finds its quote in the transcript (RapidFuzz, 90 or more, Customer turns only) and cites that line. The model is never asked for a line number. **What I noticed:** grounding checks what the model says, not what it leaves out. Both misses in interview_03 (line 7, "lost 600 GEL", and line 15, the cash-and-carry trip) were omissions, and every check still passed. **Do differently:** measure recall separately from precision, and test any prompt change on a transcript that isn't in the answer key, so I don't tune the tool to my own test.
