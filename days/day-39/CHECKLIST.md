# Day 39 — CHECKLIST

**IDs covered:** LC-07 🛠️ (middleware, the 1.x extension story), LC-08 🛠️ (built-in middleware tour)

## Demo command

```bash
uv run python days/day-39/lab/hook_order.py     # 0 requests — a fake model
uv run python days/day-39/lab/scrub_demo.py     # <= 6 requests
uv run pytest tests/test_lc_middleware.py -v
```

Expected: one line showing the true hook order with **numbered** `before_model` firings, then a real
run whose prompts contain `[REDACTED:...]` markers.

## Setup

- [ ] `./m start 39` and `./m scaffold 39` run
- [ ] No new packages
- [ ] Files created (`lc/middleware.py`, `tests/test_lc_middleware.py`, two lab files)
- [ ] `MIDDLEWARE` list exported from `lc/agent.py` and passed to `create_agent`

## LC-07 — the extension model

- [ ] Can name the four extension strategies (subclass / callback / guardrail / middleware) and who
      uses each
- [ ] Can name all five hook points and say which can halt a run
- [ ] **Internalised that `before_model` fires once per turn**, not once per run
- [ ] `hook_order.py` run, and the numbered firings observed
- [ ] Extended it with a tool so the loop iterates — cost intuition formed by experiment
- [ ] Output pasted into notes for Day 42's ADR-002

## The scrubber

- [ ] `PATTERNS` compiled at **module level**, not inside the hook
- [ ] Each redaction is **labelled** — `[REDACTED:card]`, not `[REDACTED]`
- [ ] `bearer` pattern covers **your own** key prefixes (`gsk_`, `sk-or-`)
- [ ] Card pattern's false-positive bias understood and stated as a deliberate trade
- [ ] `MAX_SCRUB_CHARS` bound present, and the **lossy** consequence written down
- [ ] `model_copy` used — copy, never mutate
- [ ] Block-list content **skipped**, and the gap recorded as a known limitation
- [ ] `return None` when nothing changed — and can say what it saves on Day 47

## Order (§3.4)

- [ ] Confirmed `before_*` runs in list order and `after_*` in reverse
- [ ] Scrubber is **first** in `MIDDLEWARE`
- [ ] Can say why ordering is a *security* property here

## LC-08 — the built-in tour

- [ ] **Summarization:** confirmed which model it uses; passed `fast_loop()` explicitly
- [ ] Summarization's request cost noted in `docs/RATE_BUDGET.md`
- [ ] **Understood that compaction rewrites history and can undo Day 8's separation rule** — noted
      for Day 65
- [ ] **HITL:** five-row comparison against Day 33 filled in
- [ ] Concluded and wrote down: framework supplies the mechanism, you still supply the record
- [ ] **Retry: deliberately NOT adopted**, and the reason written down (`router.py` owns retries)
- [ ] Can state the principle: retry belongs in the one place that knows the budget

## Tests that must be able to fail

- [ ] `test_each_pattern_redacts[card|email|bearer×2]`
- [ ] `test_our_own_key_formats_are_covered`
- [ ] `test_ordinary_text_survives` — the negative-space test
- [ ] `test_scrubbing_is_bounded`
- [ ] `test_patterns_are_precompiled`
- [ ] `test_before_model_does_not_mutate_the_input`
- [ ] `test_before_model_returns_none_when_nothing_changed`
- [ ] `test_block_content_is_skipped_not_crashed` — **a test that encodes a known gap**
- [ ] `test_the_scrubber_is_first_in_the_stack` — **flip it:** reorder, see red
- [ ] Whole file runs offline with **no keys**

## Understanding check — answer out loud

- [ ] Why does 1.x prefer five named hooks to one open class?
- [ ] What is the cost model of a `before_model` hook, and why does that change how you write one?
- [ ] Why must the scrubber be first, and what error do you get if it is not?
- [ ] How can automatic summarization break a data-flow guarantee?
- [ ] Why is a third retry layer worse than no retry at all?
- [ ] What is the difference between middleware and a callback, in one sentence?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~6, Groq)
- [ ] `AgentMiddleware` import path confirmed
- [ ] Hook names and signatures confirmed by running, not by reading
- [ ] `wrap_tool_call` noted for Day 66's least-privilege lab
- [ ] `return None` == "no change" confirmed
- [ ] `middleware=` ordering semantics confirmed — a security claim, so verified
- [ ] `SummarizationMiddleware` default model established
- [ ] `FakeListChatModel` import path confirmed — load-bearing for cheap tests all week
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 39
```

- [ ] Bake-off rows updated: **extension mechanism** and **can I run the full loop without a
      provider?** (check the other three frameworks' answers too)
- [ ] `./m done 39` succeeded — trackers updated automatically
