# Day 73 — CHECKLIST

**IDs covered:** LG-18 🛠️ (datasets, experiments, baseline pinning, per-example comparison)

## Demo command

```bash
uv run pytest tests/test_dataset.py -v                              # 0 requests
uv run python days/day-73/lab/upload_dataset.py                     # idempotent
uv run python days/day-73/lab/run_experiment.py triage-baseline-D73
uv run python days/day-73/lab/compare.py triage-baseline-D73 triage-baseline-D73  # 0 broken
```

Expected: dataset uploaded once (second run says "nothing to do"); baseline JSON written to
`tests/fixtures/experiments/`; comparison prints aggregate + `fixed`/`BROKEN` lists.

## Setup

- [ ] `./m start 73` and `./m scaffold 73` run
- [ ] `langsmith==0.11.1` **verified live** before `uv add`, then pinned
- [ ] `LANGSMITH_API_KEY` added to `.env` (gitignored) and to the Day-66 credential-scoping table
- [ ] `LANGSMITH_TRACING=false` in `.env.example` **with a comment saying why**
- [ ] Confirmed no new golden examples written today — dataset unchanged while tooling changes

## LG-18 — dataset identity

- [ ] `Example.id` is stable and human-readable (`T-9002`), not a UUID
- [ ] `version()` is a content hash of the **whole** set, canonicalised (`sort_keys`, tight separators)
- [ ] `input_hash` per example — catches an edited body under an unchanged ID
- [ ] Can say why every experiment must record the dataset version

## LG-18 — upload (one direction)

- [ ] Dataset name embeds the content version (`mandala-golden@<hash>`)
- [ ] Upload is **idempotent** — verified by running it twice
- [ ] `mandala_id` carried in metadata as the join key back to the repo
- [ ] Examples uploaded in **one bulk call**, not a loop
- [ ] Nothing ever pulled from the service into the repo

## LG-18 — experiments and comparison

- [ ] `run_experiment.py` grades **locally** with the Day-71/72 rubrics, then records results
- [ ] Results written to `tests/fixtures/experiments/<name>.json` and committed
- [ ] `compare.py` **refuses** (exits non-zero) on a dataset-version mismatch
- [ ] Output includes per-example `fixed` and `BROKEN` ID lists, not just an aggregate
- [ ] `sys.exit(1)` when anything broke — already CI-shaped for tomorrow
- [ ] Baseline pinned and committed as `triage-baseline-D73.json`
- [ ] Can give a concrete example of a swap that a +1 aggregate would hide

## Tests that must be able to fail

- [ ] `test_every_example_has_a_stable_human_readable_id`
- [ ] `test_example_ids_are_unique`
- [ ] `test_the_dataset_version_is_deterministic`
- [ ] `test_the_version_changes_when_an_example_changes` — **flip it:** hash only IDs, watch an
      edited body slip through
- [ ] `test_every_example_has_the_labels_the_outcome_layer_needs`
- [ ] `test_the_pinned_baseline_exists_and_records_its_dataset_version`
- [ ] `test_the_suite_runs_without_langsmith` — key deleted, evals still work
- [ ] `test_tracing_is_off_by_default`
- [ ] All of the above cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why must the repo, not the service, be the source of truth?
- [ ] Why refuse to compare experiments run against different dataset versions?
- [ ] What does a per-example diff show that an aggregate cannot?
- [ ] Why is `LANGSMITH_TRACING=true` a data-flow decision rather than a logging one?
- [ ] What exactly do you lose if the free tier disappears tomorrow?
- [ ] When should the baseline be re-pinned, and what should force you to notice?

## Budget & freshness

- [ ] Model request count logged in `docs/RATE_BUDGET.md` (declared: ~20)
- [ ] **New LangSmith row added** to `docs/RATE_BUDGET.md` with the real free-tier cap
- [ ] Confirmed whether *examples* count against the trace cap
- [ ] `create_examples()` signature verified against the installed package
- [ ] `list_datasets(dataset_name=...)` matching semantics confirmed
- [ ] Confirmed `langsmith` does **not** auto-instrument on import
- [ ] Data-residency / what-is-stored checked before any real ticket text is uploaded
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 73
```

- [ ] `triage-baseline-D73.json` committed — tomorrow's gate depends on it
- [ ] `.env.example` updated; no keys committed
- [ ] `./m done 73` succeeded
