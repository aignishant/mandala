# Day 30 — CHECKLIST

**IDs covered:** CR-14 🛠️ (`@start` / `@listen`), CR-15 🛠️ (structured flow state)

## Demo command

```bash
uv run python days/day-30/lab/state_trap.py       # 0 model calls
uv run python days/day-30/lab/first_flow.py T-1004
open days/day-30/lab/intake_flow.html             # the generated graph
```

## Setup

- [ ] `./m start 30` and `./m scaffold 30` run
- [ ] No new packages — Flows ship inside `crewai==1.15.17`
- [ ] **Flow import path settled for 1.15.17** and noted — the rest of Phase 5 depends on it
- [ ] Files created (`flows/state.py`, `flows/intake.py`, two lab files, two test files)

## CR-14 — `@start` and `@listen`

- [ ] Can recite the Crews-vs-Flows table, especially **who decides order**
- [ ] Understands the graph lives **in the decorators**, next to each step
- [ ] Can state the two channels: previous **return value** vs. **`self.state`**
- [ ] Reading `IntakeFlow` top to bottom **is** reading the graph
- [ ] `classify` wired to the Day-29 agents (the TODO(me)) — shape kept
- [ ] `research` and `draft` wired
- [ ] `flow.plot()` run and the **HTML graph actually opened**
- [ ] Noted the parallel to LangGraph Studio (Day 43)

## CR-15 — structured state

- [ ] `state_trap.py` run — **saw the typo become a second key**
- [ ] Can give the four reasons in order, and can say why reason 3 is deepest
- [ ] State model has `# transient` vs. `# accumulated` sections — not decoration
- [ ] `ticket_body` carries the shouting description
- [ ] **Every** string and list field bounded (`max_length`)
- [ ] `stage` is a `Literal` — countable on Day 71
- [ ] `TriageResult` reused unchanged — **fourth** framework, no flow-flavoured copy
- [ ] `record()` accumulates the audit trail as a side effect of doing the work

## Typed but global (§4.4) — the new problem

- [ ] Can recite the crew-context vs. flow-state table
- [ ] Can state the reversal: crew seam **narrow by default**, flow state **wide by default**
- [ ] `drop_body()` written and called immediately after classification
- [ ] `assert` guards at the top of `research` and `draft`
- [ ] **Decided whether asserts should be real raises** (`python -O` strips asserts) — decision recorded
- [ ] Can name the one thing deletion does **not** protect against
- [ ] Understands that **ordering is now a security property**
- [ ] Bake-off entry written: "Day 30: typed (better) but global (worse); scoping by deletion"

## The LangGraph comparison (§4.2) — start it today

- [ ] Table started with the CrewAI column filled in
- [ ] **Concurrent-write row answered** — or recorded as "the framework has no answer", which is a finding
- [ ] Persistence row noted (Day 32 `@persist` vs. Day 47 checkpointers)
- [ ] Saved somewhere Day 43 will find it

## Tests that must be able to fail

- [ ] `test_a_typo_is_rejected` — **flip it:** use a dict and notice the test becomes unwritable
- [ ] `test_wrong_types_are_rejected_at_the_boundary`
- [ ] `test_the_raw_body_starts_empty`
- [ ] `test_every_string_field_is_bounded` (+ TODO(me): read Pydantic metadata properly)
- [ ] `test_stage_is_countable`
- [ ] `test_the_schema_is_still_day_4s`
- [ ] `test_record_accumulates_an_audit_trail`
- [ ] `test_the_audit_trail_is_bounded` — routers arrive tomorrow and routers loop
- [ ] `test_drop_body_removes_it`
- [ ] `test_drop_body_is_recorded`
- [ ] `test_downstream_steps_refuse_to_run_with_the_body_present` — **the security test; flip it**
- [ ] `test_the_step_order_is_declared_in_the_class` — crude on purpose, TODO(me) to do it properly
- [ ] `test_a_full_run_ends_with_no_raw_text_anywhere` — ships **skipped**; wire it after the agents
- [ ] Both test files cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why does one vendor shipping two answers to "who owns the loop" matter?
- [ ] What exactly does an untyped dict cost me, in the order that matters?
- [ ] Why is flow state better *and* worse than the crew seam?
- [ ] Why is deletion the only scoping mechanism available?
- [ ] Why is "ordering is a security property" uncomfortable, and why is it defensible here?
- [ ] Why did today cost so little compared with yesterday?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~38, Groq)
- [ ] Noticed the design property: **deterministic skeleton is free; autonomous organs cost**
- [ ] `@start()` / `@listen` signatures confirmed for 1.15.17
- [ ] **`kickoff(inputs={...})` unknown-key behaviour confirmed** — the most consequential small question
- [ ] `flow.plot()` confirmed; if it pulls a dependency, **ledger row + changelog line**
- [ ] Concurrent state writes investigated
- [ ] Whether `Flow` exposes its graph programmatically — checked
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 30
```

- [ ] Bake-off list updated: Flows as a **separate row** from Crews, not a variant
- [ ] `./m done 30` succeeded — trackers updated automatically
