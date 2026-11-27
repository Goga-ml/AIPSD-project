# HW2 · Tool contract · `ask_interviews` · Goga-ml

**Tool:** `ask_interviews` · **Owner:** Goga-ml (Goga Jintcharadze) · **Team repo:** https://github.com/Goga-ml/AIPSD-project
**Code on `main`:** contract class `AskInterviews` in [`src/contracts.py`](../../src/contracts.py) line 71 · function `ask_interviews` in [`src/tools.py`](../../src/tools.py) line 174 · registry entry in `src/tools.py` line 214 · MCP registration in [`src/mcp_server.py`](../../src/mcp_server.py) line 78 · the capstone function `answer_question` in [`src/ask.py`](../../src/ask.py) line 71
**Product pull request:** [#29](https://github.com/Goga-ml/AIPSD-project/pull/29) · merged commit `00c4457`. The full contract section is in [`docs/tool-contracts.md`](../../docs/tool-contracts.md).

**In one sentence, for the model:** Answer a question about what customers said in the founder's interviews, citing transcript lines like [interview_01:L11]. Says exactly "no evidence found" when the transcripts do not answer it. Reads only, changes nothing.

| | |
|---|---|
| **Effect** | reads: the `interview_NN.txt` files in the caller's workspace |
| **Undo** | nothing to undo: no state changes |
| **Idempotent?** | yes for the data. Second identical call, offline (`How do they track stock today?`, caller `founder-1`): `{"answer": "How do you track stock today? [interview_01:L8]", "abstained": false, "best_score": 1.0, "citations": [{"interview_id": "interview_01", "line": 8}]}`, equal to the first. With the real model the wording can change; the citations are always checked against what was retrieved |
| **Offered to** | signed-in founders only: `tools_for(caller)` in `src/tools.py` offers a visitor no tool with `needs_caller=True`, and this one has the default `True` |
| **Identity from** | the session: `call_tool(call, allowed, caller)` in `src/act.py`; in the MCP server, `GROUNDWORK_FOUNDER` through `Resolve(signed_in_founder)`. The caller picks the workspace (`transcripts_dir(caller)`), never an argument |
| **Touches** | the transcripts folder from `transcripts_dir(caller)` (`data/transcripts/` for now), read only; one embedding call (`embed()` in `src/llm.py`) and at most one chat call (`complete()` in `src/router.py`) per question |
| **Must never** | answer from outside the transcripts, cite a line it did not retrieve, or let the model lower the abstain threshold |

**Inputs.** Copied from `AskInterviews`. `extra="forbid"` refuses anything else.

| Argument | Type | Constraint (as written in code) | Description the model reads |
|---|---|---|---|
| `question` | `str` | `min_length=3, max_length=300, pattern=r"^[^\x00-\x1f\x7f]+$"` | The founder's question in plain words, one line, 3 to 300 characters |
| `interviews` | `list[InterviewId] \| None` | `max_length=10`; each item `^interview_[0-9]{2}$` | Only search these interviews; leave out to search all |
| `k` | `int` | `ge=1, le=10`, default 5 | How many transcript lines to retrieve, 1 to 10 |

**Expected failures.** The exact strings from `src/tools.py`.

| When | Message the model reads |
|---|---|
| an interview id that is not in the workspace | `There is no interview interview_99. Available: interview_01, interview_02, interview_03. Call again with those ids, or leave interviews out to search all.` |
| every chat model is down (the router's sorry sentence), or the embedding provider is overloaded, rate limited, timed out or unreachable | `The interview search is busy right now (the model provider is overloaded). Tell the founder to try again in a minute; do not retry immediately.` |
| arguments fail the contract (from `call_tool`) | `invalid arguments: k: Input should be less than or equal to 10` |
| a 400 or 401 (our bug, not caught by the tool) | `the tool failed unexpectedly; tell the founder and do not retry` (from `call_tool`) |

**The decision I had to make.** The first version of this function, `hw1/Goga-ml/src/ask.py`, took `--min-score` on the command line, so whoever called it could set the threshold. Copying that into the contract would have been the obvious move; I left it out. The threshold is what makes the tool say "no evidence found" instead of answering an off-topic question from weak matches (0.65, measured in [decision 0002](../../docs/decisions/0002-ask-min-score-0-65.md)). If the model could send `min_score: 0`, it could talk the tool out of abstaining whenever it wanted an answer. The threshold now lives only in `min_score()` in `src/ask.py`, read from the environment. Golden case `a2` sends `min_score: 0` and must be refused, and the red run (#33) shows that case going red as soon as `extra="forbid"` is removed.
