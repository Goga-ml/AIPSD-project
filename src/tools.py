"""The tools behind the contracts in src/contracts.py. Spec: docs/tool-contracts.md.

Every tool takes a validated contract (never raw model output) and returns a pydantic result.
An expected failure raises ToolFailure with a message written for the model: what happened and
what to do next, never a path, a file name or a stack trace. Anything else is a bug.

Nothing here writes, sends or deletes.
"""
import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

from pydantic import BaseModel

from shared.transcript import parse_transcript

from . import ask, coach, verify
from .contracts import (AskInterviews, CheckRewrite, Contract, GetTranscript, RememberFocus, SaveEvidence,
                        TalkRatio, VerifyQuote)

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


# ---------------------------------------------------------------- check_rewrite (HW2 · Petre)

class RewriteOut(BaseModel):
    verdict: Literal["falsifiable", "vague"]
    rewrite: str                                # what to show the founder
    unchanged: bool                             # True: rewrite is the founder's exact words
    to_confirm: list[str]                       # the details inside [square brackets]


BRACKETED = re.compile(r"\[([^\[\]]*)\]")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


def check_rewrite(args: CheckRewrite) -> RewriteOut:
    """The model proposes a verdict and a rewrite; this decides what the founder may be shown.
    No caller, no file, no model: the answer depends on the three arguments and nothing else."""
    if args.verdict == "falsifiable":           # INTERFACES.md section 9: the input comes back unchanged
        return RewriteOut(verdict="falsifiable", rewrite=args.hypothesis, unchanged=True, to_confirm=[])
    if args.rewrite is None:
        raise ToolFailure("A vague hypothesis needs a rewrite. Send one in `rewrite`, with every detail "
                          "the founder did not state in [square brackets].")
    if args.rewrite.casefold() == args.hypothesis.casefold():
        raise ToolFailure("The rewrite repeats the founder's words, so it is still vague. Rewrite it with a "
                          "specific segment, a past behavior and a threshold, each in [square brackets] "
                          "if the founder did not state it.")
    to_confirm, outside = [], args.rewrite
    while BRACKETED.search(outside):            # innermost first, so nested brackets are handled too
        to_confirm += [m.strip() for m in BRACKETED.findall(outside) if m.strip()]
        outside = BRACKETED.sub(" ", outside)
    said = set(NUMBER.findall(args.hypothesis))
    invented = list(dict.fromkeys(n for n in NUMBER.findall(outside) if n not in said))
    if invented:
        raise ToolFailure(f"The rewrite states {', '.join(invented)} as if the founder had said it. Put each one "
                          "in [square brackets] or remove it, then call check_rewrite again.")
    if not to_confirm:
        raise ToolFailure("The rewrite marks nothing in [square brackets], so the founder cannot tell what you "
                          "assumed. Put every detail they did not state in [square brackets], then call "
                          "check_rewrite again.")
    return RewriteOut(verdict="vague", rewrite=args.rewrite, unchanged=False, to_confirm=to_confirm)


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


# ---------------------------------------------------------------- verify_quote (HW2 · heinrichcorneliusagrippa)

class QuoteCheck(BaseModel):
    interview_id: str
    supported: bool                        # true only at match_score >= 90 against a Customer turn
    citation: Citation | None              # set only when supported (INTERFACES section 5)
    best_line: int | None                  # the closest Customer line, also when not supported
    match_score: float                     # 0 to 100, rounded to 1 decimal
    reason: Literal["quote_not_found"] | None


def verify_quote(args: VerifyQuote, caller: str) -> QuoteCheck:
    """The model proposes, code decides: the Task 1 check (src/verify.py), now callable by a model."""
    path = transcripts_dir(caller) / f"{args.interview_id}.txt"   # safe: the id matched ^interview_[0-9]{2}$
    if not path.is_file():
        raise ToolFailure(f"There is no interview {args.interview_id}. "
                          "Ask the founder which interview they mean; ids look like interview_01.")
    try:
        tr = parse_transcript(path)
    except ValueError:
        raise ToolFailure(f"{args.interview_id} is not in the transcript format, so no quote in it can be verified. "
                          "Tell the founder to fix the file; do not cite it.") from None
    m = verify.best_match(args.quote, tr)
    ok = verify.is_supported(m)
    return QuoteCheck(interview_id=tr.interview_id, supported=ok,
                      citation=Citation(interview_id=tr.interview_id, line=m.line) if ok else None,
                      best_line=m.line, match_score=m.score, reason=None if ok else "quote_not_found")


