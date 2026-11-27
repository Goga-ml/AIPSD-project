"""Offline stand-ins for the two model calls, used when GROUNDWORK_OFFLINE=1 (tests, CI, demos without a key).

embed(): a hashed bag of words, deterministic, no network. Its scores are on a different scale from
gemini-embedding-001, so tests set GROUNDWORK_ASK_MIN_SCORE for it (tests/conftest.py).
generate(): extractive. It answers with the best-ranked excerpt and its tag, so citation checks still run.
Real answers need the real model.
"""
import hashlib
import re
from types import SimpleNamespace as NS

import numpy as np

DIM = 4096
STOP = set("a an and are as at be but by did do does for from has have how i in is it its me my of on or "
           "our so that the their them they this to was we were what when where which who why will with "
           "you your people currently last like just about would could any anything".split())


def _vector(text: str) -> np.ndarray:
    v = np.zeros(DIM)
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        if word in STOP or word in ("customer", "interviewer"):
            continue
        v[int(hashlib.md5(word.encode()).hexdigest(), 16) % DIM] += 1.0
    return v


def embed(texts: list[str], task_type: str = "") -> list[np.ndarray]:
    return [_vector(t) for t in texts]


def generate(prompt: str) -> str:
    first = re.search(r"^(\[interview_\d+:L\d+\]) (?:Customer|Interviewer): (.+)$", prompt, re.MULTILINE)
    return f"{first.group(2)} {first.group(1)}" if first else "no evidence found"


def stream_chunks(messages: list[dict]):
    """A streamed answer without a model: the last user message echoed back in word-sized pieces,
    then a usage chunk, in the shape the OpenAI SDK yields. No tool calls."""
    question = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    words = f"Offline answer to: {question}".split(" ")
    for i, word in enumerate(words):
        piece = word if i == 0 else " " + word
        yield NS(usage=None, choices=[NS(delta=NS(content=piece, tool_calls=None))])
    yield NS(usage=NS(prompt_tokens=sum(len(m.get("content") or "") for m in messages) // 4,
                      completion_tokens=len(words)), choices=[])
