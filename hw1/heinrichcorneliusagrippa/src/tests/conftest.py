import json
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1]          # tests/ lives inside src/
sys.path.insert(0, str(SRC))

DATA = SRC.parents[2] / "data" / "transcripts"     # shared team transcripts at the repo root


class FakeModel:
    """Stands in for llm.complete_json. Returns the given replies in order; never calls the network."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.prompts = []

    def __call__(self, system, user, schema):
        self.prompts.append(user)
        reply = self.replies.pop(0)
        text = reply if isinstance(reply, str) else json.dumps(reply)
        return text, {"model": "fake", "input_tokens": 100, "output_tokens": 20, "cost_usd": 0.0001}


@pytest.fixture
def tr01():
    from transcript import parse_transcript
    return parse_transcript(DATA / "interview_01.txt")
