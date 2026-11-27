# HW2 · Tool Contract · `talk_ratio`

**Tool:** `talk_ratio` · **Owner:** `Ghmertoto` (Otar Khunashvili) · **Team repo:** https://github.com/Goga-ml/AIPSD-project
**Code on `main`:** contract class `TalkRatio` in `src/contracts.py` line `<TODO>` · function `talk_ratio` in `src/tools.py` line `<TODO>` (the counting is `talk_ratio` in `src/coach.py`) · registry entry in `src/tools.py` (`TOOLS`) · MCP registration in `src/mcp_server.py`
**Product pull request:** `#<TODO>` · merged commit `<TODO short SHA>`

**In one sentence, for the model:** "Talk ratio for one interview: interviewer and customer word counts and the interviewer's share, counted by code. Reads only."

| | |
|---|---|
| **Effect** | reads one transcript file in `data/transcripts/` |
| **Undo** | nothing to undo |
| **Idempotent?** | yes. The second identical call returned the same result: `{"interview_id": "interview_01", "interviewer_words": 78, "customer_words": 115, "interviewer_share": 0.4, "ratio": "40:60"}` |
| **Offered to** | every caller, signed in or not: `tools_for()` in `src/tools.py` keeps every tool whose `writes` is `False` (`if caller or not t.writes`) |
| **Identity from** | the `caller` argument of `call_tool()` in `src/act.py`, set by our server; in the MCP server, `signed_in_founder()` reads `GROUNDWORK_FOUNDER`. Never an argument, and this tool does not use it at all |
| **Touches** | the folder `data/transcripts/`, read-only, one file per call, through `load_interview()` |
| **Must never** | open any file that is not `data/transcripts/interview_NN.txt`, even if the id is written to look like a path |

**Inputs.**

| Argument | Type | Constraint (as written in code) | Description the model reads |
|---|---|---|---|
| `interview_id` | `str` | `pattern=r"^interview_[0-9]{2}$"` (`InterviewId` in `src/contracts.py`); the class has `extra="forbid"` | "Interview id, like interview_01" |

**Expected failures.**

| When | Message the model reads |
|---|---|
| the id has the wrong shape | `invalid arguments: interview_id: String should match pattern '^interview_[0-9]{2}$'` |
| an argument the tool did not ask for | `invalid arguments: founder: Extra inputs are not permitted` |
| the interview does not exist | `There is no interview_99. Ask the founder which interview they mean; do not guess an id.` |
| the file is not a valid transcript | `interview_01 is not a valid transcript, so it cannot be read. Tell the founder the file needs fixing; do not guess its content.` |
| the transcript has no turns | `interview_01 has no spoken turns, so there is no talk ratio. Tell the founder the transcript is empty; do not estimate one.` |

**The decision I had to make.** The first version of the id pattern was `^interview_\d{2}$`. It accepted `interview_٠١`, because `\d` matches digits from every script, not only 0 to 9. That id could not leave the transcripts folder, but the contract accepted something that is never a real interview id, so the model would get "there is no such interview" instead of "wrong shape". I changed the pattern to `[0-9]` and added a test with five ids that only look right (`test_ids_that_only_look_right_are_refused` in `tests/test_talk_ratio.py`). The change is one line in `src/contracts.py` in the product pull request. I also chose to wrap only the talk ratio and not the question labels from my HW1 coach: the labels need a model call, and a tool whose cases cannot run in CI without a key cannot be gated.
