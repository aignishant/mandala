# Day 77 — CHECKLIST 🎯 Phase-11 gate

**IDs covered:** — (buffer/consolidation + gate; produces `docs/adr/gate-phase-11.md`, the behaviour
map, and `make report`)

## Demo command

```bash
uv run pytest -m "eval_unit or eval_trajectory" -q     # 0 requests, whole suite
uv run python scripts/gen_permission_table.py --check
uv run python days/day-77/lab/one_ticket_end_to_end.py T-9001
make report                                            # one command, one screen
uv run pytest tests/test_gate_phase11.py -v
```

Expected: full offline suite green; a single ticket's journey reconstructed from **one** trace
source; a daily report showing requests, phases, retries, cache hits, eval rates and gate status.

## Consolidation (§3)

- [ ] The five flagged debts listed from Days 70–76
- [ ] **Exactly two chosen** — and can say why those two (they make tomorrow harder if left)
- [ ] Debt A: leash constraints moved into `CONSTRAINTS` and rendered by the generator
- [ ] `ActionKind.__args__` used so documented vocabulary cannot diverge from enforced
- [ ] Drift test now covers the leash — verified by changing `MAX_STEPS` and seeing red
- [ ] Debt B: re-record trigger narrowed to behavioural modules, docstrings stripped
- [ ] `test_every_behavioural_module_is_watched` added so the narrowing can't go too far
- [ ] `days/day-77/lab/debts.md` written — **every deferred debt has the day it bites**
- [ ] Day 84 noted as the day that opens by reading `debts.md`

## Gate criterion 1 — every behaviour has a failing-able test

- [ ] `BEHAVIOURS` map written in the language of **promises**, not modules
- [ ] Each row resolves to a **named** test or rubric
- [ ] Any behaviour with no test → test written today, or the row deleted (no aspirational rows)
- [ ] `test_every_declared_behaviour_names_a_real_test` green
- [ ] Map is short and true — would survive a reader spot-checking three rows

## Gate criterion 2 — traces flow to one place

- [ ] `one_ticket_end_to_end.py` reconstructs the full journey from **one** source
- [ ] Journey covers: intake → triage → routing → research (with provider + any rotation) → draft →
      approval stop
- [ ] Any framework not emitting into the neutral layer wired up **or** named as opaque
- [ ] **Opaque internals written into the ADR by framework** — a real Phase-9 bake-off input

## Gate criterion 3 — what did today cost?

- [ ] `scripts/daily_report.py` written; runs in **one command, offline, 0 requests**
- [ ] Shows per-provider requests **against real ceilings**, with flags
- [ ] Shows by-phase breakdown
- [ ] Shows retries as a **percentage**
- [ ] Shows cache hit rate
- [ ] Shows eval rates **on the same screen** as costs — and can say why that matters
- [ ] Wired to `make report` (checked first whether `./m` should own it instead)

## The ADR

- [ ] `docs/adr/gate-phase-11.md` written with an evidence column
- [ ] **Calibration numbers recorded**: kappa per rubric line, position-bias flip count
- [ ] "What is still opaque" section written
- [ ] Debts table carried in, with dates
- [ ] **"What I would not yet conclude from these numbers" written** — golden-set size, judge kappa,
      cache hit rate implications
- [ ] `/freshness` run; one line per pin in `docs/CHANGELOG_PLAN.md`, nil reports included
- [ ] `git tag -a phase-11-complete` created
- [ ] **ADR not signed today** — cold read scheduled for tomorrow morning

## Tests that must be able to fail

- [ ] `test_every_declared_behaviour_names_a_real_test` — **flip it:** delete it and the map becomes
      reassuring fiction
- [ ] `test_every_behavioural_module_is_watched`
- [ ] `test_the_leash_constraints_appear_in_the_generated_table`
- [ ] `test_the_daily_report_runs_offline`
- [ ] `test_the_gate_adr_records_calibration_numbers`
- [ ] `test_debts_carry_a_date`
- [ ] Whole offline suite green: unit + trajectory + red team + drift + gate

## Understanding check — answer out loud

- [ ] What is a buffer day actually for?
- [ ] Why two debts rather than five?
- [ ] Why is "four trace destinations" the same as none?
- [ ] Name one framework internal that is still opaque, and what that costs you
- [ ] Why do costs and eval scores belong on the same screen?
- [ ] What can a 20-example golden set detect, and what can it not?
- [ ] Given your judge's kappa, how many decimal places should you quote?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~15)
- [ ] Closing line written: **what the warm cache does to re-record cost**, and what that enables
      for the capstone
- [ ] `pytest --collect-only -q` output format confirmed for the behaviour-map test
- [ ] `ast.dump` stability across patch versions confirmed (or a stabler approach chosen)
- [ ] `Literal.__args__` confirmed on `ActionKind`
- [ ] All Phase-11 pins re-verified; full `/freshness` sweep logged

## Commit

```bash
./m check
./m done 77
```

- [ ] Behaviour map, daily report, ADR and debts all committed
- [ ] Phase-11 rows updated in `docs/CURRICULUM_INDEX.md` by `./m done`, not by hand
- [ ] `./m done 77` succeeded
- [ ] **Day 78 not started until the cold read is done**
