# Delegation log · Hypothesis Linter

**Date:** 2026-10-15 (submission fixes 2026-10-20) · **Rung on the Autonomy Ladder:** 3. The agent planned and wrote code across files; I approved the plan and made the decisions at each checkpoint. I verified mostly through gates (tests, live golden runs, a browser check) rather than reading every line of the diff, which the course calls a slide toward rung 4. Reading `parser.py` and `prompt.txt` myself is still on the list below.

**Delegated to AI (Claude Code, Opus 5.5):** almost everything. That includes the spec and AGENTS.md drafts, checking the Gemini docs and SDK, all of `src/` and its 31 tests, the curl checks, the golden runs, and this draft. I made the decisions at each checkpoint.

| What came back wrong | Caught by | Fix |
|---|---|---|
| The spec didn't follow the course template (6 ACs, weekly cost, no Risks section) | **Me**, by pasting the template | Rewritten before any code was committed |
| The agent took "do what's required" as permission to install Ollama and a 2 GB model | **Me**: I interrupted it | Everything was undone; it now asks before installing |
| My prompt contradicted the team contract (INTERFACES §9) | The agent asked | I chose §9 |
| A bad key showed raw JSON (it assumed 401; Gemini actually returns 400) | A live run with a fake key | Mapping fixed and tested |
| **A 429 hung the page:** the SDK slept for `Retry-After` ~8.7 h, and two fixes guessed from the docstring failed. Also, `thinking_level: "minimal"` was rejected by the model | An HTTP trace, then reading the SDK source | Retry only 503, a 30 s cap, `"low"` |
| G1 and G2 are the prompt's own few-shots (G1 was copied word for word); the latency target was missed (4.6 to 26.6 s) | Reading the golden output | Documented in golden.md, not fixed |
| Submitting: the agent rebased my commits and pushed them straight to `main`, but the brief says to merge through a pull request. The rebase also left golden.md citing a commit hash that no longer existed | A teammate's review against the brief's checklist (2026-10-20) | These fixes go in through the PR `HW1 · petre-kharazashvili`; hash corrected |

**Lesson:** every Gemini bug surfaced only in live runs, because the tests use mocks. The first test run was 27/27 green; breaking the code on purpose showed that one test checked less than it seemed to. I checked the page in a browser myself (mock provider): the badge, reason and rewrite render correctly. My first Stop click came too late (the ~1 s stream had finished: "Done."); on the second try, Stop froze the reason mid-word with "Stopped." and no rewrite.

## My additions
**What I caught that the AI didn't:** the spec didn't follow the course template, and the AI installed software I hadn't asked for (both in the table above). I also kept the API key out of the chat and the repo: it lives in macOS Keychain.

**Checks worth doing myself** (the AI can't verify these for me):
- [x] Open the page in a browser: the badge, reason and rewrite render (done 2026-10-15, mock provider).
- [x] Click Stop while it's still streaming: "Stopped.", with the reason frozen mid-word (second try, 2026-10-15).
- [ ] Stop the server mid-use and check the page shows the "Lost connection" error.
- [ ] Read `prompt.txt` and the three golden outputs: do I agree with the rubric and the verdicts, and do the rewrites keep my intent?
- [ ] Read `parser.py`'s substitution for falsifiable inputs; it's the one rule the whole AC2 depends on.
- [ ] `git log -p`: no key, `.env` or `.venv` committed (`src/.gitignore` and the root `.gitignore`).
- [ ] In AI Studio, confirm the key's project has no billing attached, so it stays free.
- [ ] Try two or three hypotheses of my own that aren't in the prompt; only G3 tested that.
