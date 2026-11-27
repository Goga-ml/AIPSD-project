# HW2 · Tool Contract · `talk_ratio`

**Tool:** `talk_ratio` · **Owner:** `Ghmertoto` (Otar Khunashvili) · **Team repo:** https://github.com/Goga-ml/AIPSD-project
**Code on `main`:** contract class `TalkRatio` in `src/contracts.py` line `<TODO, 35 on the branch>` · function `talk_ratio` in `src/tools.py` line `<TODO, 89 on the branch>` (the counting is `talk_ratio` in `src/coach.py` line 14) · registry entry in `src/tools.py` (`TOOLS`) · MCP registration in `src/mcp_server.py`
**Product pull request:** `#<TODO>` · merged commit `<TODO short SHA>`

**In one sentence, for the model:** "Talk ratio for one customer interview: how many words the interviewer and the customer spoke, and the interviewer's share, counted by code and never estimated. Reads only, changes nothing."

| | |
|---|---|
| **Effect** | reads one transcript file in `data/transcripts/` |
| **Undo** | nothing to undo |
| **Idempotent?** | yes. The second identical call returned the same result: `{"interview_id": "interview_01", "interviewer_words": 78, "customer_words": 115, "interviewer_share": 0.4, "ratio": "40:60"}` |
| **Offered to** | signed-in founders only. `tools_for()` in `src/tools.py` decides: `if caller or not t.needs_caller`. A visitor (`caller=None`) is offered no tool, because transcripts are customers' words |
| **Identity from** | the `caller` argument of `call_tool()` in `src/act.py`, which comes from the session; in the MCP server, `signed_in_founder()` reads `GROUNDWORK_FOUNDER` on the server. Never an argument |
| **Touches** | the folder `data/transcripts/` (`transcripts_dir(caller)`), read-only, one file per call |
| **Must never** | open any file that is not `interview_NN.txt` in the caller's transcripts folder, even if the id is written to look like a path |

**Inputs.**

| Argument | Type | Constraint (as written in code) | Description the model reads |
|---|---|---|---|
| `interview_id` | `str` | `pattern=r"^interview_[0-9]{2}$"` (`InterviewId` in `src/contracts.py`); the class has `extra="forbid"` | "Interview id: the file name without .txt, like interview_01" |

**Expected failures.**

| When | Message the model reads |
|---|---|
| the id has the wrong shape | `invalid arguments: interview_id: String should match pattern '^interview_[0-9]{2}$'` |
| an argument the tool did not ask for | `invalid arguments: founder: Extra inputs are not permitted` |
| nobody is signed in | `no tool named 'talk_ratio' is available` |
| the interview does not exist | `There is no interview interview_99. Ask the founder which interview they mean; do not guess an id.` |
| the file is not a valid transcript | `interview_01 is not in the transcript format, so its words cannot be counted. Tell the founder to fix the file; do not estimate a ratio.` |
| the transcript has no turns | `interview_01 has no spoken turns, so there is no talk ratio. Tell the founder the transcript is empty; do not estimate one.` |

**The decision I had to make.** The id pattern was `^interview_\d{2}$`. It accepted `interview_٠١`, because `\d` matches digits from every script, not only 0 to 9. That id could not leave the transcripts folder, but the contract accepted something that is never a real interview id, so the model would get "there is no such interview" instead of "wrong shape". I changed the shared `InterviewId` to `[0-9]` and added a test with five ids that only look right (`test_ids_that_only_look_right_are_refused` in `tests/test_talk_ratio.py`). The change is one line in `src/contracts.py` in the product pull request. I also wrapped only the talk ratio and not the question labels from my HW1 coach: the labels need a model call, and a tool whose cases cannot run in CI without a key cannot be gated.
