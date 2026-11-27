# 0004 · An evidence board, saved only after the founder's yes

**Date:** 27 November 2026 · **Decided by:** Goga Jintcharadze (to be confirmed by the team)

**Context.** Lab 7 needs one action that waits for a person. Every Groundwork tool so far only reads, except `remember_focus`, which the founder triggers themselves. The supervised loop collects quotes; something has to happen to them.

**Decision.** A third row in `docs/state-contract.md`: the founder's evidence board, verified Customer quotes with their citation and kind (`pain`, `workaround`, `spending`, `commitment`, the categories of our answer key). Scope: one founder (hashed key). Lifetime: 180 days, about one discovery phase. Written only by `save_evidence`, which only `confirm()` runs, after the founder's yes; the quote is verified again at that moment. Deleted by expiry or `DELETE /me/memory`.

**Alternatives.** No write at all, and the loop just answers: then there is nothing to confirm and Lab 7's gate proves nothing. Let the loop save directly: fast, but a hallucinated or mis-cited quote would land on the board unseen.

**Consequences.** `DELETE /me/memory` now also returns an `evidence` count. The board holds customers' words for 180 days under a founder's key; the Design Review's privacy row has to cover it before real transcripts are used.
