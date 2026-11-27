# AGENTS.md · Groundwork
Helps early-stage founders separate real evidence from polite answers in customer interviews, every claim cited to a transcript line. Specs: docs/INTERFACES.md, docs/DESIGN-REVIEW.md

## Commands
install:  pip install -r requirements.txt
test:     pytest

## Conventions
- Model id comes from env GROUNDWORK_CHAT_MODEL (default gemini-3.8-flash, decision 0003)
- Keys come only from env: OPENROUTER_API_KEY or GEMINI_API_KEY
- Every model call goes through src/llm.py, which writes one line to logs/usage.jsonl
- Transcripts are parsed only by shared/transcript.py; it changes only by PR
- Tools: contract in src/contracts.py, gates in src/act.py, one line per call in logs/tools.jsonl
- New feature = a test in tests/; new tool = a contract in docs/tool-contracts.md first
- Tests in tests/ never call a real model and need no key

## Always
- Run pytest before saying you are done, and paste the result
- Every model call goes through complete() in src/router.py; never call a model directly (until the router lands: one_call() in src/llm.py)

## Ask first
- Adding a dependency · changing a public response shape · editing .github/workflows/

## Never
- Read or write .env, or print a key
- Delete, skip, or weaken a test to make it pass
- Put a user, student or account id in a tool's arguments
- Add a tool that deletes or sends without asking first
