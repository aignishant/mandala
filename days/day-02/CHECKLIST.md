# Day 2 — CHECKLIST 🎯 Phase-0 gate

**IDs covered:** none (Phase-0 infrastructure) · **Principles served:** 1, 7, 9, 13

## Demo command

```bash
make check                       # green, offline, under ~30s
uv run pytest -m live --collect-only   # shows live tests exist but are skipped by default
```

## Definition of done

- [ ] `Makefile` — `check`, `lint`, `test`, `live`, `fmt` targets
- [ ] `make check` green **and fast** (< ~30s)
- [ ] `make check` makes **zero network calls**
- [ ] `.pre-commit-config.yaml` — ruff (pinned), pytest, and the "no `.env` staged" guard
- [ ] `pre-commit install` run; hook fires on a test commit
- [ ] `.github/workflows/check.yml` — `uv sync --locked`, ruff, pytest, **no secrets configured**
- [ ] CI run is green on a real push
- [ ] `tests/conftest.py` — `live` and `cassette` markers; live skipped unless `-m live`
- [ ] `tests/fixtures/tickets.json` — **10 invented tickets**, ≥4 categories, one very short, one ambiguous, one long
- [ ] Deliberately triggered one 429 and read the real error/headers

## Tests that must be able to fail

- [ ] `tests/test_markers.py::test_live_tests_are_skipped_by_default` — red if the skip hook is removed
- [ ] `tests/test_fixtures.py::test_golden_set_is_varied` — red if the golden set is monotonous

## Docs machine

- [ ] `docs/CHANGELOG_PLAN.md` — Day 1 and Day 2 lines appended
- [ ] `docs/RATE_BUDGET.md` — live numbers, dated
- [ ] `docs/PINS.md` — re-verified, dated
- [ ] `docs/03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md` — signed off
- [ ] `docs/adr/ADR-TEMPLATE.md` — read
- [ ] **Friday freshness check scheduled in a real calendar** (Principle 13)

## 🎯 Phase-0 gate criteria

- [ ] `make check` green (local + CI)
- [ ] Pins committed (`pyproject.toml`, `uv.lock`, `docs/PINS.md`)
- [ ] Budget/rate-limit story proven (RATE_BUDGET filled, one 429 observed)
- [ ] Docs machine live
- [ ] `docs/adr/gate-phase-0.md` written with the evidence
- [ ] Repo tagged `phase-0-complete`

## Commit

- [ ] Committed — `day-02: foundry — CI, quality gates, docs machine (phase-0 gate)`
- [ ] `LESSON.md` frontmatter: `status: done`, `commit: <sha>`
- [ ] `docs/CURRICULUM_INDEX.md` Day 2 row set to ✅
