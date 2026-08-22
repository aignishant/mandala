# Day 18 — CHECKLIST

**IDs covered:** OAI-17 🅿️+🛠️ (Programmatic Tool Calling, concept only + the free coordinator tool)

## Demo command

```bash
uv run python days/day-18/lab/coordinator_demo.py       # one plan, one tool call, 8 tickets
uv run python days/day-18/lab/roundtrip_count.py        # THE measurement — run it, record it
uv run python days/day-14/lab/span_tree.py              # read the two shapes side by side
```

## Setup

- [ ] `./m start 18` and `./m scaffold 18` run
- [ ] **No new packages** — `docs/PINS.md` grows no Day-18 ledger row, and can say why
- [ ] `tests/test_permissions.py` and `tests/test_tracing.py` green **before** starting
- [ ] Fixtures hold T-1001 … T-1010 (+ T-9002); today's batch is T-1001 … T-1008
- [ ] Files created (`src/mandala/coordinator.py`, two lab files, one test file)

## OAI-17 🅿️ — the paid feature (read, not run)

- [ ] Can draw the two loops: 9 model calls naive vs. ~2 with a model-written program
- [ ] Can say **why it is two turns, not one** (write the program, interpret the result)
- [ ] Can explain the second win: tool results stay in program variables, never in the context
- [ ] Knows it is the hosted **code interpreter** (OAI-14) plus one permission field
- [ ] Can state the §3.3 sentence: **`allowed_callers` is "who may call this tool", not "how fast"**
- [ ] Can give the `post_reply` example — why a write must never be in the program's caller list
- [ ] Read the live docs and **confirmed the program's language** (the plan says JS — verify)
- [ ] Can name **three things the paid version genuinely does better**, without flinching
- [ ] Can say precisely *why* we cannot run it (Responses API + hosted tool type + Principle 5)

## 🛠️ The coordinator — the security rules (§4.2)

- [ ] `OPERATIONS` is an **allowlist**, closed, and an unknown `op` is a `ValidationError`
- [ ] Every step is `extra="forbid"`; every argument typed and bounded
- [ ] `MAX_STEPS` / `MAX_ITEMS` / `MAX_OUTPUT_CHARS` enforced **before** execution
- [ ] No path, URL, shell fragment or `getattr` dispatch anywhere in the schema or executor
- [ ] Every op that touches a tool declares `requires`, and that tool is in `permissions.TOOLS`
- [ ] `permissions.check()` runs for **every** step **before** step one executes
- [ ] Can say the corollary out loud: **a coordinator may never widen a grant**
- [ ] The coordinator is **read-only** — no operation reaches a `writes=True` tool (Principle 6)

## 🛠️ The coordinator — built

