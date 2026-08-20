# Day 29 — CHECKLIST

**IDs covered:** CR-13 🛠️ (Mandala-mini) · **PHASE-4 GATE 🎯**

## Demo command

```bash
uv run python days/day-29/lab/gate_run.py T-1004
uv run python days/day-29/lab/gate_run.py T-1006      # the vague ticket
uv run python days/day-29/lab/collision_checks.py
uv run crewai test -n 3 -m openrouter/<free-model>
uv run python days/day-14/lab/span_tree.py
```

## Setup

- [ ] `./m start 29` and `./m scaffold 29` run
- [ ] **No new packages**
- [ ] OpenRouter quota checked **before** starting — the scorer needs a slice
- [ ] `pytest -q -m "not docker and not temporal"` green **before** building
- [ ] Day 27's guardrails still block; Day 14's viewer still reads
- [ ] Files created (`crew/mandala_mini.py`, two lab files, one test file)
- [ ] **`analyst` role added to `mandala.permissions`** with an honest `blast_radius`

## The artifact

- [ ] Three agents, and can justify each one's row in the §3.1 table
- [ ] The Writer holds **no read tool** — separation is an omission, not a request
- [ ] `mandala_mini.py` **composes only** — no new logic written there
- [ ] Every feature flag defaults to its gate-required value
- [ ] Data flow declared (`context` chain), not inferred from order
- [ ] Per-agent `max_iter` budgets set deliberately (5 / 8 / 4)
- [ ] Ran on **three different kinds of ticket**, including T-1006
- [ ] T-1006 did **not** get a confident answer

## The three collisions (§3.4) — the row that makes this a gate

- [ ] **Collision 1** — memory bypasses the output guardrail: reproduced? **yes / no**
- [ ] Canary found in the memory store? **yes / no**
- [ ] Response chosen: **agent-level memory off / accept + document / input-side check**
- [ ] The choice is **written into the ADR**, not just decided
- [ ] **Collision 2** — `wipe()` clears memory but not knowledge? **yes / no**
- [ ] TODO(me) done: extended `wipe()` or renamed it `wipe_memory()`
- [ ] **Collision 3** — token cost measured:
  - [ ] baseline (no memory, no knowledge): **___**
  - [ ] + knowledge: **___**
  - [ ] + memory: **___**  → full config is **___×** baseline
- [ ] If more than ~2×, decided whether both retrievers earn their place before Day 84

## The gate evidence table (§4.1)

- [ ] All 17 rows attempted, each with the command that produced the evidence
- [ ] Rows marked honestly — no evidence means **fail**, recorded as one
- [ ] Row 9 (golden set) **and** row 10 (`crewai test`) both pass — different questions
- [ ] Row 11: scorer ran on a **different provider** than the crew
- [ ] Row 13: `grep -ril "PINEAPPLE" .mandala/traces/` empty
- [ ] Row 16: collisions found **and each one answered**
- [ ] Rows passed: **___ / 17**
- [ ] `crewai test` score: **___** vs. the Day-28 threshold of **___**
- [ ] Did **not** re-choose the threshold today

## Tests that must be able to fail

- [ ] `test_three_agents`
- [ ] `test_the_writer_cannot_read_tickets` — the most important test in the file
- [ ] `test_no_agent_holds_untrusted_input_and_write_ability`
- [ ] `test_every_tool_is_declared`
- [ ] `test_no_agent_can_delegate` — only means something **paired** with the Writer test
- [ ] `test_the_data_flow_is_declared`
- [ ] `test_the_first_task_is_typed`
- [ ] `test_guardrails_are_on_by_default` — **flip it:** default to `guarded=False`
- [ ] `test_memory_and_knowledge_default_to_on_for_the_gate`
- [ ] `test_memory_bypasses_the_output_guardrail_by_design` — encodes collision 1; fails on good news
- [ ] `test_the_canary_never_enters_memory` — **no longer optional**; written before tagging
- [ ] All structural tests cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why is composition where systems break?
- [ ] Why does an output guardrail not protect against memory?
- [ ] Why are the golden set and `crewai test` both required?
- [ ] Why must the third agent be in the permission table before it gets tools?
- [ ] Why is turning memory off to pass the gate worthless?
- [ ] Which nine criteria cost nothing, and why is that not luck?

## Freshness check (§4.3, Principle 13)

- [ ] Every pin re-verified; MCP spec revision re-checked
- [ ] Each reported unchanged / cosmetic / **material**
- [ ] **`crewai` checked with particular care** — the Flows DSL surface is volatile and Day 30 is tomorrow
- [ ] CrewAI rows cleared from the **Open verification items** table (embedder string, `chromadb` version)
- [ ] Material drift → addendum written **before** tagging

## Budget

- [ ] Actual counts logged in `docs/RATE_BUDGET.md` (declared: ~215 Groq, ~9 OpenRouter)
- [ ] Three-agents-with-retrieval ratio recorded: **___×** a single-agent day
- [ ] If split across two sittings, **recorded as split** — not quietly narrowed

## Commit

```bash
./m check
./m done 29
git tag phase-4-complete     # ONLY if the evidence table is honestly green
```

- [ ] `docs/adr/gate-phase-4.md` written from `ADR-TEMPLATE.md`
- [ ] It records the **threshold, the noise floor, and why the threshold sits below it**
- [ ] It records **which collision response I chose and what I accepted**
- [ ] It records **what is still unproven**
- [ ] Cold-read sign-off scheduled for +24h
- [ ] Tag applied — or **deliberately not applied**, with the reason recorded
- [ ] `./m done 29` succeeded — trackers updated automatically
