# Day 61 — CHECKLIST

**IDs covered:** none — the slice is the artifact (Phase 9 build day 3 of 4)

## Demo command

```bash
uv run python days/day-59/lab/run_slice.py langchain T-9002
uv run pytest tests/test_bakeoff.py -v
```

## Setup

- [ ] `./m start 61` and `./m scaffold 61` run
- [ ] `SLICE.md` unchanged
- [ ] `ticket-db` running; `langchain_mcp_adapters` re-verified
- [ ] `langchain` / `langchain-core` pins confirmed
- [ ] **Model-call counting across three agents wired before the timer**
- [ ] Checked whether `MIDDLEWARE` adds model calls of its own
- [ ] Files created (`bakeoff/lc_slice.py`, `days/day-61/lab/log.md`)

## The structural question

- [ ] Can name all three places the branch could live
- [ ] **Built option 1** (plain Python), and can say why option 3 was declined
- [ ] The decline **recorded as a finding in the module docstring**, not hidden
- [ ] Lock-in row phrased **precisely**, not as advocacy

## The build

- [ ] `run_slice(ticket_id) -> SliceResult` — same contract
- [ ] Rule 3 as a plain `if` — **zero model turns**
- [ ] Rule 6 by **fresh conversations**, and the mechanism understood as an absence by construction
- [ ] `draft_agent` built with **no tools** — and can say why that is part of the boundary
- [ ] **Minutes until you trusted rule 6 recorded**, and compared with Days 59 and 60
- [ ] If it was the cheapest of the three so far: **said so**, despite complicating the story
- [ ] Tools from MCP
- [ ] `model_calls` measured, not estimated

## The three sinks (§2.3)

- [ ] Model wiring: **zero minutes recorded as a result**
- [ ] Middleware attached to **all three** agents — and noticed you had to remember three times
- [ ] Output parsing lines counted; compared with yesterday's crew parser

## The counting question (§2.4)

- [ ] Three agents' calls summed correctly
- [ ] **Answered: could a hidden call have inflated my count?**
- [ ] Recorded as a free-tier scorecard row

## The timebox

- [ ] Two hours, hard stop, respected
- [ ] `log.md` filled while the timer ran
- [ ] "Passed at" times per requirement
- [ ] Escape hatches counted
- [ ] Requirements passing at the buzzer recorded

## Comparison table (§3)

- [ ] All eight rows filled for three frameworks
- [ ] `surprises.md` written into during the build

## AG-29 — draft 3 of 4

- [ ] `who_owns_the_loop.md` LangChain row filled
- [ ] Interview paragraph rewritten as **draft 3** — drafts 1 and 2 kept

## Understanding check — answer out loud

- [ ] Where does a branch live when the framework's API is a loop?
- [ ] Why would taking the framework's own answer have invalidated today?
- [ ] Why is an empty tool list a security control?
- [ ] Why might the simplest framework express the security rule most cheaply?
- [ ] What can silently inflate your request count here?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~14, Groq)
- [ ] Landed between Days 60 and 62 as expected — **or investigated why not**
- [ ] `response_format` extra-turn question (Day 38 §4.1) answered and logged
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 61
```

- [ ] `./m done 61` succeeded — trackers updated automatically
