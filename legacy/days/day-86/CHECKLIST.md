# Day 86 — CHECKLIST

**IDs covered:** LG-20 🛠️ (LangGraph Server the $0 way — runs, threads, crons, webhooks),
LG-21 🛠️ (scaling stateful graphs: stateless API + checkpointer-backed workers)

## Demo command

```bash
uv run langgraph dev --port 2024 &
uv run python days/day-86/lab/two_workers_one_thread.py T-9201
uv run pytest tests/test_worker.py -v                    # 0 requests
# in two terminals:
MANDALA_CHECKPOINT_DB=.state/shared/mandala.sqlite uv run python -m mandala.worker.runner
```

Expected: a run submitted through the server suspends at the gate; a second worker finishes a thread
its predecessor started; **no node executes twice**.

## Setup

- [ ] `./m start 86` and `./m scaffold 86` run
- [ ] `langgraph` CLI availability checked — bundled or separate package?
- [ ] If a new package was needed: **verified, pinned, and a Day-86 row added to the `PINS.md` ledger**
- [ ] `.state/shared/` created as the shared checkpoint location
- [ ] Yesterday's `statefulness_hunt.md` reopened — the `.state/` row is due today

## LG-20 — graph as an API

- [ ] `langgraph.json` written against the **verified** schema
- [ ] `build_for_server` is a new zero-arg entry point that supplies **no checkpointer**
- [ ] Dev server confirmed **not** to print secrets at startup
- [ ] Dev server confirmed **not** to enable LangSmith tracing by default (Day 75's decision stands)
- [ ] Explored: threads, runs, crons, webhooks — ten minutes each
- [ ] Table filled in: which concept is yours, which is theirs, and why
- [ ] **Interrupt tested through the server**, resumed via its API rather than the Day-82 CLI
- [ ] Any place where approval logic assumed a process — found and noted

## Crons and webhooks (§3.1)

- [ ] `cron_and_webhook.md` written
- [ ] The cron you would schedule named (weekly freshness — Principle 13)
- [ ] Noted: **a cron in a dev server nobody runs is not a cron** — carried to Day 90
- [ ] The webhook you would use named (approval callback)
- [ ] **Security consequence written down**: a webhook is a network path that resumes a graph, and
      Day 82's hash+run binding is what makes it survivable

## LG-21 — workers

- [ ] `MANDALA_CHECKPOINT_DB` read with **`os.environ[...]`, no default** — and can say why
- [ ] Worker holds no state between jobs; graph built per job
- [ ] Resume uses `invoke(None, ...)` (or the verified correct idiom) — **not** the original input
- [ ] Jobs are **leased**, not locked
- [ ] Failure path: `release(job)` then **re-raise** — no silent retry
- [ ] `worker` recorded on the span
- [ ] No `MemorySaver` anywhere in `src/`

## The two-workers-one-thread drill (§4.1)

- [ ] Two workers run against the **same shared** checkpoint DB
- [ ] First worker killed mid-node; second finished the thread
- [ ] Verified the second worker **resumed** rather than re-ran the completed node
- [ ] Both workers pointed at one thread simultaneously — SQLite's contention behaviour observed
- [ ] **Trace checked: no node ran twice; no write ran twice**
- [ ] If a write ran twice: **stopped**, fixed, and noted — Day 88's gate cannot pass otherwise
- [ ] Postgres justification written from the contention result

## Tests that must be able to fail

- [ ] `test_the_checkpoint_path_has_no_default` — **flip it:** add a default, workers use own files
- [ ] `test_the_worker_holds_no_state_between_jobs`
- [ ] `test_a_failed_job_is_released_and_reraised`
- [ ] `test_jobs_are_leased_not_locked`
- [ ] `test_an_expired_lease_becomes_claimable`
- [ ] `test_a_live_lease_is_not_stealable`
- [ ] `test_the_server_entry_point_does_not_supply_its_own_checkpointer`
- [ ] `test_langgraph_json_points_at_the_server_entry_point`
- [ ] `test_no_memory_saver_anywhere_outside_tests`
- [ ] `test_resume_passes_none_as_input`
- [ ] All cost **0 model requests**

## Understanding check — answer out loud

- [ ] Where did the state go, and why does that make workers interchangeable?
- [ ] Lock vs lease — what does a dead worker cost you under each?
- [ ] Why must a failed job re-raise rather than retry quietly?
- [ ] What happens if a resume re-supplies the original input?
- [ ] Why is SQLite-on-a-volume acceptable here, and what would force Postgres?
- [ ] Why does a webhook that resumes a graph not terrify you, given Day 82?

## Budget & freshness

- [ ] Request count logged in `docs/RATE_BUDGET.md` (declared: ~12)
- [ ] **Unexpectedly high count treated as a correctness signal** — checked for double-execution
- [ ] `langgraph.json` schema verified against the installed CLI
- [ ] Resume idiom verified: `invoke(None, ...)` vs `Command(resume=...)` — **not the same thing**
- [ ] SQLite concurrent-writer behaviour recorded
- [ ] Postgres checkpointer package named correctly for the literacy note
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 86
```

- [ ] Drill write-up and `cron_and_webhook.md` committed
- [ ] `langgraph.json` committed; `.env` still ignored
- [ ] `./m done 86` succeeded
