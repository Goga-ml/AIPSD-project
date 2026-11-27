"""The MCP door: the same tools and the same arguments as function calling, through an in-memory client.

Offline: Client(mcp) talks to the server object in this process. No network, no key, no subprocess.
"""
import asyncio

import pytest
from mcp import Client

from src import tools
from src.mcp_server import mcp

IDENTITY_WORDS = ("founder", "user", "account", "student", "caller")


def run(coro):
    return asyncio.run(coro)


async def listed():
    async with Client(mcp) as c:
        return {t.name: t for t in (await c.list_tools()).tools}


async def call(name, args):
    async with Client(mcp) as c:
        return await c.call_tool(name, args)


def strip(schema):
    """Argument schemas without the auto-generated titles, which differ between the two doors."""
    return {k: {kk: vv for kk, vv in v.items() if kk != "title"} for k, v in schema.get("properties", {}).items()}


@pytest.fixture
def signed_in(monkeypatch):
    monkeypatch.setenv("GROUNDWORK_FOUNDER", "founder-1")


def test_same_tools_through_both_doors():
    assert set(run(listed())) == set(tools.TOOLS), "every tool in TOOLS must also be registered in src/mcp_server.py"


@pytest.mark.parametrize("name", sorted(tools.TOOLS))
def test_both_doors_describe_the_arguments_identically(name):
    mcp_schema = run(listed())[name].input_schema
    fc_schema = tools.TOOLS[name].schema()["function"]["parameters"]
    assert strip(mcp_schema) == strip(fc_schema)
    assert set(mcp_schema.get("required", [])) == set(fc_schema.get("required", []))


@pytest.mark.parametrize("name", sorted(tools.TOOLS))
def test_both_doors_give_the_model_the_same_description(name):
    assert run(listed())[name].description == tools.TOOLS[name].schema()["function"]["description"]


@pytest.mark.parametrize("name", sorted(tools.TOOLS))
def test_annotations_match_what_the_tool_does(name):
    """Read-only tools say so; a tool that stores something (Tool.writes) does not claim to be read-only.
    No tool is destructive."""
    notes = run(listed())[name].annotations
    assert notes.read_only_hint is (not tools.TOOLS[name].writes) and notes.destructive_hint is False


def test_one_call_through_the_client(signed_in):
    r = run(call("get_transcript", {"interview_id": "interview_01", "speaker": "Customer", "max_turns": 2}))
    assert not r.is_error
    assert r.structured_content["interview_id"] == "interview_01"
    assert [t["speaker"] for t in r.structured_content["turns"]] == ["Customer", "Customer"]
    assert r.structured_content["truncated"] is True


def test_bad_arguments_are_rejected_before_the_tool_runs(signed_in, monkeypatch):
    ran = []
    monkeypatch.setattr(tools, "get_transcript", lambda *a: ran.append(a))
    r = run(call("get_transcript", {"interview_id": "../../.env"}))
    assert r.is_error and ran == []


def test_expected_failure_reaches_the_model_as_text(signed_in):
    r = run(call("get_transcript", {"interview_id": "interview_99"}))
    assert r.is_error and "There is no interview interview_99" in r.content[0].text
    assert "Traceback" not in r.content[0].text


def test_nobody_signed_in_means_no_transcript():
    r = run(call("get_transcript", {"interview_id": "interview_01"}))
    assert r.is_error and "Not signed in" in r.content[0].text


def test_identity_is_not_in_any_schema_and_the_model_cannot_set_it(signed_in, monkeypatch):
    for name, tool in run(listed()).items():
        assert not any(w in arg.lower() for arg in tool.input_schema.get("properties", {})
                       for w in IDENTITY_WORDS), name
    seen = []
    real = tools.get_transcript
    monkeypatch.setattr(tools, "get_transcript", lambda args, caller: seen.append(caller) or real(args, caller))
    run(call("get_transcript", {"interview_id": "interview_01", "founder": "founder-2"}))
    assert seen == ["founder-1"], "the caller must be the server's founder, not the one in the arguments"
