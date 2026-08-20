---
day: 2
phase: 0
phase_name: "Foundry"
title: "Foundry II — CI, quality gates, and the golden set"
ids: []
principles: ["P1 build daily", "P7 evals before features", "P9 interview-ready artifacts", "P13 weekly freshness"]
kind: gate
plan_version: "v1.1.0"
generated: "2026-08-20"
status: in-progress
lab_scaffolded: false
commit: ""
---

# Day 2 — Foundry II: CI, quality gates, and the golden set

**Phase 0 · Foundry** · 🎯 **Phase-0 gate day** · Principles served: **7, 9, 13**

> **Yesterday:** pins, three working keys, real rate limits written down.
> **Today:** the machine that keeps all of that true when you are tired — a three-tier test
> strategy, a pre-commit hook, CI with no secrets, and the ten invented tickets you will stare at
> for three months.
> **Tomorrow:** the first agent. Written from scratch. No frameworks.

```bash
./m start 2
```

---

## §1 The story

There is a moment, usually around Day 30, when you are tired, it is late, the lab nearly works, and
you think: *I'll just skip the test today.*

Today's job is to make that moment cost you nothing, because a machine already said no.

The enemy of a 90-day project is not difficulty. It is **drift**. Small compromises that each seem
fine. A version unpinned "just for now". A test commented out. A model id hardcoded in one lab
because you were in a hurry. Individually invisible. By Day 60, collectively, they mean you cannot
reproduce your own results — and the whole point of the project, *evidence you can defend to a
hiring panel*, quietly evaporates.

So you build the guardrails today, while you are fresh and still care:

- **`./m check`** — one command: lint, format check, tests. Green or the day is not done.
  (You built it on Day 0; today you give it something real to run.)
- **A pre-commit hook** — so `./m check` runs *before* the commit exists, not after.
- **CI** — so it runs on a machine that is not yours, **with no `.env` in sight.** That last part is
  sneaky and important: CI proves your tests do not secretly need your API keys.

And one thing that is not a guardrail but a habit: **the golden set**. Ten invented support tickets.
They are the Phase-1 gate, the Phase-11 eval dataset, and the Phase-12 demo input. Ten tickets, three
months. Write them carefully.

---

## §2 Setup — run this

### 2.1 Install the development tooling

```bash
uv add --dev "ruff==0.16.3" "pytest==9.1.1" "pytest-recording==0.13.4" \
             "vcrpy==8.3.0" "pre-commit==4.6.2"
```

**Line by line:**

- `uv add --dev` — record these under `[dependency-groups] dev` in `pyproject.toml` rather than under
  `dependencies`. The distinction matters: **someone running Mandala needs `openai`; they do not
  need your linter.** Dev dependencies are installed locally and in CI, and skipped by anyone who
  just wants to use your package.
- `"ruff==0.16.3"` — linter and formatter in one binary. Written in Rust, so it finishes before you
  notice it started, which is the property that makes you actually run it.
- `"pytest==9.1.1"` — the test runner.
- `"pytest-recording==0.13.4"` — the pytest plugin that gives you the `@pytest.mark.vcr` marker for
  recording and replaying HTTP.
- `"vcrpy==8.3.0"` — the library underneath it that does the actual record/replay. Named after
  videocassette recorders, which is also where "cassette" comes from.