- [ ] `Plan` / `Step` / `CoordinatorResult` written; `Field(discriminator="op")` on the union
- [ ] `plan_cost()` written (the TODO(me)) — can say what I decided an "item" is, and why
- [ ] `_apply` dispatches with `isinstance`, not by string lookup — can say why
- [ ] `_tickets()` reads `context.tickets_path` (Day 12's DI), not a second data path
- [ ] `render()` separate from `run_plan()`; truncation notice is **advice**, not an ellipsis
- [ ] `TakeFields` includes `"body"` on purpose — can explain why excluding it would be theatre
- [ ] `ctx.context.audit(...)` line emitted per batch (the observability repayment)
- [ ] Printed `coordinate.params_json_schema` and looked at what the model actually receives

## The permission table (§4.4) — table first, agent second

- [ ] `"coordinate"` added to `permissions.TOOLS` with `writes=False`, `reads_untrusted=True`
- [ ] `blast_radius` says **"a batcher, never a widener"**
- [ ] Granted in `AGENTS["researcher"].tools`
- [ ] `uv run pytest tests/test_permissions.py -q` green; `trifecta_violations()` still `[]`

## The measurement (§4.6) — the deliverable

- [ ] Confirmed `model_calls()` matches **my provider's** span type before trusting any number
- [ ] `roundtrip_count.py` run at least twice, trace dirs cleared between runs
- [ ] **Naive model calls: ___**
- [ ] **Coordinator model calls: ___**
- [ ] **Ratio: ___ x**
- [ ] Re-measured naive with `parallel_tool_calls=True` — batched naive count: **___**
      (or noted here that the setting does not exist / is ignored: ______)
- [ ] Read both span trees; can describe the staircase vs. the three spans
- [ ] Both numbers logged in `docs/RATE_BUDGET.md` alongside the request count

## What it costs (§4.8)

- [ ] Can name the adaptivity loss, and the mitigation (a second plan is still 2, not 9)
- [ ] Can name the schema-maintenance cost of choosing data over code
- [ ] Can recite the three-day pattern: Day 14 processor, Day 15 hit loop, Day 18 batch —
      **partial-failure isolation, the batch survives the item**
- [ ] Can name the pattern's limit: ingestion degrades, **boundaries never do**

## Tests that must be able to fail

- [ ] `test_the_plan_schema_rejects_an_unknown_operation` — the allowlist proof
- [ ] `test_a_step_cannot_carry_an_argument_nobody_defined` — `extra="forbid"`
- [ ] `test_the_operation_registry_is_exactly_the_five_we_reviewed` — deliberate change-detector
- [ ] `test_a_plan_longer_than_max_steps_is_rejected`
- [ ] `test_a_plan_that_would_touch_too_many_items_is_refused_before_it_runs` — red until `plan_cost`
- [ ] `test_the_rendered_output_is_bounded` — 50 KB body, 30 rows, still fits (Day 4)
- [ ] `test_every_operation_that_touches_a_tool_names_a_real_permission` — the trap of the day
- [ ] `test_the_coordinator_can_reach_nothing_its_caller_lacks` — the subset assertion
- [ ] `test_a_caller_without_the_tool_is_denied` — `PermissionDenied` propagates (Day 10)
- [ ] `test_permission_is_checked_before_any_step_runs` — **flip it:** move the check inside the
      execution loop and watch it go red
- [ ] `test_the_coordinator_grants_no_write_ability` + `trifecta_violations() == []`
- [ ] `test_one_bad_ticket_does_not_lose_the_batch` — asserts **both** halves
- [ ] `test_filter_and_count_agree` — a relationship, not a hard-coded tally
- [ ] `test_the_coordinator_path_costs_strictly_fewer_model_calls` — cassette-backed, and asserts
      `coord_calls > 0` **first**
- [ ] Every test but the last costs **0 model requests**

## Understanding check — answer out loud

- [ ] Why is `allowed_callers` a permission boundary rather than an optimisation?
- [ ] Why is "their model emits code, mine emits data" the whole compare/contrast?
- [ ] Why must the permission loop run before *any* step, not per step?
- [ ] Why does `_apply` use `isinstance` instead of a dict of handlers keyed by `op`?
- [ ] Why is excluding `"body"` from `TakeFields` security theatre?
- [ ] Why does `PermissionDenied` escape the batch loop when every other exception is collected?
- [ ] On a free tier, why is "fewer round trips" a budget claim rather than a performance claim?
- [ ] What did Day 14's tracer buy me today that a `print` statement could not?

## Budget & freshness

- [ ] Model requests logged in `docs/RATE_BUDGET.md` (declared: ~61, Groq)
- [ ] Roughly half the budget went on *demonstrating* the naive path — paid once, not repeatedly
- [ ] `allowed_callers` shape verified against the live Responses docs (read, not tested)
- [ ] Pydantic-model-as-tool-parameter behaviour confirmed in `openai-agents` 0.22.0
- [ ] `ModelSettings.parallel_tool_calls` confirmed in 0.22.0 (or its absence recorded)
- [ ] Generation-span type confirmed for my provider (Day 14 §8's open item, now closed)
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md` — **do not silently adapt** (Principle 14)

## Commit

```bash
./m check
./m done 18
```

- [ ] `./m done 18` succeeded — trackers updated automatically
- [ ] Tomorrow is the harness 🅿️ + the local Docker sandbox — `docker` and Docker Desktop are the
      Day-19 ledger row, so install Docker Desktop tonight
