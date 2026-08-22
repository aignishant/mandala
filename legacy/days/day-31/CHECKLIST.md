# Day 31 — CHECKLIST

**IDs covered:** CR-16 🛠️ (`@router` & conditional logic), CR-17 🛠️ (crews inside flows)

## Demo command

```bash
uv run python days/day-31/lab/route_table.py        # 0 model calls
uv run python days/day-31/lab/run_branch.py T-1001  # fast lane, 1 call
uv run python days/day-31/lab/run_branch.py T-9002  # deep lane, ~20 calls — ONCE
uv run pytest tests/test_routes.py tests/test_organs.py -v
```

Expected: a five-row decision table with a worst-case cost, then a trail ending
`... -> route:deep -> deep_research -> organ:T-9002 -> finish` with `body None`.

## Setup

- [ ] `./m start 31` and `./m scaffold 31` run
- [ ] No new packages — routers ship inside `crewai==1.15.17`
- [ ] Files created (`flows/routes.py`, `flows/organs.py`, two tests, two lab files)
- [ ] Yesterday's tests confirmed green **before** `intake.py` was touched

## CR-16 — the router

- [ ] Can state the inversion: `@listen(step)` vs. `@listen("label")`
- [ ] Knows what `or_` does and what `and_` would do
- [ ] `routes.py` written — `Route`, `ALL_ROUTES`, `ROUTE_BUDGET`, `FAST_LANE_CATEGORIES`
- [ ] Can defend **`Final` strings instead of `Enum`** (string equality vs. the framework)
- [ ] `route()` written with the **`None` branch first**
- [ ] Fast lane requires **severity AND category**, not severity alone
- [ ] Every routing decision calls `state.record(f"route:{...}")`
- [ ] `escalate` makes **zero** model calls — and you noticed why that matters
- [ ] `finish` rejoins all three lanes with `or_` and returns `self.state`
- [ ] `route_table.py` run, and the **worst-case batch cost read before spending it**

## §3.4 — loops

- [ ] `MAX_STEPS` set **below** the state field's `max_length=32`, and can say why
- [ ] Can explain why Pydantic's `max_length` does not stop `.append()`
- [ ] `guard_progress` called from both `route` and `finish`
- [ ] Error message quotes `state.steps` — the trail *is* the debug output

## CR-17 — the crew organ

- [ ] Can say the sentence: **the flow decides, the crew figures out**
- [ ] `organs.py` written with **one** exported function
- [ ] Both preconditions are real `raise`s, not `assert`s — Day 30's TODO(me) resolved
- [ ] The crew receives `state.triage.summary`, **never** `state.ticket_body`
- [ ] Uneasiness about the summary noted for Day 65 (still model output from untrusted input)
- [ ] `memory` / `knowledge` / `guarded` passed **explicitly** despite being defaults
- [ ] `_findings_from` / `_sources_from` written yourself, and bounded to 6 / 8
- [ ] Understood why truncating beats letting Pydantic raise here
- [ ] `ORGAN_REQUEST_BUDGET` agrees with `ROUTE_BUDGET[Route.DEEP]`

## The seam table (§4.3)

- [ ] Four-row seam table filled in (Days 24, 26/27, 30, 31)
- [ ] Can state the asymmetry: **typed going in, text coming out**
- [ ] Parsing effort recorded for the Day-63 scorecard as a *number*

## Tests that must be able to fail

- [ ] `test_the_routing_table` — all five rows green
- [ ] `test_an_unclassified_ticket_escalates` — **flip it:** delete the `None` branch, see red
- [ ] `test_every_route_is_a_known_label` (all 16 combinations)
- [ ] `test_every_route_has_a_budget` — set equality both directions
- [ ] `test_the_cheap_lane_is_actually_cheap`
- [ ] `test_the_router_makes_no_model_call` — **flip it:** add a model call, see red
- [ ] `test_the_organ_refuses_an_unclassified_ticket`
- [ ] `test_the_organ_refuses_to_run_while_the_body_is_present` — **the security test; flip it**
- [ ] `test_the_two_budgets_agree`
- [ ] `test_the_organ_is_the_only_place_the_crew_is_built` — the architecture test
- [ ] Both test files cost **0 model requests**

## Understanding check — answer out loud

- [ ] What exactly does a router return, and how does a downstream step find it?
- [ ] Why is a typo in a route label worse than a crash?
- [ ] Why does the fast lane need two conditions and not one?
- [ ] Why is the safest branch also the cheapest, and is that always true?
- [ ] Why must `MAX_STEPS` be lower than the field's `max_length`?
- [ ] Why is the crew given a summary rather than the ticket, and what does that *not* fix?
- [ ] Why is "the crew is built in exactly one place" worth a test?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~22, Groq)
- [ ] If the deep lane cost far less than 20, `max_iter` investigated and the finding written down
- [ ] `router` / `or_` / `and_` import paths confirmed for 1.15.17
- [ ] **Router-with-no-return behaviour confirmed** (raises, or silently halts?)
- [ ] Whether a router may listen to another router — checked (Day 34 depends on it)
- [ ] Whether `or_` passes the upstream return value through — confirmed
- [ ] `crew.kickoff()` return type re-checked; `.pydantic` availability noted
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 31
```

- [ ] Bake-off row updated: **routing locus of control** — model (Day 13) vs. code (today)
- [ ] `./m done 31` succeeded — trackers updated automatically
