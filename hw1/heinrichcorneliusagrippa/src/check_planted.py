"""Compare evidence JSON files with the answer key: was every planted fact recovered?

Usage (from the repo root):
        python hw1/heinrichcorneliusagrippa/src/check_planted.py data/transcripts/answer_key.json hw1/heinrichcorneliusagrippa/results/interview_0*.json
A planted fact counts as recovered when an ACCEPTED evidence item has the same type
and cites the same line. Exit 0 if every planted fact in the given files is recovered.
"""
import json
import sys


def check(key: dict, result: dict) -> list[tuple[dict, bool]]:
    got = {(e["type"], e["citation"]["line"]) for e in result["evidence"]}
    return [(p, (p["type"], p["line"]) in got) for p in key[result["interview_id"]]["planted"]]


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 1
    key = json.load(open(argv[0], encoding="utf-8"))
    found = total = 0
    for path in argv[1:]:
        result = json.load(open(path, encoding="utf-8"))
        s = result["stats"]
        print(f"{result['interview_id']}: accepted {s['accepted']}, rejected {s['rejected']}")
        for p, ok in check(key, result):
            total += 1
            found += ok
            print(f"  [{'x' if ok else ' '}] {p['type']:<10} L{p['line']:<3} {p['fact']}")
    print(f"recovered {found}/{total}")
    return 0 if found == total else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