- `"pre-commit==4.6.2"` — the git-hook manager.
- `\` at line end — continuation, so one long command reads as three lines. Nothing may follow the
  backslash, not even a space.

### 2.2 Create today's files

```bash
touch tests/conftest.py
touch tests/test_markers.py
touch tests/test_fixtures.py
touch tests/fixtures/tickets.json
touch .pre-commit-config.yaml
mkdir -p .github/workflows
touch .github/workflows/check.yml
mkdir -p days/day-02/lab
touch days/day-02/lab/trigger_429.py
```

- `tests/conftest.py` — pytest automatically imports this file before collecting tests. It is where
  shared fixtures and collection hooks live. **You never import it yourself**; pytest finds it by
  name, and it applies to every test in that folder and below.
- `tests/fixtures/cassettes/` already exists from Day 0 — that is where recorded responses land.

---

## §3 The offline test strategy (read this twice)

This section decides whether the next 88 days cost you quota or not.

**The problem:** your tests want to check agent behaviour. Agent behaviour comes from model calls.
Model calls cost requests. Requests are your budget (Principle 5). If every `pytest` run burns
fifteen Gemini requests, you will stop running `pytest`. And a test suite you do not run is worse
than no test suite, because it gives you false confidence.

**The solution: three tiers, and only one touches a network.**

| Tier | Marker | Network? | In CI? | Runs |
|---|---|---|---|---|
| **Unit** | *(none)* | ❌ never | ✅ always | every save |
| **Cassette** | `@pytest.mark.vcr` | ❌ replays a recorded file | ✅ always | every save |
| **Live** | `@pytest.mark.live` | ✅ real provider | ❌ **never** | manually, `-m live` |

A **cassette** is a recorded HTTP exchange saved as a YAML file. The first run makes a real call and
saves what came back; every run after replays the file. Same assertions, zero requests, works on a
plane.

> **Why not just mock the model?** Because a mock encodes what you *think* the API returns. A
> cassette encodes what it *actually* returned. When a provider changes a response shape, a mock
> stays cheerfully green and lies to you; a cassette re-recorded on Friday goes red and tells you.
> That is Principle 13 wearing a different hat.

### `tests/conftest.py`

```python
"""Shared pytest configuration.

Three test tiers:
  * unit      — no marker, no network, always runs
  * cassette  — @pytest.mark.vcr, replays a recorded response, always runs
  * live      — @pytest.mark.live, real provider, SKIPPED unless you pass -m live

Run the free suite:      uv run pytest
Run the live suite:      uv run pytest -m live
Re-record a cassette:    uv run pytest -m live --record-mode=rewrite
"""

from __future__ import annotations

import json
import pathlib

import pytest

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def pytest_collection_modifyitems(config, items):
    """Skip every @pytest.mark.live test unless the run explicitly asked for them."""
    if "live" in (config.getoption("-m") or ""):
        return
    skip_live = pytest.mark.skip(reason="live test — run with `uv run pytest -m live`")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture(scope="session")
def vcr_config():
    """How cassettes are recorded. Secrets are stripped before anything hits disk."""
    return {
        "filter_headers": [
            ("authorization", "REDACTED"),
            ("x-goog-api-key", "REDACTED"),
            ("api-key", "REDACTED"),
        ],
        "filter_query_parameters": [("key", "REDACTED")],
        "record_mode": "once",
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
    }


@pytest.fixture
def golden_tickets() -> list[dict]:
    """The ten invented tickets. Used by every phase from here to Day 90."""
    return json.loads((FIXTURES / "tickets.json").read_text(encoding="utf-8"))
