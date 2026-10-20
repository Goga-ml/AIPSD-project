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
