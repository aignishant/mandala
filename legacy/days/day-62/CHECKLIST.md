# Day 62 — CHECKLIST

**IDs covered:** none — the slice is the artifact (Phase 9 build day 4 of 4)

## Demo command

```bash
uv run python days/day-59/lab/run_slice.py graph T-9002
uv run pytest tests/test_bakeoff.py -v
```

## Setup

- [ ] `./m start 62` and `./m scaffold 62` run
- [ ] `SLICE.md` unchanged
- [ ] `ticket-db` running; the LangGraph mount re-verified
- [ ] `langgraph==1.2.11` pin confirmed
- [ ] **`build_core()` confirmed green before the timer** — do not measure your debugging
- [ ] Model-call counting via the `notes` turn-count habit still in place
- [ ] Files created (`bakeoff/graph_slice.py`, `days/day-62/lab/log.md`)

## Discipline — the trap of the day

- [ ] Discipline note written at the **top of the module**, not just in your head
- [ ] **Persistence NOT built** (one line, out of scope)
- [ ] **Approvals NOT built** (one line, out of scope)
- [ ] **Streaming NOT built** (out of scope)
- [ ] **Retries NOT built** (out of scope)
- [ ] Temptations recorded in the fairness ledger
- [ ] **Stopped when the timer rang** — including if it rang early
- [ ] Spare time **not** spent polishing

## The build

- [ ] `run_slice(ticket_id) -> SliceResult` — same contract
- [ ] Rule 3 as a conditional edge — **zero model turns**
- [ ] Cross-day routing arithmetic finished: 3 of 4 cost zero, 1 costs one
- [ ] Rule 6 by **subgraph schema** (absence), not the scrub node (deletion)
- [ ] Can state the difference precisely, and why absence is stronger than deletion
- [ ] Recorded that this was the **only framework offering a choice of security mechanism** — and
      formed a view on whether that is expressive power or unnecessary optionality
- [ ] **Confidence-time for rule 6 recorded**, and expected to be the lowest of the four
- [ ] Tools from MCP
- [ ] `model_calls` measured

## The fairness ledger (§2.4) — written while the timer ran

- [ ] Foundation started from, recorded — and compared with Day 59's
- [ ] Days since last using this framework vs. the SDK
- [ ] Out-of-scope temptations listed
- [ ] Timer honoured
- [ ] **Lines of new code, excluding reuse** — the number that flatters LangGraph least

## The three sinks (§2.3)

- [ ] Minutes to first passing test recorded — **expected to be the worst of the four**
- [ ] Subgraph mapping written; it is the security boundary
- [ ] Model-call counting noted as **easy** — observability being cheap is a real property

## The completed comparison table (§3)

- [ ] **All thirteen rows filled for all four frameworks** — no blanks
- [ ] `surprises.md` written into during the build

## AG-29 — draft 4 of 4

- [ ] `who_owns_the_loop.md` LangGraph row filled; the table is complete
- [ ] Interview paragraph rewritten as **draft 4** — drafts 1–3 kept

## Understanding check — answer out loud

- [ ] Why is the out-of-scope list more binding today than on any other day?
- [ ] What is the difference between deletion and absence, as security mechanisms?
- [ ] Why is "lines of new code excluding reuse" the fairest velocity number?
- [ ] What would it mean if this were *not* the cheapest implementation to run?
- [ ] Name the two confounds that make you want this framework to win.

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~12, Groq)
- [ ] **Expected to be the lowest of the four** — or investigated if not
- [ ] Phase-9 four-day total computed, alongside Phases 5, 6, 7, 8
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 62
```

- [ ] **Everything collected into one folder tonight**: four `log.md` files, `surprises.md`,
      `prediction.md`, four drafts of `who_owns_the_loop.md`, and the completed §3 table
- [ ] `./m done 62` succeeded — trackers updated automatically
