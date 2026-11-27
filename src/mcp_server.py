"""Groundwork as an MCP server: the same tools as src/tools.py, usable by any MCP host.

Run it over stdio (what Claude Code, Cursor and VS Code launch):
    GROUNDWORK_FOUNDER=<test-founder> python -m src.mcp_server
Or over Streamable HTTP:
    GROUNDWORK_FOUNDER=<test-founder> python -m src.mcp_server --http     # http://127.0.0.1:8000/mcp

MCP Python SDK 2.x: the server class is MCPServer (FastMCP is the version 1 name).
One schema, two doors: the type hints below are the aliases from src/contracts.py, and the
description is the one the function-calling schema uses. tests/test_mcp.py fails if the two
doors offer different tools or describe an argument differently.

Identity: transcripts are customers' words, so every tool needs a caller. The caller is
GROUNDWORK_FOUNDER, set by whoever launches the server. It is resolved on the server, so it
is not in any tool's schema and the model cannot send it.
"""
from __future__ import annotations

import os
import sys
from typing import Annotated

from mcp.server import MCPServer
from mcp.server.mcpserver import Resolve
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from . import tools
from .contracts import (AskInterviews, CheckRewrite, GetTranscript, HypothesisText, InterviewId, InterviewIds,
                        MaxTurns, Question, Quote, RewriteText, Speaker, TalkRatio, TopK, Verdict,
                        VerifyQuote)

mcp = MCPServer("groundwork", instructions="Customer-interview evidence for founders. Tools read "
                                           "transcripts by interview id and give physical line numbers "
                                           "for citations like [interview_01:L11].")
READS = ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False)


def signed_in_founder() -> str:
    """Who is calling. Set by whoever launches the server, never by the model."""
    founder = os.environ.get("GROUNDWORK_FOUNDER")
    if not founder:
        raise ToolError("Not signed in: this server was started without GROUNDWORK_FOUNDER.")
    return founder


Founder = Annotated[str, Resolve(signed_in_founder)]


def describe(name: str) -> str:
    """The description the function-calling door gives the model, so both doors say the same."""
    return tools.TOOLS[name].schema()["function"]["description"]


def _run(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except tools.ToolFailure as e:          # expected failures reach the model as readable errors
        raise ToolError(str(e)) from e


@mcp.tool(annotations=READS, description=describe("get_transcript"))
def get_transcript(interview_id: InterviewId, founder: Founder, speaker: Speaker | None = None,
                   max_turns: MaxTurns = 100) -> tools.TranscriptOut:
    args = GetTranscript(interview_id=interview_id, speaker=speaker, max_turns=max_turns)
    return _run(tools.get_transcript, args, founder)


@mcp.tool(annotations=READS, description=describe("talk_ratio"))
def talk_ratio(interview_id: InterviewId, founder: Founder) -> tools.TalkRatioOut:
    return _run(tools.talk_ratio, TalkRatio(interview_id=interview_id), founder)


@mcp.tool(annotations=READS, description=describe("check_rewrite"))
def check_rewrite(hypothesis: HypothesisText, verdict: Verdict, rewrite: RewriteText | None = None) -> tools.RewriteOut:
    # No founder parameter, on purpose: the tool reads no stored data, so it needs no caller.
    return _run(tools.check_rewrite, CheckRewrite(hypothesis=hypothesis, verdict=verdict, rewrite=rewrite))
@mcp.tool(annotations=READS, description=describe("ask_interviews"))
def ask_interviews(question: Question, founder: Founder, interviews: InterviewIds = None,
                   k: TopK = 5) -> tools.AskOut:
    return _run(tools.ask_interviews, AskInterviews(question=question, interviews=interviews, k=k), founder)


@mcp.tool(annotations=READS, description=describe("verify_quote"))
def verify_quote(interview_id: InterviewId, quote: Quote, founder: Founder) -> tools.QuoteCheck:
    return _run(tools.verify_quote, VerifyQuote(interview_id=interview_id, quote=quote), founder)


if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.run("streamable-http", host="127.0.0.1", port=8000)
    else:
        mcp.run()
