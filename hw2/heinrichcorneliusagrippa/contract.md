# HW2 · Tool Contract · `verify_quote`

**Tool:** `verify_quote` · **Owner:** `heinrichcorneliusagrippa` (Dachi Khelashvili) · **Team repo:** https://github.com/Goga-ml/AIPSD-project
**Code on `main`:** contract class `VerifyQuote` in [`src/contracts.py` line 83](https://github.com/Goga-ml/AIPSD-project/blob/1f3a47d/src/contracts.py#L83) · function `verify_quote` in [`src/tools.py` line 205](https://github.com/Goga-ml/AIPSD-project/blob/1f3a47d/src/tools.py#L205) (the check itself is `best_match` in [`src/verify.py` line 35](https://github.com/Goga-ml/AIPSD-project/blob/1f3a47d/src/verify.py#L35), copied from my HW1) · registry entry in [`src/tools.py` line 244](https://github.com/Goga-ml/AIPSD-project/blob/1f3a47d/src/tools.py#L244) (`TOOLS`) · MCP registration in [`src/mcp_server.py` line 85](https://github.com/Goga-ml/AIPSD-project/blob/1f3a47d/src/mcp_server.py#L85)
**Product pull request:** [#32](https://github.com/Goga-ml/AIPSD-project/pull/32) (issue [#30](https://github.com/Goga-ml/AIPSD-project/issues/30)) · merged commit `1f3a47d`

**In one sentence, for the model:** "Check that a quote really appears in a Customer turn of one interview, and get the line to cite. Use it before citing any quote as evidence. supported=false means do not cite it. Reads only, changes nothing."

| | |
|---|---|
| **Effect** | reads. It scores one quote against one transcript and changes nothing |
| **Undo** | nothing to undo |
| **Idempotent?** | yes. The second identical call returns the same result: `{"interview_id": "interview_01", "supported": true, "citation": {"interview_id": "interview_01", "line": 11}, "best_line": 11, "match_score": 100.0, "reason": null}` |
| **Offered to** | signed-in founders only. `tools_for(caller)` in [`src/tools.py` line 248](https://github.com/Goga-ml/AIPSD-project/blob/1f3a47d/src/tools.py#L248) drops every tool with `needs_caller=True` when there is no caller |
| **Identity from** | the session: `call_tool(call, allowed, caller)` in `src/act.py`; over MCP, `Founder = Annotated[str, Resolve(signed_in_founder)]` reads `GROUNDWORK_FOUNDER` on the server. Never an argument |
| **Touches** | one file, read only: `data/transcripts/<interview_id>.txt`, parsed by `shared/transcript.py` |
| **Must never** | say `supported: true` for words that are not in a Customer turn, or cite a line the code did not match |

**Inputs.** Copied from `VerifyQuote`. Unknown fields are refused (`extra="forbid"` on the `Contract` base class).

| Argument | Type | Constraint (as written in code) | Description the model reads |
|---|---|---|---|
| `interview_id` | string | `pattern=r"^interview_[0-9]{2}$"` | Interview id: the file name without .txt, like interview_01 |
| `quote` | string | `min_length=8, max_length=300, pattern=r"^[^\x00-\x1f\x7f]+$"` | The exact words to check, copied from one Customer turn, 8 to 300 characters |

**Expected failures.** The exact strings from the code.

| When | Message the model reads |
|---|---|
| no such interview | There is no interview interview_99. Ask the founder which interview they mean; ids look like interview_01. |
| transcript breaks the format | interview_07 is not in the transcript format, so no quote in it can be verified. Tell the founder to fix the file; do not cite it. |
| quote spans two turns | invalid arguments: quote: String should match pattern '^[^\x00-\x1f\x7f]+$' |
| identity in the arguments | invalid arguments: founder: Extra inputs are not permitted |
| not signed in | no tool named 'verify_quote' is available |

A quote that is not in the transcript is not a failure. It comes back as `supported: false`, `reason: "quote_not_found"`, with the best line and its score, the same way my HW1 extractor keeps it in `rejected[]` instead of hiding it.

**The decision I had to make.** In HW1 the rule "a quote may not span two turns" lived in the model's instructions, and was enforced only indirectly: a two-turn quote matched no single turn well and got rejected after scoring. In the tool, that rule moved into the contract: `quote` is capped at 300 characters and may not contain a newline, so INTERFACES section 6 ("a quote may not span two turns") is now checked by code before the matcher runs (golden `b1`). I also kept the tool to one `interview_id` per call instead of searching every interview at once, which is what a model would find easiest: that way a citation can only point at the interview the model named, and the tool never reads more transcripts than it needs.
