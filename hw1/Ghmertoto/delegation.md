# Delegation log · Interview Technique Coach (HW1)

*Agent: Claude Code (Claude Opus 5.5) in the Claude desktop app, 15 October 2026. Context it had: the assignment brief, `docs/INTERFACES.md`, `Lab-3/MILESTONE-1.md` and the hw1 example. Only what is marked "Otar" was done by me; everything else was done and reported by the agent.*

### Entry 1 · Spec before code
- **Task:** write `spec.md` (problem, users, 3 success criteria, context list, 3 acceptance criteria, napkin math, risks, out of scope), then stop.
- **Plan check:** the agent stopped and asked about two conflicts first: folder name (brief says GitHub username) and repo (course repo vs team repo). **Otar** chose `hw1/Otar Khunashvili/` and `AIPSD-project`, then approved the spec. After merge, Otar asked to rename the folder to `hw1/Ghmertoto/` to match the brief, trim the spec to one page, and sync the parser copy with `shared/transcript.py`.
- **Came back wrong:** section D said shares are null "if either total is zero", which contradicts AC2 (no Customer turns gives share 1.0). Prices for Gemini 2.5 Flash are copied from a teammate's spec, not verified.
- **Caught by:** the agent rereading the spec against the acceptance criteria before writing the code. D was corrected to "if the combined total is zero". Prices are labelled as assumptions in the spec.

### Entry 2 · Build `src/` and the tests
- **Task:** parser copy, talk ratio, classifier with validation and retries, Gemini client, CLI, pytest suite with a mock model.
- **Came back wrong:** with no API key the classifier retried the missing key 3 times and then said "failed on every attempt". Retrying cannot fix a configuration error.
- **Caught by:** running the real CLI without a key (not by a test; the mocked tests all passed). **Fix:** a `ModelUnavailable` error that stops retries, a clearer message, and a test asserting no second attempt.
- **Also checked:** the agent's own `awk` cross-check of word counts first printed 6/6, because `-F': '` split on the label. Fixed to `NF-1`, which then matched the hand counts (58/61, 73/35). To check that the tests can fail, the agent swapped the share formula: 6 of 26 tests failed, and passed again after it was restored.

### Entry 3 · Review pass ("check if everything is done correctly")
- **Task:** **Otar** asked the agent to re-check the work against the spec and the brief.
- **Came back wrong:** the md report for 20 flagged questions was 67 lines, breaking success criterion 3 (at most 40). The existing test used only 6 questions, so it never noticed. The validator also accepted `"line": true` as line 1, because a Python bool is an int.
- **Caught by:** measuring a 20-question worst case and probing the validator with odd input. **Fix:** one line per flagged question, plus a regression test for each issue.

### Entry 4 · Live golden runs with a real key
- **Task:** **Otar** created a Gemini key and stored it as a user environment variable (never shown in chat). The agent ran `golden.py`.
- **Came back wrong:**
  - The default `gemini-2.5-flash` was a teammate's assumption, but Google returns 404 for it on new keys.
  - `golden.py` printed vacuous PASSes for label checks on unclassified questions.
  - The spec's token estimate was nearly 3× too low (about 2,500 output tokens, not 900), because thinking tokens count as output.
  - Immediate retries all hit the same 503 spike.
- **Caught by:** running against the real API. None of this was visible to the mocked tests.
- **Fix:**
  - Default changed to `gemini-3.8-flash` at its list prices (checked on ai.google.dev).
  - 401/403/404 are not retried; after run 4, 429 (quota) is not retried either.
  - `golden.py` fails label checks when nothing was classified.
  - Napkin math corrected.
  - A 2 s / 4 s retry wait was added.
- **Still open:** the free tier's 5 requests per minute plus provider overload meant only run 1 classified both transcripts. Runs 2 and 4 classified one, run 3 none. Run 4 used up the daily limit of 20 requests.

### Not verified yet
- Live classification passed in 1 of 4 full runs (both transcripts) and on interview_01 in 3 of 4; the other attempts were provider failures, not wrong labels. A single run is not proof of stable accuracy.
- **Otar** has not yet personally read the code diff or run the tests. *To confirm before submitting.*
