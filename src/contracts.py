"""Tool contracts: what each tool accepts, as types the code checks. Spec: docs/tool-contracts.md.

One source of truth, two doors:
  * src/tools.py builds the function-calling schema from the contract classes below
  * src/mcp_server.py builds the MCP tools from the same type aliases
Rules for every contract:
  * extra="forbid": an argument we did not ask for is refused, never ignored
  * every string has a pattern or a fixed set of values; every number has bounds
  * no user, founder, student or account field. Identity comes from the session (src/act.py).
"""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

# [0-9], not \d: \d also matches digits from other scripts (interview_٠١), which are never real ids.
InterviewId = Annotated[str, Field(pattern=r"^interview_[0-9]{2}$",
                                   description="Interview id: the file name without .txt, like interview_01")]
Speaker = Annotated[Literal["Interviewer", "Customer"],
                    Field(description="Only this speaker's turns. Leave out for both")]
MaxTurns = Annotated[int, Field(ge=1, le=200, description="How many turns to return, 1 to 200")]
# One quote from one turn: printable text, no newline (a quote may not span two turns, INTERFACES section 6).
Quote = Annotated[str, Field(min_length=8, max_length=300, pattern=r"^[^\x00-\x1f\x7f]+$",
                             description="The exact words to check, copied from one Customer turn, 8 to 300 characters")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GetTranscript(Contract):
    """Read one customer interview: every turn with its speaker and its line number, for citations
    like [interview_01:L11]. Reads only, changes nothing."""
    interview_id: InterviewId
    speaker: Speaker | None = None
    max_turns: MaxTurns = 100


class TalkRatio(Contract):
    """Talk ratio for one customer interview: how many words the interviewer and the customer spoke,
    and the interviewer's share, counted by code and never estimated. Reads only, changes nothing."""
    interview_id: InterviewId


# ---------------------------------------------------------------- check_rewrite (HW2 · Petre)

ONE_LINE = r"^\S(?:[^\x00-\x1f\x7f]*\S)?$"       # no line breaks or control characters, no outer spaces
HypothesisText = Annotated[str, Field(min_length=1, max_length=500, pattern=ONE_LINE,
                                      description="The founder's hypothesis, exactly as they wrote it, on one line")]
Verdict = Annotated[Literal["falsifiable", "vague"], Field(description="Your verdict on the hypothesis")]
RewriteText = Annotated[str, Field(min_length=1, max_length=1000, pattern=ONE_LINE,
                                   description="Your rewrite. Needed when the verdict is vague. Every detail "
                                               "the founder did not state goes in [square brackets]")]


class CheckRewrite(Contract):
    """Check your verdict and rewrite of a founder's hypothesis before you show them: a falsifiable
    hypothesis comes back in the founder's exact words, and a rewrite may only state numbers the
    founder wrote or numbers inside [square brackets]. Reads nothing, changes nothing."""
    hypothesis: HypothesisText
    verdict: Verdict
    rewrite: RewriteText | None = None


class VerifyQuote(Contract):
    """Check that a quote really appears in a Customer turn of one interview, and get the line to cite.
    Use it before citing any quote as evidence. supported=false means do not cite it. Reads only, changes nothing."""
    model_config = ConfigDict(extra="allow")    # RED RUN, do not merge: weakens the contract for HW2 evidence
    interview_id: InterviewId
    quote: Quote
