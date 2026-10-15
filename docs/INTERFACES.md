# Groundwork · Interface Agreement (v1)

Everyone builds one of the four HW1 tasks separately. This file fixes the parts we share, so the pieces fit together later without rewrites: the transcript format, the parser, the JSON shapes, citations, and config.

**Read this before you write code. Do not change it on your own** (see section 11).

---

## 0. Who does what

| # | Task | Owner | Reads | Produces |
|---|------|-------|-------|----------|
| 0 | Test transcripts + answer key (first, ~30 min) | _TBD_ | — | `data/transcripts/*` |
| 1 | Verified evidence extraction (CLI) | _TBD_ | transcripts | evidence JSON (section 6) |
| 2 | Hypothesis linter (web form, streaming) | _TBD_ | user input | streamed text (section 9) |
| 3 | Interview technique coach (CLI) | _TBD_ | transcripts | coach JSON (section 7) |
| 4 | Ask across interviews (CLI) | _TBD_ | transcripts | answer JSON (section 8) |

Tasks 1, 3 and 4 all read transcripts, so **nobody starts until task 0 is pushed.**

---

## 1. Stack and shared rules

- **Python 3.11.** Main libraries: `google-genai` (Gemini), `rapidfuzz` (task 1), `fastapi` + `uvicorn` (task 2). Keep your own `requirements.txt` in your HW folder.
- **API key** comes only from the environment variable `GEMINI_API_KEY`. Never put a key in a file you commit. `.env` must be in `.gitignore`.
- **Models** are set by environment variable, so we all use the same ones:

  | Variable | Value we agreed on | Price (USD per 1M tokens) |
  |---|---|---|
  | `GROUNDWORK_CHAT_MODEL` | _fill in_ | in: _ · out: _ |
  | `GROUNDWORK_EMBED_MODEL` | _fill in_ | in: _ |

- **Every model call records its usage** (tokens in and out, cost). Shape in section 5.
- **CLI conventions:** run from the repo root. Print the JSON result to **stdout**. Print logs and progress to **stderr**. Exit code `0` on success, `1` on error.

---

## 2. Repo layout

```
data/
  transcripts/
    interview_01.txt
    interview_02.txt
    interview_03.txt
    answer_key.json        ← planted facts, used by everyone's golden.md
shared/
  transcript.py            ← the one parser everyone uses (section 4)
docs/
  INTERFACES.md            ← this file
hw1/<name>/                ← each person's HW1 (spec, golden, delegation, journal, src/)
```

HW1 is graded per folder, so **copy `shared/transcript.py` into your own `src/` unchanged.** If it needs a fix, fix `shared/` (section 11) and everyone copies it again.

---

## 3. Transcript format

Plain text. These rules are strict, because citations depend on them.

1. File name is `interview_NN.txt`, UTF-8. The **interview id** is the file name without `.txt` (for example `interview_01`).
2. Optional header lines at the top, in the form `# key: value`. Supported keys: `segment`, `date`, `role`. Parsers read them as metadata; they are not turns.
3. **One turn = one line.** It starts with exactly `Interviewer: ` or `Customer: ` (capital letter, colon, one space). A turn never wraps onto a second line.
4. Blank lines are allowed and ignored.
5. Any other line is an error: the parser raises, it does not guess.
6. One interviewer and one customer per file.
7. **Line numbers are the physical line numbers in the file, starting at 1**, the same as your editor shows. Headers and blank lines count. Every citation in every task uses these numbers.

Example:

```
# segment: independent cafe owners
# date: 2026-10-10

Interviewer: Tell me about the last time you ran out of an ingredient.
Customer: Last Saturday we ran out of oat milk by 11, lost maybe twenty orders.
Interviewer: Wouldn't an app that predicts stock be great for you?
Customer: Sure, sounds nice.
Interviewer: How do you track stock today?
Customer: A paper sheet on the fridge, and I text my supplier every Thursday.
Interviewer: Do you pay for anything to help with that?
Customer: We pay 45 GEL a month for a POS add-on, but it doesn't do inventory.
```

