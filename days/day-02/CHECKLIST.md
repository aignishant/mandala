# Day 2 — CHECKLIST 🎯 Phase-0 gate

**IDs covered:** none (Phase-0 infrastructure) · **Principles served:** 1, 7, 9, 13

## Demo command

```bash
uv run pytest -v                    # all green, offline
uv run pytest -m live --co -q       # live tests exist, and are collected only on request
./m check                           # lint + format + tests
```

## Setup

- [ ] `./m start 2` run
- [ ] `uv add --dev "ruff==0.16.3" "pytest==9.1.1" "pytest-recording==0.13.4" "vcrpy==8.3.0" "pre-commit==4.6.2"`
- [ ] Dev deps appear under a **dev group** in `pyproject.toml`, not under `dependencies`
- [ ] Today's files created (`tests/conftest.py`, `test_markers.py`, `test_fixtures.py`, `fixtures/tickets.json`, `.pre-commit-config.yaml`, `.github/workflows/check.yml`, `days/day-02/lab/trigger_429.py`)

## The three-tier test strategy

- [ ] `tests/conftest.py` written — `pytest_collection_modifyitems` skip hook, `vcr_config`, `golden_tickets`
- [ ] `vcr_config` filters `authorization`, `x-goog-api-key`, `api-key`, and the `key` query param
- [ ] `record_mode` is `"once"`
- [ ] **Wifi off → `uv run pytest` still passes** (the offline tier is genuinely offline)

## The golden set

- [ ] `tests/fixtures/tickets.json` — 10 invented tickets, valid JSON
- [ ] ≥ 4 distinct categories
- [ ] Contains a **very short** ticket (T-1006 style)
- [ ] Contains an **ambiguous** ticket (T-1007 style)
- [ ] Contains a **long rambling** ticket (T-1009 style)
- [ ] Contains one that must never be auto-resolved (T-1008 style)
- [ ] All fiction — no real names, data, or credentials

## Tests that must be able to fail

- [ ] `test_live_tests_are_skipped_by_default` — delete the skip hook and confirm it goes **red**
- [ ] `test_live_tests_run_when_asked`
- [ ] `test_golden_set_size`
- [ ] `test_golden_set_is_varied`
- [ ] `test_golden_set_has_a_very_short_ticket`
- [ ] `test_golden_set_has_a_long_ticket`
- [ ] `test_every_ticket_has_the_required_fields`
- [ ] `test_ticket_ids_are_unique`

## Pre-commit

- [ ] `.pre-commit-config.yaml` written, ruff `rev` **pinned**
- [ ] `uv run pre-commit install` run
- [ ] Hook observed firing on a deliberate test commit
- [ ] The `no-env-staged` guard rejects a staged `.env` but **allows** `.env.example`

## CI

- [ ] `.github/workflows/check.yml` written
- [ ] `uv sync --locked --all-groups` — the `--locked` flag present
- [ ] **No secrets configured in the workflow** — on purpose
- [ ] Pushed, and the run is **green** on GitHub
- [ ] The `check-ids` step passes

## The 429

- [ ] `trigger_429.py` run against **Groq** (not Gemini)
- [ ] A real `RateLimitError` observed — or the `for...else` reported none
- [ ] `retry-after` header value and the limit-type message recorded in `docs/RATE_BUDGET.md`

## Understanding check — answer out loud

- [ ] Why is a cassette better than a mock for catching provider drift?
- [ ] What exactly does `item.add_marker(skip_live)` do, and what breaks if you delete it?
- [ ] Why is `body` deliberately absent from VCR's `match_on` list?
- [ ] Why does `grep -qx "\.env"` use `-x`, and what would break without it?
- [ ] What does `for ... else` mean in Python, and why is it right in `trigger_429.py`?
- [ ] Why does CI having **no** secrets make the test suite better rather than weaker?

## 🎯 Phase-0 gate

- [ ] `./m check` green locally **and** in CI
- [ ] Pins committed (`pyproject.toml`, `uv.lock`, dated `docs/PINS.md`)
- [ ] Rate-limit story proven (RATE_BUDGET filled; one 429 observed)
- [ ] `docs/03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md` signed off
- [ ] **Friday freshness check scheduled in a real calendar** (Principle 13)
- [ ] `docs/adr/gate-phase-0.md` written with the evidence
- [ ] `git tag phase-0-complete`

## Commit

```bash
./m check
./m done 2
```

- [ ] `./m done 2` succeeded — trackers updated automatically