```

**Line by line:**

- `FIXTURES = pathlib.Path(__file__).parent / "fixtures"` — the fixtures folder, located relative to
  *this file*. Not relative to the working directory. This is why the tests pass whether you run
  `pytest` from the repo root or from inside `tests/`.
- `def pytest_collection_modifyitems(config, items):` — a **pytest hook**. Pytest calls any function
  with this exact name after it has collected the tests but before running them. `items` is the list
  of collected tests, and you may modify it in place.
- `config.getoption("-m")` — read the `-m` marker expression the user typed. Returns `None` when
  absent, hence the `or ""` so the `in` check cannot fail on `None`.
- `if "live" in ...: return` — if the run asked for live tests, change nothing and let them run.
- `pytest.mark.skip(reason=...)` — build a skip marker. The `reason` is printed in the summary, so
  the output tells you *how* to run them rather than just that they were skipped.
- `if "live" in item.keywords:` — `item.keywords` contains every marker name applied to that test.
- `item.add_marker(skip_live)` — attach the skip. **This is the line that makes the default test run
  free.** Delete it and your suite starts spending quota silently.
- `@pytest.fixture(scope="session")` — a fixture computed **once per test session** rather than once
  per test. Correct for configuration, which never changes mid-run.
- `def vcr_config():` — `pytest-recording` looks for a fixture with this exact name and uses whatever
  dict it returns to configure VCR. Naming is the wiring; there is no registration step.
- `"filter_headers": [("authorization", "REDACTED"), ...]` — **the most important three lines in this
  file.** Before a cassette is written, these headers are replaced. Without them your API key is
  saved into a YAML file and committed to git. Three headers because the three providers
  authenticate differently: `authorization: Bearer ...` (Groq, OpenRouter), `x-goog-api-key`
  (Gemini's native path), and `api-key` (some compatibility layers).
- `"filter_query_parameters": [("key", "REDACTED")]` — some Google endpoints accept the key as
  `?key=...` in the URL rather than a header. Belt and braces.
- `"record_mode": "once"` — record if no cassette exists; otherwise replay and **never** hit the
  network. The safe default. Other modes exist (`rewrite`, `all`, `none`); `once` is the one that
  cannot surprise you.
- `"match_on": [...]` — how VCR decides that an incoming request matches a recorded one. Note that
  **body is not in the list**: prompts change slightly as you iterate, and you do not want a
  one-word prompt edit to invalidate the cassette. Method + URL is the right granularity here.
- `@pytest.fixture def golden_tickets()` — any test that names `golden_tickets` as a parameter gets
  the parsed list. No import, no path juggling in each test.
- `read_text(encoding="utf-8")` — always specify the encoding on Windows.

---

## §4 The golden set — write this carefully

Ten invented support tickets. Not a throwaway: they are the Phase-1 gate, the Phase-11 eval dataset,
and the Phase-12 demo input.

Make them **varied on purpose.** Include at least one genuinely **ambiguous** ticket (careful humans
would disagree about its category), one **very short** one, and one **long and rambling** one. Those
three are where your agents will fail, and failing on Day 3 in a controlled way is the point.

```bash
cat > tests/fixtures/tickets.json <<'EOF'
[
  {"id": "T-1001", "severity": "high", "category": "auth",
   "body": "Login redirects in a loop after SSO. Started this morning around 09:15. About 40 users affected. Clearing cookies does not help."},

  {"id": "T-1002", "severity": "low", "category": "billing",
   "body": "Invoice PDF still shows our old company name after we renamed the org."},

  {"id": "T-1003", "severity": "medium", "category": "billing",
   "body": "We were charged twice for March. Need one of them refunded."},

  {"id": "T-1004", "severity": "high", "category": "data",
   "body": "Scheduled export job has produced empty CSVs since the 14th. No error, just zero rows."},

  {"id": "T-1005", "severity": "low", "category": "howto",
   "body": "How do I rename a workspace?"},

  {"id": "T-1006", "severity": "medium", "category": "data",
   "body": "it's broken"},

  {"id": "T-1007", "severity": "medium", "category": "billing",
   "body": "Our usage dashboard shows 4.2M API calls for July but the invoice is calculated on 5.1M. Either the dashboard is under-reporting or we are being over-billed, and I genuinely cannot tell which. The finance team needs an answer before the 30th."},

  {"id": "T-1008", "severity": "critical", "category": "auth",
   "body": "A former employee's account still has admin access three weeks after offboarding. Please revoke immediately."},

  {"id": "T-1009", "severity": "low", "category": "other",
   "body": "Hi team! Just wanted to say the new dashboard looks great. Also, unrelated, at some point last week I think I saw a spinner that never stopped on the reports page, but I refreshed and it was fine, so probably nothing. Anyway, no action needed, feel free to close this. Thanks for all your work!"},

  {"id": "T-1010", "severity": "high", "category": "data",
   "body": "Webhook deliveries stopped at 03:00 UTC. Our queue is backing up at roughly 2k events an hour."}
]
EOF
```

**What each ticket is *for* — this is the design, not decoration:**

| Ticket | Its job in the curriculum |
|---|---|
| T-1001 | The clean case. Everything should get this right; if it does not, something is broken. |
| T-1002, T-1005 | Genuinely low severity. Tests that your agent does not panic-escalate everything. |
| T-1003 | Clean billing case, contrasts with T-1007. |
| T-1004 | Silent failure — no error message. Tests whether the agent reads the *symptom*. |
| **T-1006** | **The very short one.** "it's broken" has no information. A good agent asks; an overconfident one invents. This is the Day-4 confidence test and the Day-56 Elicitation demo. |
| **T-1007** | **The ambiguous one.** Billing or data? Careful humans disagree. This is your calibration case for Day 4 and your LLM-as-judge disagreement case for Day 72. |
| T-1008 | The one that must **never** be auto-resolved. Your Day-84 graduated-autonomy rule will explicitly exclude it. |
| **T-1009** | **The long rambling one**, which also says "no action needed" — a trap for agents that pattern-match on length rather than content. Also your context-budget experiment on Day 4. |
| T-1010 | High severity with a rate, for testing whether severity reasoning uses the numbers. |

Validate the JSON parses before you go further:

```bash
uv run python -c "import json,pathlib; t=json.loads(pathlib.Path('tests/fixtures/tickets.json').read_text(encoding='utf-8')); print(len(t),'tickets,',len({x['category'] for x in t}),'categories')"
```

- `{x['category'] for x in t}` — a **set comprehension**: collect the categories, duplicates removed.
  `len()` of that set is the number of distinct categories.
- Expected output: `10 tickets, 5 categories`.

⚠️ **All invented.** Free-tier Gemini prompts may be used for training. Every ticket in this repo,
forever, is fiction.

---

## §5 The tests about your test infrastructure

### `tests/test_markers.py`

```python
"""Proves the live tier is genuinely skipped by default.

If someone (you, on Day 40, tired) deletes the skip hook from conftest.py,
this test goes red immediately.
"""

