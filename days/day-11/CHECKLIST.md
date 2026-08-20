# Day 11 — CHECKLIST

**IDs covered:** OAI-05 🛠️ (structured outputs / `output_type`), OAI-06 🛠️ (sessions & memory)

## Demo command

```bash
cd days/day-11/lab
uv run python typed_agent.py T-1001
uv run python session_demo.py t-4521 "my login loops after SSO"
uv run python session_demo.py t-4521 "what did I first tell you?"
uv run python session_edges.py
cd ../../..
```

Expected: a typed `TriageResult` printed as JSON; the second `session_demo` run answers from
history; `session_edges.py` gives you a definite answer about the trimming edge.

## Setup

- [ ] `./m start 11` and `./m scaffold 11` run
- [ ] No new packages (SQLite is stdlib)
- [ ] `.mandala/` ignored by git
- [ ] Files created (three lab files, two test files)

## OAI-05 — structured output

- [ ] `output_type=TriageResult` on the agent
- [ ] `result.final_output` is a `TriageResult`, not a string
- [ ] `needs_human_review()` still works — schema behaviour survived the framework
- [ ] `ModelBehaviorError` import path verified in 0.22.0
- [ ] The agent still has tools, and can look things up **before** producing typed output

### The three verifications (do not skip — the adapter is documented as beta)

- [ ] **(1)** Ran with LiteLLM verbose and identified **which mechanism** is used on Groq (`response_format` vs a synthetic tool) — written down
- [ ] **(2)** Forced a failure and **counted the retries** in `usage.requests` — written down
- [ ] **(3)** Confirmed a bad `Literal` value produces `ModelBehaviorError`, not a coerced value

## OAI-06 — sessions

- [ ] Can name which session classes are usable on $0 and which need a paid key
- [ ] Can list the four protocol methods and map each onto your Day-7 `JsonSession`
- [ ] Noted `pop_item()` has no Day-7 equivalent, and what it is for
- [ ] `SQLiteSession(id, DB)` with **two** arguments (file-backed, not in-memory)
- [ ] `session=session` passed to `Runner.run`
- [ ] Ran three times and confirmed memory across separate processes
- [ ] Watched the item count grow, and understood that nothing trims it by default
- [ ] Inspected the SQLite file
- [ ] Spent fifteen minutes checking how `session_id` is used in the SDK's SQL (parameterised?)

## The interrogation (§4.4) — the day's most valuable half hour

- [ ] `session_edges.py` run, with a history that **contains assistant→tool pairs**
- [ ] Identified which item shape the SDK stores through LiteLLM (`role`/`tool_calls` vs `type: function_call`)
- [ ] Determined whether a naive `items[-6:]` window starts with an **orphaned tool result**
- [ ] Ran both `SessionSettings(limit=...)` and `session_input_callback` and looked for degraded answers
- [ ] **Finding written into `docs/CHANGELOG_PLAN.md`** — whichever way it went
- [ ] Decided: delete `_trim_safely`, or wire it in as a `session_input_callback`

## Tests that must be able to fail

- [ ] `test_final_output_is_a_typed_object_not_a_string`
- [ ] `test_schema_behaviour_survives_the_framework`
- [ ] `test_literal_constraint_is_still_enforced`
- [ ] `test_agent_can_use_tools_before_producing_typed_output`
- [ ] `test_structured_output_retries_are_counted` — including the `usage.requests is not None` half
- [ ] `test_session_protocol_round_trip`
- [ ] `test_clear_session_empties_it`
- [ ] `test_get_items_limit_returns_the_most_recent` — verifies **which end** `limit` takes from
- [ ] `test_naive_window_can_orphan_a_tool_result` — **`TODO(me)` solved by asserting what you measured**, not what you hoped
- [ ] `tests/test_sdk_session.py` costs **0 model requests**
- [ ] Cassettes recorded; suite replays offline

## Understanding check — answer out loud

- [ ] What does `output_type` replace from Day 4, line for line?
- [ ] Why can the SDK agent look a ticket up *before* producing typed output, when Day 4's could not?
- [ ] Which two session classes are paid, and what does that tell you about the SDK's shape?
- [ ] What is the exact edge case you interrogated, and what did you find?
- [ ] Why is "having built it myself" what let you ask that question?
- [ ] Where do hidden requests come from today, and how did you count them?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~50, Groq)
- [ ] `SessionSettings` import path verified
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 11
```

- [ ] `./m done 11` succeeded — trackers updated automatically
