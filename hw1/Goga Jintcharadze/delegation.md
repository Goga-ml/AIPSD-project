# Delegation log · Groundwork · Ask Across Interviews

Delegated to Claude Code (Claude Opus 5.5) in VS Code. It had the course repo, `spec.md`, `AGENTS.md` and `docs/INTERFACES.md`.

### Entry 1 · Team interface agreement
- **Task:** write `docs/INTERFACES.md` so the four team tasks share one transcript format, citation shape and JSON outputs.
- **Delegated to:** Claude Code, with the four task descriptions as context.
- **Plan check:** approved as proposed. It chose Python for every task (rapidfuzz is a Python library) and had each person copy the parser into their own folder, so every HW1 folder runs by itself.
- **Came back wrong:** the talk-ratio example used made-up word counts (52 / 61) that didn't match the example transcript in the same document.
- **Caught by:** running the documented parser on the example transcript. The real counts are 37 / 45.
- **Decision:** fixed the example, then pushed.
- **AGENTS.md change:** none. It was a documentation error, not a rule gap.

### Entry 2 · Retrieval, abstain path and tests
- **Task:** acceptance criteria 1–3 (`ask.py`, `retrieval.py`, offline tests).
- **Delegated to:** Claude Code, with `spec.md`, `AGENTS.md` and INTERFACES.md section 8.
- **Plan check:** it added one rule that isn't in the spec. If every citation in the model's answer is invalid, the tool abstains instead of returning the answer. I kept it, because it matches the product rule of rejecting anything that can't be traced to a transcript.
- **Came back wrong:** a test assumed every transcript has 18 turns. `interview_03` has 16.
- **Caught by:** running the tests (1 failed, 6 passed).
- **Decision:** fixed the test's expected count (52), not the code. 7/7 pass.
- **AGENTS.md change:** none. The code was right; the test made an assumption about the data.

### Entry 3 · Test transcripts and answer key
- **Task:** 3 synthetic transcripts with planted facts and bad questions, plus `answer_key.json`.
- **Delegated to:** Claude Code.
- **Came back wrong:** nothing found. I checked by printing every numbered line and comparing each planted fact and question line with the answer key; all of them matched.
- **Still unverified:** the napkin-math prices came from third-party sites that disagreed with each other. Check them against ai.google.dev before trusting the cost figure.
