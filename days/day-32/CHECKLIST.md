# Day 32 — CHECKLIST

**IDs covered:** CR-18 🛠️ (persistence, checkpoints, resume gating) · **AG-27 applied**

## Demo command

```bash
uv run python days/day-32/lab/kill_and_resume.py T-9002 crash    # ~20 requests, dies on purpose
uv run python days/day-32/lab/kill_and_resume.py T-9002 resume   # ~0 requests
uv run python days/day-32/lab/inspect_checkpoints.py             # 0 requests
uv run pytest tests/test_persistence.py -v
```

Expected: the resume prints a trail containing the **pre-crash** steps, `stage` past `classified`,
`body None`, and costs a fraction of the crash run.

## Setup

- [ ] `./m start 32` and `./m scaffold 32` run
- [ ] No new packages — `@persist` ships inside `crewai==1.15.17`
- [ ] `grep -n '^\.mandala/$' .gitignore` printed **SAFE** *before* the first persisted run
- [ ] Any other store path the framework created is also git-ignored, same commit
- [ ] Files created (`flows/persistence.py`, `tests/test_persistence.py`, two lab files)

## CR-18 — `@persist`

- [ ] Can say why **class-level** beats method-level here, in cost terms
- [ ] `@persist()` form confirmed for 1.15.17 (factory or plain decorator)
- [ ] `ensure_store()` called from `__init__`, **not** at import time — and can say why
- [ ] `super().__init__()` called **after** the store exists
- [ ] First run performed, and the store's actual location found on disk

## What reaches disk

- [ ] `persistence.py` written — `CHECKPOINT_DIR`, `NEVER_PERSIST`, `MAX_CHECKPOINT_AGE_HOURS`
- [ ] Can name the exact window `scrub()` exists for (crash between `load` and `drop_body`)
- [ ] `scrub()` uses `model_copy` — **does not mutate live state**
- [ ] `inspect_checkpoints.py` run against a real checkpoint
- [ ] The `NEVER_PERSIST` scan printed **no** `!!` line
- [ ] Understood that persistence turns milliseconds of exposure into a file (Principle 6)

## Resume

- [ ] `kill_and_resume.py ... crash` run **once**, dying at a named step
- [ ] `kill_and_resume.py ... resume` run, passing **only** the id
- [ ] Trail shows pre-crash steps followed by resumed steps — not a restart from `load`
- [ ] `body` is `None` **after** a round trip through disk
- [ ] Can state the identity rule: **a run id names an attempt, not a subject**
- [ ] Run id switched off the bare ticket id (or the risk written down and accepted)
- [ ] **Resume-gating behaviour of 1.15.17 established** and written into §4.3
- [ ] If it resumes by default, `resume_allowed()` written with the keyword-only flag
- [ ] Can say why "loud failure beats quiet wrong answer" is the same call as Day 1 and Day 31

## Tests that must be able to fail

- [ ] `test_scrub_removes_the_body` — **flip it:** remove the scrub, see red
- [ ] `test_scrub_keeps_everything_else` — the negative-space sibling
- [ ] `test_scrub_does_not_mutate_the_live_state`
- [ ] `test_every_never_persist_field_exists_on_the_model` — the typo test
- [ ] `test_the_checkpoint_dir_is_git_ignored`
- [ ] `test_ensure_store_is_idempotent`
- [ ] `test_staleness_policy_is_hours_not_days`
- [ ] `test_fresh_checkpoints_resume[0.5|23.9]`
- [ ] `test_resume_requires_an_explicit_request` — **flip it:** default it to `True`, see red
- [ ] Understood what is deliberately **not** tested here (the framework's own round-trip)

## Understanding check — answer out loud

- [ ] Why is durability a *budget* feature on a free tier, not just an ops feature?
- [ ] What is in a checkpoint, and who can read it?
- [ ] Why is resuming by default dangerous, and what exactly goes stale?
- [ ] Why must `scrub` copy rather than mutate?
- [ ] Why does `resume_allowed` return a bool while `organs.py` raises?
- [ ] What does a checkpoint prove, and what does it not prove?

## Budget & freshness

- [ ] **Both** numbers logged in `docs/RATE_BUDGET.md`: crash run and resume run
- [ ] The ratio between them noted — that ratio is today's result
- [ ] `crewai.flow.persistence` import path confirmed
- [ ] Default store location confirmed, and git-ignored
- [ ] Whether class-level `@persist` checkpoints after **every** step — confirmed
- [ ] `kickoff` id-key name confirmed (`"id"` is only an assumption)
- [ ] Store schema noted as documented or internal — Day 35 depends on the answer
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 32
```

- [ ] Bake-off row started: **durability granularity** — CrewAI per step (today) vs. LangGraph per
      super-step (Day 47) vs. Temporal per activity (Day 20)
- [ ] `./m done 32` succeeded — trackers updated automatically
