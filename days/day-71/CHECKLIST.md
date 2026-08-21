# Day 71 — CHECKLIST

**IDs covered:** AG-22 🛠️ (evals: the three layers — unit, trajectory, outcome)

## Demo command

```bash
uv run pytest -m eval_unit -q                       # instant, 0 requests
uv run python days/day-71/lab/run_layers.py         # 20 golden tickets, records trajectories
uv run pytest tests/test_eval_trajectory.py tests/test_eval_scoring.py -v
ls tests/fixtures/trajectories/*.json | wc -l       # ≥ 20
```

Expected: per-layer scores printed (unit / trajectory / outcome), every trajectory written to disk,
and grading the recordings costs **0 requests**.

## Setup

- [ ] `./m start 71` and `./m scaffold 71` run
- [ ] **No new dependencies** — third day running
- [ ] `src/mandala/evals/` created as a **library**, not a script folder
- [ ] Day-2 golden set re-read before writing anything
- [ ] Labels that no longer match today's judgement **fixed in their own commit**
- [ ] `tests/fixtures/trajectories/` created and gitignore reviewed (these are committed, on purpose)

## The three layers

- [ ] Can name all three, the question each answers, and how each fails
- [ ] Can say why one aggregate number cannot distinguish the three
- [ ] Markers added to `pyproject.toml`; `--strict-markers` confirmed on
- [ ] `tests/test_markers.py` (Day 2) extended so an **unmarked eval fails the suite**
- [ ] `pytest -m eval_unit` and `-m eval_outcome` both select the right sets
- [ ] Resisted adding a fourth "integration" marker — and can say why

## Layer two — trajectory (the important one)

- [ ] `Trajectory` and `Step` are **frozen**
- [ ] Trajectories serialise to JSON and round-trip
- [ ] `writes()` derives from `permissions.TOOLS`, never a hard-coded list
- [ ] `escalated_before_any_external_write` written — the plan's own AG-22 example
- [ ] Vacuous-truth case decided deliberately (read-only run passes) and **encoded in a test**
- [ ] Ordering compared by **index**, not timestamp
- [ ] `no_agent_exceeded_its_permissions` written
- [ ] `terminated_within_budget` written
- [ ] `did_not_retry_a_write` written — and can say why a retried write is its own class of bug
- [ ] Every rubric returns `(bool, reason)`; reasons readable in a CI log at midnight
- [ ] `ALL` dict keyed by name so Day 74 can report per-rubric pass rates

## Layer three — outcome (deterministic part only)

- [ ] `outcome_checks` written; judge deferred to tomorrow
- [ ] `_no_canary` wires **Day 69's red team into the standing suite** — and can say why that matters
- [ ] `aggregate` uses per-item `all(...)`, not per-check averaging
- [ ] Empty set scores **0.0**, not 1.0

## Tests that must be able to fail

- [ ] `test_write_without_approval_fails`
- [ ] `test_approval_after_the_write_fails` — **flip it:** use timestamps, watch it go flaky
- [ ] `test_approval_before_the_write_passes`
- [ ] `test_a_read_only_run_passes_vacuously` — encodes the decision, not just the behaviour
- [ ] `test_every_rubric_returns_a_reason_string`
- [ ] `test_an_empty_eval_set_scores_zero_not_one`
- [ ] `test_a_row_fails_if_any_check_in_it_fails`
- [ ] `test_write_tools_come_from_the_permission_table` — **flip it:** hard-code the list, see the
      coupling break
- [ ] All grading tests cost **0 model requests**

## Understanding check — answer out loud

- [ ] Give a failure that unit catches and trajectory does not, and vice versa
- [ ] Why is "escalated before any external write" the highest-value eval in this plan?
- [ ] Why does a read-only run pass that rubric, and what would break if it didn't?
- [ ] Why average items rather than checks?
- [ ] Why does an empty eval set score zero?
- [ ] Why record trajectories rather than re-run the agent to grade it?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~20)
- [ ] Ratio noted: producing evidence costs, grading it is free
- [ ] `--strict-markers` confirmed
- [ ] `pytest -m` boolean expression syntax confirmed for Day 74
- [ ] Golden-set schema confirmed to carry the labels the outcome layer needs
- [ ] `Trajectory` JSON serialisation approach chosen deliberately
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 71
```

- [ ] Recorded trajectories committed (they are Day 74's CI input)
- [ ] Golden-label changes, if any, in a **separate** commit from code
- [ ] `./m done 71` succeeded
