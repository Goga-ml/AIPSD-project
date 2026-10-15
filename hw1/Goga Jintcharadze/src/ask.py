"""Ask Across Interviews: answer a founder's question from the interview transcripts, with citations.

Usage (from the repo root):
    python "hw1/Goga Jintcharadze/src/ask.py" "What do people currently pay?" [--min-score 0.6] [--k 5]

Prints the JSON from docs/INTERFACES.md section 8 to stdout, logs and cost to stderr.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

import numpy as np

from retrieval import Chunk, load_chunks, rank

REPO_ROOT = Path(__file__).resolve().parents[3]
TRANSCRIPTS_DIR = REPO_ROOT / "data" / "transcripts"

ABSTAIN = "no evidence found"
CITATION_RE = re.compile(r"\[(interview_\d+):L(\d+)\]")

CHAT_MODEL = os.environ.get("GROUNDWORK_CHAT_MODEL", "gemini-2.5-flash")
EMBED_MODEL = os.environ.get("GROUNDWORK_EMBED_MODEL", "gemini-embedding-001")
# USD per 1M tokens. Defaults match the napkin math in spec.md; override if the team picks other models.
PRICE_CHAT_IN = float(os.environ.get("GROUNDWORK_CHAT_PRICE_IN", "0.30"))
PRICE_CHAT_OUT = float(os.environ.get("GROUNDWORK_CHAT_PRICE_OUT", "2.50"))
PRICE_EMBED_IN = float(os.environ.get("GROUNDWORK_EMBED_PRICE_IN", "0.15"))

DEFAULT_MIN_SCORE = 0.6  # tuned on the golden questions, see golden.md
DEFAULT_K = 5
EMBED_BATCH = 100  # texts per embedding request
MAX_EMBED_CALLS = 10  # hard cap per run: refuse to embed more than 1,000 chunks

SYSTEM_PROMPT = """You answer a startup founder's question using ONLY the interview excerpts provided.
Each excerpt starts with a tag like [interview_01:L11].
Rules:
- Use only facts stated in the excerpts. No outside knowledge, no guessing.
- After every claim, copy the tag of the excerpt it came from, exactly, e.g. [interview_01:L11].
- Report what customers actually said or did. Keep numbers exactly as written.
- If the excerpts do not answer the question, reply with exactly: no evidence found
- Keep the answer under 80 words."""


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


class Usage:
    def __init__(self):
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.cost_usd = 0.0

    def add(self, tokens_in: int, tokens_out: int, price_in: float, price_out: float = 0.0) -> None:
        self.calls += 1
        self.input_tokens += tokens_in
        self.output_tokens += tokens_out
        self.cost_usd += (tokens_in * price_in + tokens_out * price_out) / 1_000_000

    def as_dict(self) -> dict:
        return {
            "model": CHAT_MODEL,
            "embed_model": EMBED_MODEL,
            "calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": round(self.cost_usd, 6),
        }


def build_prompt(question: str, chunks: list[Chunk]) -> str:
    excerpts = "\n".join(f"{c.tag} {c.text}" for c in chunks)
    return f"Excerpts:\n{excerpts}\n\nQuestion: {question}"


def verify_citations(answer: str, allowed: set[tuple[str, int]]) -> tuple[str, list[dict], list[str]]:
    """Keep citations that point at a retrieved chunk and strip the rest.

    Returns (cleaned answer, citations in order of first use, removed tags).
    """
    kept, removed = [], []

    def check(m: re.Match) -> str:
        key = (m.group(1), int(m.group(2)))
        if key in allowed:
            if key not in kept:
                kept.append(key)
            return m.group(0)
        removed.append(m.group(0))
        return ""

    cleaned = CITATION_RE.sub(check, answer)
    cleaned = re.sub(r"[ \t]+([.,;])", r"\1", re.sub(r"[ \t]{2,}", " ", cleaned)).strip()
    return cleaned, [{"interview_id": i, "line": n} for i, n in kept], removed


def answer_question(question, chunks, chunk_vecs, embed_query, generate,
                    k=DEFAULT_K, min_score=DEFAULT_MIN_SCORE) -> dict:
    """Retrieve, then abstain or answer. embed_query and generate are injected so tests run offline."""
    top = rank(embed_query(question), chunk_vecs, k)
    best = top[0][1] if top else 0.0
    result = {
        "question": question,
        "answer": ABSTAIN,
        "abstained": True,
        "best_score": round(best, 3),
        "citations": [],
        "retrieved": [{"citation": chunks[i].citation, "score": round(s, 3)} for i, s in top],
    }
    if best < min_score:
        log(f"best score {best:.3f} < min score {min_score}: abstaining without a chat call")
        return result

    picked = [chunks[i] for i, _ in top]
    raw = generate(build_prompt(question, picked)).strip()
    if raw.rstrip(".").lower() == ABSTAIN:
        log("model said the excerpts don't answer the question")
        return result

    answer, citations, removed = verify_citations(raw, {(c.interview_id, c.line) for c in picked})
    for tag in removed:
        log(f"removed citation not in retrieved chunks: {tag}")
    if not citations:
        log("answer had no valid citation: abstaining instead of returning an ungrounded answer")
        return result

    result.update(answer=answer, abstained=False, citations=citations)
    return result


def make_gemini(usage: Usage):
    """Return (embed, generate) functions that call Gemini and record usage."""
    from google import genai
    from google.genai import types

    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is not set")
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    def embed(texts: list[str], task_type: str) -> np.ndarray:
        if len(texts) > EMBED_BATCH * MAX_EMBED_CALLS:
            raise RuntimeError(f"refusing to embed {len(texts)} texts (cap {EMBED_BATCH * MAX_EMBED_CALLS})")
        vecs = []
        for start in range(0, len(texts), EMBED_BATCH):
            batch = texts[start:start + EMBED_BATCH]
            resp = client.models.embed_content(
                model=EMBED_MODEL, contents=batch,
                config=types.EmbedContentConfig(task_type=task_type),
            )
            vecs.extend(e.values for e in resp.embeddings)
            # The embedding API returns no token count, so estimate ~4 characters per token.
            usage.add(sum(len(t) for t in batch) // 4, 0, PRICE_EMBED_IN)
        return np.array(vecs)

    def generate(prompt: str) -> str:
        resp = client.models.generate_content(
            model=CHAT_MODEL, contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0),
        )
        meta = resp.usage_metadata
        tokens_out = (meta.candidates_token_count or 0) + (meta.thoughts_token_count or 0)  # thinking bills as output
        usage.add(meta.prompt_token_count or 0, tokens_out, PRICE_CHAT_IN, PRICE_CHAT_OUT)
        return resp.text or ""

    return embed, generate


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Ask a question across the interview transcripts.")
    parser.add_argument("question")
    parser.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE)
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--transcripts", default=str(TRANSCRIPTS_DIR))
    args = parser.parse_args(argv)

    usage = Usage()
    try:
        chunks = load_chunks(args.transcripts)
        if not chunks:
            raise RuntimeError(f"no interview_*.txt files in {args.transcripts}")
        embed, generate = make_gemini(usage)
        chunk_vecs = embed([c.text for c in chunks], "RETRIEVAL_DOCUMENT")
        result = answer_question(
            args.question, chunks, chunk_vecs,
            embed_query=lambda q: embed([q], "RETRIEVAL_QUERY")[0],
            generate=generate, k=args.k, min_score=args.min_score,
        )
    except Exception as e:
        log(f"error: {type(e).__name__}: {e}")
        return 1

    result["usage"] = usage.as_dict()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    log(f"cost: ${usage.cost_usd:.5f} ({usage.input_tokens} in / {usage.output_tokens} out)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
