"""Check every quote against the transcript in code. The model's word is never trusted.

Rule (docs/INTERFACES.md section 6): for each quote, score it with
rapidfuzz.fuzz.partial_ratio against every Customer turn and keep the best turn.
Score >= THRESHOLD -> accepted, cited to that turn's line. Otherwise -> rejected.

One extra guard: partial_ratio slides the SHORTER string along the longer one.
If the model returns a quote longer than the turn (a real sentence plus invented
text), the turn fits inside the quote and scores 100. So when the quote is longer
than the turn we score with fuzz.ratio (whole string vs whole string) instead.
"""
from dataclasses import dataclass

from rapidfuzz import fuzz

from transcript import Transcript

THRESHOLD = 90.0


@dataclass
class Match:
    line: int | None   # line of the best Customer turn, None if there are no Customer turns
    score: float       # 0..100, rounded to 1 decimal


def score(quote: str, turn_text: str) -> float:
    if len(quote) > len(turn_text):
        return fuzz.ratio(quote, turn_text)
    return fuzz.partial_ratio(quote, turn_text)


def best_match(quote: str, tr: Transcript) -> Match:
    best = Match(line=None, score=0.0)
    for turn in tr.by("Customer"):
        s = score(quote, turn.text)
        if s > best.score:
            best = Match(line=turn.line, score=s)
    best.score = round(best.score, 1)
    return best


def is_supported(m: Match) -> bool:
    return m.line is not None and m.score >= THRESHOLD
