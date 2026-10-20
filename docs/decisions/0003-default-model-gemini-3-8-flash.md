# 0003 · Default chat model `gemini-3.8-flash`, set by environment variable

**Date:** Week 4 (15 October 2026) · **Decided by:** Goga Jintcharadze, Otar Khunashvili, Dachi Khelashvili, Petre Kharazashvili

**Context.** Our specs assumed `gemini-2.5-flash`. On the first live runs, every feature got `404: gemini-2.5-flash is no longer available to new users` (`hw1/Goga-ml/golden.md`, `hw1/Ghmertoto/golden.md`). The free tier of the replacement allows 20 requests a day, which two members used up and replaced with `gemini-3.5-flash-lite` and `gemini-3.6-flash` for their runs.

**Decision.** Every feature defaults to `gemini-3.8-flash` ($0.75 in / $3.75 out per 1M tokens until 31 December 2026, doubling on 1 January 2027), read from `GROUNDWORK_CHAT_MODEL`, so a model can be swapped without a code change. Prices are configurable the same way. A 429 quota error is not retried.

**Alternatives.** A lite model as default: cheaper, but recall was 12/14 on extract and we have not compared it with 3.8 yet. Hard-coding the model id: one less variable, but the 404 showed a retired model breaks every feature at once.

**Consequences.** Swapping models is one environment variable. Thinking tokens bill as output and made real output up to 5 times our estimates, so cost is logged on every call. Watch: results from different members used three different models; the Week 6 re-runs use `3.8-flash` for all features so results are comparable. Week 10 adds a paid key and a fallback model.
