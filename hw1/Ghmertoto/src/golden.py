"""Live golden check: run the real model on the golden transcripts and compare with the answer key.

    python golden.py            # needs GEMINI_API_KEY; costs about $0.005 per run

Not a pytest test on purpose: tests never call a real model. Prints one verdict line per check
and exits 1 if any check fails.
"""

import json
import sys
from pathlib import Path

from coach import run, to_markdown
from llm import GeminiClient

FIXTURES = Path(__file__).parent / "tests" / "fixtures"


def check(interview: str, key: dict) -> list[tuple[str, bool]]:
    client = GeminiClient()
    result, code = run(str(FIXTURES / f"{interview}.txt"), client.generate, client.usage)
    print(to_markdown(result) + "\n")
    by_line = {q["citation"]["line"]: q for q in result["questions"]}
    flagged_good = [l for l in key["good_question_lines"] if by_line[l]["label"] not in ("good", None)]
    problems = [q for q in result["questions"] if q["status"] == "classified" and q["label"] != "good"]
    return [
        ("exit code 0, all classified", code == 0),
        ("talk ratio equals hand count", result["talk_ratio"] == key["hand_count"]),
        ("every planted leading line has 'leading'",
         all("leading" in by_line[l]["labels"] for l in key["leading_question_lines"])),
        ("every expected label present",
         all(set(want) <= set(by_line[int(l)]["labels"]) for l, want in key["expected_labels"].items())),
        (f"planted good questions flagged: {flagged_good} (allowed: at most 1)", len(flagged_good) <= 1),
        ("explanations <= 20 words, rewrites <= 25 words ending in '?'",
         all(len(q["explanation"].split()) <= 20 and len(q["suggestion"].split()) <= 25
             and q["suggestion"].endswith("?") for q in problems)),
    ]


def main() -> int:
    key = json.loads((FIXTURES / "answer_key.json").read_text(encoding="utf-8"))
    sys.stdout.reconfigure(encoding="utf-8")
    failed = 0
    for interview in key:
        print(f"=== {interview}")
        for name, ok in check(interview, key[interview]):
            print(f"{'PASS' if ok else 'FAIL'}  {name}")
            failed += not ok
        print()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
