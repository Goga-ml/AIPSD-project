"""Offline tests: fake embeddings and a fake model, real transcripts. No network, no API key."""
import json
from pathlib import Path

import numpy as np
import pytest

from ask import ABSTAIN, answer_question, verify_citations
from retrieval import load_chunks, rank

REPO_ROOT = Path(__file__).resolve().parents[3]
TRANSCRIPTS = REPO_ROOT / "data" / "transcripts"
ANSWER_KEY = json.loads((TRANSCRIPTS / "answer_key.json").read_text(encoding="utf-8"))

VOCAB = ["pay", "gel", "month", "cups", "milk", "bread", "weather", "football"]


def fake_embed(text: str) -> np.ndarray:
    """Bag of keywords plus a small constant so no vector is all zeros."""
    words = text.lower().replace(",", " ").replace(".", " ").split()
    return np.array([words.count(w) for w in VOCAB] + [0.01], dtype=float)


class FakeModel:
    def __init__(self, reply: str):
        self.reply = reply
        self.prompts = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.reply


@pytest.fixture(scope="module")
def corpus():
    chunks = load_chunks(TRANSCRIPTS)
    return chunks, np.array([fake_embed(c.text) for c in chunks])


def test_one_chunk_per_turn_with_real_line_numbers(corpus):
    chunks, _ = corpus
    assert len(chunks) == 18 + 18 + 16  # turns in interview_01, 02, 03
    by_tag = {c.tag: c.text for c in chunks}
    for interview_id, entry in ANSWER_KEY.items():
        if interview_id.startswith("_"):
            continue
        for fact in entry["planted"]:
            assert by_tag[f"[{interview_id}:L{fact['line']}]"].startswith("Customer: ")


def test_rank_returns_best_first():
    docs = np.array([[1.0, 0.0], [0.7, 0.7], [0.0, 1.0]])
    assert [i for i, _ in rank([1.0, 0.1], docs, k=2)] == [0, 1]


def test_abstains_below_threshold_without_calling_model(corpus):
    chunks, vecs = corpus
    model = FakeModel("should not be used")
    result = answer_question("What is the weather like?", chunks, vecs, fake_embed, model, min_score=0.5)
    assert result["answer"] == ABSTAIN
    assert result["abstained"] is True
    assert result["citations"] == []
    assert model.prompts == []


def test_answers_with_valid_citation(corpus):
    chunks, vecs = corpus
    model = FakeModel("One owner pays 45 GEL a month for a POS add-on [interview_01:L11].")
    result = answer_question("What do people pay per month in GEL?", chunks, vecs, fake_embed, model, min_score=0.5)
    assert result["abstained"] is False
    assert {"interview_id": "interview_01", "line": 11} in result["citations"]
    assert "[interview_01:L11]" in model.prompts[0]  # the cited chunk was really retrieved


def test_invented_citation_is_removed():
    allowed = {("interview_01", 11)}
    answer, citations, removed = verify_citations(
        "Pays 45 GEL [interview_01:L11] and 900 GEL [interview_02:L99].", allowed)
    assert answer == "Pays 45 GEL [interview_01:L11] and 900 GEL."
    assert citations == [{"interview_id": "interview_01", "line": 11}]
    assert removed == ["[interview_02:L99]"]


def test_answer_with_only_invented_citations_abstains(corpus):
    chunks, vecs = corpus
    model = FakeModel("Everyone pays 900 GEL [interview_09:L1].")
    result = answer_question("What do people pay per month in GEL?", chunks, vecs, fake_embed, model, min_score=0.5)
    assert result["answer"] == ABSTAIN
    assert result["abstained"] is True


def test_model_saying_no_evidence_is_an_abstain(corpus):
    chunks, vecs = corpus
    model = FakeModel("No evidence found.")
    result = answer_question("What do people pay per month in GEL?", chunks, vecs, fake_embed, model, min_score=0.5)
    assert result["answer"] == ABSTAIN
    assert result["abstained"] is True
