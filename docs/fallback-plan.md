# Groundwork · Fallback Plan

*Lab 8. The code that implements every line is [`src/router.py`](../src/router.py); the tests that hold us to it are [`tests/test_router.py`](../tests/test_router.py).*

| # | Decision | In code | Why |
|---|---|---|---|
| 1 | Protect `one_call()` in [`src/llm.py`](../src/llm.py) first | `call=one_call` | It is the only model call in `src/`, so every tool we add goes through it; the first is the hypothesis linter. Today a failed call has no second model: on a used-up quota the HW1 linter shows `Gemini rate limit or free-tier quota reached. ... limit: 20 requests per day on Free Tier ... retry in 8h42m17s` and the founder gets no verdict ([`hw1/petre-kharazashvili/golden.md`](../hw1/petre-kharazashvili/golden.md), "Hang on 429") |
| 2 | Every job: Gemini 3.8 Flash, then Claude Haiku 5.5 | `CHAINS["chat"]` | Two companies, so one outage or one quota does not take both. Flash first because it is our default ([decision 0003](decisions/0003-default-model-gemini-3-8-flash.md)) and every golden result we have was produced on Gemini. Haiku has not been run on any of them |
| 3 | One model gets 30 seconds | `TIMEOUT_S = 30` | The only latencies in [`logs/usage.jsonl`](../logs/usage.jsonl) are three lint calls: 6.0 s, 26.6 s and 27.8 s. The starter's 12 seconds would have called the first model "down" on two of those three. 30 is the cap the HW1 linter already uses. Worst case with two models: 60 seconds, then the sentence |
| 4 | An answer may be reused for 10 minutes | `CACHE_TTL_S = 600` | The key is the job plus every message, so a changed rubric, hypothesis or transcript is already a different key. What the key cannot see is which model answered: an answer Haiku gave during an outage would otherwise keep being served after Gemini is back. Ten minutes bounds that, and bounds how long customer text sits in memory |
| 5 | "Groundwork cannot reach its models right now. Your transcripts and earlier results were not changed. Please try again in a few minutes." | `SORRY` | Says what happened, says the founder's data is untouched (every tool we have only reads), says what to do |

## What the chain needs

`OPENROUTER_API_KEY`. The two ids in `CHAINS` are OpenRouter ids, and only OpenRouter reaches both companies with one key. With only `GEMINI_API_KEY` set, `one_call()` talks to Gemini directly, the first id is rejected as an unknown model, and the router raises it instead of hiding it. That is the intended behaviour: a wrong model id is our bug, not an outage.

## What we decided not to do

- **No retry of the same model.** The chain is the retry. HW1 showed what a hidden retry does: the Gemini SDK slept through a `Retry-After` of about 8.7 hours and the page hung.
- **No fallback for our own bugs.** A 400, 401 or 403 is raised, not passed to the next model. `test_our_own_bug_is_raised_not_hidden_by_the_next_model` holds us to it. In HW1, Gemini answered a bad key with a 400 and an unsupported `thinking_level` with a 400, and both were ours to fix.
- **No cached apology and no cached tool turn.** The sorry reply is returned after the loop, where nothing is stored; a call that offers tools is never stored either.

## Open questions

- **30 seconds comes from three calls on another route.** Those latencies are `gemini-3.6-flash` on the direct Gemini API with thinking on. We have no measurement through OpenRouter yet. `evals/measure.py` (before Lab 9) gives the real median; if it is near 2 seconds, the limit drops.
- **Is Haiku's answer good enough to be in the chain?** Unknown until the golden set runs against it. Until then: a second answer beats no verdict.
- **The fallback sends the same messages to a second company.** For the linter that is one hypothesis. For extract and ask it is customer interview text. The privacy row in the Design Review ("no real transcripts on free-tier keys") has to cover OpenRouter and Anthropic before those features move onto this chain. Owner: Petre.
- **The cache only helps a long-running process.** It is a dict in memory: it empties on restart, and a one-shot CLI run never hits it.
