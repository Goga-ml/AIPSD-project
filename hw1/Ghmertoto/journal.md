# Pattern Journal · Otar Khunashvili · Weeks 1 to 4

*Drafted on 15 October 2026 by Claude Code from what happened while building this feature. Lines marked **[to confirm]** need my own words or confirmation before I submit.*

Format per entry: **W# · Pattern** · Where I applied it · What I delegated to AI · How I verified it

---

**W1 · Context as Budget** · The classifier sends the model only the interviewer questions as `L<line>: <text>` plus a fixed rubric (about 1,000 tokens per interview), never customer answers, metadata or word counts. I delegated writing the prompt to Claude Code. `test_prompt_contains_only_interviewer_questions` checks that no customer turn or header text reaches the prompt. **[to confirm: one thing I would do differently]**

**W2 · Spec Before Code** · `spec.md` was written and approved before any code. The agent had to stop after the spec, and it raised the folder-name and repo conflicts before creating files. Rereading the spec against its own acceptance criteria caught a contradiction about zero-word shares before it reached the code. **[to confirm: my own review of the spec]**

**W3 · Uncertainty-Aware UX** · The report says labels are "model judgments, not facts". When the model fails, questions are shown as `not classified` instead of being guessed, and the talk ratio, which is certain, is still shown. The failure paths (invalid JSON 3 times, API down, missing key) were delegated and are covered by tests. Running the real CLI without a key showed that the missing-key case was retried pointlessly. **[to confirm]**

**W4 · Grounded Generation** · Grounding here means every label is tied to a real line: the model must answer exactly the line numbers sent, and code rejects unknown lines, missing lines, unknown labels, and `good` mixed with other labels. The numbers in the report come only from code. Whether the real model's labels match the planted answer key is **not verified yet**, because no live call has been made (see `golden.md`). **[to confirm after running golden.py]**
