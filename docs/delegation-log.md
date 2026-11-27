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
