# Spec v0 · Groundwork · Ask Across Interviews

*HW1 · Goga Jintcharadze · Task 4 of the Groundwork capstone. Shared formats follow `docs/INTERFACES.md` v1.*

## Problem
After ten customer interviews, a founder can't remember who said what. To answer a simple question like "what do people pay today?", they reread every transcript by hand, or they answer from memory and remember the flattering parts.

## Users
Early-stage founders who have run 3 or more customer-discovery interviews, have the transcripts as text, and need to answer a specific question across all of them before making a product decision.

## Success criteria
1. For a question whose answer is in the transcripts, the answer cites the correct interview and line in **3 of 3** golden questions.
2. For a question with no answer in the transcripts, the tool says **"no evidence found"** and makes **no** chat-model call, in 100% of golden cases.
3. Each answer costs **under $0.002**, and every query prints its cost.

## Core feature (Weeks 2 to 4 scope)
A CLI, `ask.py "<question>"`. It splits the 3 test transcripts into chunks of one speaker turn each, embeds them with a Gemini embedding model and keeps them in memory. For each question it embeds the question, ranks chunks by cosine similarity and keeps the top 5. If the best score is below a threshold, it returns "no evidence found". Otherwise it sends only those chunks to the chat model, and the model answers using only them, citing each claim as `[interview_NN:LNN]`. In code, the tool checks that every citation in the answer belongs to a retrieved chunk. The output is the JSON from INTERFACES.md section 8.

## Context list
| What the model sees | Where it comes from |
|---|---|
| The question | command-line argument |
| Top 5 retrieved turns, each labelled `[interview_NN:LNN] Speaker: text` | `data/transcripts/*.txt`, parsed by `shared/transcript.py` |
| Instructions: answer only from the chunks, cite every claim, say so if the chunks don't answer it | system prompt in `src/` |

The model does **not** see whole transcripts, other interviews' metadata or any outside knowledge. Five turns is enough to answer and keeps input small (Context as Budget).

## Acceptance criteria
1. `ask.py "What do people currently pay?"` returns an answer that contains the spending fact planted in `answer_key.json`, with a citation that matches its `interview_id` and `line`.
2. `ask.py "<unrelated_question from answer_key.json>"` returns `answer == "no evidence found"`, `abstained == true`, `citations == []`, and makes zero chat-model calls.
3. Every citation in every answer appears in `retrieved`. If the model invents a citation, the tool removes it and logs it to stderr.

## Napkin math
One question = 1 embedding call (about 20 tokens) + 1 chat call (about 500 tokens in, 120 out).
Assumed models: Gemini 2.5 Flash ($0.30 in / $2.50 out per 1M tokens) and Gemini Embedding ($0.15 per 1M tokens in). *Check against ai.google.dev pricing before submitting.*
Chat: 500 × $0.30/1M + 120 × $2.50/1M = $0.00045. Embedding: about $0.000003.
**10 founders × 10 questions/day × $0.00045 × 30 = about $1.35/month.** Embedding the 3 transcripts once (about 2,000 tokens) costs less than $0.001.

## Risks and safety
- **Wrong citation:** the model cites the right fact with the wrong line. Mitigation: citations are checked in code against the retrieved chunks.
- **Threshold too low or too high:** the tool either answers unrelated questions or abstains on real ones. Mitigation: tune it on the golden questions and record the value in INTERFACES.md.
- **Misuse:** a founder quotes a single cherry-picked line as proof. Mitigation: every answer shows its citations, so the reader can check the source.

## Out of scope (for now)
Audio, a web UI, persistent SQLite storage, more than 3 transcripts, re-ranking, cross-interview contradiction detection, saturation tracking, local models through Ollama, and evidence-strength rating.
