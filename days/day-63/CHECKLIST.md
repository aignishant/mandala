# Day 63 — CHECKLIST

**IDs covered:** none — the **published scorecard** is the artifact

## Demo command

```bash
uv run pytest tests/test_bakeoff.py -v      # all four implementations still green
cat days/day-63/lab/SCORECARD.md
```

**No model requests today.** The deliverable is a document.

## Setup

- [ ] `./m start 63` and `./m scaffold 63` run
- [ ] All four implementations confirmed **still green** before scoring
- [ ] All four `log.md` files complete — **no blank cells**
- [ ] `prediction.md` confirmed untouched since Day 59 (`git log`)
- [ ] Framework versions confirmed against `docs/PINS.md`
- [ ] Everything from Day 62's collection step in one folder

## Weights — declared BEFORE opening any log

- [ ] `weights.md` written **first**
- [ ] Eight dimensions, weights totalling **100**
- [ ] Every weight justified **for Mandala specifically**
- [ ] "The system I am weighting for" paragraph written
- [ ] **"What would change these weights" written** — the credibility test
- [ ] Weights **not changed** after seeing any score

## Dimensions pinned

- [ ] One operational sentence per dimension
- [ ] Evidence source named per dimension
- [ ] **Testing scored by counting** test suites that run without keys — not by feel
- [ ] **Free-tier friendliness scored from the ledger** — nine real numbers

## Scoring

- [ ] 1–5 per framework per dimension
- [ ] Every score carries a one-line evidence pointer
- [ ] **Every score marked M (measurement) or J (judgement)**
- [ ] Any dimension that is entirely J — **flagged as such in its header**
- [ ] The eight already-measured rows copied from the logs, not re-derived

## `SCORECARD.md`

- [ ] "Scored for" line states the system
- [ ] Method stated: frozen spec, shared MCP layer, agnostic tests, two hours, weights first
- [ ] Totals table
- [ ] Eight per-dimension tables with evidence and M/J
- [ ] "Where each framework wins outright" — **and any framework with none said plainly**
- [ ] **Predictions vs. results table**, with a count of wrong predictions
- [ ] If zero were wrong: explained why the reader should still trust it
- [ ] Five surprises, **in the words written at the time**
- [ ] **"What this does NOT measure"** — specific about fixtures, scale, versions, out-of-scope
- [ ] "What I would choose, and for what" — a sentence per framework naming a system

## AG-29 — the final draft

- [ ] `who_owns_the_loop.md` draft 5 written, table complete with costs/buys/best-for
- [ ] Final interview paragraph written
- [ ] **Diffed against draft 1**, and what changed written down
- [ ] All five drafts kept — flagged for Day 89's portfolio

## The self-check (§5)

- [ ] No framework won every row — **or the missing row was found**
- [ ] Weights unchanged since declaration
- [ ] Judgement-only dimensions flagged
- [ ] Prediction count honest
- [ ] Conclusion written from the per-dimension tables, **not from the totals**
- [ ] A stranger could reproduce at least one score from the evidence given
- [ ] **"Does not measure" section is not shorter than the totals section**

## Understanding check — answer out loud

- [ ] Why must weights be declared before scores?
- [ ] Why is a clean sweep a warning sign?
- [ ] What does the M/J column protect you from?
- [ ] Which dimension has the hardest numbers, and why does nobody else's bake-off have it?
- [ ] Why did the protocol phase cost a quarter of the framework phases?
- [ ] What would make you re-weight this scorecard tomorrow?

## Budget

- [ ] Logged in `docs/RATE_BUDGET.md`: **0 requests**
- [ ] Standing note added to `RATE_BUDGET.md` §2: decision days are free, behaviour days are
      expensive — schedule accordingly

## Commit

```bash
./m check
./m done 63
```

- [ ] **Did NOT re-read the scorecard after finishing** — tomorrow's ADR needs a cold read
- [ ] `./m done 63` succeeded — trackers updated automatically
