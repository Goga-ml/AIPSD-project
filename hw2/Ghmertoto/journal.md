# HW2 · Pattern Journal · Weeks 5, 6 and 7

*Copied from `docs/journal/Ghmertoto.md`.*

*One entry per teaching week. All three entries below were written on 27 November 2026, when our team caught up on Labs 5 to 7, not in their own weeks. Drafted with Claude Code from the actual build and edited by me.*

### Week 5 · Tool Contract · written 2026-11-27
**Where I used it:** the `TalkRatio` contract in `src/contracts.py`, the `talk_ratio` tool in `src/tools.py`, and its seven cases in `evals/tools/Ghmertoto.yaml`.
**What I noticed:** I expected the pattern on `interview_id` to be the strict part of the contract. It was not: `^interview_\d{2}$` accepted `interview_٠١`, because `\d` matches digits from any script. And when I removed `extra="forbid"` to rehearse the red run, only 2 of 48 tests failed. The path case (`../../.env`) stayed green, because the pattern stops it, not `extra="forbid"`. Each rule protects against one thing only.
**Do differently:** write the adversarial case first and probe every pattern with odd input before I trust it. A pattern I have not attacked is a guess.

### Week 6 · Session State · written 2026-11-27
**Where I used it:** not yet. Lab 6 is not in our repo, so the product remembers nothing between turns. My tool is stateless on purpose: every call re-reads `data/transcripts/`. The only thing a call leaves behind is one line in `logs/tools.jsonl`, with the caller stored as a hash (`caller_key` in `src/tools.py`). That log has no lifetime and no delete yet, which is exactly what a state contract would make us decide.
**What I noticed:** because nothing is remembered, the second identical call returns the same result for free (`test_the_second_identical_call_returns_the_same_result` in `tests/test_talk_ratio.py`). I had thought of idempotency as extra work. For a read-only tool it is what you get when you add no state.
**Do differently:** write scope, lifetime and deletion in `docs/state-contract.md` before any memory code, starting with the tool log, since it already stores something about a caller.

### Week 7 · Supervised Autonomy Loop · written 2026-11-27
**Where I used it:** not yet. We have no loop (`src/agent.py` does not exist). What I built is what a loop would stand on: `call_tool()` never raises, and `tools_for(None)` never offers a write tool. `NEEDS_YES` would be empty today, because both tools (`get_transcript`, `talk_ratio`) only read (`writes=False` in `TOOLS`).
**What I noticed:** choosing a read-only function for HW2 removed the need for a confirmation gate. The first tool that would need a person's yes is one that saves coach notes or rewrites a question in the founder's file, and we have not built it.
**Do differently:** do each lab in its own week. Three patterns in one evening meant I used one properly and only described the other two.
