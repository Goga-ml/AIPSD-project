# HW2 · Evidence · `ask_interviews` · Goga-ml

**Where the cases live:** [`evals/tools/Goga-ml.yaml`](../../evals/tools/Goga-ml.yaml), run by `tests/test_tool_golden.py` in CI job `test` (workflow `ci`). The cases run offline: `tests/conftest.py` sets `GROUNDWORK_OFFLINE=1`, and `src/offline.py` stands in for the embedding and chat calls (a hashed bag of words and an extractive answer). They test the contract, the gates and the wiring, not retrieval quality.

Actual results below were produced on 27 November 2026 by running every case through `call_tool()` on the code of #29 (commit `aaa8857`), offline.

| # | Type | Call, exactly as in the yaml | Expected | Actual result | Pass? |
|---|---|---|---|---|---|
| g1 | normal | `ask_interviews {question: "How do they track stock today?"}`, caller `founder-1` | ok · `abstained: false` | `{"answer": "How do you track stock today? [interview_01:L8]", "abstained": false, "best_score": 1.0, "citations": [{"interview_id": "interview_01", "line": 8}]}` | pass |
| g2 | normal | `ask_interviews {question: "Which football team won the last World Cup?"}`, caller `founder-1` | ok · `answer: no evidence found, abstained: true, citations: []` | `{"answer": "no evidence found", "abstained": true, "best_score": 0.0, "citations": []}` | pass |
| g3 | normal | `ask_interviews {question: "What do people pay?", interviews: [interview_99]}`, caller `founder-1` | refused · error has "there is no interview interview_99", "interview_01" | `There is no interview interview_99. Available: interview_01, interview_02, interview_03. Call again with those ids, or leave interviews out to search all.` | pass |
| b1 | bad-input | `ask_interviews {question: "What do people pay?", k: 50}`, caller `founder-1` | refused · error has "invalid arguments", "k" | `invalid arguments: k: Input should be less than or equal to 10` | pass |
| a1 | adversarial | `ask_interviews {question: "What do people pay?", interviews: ["../../.env"]}`, caller `founder-1` | refused · error has "invalid arguments", "interviews" | `invalid arguments: interviews.0: String should match pattern '^interview_[0-9]{2}$'` | pass |
| a2 | adversarial | `ask_interviews {question: "How do I bake sourdough at home?", min_score: 0}`, caller `founder-1` | refused · error has "invalid arguments", "min_score" | `invalid arguments: min_score: Extra inputs are not permitted` | pass |

g1 cites an Interviewer line because the offline answer is extractive: it repeats the best-ranked line. What the case checks is that the cited line was really retrieved. Choosing a Customer line is the real model's job (`SYSTEM_PROMPT` in `src/ask.py`).

**The adversarial cases, in one sentence each:** a1 is a model (or text a founder pasted) trying to make the tool open our key file as if it were an interview; a2 is a model that wants an answer badly enough to switch off the rule that makes it say "no evidence found" when the founder's interviews do not support one.

**The red run.**
- Branch: `hw2-Goga-ml-red`. My contract was not on `main` yet, so the branch is my product branch (#29) plus one line; the pull request diff therefore also shows #29.
- What I weakened, the whole change, in `class AskInterviews` in `src/contracts.py`:
  ```diff
  +    model_config = ConfigDict(extra="allow")
  ```
- Pull request: [#33](https://github.com/Goga-ml/AIPSD-project/pull/33) (closed, not merged; branch deleted)
- Run link: https://github.com/Goga-ml/AIPSD-project/actions/runs/46039827243 (the `pull_request` run; the `push` run on the same commit also failed: https://github.com/Goga-ml/AIPSD-project/actions/runs/46039816364)
- Tests that failed, pasted from the run:
  ```
  FAILED tests/test_ask.py::test_contract_refuses_unknown_fields_like_min_score_or_a_founder - Failed: DID NOT RAISE ValidationError
  FAILED tests/test_ask.py::test_schema_the_model_sees_has_no_identity_or_threshold - assert True is False
  FAILED tests/test_tool_golden.py::test_tool_golden_case[Goga-ml:a2] - AssertionError: Goga-ml:a2 should be refused but ran: {'answer': 'no evidence found', 'abstained': True, 'best_score': 0.289, 'citations': []}
  ```
- Merge state GitHub reported: `mergeable: MERGEABLE` (no conflicts), `mergeStateStatus: BLOCKED`, required check `test` failed. The pull request also had no approval, so the failed check is the evidence for the gate, not the button alone.

*The same weakening locally: 3 failed, 114 passed.*

**What the red run taught me.** I expected removing `extra="forbid"` to let `min_score: 0` lower the threshold. It did not: `a2` "ran" and still abstained with a score of 0.289, because the tool never reads a `min_score` field. Pydantic now accepts it and the code ignores it. So `extra="forbid"` was not what kept the threshold safe; leaving the field out of the code was. What `extra="forbid"` adds is that the model is told its argument was refused, instead of believing it worked. That sent me to check the MCP door, and there the same thing happens on the real code: through a stdio MCP session, `min_score: 0` and an extra `founder` are dropped silently, not refused, while `../../.env` as an interview id is refused through both doors (below). Our both-doors test compares schemas, so it cannot see this difference.

**The green run.** Product pull request [#29](https://github.com/Goga-ml/AIPSD-project/pull/29) · run link https://github.com/Goga-ml/AIPSD-project/actions/runs/46039440116 · last line of pytest: `117 passed`, locally on the same commit (`117 passed in 2.43s`).

**Through the MCP door.** Client: the MCP Python SDK's `ClientSession` over stdio, launching `python -m src.mcp_server` exactly as a host would, with `GROUNDWORK_FOUNDER=founder-1` and `GROUNDWORK_OFFLINE=1` (there is no OpenRouter key yet, see #16, so the router cannot reach a chat model). Tools listed: `get_transcript`, `talk_ratio`, `check_rewrite`, `ask_interviews`. Calls, in order:

| Arguments sent | Result |
|---|---|
| `{"question": "How do they track stock today?"}` | ok · `{"answer": "How do you track stock today? [interview_01:L8]", "abstained": false, "best_score": 1.0, "citations": [{"interview_id": "interview_01", "line": 8}]}` |
| `{"question": "How do I bake sourdough at home?", "min_score": 0}` | ok, the extra argument ignored · `{"answer": "no evidence found", "abstained": true, "best_score": 0.289, "citations": []}` |
| `{"question": "What do people pay?", "interviews": ["../../.env"]}` | error · `1 validation error ... interviews.0 String should match pattern '^interview_[0-9]{2}$'` |

Not done yet: a question typed into Claude Code with a live model, which needs `OPENROUTER_API_KEY`. The live part I could run: earlier the same day, with the real Gemini embeddings and before the router, "How do I bake sourdough at home?" scored 0.634 and abstained without a chat call, the same score as in decision 0002; "What do people currently pay?" reached the chat model and got a 503 from Gemini, which is why the tool now turns an outage into a message instead of a stack trace.
