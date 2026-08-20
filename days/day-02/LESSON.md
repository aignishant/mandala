---
day: 2
phase: 0
phase_name: "Foundry"
title: "Foundry II — CI, quality gates, and the docs machine"
ids: []
principles: ["P1 build daily", "P7 evals before features", "P9 interview-ready artifacts", "P13 weekly freshness"]
kind: gate
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 2 — Foundry II: CI, quality gates, and the docs machine

**Phase 0 · Foundry** · 🎯 **Phase-0 gate day** · Principles served: **7, 9, 13**

> **Yesterday:** the repo, the pins, the three free keys, and the real rate limits.
> **Today:** the machine that keeps all of that true when you are tired — CI, a pre-commit hook, an
> offline test strategy, and the documents that will still be here on Day 90.
> **Tomorrow:** the first agent. Written from scratch. No frameworks.

---

## §1 The story

There is a moment, usually around Day 30, when you are tired, it is late, the lab nearly works, and
you think: *I'll just skip the test today.*

Today's job is to make that moment cost you nothing, because a machine already said no.

Here is the thing about 90-day projects: the enemy is not difficulty, it is **drift**. Small
compromises that each seem fine. A version unpinned "just for now". A test commented out. A model id
hardcoded in one lab because you were in a hurry. Individually invisible. By Day 60, collectively,
they mean you cannot reproduce your own results, and the whole point of the project — *evidence you
can defend to a hiring panel* — quietly evaporates.

So you build the guardrails on Day 2, while you are still fresh and still care. Three of them:

- **`make check`** — the one command. Lint, format, types-if-you-want, tests. Green or it isn't done.
- **A pre-commit hook** — so `make check` runs *before* the commit exists, not after.
- **CI** — so it runs on a machine that is not yours, with no `.env` in sight. That last part is
  sneaky and important: CI proves your tests don't secretly need your API keys.

And one more thing, which is not a guardrail but a habit: **the docs machine**. `CHANGELOG_PLAN.md`,
`TRACEABILITY.md`, the ADR template, the Friday freshness slot. These are the artifacts that turn
"I did a course" into "here is the decision record for why this system is shaped this way". The plan
calls that Principle 9. Interviews call it the difference between a candidate and a hire.

---

## §2 The offline test strategy (this is the important bit)

Read this section twice. It decides whether the next 88 days cost you quota or not.

**Problem:** your tests want to check agent behaviour. Agent behaviour comes from model calls. Model
calls cost requests. Requests are your budget (Principle 5). If every `pytest` run burns fifteen
Gemini requests, you will stop running `pytest`.

**Solution: three tiers of test, and only one of them touches a network.**

| Tier | Marker | Touches network? | Runs in CI? | When |
|---|---|---|---|---|
| **Unit** | *(none)* | ❌ never | ✅ always | every save |
| **Cassette** | `@pytest.mark.cassette` | ❌ replays a recorded response | ✅ always | every save |
| **Live** | `@pytest.mark.live` | ✅ real provider | ❌ **never** | manually, when you choose |

A **cassette** is just a recorded HTTP response saved to disk. The first time a test runs, it makes
a real call and saves what came back. Every time after that, it replays the file. Same assertions,
zero requests, works on a plane.

```python
# tests/conftest.py
import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "live: hits a real provider; costs quota; excluded from CI")
    config.addinivalue_line("markers", "cassette: replays a recorded response; free and offline")

def pytest_collection_modifyitems(config, items):
    """Skip live tests unless explicitly asked for with `-m live`."""
    if config.getoption("-m") == "live":
        return
    skip = pytest.mark.skip(reason="live test — run with `pytest -m live`")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)
```

Now `make check` is free and instant, and `pytest -m live` is the deliberate act of spending quota.
That distinction — **free by default, spending is explicit** — is the same discipline you will apply
to external writes in Phase 10. Get used to it here, where the stakes are only your rate limit.

> **Why not just mock the model?** Because mocks encode what you *think* the API returns. Cassettes
> encode what it *actually* returned. When a provider changes a response shape, a mock stays
> cheerfully green and lies to you; a cassette re-recorded next Friday goes red and tells you. That
> is Principle 13 wearing a different hat.

---

## §3 `make check` — the one command

```makefile
# Makefile
.PHONY: check test lint fmt live freshness

check: lint test          ## the one command. Green or the day isn't done.

lint:
	uv run ruff check .
	uv run ruff format --check .

test:
	uv run pytest -q

live:                     ## costs quota — deliberate, never in CI
	uv run pytest -q -m live

fmt:
	uv run ruff format .
	uv run ruff check --fix .
```

