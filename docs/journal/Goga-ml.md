# Pattern Journal · Goga-ml (Goga Jintcharadze) · from Week 5

*Weeks 1 to 4 are in [`hw1/Goga-ml/journal.md`](../../hw1/Goga-ml/journal.md). Drafted with Claude Code from the work in this repo.*

## Week 5 · Tool Contract

**Where I used it:** `ask_interviews` (#29) and the tool loop with `POST /act` (#40). **What I noticed:** the contract mattered most for what it leaves out. HW1's command line took `--min-score`; the tool does not, so the model cannot talk it out of abstaining, and golden case `a2` proves it. The red run taught me that `extra="forbid"` was not what protected the threshold, leaving the field out of the code was; `forbid` makes the refusal visible to the model. **Do differently:** check both doors for the same input. Through MCP, extra arguments are dropped silently, not refused, and our both-doors test only compares schemas.

## Week 6 · Session State

**Where I used it:** `src/memory.py` and `docs/state-contract.md` (#43): conversation turns for one session (24 hours), and the founder's focus segment (30 days), written only by the `remember_focus` tool when they ask. `DELETE /me/memory` returns counts and needs no model. **What I noticed:** all 21 tests passed on the first run, so I broke the store on purpose. Ignoring expiry turned one test red; dropping the founder from the key turned five red. A green suite only counted once I had seen it go red for the right reason. **Do differently:** list the caches that are not in the contract before writing it. The router's 10-minute answer cache and the embedding cache hold data that `DELETE /me/memory` does not reach; they are now under "known limits", not solved.

## Week 7 · Supervised Autonomy Loop

**Where I used it:** `src/agent.py` (#46). The goal is collecting evidence for a hypothesis; `save_evidence` waits for the founder's yes. **The one action that must wait for a yes:** saving a quote to the founder's evidence board, because a wrong quote there becomes a "fact" in their next decision. **What I noticed:** the starter's gate only protects the loop. If `save_evidence` had gone into `TOOLS` like every other tool, `/act`, `/chat` and the MCP server could have run it with no yes at all. It lives in `PROPOSE_ONLY`, and `confirm()` checks the quote again. **Do differently:** ask "which other doors can reach this tool?" before asking "does the loop park it?".

## Week 8 · Fallback Chain

**Where I used it:** `ask_interviews` sends its chat call through `complete()`, and Lab 6 added `stream()` to the router: for a stream, a model is "down" only if it fails before the first piece. **The sentence a founder reads when every model is down:** "Groundwork cannot reach its models right now. Your transcripts and earlier results were not changed. Please try again in a few minutes." My tool turns it into a `ToolFailure` so it is never shown as an answer to their question. **What I noticed:** the chain uses OpenRouter ids and the team only had a Gemini key, so the router that is supposed to keep us up made every live chat call fail. **Do differently:** get the key that the plan depends on before merging the plan; `evals/measure.py` and `docs/measurements.md` are still waiting for it.
