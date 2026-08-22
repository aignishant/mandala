# Day 76 — CHECKLIST

**IDs covered:** AG-26 🛠️ (rate-limit & cost engineering), LG-22 🛠️ (caching, node caching, model
tiering), LG-19 🅿️ (LangSmith platform literacy)

## Demo command

```bash
uv run python days/day-76/lab/cost_report.py                 # 0 requests — reads .traces/
uv run pytest tests/test_budget.py tests/test_cache.py -v    # 0 requests
uv run python days/day-76/lab/tiering_experiment.py          # ≤ 20 requests
uv run python days/day-73/lab/compare.py triage-baseline-D73 tiering-small-router
uv run python days/day-76/lab/tiering_experiment.py          # again — near-zero, cache hits
```

Expected: request counts by provider / model / phase with headroom flags; the tiering comparison
showing per-example wins and losses; the second run costing almost nothing.

## Setup

- [ ] `./m start 76` and `./m scaffold 76` run
- [ ] **No new dependencies**
- [ ] **Every TBD in `docs/RATE_BUDGET.md` filled with a real, current number** before optimising
- [ ] `.cache/` added to `.gitignore` beside `.traces/`
- [ ] Before-picture printed and **saved to notes** before any change

## AG-26 — measure

- [ ] `costs.py` groups by **any attribute** — provider, model, and pipeline phase
- [ ] Phase view produced (only possible because of Day 75's span naming) — noted what surprised you
- [ ] **Retries counted as billable** — and can say why excluding them flatters the report
- [ ] Non-model spans excluded from the report
- [ ] `headroom()` reports against **real ceilings**, with a flag
- [ ] **No dollar figures anywhere** — and can say why

## LG-22 — cache

- [ ] Key includes provider, model, **system prompt**, user, temperature
- [ ] Sharded directory layout (`k[:2]`)
- [ ] `cacheable()` written as **testable policy**, not a comment
- [ ] Temperature > 0 never cached
- [ ] Prompts containing tool results never cached — and can say why
- [ ] Hit rate measured on the eval suite; second run near-zero
- [ ] If the hit rate was **not** ~100% on a repeat run, found what non-determinism was in the key

## LG-22 — tiering

- [ ] Tier table written for your actual pipeline steps
- [ ] **One** step moved to the small tier and re-run — not all of them at once
- [ ] Compared with Day 73's `compare.py`, per example
- [ ] Outcome recorded: kept / reverted / suspicious
- [ ] If the pass rate **rose**, investigated whether the small model games a rubric (e.g. length)
- [ ] Checked whether `langgraph==1.2.11` has a built-in node cache before duplicating it

## AG-26 — budget (the RT-12 fix)

- [ ] `RunBudget` is **per run**, not per day — and can say why that's the RT-12 threat model
- [ ] `charge()` called from the router (choke point), not by each caller
- [ ] Exception message includes the **per-phase breakdown**
- [ ] Context pruning applied (keep first + last N); noted Day 47 offers a better version
- [ ] Provider rotation on 429 confirmed working; span records **which provider answered**
- [ ] Ran the rotation drill deliberately and watched the fallback fire

## LG-19 🅿️ — literacy

- [ ] `days/day-76/lab/managed_layer.md` written **in your own words**
- [ ] Fleet, Insights and full-workflow cost tracking each named
- [ ] **The specific gap that would hurt at scale named in your own sentence** — not a generic
      "it's more polished"
- [ ] Docs page cited with today's date

## Tests that must be able to fail

- [ ] `test_a_runaway_run_is_stopped`
- [ ] `test_the_budget_error_names_the_guilty_phase`
- [ ] `test_rt12_is_now_a_permanent_test` — cross-referenced from `docs/REDTEAM.md`
- [ ] `test_temperature_above_zero_is_never_cached`
- [ ] `test_prompts_containing_tool_results_are_never_cached`
- [ ] `test_the_system_prompt_is_part_of_the_cache_key` — **flip it:** drop `system`, watch evals
      replay answers to a deleted prompt
- [ ] `test_retries_count_against_the_quota`
- [ ] `test_non_model_spans_do_not_dilute_the_report`
- [ ] All cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why is "shorten the prompt" the wrong first move on a per-day request cap?
- [ ] Why do retries count, and what does excluding them do to your picture?
- [ ] Give two things that must never be cached, with reasons
- [ ] What is the total-eval-integrity failure caused by a cache key missing the system prompt?
- [ ] Why validate tiering by per-example diff rather than aggregate?
- [ ] Why is a per-run budget a security control and not just an economic one?
- [ ] Name the choke-point pattern you have now applied three times (Days 70, 75, 76)

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~45)
- [ ] **Cache hit rate recorded** and its consequence for Day 74's re-record step noted
- [ ] Real RPM / RPD / TPM confirmed today for every provider
- [ ] Confirmed how each provider counts a 429'd request
- [ ] LangGraph node caching checked on 1.2.11
- [ ] Prompt caching availability on free tiers checked
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 76
```

- [ ] Before/after request numbers committed in the day's notes
- [ ] `.cache/` and `.traces/` confirmed absent from `git status`
- [ ] `./m done 76` succeeded
