"""Incremental parser: turns the model's raw stream into the INTERFACES.md section 9 wire format.

Model output (any chunking):      Wire output (streamed as soon as it is safe):
  VERDICT: FALSIFIABLE | VAGUE      VERDICT: falsifiable | vague
  REASON: <1-3 sentences>           REASON: <same text>
  REWRITE: <rewrite> | UNCHANGED    REWRITE: <rewrite>, or the exact input if falsifiable

Tolerated: upper/lower case labels, markdown bold ("**VERDICT:**"), preamble before VERDICT,
and REASON/REWRITE values wrapped over several lines (joined with a space).
"""

LABELS = ("VERDICT", "REASON", "REWRITE")
VERDICTS = ("falsifiable", "vague")
_LABEL_MAX = 16  # a line prefix longer than this without ":" can't be a label


class ParseError(Exception):
    """The model's reply doesn't follow the output format."""


class LintParser:
    def __init__(self, hypothesis: str):
        self.hypothesis = hypothesis
        self.verdict: str | None = None
        self.seen: list[str] = []      # labels in the order they arrived
        self.field: str | None = None  # field the current or last line belongs to
        self.state = "label"           # "label": deciding what a line is; "value": streaming it; "skip"
        self.pending = ""              # start of the line while its label is undecided
        self.verdict_text = ""
        self.value_started = False
        self.newline_due = False       # REASON/REWRITE line ended; "\n" is sent once we know it didn't wrap
        self.done = False              # REWRITE is complete; ignore anything after

    def feed(self, chunk: str) -> str:
        """Consume a chunk of model output; return wire text that is safe to send now."""
        return "".join(self._char(ch) for ch in chunk)

    def finish(self) -> str:
        """Call at end of stream. Returns the remaining wire text or raises ParseError."""
        if self.done:
            return ""
        out = self._end_line()
        missing = [label for label in LABELS if label not in self.seen]
        if missing:
            raise ParseError(f"The model's reply was missing {', '.join(missing)}.")
        if self.newline_due:
            out += "\n"
            self.newline_due = False
        self.done = True
        return out

    def _char(self, ch: str) -> str:
        if self.done:
            return ""
        if ch == "\n":
            return self._end_line()
        if self.state == "skip":
            return ""
        if self.state == "value":
            return self._value(ch)
        if not self.pending and ch.isspace():
            return ""
        self.pending += ch
        if ch == ":":
            label = self.pending[:-1].strip(" *#>-_`").upper()
            if label in LABELS:
                self.pending = ""
                return self._start_field(label)
            return self._continuation()
        if len(self.pending) > _LABEL_MAX:
            return self._continuation()
        return ""

    def _start_field(self, label: str) -> str:
        expected = LABELS[len(self.seen)] if len(self.seen) < len(LABELS) else None
        if label != expected:
            raise ParseError(f"The model's reply had {label} where {expected or 'nothing'} was expected.")
        self.seen.append(label)
        self.field = label
        self.state = "value"
        self.value_started = False
        out = "\n" if self.newline_due else ""
        self.newline_due = False
        if label == "VERDICT":
            return out
        if label == "REWRITE" and self.verdict == "falsifiable":
            # INTERFACES section 9: a falsifiable hypothesis comes back unchanged, guaranteed here, not by the model.
            self.done = True
            return out + f"REWRITE: {self.hypothesis}\n"
        return out + f"{label}: "

    def _continuation(self) -> str:
        """The pending line has no label: it continues REASON/REWRITE, or is ignored."""
        text, self.pending = self.pending, ""
        if self.field in ("REASON", "REWRITE") and self.newline_due:
            self.newline_due = False
            self.state = "value"
            self.value_started = True
            return " " + text
        self.state = "skip"  # preamble before VERDICT, or chatter after the VERDICT line
        return ""

    def _value(self, ch: str) -> str:
        if self.field == "VERDICT":
            self.verdict_text += ch
            return ""
        if not self.value_started:
            if ch in " *":
                return ""
            self.value_started = True
        return ch

    def _end_line(self) -> str:
        out = ""
        if self.state == "label" and self.pending:
            out = self._continuation()
        if self.state == "value" and self.field == "VERDICT":
            verdict = self.verdict_text.strip(" *.`").lower()
            if verdict not in VERDICTS:
                raise ParseError(f"The model's verdict {self.verdict_text.strip()!r} is not FALSIFIABLE or VAGUE.")
            self.verdict = verdict
            out += f"VERDICT: {verdict}\n"
        elif self.state == "value":
            self.newline_due = True
        self.state = "label"
        self.pending = ""
        return out
