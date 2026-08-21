# Day 70 — CHECKLIST 🎯 Phase-10 gate

**IDs covered:** — (gate day: closes AG-15…AG-19 and MCP-15; produces `docs/PERMISSION_TABLE.md`
and `docs/adr/gate-phase-10.md`)

## Demo command

```bash
uv run python scripts/gen_permission_table.py
uv run pytest tests/test_permission_table_is_current.py -v
uv run python days/day-67/lab/escape_suite.py        # sandbox — 0 requests
uv run python days/day-68/lab/serve_site.py &
uv run python days/day-68/lab/escape_attempts.py     # leash — 0 requests
uv run pytest tests/test_redteam.py -v               # 12 passed, 0 xfailed
uv run python scripts/gen_permission_table.py --check && echo "table current"
```

Expected: table regenerated with **0 violations**; every escape blocked; the red-team suite fully
green with no xfails; `--check` exits 0.

## Movement one — fix (§3)

- [ ] Every ID in `BREACHED_TODAY` classified **before** any code changed
- [ ] `days/day-70/lab/fixes.md` has one line per breach: **missing / wrong / not-wired**
- [ ] For each "not wired": **grepped for every other dispatch path**, not just the one that failed
- [ ] Fix A considered — a single dispatch chokepoint through which every tool call passes
- [ ] Fix B: if unicode normalisation added, the **trade-off recorded** (legitimate Cyrillic input)
- [ ] Fix C: draft/send split checked everywhere, not just in the table
- [ ] Fix D: MCP `tool_fingerprint` includes the **description**, and can say why that's the point
- [ ] Fingerprint is order-stable (`sorted` + `sort_keys`) — and can say why instability is dangerous
- [ ] No fix that special-cases yesterday's exact payload string
- [ ] `BREACHED_TODAY` emptied; all `xfail` markers deleted
- [ ] Any attack not fixed → **accepted risk** row with compensating control **and a review date**

## Movement two — the generated table (§4)

- [ ] `scripts/gen_permission_table.py` written
- [ ] Output line 1 says **generated, do not edit**
- [ ] Everything sorted — output is byte-identical across runs
- [ ] Tools section includes the **"returns untrusted text?"** column
- [ ] Agents section derives "may write?" from the tool registry, not a hand-kept field
- [ ] Trifecta section computes `both` per row **and** prints `trifecta_violations()` — two paths
- [ ] Computer-use section notes the leash rules and **honestly flags that they live outside
      `permissions.py`** (candidate Day-77 buffer task)
- [ ] `--check` mode exits 1 on drift
- [ ] `docs/PERMISSION_TABLE.md` generated **and committed**

## Tests that must be able to fail

- [ ] `test_the_checked_in_table_is_not_stale` — **flip it:** add a tool, don't regenerate, see red
- [ ] `test_the_table_is_deterministic`
- [ ] `test_no_agent_holds_the_lethal_trifecta`
- [ ] `test_every_agent_tool_exists_in_the_tool_registry`
- [ ] `test_every_write_tool_has_a_non_empty_blast_radius` — Principle 6, enforced mechanically
- [ ] `test_the_generated_doc_says_it_is_generated`
- [ ] `tests/test_redteam.py` — **12 passed, 0 xfailed**
- [ ] `tests/test_computer_leash.py` still green
- [ ] All of the above cost **0 model requests**

## Movement three — the gate (§5)

- [ ] Separation proof demo run
- [ ] Sandbox escape suite run — **N/N blocked**, number recorded
- [ ] Browser escape attempts run — **6/6**, zero ❌
- [ ] `danger.html` loop run — ended at ⏸ or 🛑, transcript attached to the ADR
- [ ] `docs/adr/gate-phase-10.md` written with the **evidence** column filled in, not adjectives
- [ ] "e2b-style" clause addressed explicitly: **what was built instead and why** (zero-budget
      addendum), rather than skipped
- [ ] **"What I would still not deploy, and why" section written** — the keyword heuristic, the
      canary blind spot, every accepted risk
- [ ] `/freshness` run; one line per pin in `docs/CHANGELOG_PLAN.md`, **including nil reports**
- [ ] `playwright` re-checked (added yesterday)
- [ ] MCP spec revision re-checked (RT-09's fix depends on it)
- [ ] Any material change → **addendum written before any code** (Principle 14)
- [ ] `git tag -a phase-10-complete` created
- [ ] **Cold read scheduled for tomorrow — ADR not signed today**

## Understanding check — answer out loud

- [ ] Why is a hand-maintained security document always wrong, eventually?
- [ ] What exactly does the drift test protect, and what will trigger it on Day 82?
- [ ] Which two fields make the trifecta proof computable rather than arguable?
- [ ] Missing, wrong, not-wired — give an example of each from your own run
- [ ] Why does the MCP fingerprint have to include the description?
- [ ] Why is a chokepoint better than four correct call sites?
- [ ] Why is "the tests pass" not the same as "the system is safe"?
- [ ] What would you still not put in front of a real customer, and what would change that?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~10)
- [ ] Noted how much of this gate is **0-request** — and why that matters for Day 74's CI gate
- [ ] `scripts/` importability from `tests/` confirmed (`__init__.py` or `pythonpath`)
- [ ] `./m check` updated to run `gen_permission_table.py --check`
- [ ] `unicodedata.normalize("NFKC", ...)` **actually tested** against RT-03's payload — and Fix B
      revised if it does not fold those characters
- [ ] `git tag -a` used, not a lightweight tag

## Commit

```bash
./m check
./m done 70
```

- [ ] `docs/PERMISSION_TABLE.md`, `docs/REDTEAM.md`, `docs/adr/gate-phase-10.md` all committed
- [ ] Phase-10 row updated in `docs/CURRICULUM_INDEX.md` by `./m done` (not by hand)
- [ ] `./m done 70` succeeded — trackers updated automatically
- [ ] **Day 71 not started until the cold read is done**
