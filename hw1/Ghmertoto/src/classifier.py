"""Model boundary: build the prompt, validate the answer, retry, never fake success.

The classifier is provider-neutral: it takes any `call_model(prompt) -> str`.
`llm.GeminiClient.generate` is the real one; tests pass a fake.
"""

import json
import re
import sys
from typing import Callable

from transcript import Turn

LABELS = ("good", "leading", "hypothetical", "pitching", "compliment_fishing")
# Most severe first; the primary `label` is the first of these found in `labels`.
SEVERITY = ("leading", "pitching", "compliment_fishing", "hypothetical", "good")
MAX_ATTEMPTS = 3

RUBRIC = """You review the questions a founder asked in a customer-discovery interview.
Label each question with one or more of these labels:
- good: open-ended and neutral; asks about the customer's real past experience or current behaviour.
- leading: suggests the answer the founder wants, or embeds an assumption the customer has not stated.
- hypothetical: asks what the customer would do, pay or want in an imagined future instead of what they did.
- pitching: introduces, promotes or explains the founder's product instead of exploring the customer's problem.
- compliment_fishing: invites praise, agreement or validation of the founder's idea.
Rules:
- Use several labels only when each one is clearly justified by the wording. "good" is never combined with another label.
- A hypothetical question is not automatically leading. A question that mentions a product is not automatically compliment_fishing.
- Judge each question by its own words. You only see the founder's questions, not the customer's answers.
- explanation: at most 20 words, naming the problem in the wording (for good questions, why it works).
- suggestion: for any label other than good, one rewritten question of at most 25 words, ending with "?", that keeps the research goal but asks about real past behaviour without bias. For good questions, suggestion is null.
Return only JSON in exactly this shape:
{"questions": [{"line": <int>, "labels": [<label>, ...], "explanation": "<text>", "suggestion": "<text>" or null}]}
Answer every line below exactly once.

Questions:
"""


class InvalidModelOutput(ValueError):
    pass


class ModelUnavailable(RuntimeError):
    """Raised by a provider when retrying cannot help (for example, no API key)."""


def build_prompt(questions: list[Turn]) -> str:
    """Only interviewer questions with their line numbers. No customer text, no metadata."""
    return RUBRIC + "\n".join(f"L{q.line}: {q.text}" for q in questions)


def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", raw, flags=re.DOTALL)
    return match.group(1) if match else raw


def validate(raw: str, expected_lines: list[int]) -> dict[int, dict]:
    """Return {line: {labels, explanation, suggestion}} or raise InvalidModelOutput."""
    try:
        data = json.loads(_strip_fences(raw))
    except (json.JSONDecodeError, TypeError) as exc:
        raise InvalidModelOutput(f"not valid JSON: {exc}") from exc
    items = data.get("questions") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise InvalidModelOutput('missing "questions" list')

    out: dict[int, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            raise InvalidModelOutput("question entry is not an object")
        line, labels = item.get("line"), item.get("labels")
        explanation, suggestion = item.get("explanation"), item.get("suggestion")
        if type(line) is not int or line not in expected_lines:  # `type`, so JSON true is not line 1
            raise InvalidModelOutput(f"unexpected line: {line!r}")
        if line in out:
            raise InvalidModelOutput(f"line {line} answered twice")
        if not isinstance(labels, list) or not labels or len(set(labels)) != len(labels):
            raise InvalidModelOutput(f"line {line}: labels must be a non-empty list without repeats")
        unknown = [l for l in labels if l not in LABELS]
        if unknown:
            raise InvalidModelOutput(f"line {line}: unknown labels {unknown}")
        if "good" in labels and len(labels) > 1:
            raise InvalidModelOutput(f"line {line}: 'good' combined with another label")
        if not isinstance(explanation, str) or not explanation.strip():
            raise InvalidModelOutput(f"line {line}: missing explanation")
        is_good = labels == ["good"]
        if is_good and suggestion is not None:
            raise InvalidModelOutput(f"line {line}: good question must have suggestion null")
        if not is_good and (not isinstance(suggestion, str) or not suggestion.strip()):
            raise InvalidModelOutput(f"line {line}: problematic question needs a suggestion")
        out[line] = {
            "labels": labels,
            "explanation": explanation.strip(),
            "suggestion": suggestion.strip() if suggestion else None,
        }

    missing = [l for l in expected_lines if l not in out]
    if missing:
        raise InvalidModelOutput(f"lines not answered: {missing}")
    return out


def primary_label(labels: list[str]) -> str:
    return next(l for l in SEVERITY if l in labels)


def classify(questions: list[Turn], call_model: Callable[[str], str]) -> tuple[list[dict], bool]:
    """Classify all questions in one call, up to MAX_ATTEMPTS. Returns (entries, ok)."""
    lines = [q.line for q in questions]
    prompt = build_prompt(questions)
    verdicts = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            verdicts = validate(call_model(prompt), lines)
            break
        except ModelUnavailable as exc:
            print(f"classify: model unavailable, not retrying: {exc}", file=sys.stderr)
            break
        except Exception as exc:  # invalid output and API errors both count as a failed attempt
            print(f"classify: attempt {attempt}/{MAX_ATTEMPTS} failed: {exc}", file=sys.stderr)

    entries = []
    for q in questions:
        entry = {
            "citation": {"interview_id": q.interview_id, "line": q.line},
            "text": q.text,
        }
        v = verdicts[q.line] if verdicts else None
        if v:
            entry.update(label=primary_label(v["labels"]), labels=v["labels"],
                         explanation=v["explanation"], suggestion=v["suggestion"], status="classified")
        else:
            entry.update(label=None, labels=[], explanation=None, suggestion=None, status="unclassified")
        entries.append(entry)
    return entries, verdicts is not None
