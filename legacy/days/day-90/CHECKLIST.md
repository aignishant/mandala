# Day 90 — CHECKLIST 🎯 Phase-14 gate · the last day

**IDs covered:** — (retrospective, the standing freshness habit, and the handoff gate)

## Demo command

```bash
docker run -it --rm python:3.12-slim bash        # clean machine, clone from the REMOTE
# ... timer running, follow only the README ...
uv run pytest -q
uv run python scripts/audit_writes.py
uv run python scripts/freshness_check.py --format=markdown
./m status                                        # 90/90
```

Expected: a machine that has never met this project runs a ticket end to end in **under 15 minutes**.

## The gate — the real stranger test

- [ ] **Not run on your own machine**
- [ ] Best case: a real person tried it while you watched **silently**
- [ ] Every "oh, you also need to—" urge **written down, not spoken**
- [ ] Container variant: cloned from the **remote**, not a mount of your working tree
- [ ] No `.env`, `.venv`, or cached browser binary reachable from the test environment
- [ ] Timings recorded: first offline test green / first end-to-end ticket
- [ ] Blockers listed
- [ ] README fixed and **re-run**
- [ ] **Second run under 15 minutes** — or the gate fails and today became a README day (legitimate)
- [ ] All of it recorded in `docs/adr/gate-phase-14.md`

## The retrospective (`docs/RETROSPECTIVE.md`)

- [ ] §1 What was built — numbers pulled from the repo, not memory
- [ ] IDs reported **honestly**, hands-on separated from 🅿️ literacy
- [ ] §2 What it cost — total requests, most expensive day, cache hit rate, **$0 paid spend**, hours
- [ ] **Deterministic-vs-model-dependent test ratio computed and stated**
- [ ] §3 What the ecosystem did — pins that moved, amendments written, **what specifically broke**
- [ ] Prediction recorded: what is stale in three months?
- [ ] Any un-amended material drift → `docs/04_MASTER_PLAN_ADDENDUM_*.md` **written today**
- [ ] §4 What I'd do differently — each item with **"and how I'd notice earlier next time"**
- [ ] §5 **Consolidated honest limits** — four gate ADRs + five known-limit tests, one list, with days
- [ ] §6 What Mandala is not — three plain sentences

## The standing habit

- [ ] `scripts/freshness_check.py` written — **a real script**, not a prompt
- [ ] `.github/workflows/freshness.yml` with a Friday `schedule:` cron
- [ ] `permissions:` limited to `contents: read` + `issues: write`
- [ ] **Opens an issue** rather than failing a badge or emailing
- [ ] `workflow_dispatch` included for manual runs
- [ ] **Does not auto-update pins** — detection automatic, judgement human (Principle 14 survives)
- [ ] Noted: scheduled workflows are disabled after 60 days of repo inactivity — recorded in the
      retrospective as a real risk to the habit
- [ ] Triggered once manually and confirmed the issue appears

## Closing the tracker

- [ ] Full suite green
- [ ] `audit_writes.py` exit 0
- [ ] Permission table current
- [ ] **DEV ONLY items from Day 88 removed or converted into labelled dev affordances** — nothing
      left ambiguous
- [ ] `docs/CURRICULUM_INDEX.md` reads 90/90, updated by `./m done` only
- [ ] `docs/TRACEABILITY.md` regenerated
- [ ] Final `CHANGELOG_PLAN.md` entry written
- [ ] Final `/freshness` sweep logged, nil reports included
- [ ] `git tag -a phase-14-complete` and `git tag -a mandala-v1.0`
- [ ] **`gate-phase-14.md` NOT signed today — cold read tomorrow**

## Understanding check — answer out loud

- [ ] Why can the stranger test not be run on your own machine?
- [ ] Why does the freshness job open an issue rather than fail a build?
- [ ] Why must it never auto-update a pin?
- [ ] What is the single most transferable engineering result of the 90 days?
- [ ] Name three things Mandala is not
- [ ] What would kill the standing habit, and what did you do about it?

## Week 91 — pick one, and write it down

- [ ] **Run the freshness queue for a month** — four Fridays, four decisions, visible in git history
- [ ] **Try to earn one autonomy level** — 40 decisions / 28 days / zero rejections; either answer
      is a good outcome
- [ ] **Replace one organ** — swap the CrewAI researcher for a LangGraph subgraph, measure the delta
      on the existing eval suite, write ADR-004
- [ ] Committed to one, with a date
- [ ] **Did not start a new 90-day plan**

## Budget

- [ ] Final day logged (declared: ~0–5)
- [ ] **90-day total computed** and placed in the retrospective beside the `$0` figure

## Commit

```bash
./m check
./m done 90
```

- [ ] Retrospective, gate ADR, freshness workflow and script committed
- [ ] Tags pushed
- [ ] `./m done 90` succeeded — **90/90**
- [ ] Cold read scheduled for tomorrow
- [ ] Friday's freshness issue expected