Here line 5 is a pain, line 6 is a leading question, line 9 is a workaround and line 11 is spending.

---

## 4. Shared parser · `shared/transcript.py`

Everyone uses this. Nobody writes their own.

```python
from dataclasses import dataclass, field
from pathlib import Path

SPEAKERS = ("Interviewer", "Customer")


@dataclass
class Turn:
    interview_id: str
    line: int        # physical 1-based line number in the file
    speaker: str     # "Interviewer" or "Customer"
    text: str        # without the "Speaker: " prefix, stripped

    @property
    def words(self) -> int:
        return len(self.text.split())


@dataclass
class Transcript:
    interview_id: str
    meta: dict[str, str] = field(default_factory=dict)
    turns: list[Turn] = field(default_factory=list)

    def by(self, speaker: str) -> list[Turn]:
        return [t for t in self.turns if t.speaker == speaker]


def parse_transcript(path: str | Path) -> Transcript:
    path = Path(path)
    tr = Transcript(interview_id=path.stem)
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            key, _, value = line.lstrip("#").partition(":")
            tr.meta[key.strip()] = value.strip()
            continue
        for sp in SPEAKERS:
            if line.startswith(sp + ": "):
                tr.turns.append(Turn(tr.interview_id, n, sp, line[len(sp) + 2:].strip()))
                break
        else:
            raise ValueError(f"{path.name}:{n}: not a valid turn: {raw!r}")
    return tr
```

**Word count** (used by task 3) is always `Turn.words`, which splits on whitespace. That keeps everyone's numbers identical.

---

## 5. Shared JSON pieces

**Citation.** It always points at a turn:

```json
{ "interview_id": "interview_01", "line": 11 }
```

Inside text written for people, a citation looks like this: **`[interview_01:L11]`**.

**Usage.** Every output that involved model calls includes this:

```json
"usage": {
  "model": "<GROUNDWORK_CHAT_MODEL>",
  "calls": 2,
  "input_tokens": 1830,
  "output_tokens": 412,
  "cost_usd": 0.00041
}
```

If you used several calls or models, sum the tokens and cost. `cost_usd` uses the prices in section 1.

---

## 6. Task 1 · Evidence JSON

Command: `python <your src>/extract.py data/transcripts/interview_01.txt > data/evidence/interview_01.json`

```json
{
  "interview_id": "interview_01",
  "evidence": [
    {
      "id": "interview_01-e1",
      "type": "spending",
      "summary": "Pays 45 GEL/month for a POS add-on that lacks inventory.",
      "quote": "We pay 45 GEL a month for a POS add-on",
      "citation": { "interview_id": "interview_01", "line": 11 },
      "match_score": 100.0
    }
  ],
  "rejected": [
    {
      "type": "pain",
      "summary": "Loses customers to chains.",
      "quote": "we lose most customers to Starbucks",
      "best_line": 5,
      "match_score": 48.0,
      "reason": "quote_not_found"
    }
  ],
  "stats": { "extracted": 6, "accepted": 5, "rejected": 1, "attempts": 1 },
  "usage": { "...": "see section 5" }
}
```

Rules:
- `type` must be one of: `pain`, `workaround`, `spending`, `commitment` (lowercase).
- Quotes must come from **Customer** turns only. A quote may not span two turns.
- **Matching is done in code, not trusted from the model.** For each quote, compute `rapidfuzz.fuzz.partial_ratio(quote, turn.text)` against every Customer turn and keep the best one. If the score is **≥ 90**, accept it and set `citation.line` to that turn's line. Otherwise, move it to `rejected` with `reason: "quote_not_found"`.
- If the model returns invalid JSON or the wrong shape, retry up to **3 attempts** in total. If all fail, exit `1`.
- Print `accepted N, rejected M` to stderr.
- `id` is `<interview_id>-e<n>`, numbered in output order.

---

## 7. Task 3 · Coach JSON

Command: `python <your src>/coach.py data/transcripts/interview_01.txt [--format md]`

