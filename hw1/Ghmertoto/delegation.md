# Delegation log · Interview Technique Coach (HW1)

*Agent: Claude Code (Claude Opus 5.5 / Sonnet 5.5), 15–20 October 2026, from the brief, `docs/INTERFACES.md`, `Lab-3/MILESTONE-1.md` and the hw1 example. Autonomy Ladder: rung 3 (agent writes, I approve the spec first and check the results). Everything not marked "Otar" was done and reported by the agent.*

### Entry 1 · Spec before code
- **Task:** write `spec.md`, then stop for approval. **Plan check:** the agent raised two conflicts first (folder name vs the brief; course repo vs team repo). **Otar** chose the repo and folder and approved the spec; later asked for the rename to `hw1/Ghmertoto/`, a one-page spec and a parser synced to `shared/`.
- **Came back wrong:** the spec said the share is null "if either total is zero", contradicting AC2 (no customer turns gives 1.0); the model name and prices were copied from a teammate. **Caught by:** the agent rereading the spec against its criteria. Fixed before coding.

### Entry 2 · Build `src/` and tests
- **Came back wrong:** with no API key the classifier retried the missing key 3 times. **Caught by:** running the real CLI, not by a test (the mocked tests passed). **Fix:** `ModelUnavailable` stops retries, with a test. The agent's own `awk` word-count check also first printed 6/6 (wrong field split); fixed, then it matched 58/61 and 73/35. Swapping the share formula made 6 of 26 tests fail, so the tests can fail.

### Entry 3 · Review pass (asked by Otar)
- **Came back wrong:** the md report for 20 flagged questions was 67 lines (limit 40; the old test used 6 questions), and `"line": true` was accepted as line 1. **Caught by:** a 20-question worst case and odd-input probing. **Fix:** one line per flagged question; a regression test for each.

### Entry 4 · Live golden runs (Otar created the Gemini key and stored it as an environment variable)
- **Came back wrong:** the default `gemini-2.5-flash` returns 404; `golden.py` printed PASS on unclassified output; the token estimate was ~3× too low (about 2,500 output tokens, not 900); immediate retries hit the same 503. **Caught by:** the real API. **Fix:** `gemini-3.8-flash` at checked prices, no retry on 401/403/404/429, 2 s / 4 s wait, failing label checks when nothing is classified, corrected napkin math.
- **Result:** interview_01 passed in 3 of 4 runs, interview_02 in 1 of 4; the rest were provider overload or free-tier quota, not wrong labels (see `golden.md`).

### Entry 5 · Journal
- **Task:** Otar asked the agent to write `journal.md` itself. **Came back:** entries built only from events in this log and `golden.md`. **Limit:** they are the agent's draft of Otar's reflection; no personal activity is claimed beyond choosing the repo and folder, approving the spec, creating the key and requesting the reviews above.

### Checks not recorded
- A personal read-through of the code diff and a personal run of `pytest hw1/Ghmertoto` by Otar are **not** recorded here. All 28 tests were run by the agent: in this checkout, in a fresh clone with a new virtual environment (28 passed), and across the repo with Goga's folder (35 passed).
