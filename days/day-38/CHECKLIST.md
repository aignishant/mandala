# Day 38 — CHECKLIST

**IDs covered:** LC-05 🛠️ (`create_agent`), LC-06 🛠️ (structured output in 1.x)

## Demo command

```bash
uv run python days/day-38/lab/what_is_it.py         # 0 requests — introspect first
uv run python days/day-38/lab/triage_once.py T-9002 # <= 6 requests
uv run pytest tests/test_lc_agent.py -v
```

Expected: a class name containing **langgraph**, an ASCII graph of the loop, then a printed
trajectory ending in a real `TriageResult`.

## Setup

- [ ] `./m start 38` and `./m scaffold 38` run
- [ ] No new packages — and no graph-drawing dependency added without a ledger row
- [ ] Files created (`lc/agent.py`, `tests/test_lc_agent.py`, three lab files)

## LC-05 — `create_agent`

- [ ] `agent.py` written — model, tools, prompt, optional `response_format`
- [ ] Model comes from Day 36's factory; **no vendor named in this file**
- [ ] Tools come from Day 37's `READ_TOOLS`, unchanged
- [ ] Prompt **imported** from `mandala.prompts`, not inlined
- [ ] `what_is_it.py` run **before** invoking anything
- [ ] Confirmed the returned type is a **compiled LangGraph** — read from your own install
- [ ] `invoke` / `stream` / `astream` all present — the Runnable payoff from Day 36
- [ ] `draw_ascii()` output saved for comparison with Day 43's own graph
- [ ] Connected it: `create_agent` returns a graph → Day 42's seam → LG-15's deprecation

## The missing guard (§3.3)

- [ ] Found what 1.3.16 calls the iteration cap
- [ ] `MAX_STEPS` actually **passed**, not merely defined
- [ ] Can state the difference between an agent step cap and `recursion_limit`
- [ ] Four-row cap table filled in (Days 5, 10, 29, 38)
- [ ] Can say what an uncapped loop costs on a 50-RPD provider

## LC-06 — structured output

- [ ] `response_format=TriageResult` wired
- [ ] `triage_once.py` run **structured**
- [ ] `triage_once.py` run **unstructured** — and the `AIMessage` counts compared
- [ ] Determined which strategy the adapters use: native / tool-call / second call
- [ ] Cost implication written into `docs/RATE_BUDGET.md`, not just the changelog
- [ ] `structured_response` key name confirmed for 1.3.16
- [ ] Result type verified as `TriageResult`, not a lookalike dict
- [ ] Ticket body **delimited** — and understood that this is hygiene, not defence

## `four_ways.md` — the deliverable

- [ ] All four columns filled from **git history**, not memory
- [ ] "Lines of glue" includes the unwrapping, not just the declaration
- [ ] "Behaviour on schema violation" answered for all four — the row that separates them
- [ ] "Can I see the failure?" answered (Principle 8)
- [ ] Answered: did the schema survive four frameworks **unchanged**?
- [ ] Answered: which ergonomics I preferred, and why it is not simply the shortest
- [ ] One line per framework on what it made hard

## Tests that must be able to fail

- [ ] `test_the_agent_holds_only_read_tools` — **flip it:** add a write tool, see red
- [ ] `test_the_loop_is_capped` — catches "defined but never passed"
- [ ] `test_the_cap_is_small_enough_to_matter`
- [ ] `test_no_model_id_appears_in_the_agent_module`
- [ ] `test_the_prompt_is_imported_not_inlined`
- [ ] `test_the_schema_is_still_day_4s` — **flip it:** subclass `TriageResult`, see red
- [ ] `test_structured_can_be_turned_off` — both directions, and `is` not `==`
- [ ] `test_both_paths_differ_only_in_response_format[True|False]`
- [ ] Whole file runs offline with **no keys**

## Understanding check — answer out loud

- [ ] What is `create_agent` actually returning, and what three later days depend on that?
- [ ] Where did your Day-5 iteration guard go, and what is it called now?
- [ ] Why is "which structured-output strategy" a budget question?
- [ ] Which two files survived all four frameworks unchanged, and why those two?
- [ ] Why would subclassing `TriageResult` for LangChain invalidate the whole bake-off?
- [ ] How do you count today's request usage from the printed trajectory?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~12, Groq)
- [ ] Both runs logged separately — structured vs. unstructured
- [ ] `create_agent` import path confirmed
- [ ] Iteration-cap parameter name confirmed and recorded
- [ ] Output key name confirmed
- [ ] Schema-violation behaviour established for at least one provider
- [ ] `system_prompt` accepted type confirmed (`str` vs. `SystemMessage`)
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 38
```

- [ ] Bake-off rows updated: **agent construction**, **structured output**, **loop cap discoverability**
- [ ] `./m done 38` succeeded — trackers updated automatically
