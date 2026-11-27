# Groundwork · State Contract

*Lab 6. One row per thing Groundwork remembers across turns. If it is not in this table, Groundwork does not store it. [`src/memory.py`](../src/memory.py) is the code version of this table; [`tests/test_state.py`](../tests/test_state.py) proves the scope, lifetime and deletion columns.*

| What we remember | Why the product needs it | Scope: who can read it | Lifetime | Written when | Deleted by | Where it lives |
|---|---|---|---|---|---|---|
| Conversation turns: the founder's question and Groundwork's answer, at most 2,000 characters each | A follow-up ("and in the bakery interview?") needs the last few turns; at most 6 go into the prompt | This session only: key `session:<hash of X-Session-Id>` | 24 hours | Automatically, after every chat turn, both sides. Not when the answer was the router's sorry sentence | Expiry (read filter, and `expire()` at startup), or `DELETE /me/memory` | `$GROUNDWORK_STATE_DIR/memory.db` (SQLite, git-ignored), table `memory`, kind `turn` |
| The founder's focus segment, like `independent bakery owners` | Answers and searches lean toward the segment the founder is interviewing now | This founder only: key `founder:<hash of X-Founder>` | 30 days, restarted when the founder sets it again | Only when the founder asks: the `remember_focus` tool (contract `RememberFocus`, caller from the session). One per founder; a new one replaces the old | Expiry, or `DELETE /me/memory` | Same table, kind `focus` |
| The founder's evidence board: verified Customer quotes, each with its citation and kind (`pain`, `workaround`, `spending`, `commitment`) | The supervised loop (Lab 7) collects evidence; the founder keeps what they confirm | This founder only: key `founder:<hash of X-Founder>` | 180 days ([decision 0004](decisions/0004-evidence-board.md)) | Only after the founder's yes: `save_evidence`, run by `confirm()` (`POST /plan/confirm`), which verifies the quote again. Saving the same line and kind twice stores it once | Expiry, or `DELETE /me/memory` | Same table, kind `evidence` |

## What we never store

- The founder id or the session id themselves: every key holds a 12-character SHA-256 prefix (`caller_key` in `src/tools.py`), as the tool log already does. `test_keys_hold_a_hash_never_the_id`.
- Anything the model inferred about the founder that they did not state. The focus segment is written only by a tool the founder has to ask for, and the system prompt says so.
- Customers' words outside a turn, unless the founder confirmed them. A quote in an answer lives in that turn for 24 hours. The only founder row that holds customers' words is the evidence board, and only quotes the founder said yes to, each verified against the transcript at that moment.
- One founder's rows in another founder's prompt: `build_messages()` reads the focus for this founder and the turns for this session only. `test_scope_one_founders_memory_never_reaches_another`.
- Anything from a visitor (no `X-Founder`, no `X-Session-Id`): nothing is written. `test_a_visitor_leaves_nothing_behind`.

## How a founder sees and controls it

- **See:** `GET /me/memory` returns the focus segment, the evidence board, how many recent turns are held, the lifetimes, and the delete path.
- **After a write:** the `remember_focus` result names what was stored, for how long, and `DELETE /me/memory`; the model is told to say so.
- **Forget me:** `DELETE /me/memory` deletes this founder's focus row and evidence board and this session's turns, now, and returns the counts, like `{"focus": 1, "evidence": 3, "turns": 2}`. No model is involved (`test_forget_me_returns_counts_empties_the_next_read_and_needs_no_model`). Rows are removed, not flagged.

## Known limits

- The router keeps plain answers in memory for up to 10 minutes (`CACHE_TTL_S` in `src/router.py`), keyed by the full prompt. That cache is not in this table and `DELETE /me/memory` does not clear it; it empties on restart. Owner: Petre (`docs/fallback-plan.md`, open questions).
- The embedding cache (`.cache/embeddings.json`, `src/llm.py`) holds vectors of transcript lines with no lifetime. It holds no founder data, but it has no delete path yet.

## What changes the contract

Any new row needs a decision record in `docs/decisions/` and tests for its scope, lifetime and deletion.
