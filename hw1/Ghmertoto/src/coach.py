"""Interview Technique Coach CLI (INTERFACES section 7).

    python coach.py <transcript.txt> [--format md] [--no-llm]

JSON goes to stdout, logs and errors to stderr. Exit 0 on success, 1 on any error.
"""

import argparse
import json
import sys
from typing import Callable

from classifier import classify
from talk_ratio import percentages, talk_ratio
from transcript import parse_transcript

NO_USAGE = {"model": None, "calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}


def run(path: str, call_model: Callable[[str], str] | None, usage: dict | None = None) -> tuple[dict | None, int]:
    """Coach one transcript. `call_model=None` means --no-llm. Returns (result, exit_code)."""
    try:
        tr = parse_transcript(path)
    except (ValueError, OSError) as exc:  # malformed line or unreadable file: no output, no model call
        print(f"error: {exc}", file=sys.stderr)
        return None, 1

    result = {"interview_id": tr.interview_id, "talk_ratio": talk_ratio(tr), "questions": [], "usage": NO_USAGE}
    if not tr.turns:
        print(f"error: {tr.interview_id} has no Interviewer or Customer turns", file=sys.stderr)
        return result, 1

    questions = tr.by("Interviewer")
    if call_model is None or not questions:
        return result, 0

    result["questions"], ok = classify(questions, call_model)
    result["usage"] = usage if usage is not None else NO_USAGE
    if not ok:
        print("error: no valid classification from the model; questions are unclassified", file=sys.stderr)
        return result, 1
    return result, 0


def to_markdown(result: dict) -> str:
    ratio = result["talk_ratio"]
    pct = percentages(ratio)
    talk = (f"interviewer {ratio['interviewer_words']} words ({pct[0]}%) · "
            f"customer {ratio['customer_words']} words ({pct[1]}%) · ratio {pct[0]}:{pct[1]}"
            if pct else "no words spoken")
    lines = [f"# Interview coach · {result['interview_id']}", "", f"**Talk:** {talk}"]

    questions = result["questions"]
    if questions:
        to_fix = [q for q in questions if q["status"] == "classified" and q["label"] != "good"]
        unclassified = sum(q["status"] == "unclassified" for q in questions)
        lines += ["", f"**Questions:** {len(questions)} asked · {len(to_fix)} to rewrite"
                      + (f" · {unclassified} not classified (model failed)" if unclassified else ""),
                  "*Labels are model judgments, not facts. Check them against the transcript.*", ""]
        # One line per flagged question and one line for all good ones, so 20 questions stay under 40 lines.
        for q in to_fix:
            lines.append(f"- L{q['citation']['line']} · **{', '.join(q['labels'])}** · \"{q['text']}\" "
                         f"→ Try: \"{q['suggestion']}\" ({q['explanation']})")
        good = [f"L{q['citation']['line']}" for q in questions if q["label"] == "good"]
        if good:
            lines.append(f"- Good: {', '.join(good)}")
        failed = [f"L{q['citation']['line']}" for q in questions if q["status"] == "unclassified"]
        if failed:
            lines.append(f"- Not classified: {', '.join(failed)}")
    usage = result["usage"]
    if usage["calls"]:
        lines += ["", f"*{usage['model']} · {usage['calls']} call(s) · {usage['input_tokens']} in / "
                      f"{usage['output_tokens']} out · ${usage['cost_usd']:.5f}*"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Coach the interviewer's technique in one transcript.")
    parser.add_argument("transcript")
    parser.add_argument("--format", choices=("json", "md"), default="json")
    parser.add_argument("--no-llm", action="store_true", help="talk ratio only, no model call")
    args = parser.parse_args(argv)

    call_model, usage = None, None
    if not args.no_llm:
        from llm import GeminiClient
        client = GeminiClient()
        call_model, usage = client.generate, client.usage

    result, code = run(args.transcript, call_model, usage)
    if result is not None:
        sys.stdout.reconfigure(encoding="utf-8")
        print(to_markdown(result) if args.format == "md" else json.dumps(result, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