pytest_plugins = ["pytester"]


def test_live_tests_are_skipped_by_default(pytester):
    pytester.makeconftest(
        (pytester.path.parent / "conftest.py").read_text(encoding="utf-8")
        if (pytester.path.parent / "conftest.py").exists()
        else ""
    )
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.live
        def test_costs_quota():
            raise AssertionError("this must never run in the default suite")
        """
    )
    result = pytester.runpytest("-p", "no:randomly")
    result.assert_outcomes(skipped=1)


def test_live_tests_run_when_asked(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.live
        def test_opt_in():
            assert True
        """
    )
    result = pytester.runpytest("-m", "live")
    result.assert_outcomes(passed=1)
```

**Line by line:**

- `pytest_plugins = ["pytester"]` — enables pytest's own testing plugin. It gives you a `pytester`
  fixture that can create a **temporary throwaway pytest project** and run pytest inside it. This is
  how you test pytest configuration without recursion.
- `pytester.makeconftest(...)` — write a `conftest.py` into that temporary project. Here it copies
  your real one so the temporary project has the same skip hook.
- The `if ... else ""` — a conditional expression guarding against the file not existing yet, so the
  test gives a clear failure rather than a `FileNotFoundError`.
- `pytester.makepyfile("""...""")` — write a test file from a triple-quoted string.
- `raise AssertionError("this must never run...")` — the fake test **fails loudly if it executes**.
  So if the skip stops working, you do not get a silent pass; you get an explosion.
- `pytester.runpytest("-p", "no:randomly")` — run pytest in the temporary project. `-p no:randomly`
  disables a plugin that could shuffle order; harmless if you do not have it.
- `result.assert_outcomes(skipped=1)` — assert exactly one test was skipped and nothing passed or
  failed. Precise assertions catch more than "did not crash".
- The second test proves the **opposite** direction: `-m live` really does run them. A guard that
  can never be lifted is not a guard, it is a wall.

### `tests/test_fixtures.py`

```python
"""The golden set must stay varied. A monotonous dataset flatters every agent."""


def test_golden_set_size(golden_tickets):
    assert len(golden_tickets) == 10


def test_golden_set_is_varied(golden_tickets):
    categories = {t["category"] for t in golden_tickets}
    assert len(categories) >= 4, f"only {len(categories)} categories — too monotonous to be a test"


def test_golden_set_has_a_very_short_ticket(golden_tickets):
    """T-1006 is 'it's broken'. It exists so agents must learn to ask instead of guess."""
    assert any(len(t["body"]) < 40 for t in golden_tickets)


def test_golden_set_has_a_long_ticket(golden_tickets):
    """T-1009 is the context-budget case for Day 4."""
    assert any(len(t["body"]) > 300 for t in golden_tickets)


