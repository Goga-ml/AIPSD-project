# Pattern Journal · Petre Kharazashvili

*Weeks 1 to 4 are in [`hw1/petre-kharazashvili/journal.md`](../../hw1/petre-kharazashvili/journal.md). Drafted with Claude Code from the work on this branch.*

## Week 5 · Tool Contract
I turned the code half of my HW1 linter into a tool, `check_rewrite`. In HW1 the judging and the checking were one model call behind a web form. Now the model that calls the tool proposes a verdict and a rewrite, and the contract decides what the founder may be shown: one line per field, a verdict from a fixed set, no unknown fields, and no number in a rewrite unless the founder wrote it or it sits in [square brackets]. I delegated the code and the golden cases to Claude Code and verified them by breaking the tool four ways (no pattern, no `extra="forbid"`, no number check, trusting the model's rewrite): each one turned exactly one golden case and one unit test red.
**Do differently:** the tool compares digits only. A segment invented in words and left outside brackets still passes. That limit is written in the contract, but no golden case shows it; I would add one that records the miss, so the next person sees it in CI and not in a paragraph.

## Week 6 · Session State
The only state our product keeps today is the router's cache, so I wrote down its scope, lifetime and deletion the way a state contract asks. Scope: the key is a hash of the job and every message, so two different inputs never share an answer. Lifetime: `CACHE_TTL_S = 600`, checked on read. Deletion: a restart, or `CACHE.clear()`. The sorry sentence is never stored, and `test_everything_down_gives_a_sentence_not_a_stack_trace` asserts the cache is empty after it. I delegated the adaptation of the course starter and verified it with the three offline tests and by breaking the chain on purpose to see a test go red.
**Do differently:** the cache can hold customer interview text and the only way to empty it is a restart. Before any feature that reads transcripts goes through the router, add a way to clear it that does not need a deploy. I also lost something from HW1: the linter streamed and logged time to first byte (25.1 s); `one_call()` does not stream, so the number the founder feels is no longer measured.

## Week 7 · Supervised Autonomy Loop
We have no agent loop yet, so the place I saw this pattern is the router, which is the bounded part of one: at most two attempts, 30 seconds each, no retry of the same model, then it stops with a sentence. HW1 taught me why the bound has to be ours: the Gemini SDK's default retry slept through a `Retry-After` of about 8.7 hours and the page just hung.
**The one action that must wait for a yes:** today every Groundwork tool only reads, and the founder decides what to do with a verdict, so nothing waits. The first candidate is not a write at all: sending customer interview text to a second company when the chain falls back. I put that in the open questions of `docs/fallback-plan.md` with my name on it.

## Week 8 · Fallback Chain
The call I protected is `one_call()` in `src/llm.py`, the only model call in `src/`. The chain is Gemini 3.8 Flash, then Claude Haiku 5.5. I set the limit to 30 seconds, not the starter's 12, because two of the three latencies in our own log (26.6 s and 27.8 s) would have been counted as outages. When every model is down the founder reads: "Groundwork cannot reach its models right now. Your transcripts and earlier results were not changed. Please try again in a few minutes."
**Do differently:** I chose 30 seconds from three calls made on a different route (direct Gemini, an older model). Measure through OpenRouter first (`evals/measure.py`), then set the limit from that median.
