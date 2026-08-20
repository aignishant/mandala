# Day 4 — CHECKLIST

**IDs covered:** AG-03 🛠️ (structured output), AG-04 🛠️ (context window as budget)

## Demo command

```bash
uv run python days/day-04/lab/triage_naked.py T-1001
uv run python days/day-04/lab/compare.py        # the three-technique table
```

Expected: a validated `TriageResult` printed as an object, plus a token-budget report showing where
the context went.

## Definition of done

- [ ] `src/mandala/schemas.py` — `TriageResult` with `Literal` severity/category, per-field descriptions, bounded `confidence`
- [ ] `src/mandala/budget.py` — `ContextBudget.charge()` / `.report()`
- [ ] `src/mandala/loop.py` — accepts `output_schema=`; charges the budget on every call
- [ ] `days/day-04/lab/triage_naked.py` — triages one ticket into a validated object
- [ ] `days/day-04/lab/compare.py` — table of *technique × valid × invalid × mean tokens* over 10 tickets
- [ ] `days/day-04/lab/fat_context.py` — the long-ticket experiment
- [ ] The token report is printed on every run (Principle 8, cheapest form)

## Experiments actually run

- [ ] Ambiguous ticket → looked at `confidence`, saw the overconfidence problem
- [ ] Removed a `Literal` value the model likes → saw the `ValidationError` fire
- [ ] Asked-nicely-for-JSON × 20 → **counted** the malformed responses
- [ ] Fat-context run → saw tokens climb **and answer quality drop**; trimming fixed both

## Tests that must be able to fail

- [ ] `test_bad_severity_is_rejected`
- [ ] `test_confidence_is_bounded`
- [ ] `test_triage_returns_valid_object_for_every_golden_ticket` — **all 10**, not most
- [ ] `test_ambiguous_ticket_reports_low_confidence` — **was red first**; fixed via the prompt
- [ ] Cassettes recorded; `make check` green offline

## ID coverage

- [ ] **AG-03** — schema enforced at the boundary; three techniques compared with measured evidence
- [ ] **AG-04** — context instrumented, and at least one lever (trim the tool result) applied and measured

## Budget

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~80, Groq)

## Commit

- [ ] Committed — `day-04: AG-03, AG-04 — TriageResult schema and the context budget`
- [ ] `LESSON.md` frontmatter: `status: done`, `commit: <sha>`
- [ ] `docs/CURRICULUM_INDEX.md` Day 4 row ✅ · `docs/TRACEABILITY.md` AG-03, AG-04 covered