def test_every_ticket_has_the_required_fields(golden_tickets):
    for t in golden_tickets:
        assert set(t) == {"id", "severity", "category", "body"}, f"bad shape: {t.get('id')}"


def test_ticket_ids_are_unique(golden_tickets):
    ids = [t["id"] for t in golden_tickets]
    assert len(ids) == len(set(ids)), "duplicate ticket id"
```

**Line by line:**

- `def test_golden_set_size(golden_tickets):` — naming the fixture as a parameter is how you request
  it. Pytest matches by name.
- `any(len(t["body"]) < 40 for t in golden_tickets)` — `any()` short-circuits: it stops at the first
  match. The argument is a **generator expression**, so nothing is built in memory.
- `assert set(t) == {...}` — iterating a dict yields its keys, so `set(t)` is the set of field names.
  Comparing with `==` (not `>=`) catches **extra** fields as well as missing ones — a typo'd key
  like `"catgeory"` fails here rather than confusing an agent on Day 30.
- `len(ids) == len(set(ids))` — the standard duplicate check: a set discards duplicates, so if the
  lengths differ there was one.
- Every assertion has a message. When Day 84 rewrites the golden set with twenty unseen tickets,
  these messages tell you what invariant you broke.

Run everything:

```bash
uv run pytest -v
```

---

## §6 The pre-commit hook

`./m check` only helps if it runs. Make it automatic.

```bash
cat > .pre-commit-config.yaml <<'EOF'
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.16.3
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: local
    hooks:
      - id: pytest-fast
        name: pytest (unit + cassette, offline)
        entry: uv run pytest -q
        language: system
        pass_filenames: false
        always_run: true

      - id: no-env-staged
        name: refuse to commit .env
        entry: bash -c '! git diff --cached --name-only | grep -qx "\.env"'
        language: system
        pass_filenames: false
        always_run: true
EOF

uv run pre-commit install
```

**Line by line:**

- `repos:` — the list of hook sources. Each entry is a git repository (or `local`).
- `rev: v0.16.3` — **the hook version is pinned too.** Principle 4 applies to tooling: an unpinned
  hook can reformat your whole repo after an upstream release.
- `- id: ruff` with `args: [--fix]` — lint and auto-fix what is safely fixable.
- `- id: ruff-format` — format the code. Note the ordering: lint-fix first, then format, because
  fixes can change line lengths.
- `- repo: local` — hooks that run commands from your own machine rather than a downloaded repo.
- `entry: uv run pytest -q` — the command. `-q` keeps the pre-commit output short.
- `language: system` — "just run this command with the system shell"; do not create an isolated
  environment for it. Correct here because `uv run` already handles the environment.
- `pass_filenames: false` — by default pre-commit appends the staged filenames to the command.
  You do **not** want `pytest tests/conftest.py src/mandala/config.py`; you want the whole suite.
- `always_run: true` — run even when no matching file changed. A docs-only commit should still not
  break the tests.
- `entry: bash -c '! git diff --cached --name-only | grep -qx "\.env"'` — the secret guard:
  - `git diff --cached --name-only` — list the **staged** file names.
  - `grep -qx "\.env"` — `-q` is quiet (exit code only), `-x` requires the **whole line** to match,
    so `.env.example` does not trigger it. `\.` is a literal dot.
  - `!` — invert the exit code. grep succeeds when it finds `.env`, so inverting makes the hook
    **fail** in exactly that case.
- `uv run pre-commit install` — writes `.git/hooks/pre-commit` so the hooks fire on every commit.
  **This step is easy to forget**, and without it the config file is decoration.

Test that it actually fires:

```bash
echo "x = 1  " > /tmp/scratch_check.py && cp /tmp/scratch_check.py src/mandala/_scratch.py
git add src/mandala/_scratch.py
git commit -m "test: hook should reformat this"
git reset HEAD~1 2>/dev/null; rm -f src/mandala/_scratch.py
```

You should see ruff-format modify the file and the commit be rejected the first time — that is the
hook working. The last line undoes the experiment.

---

## §7 CI, with no keys

```bash
cat > .github/workflows/check.yml <<'EOF'
name: check