# ---------------------------------------------------------------- remember_focus (Lab 6 · team)

class FocusStored(BaseModel):
    segment: str
    lifetime: str
    delete_with: str


def remember_focus(args: RememberFocus, caller: str) -> FocusStored:
    """Adds one row for this founder (src/memory.py). Written only when the founder asks: the model is told
    so in the description, and the reply names how to delete it."""
    from . import memory                       # imported here: memory imports caller_key from this module
    stored = memory.remember_focus(caller, args.segment)
    return FocusStored(segment=stored, lifetime="30 days", delete_with="DELETE /me/memory")


# ---------------------------------------------------------------- save_evidence (Lab 7 · team, needs a yes)

class EvidenceSaved(BaseModel):
    citation: Citation
    kind: str
    quote: str
    added: bool                 # False: it was already on the board (saving twice changes nothing)


def save_evidence(args: SaveEvidence, caller: str) -> EvidenceSaved:
    """Writes to the founder's evidence board. Run only by confirm() in src/agent.py, after the founder's yes.
    The quote is verified again here (src/verify.py): the model proposed it, code decides."""
    from . import memory
    path = transcripts_dir(caller) / f"{args.interview_id}.txt"   # safe: the id matched ^interview_[0-9]{2}$
    if not path.is_file():
        raise ToolFailure(f"There is no interview {args.interview_id}. Nothing was saved.")
    m = verify.best_match(args.quote, parse_transcript(path))
    if not verify.is_supported(m):
        raise ToolFailure(f"That quote is not in a Customer turn of {args.interview_id} (best match {m.score}). "
                          "Nothing was saved; do not propose it again.")
    cite = Citation(interview_id=args.interview_id, line=m.line)
    added = memory.save_evidence(caller, {"interview_id": cite.interview_id, "line": cite.line,
                                          "kind": args.kind, "quote": args.quote})
    return EvidenceSaved(citation=cite, kind=args.kind, quote=args.quote, added=added)


# ---------------------------------------------------------------- the registry

@dataclass(frozen=True)
class Tool:
    name: str
    args: type[Contract]
    run: Callable[..., BaseModel]
    needs_caller: bool = True     # call_tool passes the caller from the session; the model cannot
    writes: bool = False          # True: stores or changes something (MCP: read_only_hint=False)

    def schema(self) -> dict:
        """What the model sees: name, description and JSON Schema, all from the contract."""
        return {"type": "function", "function": {
            "name": self.name, "description": " ".join(self.args.__doc__.split()),
            "parameters": self.args.model_json_schema()}}


TOOLS = {t.name: t for t in [
    Tool("get_transcript", GetTranscript, get_transcript),
    Tool("talk_ratio", TalkRatio, talk_ratio),
    Tool("check_rewrite", CheckRewrite, check_rewrite, needs_caller=False),
    Tool("ask_interviews", AskInterviews, ask_interviews),
    Tool("verify_quote", VerifyQuote, verify_quote),
    Tool("remember_focus", RememberFocus, remember_focus, writes=True),
]}


def tools_for(caller: str | None) -> dict[str, Tool]:
    """Least privilege by construction: transcripts are customers' words, so a caller who is
    not signed in is offered no tool that needs a caller."""
    return {n: t for n, t in TOOLS.items() if caller or not t.needs_caller}


# Tools a model may PROPOSE but never run. They are not in TOOLS, so call_tool() through /act, /chat or
# the MCP server can never reach them. Only confirm() in src/agent.py runs them, after a person's yes.
PROPOSE_ONLY = {t.name: t for t in [
    Tool("save_evidence", SaveEvidence, save_evidence, writes=True),
]}
