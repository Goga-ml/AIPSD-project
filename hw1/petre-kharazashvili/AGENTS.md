# AGENTS.md · Groundwork · Hypothesis Linter

*Instructions for AI coding agents working in this folder. Read this first, then `spec.md`, then `docs/INTERFACES.md` at the repo root. Adapted from the team's file in `hw1/Goga-ml/AGENTS.md`.*

## What this project is
Groundwork is an open-source, self-hostable tool that turns customer-discovery interviews into evidence for founders. This folder is **Task 2: Hypothesis Linter**. It's a single-page web form where a founder types a hypothesis and gets back a streamed verdict (`falsifiable` or `vague`), a reason, and a rewrite with a segment and a pass/fail threshold. `spec.md` is the source of truth for scope and acceptance criteria.

## Stack
- Language: Python 3.11
- Libraries: `fastapi` + `uvicorn` (server, `StreamingResponse`), `google-genai` (Gemini), `httpx` (Ollama client, test client), `pytest` (tests)
- Front end: one static HTML file, vanilla JS and inline CSS. The stream is read with `fetch` + `ReadableStream` (POST, so no `EventSource`).
- Model access: chosen by `LLM_PROVIDER=gemini|ollama|mock`. Gemini uses `GEMINI_API_KEY` and `GROUNDWORK_CHAT_MODEL` (see `docs/INTERFACES.md` section 1). Ollama uses `OLLAMA_URL` and `OLLAMA_MODEL`. `mock` needs no key.
- Data: none stored. Each request is independent.

## Layout
```
hw1/petre-kharazashvili/
  spec.md · golden.md · delegation.md · journal.md · AGENTS.md
  src/
    app.py            ← FastAPI app: GET /, POST /lint
    llm.py            ← every model call: gemini / ollama / mock behind one interface, logs tokens, cost, latency
    parser.py         ← incremental parser for the VERDICT/REASON/REWRITE format
    prompt.txt        ← system prompt with the rubric and few-shot examples
    static/index.html ← the form
    requirements.txt · .env.example · .gitignore · README.md
    tests/            ← pytest; uses the mock provider, no network
```

## How to run
All commands run from the **repo root**.
```
pip install -r hw1/petre-kharazashvili/src/requirements.txt
LLM_PROVIDER=mock uvicorn app:app --app-dir hw1/petre-kharazashvili/src --port 8000
python -m pytest hw1/petre-kharazashvili/src
```

## Conventions
- **Follow `docs/INTERFACES.md` section 9 exactly**: `POST /lint`, JSON `{"hypothesis": "..."}`, streamed `text/plain`, three labelled lines in order, lowercase verdict. Don't rename or add required fields.
- Secrets come from environment variables (`GEMINI_API_KEY`), loaded from a gitignored `.env`. Never write a key into a file you commit. The key never reaches the browser.
- Every model call reads its token usage and logs it to stderr with the cost.
- Validate input before any model call. Bad input never reaches a provider.
- Keep it small and readable. No frameworks on the front end, no classes where a function will do.

## You may
- Create and edit files in `src/`, including `src/tests/` and `src/requirements.txt`
- Propose dependency changes (ask before adding)
- Propose changes to `docs/INTERFACES.md` or `shared/`, but only as a suggestion to the human. Don't edit them.

## You may not
- Touch `.env`, other people's `hw1/` folders, `shared/`, `data/`, or `docs/`
- Delete or weaken tests to make them pass
- Call the Gemini API in loops without a cap (golden runs are 3 calls; anything more needs approval)
- Add features listed under "Out of scope" in `spec.md`
