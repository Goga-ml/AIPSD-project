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

## `verify_quote` (HW2 · @heinrichcorneliusagrippa)

**In one sentence, for the model:** Check that a quote really appears in a Customer turn of one interview, and get the line to cite. Use it before citing any quote as evidence. supported=false means do not cite it. Reads only, changes nothing.

| | |
|---|---|
| **Effect** | reads |
| **Undo** | nothing to undo |
| **Idempotent?** | yes: the same quote gets the same score and line |
| **Offered to** | signed-in founders only (`tools_for(caller)`) |
| **Identity from** | the session, as for `get_transcript`. Never an argument |
| **Touches** | one `interview_NN.txt`, read only, through `shared/transcript.py` |
| **Must never** | return `supported: true` for words that are not in a Customer turn, or cite a line the code did not match |

**Inputs.** Unknown fields are refused.

| Argument | Type | Constraint | Description the model reads |
|---|---|---|---|
| `interview_id` | string | pattern `^interview_[0-9]{2}$` | Interview id: the file name without .txt, like interview_01 |
| `quote` | string | 8 to 300 characters, pattern `^[^\x00-\x1f\x7f]+$` (no newline: a quote may not span two turns) | The exact words to check, copied from one Customer turn |

**Rule.** The Task 1 check in `src/verify.py`: RapidFuzz `partial_ratio` against every Customer turn, best turn wins, supported at 90 or more. If the quote is longer than the turn, `fuzz.ratio` is used instead, so a real sentence with invented text added does not pass.

**Result.** `interview_id`, `supported`, `citation` (`{interview_id, line}`, INTERFACES section 5, only when supported), `best_line`, `match_score`, `reason` (`quote_not_found` or null). An unsupported quote is a result, not an error: the model must see the score and not cite it.

**Expected failures.** Same as `get_transcript` (no such interview, broken transcript, invalid arguments, not offered, not signed in).

**Log line.** As for every tool; `quote` is in `FREE_TEXT`, so the log keeps its length only, never the customer's words.

**Golden cases.** `evals/tools/heinrichcorneliusagrippa.yaml`: 3 normal, 1 bad input, 2 adversarial. More tests: `tests/test_verify_quote.py`.

---

## `check_rewrite`

*HW2 · owner: Petre (@Petre-Kharazashvili) · Task 2, the hypothesis linter. Write-up: `hw2/petre-kharazashvili/`.*

**In one sentence, for the model:** Check your verdict and rewrite of a founder's hypothesis before you show them: a falsifiable hypothesis comes back in the founder's exact words, and a rewrite may only state numbers the founder wrote or numbers inside [square brackets]. Reads nothing, changes nothing.

This is the code half of the linter. In HW1 the judging and the checking were one model call behind a web form. Here the model that calls the tool does the judging; the tool only decides what may be shown to the founder.

| | |
|---|---|
| **Effect** | reads nothing and changes nothing: it computes its answer from its three arguments |
| **Undo** | nothing to undo: no state changes |
| **Idempotent?** | yes: the same arguments return the same result |
| **Offered to** | every caller, signed in or not (`needs_caller=False`, so `tools_for(None)` still offers it). It touches no transcript and no stored data |
| **Identity from** | not used. The function has no `caller` parameter, and `call_tool` does not pass one |
| **Touches** | nothing: no file, no table, no network, no model |
| **Must never** | return a number to the founder as if they had said it; call a model; keep the hypothesis anywhere (the log line records its length, not its text) |

**Inputs.** Unknown fields are refused (`extra="forbid"`).

| Argument | Type | Constraint | Description the model reads |
|---|---|---|---|
| `hypothesis` | string | 1 to 500 characters, one line: pattern `^\S(?:[^\x00-\x1f\x7f]*\S)?$` | The founder's hypothesis, exactly as they wrote it, on one line |
| `verdict` | string | `falsifiable` or `vague` | Your verdict on the hypothesis |
| `rewrite` | string, optional | 1 to 1000 characters, one line, same pattern | Your rewrite. Needed when the verdict is vague. Every detail the founder did not state goes in [square brackets] |

**Result.**

| Field | Type | Note |
|---|---|---|
| `verdict` | `falsifiable` \| `vague` | as given |
| `rewrite` | string | what to show the founder. For `falsifiable` it is the `hypothesis` argument itself, whatever `rewrite` was sent |
| `unchanged` | bool | true when `rewrite` is the founder's exact words |
| `to_confirm` | list of strings | the details inside [square brackets]: what the founder must confirm or choose |

**Expected failures.** Each one raises `ToolFailure`; `call_tool` returns it as `{ok: false, error: <message>}`.

| When | Message the model reads |
|---|---|
| vague, and no rewrite was sent | A vague hypothesis needs a rewrite. Send one in `rewrite`, with every detail the founder did not state in [square brackets]. |
| vague, and the rewrite repeats the hypothesis | The rewrite repeats the founder's words, so it is still vague. Rewrite it with a specific segment, a past behavior and a threshold, each in [square brackets] if the founder did not state it. |
| vague, and the rewrite states a number the founder did not write | The rewrite states 3, 29 as if the founder had said it. Put each one in [square brackets] or remove it, then call check_rewrite again. |
| vague, and the rewrite has nothing in brackets | The rewrite marks nothing in [square brackets], so the founder cannot tell what you assumed. Put every detail they did not state in [square brackets], then call check_rewrite again. |
| arguments fail the contract | invalid arguments: verdict: Input should be 'falsifiable' or 'vague' |

**What it does not check.** Only numbers are compared with the founder's text. An invented segment written in words and left outside brackets is not caught.

**Tests and golden cases.** `tests/test_check_rewrite.py`; golden file `evals/tools/petre-kharazashvili.yaml`, run by `tests/test_tool_golden.py` in CI.

**Log line.** `hypothesis` and `rewrite` are in `FREE_TEXT` in `src/act.py`: the log keeps their lengths, not a founder's idea.

---

## HW2 owners

Each member wraps the function from their own task in `TEAM-CONTRACT.md`. No two people wrap the same one. Fill your own row in your HW2 product pull request.

| Member | GitHub | Function (TEAM-CONTRACT task) | Tool name | Effect |
|---|---|---|---|---|
| Goga | @Goga-ml | Task 4 · ask across interviews (RAG lookup) | | reads |
| Petre | @Petre-Kharazashvili | Task 2 · hypothesis linter (the code half: verdict and rewrite check) | `check_rewrite` | reads nothing stored |
| Otar | @Ghmertoto | Task 3 · interview technique coach (talk ratio, question labels) | `talk_ratio` | reads |
| Dachi | @heinrichcorneliusagrippa | Task 1 · verified evidence extraction (quote check) | `verify_quote` | reads |
