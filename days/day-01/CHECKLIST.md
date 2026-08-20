# Day 1 — CHECKLIST

**IDs covered:** none (Phase-0 infrastructure) · **Principles served:** 1, 4, 5

## Demo command

```bash
make check && uv run python -c "from mandala.config import load_keys; from mandala import models; \
  load_keys(); print('keys ok'); print(models.WORKHORSE, models.FAST_LOOP, models.JUDGE)"
```

Expected: lint clean, tests pass, three real model ids printed (no `<placeholders>`).

## Definition of done

- [ ] `pyproject.toml` exists — Python 3.12, every dependency **exact-pinned**
- [ ] `uv.lock` generated **and committed**
- [ ] `.gitignore` committed **before** `.env` was created; `.env` is ignored
- [ ] `.env.example` lists key names only (no values)
- [ ] `Makefile` with `make check` → `ruff check` + `ruff format --check` + `pytest`
- [ ] `make check` is **green**
- [ ] `src/mandala/config.py` — `load_keys()` raises `MissingKey` with a helpful message
- [ ] `src/mandala/models.py` — `WORKHORSE`, `FAST_LOOP`, `JUDGE` filled from **live consoles**
- [ ] Three keys verified with **one request each** (≤3 requests total)
- [ ] `docs/RATE_BUDGET.md` — RPM / RPD / TPM filled in from the consoles, with today's date
- [ ] `docs/PINS.md` — re-verified against PyPI today; anything that moved is logged
- [ ] `docs/03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md` — **read and signed off**
- [ ] Decided how to resolve the missing `docs/01_MASTER_PLAN_ADDENDUM_GAPS.md` (carry it over, or amend the reference)

## Tests that must be able to fail

- [ ] `tests/test_config.py::test_missing_key_fails_loudly` — passes
- [ ] `tests/test_config.py::test_model_pins_are_explicit` — **was red before you filled `models.py`**, now green

## Commit

- [ ] Committed — `day-01: foundry — repo, pins, keys, rate budget`
- [ ] `docs/CHANGELOG_PLAN.md` has a "Day 1 complete" line
- [ ] `LESSON.md` frontmatter updated: `status: done`, `commit: <sha>`
- [ ] `docs/CURRICULUM_INDEX.md` Day 1 row set to ✅
