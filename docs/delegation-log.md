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
- **AGENTS.md change:** none.
- **Cost:** one session.

### Entry 4 · Lab 8 fallback router
- **Task:** Lab 8 Steps 1 to 3 and the offline half of Step 4: `docs/fallback-plan.md`, `src/router.py` from the course starter, `tests/test_router.py`, and the two AGENTS.md lines about model calls.
- **Delegated to:** Claude Code (Claude Fable 5.2), driven by Petre, at rung 3. Context: `Lab-8/README.md`, the starter and its tests, three Lab 8 resources, `logs/usage.jsonl`, `hw1/petre-kharazashvili/golden.md`, decision 0003, and Goga's skeleton branch (`slice-13-skeleton-ci`).
- **Plan check:** the task split fixed the scope (router only, no `src/llm.py`). Petre stopped the agent as it started writing the plan and told it to pull first.
- **Came back wrong:** (1) the agent had branched from `main` before the skeleton existed and named the branch `slice-13-...` on a guess; issue 13 was already Goga's, and the skeleton branch was on the remote by then. (2) The starter imports `src.one_call`, which we do not have; ours is `one_call()` in `src/llm.py`. (3) The starter's 12 second limit would have counted two of our three logged lint calls (26.6 s, 27.8 s) as outages. (4) The live call (Step 2.4, Step 4) was not run by the agent: it had no key in its shell.
- **Caught by:** (1) pulling, then rebuilding on the skeleton branch and running the suite the way CI does (`pytest -q tests`, 8 passed). (2) reading the starter's ADAPT 0 note against the task split, which puts the call in `src/llm.py`. (3) reading `logs/usage.jsonl` before accepting the default. Also checked that the tests can fail: replacing the `temporary()` check with "always try the next model" turns `test_our_own_bug_is_raised_not_hidden_by_the_next_model` red. (4) is open: Petre runs one real question twice and pastes the two `logs/router.jsonl` lines (`ok` with `place: 1`, then `cache`) into the pull request.
- **Decision:** opened as a pull request, to merge after the skeleton (#14).
- **AGENTS.md change:** "Only src/router.py calls one_call() in src/llm.py" and a pointer to `docs/fallback-plan.md`; removed "until the router lands" from the Always line.
- **Cost:** one session; one rebuild after the pull.

### Entry 5 · MCP server and the `talk_ratio` tool (HW2 · Ghmertoto)
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

### Entry 6 · The `ask_interviews` tool (HW2 · Goga-ml)
- **Task:** issue #25: the `AskInterviews` contract, `ask_interviews` in `src/tools.py` and `src/mcp_server.py`, `src/ask.py` and `src/retrieval.py` (moved from `hw1/Goga-ml/src/`), `src/offline.py`, `embed()` in `src/llm.py`, `tests/test_ask.py`, `evals/tools/Goga-ml.yaml`, and the contract section in `docs/tool-contracts.md`.
- **Delegated to:** Claude Code (Claude Opus 5.5), driven by Goga. Context: `Lab-5/` of the course repo (brief, templates, CampusPulse example), `hw1/Goga-ml/`, decision 0002, and the merged gates (#18), MCP server (#23) and router (#17).
- **Plan check:** no written plan. Two choices made along the way: the model cannot set `min_score` (it is not in the contract, and a golden case tries it); embeddings stay on `google-genai`, because decision 0002's 0.65 threshold was measured with its task types.
- **Came back wrong / at risk:**
  - The golden cases need an answer without a key, but `ask` makes two model calls. Added offline stand-ins (`GROUNDWORK_OFFLINE=1`) in the CampusPulse pattern. Their scores are on another scale (related 0.41 to 1.0, off-topic 0 to 0.29), so tests set the threshold to 0.35. The offline numbers test the wiring, not retrieval quality.
  - The first live run hung for over three minutes on a Gemini 503: the chat call had no timeout, so the SDK's default retries applied. A 503 also reached the caller as a stack trace. Expected outages now become a `ToolFailure` with a message for the model, and the chat call goes through the router, which has the limit.
  - It was first built before the gates existed, on a guessed registry (`writes` instead of `needs_caller`, visitors allowed). Rebuilt on the merged code: a caller from the session picks the workspace, every golden caller is signed in, and ids use `[0-9]{2}`.
- **Caught by:** running it live (the hang and the 503); a local red run (`extra="allow"` turns 3 of 98 tests red, including golden `a2`); reading the merged gates before adapting.
- **Decision:** product pull request for #25.
- **AGENTS.md change:** none. Known exception to "every model call goes through `complete()`": embeddings, because the router has chat jobs only (noted in `src/llm.py`).
- **Cost:** one session; two live Gemini calls that failed with 503 (embeddings: $0.000139).
