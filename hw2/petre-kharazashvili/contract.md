# HW2 · Tool Contract · `check_rewrite` · petre-kharazashvili

**Tool:** `check_rewrite` · **Owner:** `petre-kharazashvili` · **Team repo:** https://github.com/Goga-ml/AIPSD-project
**Code** (permanent links to the reviewed commit `49e65df`; the same files are on `main` once the pull request is merged): contract class `CheckRewrite` in [`src/contracts.py` line 51](https://github.com/Goga-ml/AIPSD-project/blob/49e65df/src/contracts.py#L42-L57) · function `check_rewrite()` in [`src/tools.py` line 120](https://github.com/Goga-ml/AIPSD-project/blob/49e65df/src/tools.py#L108-L146) · registry entry in the `TOOLS` list of [`src/tools.py`](https://github.com/Goga-ml/AIPSD-project/blob/49e65df/src/tools.py#L165-L169) · MCP registration `check_rewrite()` in [`src/mcp_server.py`](https://github.com/Goga-ml/AIPSD-project/blob/49e65df/src/mcp_server.py#L73-L77)
**Product pull request:** [#26](https://github.com/Goga-ml/AIPSD-project/pull/26) · head commit `49e65df` · issue [#22](https://github.com/Goga-ml/AIPSD-project/issues/22)
**Team copy of this contract:** [`docs/tool-contracts.md`](../../docs/tool-contracts.md), section `check_rewrite`

**In one sentence, for the model** (the docstring of `CheckRewrite`): Check your verdict and rewrite of a founder's hypothesis before you show them: a falsifiable hypothesis comes back in the founder's exact words, and a rewrite may only state numbers the founder wrote or numbers inside [square brackets]. Reads nothing, changes nothing.

| | |
|---|---|
| **Effect** | reads nothing and changes nothing. It is a read tool in the Week 7 sense: nothing in it would ever need a yes inside a loop |
| **Undo** | nothing to undo |
| **Idempotent?** | yes. The second identical call to golden case `p2` returned the same object as the first: `{"verdict": "falsifiable", "rewrite": "At least 7 of 10 independent coffee shop owners we interview will report spending 3+ hours per week on staff scheduling, and at least 3 will agree to a paid pilot at $20/month.", "unchanged": true, "to_confirm": []}` |
| **Offered to** | every caller, including a visitor. The line that decides: `return {n: t for n, t in TOOLS.items() if caller or not t.needs_caller}` in `tools_for()`, with `needs_caller=False` on this tool. `get_transcript`, which reads customers' words, is not offered to a visitor by the same line |
| **Identity from** | not used. `check_rewrite(args)` has no `caller` parameter, and `call_tool()` calls it as `tool.run(args)` |
| **Touches** | nothing: no file, no table, no network, no model. It computes its answer from its three arguments |
| **Must never** | show the founder a number as if they had said it |

**Inputs.** Copied from `CheckRewrite`. Unknown fields are refused (`extra="forbid"` on the base class `Contract`).

| Argument | Type | Constraint, as written in code | Description the model reads |
|---|---|---|---|
| `hypothesis` | `str` | `min_length=1, max_length=500, pattern=r"^\S(?:[^\x00-\x1f\x7f]*\S)?$"` | The founder's hypothesis, exactly as they wrote it, on one line |
| `verdict` | `Literal["falsifiable", "vague"]` | the fixed set | Your verdict on the hypothesis |
| `rewrite` | `str \| None`, default `None` | `min_length=1, max_length=1000`, same pattern | Your rewrite. Needed when the verdict is vague. Every detail the founder did not state goes in [square brackets] |

There is no number among the arguments, so there is nothing to bound, and no user, founder or account field.

**Expected failures.** The exact strings from `src/tools.py`.

| When | Message the model reads |
|---|---|
| vague, no rewrite sent | A vague hypothesis needs a rewrite. Send one in `rewrite`, with every detail the founder did not state in [square brackets]. |
| vague, the rewrite repeats the hypothesis | The rewrite repeats the founder's words, so it is still vague. Rewrite it with a specific segment, a past behavior and a threshold, each in [square brackets] if the founder did not state it. |
| vague, the rewrite states numbers the founder did not write | The rewrite states 3, 29 as if the founder had said it. Put each one in [square brackets] or remove it, then call check_rewrite again. |
| vague, nothing in brackets | The rewrite marks nothing in [square brackets], so the founder cannot tell what you assumed. Put every detail they did not state in [square brackets], then call check_rewrite again. |

Every message says what to do next. None contains a path, a class name or a stack trace.

**The decision I had to make.** The first version of this feature, the HW1 linter, called a model itself: `POST /lint` in `hw1/petre-kharazashvili/src/app.py` sent the hypothesis to Gemini and streamed back the verdict. The tool cannot do that. The model that calls it is already the judge, so a second model inside would double the cost and the wait (6 to 28 seconds per lint in HW1) and put the judgment where no contract can check it. It would also mean the golden cases could only run against a fake. What code can guarantee is narrower and I kept only that: the founder's exact words for a falsifiable hypothesis, and no invented numbers in a rewrite. The removal is visible in `src/tools.py`: `check_rewrite()` imports nothing from `src/llm.py` or `src/router.py`, and the "Touches" row above says "nothing". The cost of the decision is written in `docs/tool-contracts.md` under "What it does not check": only digits are compared, so a segment invented in words still passes.
