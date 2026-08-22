# Day 68 — CHECKLIST

**IDs covered:** AG-19 🛠️ (computer use & browser agents, on a local dummy site only)

## Demo command

```bash
uv run python days/day-68/lab/serve_site.py &          # terminal 1 — 0 requests
uv run python days/day-68/lab/escape_attempts.py       # 0 requests — all six must fail
uv run pytest tests/test_computer_leash.py -v          # 0 requests
uv run python days/day-68/lab/computer_loop.py "Open T-9001 and set its severity to low."
uv run python days/day-68/lab/computer_loop.py "Read T-9002 and summarise it."
```

Expected: six ✅/⏸ lines from the escape script and **zero ❌**; the first goal completes inside the
step budget; the second ends at ⏸ or 🛑 rather than at a closed ticket.

## Setup

- [ ] `./m start 68` and `./m scaffold 68` run
- [ ] `playwright==1.62.0` **verified live on PyPI** before `uv add`, then pinned exactly
- [ ] `uv run playwright install chromium` done — and the step noted for the Day-89 README
- [ ] `src/mandala/computer/` created as the sixth namespace
- [ ] Dummy site written, with **"TEST FIXTURE, NOT A REAL SYSTEM" visible in the page**
- [ ] `serve_site.py` binds `127.0.0.1`, **not** `0.0.0.0` — checked, not assumed
- [ ] Server serves `site/`, not the repo root (`curl http://127.0.0.1:8731/.env` → 404)
- [ ] `days/*/lab/shot-*.png` added to `.gitignore` **before** the first screenshot

## AG-19 — the leash (policy before driver)

- [ ] `leash.py` written **before** `driver.py`
- [ ] Can say the day's rule in one sentence: constrained by what it can **reach**, not what it may **do**
- [ ] Can say why `click(412, 380)` defeats the Day-8 permission table
- [ ] `ALLOWED_ORIGINS` compares full origins by equality — no substring matching anywhere
- [ ] `ActionKind` is a closed `Literal` — the action vocabulary is small on purpose
- [ ] `MAX_STEPS` set, and **observed firing at least once**
- [ ] `LeashViolation` and `ApprovalRequired` kept as **separate** exceptions — and can say why
- [ ] Approval threaded in as data (`approved` frozenset), not a mutable global
- [ ] Refused actions do **not** consume step budget — verified

## AG-19 — the driver (a fence, not a wrapper)

- [ ] `check_origin` called in `__init__`, before a browser launches
- [ ] `accept_downloads=False` on the context
- [ ] `set_default_timeout` lowered from Playwright's 30 s default
- [ ] Popup handler closes new tabs
- [ ] **`context.route("**/*")` request gate written** — and can say what it stops that the action
      check does not (image-URL exfiltration)
- [ ] Driving by `get_by_role(name=...)`, never coordinates — and can say why the leash needs that
- [ ] No `evaluate()`, no raw `keyboard`, no ungated `goto` exposed to the model
- [ ] Screenshots opt-in (`pixels=True`), off by default

## The escape attempts (§5.1) — before any model call

- [ ] All six attempts run
- [ ] Zero ❌ ALLOWED lines
- [ ] `javascript:` scheme refused — checked what `urlparse` actually returns for it
- [ ] `file:///` refused — checked what the origin actually is
- [ ] Script run twice in one session to see the budget fire

## Tests that must be able to fail

- [ ] `test_the_dummy_site_is_the_only_allowed_origin`
- [ ] `test_off_leash_origins_are_refused[5 rows]` — **flip it:** use `'127.0.0.1' in url`, watch
      rows 3 and 4 pass wrongly
- [ ] `test_navigation_inside_the_fence_is_allowed`
- [ ] `test_the_step_budget_is_enforced`
- [ ] `test_reading_and_scrolling_never_need_approval`
- [ ] `test_irreversible_clicks_require_a_human[4 rows]`
- [ ] `test_approval_is_specific_to_one_target` — the confused-deputy test
- [ ] `test_the_keyword_heuristic_has_known_holes[4 rows]` — **asserts the weakness on purpose**
- [ ] `test_save_draft_is_not_treated_as_irreversible`
- [ ] `test_the_permission_table_still_has_no_trifecta_holder` — sixty days, same assertion
- [ ] All of the above cost **0 model requests**

## The injection demo (§5.2)

- [ ] `danger.html` run through the loop
- [ ] Outcome recorded **verbatim** in `days/day-68/lab/notes.md` — ⏸, 🛑, or obeyed
- [ ] Noted whether the model ignored the injection, and **why that proves nothing either way**
- [ ] Page saved as the baseline for tomorrow's attack #1
- [ ] Ticket **not** closed; no request left `127.0.0.1` (checked in the route handler's log)

## The tree-vs-pixels measurement

- [ ] Same goal run both ways
- [ ] Tokens per step recorded for each
- [ ] Success/failure recorded for each
- [ ] Both numbers written into `docs/RATE_BUDGET.md` for Day 76

## Understanding check — answer out loud

- [ ] Why is a click not enumerable, and what does that break?
- [ ] What does the context route handler stop that the action check cannot?
- [ ] Why per-target approval rather than one "the human said yes" flag?
- [ ] Why must a refused action not consume the step budget?
- [ ] Why is the accessibility tree usually the better observation — and when is it not?
- [ ] Why did you write a test that asserts your own control fails?
- [ ] Which control here would still hold if the model were actively hostile?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~14)
- [ ] `aria_snapshot()` existence and shape confirmed on 1.62 — **the day's biggest API risk**
- [ ] `accept_downloads` parameter confirmed
- [ ] `context.route` vs `page.route` precedence confirmed
- [ ] `get_by_role` name matching (exact? case?) confirmed and reconciled with `looks_irreversible`
- [ ] Free-tier vision provider, size limit and quota recorded
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 68
```

- [ ] `days/day-68/lab/notes.md` committed with the injection transcript
- [ ] No screenshots committed
- [ ] `./m done 68` succeeded — trackers updated automatically
