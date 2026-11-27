"""Groundwork's fallback chain: every model call in src/ goes through complete().

Built from the Lab 8 starter (Lab-8/templates/router_starter.py in the course repo). Only the
import and the four settings are ours; the reasons for each are in docs/fallback-plan.md.

Three ideas, and nothing else:
  the chain   for each kind of job, an ordered list of models. Ask the first; if it cannot
              answer, ask the next. The last link is a sentence we wrote, not a model.
  the limit   one model gets TIMEOUT_S seconds. Slow counts as down.
  the cache   the same question inside CACHE_TTL_S seconds is answered from memory, for free.

Every call writes one line to logs/router.jsonl. `python -m src.router` prints the summary
for docs/measurements.md.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

# Our one model call. The router needs exactly this shape:
#   one_call(messages, tools, timeout=..., model=...) -> {"content", "tool_calls", "usage": {"cost_usd"}}
# Given a timeout, one_call() switches the SDK's own retries off: the chain is the retry.
from src.llm import one_call

CHAINS = {                                      # per job, who answers, in order. Two companies.
    "chat": ["google/gemini-3.8-flash", "anthropic/claude-haiku-5.5"],
}
TIMEOUT_S = 30                                  # seconds one model gets (fallback-plan.md, line 3)
CACHE_TTL_S = 600                               # seconds an answer may be reused. 0 = never
SORRY = ("Groundwork cannot reach its models right now. Your transcripts and earlier results "
         "were not changed. Please try again in a few minutes.")

CACHE: dict[str, tuple[float, dict]] = {}       # key -> (when, answer). A dict is enough for today.
LOG = Path(os.environ.get("ROUTER_LOG", "logs/router.jsonl"))


def temporary(error: Exception) -> bool:
    """Is the next model worth a try? A timeout, a dropped connection, a 429 or a 5xx: yes.
    A 400, 401 or 403 is our own bug. Another model will not fix it, so it is raised."""
    name = type(error).__name__
    return ("Timeout" in name or "Connection" in name
            or getattr(error, "status_code", None) in (408, 429, 500, 502, 503, 504))


def complete(messages: list[dict], tools: list[dict] | None = None, job: str = "chat", call=one_call) -> dict:
    key = hashlib.sha256(json.dumps([job, messages], sort_keys=True).encode()).hexdigest()
    saved = CACHE.get(key)
    if saved and not tools and time.time() - saved[0] < CACHE_TTL_S:      # THE CACHE: seen it, still fresh
        return note(job, "cache", saved[1], saved_usd=cost(saved[1]))
    for place, model in enumerate(CHAINS[job], start=1):                  # THE CHAIN: first, then next
        started = time.perf_counter()
        try:
            answer = call(messages, tools or [], timeout=TIMEOUT_S, model=model)      # THE LIMIT
        except Exception as error:
            if not temporary(error):
                raise                                                     # our bug: fail loudly
            note(job, "failed", model=model, place=place, why=type(error).__name__)
            continue                                                      # their outage: next model
        if not tools:
            CACHE[key] = (time.time(), answer)                            # only plain answers are reused
        return note(job, "ok", answer, model=model, place=place, cost_usd=cost(answer),
                    ms=int((time.perf_counter() - started) * 1000))
    return note(job, "exhausted", {"content": SORRY, "tool_calls": [], "degraded": True})


def cost(answer: dict) -> float:
    return (answer.get("usage") or {}).get("cost_usd", 0.0)


def note(job: str, outcome: str, answer: dict | None = None, **fields) -> dict | None:
    """One line per attempt. This file is the evidence for the before/after table."""
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(json.dumps({"ts": round(time.time(), 3), "job": job, "outcome": outcome, **fields}) + "\n")
    return answer


def summary(path: Path | None = None) -> dict:
    """Read the log, count what happened. `python -m src.router` prints it."""
    path = path or LOG
    lines = [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
    count = lambda outcome: sum(1 for x in lines if x["outcome"] == outcome)      # noqa: E731
    ok = sorted(x["ms"] for x in lines if x["outcome"] == "ok")
    return {"requests": count("ok") + count("cache") + count("exhausted"),
            "answered_by_first_model": sum(1 for x in lines if x["outcome"] == "ok" and x["place"] == 1),
            "answered_by_a_fallback": sum(1 for x in lines if x["outcome"] == "ok" and x["place"] > 1),
            "answered_from_cache": count("cache"),
            "sorry_message": count("exhausted"),
            "failed_attempts": count("failed"),
            "median_ms": ok[len(ok) // 2] if ok else None,
            "spent_usd": round(sum(x.get("cost_usd", 0) for x in lines), 6),
            "saved_by_cache_usd": round(sum(x.get("saved_usd", 0) for x in lines), 6)}


if __name__ == "__main__":
    for name, value in summary().items():
        print(f"{name:<26} {value}")
