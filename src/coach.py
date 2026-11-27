"""Interview technique coach, the part that needs no model: the talk ratio.

Moved from hw1/Ghmertoto/src/talk_ratio.py (HW1, Task 3) with one change: the parser import
now points at shared/transcript.py. Pure functions, no I/O.

Formula (hw1/Ghmertoto/spec.md, D2):
    interviewer_share = interviewer_words / (interviewer_words + customer_words), rounded to 2 decimals
Words are `Turn.words` (whitespace split of the turn text), so speaker labels,
`#` headers and blank lines are never counted.
"""
from shared.transcript import Transcript


def talk_ratio(tr: Transcript) -> dict:
    interviewer = sum(t.words for t in tr.by("Interviewer"))
    customer = sum(t.words for t in tr.by("Customer"))
    total = interviewer + customer
    return {
        "interviewer_words": interviewer,
        "customer_words": customer,
        "interviewer_share": round(interviewer / total, 2) if total else None,
    }


def percentages(ratio: dict) -> tuple[int, int] | None:
    """Whole-number percentages that always add up to 100, or None when nothing was said."""
    total = ratio["interviewer_words"] + ratio["customer_words"]
    if not total:
        return None
    interviewer_pct = round(ratio["interviewer_words"] * 100 / total)
    return interviewer_pct, 100 - interviewer_pct
