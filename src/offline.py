"""Offline stand-ins for the two model calls, used when GROUNDWORK_OFFLINE=1 (tests, CI, demos without a key).

embed(): a hashed bag of words, deterministic, no network. Its scores are on a different scale from
gemini-embedding-001, so tests set GROUNDWORK_ASK_MIN_SCORE for it (tests/conftest.py).
generate(): extractive. It answers with the best-ranked excerpt and its tag, so citation checks still run.
Real answers need the real model.
"""
import hashlib
import re

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