Keep it this short. A `check` target that takes four minutes is a `check` target you stop running.
If it ever creeps past ~30 seconds, something belongs in the `live` tier instead.

---

## §4 The pre-commit hook

`make check` only helps if it runs. Make it automatic:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.16.3          # pinned — Principle 4 applies to tooling too
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: local
    hooks:
      - id: pytest-fast
        name: pytest (unit + cassette)
        entry: uv run pytest -q
        language: system
        pass_filenames: false
      - id: no-secrets
        name: no .env staged
        entry: bash -c '! git diff --cached --name-only | grep -qE "^\.env$"'
        language: system
        pass_filenames: false
```

That last hook is thirty seconds of work and prevents the one mistake that is genuinely hard to
undo. A leaked key in git history outlives the commit that removed it.

---

## §5 CI, with no keys

```yaml
# .github/workflows/check.yml
name: check
on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          version: "0.12.5"          # pinned
      - run: uv python install 3.12
      - run: uv sync --locked         # --locked: fail if uv.lock is stale
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run pytest -q         # no -m live. No secrets. On purpose.
```

Two lines are doing quiet, heavy work:

- **`uv sync --locked`** fails the build if `uv.lock` doesn't match `pyproject.toml`. That is
  Principle 4 enforced by a machine instead of by your memory.
- **No secrets are configured at all.** If a test needs a key, CI goes red, and that is the correct
  outcome — it means that test belongs in the `live` tier. CI is your proof that the offline tier
  really is offline.

This same workflow file grows one more job on **Day 74**, when the eval regression gate lands
(AG-24). Leave room for it mentally; don't build it now.

---

## §6 The docs machine

These already exist from the bulk-generation pass. Today you make them *yours* — you read them,
you fix anything that is wrong, and you schedule the habit.

| File | What you do today |
|---|---|
| `docs/CURRICULUM_INDEX.md` | Read it end to end. This is your map for 88 more days. |
| `docs/TRACEABILITY.md` | Skim. You will regenerate it at every gate. |
| `docs/CHANGELOG_PLAN.md` | Append your Day-1 and Day-2 lines. |
| `docs/PINS.md` | Should already be re-verified from yesterday. |
| `docs/RATE_BUDGET.md` | Should already have live numbers. If not, it is not Day 2 yet. |
| `docs/adr/ADR-TEMPLATE.md` | Read it. ADR-001 arrives on Day 16 — know the shape now. |
| `docs/03_..._FRESHNESS_2026-08-20.md` | Sign it off if you didn't yesterday. |

**And schedule the Friday freshness check.** An actual recurring block in an actual calendar. The
plan makes this Principle 13 and the kickoff checklist repeats it, because a habit that lives only
in a markdown file is not a habit. Thirty minutes, every Friday, running `/freshness`: read the
release notes for every pin and the MCP spec page, and write down what you found — **including
"nothing changed"**. Nil reports are the majority of them and writing them down is what makes the
non-nil one impossible to miss.

---

## §7 Build brief

```
Makefile                     # TODO(me): check / lint / test / live / fmt targets
.pre-commit-config.yaml      # TODO(me): ruff + pytest + the no-.env guard
.github/workflows/check.yml  # TODO(me): uv sync --locked, ruff, pytest, no secrets
tests/conftest.py            # TODO(me): live + cassette markers, skip-live-by-default hook
tests/fixtures/tickets.json  # TODO(me): 10 invented support tickets — the golden set
tests/test_markers.py        # proves the live tier is actually skipped by default
docs/CHANGELOG_PLAN.md       # append Day 1 + Day 2 lines
```

### About `tests/fixtures/tickets.json` — write this carefully

Ten invented support tickets. This is **the golden set**, and it is not a throwaway. It is the
Phase-1 gate ("naked agent passes a 10-case golden set"), it is the eval dataset in Phase 11, and it
is the demo input in Phase 12. You will look at these ten tickets for three months.

Make them *varied on purpose*:

```json
[
  {"id": "T-1001", "severity": "high",   "category": "auth",
   "body": "Login redirects in a loop after SSO. Started this morning. 40 users affected."},
  {"id": "T-1002", "severity": "low",    "category": "billing",
   "body": "Invoice PDF shows the old company name."},
  {"id": "T-1003", "severity": "medium", "category": "billing",
   "body": "Charged twice for March. Need one refunded."},
  {"id": "T-1004", "severity": "high",   "category": "data",
   "body": "Export job has produced empty CSVs since the 14th."},
  {"id": "T-1005", "severity": "low",    "category": "howto",
   "body": "How do I rename a workspace?"}
]
```

…and five more. Include at least one **ambiguous** ticket (could be `billing` or `data` — good
graders disagree), one **very short** one ("it's broken"), and one **long rambling** one. Those
three are where your agent will fail, and failing on Day 3 in a controlled way is the point.

⚠️ **All invented.** Free-tier Gemini prompts may be used for training. Every ticket in this repo,
forever, is fiction.

---

## §8 The eval that must be able to fail

```python
# tests/test_markers.py
def test_live_tests_are_skipped_by_default(pytester):
    pytester.makepyfile("""
        import pytest
        @pytest.mark.live
        def test_costs_money():
            raise AssertionError("this must never run in the default suite")
    """)
    result = pytester.runpytest()
    result.assert_outcomes(skipped=1)
