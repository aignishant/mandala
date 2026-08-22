# Day 84 — CHECKLIST 🎯 Phase-12 gate

**IDs covered:** AG-21 🅿️ (graduated autonomy) · gate day: produces
`days/day-84/lab/autonomy_review.md` and `docs/adr/gate-phase-12.md`

## Demo command

```bash
uv run pytest -m "eval_unit or eval_trajectory" -q     # whole offline suite
uv run python scripts/audit_writes.py                  # exit 0
uv run python scripts/eval_gate.py                     # exit 0
uv run python scripts/gen_permission_table.py --check
uv run python scripts/daily_report.py
uv run pytest tests/test_autonomy.py -v
```

Expected: everything green; `GRANTS == ()`; the report showing the full capstone run's cost.

## Before you start

- [ ] **`days/day-77/lab/debts.md` read** — the golden-label debt is due today
- [ ] Five golden labels sampled and re-judged; would you still label them that way?
- [ ] If labels changed: baseline re-pinned **in its own commit**
- [ ] Judge kappa (Day 72) re-checked — it is part of the evidence chain
- [ ] **No new dependencies** — ninth consecutive day; noted in the ADR

## AG-21 — the ladder

- [ ] Levels 0–3 defined; **nothing starts above 0, nothing skips a level**
- [ ] Autonomy granted to **(agent, tool, condition)** triples, never globally
- [ ] `MAX_LEVEL_EVER` ceiling set **now**, with reasoning in the docstring
- [ ] `Grant.evidence` is a **pointer to a document**, not copied numbers
- [ ] `Grant.review_by` — every grant expires
- [ ] `Rule` is machine-evaluable: window **and** count, zero rejections, zero edits, zero
      verification failures
- [ ] Can say why "zero" rather than "few" is the statistically honest bar at n=20
- [ ] Condition registry is **closed**; unknown conditions raise
- [ ] No `eval()` anywhere near autonomy
- [ ] Started with the **narrower** condition (`low and confident`), not the broader one
- [ ] `demote()` goes straight to level 0 — asymmetry implemented
- [ ] **`GRANTS` is empty** — and can say why that is today's correct answer

## Wiring

- [ ] Auto-approval path writes the **same `Approval` record**, `decided_by="auto:<condition>"`
- [ ] Day 83's audit works unchanged against auto-approved writes — verified
- [ ] Same `check()` and same write path for auto and human — sixth chokepoint application
- [ ] Level-1 sampling **not** built (no level-1 grant exists)

## The review document (§4)

- [ ] Section 1 — what happened: numbers only, from Day 83
- [ ] Section 2 — **rejection analysis, grouped**; at least one group converted into a rubric line
      today
- [ ] Section 3 — the rule stated, and the honest answer: **"Mandala remains at level 0 for every
      tool"**
- [ ] Section 4 — what would change the answer, **with a date**
- [ ] Mentions the golden-label recheck (the Day-77 debt)

## The Phase-12 gate

- [ ] End-to-end criterion: unseen set disjoint-test green, run log attached
- [ ] Eval suite criterion: offline suite + `eval_gate.py` both exit 0
- [ ] Zero-unapproved-writes criterion: `audit_writes.py` exit 0, **three records crossed**, write
      count stated
- [ ] `docs/adr/gate-phase-12.md` written with a specific evidence column
- [ ] **"What broke during the unseen run"** section written — if nothing broke, the tickets were
      too easy
- [ ] **"What I would still not deploy, and why"** — third gate ADR with this section
- [ ] Debts updated and carried into Phase 13
- [ ] `/freshness` run; nil reports included in `docs/CHANGELOG_PLAN.md`
- [ ] `git tag -a phase-12-complete` created
- [ ] **ADR not signed today** — cold read tomorrow

## Tests that must be able to fail

- [ ] `test_everything_starts_at_level_zero` — **flip it:** grant yourself level 1 "for the demo"
- [ ] `test_no_grant_may_exceed_the_ceiling`
- [ ] `test_every_grant_has_an_expiry_and_an_evidence_pointer`
- [ ] `test_the_promotion_rule_demands_zero_rejections`
- [ ] `test_the_rule_requires_a_window_not_just_a_count`
- [ ] `test_yesterdays_evidence_does_not_meet_the_rule` — encodes the honest answer
- [ ] `test_an_unknown_condition_raises`
- [ ] `test_conditions_are_a_closed_registry_not_evaluated_strings`
- [ ] `test_auto_approval_still_writes_an_approval_record` — **flip it:** skip the record, the audit
      silently stops working
- [ ] `test_demotion_goes_straight_to_zero`
- [ ] `test_the_golden_labels_were_rechecked_today`
- [ ] All cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why is autonomy per (agent, tool, condition) rather than a level for the system?
- [ ] Why a window **and** a count?
- [ ] Why zero rejections rather than a small tolerance?
- [ ] Why must demotion be easier than promotion?
- [ ] What would have broken if auto-approval skipped the approval record?
- [ ] Why is an evaluated condition string a privilege-escalation channel?
- [ ] What exactly would have to be true for you to grant level 1, and when could that happen?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~10)
- [ ] **Three consecutive gates passed on deterministic evidence** — noted in the ADR
- [ ] Approval CLI records **edits** distinctly from approvals — added today, or `max_edits` dropped
      honestly
- [ ] Judge kappa re-checked and recorded
- [ ] `Literal` with int members confirmed in the type checker
- [ ] Full `/freshness` sweep logged

## Commit

```bash
./m check
./m done 84
```

- [ ] `autonomy_review.md`, gate ADR and the empty `GRANTS` all committed
- [ ] New rubric line (from the rejection analysis) committed
- [ ] `./m done 84` succeeded
- [ ] **Day 85 not started until the cold read is done**
