# Day 35 — CHECKLIST 🎯 Phase-5 gate

**IDs covered:** CR-22 🛠️ (Mandala-flow, the gate artifact)

## Demo command

```bash
bash days/day-35/lab/gate_demo.sh
```

Expected: a run that pauses, a store with rows **while nothing is running**, a human decision in a
separate process, a resume whose trail begins before the pause, and green tests — in that order.

## Setup

- [ ] `./m start 35` and `./m scaffold 35` run
- [ ] **No new dependencies** — and the urge to add one was noted, not acted on
- [ ] `git status` clean before assembly began
- [ ] Store cleared (`.mandala/flows`, `.mandala/approvals`) — staleness policy applied by hand
- [ ] Checkpoint sweep written as a real function, or explicitly deferred with a note
- [ ] ADR number chosen without colliding with 001 / 002 / 003, and the choice logged

## The artifact

- [ ] `mandala_flow.py` written — **assembly only**, no new behaviour
- [ ] `--attempt` is required, and can say why (Day 32 §4.2)
- [ ] `--resume` is an explicit opt-in (Day 32 §4.3)
- [ ] `FlowPaused` exits **0** — a pause is a success
- [ ] The pause branch prints the store size, so the evidence is on camera
- [ ] `gate_demo.sh` written with `set -euo pipefail` and a fresh attempt id per take

## The three collisions (§3.3)

- [ ] **Collision 1** — lifecycle vocabulary: one name chosen for "a human has it", `Literal` fixed
- [ ] **Collision 2** — `MAX_STEPS` scope decided (per attempt or per run) and **written in the source**
- [ ] **Collision 3** — approvals keyed on the run id, not the ticket id; `decision_key()` added
- [ ] All three written into the ADR as findings, not fixed silently

## Evidence table (§4)

- [ ] Row 1 — routes without a model
- [ ] Row 2 — every route has a budget
- [ ] Row 3 — `organ:` in the trail
- [ ] Row 4 — crew built in exactly one place
- [ ] Row 5 — raw text never reaches the research step
- [ ] Row 6 — raw text never reaches disk
- [ ] Row 7 — state survives process death (demo step 3)
- [ ] Row 8 — resume continues rather than restarts
- [ ] Row 9 — resume is explicit
- [ ] Row 10 — nothing sends without a human decision
- [ ] Row 11 — one function decides authorisation
- [ ] Row 12 — the reviewer's edit is what gets sent
- [ ] Row 13 — decision record immutable and attributed
- [ ] Row 14 — resume cost vs. first-run cost, **both numbers logged**
- [ ] Row 15 — pins re-verified, drift logged or nil-reported
- [ ] Every cell filled with a **filename or command**, not a feeling
- [ ] Rows 5 and 6 examined as a pair — same property, two layers

## Tests that must be able to fail

- [ ] `test_every_stage_value_is_reachable`
- [ ] `test_the_lifecycle_vocabulary_has_no_synonyms`
- [ ] `test_the_step_budget_scope_is_documented` — and its weakness understood
- [ ] `test_an_approval_is_bound_to_an_attempt` — **flip it:** key on ticket id, see red
- [ ] `test_the_gate_artifact_adds_no_logic`
- [ ] `test_every_route_survived_the_phase`
- [ ] `test_the_never_persist_set_is_not_empty`
- [ ] `test_a_decision_still_requires_a_reviewer`
- [ ] All Phase-5 tests green **before** the first recording
- [ ] Can say which claims a test carries and which need the demo

## The demo

- [ ] Recorded, reading from `gate_demo.sh`
- [ ] **Step 3 paused on and narrated** — nothing running, state still exists
- [ ] The human decision made in a genuinely separate process
- [ ] The resumed trail visibly begins before the pause
- [ ] `body None` visible on screen after the round trip through disk

## The ADR

- [ ] Written today, while the collisions were fresh
- [ ] Q1 — when I would choose Flows, **and when I would not**
- [ ] Q2 — what Flows gave me that Crews could not, ranked
- [ ] Q3 — where the DSL boundary belongs (carried from yesterday's `compare.md`)
- [ ] Q4 — **predictions** for LangGraph Days 43 / 47 / 50, written before seeing them
- [ ] Reads like something a hiring panel could be handed (Principle 9)

## Standing gate freshness check (§7)

- [ ] `crewai` / `crewai-tools` versions re-verified against `docs/PINS.md`
- [ ] Declarative-flow surface specifically checked for movement
- [ ] MCP spec revision checked — even though Phase 5 does not use it
- [ ] Result written in `docs/CHANGELOG_PLAN.md`, **including a nil report if nothing moved**
- [ ] Minor/major drift → addendum written **before** any pin changed

## Budget

- [ ] Actual counts logged in `docs/RATE_BUDGET.md` (declared: ~25, Groq)
- [ ] First-run and resume costs logged **separately**, with the ratio

## Commit

```bash
./m check
./m done 35
```

- [ ] Phase-5 row of the bake-off complete: control, durability, HITL, testing, ops, velocity,
      lock-in, free-tier friendliness
- [ ] Day 36 §1 read, and the **unsigned LangChain amendment** in
      `docs/03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md` handled before Phase 6 starts
- [ ] `./m done 35` succeeded — trackers updated automatically