on:
  push:
  pull_request:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: install uv
        uses: astral-sh/setup-uv@v5
        with:
          version: "0.12.5"

      - name: install python
        run: uv python install 3.12

      - name: sync dependencies (fails if uv.lock is stale)
        run: uv sync --locked --all-groups

      - name: lint
        run: uv run ruff check .

      - name: format check
        run: uv run ruff format --check .

      - name: tests (offline tier only — no secrets are configured on purpose)
        run: uv run pytest -q

      - name: docs consistency
        run: uv run python scripts/mandala.py check-ids
EOF
```

**Line by line:**

- `name: check` — what shows up in the GitHub UI.
- `on: push: / pull_request:` — trigger on both. The empty values mean "all branches".
- `runs-on: ubuntu-latest` — a clean Linux machine. Running CI on a different OS than you develop on
  is a feature: it catches path separators, encodings and case-sensitivity bugs early. (You are on
  Windows; this is exactly why every path in this project uses `pathlib`.)
- `uses: actions/checkout@v4` — clone your repo into the runner. `@v4` pins the major version.
- `uses: astral-sh/setup-uv@v5` with `version: "0.12.5"` — install the same `uv` you use locally.
  Pinned, because Principle 4 does not stop at the repo boundary.
- `run: uv python install 3.12` — install the interpreter your `pyproject.toml` demands.
- `run: uv sync --locked --all-groups` — install dependencies:
  - `--locked` — **fail the build if `uv.lock` does not match `pyproject.toml`.** This is Principle 4
    enforced by a machine instead of by your memory. Without it, CI silently resolves fresh versions
    and your pins become decorative.
  - `--all-groups` — include the `dev` group, since CI needs ruff and pytest.
- `run: uv run pytest -q` — **no `-m live`, and no secrets configured anywhere in this file.** If a
  test needs a key, CI goes red — and that is the correct outcome, because it means the test belongs
  in the live tier. **CI is your proof that the offline tier really is offline.**
- The final `check-ids` step — runs the tracker's consistency check, so documentation drift breaks
  the build like any other bug.

This file grows one more job on **Day 74**, when the eval regression gate lands (AG-24). Leave room
for it mentally; do not build it now.

Push and watch it go green:

```bash
git add -A && git commit -m "day-02: wip — CI" && git push
```

---

## §8 Meet a real 429

Before Day 6 asks you to build a router that survives rate limits, spend three minutes meeting one.

### `days/day-02/lab/trigger_429.py`

```python
"""Deliberately hit a rate limit once, and look at what it actually is.

Budget: up to ~25 tiny requests on Groq, which has the most generous daily
allowance of the three. Do NOT point this at Gemini.

Run:
    uv run python days/day-02/lab/trigger_429.py
"""

from openai import OpenAI, RateLimitError

from mandala.config import load_keys
from mandala.models import PROVIDERS

provider = PROVIDERS["groq"]
client = OpenAI(api_key=load_keys().groq, base_url=provider.base_url)

for attempt in range(1, 26):
    try:
        client.chat.completions.create(
            model=provider.default_model,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,
        )
        print(f"{attempt:>3}  ok")
    except RateLimitError as exc:
        print(f"{attempt:>3}  RATE LIMITED")
        print(f"     type      : {type(exc).__name__}")
        print(f"     status    : {exc.status_code}")
        print(f"     retry-after: {exc.response.headers.get('retry-after')}")
        print(f"     body      : {exc.message[:200]}")
        break
else:
    print("no 429 in 25 requests — your limits are generous today; note that in RATE_BUDGET.md")