```json
{
  "interview_id": "interview_01",
  "talk_ratio": {
    "interviewer_words": 37,
    "customer_words": 45,
    "interviewer_share": 0.45
  },
  "questions": [
    {
      "citation": { "interview_id": "interview_01", "line": 6 },
      "text": "Wouldn't an app that predicts stock be great for you?",
      "label": "leading",
      "suggestion": "How do you decide how much stock to order?"
    }
  ],
  "usage": { "...": "see section 5" }
}
```

Rules:
- The talk ratio is **computed in code** with `Turn.words`. `interviewer_share = interviewer_words / (interviewer_words + customer_words)`, rounded to 2 decimals.
- **Every Interviewer turn counts as a question** and is sent to the model. Customer text is never sent.
- `label` must be one of: `good`, `leading`, `hypothetical`, `pitching`, `compliment_fishing`.
- `suggestion` is `null` when the label is `good`.
- `--format md` prints a short human-readable report instead of JSON. JSON is the default.

---

## 8. Task 4 · Ask JSON

Command: `python <your src>/ask.py "What do people currently pay?" [--min-score X]`

```json
{
  "question": "What do people currently pay?",
  "answer": "One owner pays 45 GEL a month for a POS add-on [interview_01:L11].",
  "abstained": false,
  "best_score": 0.82,
  "citations": [ { "interview_id": "interview_01", "line": 11 } ],
  "retrieved": [
    { "citation": { "interview_id": "interview_01", "line": 11 }, "score": 0.82 }
  ],
  "usage": { "...": "see section 5, include embedding tokens" }
}
```

Rules:
- **One chunk = one turn**, both speakers. The text that gets embedded is `"<speaker>: <text>"`. The chunk id is its citation.
- Use cosine similarity. Storage (in memory or SQLite) is the owner's choice and is not shared.
- If `best_score < min_score`, then `answer` is exactly **`no evidence found`**, `abstained` is `true`, `citations` is `[]` and the chat model is not called. Write the default `min_score` you chose here: _fill in_.
- Every inline citation in `answer` must appear in `citations`, and must be one of the `retrieved` chunks.
- Print the per-query cost to stderr: `cost: $0.00041 (1830 in / 412 out)`.

---

## 9. Task 2 · Linter HTTP

- `GET /` serves the form.
- `POST /lint` takes JSON `{"hypothesis": "..."}` and returns a **streamed** `text/plain` response.
- The streamed text has exactly three labelled lines, in this order:

```
VERDICT: vague
REASON: No segment, no measurable threshold, and nothing that could prove it wrong.
REWRITE: At least 6 of 10 smallholder farmers in Imereti will say they lost a harvest to late pest detection in the past year.
```

- `VERDICT` is `falsifiable` or `vague`. If it is `falsifiable`, `REWRITE` repeats the input **unchanged**.
- Default port: `8000`.

---

## 10. Answer key · `data/transcripts/answer_key.json`

Whoever writes the transcripts also writes this file. Everyone's `golden.md` checks against it.

```json
{
  "interview_01": {
    "segment": "independent cafe owners",
    "planted": [
      { "type": "pain",       "line": 5,  "fact": "ran out of oat milk, lost ~20 orders" },
      { "type": "workaround", "line": 9,  "fact": "paper sheet + texts supplier" },
      { "type": "spending",   "line": 11, "fact": "45 GEL/month POS add-on" }
    ],
    "leading_question_lines": [6],
    "unrelated_question": "What programming language do they use?"
  }
}
```

Plant in each transcript at least one `pain`, `workaround` and `spending`, at least one `commitment` across the set, and two or more bad questions (leading, hypothetical or pitching). Line numbers must match the file exactly.

---

## 11. Changing this agreement

- This is **v1**. To change anything shared (this file, `shared/`, `data/`), open a PR, bump the version at the top, and post on Teams before merging.
- Additive changes (a new optional field) are fine. Renaming or removing a field needs everyone to agree.
