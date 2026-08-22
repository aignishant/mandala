# Day 52 — CHECKLIST 🎯 Phase-7 gate

**IDs covered:** LG-23 🛠️ (the durable Mandala core)

## Demo command

```bash
bash days/day-52/lab/gate_demo.sh
```

Expected, in order: the nested shape, a run that pauses, a checkpoint table **while nothing is
running**, a resume from a different process, a forked re-run of one node, and a fully green suite.

## Setup

- [ ] `./m start 52` and `./m scaffold 52` run
- [ ] **No new dependencies** — the urge noted, not acted on
- [ ] `git status` clean before assembly
- [ ] `.mandala/graph` cleared — ten days of edits make every old checkpoint stale
- [ ] ADR number chosen without colliding with 001 / 002 / 003, and logged
- [ ] Files created (`graph/core.py`, `gate_demo.sh`, `timetravel_demo.py`, `core_run.py`, tests, ADR)

## The artifact

- [ ] `build_core()` returns an **uncompiled** graph — durability is the caller's choice
- [ ] Can name the three durability stories one definition now supports
- [ ] `NODE_POLICY` applied at wiring time via `_retry_from()`
- [ ] **`scrub` sits between `triage` and the lanes** — and can say why placement *is* the control
- [ ] Routing hangs off `scrub`, not `triage`
- [ ] `DRAFTING_LANES` named; `escalate` **skips** the gate, and can say why
- [ ] `research` wired as **one node** — the parent does not know it is a graph or that it fans out
- [ ] No `similar` computation or fan-out in the parent

## The four collisions (§3.4)

- [ ] **Collision 1** — grepped `graph/` for `ticket_body`; every reader confirmed upstream of `scrub`
- [ ] **Collision 2** — interrupts inside Research: decided, and the reasoning written down
- [ ] **Collision 3** — `stage` `Literal` reconciled; unreachable values deleted
- [ ] **Collision 4** — `test_every_node_has_a_policy` was **red first**, and the *policy* was fixed
- [ ] All four written into the ADR as findings, not fixed silently

## Evidence table (§4)

- [ ] Rows 1–18 all green
- [ ] Every cell carries a **filename or command**
- [ ] **Rows 6 and 7 examined as a pair** — the observation and its structural reason
- [ ] Row 5 verified from the ledger: the resume run cost **0**
- [ ] Row 15's ratio recorded (fork ≈4 vs. full ≈11)
- [ ] Row 17: `pytest -q` run over the **whole** suite, not just today's file

## The demo

- [ ] Recorded, reading from `gate_demo.sh`
- [ ] **Step 2 shown before step 3** — the shape before the behaviour
- [ ] **Step 4 paused on and narrated**: nothing running, state on disk
- [ ] Pointed at the row where `next` is `await_approval`
- [ ] Pointed at the row where `ticket_body` stops appearing
- [ ] Step 5 answered from a genuinely separate process
- [ ] Step 6 showed a forked branch, and the history surviving
- [ ] `body None` visible on the forked branch too

## Tests that must be able to fail

- [ ] `test_the_graph_compiles_without_a_checkpointer` — **flip it:** bake one in, see red
- [ ] `test_scrub_precedes_every_lane` — the **strong** version of Day 47's admittedly weak test
- [ ] `test_nothing_after_scrub_reads_the_raw_body`
- [ ] `test_only_drafting_lanes_reach_the_approval_gate`
- [ ] `test_escalate_skips_the_gate`
- [ ] `test_every_node_has_a_policy`
- [ ] `test_every_stage_value_is_reachable` — ported from Day 35
- [ ] `test_the_capstone_surface_is_one_function`
- [ ] `test_research_is_one_node_from_the_parents_view`
- [ ] `test_the_schema_is_still_day_4s`
- [ ] Every gate test runs with **no checkpointer, no store, no keys**

## The ADR

- [ ] Q1 — is LangGraph the spine? **Answered and dated, before the bake-off**
- [ ] Q2 — what the graph cost: wiring lines, request totals, concepts a newcomer must learn
- [ ] Q3 — what Mandala can do now that it could not on Day 42, specifically
- [ ] Q4 — **prediction** for what MCP does to `kb.search()` and `READ_TOOLS`
- [ ] Phase totals compared: Phase 5 (~110/6d), Phase 6 (~60/7d), Phase 7 (~100/10d)
- [ ] Reads like something a hiring panel could be handed (Principle 9)

## Standing gate freshness check (§7)

- [ ] Four LangChain/LangGraph packages re-verified against `docs/PINS.md`
- [ ] **MCP spec revision checked properly** — Phase 8 starts tomorrow and is built on 2026-07-28
- [ ] **`01_MASTER_PLAN_ADDENDUM_GAPS.md` question settled tonight** (carry it over, or repoint
      `CLAUDE.md`) — so Day 53 starts clean
- [ ] Result written in `docs/CHANGELOG_PLAN.md`, **nil report included if nothing moved**
- [ ] Minor/major drift → addendum **before** any pin changed

## Budget

- [ ] Actual counts logged in `docs/RATE_BUDGET.md` (declared: ~25, Groq)
- [ ] Phase-7 ten-day total computed and recorded

## Commit

```bash
./m check
./m done 52
```

- [ ] Phase-7 bake-off row complete: control, durability, HITL, testing, ops, velocity, lock-in,
      free-tier friendliness
- [ ] Day 53 §1 read **tonight**
- [ ] `./m done 52` succeeded — trackers updated automatically
