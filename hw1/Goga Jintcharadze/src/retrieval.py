"""Chunking and cosine ranking for Ask Across Interviews.

One chunk = one speaker turn (docs/INTERFACES.md section 8). No API calls here,
so everything in this file is testable offline.
"""
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from transcript import parse_transcript


@dataclass
class Chunk:
    interview_id: str
    line: int
    text: str  # "Speaker: text", the exact string that gets embedded

    @property
    def citation(self) -> dict:
        return {"interview_id": self.interview_id, "line": self.line}

    @property
    def tag(self) -> str:
        return f"[{self.interview_id}:L{self.line}]"


def load_chunks(transcripts_dir: str | Path) -> list[Chunk]:
    chunks = []
    for path in sorted(Path(transcripts_dir).glob("interview_*.txt")):
        for turn in parse_transcript(path).turns:
            chunks.append(Chunk(turn.interview_id, turn.line, f"{turn.speaker}: {turn.text}"))
    return chunks


def rank(query_vec, doc_vecs, k: int) -> list[tuple[int, float]]:
    """Return the top k (chunk index, cosine similarity) pairs, best first."""
    q = np.asarray(query_vec, dtype=float)
    d = np.asarray(doc_vecs, dtype=float)
    scores = (d @ q) / (np.linalg.norm(d, axis=1) * np.linalg.norm(q))
    order = np.argsort(-scores)[:k]
    return [(int(i), float(scores[i])) for i in order]
