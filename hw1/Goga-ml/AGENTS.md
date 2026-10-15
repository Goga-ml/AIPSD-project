# AGENTS.md · Groundwork · Ask Across Interviews

*Instructions for AI coding agents working in this folder. Read this first, then `spec.md`, then `docs/INTERFACES.md` at the repo root.*

## What this project is
Groundwork is an open-source tool that turns customer-discovery interviews into evidence for founders. This folder is **Task 4: Ask Across Interviews**. It's a CLI that answers a founder's question from the interview transcripts, cites the interview and line for every claim, and says "no evidence found" when the transcripts don't contain the answer. `spec.md` is the source of truth for scope and acceptance criteria.

## Stack
- Language: Python 3.11
- Libraries: `google-genai` (Gemini chat + embeddings), `numpy` (cosine similarity), `pytest` (tests)
- Model access: Gemini API directly. Models come from env vars `GROUNDWORK_CHAT_MODEL` and `GROUNDWORK_EMBED_MODEL` (see `docs/INTERFACES.md` section 1)
- Data: `data/transcripts/*.txt` and `data/transcripts/answer_key.json` at the repo root. Chunks are kept in memory only.

## Layout
```
hw1/Goga-ml/
  spec.md · golden.md · delegation.md · journal.md · AGENTS.md
  src/
    transcript.py     ← copy of shared/transcript.py, DO NOT EDIT here
    retrieval.py      ← chunking, embedding, cosine ranking
    ask.py            ← CLI entry point: retrieve, abstain or answer, verify citations
    requirements.txt
    tests/            ← pytest; unit tests use fake embeddings, no network
```

## How to run
All commands run from the **repo root**.
```
pip install -r hw1/Goga-ml/src/requirements.txt
python hw1/Goga-ml/src/ask.py "What do people currently pay?"
python -m pytest hw1/Goga-ml
```

## Conventions
- **Follow `docs/INTERFACES.md` exactly**: transcript format, citation shape `{interview_id, line}`, inline form `[interview_NN:LNN]`, and the output JSON in section 8. Don't rename or add required fields.
- Secrets come from environment variables (`GEMINI_API_KEY`). Never write a key into a file.
- Every model call reads `usage` and adds it to the output's `usage` object, so cost is printed to stderr on every query.
- JSON result goes to stdout, logs to stderr. Exit `0` on success, `1` on error.
- When abstaining, the answer is exactly `no evidence found` and the chat model is **not called**.
- Citations are verified **in code**: any citation in the answer that isn't one of the retrieved chunks is removed and logged to stderr. Never trust the model's citations.
- Keep it small and readable. No frameworks, no classes where a function will do.
- Verify a model name with one live call before building on it. Models get retired (`gemini-2.5-flash` returned 404).
- Chunk embeddings are cached in `src/.embed_cache.json` (git-ignored). Don't re-embed the whole corpus per question; the free tier allows 100 embedding requests/minute.

## You may
- Create and edit files in `src/` (except `transcript.py`), including `src/tests/` and `src/requirements.txt`
- Propose dependency changes (ask before adding)
- Propose changes to `docs/INTERFACES.md` or `shared/`, but only as a suggestion to the human. Don't edit them.

## You may not
- Touch `.env`, other people's `hw1/` folders, `shared/`, `data/`, or `docs/`
- Delete or weaken tests to make them pass
- Call the Gemini API in loops without a cap (embedding the 3 transcripts once per run is fine; anything more needs approval)
- Add features listed under "Out of scope" in `spec.md`
