# Day 74 — CHECKLIST

**IDs covered:** AG-24 🛠️ (regression gates in CI — evals on every PR, a drop blocks merge)

## Demo command

```bash
uv run python days/day-74/lab/refresh_recordings.py     # ~20 requests, your machine
uv run python scripts/eval_gate.py                      # 0 requests — must exit 0
uv run pytest tests/test_eval_gate.py -v                # 0 requests
act -j gate 2>/dev/null || echo "push the branch and watch the run"
```

Expected: gate prints `rate x -> y · fixed [...] · broken []` and exits 0; a deliberately broken
rubric makes it exit 1 with an annotation naming the ticket **and** the rubric line.

## Setup

- [ ] `./m start 74` and `./m scaffold 74` run
- [ ] **No new dependencies** — `pytest-recording` / `vcrpy` came on Day 2
- [ ] Day-2 workflow inspected first; today **extends** it rather than replacing it
- [ ] `source_hash` added to the output of `run_experiment.py`

## AG-24 — the gate script

- [ ] **Rule 1** (hard floor ≥ 0.85, the plan's own AG-24 example) implemented
- [ ] **Rule 2** (no example that passed in the baseline may fail now) implemented
- [ ] Can give a concrete swap that rule 1 misses and rule 2 catches
- [ ] Dataset-version mismatch checked **first**, with its own message naming the fix
- [ ] All failures collected and reported — the gate does not stop at the first
- [ ] Per-failure GitHub annotations carry the Day-71 `why` string
- [ ] A new example present only in the candidate **does not** block merge — deliberate, and tested
- [ ] `fixed` list printed even on success

## AG-24 — the workflow

- [ ] `.github/workflows/evals.yml` written
- [ ] `permissions: contents: read` — least privilege for the workflow token
- [ ] **Step asserting model API keys are ABSENT** — and can say why that's the interesting direction
- [ ] `uv sync --frozen`; `uv` version pinned in the action
- [ ] `gen_permission_table.py --check` runs (Day 70's drift check, now enforced)
- [ ] `tests/test_redteam.py` runs — twelve attacks, every PR, zero requests
- [ ] `pytest -m "eval_unit or eval_trajectory"` runs; outcome layer excluded
- [ ] Steps ordered cheapest-first
- [ ] Trigger is `pull_request`, **never `pull_request_target`**
- [ ] Job made **required** in branch protection — a gate that isn't required is a suggestion

## Recordings stay honest (§4)

- [ ] `refresh_recordings.py` written; it is the **only** step that costs money
- [ ] `test_recordings_were_refreshed_after_the_last_source_change` written
- [ ] Verified it goes red: touch a file in `src/mandala/`, run the suite, see the failure
- [ ] Failure message names the exact command to run
- [ ] `pr-candidate.json` committed alongside the change that produced it
- [ ] Noted `WATCHED` is coarse today; logged as a candidate Day-77 buffer task

## Tests that must be able to fail

- [ ] `test_the_floor_matches_the_plan` — lowering it requires an amendment
- [ ] `test_a_regression_fails_the_gate`
- [ ] `test_a_swap_fails_even_when_the_aggregate_rises` — **the headline test**
- [ ] `test_a_dataset_change_fails_with_a_distinct_message`
- [ ] `test_a_new_example_does_not_block_the_merge`
- [ ] `test_recordings_were_refreshed_after_the_last_source_change` — **flip it:** delete it and
      stale recordings pass forever
- [ ] `test_the_workflow_asserts_no_model_keys_are_present`
- [ ] `test_the_workflow_runs_the_permission_table_drift_check`
- [ ] Every test costs **0 model requests**

## Understanding check — answer out loud

- [ ] Why can't the gate call models — give both reasons (security and flakiness)?
- [ ] Why is a flaky gate worse than no gate?
- [ ] Give a numeric example where the aggregate rises and the gate correctly fails
- [ ] What exactly makes an offline eval gate become theatre, and what prevents it?
- [ ] Why must the baseline be re-pinned in its own commit?
- [ ] What is the honest cost of an offline gate, and who pays it when?

## Budget & freshness

- [ ] `docs/RATE_BUDGET.md` records **0 requests per CI run**, in bold
- [ ] Re-record cost (~20) recorded as per-behaviour-change, not per-push
- [ ] `setup-uv` action pinned; `uv sync --frozen` fails (not resolves) on a stale lock — verified
- [ ] Annotation syntax confirmed rendering on the Files-changed tab
- [ ] `-m` marker expression verified with `--collect-only`
- [ ] Confirmed forked-PR runs cannot see secrets
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 74
```

- [ ] Opened one throwaway PR and **watched the gate go red on purpose**, then green
- [ ] Workflow + gate script + recordings committed
- [ ] `./m done 74` succeeded
