# Day 22 — CHECKLIST

**IDs covered:** — (gate day) · **PHASE-3 GATE 🎯**

## Demo command

```bash
uv run python days/day-22/lab/long_run.py --tickets 3    # rehearse first
uv run python days/day-22/lab/long_run.py                # the full run
# ... Ctrl-C partway, then run it again — the resume test
uv run python days/day-14/lab/span_tree.py               # the evidence
```

## Setup

- [ ] `./m start 22` and `./m scaffold 22` run
- [ ] **No new packages** — a gate day that needs a dependency is smuggling in new work
- [ ] `docker run --rm hello-world` succeeds
- [ ] `temporal server start-dev` succeeds
- [ ] `uv run pytest -q -m "not docker and not temporal"` green **before** starting
- [ ] Files created (`src/mandala/workspace.py`, two lab files, two test files)

## The blast-radius decision (§3.2)

- [ ] Can state the three options and why the first two were rejected
- [ ] Widening is **one directory, one run, disposable** — nothing else changed
- [ ] Network still off, credentials still absent, timeout still enforced
- [ ] The justification is written down, not just decided

## `workspace.py`

- [ ] Lives under `.mandala/` (gitignored since Day 14)
- [ ] Run ids are **rejected, not sanitised**
- [ ] `resolve()` resolves **before** comparing — can say why the order matters
- [ ] `MAX_FILES` and `MAX_FILE_BYTES` enforced
- [ ] `destroy()` used when changing artifact format mid-debug
- [ ] `mount_spec()` written (the TODO(me)) and **eye-checked against Day 19's `container_kwargs`**

## The three collisions (§3.4) — answer each out loud

- [ ] Writes vs. read-only → resolved how?
- [ ] Retries vs. one-effect → resolved how?
- [ ] Approvals vs. unattended runs → resolved how, and what is the rule?
- [ ] Can state why a gate that fires on scratch is worse than no gate

## The long run

- [ ] `ticket_ids()` written (the TODO(me)) — reads the fixture, not hard-coded
- [ ] Rehearsed on 3 tickets **before** running 11
- [ ] Filenames derived from the **ticket id**, never a counter
- [ ] Every write goes through `ws.write()`, never bare `open()`
- [ ] The long-horizon agent still holds **no write tool**
- [ ] Full run completed: **___** analyses + 1 rollup

## The kill test (§3.6) — do not skip

- [ ] Killed mid-run after **___** files
- [ ] Second run printed `already done, skipping` for each finished ticket
- [ ] Model calls, first run: **___** · second run: **___**
- [ ] Second run cost **strictly less** — if not, resumption is decorative

## The gate evidence table (§4.1)

- [ ] All 15 rows attempted, each with the command that produced the evidence
- [ ] Rows marked honestly — a criterion with no evidence is a **fail**, and recorded as one
- [ ] `git status --short` clean after the run (row 3)
- [ ] `docker ps -a --filter label=mandala.sandbox` empty (row 6)
- [ ] Suite green with neither Docker nor Temporal (row 14)
- [ ] Number of rows passed: **___ / 15**

## The harness explainer (§4.2)

- [ ] `docs/explainers/paid-harness-and-sandbox.md` finished
- [ ] Answers all five required questions
- [ ] Contains an honest "what mine does worse" list
- [ ] Contains an **"I would buy theirs when…"** paragraph
- [ ] **Read cold, out loud, ≥24h later** — and it still convinces me
- [ ] Not a documentation summary — it compares from experience

## Freshness check (§4.3, Principle 13)

- [ ] Every pin in `docs/PINS.md` re-verified
- [ ] MCP spec revision re-checked
- [ ] Each reported as unchanged / cosmetic / **material**
- [ ] "Checked, unchanged" written down — a nil report is a real result
- [ ] Material drift → addendum written **before** tagging (Principle 14)
- [ ] **Open verification items** table worked through, especially the generation-vs-response
      span type (criterion 9 quotes a number that depends on it)

## Tests that must be able to fail

- [ ] `test_a_run_id_that_is_a_path_is_refused` — **flip it:** sanitise instead of reject
- [ ] `test_a_filename_that_escapes_is_refused`
- [ ] `test_a_symlink_cannot_be_used_to_escape` — the one that proves the resolve order
- [ ] `test_file_count_is_capped`
- [ ] `test_file_size_is_capped`
- [ ] `test_writing_the_same_path_twice_is_one_file`
- [ ] `test_destroy_removes_everything`
- [ ] `test_no_agent_holds_untrusted_input_and_write_ability`
- [ ] `test_the_long_run_agent_has_no_write_tool`
- [ ] `test_workspace_writes_are_not_classified_as_external_side_effects`
- [ ] `test_no_paid_provider_is_referenced_anywhere`
- [ ] `test_the_explainer_exists_and_is_about_a_page`
- [ ] `test_resuming_costs_less_than_starting` — ships **skipped**; unskip it
- [ ] All §5 tests cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why does a gate day break things that all passed their own tests?
- [ ] What is the rule for what needs an approval gate, in one sentence?
- [ ] Why does deriving the filename from the ticket id make resumption correct?
- [ ] When would you reach for Temporal instead of the four-line `if`?
- [ ] Why resolve before comparing paths?
- [ ] Which seven criteria cost nothing to check, and why is that not luck?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~124, Groq)
- [ ] If ~124 exceeds 10% of daily RPD → **gate split across two sittings** (legitimate)
- [ ] Did **not** quietly run a smaller gate instead

## Commit

```bash
./m check
./m done 22
git tag phase-3-complete     # ONLY if the evidence table is honestly green
```

- [ ] `docs/adr/gate-phase-3.md` written from `ADR-TEMPLATE.md`
- [ ] It names **what I would not do again**
- [ ] It names **what is still unproven**
- [ ] Cold-read sign-off scheduled for +24h
- [ ] Tag applied — or **deliberately not applied**, with the reason recorded
- [ ] `./m done 22` succeeded — trackers updated automatically
