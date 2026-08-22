# Day 64 — CHECKLIST 🎯 Phase-9 gate

**IDs covered:** LG-24 🛠️ (capstone orchestration decision record), AG-20 🛠️ (approval-gate design)

## Demo command

```bash
cat days/day-64/lab/cold_read.md
cat docs/adr/ADR-003-capstone-architecture.md
cat docs/adr/ADR-003a-approval-gate.md
uv run pytest tests/test_bakeoff.py -v
```

## The cold read — FIRST

- [ ] Scorecard **not re-read yesterday**; read today, end to end, before writing anything
- [ ] `cold_read.md` dated, and written **before** ADR-003
- [ ] Three claims I would challenge, written
- [ ] The dimension I now think is mis-scored, named
- [ ] Any unmarked slide from measurement into judgement, found
- [ ] **Alternative weighting arithmetic run** — a different engineer's plausible weights
- [ ] Recorded whether the ranking **survives** or **flips**
- [ ] If it flips easily: ADR-003 says the decision is finely balanced
- [ ] **Scorecard NOT edited** — errors noted in `cold_read.md` and referenced from the ADR

## LG-24 — ADR-003

- [ ] Context in three sentences, pointing at `SCORECARD.md`
- [ ] Decision table: a framework per component, each citing a **scorecard row**
- [ ] **Exactly three decisive rows** — or an honest admission that there were fewer
- [ ] "What would have changed this decision" — falsifiable, and **at least one condition plausibly
      true for someone else**
- [ ] If it confirms the plan's expectation: said what would have changed your mind
- [ ] If it contradicts it: followed the evidence and said so
- [ ] **Counter-case stated at its strongest** (Day 62's most-new-code finding), then answered
- [ ] Consequences written for Phases 10, 11, 12, 13
- [ ] "What I now cannot easily change" listed
- [ ] Risks accepted, with likelihood and mitigation
- [ ] **Review trigger named**, with a date or condition
- [ ] Phase totals for Phases 5–9 included

## AG-20 — ADR-003a

- [ ] Principle-12 rule restated
- [ ] Gated/not-gated table complete — **including the `no` rows and why**
- [ ] Escalation explicitly **not** gated, and can say why
- [ ] Record = Day 33's `Decision`, unchanged, bound to run id **and** fingerprint
- [ ] Mechanism = `interrupt()` + `Command(resume=...)`, resume costs 0
- [ ] **Q1 timeout answered** — and checked against Day 32's 24-hour staleness bound
- [ ] **Q2 who may approve** answered, and where the check lives
- [ ] **Q3 batch approval** answered — one record or twenty, given the fingerprint binding
- [ ] **Q4 revocation window** answered
- [ ] **Q5 reviewer never returns** answered — "waits forever" counts only if written down
- [ ] Audit trail spec written; `final_text()` named as the proof of approved == sent
- [ ] Graduated autonomy **explicitly deferred to Day 84**

## Evidence table (§4)

- [ ] Rows 1–14 all green
- [ ] Row 6 held strictly — no padding

## Standing gate freshness check (§5)

- [ ] Five packages re-verified against `docs/PINS.md`
- [ ] MCP spec revision checked
- [ ] **If any framework moved a minor version: noted as a scorecard expiry**, and folded into
      ADR-003's review trigger
- [ ] Result written in `docs/CHANGELOG_PLAN.md`, nil report included

## Understanding check — answer out loud

- [ ] Why is the cold read a method rather than a formality?
- [ ] What does re-totalling with someone else's weights tell you?
- [ ] Why cap the decisive evidence at three rows?
- [ ] State the counter-case to your own architecture decision, at its strongest.
- [ ] Which five questions does `interrupt()` not answer?
- [ ] Why does Day 32's staleness bound make the timeout question non-hypothetical?

## Budget

- [ ] Actual counts logged in `docs/RATE_BUDGET.md` (declared: ~4, Groq)
- [ ] Phase-9 six-day total computed and recorded in ADR-003

## Commit

```bash
./m check
./m done 64
```

- [ ] Day 65 §1 read — **the deferred summary-seam question comes due tomorrow**
- [ ] `./m done 64` succeeded — trackers updated automatically
