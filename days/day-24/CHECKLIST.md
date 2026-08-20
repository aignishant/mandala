# Day 24 — CHECKLIST

**IDs covered:** CR-03 🛠️ (tasks: description, expected_output, context), CR-04 🛠️ (sequential process)

## Demo command

```bash
uv run python days/day-24/lab/sequential_crew.py T-1004
uv run python days/day-24/lab/context_leak.py        # run this FOUR times
```

## Setup

- [ ] `./m start 24` and `./m scaffold 24` run
- [ ] No new packages
- [ ] `RESOLUTION_WRITER` prompt added to `crew/roles.py`, sourced from Day 8's `RESOLVER_PROMPT`
- [ ] `scaffold_tour.py --write` re-run after adding the role
- [ ] Saw yesterday's drift test go red **before** regenerating — the system working
- [ ] Files created (`crew/tasks.py`, two lab files, one test file)

## CR-03 — tasks

- [ ] Can say why **the task, not the agent, is the unit of work**
- [ ] Can name the mistake associated with each of the four fields
- [ ] `expected_output` specifies **format, bounds and a prohibition** — all checkable
- [ ] Can tell a contract from a wish, with an example of each
- [ ] `NO_QUOTING` is a **named constant**, not a bare literal — so it is greppable and testable
- [ ] Ticket body wrapped in `<ticket>` with an explicit data-not-instructions line
- [ ] Understood that CrewAI provides **no untrusted envelope** by default
- [ ] `context=[research]` declared explicitly, not inferred from list order — can say why

## The seam (§3.2) — the important table

- [ ] Can recite what crosses the seam in all five rows (Day 8 / 13 handoff / 13 as_tool / 14 / today)
- [ ] Can state today's guarantee in one sentence, honestly
- [ ] Knows which future day fixes the **typing** half (Day 26) and which fixes the **checking** half (Day 27)

## The context experiment (§3.5) — do not skip

- [ ] `context_leak.py` run **4 times**
- [ ] Canary in the **research** output: **___ / 4**
- [ ] Canary in the **probe** output: **___ / 4**
- [ ] Observed that the second is entirely determined by the first — there is no filter between
- [ ] Can contrast this with Day 13's `input_filter`, which was mechanical
- [ ] Probe was hostile enough to be meaningful (a weak probe proves nothing — Day 13's lesson)

## CR-04 — the sequential process

- [ ] `process=Process.sequential` — the one-liner
- [ ] Can recite the Day-14 comparison table, **both** the wins and the two losses
- [ ] Can state the three things "sequential" does **not** mean
- [ ] Read `tasks_output` per task, not just the final result
- [ ] `token_usage` recorded: **___** (vs. yesterday's one-agent number: **___**) — ratio **___**

## Where the check went (§4.3)

- [ ] Can name all five options and what each costs
- [ ] Knows Mandala is currently on the **last row** — prompt-enforced only
- [ ] **Dated gap written into the bake-off list:** "Days 24–26: crew seam is prompt-enforced only"
- [ ] Understood the general lesson: you can always buy back control by using less of the framework

## Tests that must be able to fail

- [ ] `test_expected_output_is_a_contract_not_a_wish`
- [ ] `test_the_research_contract_forbids_quoting` — **flip it:** drop `NO_QUOTING`, confirm red
- [ ] `test_the_writer_is_told_it_has_not_seen_the_ticket`
- [ ] `test_data_flow_is_declared_not_inferred_from_order`
- [ ] `test_the_pipeline_has_exactly_one_declaration`
- [ ] `test_the_ticket_body_is_wrapped_as_untrusted`
- [ ] `test_the_seam_is_known_to_be_unfiltered` — **designed to fail on good news**; can explain why
- [ ] `test_the_canary_does_not_cross_the_seam` — ships **skipped**; lift the crew out of `main()`
- [ ] All tests but the last cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why is `expected_output` a contract rather than a hint?
- [ ] What exactly crosses `context`, and what does not?
- [ ] What did the one-line pipeline cost me compared with Day 14's function?
- [ ] Why declare `context` when `Process.sequential` already runs tasks in order?
- [ ] Why does a test that asserts the *absence* of a feature earn its place?
- [ ] Which is the stronger control — `input_filter` or `NO_QUOTING`, and why?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~74, Groq)
- [ ] `Task` constructor args verified for 1.15.17 (`context`, `output_file`, `async_execution`, `human_input`)
- [ ] **Verified whether a task with no `context` still implicitly receives earlier outputs** — this
      lesson assumes not; log the answer either way
- [ ] `result.tasks_output` attribute name and element shape confirmed
- [ ] Confirmed `Task` exposes no context-filtering hook in 1.15.17
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 24
```

- [ ] Bake-off list updated: one-line pipeline gained, typed seam and inter-step check lost
- [ ] `./m done 24` succeeded — trackers updated automatically