```

If someone (you, on Day 40, tired) deletes the skip hook from `conftest.py`, this test goes red
immediately. It is a test **about your test infrastructure**, and that is exactly the kind that
survives 90 days.

Add one more:

```python
# tests/test_fixtures.py
import json, pathlib

def test_golden_set_is_varied():
    tickets = json.loads(pathlib.Path("tests/fixtures/tickets.json").read_text())
    assert len(tickets) == 10
    assert len({t["category"] for t in tickets}) >= 4, "golden set is too monotonous to be a test"
    assert any(len(t["body"]) < 40 for t in tickets), "need at least one very short ticket"
```

---

## §9 Request budget

**0 model requests.** Today is entirely local. If your `make check` makes a network call, that is a
bug you want to find now rather than on Day 74 in CI.

---

## §10 Traps

- **A `check` target that takes minutes.** It will be skipped. Move slow things to `live`.
- **Configuring secrets in CI "so the tests pass".** Backwards. The test belongs in `live`.
- **Forgetting `--locked` on `uv sync`.** Without it CI silently resolves fresh versions and your
  pins are decorative.
- **A boring golden set.** Ten near-identical tickets will make every agent you build for 90 days
  look brilliant, right up until Day 84 when real variety arrives.
- **Treating the freshness check as optional.** It is a graded item at every phase gate. Put it in
  the calendar today.
- **Not committing the pre-commit config** because "it's local tooling". Commit it — it's part of
  how a stranger reproduces your repo (Day 90's gate).

---

## §11 Verify before you code

- `https://docs.astral.sh/ruff/` — current `ruff` CLI flags (pinned 0.16.3 as of 2026-08-20).
- `https://docs.pytest.org/` — `pytester` fixture requires `pytest_plugins = ["pytester"]` in
  `conftest.py`; check the current recipe.
- `https://github.com/astral-sh/setup-uv` — action version + inputs.
- `https://pre-commit.com/` — hook schema.

---

## §12 🎯 Phase-0 gate

The plan's gate for Phase 0 is: **`make check` green · budget alert test-fired · pins committed.**
On a $0 budget "budget alert" means the rate-limit story, so it reads:

| Gate criterion | Evidence |
|---|---|
| `make check` green | terminal output, and a green CI run |
| Pins committed | `pyproject.toml` + `uv.lock` in git; `docs/PINS.md` re-verified with today's date |
| Budget alert test-fired | `docs/RATE_BUDGET.md` filled from live consoles; you have deliberately triggered one 429 and seen the error surface cleanly |
| Docs machine live | `CHANGELOG_PLAN.md` has real entries; Friday freshness block is in your calendar |
| Amendment resolved | `03_..._FRESHNESS_2026-08-20.md` signed off |

That "deliberately triggered one 429" line is worth doing. Fire a fast loop of ten tiny requests at
Groq and watch what a rate-limit error actually looks like — the exception type, the headers, the
retry hint. On Day 6 you will build the router that handles it, and you will build it much better
having seen the real thing once.

---

## §13 Say it in an interview

> "The test suite has three tiers: unit, cassette-replay, and live. CI runs the first two and has no
> API keys at all — which is deliberate, because it proves the fast suite is genuinely offline. Live
> tests cost quota, so spending it is an explicit act, never a side effect of running the tests."

---

## §14 Done when

See `CHECKLIST.md`. Then tomorrow: **no frameworks.** Just you, a loop, and the raw API.
