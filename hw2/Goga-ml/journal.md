# Pattern Journal · Goga-ml (Goga Jintcharadze) · Weeks 5 to 7

*Weeks 1 to 4 are in [`hw1/Goga-ml/journal.md`](../../hw1/Goga-ml/journal.md). Drafted with Claude Code from the work in this repo.*

## Week 5 · Tool Contract

**Where I used it:** `AskInterviews` in `src/contracts.py` and `ask_interviews` in `src/tools.py` (#29), wrapping my HW1 `answer_question`. **What I noticed:** the hard part was not the contract, it was that my function calls two models, and a golden case in CI cannot. I added offline stand-ins (`src/offline.py`), and their scores sit on a different scale (related 0.41 to 1.0, off-topic 0 to 0.29), so the tests need their own threshold, 0.35. That makes the cases prove the gates and the wiring, not retrieval. The first live run also hung for over three minutes on a Gemini 503 because the chat call had no timeout and the SDK retried on its own. **Do differently:** decide how a tool runs without a key before writing its contract, and give every model call a limit from the first version.

## Week 6 · Session State

**Where I used it:** not deliberately: our repo has no Lab 6 state. But my tool keeps three things I had not counted as state. Embeddings are cached on disk in `.cache/embeddings.json` (git-ignored, keyed by a hash of model, task type and text, no lifetime, deleted only by hand); the chunk vectors are kept per process by `lru_cache` in `corpus()` in `src/ask.py`; and because the chat call goes through `complete()`, the router keeps each answer, keyed by the full prompt with the customer excerpts in it, in memory for `CACHE_TTL_S = 600` seconds. **What I noticed:** the router's cache holds customers' words for ten minutes, which Petre already raised in `docs/fallback-plan.md`. Answers are also keyed by excerpts, not by founder; that is safe only while every founder shares one workspace. **Do differently:** write scope, lifetime and deletion for each cache in a state contract before per-founder workspaces exist, starting with the embedding cache, which never expires.

## Week 7 · Supervised Autonomy Loop

**Where I used it:** not yet. We have no agent loop, so there is no `NEEDS_YES`. If there were one, it would be empty: `ask_interviews` only reads, and so do the other three tools in `TOOLS`. **What I noticed:** the nearest thing to a bound loop I have is the router: at most two models, 30 seconds each, then a sentence. Turning that sentence into a `ToolFailure` (`ModelUnavailable` in `src/ask.py`) mattered, because otherwise a loop would have read "Groundwork cannot reach its models right now" as an answer to the founder's question. **Do differently:** do each lab in its own week. Doing Labs 5 to 8 in one evening meant I used the Tool Contract properly and only described the other two patterns.
