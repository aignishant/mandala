# Day 1 — CHECKLIST

**IDs covered:** none (Phase-0 infrastructure) · **Principles served:** 1, 4, 5

## Demo command

```bash
uv run python days/day-01/lab/verify_keys.py
uv run pytest tests/test_config.py -v
```

Expected: three `ok` lines with live rate-limit headers, and three green tests.

## Setup

- [x] `./m start 1` run
- [x] `uv add "openai==3.3.1" "python-dotenv==1.2.3"` — and both appear in `pyproject.toml`
- [x] `uv.lock` updated and staged
- [x] Today's files created (`src/mandala/config.py`, `models.py`, `tests/test_config.py`, `.env.example`, `days/day-01/lab/verify_keys.py`)
- [x] `grep -n '^\.env$' .gitignore` printed **SAFE** *before* `.env` was created

## Pins (Principle 4)

- [x] Ran the §3 PyPI loop and compared every line against `docs/PINS.md`
- [x] Any patch drift pinned and logged in `docs/CHANGELOG_PLAN.md`
- [x] Any minor/major drift → addendum written **before** pinning — *none today; the only movement was `langchain` 1.3.15 → 1.3.16, a patch, logged and pinned*
- [ ] `docs/03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md` — read and **signed off**
- [ ] Decided how to resolve the missing `docs/01_MASTER_PLAN_ADDENDUM_GAPS.md` (carry it over, or amend the reference)

## Keys (Principle 5)

- [x] Gemini account + `GEMINI_API_KEY`
- [x] Groq account + `GROQ_API_KEY`
- [x] OpenRouter account + `OPENROUTER_API_KEY`
- [x] `.env.example` committed with **names only, no values**
- [x] `.env` created, filled, and **not** appearing in `git status --porcelain`
- [x] `src/mandala/config.py` written — `load_keys()`, `MissingKey`, frozen `Keys`
- [x] `src/mandala/models.py` written — `WORKHORSE` / `FAST_LOOP` / `JUDGE` / `OFFLINE` + `PROVIDERS`
- [x] Model ids filled from the **live consoles**, no `<placeholders>` left
- [x] `verify_keys.py` prints `ok` for all three providers

## Rate budget

- [ ] `docs/RATE_BUDGET.md` §1 filled: RPM / RPD / TPM per provider, with today's date
- [x] Actual request count (≤3) logged in the §3 ledger
- [x] Understood the Gemini training-data warning — **fixtures only, forever**

## Tests that must be able to fail

- [x] `test_missing_key_fails_loudly` — green
- [x] `test_blank_key_is_treated_as_missing` — green (delete `.strip()` and confirm it goes red)
- [x] `test_model_pins_are_explicit[WORKHORSE|FAST_LOOP|JUDGE]` — **was red before you filled `models.py`**, now green

## Understanding check — answer out loud

- [ ] Why does `load_dotenv()` *not* overwrite an already-set environment variable, and why is that right?
- [ ] Why is `Keys` frozen?
- [ ] Why does `models.py` store `key_attr` (a name) instead of the key itself?
- [ ] Why are the constants named `WORKHORSE`/`JUDGE` rather than `GEMINI`/`OPENROUTER`?
- [ ] What does `with_raw_response` buy you that the normal call does not?

## Commit

```bash
./m check
./m done 1
```

- [ ] `./m done 1` succeeded — commit made, index/traceability/changelog updated automatically
