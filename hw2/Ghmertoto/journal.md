# HW2 · Pattern Journal · Weeks 5, 6 and 7

*Based on `docs/journal/Ghmertoto.md`, reworded here.*

*Drafted with Claude Code from what we actually built; I read and checked every line.*

### Week 5 · Tool Contract
**Where I used it:** the `TalkRatio` contract in `src/contracts.py`, the `talk_ratio` tool in `src/tools.py` and its eight cases in `evals/tools/Ghmertoto.yaml` (pull request #21).
**What I noticed:** the id pattern looked strict and was not. `^interview_\d{2}$` let `interview_٠١` through, because `\d` means any digit in any script, not only 0 to 9. None of my normal cases would have found this. It showed up only when odd ids were tried against the contract on purpose. I changed it to `[0-9]` and added `test_ids_that_only_look_right_are_refused`. The numbers were a second trap. The plan was to reuse the counts from my HW1 golden file for `interview_01` (58 and 61 words). Running the tool on `data/transcripts/` before writing the cases gave 78 and 115: my HW1 fixture is a shorter copy of that interview.
**Do differently:** try to break a pattern before I write the normal cases, and take expected numbers from a run on the real data, not from memory.

### Week 6 · Session State
**Where I used it:** I did not. Lab 6 is not in our repo yet, so the product remembers nothing between turns. My tool keeps no state: every call reads the transcript again. The only thing a call leaves is one line in `logs/tools.jsonl`, where the caller is a hash (`caller_key` in `src/tools.py`).
**What I noticed:** the second identical call gives the same result without any extra code (`test_the_second_identical_call_returns_the_same_result`). Nothing was built for that. For a tool that only reads, idempotency comes from not adding state. I also noticed the tool log already stores something about a caller and nobody has decided how long it lives or who can delete it.
**Do differently:** when we add memory, write its scope, lifetime and deletion in `docs/state-contract.md` first, and start with that log.

### Week 7 · Supervised Autonomy Loop
**Where I used it:** I did not. We have no loop, `src/agent.py` does not exist. What we have is the part a loop would stand on: `call_tool()` in `src/act.py` never raises, and `tools_for(None)` gives a visitor nothing. `NEEDS_YES` would be empty today, because both tools (`get_transcript` and `talk_ratio`) only read.
**What I noticed:** picking a read-only function for HW2 meant I never needed a confirmation step. The first tool that would need a person's yes is one that saves coach notes or rewrites a question in the founder's file, and we have not built it.
**Do differently:** do each lab in its own week. Doing three patterns in one evening meant I really used one and only described the other two.
