"""Verified evidence extraction (Groundwork Task 1).

Usage (from the repo root):
        python hw1/heinrichcorneliusagrippa/src/extract.py data/transcripts/interview_01.txt > hw1/heinrichcorneliusagrippa/results/interview_01.json
Stdout: evidence JSON (docs/INTERFACES.md section 6). Stderr: logs + "accepted N, rejected M".
Exit:   0 on success, 1 on a bad transcript or no valid model reply after 3 attempts.

Split of work: the model proposes (type, summary, quote). Code decides what is true:
pydantic checks the shape, verify.py checks the quote is really in a Customer turn.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parent))  # lets `python src/extract.py` import siblings

from pydantic import BaseModel, ValidationError  # noqa: E402

import verify  # noqa: E402
from transcript import Transcript, parse_transcript  # noqa: E402

MAX_ATTEMPTS = 3


class Item(BaseModel):
    type: Literal["pain", "workaround", "spending", "commitment"]
    summary: str
    quote: str


class Reply(BaseModel):
    evidence: list[Item]


class ExtractionFailed(Exception):
    pass


SYSTEM = """You extract evidence from one customer-discovery interview transcript.

Evidence types:
- pain: a specific problem the customer actually experienced, ideally with what it cost them.
- workaround: what the customer does today to cope with the problem.
- spending: money or time the customer ALREADY spends today, including a clear "we pay nothing".
  Not what they say they might pay in the future.
- commitment: a concrete next step the customer agreed to (a date, an introduction, sending data, a trial).

Rules:
1. Quote only from lines that start with "Customer:". Never quote the interviewer.
2. "quote" must be copied character for character from ONE Customer line: a contiguous piece of
   that line, without the "Customer: " prefix. Do not fix grammar, translate, shorten, or join lines.
3. Keep each quote short: the one sentence or clause that proves the item.
4. Polite or hypothetical answers ("maybe", "sounds useful", "I would try it") are not evidence.
5. If there is no evidence of a type, return nothing for it. Never invent evidence.
"summary" is one short sentence in your own words."""


def render(tr: Transcript) -> str:
    return "\n".join(f"{t.speaker}: {t.text}" for t in tr.turns)


def ask_model(tr: Transcript, call) -> tuple[Reply, int, dict]:
    """Call the model until the reply validates, at most MAX_ATTEMPTS times."""
    usage = {"model": None, "calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
    base = f"Transcript {tr.interview_id}:\n\n{render(tr)}"
    error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        user = base if error is None else (
            f"{base}\n\nYour previous reply was rejected by the validator:\n{error}\n"
            "Reply again with JSON that matches the schema exactly."
        )
        text, u = call(SYSTEM, user, Reply)
        usage["model"] = u["model"]
        usage["calls"] += 1
        usage["input_tokens"] += u["input_tokens"]
        usage["output_tokens"] += u["output_tokens"]
        usage["cost_usd"] = round(usage["cost_usd"] + u["cost_usd"], 6)
        try:
            return Reply.model_validate_json(text), attempt, usage
        except ValidationError as e:
            error = str(e)[:500]
            print(f"attempt {attempt}/{MAX_ATTEMPTS}: invalid reply: {error}", file=sys.stderr)
    raise ExtractionFailed(f"no valid reply after {MAX_ATTEMPTS} attempts")


def verify_items(tr: Transcript, reply: Reply) -> tuple[list[dict], list[dict]]:
    accepted, rejected = [], []
    for item in reply.evidence:
        m = verify.best_match(item.quote, tr)
        if verify.is_supported(m):
            accepted.append({
                "id": f"{tr.interview_id}-e{len(accepted) + 1}",
                "type": item.type,
                "summary": item.summary,
                "quote": item.quote,
                "citation": {"interview_id": tr.interview_id, "line": m.line},
                "match_score": m.score,
            })
        else:
            rejected.append({
                "type": item.type,
                "summary": item.summary,
                "quote": item.quote,
                "best_line": m.line,
                "match_score": m.score,
                "reason": "quote_not_found",
            })
            print(f"rejected (score {m.score}, best line {m.line}): {item.quote!r}", file=sys.stderr)
    return accepted, rejected


def extract(tr: Transcript, call) -> dict:
    reply, attempts, usage = ask_model(tr, call)
    accepted, rejected = verify_items(tr, reply)
    return {
        "interview_id": tr.interview_id,
        "evidence": accepted,
        "rejected": rejected,
        "stats": {
            "extracted": len(reply.evidence),
            "accepted": len(accepted),
            "rejected": len(rejected),
            "attempts": attempts,
        },
        "usage": usage,
    }


def main(argv: list[str] | None = None, call=None) -> int:
    parser = argparse.ArgumentParser(description="Extract verified evidence from one transcript.")
    parser.add_argument("transcript", help="path to interview_NN.txt")
    args = parser.parse_args(argv)
    try:
        tr = parse_transcript(args.transcript)
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if call is None:
        import llm
        call = llm.complete_json
    try:
        result = extract(tr, call)
    except (ExtractionFailed, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    s = result["stats"]
    print(f"accepted {s['accepted']}, rejected {s['rejected']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
