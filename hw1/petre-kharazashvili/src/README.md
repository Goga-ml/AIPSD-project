# Hypothesis linter (Groundwork · HW1 Task 2)

Type a hypothesis and get back a streamed verdict (`falsifiable` / `vague`), the reason, and a rewrite with a segment and a pass/fail threshold. A falsifiable hypothesis comes back unchanged. See `../spec.md`.

## Setup
From the repo root:
```
python3.11 -m venv hw1/petre-kharazashvili/src/.venv
hw1/petre-kharazashvili/src/.venv/bin/pip install -r hw1/petre-kharazashvili/src/requirements.txt
```

## Configure
Pick a provider with `LLM_PROVIDER`:
- `mock` (default): canned answer, no key, no cost.
- `gemini`: needs `GEMINI_API_KEY`; the model comes from `GROUNDWORK_CHAT_MODEL` (default `gemini-3.8-flash`).
- `ollama`: needs a running Ollama; set `OLLAMA_URL` and `OLLAMA_MODEL`.

Put the settings in `src/.env` (copy `.env.example`; `.env` is gitignored) or export them. The key never leaves the server.
On macOS you can keep the key in Keychain instead of a file:
```
security add-generic-password -a "$USER" -s GEMINI_API_KEY -w    # asks for the key
export GEMINI_API_KEY="$(security find-generic-password -s GEMINI_API_KEY -w)"
```

## Run
```
LLM_PROVIDER=mock hw1/petre-kharazashvili/src/.venv/bin/uvicorn app:app --app-dir hw1/petre-kharazashvili/src --port 8000
```
Open http://localhost:8000, or stream from the terminal:
```
curl -N -X POST localhost:8000/lint -H 'content-type: application/json' -d '{"hypothesis": "Farmers want better tools"}'
```
Every request logs one line to stderr from `llm.py`: model, outcome, verdict, tokens, cost and latency.

## Test
```
hw1/petre-kharazashvili/src/.venv/bin/python -m pytest hw1/petre-kharazashvili/src
```
The tests use the mock provider or fakes; they never call a paid API.

## API (INTERFACES.md section 9)
`POST /lint` with `{"hypothesis": "..."}` (at most 500 characters) returns `text/plain`, streamed:
```
VERDICT: vague
REASON: ...
REWRITE: ...
```
- Bad input: HTTP 400, `ERROR: <message>`, and no model call.
- Provider fails before the verdict: HTTP 502, `ERROR: <message>`.
- Provider fails mid-stream: the stream ends with an `ERROR: <message>` line.
