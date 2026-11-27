# Groundwork · Agent Contract

*Lab 7, from `Lab-7/templates/agent-contract.md`. The code is [`src/agent.py`](../src/agent.py); the gate test is [`tests/test_agent.py`](../tests/test_agent.py). Chosen without a team vote, to keep moving; change it here first, then in code.*

1. **The goal, in one sentence.** Given a hypothesis or a question ("collect evidence on what people pay for stock tools"), find supporting or contradicting Customer quotes in the founder's interviews, verify each one, and propose saving the strongest to the founder's evidence board.
2. **The tools this loop may use.** `ask_interviews`, `get_transcript`, `verify_quote`, `save_evidence` (`LOOP_TOOLS`). Not `talk_ratio`, `check_rewrite` or `remember_focus`: the goal does not need them.
3. **The one tool that must wait for a yes, and why.** `save_evidence` (`NEEDS_YES`). It writes to the founder's evidence board, and what counts as evidence is the founder's call: a quote saved by mistake becomes a "fact" in their next decision. It lives in `PROPOSE_ONLY`, outside `TOOLS`, so `/act`, `/chat` and the MCP server can never run it; only `confirm()` does, and it checks the quote again first.
4. **The most steps it may take.** Six (`MAX_STEPS`).
5. **What the person sees before they say yes.** One line per proposed action, from `describe()`:
   `Save as spending: "We pay 45 GEL a month for a POS add-on" (interview_01)`
