# 0001 · One shared contract before anyone builds

**Date:** Week 3 · **Decided by:** Goga Jintcharadze, Otar Khunashvili, Dachi Khelashvili, Petre Kharazashvili

**Context.** Four people were building four Groundwork features alone for HW1. Three of them read transcripts and all four cite lines. Without a shared format, the pieces would need rewriting before they could be joined, and citations from different features would not agree.

**Decision.** We fixed the transcript format, one parser (`shared/transcript.py`), the JSON shapes, the citation form `[interview_NN:LNN]` and the usage object in `docs/INTERFACES.md` v1, plus shared test transcripts with planted facts (`data/transcripts/answer_key.json`), before anyone wrote feature code. Line numbers come from the parser, never from a model.

**Alternatives.** Each person defines their own formats and we reconcile later: faster to start, but every join becomes a rewrite. One person builds a shared core first: blocks three people for a week.

**Consequences.** Every feature's golden run checks the same planted facts, so results are comparable. Any change to the contract needs a PR, a version bump and a Teams post (section 11), which is slower. Watch: the linter already adds an `ERROR:` line and a 500-character limit beyond section 9; these need to be proposed as v2.
