# Delegation log · HW1 · Verified Evidence Extraction

**Date:** 2026-10-15 · **Tool:** Claude (Cowork), given the course repo AIPSD-F26, the team repo, `docs/INTERFACES.md` and this folder · **Rung on the Autonomy Ladder:** 3 (the agent drafts spec, code and tests; I read the diff and approve before anything is pushed)

### Entry 1 · Build the extractor from INTERFACES §6
- **Task:** spec acceptance criteria 1 to 5 and 7: CLI, quote check, retry, exit codes, offline tests.
- **Plan check:** I asked for the plan and the exact file list before any code was written, and nothing was pushed without my confirmation. Before planning, the agent noticed that the course repo I first pointed it at (PDFSE-F26) was a different course: customer discovery, not this HW. It switched to AIPSD-F26, Lab 3 `MILESTONE-1.md`.
- **Came back wrong:**
  1. *The shared spec has a hole.* INTERFACES §6 says to score quotes with `partial_ratio(quote, turn)`. When the quote is longer than the turn, partial_ratio slides the turn inside the quote, so a real sentence with invented text added scores 100 and passes. The agent added a guard (use `fuzz.ratio` when the quote is longer) and `test_real_sentence_plus_invented_text_is_rejected`. On the shared transcript, that padded quote now scores 75.3 and is rejected.
  2. *A false alarm during verification.* All 15 tests passed on the first run, which proves nothing on its own. A mutation check followed: remove the length guard, drop the threshold to 50, set retries to 1. The right tests failed each time. After the originals were restored, one run still showed 2 failures. The cause was stale `__pycache__` bytecode (the file had the same size and was edited within the same second), not a bug. This was caught by grepping the restored constants and re-running with the cache cleared: 15 passed.
  3. *Prices from memory would have been wrong.* The agent checked the live pricing page instead of using remembered numbers: `gemini-3.8-flash` is $0.75/$3.75 per 1M tokens until 31 Dec 2026, and thinking tokens are billed as output. It also checked the real `google-genai` field names (`prompt_token_count`, `candidates_token_count`, `thoughts_token_count`) by installing the SDK, not from memory.
  4. *Built on stale team state.* The first version used its own three transcripts in my folder, because the shared Task 0 data didn't exist yet. Before the push, a fresh clone showed that teammates had added `data/transcripts/`, `shared/transcript.py` and the `hw1/<github-username>/` layout. The agent switched to the shared data, rewrote the tests against `interview_01` (lines 5, 9, 11, 15), copied the parser byte for byte (checked with `diff`), and renamed the folder.
- **Caught by:** reading INTERFACES against the RapidFuzz behaviour (1), a mutation check (2), the pricing page and the SDK's own types (3), a fresh clone before pushing (4).
- **Decision:** kept, inside my folder only. Guard 1 is a proposed change to the shared rule; I will raise it with the team as a PR to INTERFACES (section 11).
- **AGENTS.md change:** added "Never call the real model from a test", "Ask first before changing the output shape or the 90 threshold" and "data/ is shared, change it only by PR".
- **Cost:** about 0 model spend (offline tests only).

### Entry 2 · My own review  *(fill in yourself, Dachi; do not leave this generated)*
- **What I read in the diff:**
- **What I ran myself, and the output:**
- **What I changed or rejected:**
- **What the first real Gemini run got wrong (golden Q1/Q2):**
