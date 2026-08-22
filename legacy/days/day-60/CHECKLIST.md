# Day 60 — CHECKLIST

**IDs covered:** none — the slice is the artifact (Phase 9 build day 2 of 4)

## Demo command

```bash
uv run python days/day-59/lab/run_slice.py crew T-9002
uv run pytest tests/test_bakeoff.py -v
```

## Setup

- [ ] `./m start 60` and `./m scaffold 60` run
- [ ] `SLICE.md` **unchanged** — and the impulse to change it recorded in `surprises.md` if it arose
- [ ] `ticket-db` MCP server running before the timer
- [ ] **Model-call counting wired before the timer** (Day 28's callbacks)
- [ ] `crewai` / `crewai-tools` pins confirmed
- [ ] Files created (`bakeoff/crew_slice.py`, `days/day-60/lab/log.md`)

## The choice only CrewAI poses

- [ ] Crews or Flows — **decided, and the reason written down**
- [ ] **Minutes spent deciding recorded** — the cost of optionality
- [ ] Built the production shape: Flow skeleton, Crew in the research branch (CR-17)
- [ ] Can say why a pure Crew would be building the framework's weaker half on purpose
- [ ] Recorded "this framework made me choose first" as a scorecard row, with a verdict

## The build

- [ ] `run_slice(ticket_id) -> SliceResult` — same contract, no changes
- [ ] Rule 3 as a `@router` — **zero model turns**, recorded against yesterday's one
- [ ] Rule 6 by deletion, and the ordering consequence stated
- [ ] **Minutes until you *trusted* rule 6 recorded** — not minutes to write `drop_body()`
- [ ] Tools from MCP, not local fixtures
- [ ] Output parser written, and **its lines counted**
- [ ] `model_calls` measured, not estimated
- [ ] Reused `mandala_mini` rather than rebuilding it

## The timebox

- [ ] Two hours, hard stop, respected
- [ ] `log.md` filled **while the timer ran**
- [ ] "Passed at" times per requirement
- [ ] Escape hatches counted
- [ ] Requirements passing at the buzzer recorded
- [ ] Two extra lines filled: the Crews/Flows choice, and minutes spent deciding

## The three predictable sinks (§2.3)

- [ ] MCP adapter lifecycle — time spent recorded **at minute twenty**, not at the buzzer
- [ ] Crew-output parsing — lines counted
- [ ] Model-call counting — solved before the timer, not during it

## Comparison table (§3)

- [ ] All six rows filled for both SDK and CrewAI
- [ ] `surprises.md` written into **during** the build
- [ ] Any impulse to change the spec recorded

## AG-29 — draft 2 of 4

- [ ] `who_owns_the_loop.md` CrewAI row filled
- [ ] Interview paragraph rewritten as **draft 2** — and draft 1 kept

## Understanding check — answer out loud

- [ ] Why is "the framework made me choose first" a scorecard row rather than a compliment?
- [ ] What is the per-ticket cost difference between a handoff and a `@router`?
- [ ] Why does global flow state make ordering a security property?
- [ ] Why record confidence-time rather than write-time for rule 6?
- [ ] What does "typed in, prose out" cost you, in lines?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~18, Groq)
- [ ] Noted whether you ran out of **quota** before running out of **time**
- [ ] Recorded "what does one slice cost in this framework" as a scorecard row
- [ ] `MCPServerAdapter` re-verified after Phase 8
- [ ] `@router` return-value matching confirmed for 1.15.17
- [ ] Adapter context-manager lifecycle inside a flow step — **answered** (Day 55's open question)
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 60
```

- [ ] `./m done 60` succeeded — trackers updated automatically
