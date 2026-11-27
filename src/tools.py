"""The tools behind the contracts in src/contracts.py. Spec: docs/tool-contracts.md.

Every tool takes a validated contract (never raw model output) and returns a pydantic result.
An expected failure raises ToolFailure with a message written for the model: what happened and
what to do next, never a path, a file name or a stack trace. Anything else is a bug.

Nothing here writes, sends or deletes.
"""
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

from pydantic import BaseModel

from shared.transcript import parse_transcript

from . import ask, coach
from .contracts import AskInterviews, Contract, GetTranscript, TalkRatio

ROOT = Path(__file__).resolve().parents[1]
META_KEYS = ("segment", "date", "role")          # INTERFACES.md section 3: the only header keys


class ToolFailure(Exception):
    """An expected failure. The message goes back to the model, so it says what to do next."""


def caller_key(caller: str) -> str:
    """Logs keep a short hash of the caller, never the id itself."""
    return hashlib.sha256(caller.encode()).hexdigest()[:12]


def transcripts_dir(caller: str) -> Path:
    """The caller's workspace. One shared demo workspace for now; per-founder folders later
    change only this function, never a tool's arguments."""
    return Path(os.environ.get("GROUNDWORK_TRANSCRIPTS", ROOT / "data" / "transcripts"))


# ---------------------------------------------------------------- results

class TurnOut(BaseModel):
    line: int                                   # physical line number, for [interview_01:L11]
    speaker: Literal["Interviewer", "Customer"]
    text: str


class TranscriptOut(BaseModel):
    interview_id: str
    meta: dict[str, str]
    turns: list[TurnOut]
    total_turns: int                            # before the speaker filter and max_turns
    truncated: bool


# ---------------------------------------------------------------- get_transcript

def get_transcript(args: GetTranscript, caller: str) -> TranscriptOut:
    path = transcripts_dir(caller) / f"{args.interview_id}.txt"   # safe: the id matched ^interview_[0-9]{2}$
    if not path.is_file():
        raise ToolFailure(f"There is no interview {args.interview_id}. "
                          "Ask the founder which interview they mean; ids look like interview_01.")
    try:
        tr = parse_transcript(path)
    except ValueError:
        raise ToolFailure(f"{args.interview_id} is not in the transcript format, so it cannot be cited. "
                          "Tell the founder to fix the file; do not guess its content.") from None
    turns = [t for t in tr.turns if args.speaker is None or t.speaker == args.speaker]
    return TranscriptOut(
        interview_id=tr.interview_id,
        meta={k: v for k, v in tr.meta.items() if k in META_KEYS},
        turns=[TurnOut(line=t.line, speaker=t.speaker, text=t.text) for t in turns[: args.max_turns]],
        total_turns=len(tr.turns),
        truncated=len(turns) > args.max_turns,
    )


# ---------------------------------------------------------------- talk_ratio (HW2 · Ghmertoto)

class TalkRatioOut(BaseModel):
    interview_id: str
    interviewer_words: int
    customer_words: int
    interviewer_share: float                    # 0.0 to 1.0, two decimals
    ratio: str                                  # "interviewer:customer" in whole percent, adds up to 100


def talk_ratio(args: TalkRatio, caller: str) -> TalkRatioOut:
    path = transcripts_dir(caller) / f"{args.interview_id}.txt"   # safe: the id matched ^interview_[0-9]{2}$
    if not path.is_file():
        raise ToolFailure(f"There is no interview {args.interview_id}. "
                          "Ask the founder which interview they mean; do not guess an id.")
    try:
        tr = parse_transcript(path)
    except ValueError:
        raise ToolFailure(f"{args.interview_id} is not in the transcript format, so its words cannot be counted. "
                          "Tell the founder to fix the file; do not estimate a ratio.") from None
    counts = coach.talk_ratio(tr)
    pct = coach.percentages(counts)
    if pct is None:
        raise ToolFailure(f"{args.interview_id} has no spoken turns, so there is no talk ratio. "
                          "Tell the founder the transcript is empty; do not estimate one.")
    return TalkRatioOut(interview_id=tr.interview_id, ratio=f"{pct[0]}:{pct[1]}", **counts)


# ---------------------------------------------------------------- ask_interviews (HW2 · Goga-ml)

class Citation(BaseModel):
    interview_id: str
    line: int                                   # physical line number, for [interview_01:L11]


class AskOut(BaseModel):
    answer: str             # with inline tags like [interview_01:L11], or exactly "no evidence found"
    abstained: bool
    best_score: float       # cosine score of the best transcript line; below the threshold means abstain
    citations: list[Citation]


def _model_unavailable(e: Exception) -> bool:
    """Every chat model down (the router's sorry), or the embedding provider overloaded, rate limited,
    timed out or unreachable: expected, not our bug. A 400 or 401 is our bug and is not caught here."""
    if isinstance(e, ask.ModelUnavailable):
        return True
    if "Timeout" in type(e).__name__ or "Connection" in type(e).__name__:
        return True
    status = getattr(e, "status_code", None) or getattr(e, "code", None)
    return isinstance(status, int) and (status == 429 or status >= 500)


def ask_interviews(args: AskInterviews, caller: str) -> AskOut:
    """Reads only: retrieves transcript lines from the caller's workspace and answers from them."""
    folder = transcripts_dir(caller)
    if args.interviews:
        known = ask.known_interviews(folder)
        unknown = sorted(set(args.interviews) - set(known))
        if unknown:
            raise ToolFailure(f"There is no interview {', '.join(unknown)}. Available: {', '.join(known)}. "
                              "Call again with those ids, or leave interviews out to search all.")
    try:
        out = ask.ask(args.question, folder, interviews=args.interviews, k=args.k)
    except Exception as e:
        if not _model_unavailable(e):
            raise                                   # anything else is a bug: call_tool reports it, nothing leaks
        raise ToolFailure("The interview search is busy right now (the model provider is overloaded). "
                          "Tell the founder to try again in a minute; do not retry immediately.") from None
    return AskOut(answer=out["answer"], abstained=out["abstained"], best_score=out["best_score"],
                  citations=[Citation(**c) for c in out["citations"]])


# ---------------------------------------------------------------- the registry

@dataclass(frozen=True)
class Tool:
    name: str
    args: type[Contract]
    run: Callable[..., BaseModel]
    needs_caller: bool = True     # call_tool passes the caller from the session; the model cannot

    def schema(self) -> dict:
        """What the model sees: name, description and JSON Schema, all from the contract."""
        return {"type": "function", "function": {
            "name": self.name, "description": " ".join(self.args.__doc__.split()),
            "parameters": self.args.model_json_schema()}}


TOOLS = {t.name: t for t in [
    Tool("get_transcript", GetTranscript, get_transcript),
    Tool("talk_ratio", TalkRatio, talk_ratio),
    Tool("ask_interviews", AskInterviews, ask_interviews),
]}


def tools_for(caller: str | None) -> dict[str, Tool]:
    """Least privilege by construction: transcripts are customers' words, so a caller who is
    not signed in is offered no tool that needs a caller."""
    return {n: t for n, t in TOOLS.items() if caller or not t.needs_caller}
