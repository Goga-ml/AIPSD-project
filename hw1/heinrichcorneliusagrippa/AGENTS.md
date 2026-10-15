# AGENTS.md · Groundwork · Verified Evidence Extraction (HW1)
CLI that turns one interview transcript into evidence JSON, keeping only quotes found in the transcript. Spec: spec.md · Shared formats: docs/INTERFACES.md v1, section 6

## Commands (run from the repo root, like the rest of the team)
install:  pip install -r hw1/heinrichcorneliusagrippa/src/requirements.txt
run:      python hw1/heinrichcorneliusagrippa/src/extract.py data/transcripts/interview_01.txt > hw1/heinrichcorneliusagrippa/results/interview_01.json
test:     pytest hw1/heinrichcorneliusagrippa        (no API key, no network)

## Conventions
- Python 3.11+. Model from GROUNDWORK_CHAT_MODEL (default gemini-3.8-flash), key from GEMINI_API_KEY only.
- Every model call goes through src/llm.py, which logs tokens, cost and latency to stderr.
- JSON result on stdout, logs on stderr. Exit 0 on success, 1 on error.
- Transcripts and answer key: data/transcripts/ (shared, read-only for this task). Line numbers are physical
  file lines from 1. Only src/transcript.py (a copy of shared/transcript.py) parses them.
- The model never decides what is true: quotes are checked in src/verify.py, shapes by pydantic.
- Every new rule ships with a test that would fail without it.

## Always
- Run `pytest hw1/heinrichcorneliusagrippa` before saying you are done, and paste the result

## Ask first
- Adding a dependency
- Changing the JSON output shape or the 90 threshold (both are shared with the team)
- Editing src/transcript.py or anything in data/ (shared with the team; change by PR, INTERFACES section 11)

## Never
- Read or write .env, or print a key
- Delete, skip, or weaken a test to make it pass
- Call the real model from a test, or in a loop without a cap
- Touch files outside hw1/heinrichcorneliusagrippa/
