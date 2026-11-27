# AGENTS.md · Groundwork
Helps early-stage founders separate real evidence from polite answers in customer interviews, every claim cited to a transcript line. Specs: docs/INTERFACES.md, docs/DESIGN-REVIEW.md

## Commands
install:  pip install -r requirements.txt
test:     pytest
run:      uvicorn src.app:app --reload        (caller: X-Founder header, a stand-in for sign-in)

## Conventions
- Model id comes from env GROUNDWORK_CHAT_MODEL (default gemini-3.8-flash, decision 0003)
- Keys come only from env: OPENROUTER_API_KEY or GEMINI_API_KEY
- Only src/router.py calls one_call() in src/llm.py; llm.py writes one line per model call to logs/usage.jsonl
- The router writes one line per attempt to logs/router.jsonl; chain, limit, cache lifetime and the sorry sentence: docs/fallback-plan.md
- Transcripts are parsed only by shared/transcript.py; it changes only by PR
- Tools: contract in src/contracts.py, gates in src/act.py, one line per call in logs/tools.jsonl
- State: only src/memory.py stores anything across turns; every row is in docs/state-contract.md
- New feature = a test in tests/; new tool = a contract in docs/tool-contracts.md first
- Tests in tests/ never call a real model and need no key

## Always
- Run pytest before saying you are done, and paste the result
- Every model call goes through complete() in src/router.py; never call a model directly

## Ask first
- Adding a dependency · changing a public response shape · editing .github/workflows/

## Never
- Read or write .env, or print a key
- Delete, skip, or weaken a test to make it pass
- Put a user, student or account id in a tool's arguments
- Add a tool that deletes or sends without asking first
- Store a raw founder or session id, a recording, or anything the founder did not state (docs/state-contract.md)
- Add a memory write the founder did not ask for