```

**Line by line:**

- `from openai import OpenAI, RateLimitError` — the client library defines a specific exception class
  for HTTP 429. Catching the specific type is better than catching `Exception`, because it means you
  are only handling the case you understand.
- `for attempt in range(1, 26):` — start at 1 (nicer output) and stop before 26, so 25 attempts.
- `max_tokens=1` — the smallest possible response. You are testing *request* limits, not spending
  tokens.
- `except RateLimitError as exc:` — the branch you are here to see.
- `exc.status_code` — 429.
- `exc.response.headers.get('retry-after')` — **the number that matters.** Providers often tell you
  exactly how many seconds to wait. On Day 6 your router will read this header instead of guessing
  a backoff, which is the difference between a router that works and one that thrashes.
- `exc.message[:200]` — the first 200 characters of the body. Providers put useful detail here
  (which limit you hit: requests-per-minute, tokens-per-minute, requests-per-day).
- `break` — stop as soon as you have seen one. You are not trying to exhaust your quota.
- `else:` **attached to the `for`, not the `try`** — this is a genuine Python feature people miss.
  A `for...else` block runs **only if the loop finished without hitting `break`**. So it means "we
  never got rate limited", which is a legitimate outcome worth reporting.

Write what you saw into `docs/RATE_BUDGET.md`. On Day 6 you will build the router that handles it,
and you will build it much better having seen the real thing once.

---

## §9 Request budget

| Activity | Requests |
|---|---|
| `trigger_429.py` | ≤ 25 (Groq only) |
| Everything else today | **0** |

If `./m check` makes a network call, that is a bug you want to find now rather than on Day 74 in CI.
Verify by disconnecting your wifi and running `uv run pytest`. It must still pass.

---

## §10 Traps

- **Forgetting `uv run pre-commit install`.** The config file alone does nothing.
- **Configuring secrets in CI "so the tests pass".** Backwards. The test belongs in the live tier.
- **Omitting `--locked` from `uv sync` in CI.** Then CI resolves fresh versions and your pins are
  theatre.
- **Committing a cassette without checking it.** Open the YAML once and confirm your key really was
  redacted. `grep -ri "gsk_\|sk-\|AIza" tests/fixtures/cassettes/` should return nothing.
- **A boring golden set.** Ten near-identical tickets make every agent look brilliant, right up
  until Day 84 when real variety arrives.
- **A `./m check` that takes minutes.** It will be skipped. Move slow things to the live tier.
- **Treating the freshness check as optional.** It is graded at every phase gate. Put it in the
  calendar today.

---

## §11 Verify before you code

Written **2026-08-20**.

- `https://docs.astral.sh/ruff/` — current CLI flags for `ruff check` / `ruff format`.
- `https://docs.pytest.org/en/stable/reference/reference.html#pytester` — the `pytester` fixture and
  whether `pytest_plugins = ["pytester"]` is still the enabling incantation.
- `https://github.com/kiwicom/pytest-recording` — marker name (`vcr`) and the `vcr_config` fixture
  contract.
- `https://github.com/astral-sh/setup-uv` — action inputs.
- `https://pre-commit.com/#plugins` — hook schema keys.

---

## §12 🎯 Phase-0 gate

The plan's Phase-0 gate is **`make check` green · budget alert test-fired · pins committed**. On a $0
budget, "budget alert" means the rate-limit story, and `make` is `./m`:

| Gate criterion | Evidence |
|---|---|
| Checks green | `./m check` locally **and** a green CI run on GitHub |
| Pins committed | `pyproject.toml` + `uv.lock` in git; `docs/PINS.md` re-verified, dated |
| Budget alert test-fired | `docs/RATE_BUDGET.md` filled from live consoles; **one real 429 observed** and its `retry-after` recorded |
| Offline tier proven | `uv run pytest` passes with wifi disconnected; CI has no secrets |
| Docs machine live | `./m check-ids` green; `docs/CHANGELOG_PLAN.md` has real entries; Friday freshness block in a real calendar |
| Amendment resolved | `docs/03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md` signed off |

Write the evidence into `docs/adr/gate-phase-0.md` and tag the repo:

```bash
git tag phase-0-complete
```

---

## §13 Say it in an interview

> "The test suite has three tiers: unit, cassette-replay, and live. CI runs the first two and has no
> API keys at all — deliberately, because that's what proves the fast suite is genuinely offline.
> Live tests cost quota, so spending it is an explicit act rather than a side effect of running the
> tests. And the cassette config strips auth headers before anything touches disk, because the
> failure mode of a recorded HTTP fixture is a committed secret."

---

## §14 Done when

```bash
./m check
./m done 2
```

Tomorrow: **no frameworks.** Just you, a loop, and the raw API.
