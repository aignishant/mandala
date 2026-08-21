# Day 59 — CHECKLIST

**IDs covered:** AG-29 🅿️ (the framework-choice question) · **the bake-off rules are set today**

## Demo command

```bash
# terminal 1: the shared tool layer for all four days
uv run python -m mandala_mcp.http_server
# terminal 2
uv run python days/day-59/lab/run_slice.py sdk T-9002
uv run pytest tests/test_bakeoff.py -v
```

## Setup

- [ ] `./m start 59` and `./m scaffold 59` run
- [ ] No new packages
- [ ] `ticket-db` MCP server running **before the timer starts**
- [ ] Model-call counting method for the SDK **found before the timer starts**
- [ ] Files created (`SLICE.md`, `tests/test_bakeoff.py`, `bakeoff/sdk_slice.py`, `log.md`,
      `prediction.md`, `surprises.md`, `who_owns_the_loop.md`)

## The rules — binding for four days

- [ ] `SLICE.md` written and **frozen**
- [ ] Can say why rule 1 (MCP) makes the comparison honest
- [ ] Can say why rule 3 (a branch) is what makes the frameworks differ at all
- [ ] Can say why rule 6 (drafter never sees the body) is the interesting requirement
- [ ] **Out-of-scope list written** — persistence, approval, streaming, retries
- [ ] Can say why an out-of-scope list matters as much as the requirements

## The acceptance tests — written BEFORE any implementation

- [ ] `SliceResult` contract frozen
- [ ] `saw_raw_body` and `model_calls` in the contract — **run properties, not outputs**
- [ ] Every test asserts against `SliceResult`, never a framework object
- [ ] Nine tests written and passing against a recorded result
- [ ] Noted that four of them are tests you have already written three times

## The timebox

- [ ] Two hours, wall clock, **hard stop** — and it was respected
- [ ] `log.md` filled **while the timer ran**, not afterwards
- [ ] "Passed at" times recorded per requirement, not just a total
- [ ] Unfinished requirements recorded as **data**, not hidden
- [ ] **"Times I reached for an escape hatch" counted**

## Guarding the outcome (§2.4)

- [ ] `prediction.md` written **before** building — which framework wins each row, and by how much
- [ ] Build order follows the plan (expected winner last)
- [ ] `surprises.md` started, and written into during the build

## Today's build — the Agents SDK

- [ ] `run_slice(ticket_id) -> SliceResult` is the only export
- [ ] **Built the SDK's way** — rule 3 as a handoff, not an if-statement around the runner
- [ ] Can say why forcing an if-statement would make the comparison meaningless
- [ ] Rule 6 solved, and **which of the three options** recorded, with minutes
- [ ] If a guardrail was used: recorded as **detection, not prevention** (Day 29's finding)
- [ ] Tools came from MCP, not local fixtures
- [ ] `model_calls` measured honestly for one run
- [ ] Lines of code counted

## AG-29 — draft 1 of 4

- [ ] `who_owns_the_loop.md` table started, SDK row filled
- [ ] Today's evidence written in **minutes and lines**, not adjectives
- [ ] The interview paragraph written — **draft 1, kept**

## Understanding check — answer out loud

- [ ] Name the five confounds a naive framework comparison has, and how each is removed.
- [ ] Why must the acceptance tests be written before the implementations?
- [ ] Why is an unfinished implementation data rather than failure?
- [ ] What does "the model owns the loop" cost you on rule 6?
- [ ] Why is a guardrail on the draft not the same as preventing the exposure?
- [ ] Why would zero wrong predictions be a bad sign?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~15, Groq)
- [ ] Noted that four build days together cost more than a full OpenRouter day
- [ ] `openai-agents==0.22.0` still pinned and installed
- [ ] Day 55's SDK MCP mount re-verified after Phase 8
- [ ] `require_approval` confirmed not to block an unattended run
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 59
```

- [ ] `SLICE.md` and `tests/test_bakeoff.py` committed **before** Day 60 starts — they are frozen now
- [ ] `./m done 59` succeeded — trackers updated automatically
