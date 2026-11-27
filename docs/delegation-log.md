# Delegation log · Groundwork

One entry per team-level delegation that mattered. Feature-level delegations are in each `hw1/<username>/delegation.md`.

### Entry 1 · Design Review sections 2 to 6
- **Task:** Design Review sections 2 to 6, plus the files they link to: `evals/golden.yaml`, `evals/results/2026-10-15-live-ask.json`, `logs/usage.jsonl`, `docs/confidence-policy.md`, `TEAM-CONTRACT.md`, `docs/TEAM-REPO.md`, `docs/decisions/0001` to `0003`. Section 1 was written by Otar (PR #9).
- **Delegated to:** Claude Code (Claude Opus 5.5), driven by Goga. Context: the course brief and templates, `docs/INTERFACES.md`, and every member's `spec.md`, `golden.md` and committed results.
- **Plan check:** told it to state only numbers that are already recorded in the repo, and to mark what was not run.
- **Came back wrong / at risk:** there was no usage log, so the numbers had to be copied from `golden.md` files and results JSON into `logs/usage.jsonl`; each line names its source, and latency is `null` where it was never recorded. The golden result is compiled by hand from recorded runs, not produced by a script, and says so. Roles, sync time and the no-show rule in `TEAM-CONTRACT.md` were proposed by the agent and need every member to confirm.
- **Caught by:** a teammate review of the pull request: each member checks the risk rows they own and the numbers from their own `golden.md`.
- **Decision:** opened as a pull request for review before the tag.
- **AGENTS.md change:** none (no team-level AGENTS.md yet).
- **Cost:** one session.

### Entry 2 · Skeleton, one_call and CI
- **Task:** issue #13, PR #14: `requirements.txt`, `src/llm.py` with `one_call(messages, tools, timeout=..., model=...)` in the shape `Lab-8/templates/one_call.py` asks for, offline tests, `.github/workflows/ci.yml` from `Lab-2/templates/ci.yml`, `AGENTS.md` and `CLAUDE.md`. This is the frame for the Lab 5 to 8 catch-up and HW2.
- **Delegated to:** Claude Code (Claude Opus 5.5), driven by Goga. Context: the Lab 2, 5 and 8 READMEs and templates, `docs/TEAM-REPO.md`, decision 0003 and `hw1/Goga-ml/src/llm.py`.
- **Plan check:** agreed a task list (skeleton and CI for Goga, gates for Dachi, MCP server for Otar, router for Petre) before any file was written; no written plan for the code itself. Two choices made along the way: Gemini stays the default (decision 0003), with OpenRouter used when its key is set, because the Lab 8 chain needs two companies; and `tests/test_tool_golden.py` was left out because it imports `src/act.py`, which does not exist yet, and would turn CI red.
- **Came back wrong:** the first CI run failed with `ModuleNotFoundError: No module named 'src'`. The tests had passed locally only because they were run with `python -m pytest`, which puts the repo root on the path; CI runs plain `pytest`. Fixed with `pythonpath = .` in `pytest.ini`, after reproducing the failure locally with plain `pytest`.
- **Caught by:** CI on the pull request.
- **Decision:** fixed on the same branch; CI green; waiting for a teammate's review and squash-merge.
- **AGENTS.md change:** created it, with the Never lines from Lab 5 (no identity in tool arguments; no tool that deletes or sends without asking) and the Always line from Lab 8 (every model call through `complete()` in `src/router.py`). Lesson for next time: run tests exactly as CI does (`pytest`, not `python -m pytest`) before pushing.
- **Cost:** one session, one red CI run.

### Entry 3 · Tool contract and the three gates
- **Task:** issue #15: `docs/tool-contracts.md` (team tool `get_transcript` and the HW2 owners table), `src/contracts.py`, `src/tools.py`, `src/act.py`, `tests/test_act.py`, `tests/test_tool_golden.py` (from `Lab-5/templates/`, left out of #13 because it needs `src/act.py`) and `evals/tools/team-get-transcript.yaml`. Built on the #13 skeleton (PR #14, merged).
- **Delegated to:** Claude (Claude Opus 5.5), driven by Dachi. Context: `Lab-5/examples/campuspulse-tools/src/` (`contracts.py`, `tools.py`, `act.py`), `Lab-5/templates/`, `docs/INTERFACES.md`, `shared/transcript.py`, `AGENTS.md`.
- **Plan check:** the task list in the Lab 5 to 8 catch-up split; no separate written plan for the code.
- **Came back wrong:** a test helper took the session identity as a keyword named `caller`, so the test that sends `caller` as a model argument silently replaced the session identity instead of being refused, and failed. Renamed the helper's parameter. Same lesson as the contract: a name the model can fill must never collide with identity.
- **Caught by:** `pytest`, then a red-run check by hand: dropping `extra="forbid"` and removing the id pattern each turn two tests red.
- **Decision:** pull request to `main`; waiting for a teammate's review and squash-merge. Otar builds the MCP server on this branch.

### Entry 4 · MCP server and the `talk_ratio` tool (HW2 · Ghmertoto)
- **Task:** `src/mcp_server.py` and `tests/test_mcp.py` (task 3 of the Lab 5 catch-up), then Otar's HW2 tool: the `TalkRatio` contract, `talk_ratio` in `src/tools.py`, `src/coach.py` (moved from `hw1/Ghmertoto/src/talk_ratio.py`), the registry and MCP entries, `evals/tools/Ghmertoto.yaml` and `tests/test_talk_ratio.py`.
- **Delegated to:** Claude Code (Claude Opus 5.5, then Claude Fable 5.2), driven by Otar, at rung 3: the agent edits, Otar reads every line. Context: `Lab-5/` of the course repo (brief, templates, the CampusPulse example), Goga's task split, `docs/INTERFACES.md`, Dachi's branch `slice-15-tool-gates`, and Otar's HW1 folder.
- **Plan check:** one read-only tool with no model call, so the cases run in CI without a key; the function is the HW1 one, not a rewrite; identity is never an argument.
- **Came back wrong / at risk:**
  - The first version was built before Dachi's branch existed, against the agent's own guess at task 2. The guess was wrong in two places: in the real code every tool takes the caller from the session, and a visitor is offered no tool at all. The MCP server, the tool's signature and the callers in the cases were redone on the real code.
  - The id pattern `^interview_\d{2}$` accepted digits from other scripts (`interview_٠١`), because `\d` is not only 0 to 9. It could not leave the transcripts folder, but the contract was looser than it said.
  - The first expected numbers for `interview_01` were the ones from Otar's HW1 fixtures (58 and 61 words). The shared transcripts in `data/transcripts/` are longer: 78 and 115.
  - One MCP test could pass without proving anything: it checked that the other founder's id was *not* in a list that would also be empty if the call had failed. It now checks that the list is exactly the server's founder.
- **Caught by:** reading Dachi's code when it was pushed, then running the tests on it; probing the contract with odd ids (trailing newline, upper case, other digits) instead of trusting the pattern; running the function on the shared transcripts before writing the cases, plus a second count in `tests/test_talk_ratio.py` that does not use the shared parser; rereading each test and asking what it would do if the feature were broken.
- **Decision:** pattern changed to `[0-9]` with a test for each odd id (this touches one line of Dachi's `InterviewId`); expected numbers taken from the run, not from HW1. Weakening the contract locally (`extra="allow"`) turned 2 of 58 tests red, which is the red run HW2 asks for.
- **Review rule:** Otar reviews every line of the diff before a pull request is opened, and nothing is merged that he cannot explain line by line.
- **AGENTS.md change:** none.
- **Cost:** one session.
