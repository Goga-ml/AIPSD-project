# Tool contracts · Groundwork

*From `Lab-5/templates/tool-contract.md`. One section per tool. Every rule here exists in code: `src/contracts.py` (the contract), `src/tools.py` (the tool and the `TOOLS` registry), `src/act.py` (the three gates and the log). A new tool gets its section here before its code (AGENTS.md).*

## `get_transcript`

**In one sentence, for the model:** Read one customer interview: every turn with its speaker and its line number, for citations like [interview_01:L11]. Reads only, changes nothing.

| | |
|---|---|
| **Effect** | reads |
| **Undo** | nothing to undo: no state changes |
| **Idempotent?** | yes: the same arguments return the same turns |
| **Offered to** | signed-in founders only (`tools_for(caller)`). A visitor is offered nothing: transcripts are customers' words |
| **Identity from** | the session: `call_tool(call, allowed, caller)` gets `caller` from the app; the MCP server gets it from the environment it was started with (`GROUNDWORK_FOUNDER`) through `Resolve(...)`. Never an argument |
| **Touches** | one file, read only: `<workspace>/<interview_id>.txt`, parsed by `shared/transcript.py`. The workspace is `data/transcripts/` for now (`transcripts_dir(caller)`) |
| **Must never** | open any file other than an `interview_NN.txt` in the caller's workspace (not `answer_key.json`, not `.env`), or write anything |

**Inputs.** Unknown fields are refused (`extra="forbid"`).

| Argument | Type | Constraint | Description the model reads |
|---|---|---|---|
| `interview_id` | string | pattern `^interview_\d{2}$` | Interview id: the file name without .txt, like interview_01 |
| `speaker` | string, optional | `Interviewer` or `Customer` | Only this speaker's turns. Leave out for both |
| `max_turns` | integer | 1 to 200, default 100 | How many turns to return |

**Result.**

| Field | Type | Note |
|---|---|---|
| `interview_id` | string | |
| `meta` | object of strings | only the header keys `segment`, `date`, `role` (INTERFACES.md section 3) |
| `turns` | list of `{line: int, speaker: "Interviewer" \| "Customer", text: string}` | `line` is the physical line number every citation uses |
| `total_turns` | int | before the speaker filter and `max_turns` |
| `truncated` | bool | true if `max_turns` cut the list |

No file path, no owner, no internal id.

**Expected failures.** Each one raises `ToolFailure`; `call_tool` returns it as `{ok: false, error: <message>}`.

| When | Message the model reads |
|---|---|
| no such interview | There is no interview interview_99. Ask the founder which interview they mean; ids look like interview_01. |
| file breaks the transcript format | interview_07 is not in the transcript format, so it cannot be cited. Tell the founder to fix the file; do not guess its content. |
| arguments fail the contract | invalid arguments: interview_id: String should match pattern '^interview_\d{2}$' |
| not offered to this caller | no tool named 'get_transcript' is available |
| no caller in the session | not signed in: ask the founder to sign in first |
| a bug in the tool | the tool failed unexpectedly; tell the founder and do not retry |

None of them contains a path, a file name or a stack trace.

**Tests and golden cases.**

| Case | Expect | Where |
|---|---|---|
| a valid call | runs; turns carry physical line numbers (interview_01 first Customer turn is line 5) | `tests/test_act.py::test_valid_call_runs_and_cites_physical_lines` · golden `t1`, `t2` |
| invalid arguments | refused before the tool runs (the parser is replaced by one that fails the test if called) | `test_invalid_arguments_never_reach_the_tool` · golden `t4` |
| not offered to this caller | refused, nothing runs | `test_a_tool_not_offered_never_runs` · golden `t7` |
| identity in the arguments | refused (`founder`, `user_id`, `caller`); no identity field in any schema | `test_the_model_cannot_set_identity` · golden `t6` |
| adversarial: path in the id (`../transcripts/answer_key`) | refused by the pattern | golden `t5` |
| expected failures | message says what to do next, leaks nothing | `test_expected_failures_tell_the_model_what_to_do_and_leak_nothing` · golden `t3` |

Golden file: `evals/tools/team-get-transcript.yaml`, run by `tests/test_tool_golden.py` in CI. Checked locally: dropping `extra="forbid"` turns `t6` and the identity test red; removing the id pattern turns `t5` and the invalid-arguments test red.

**Log line.** One line per call in `logs/tools.jsonl` (`GROUNDWORK_TOOL_LOG` in tests): time, tool, arguments, ok, error, a 12-character hash of the caller, latency. It leaves out the caller id and the result, because the result is customers' words. Argument names listed in `FREE_TEXT` in `src/act.py` are logged as a length only.

---

## HW2 owners

Each member wraps the function from their own task in `TEAM-CONTRACT.md`. No two people wrap the same one. Fill your own row in your HW2 product pull request.

| Member | GitHub | Function (TEAM-CONTRACT task) | Tool name | Effect |
|---|---|---|---|---|
| Goga | @Goga-ml | Task 4 · ask across interviews (RAG lookup) | | reads |
| Petre | @Petre-Kharazashvili | Task 2 · hypothesis linter | | reads |
| Otar | @Ghmertoto | Task 3 · interview technique coach (talk ratio, question labels) | | reads |
| Dachi | @heinrichcorneliusagrippa | Task 1 · verified evidence extraction (quote check) | `verify_quote` | reads |
