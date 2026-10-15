"""Shared transcript parser for Groundwork. Spec: docs/INTERFACES.md sections 3-4.

Everyone copies this file unchanged into their own src/. Change it only by PR (section 11).
"""
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
