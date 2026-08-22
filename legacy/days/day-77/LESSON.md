---
day: 77
phase: 11
phase_name: "Evals & observability"
title: "Consolidation + Phase-11 gate"
ids: []
kind: gate
plan_version: "v1.1.0"
generated: "2026-08-21"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 77 — Consolidation + Phase-11 gate 🎯

**Phase 11 · Evals & observability** · IDs: **—** · **Phase-11 gate** · the plan's designated
**buffer day**

> **Yesterday:** a cost report denominated in requests, a cache, a tier experiment, and a per-run
> budget that closes RT-12.
> **Today:** two jobs. Pay down the debts Days 71–76 deliberately left, then sit the gate — whose
> three criteria are *every behavior has a failing-able test*, *traces flow to one place*, and *the
> cost dashboard answers "what did today cost?"*.
> **Tomorrow:** Phase 12. The capstone. Everything you built this week becomes the thing that tells
> you whether the capstone works.

```bash
./m start 77
./m scaffold 77
```

---

## §1 The story

The plan calls Day 77 "buffer/consolidation", and there is a strong temptation to read that as "a
day off". It is not. **A buffer day is where you pay the interest on the shortcuts you took on
purpose** — and this phase took several, each flagged at the time:

| Day | Debt flagged | Where |
|---|---|---|
| 70 | leash rules (`ALLOWED_ORIGINS`, `MAX_STEPS`) live outside `permissions.py`, so the generated table describes them in prose | D70 §4.1 |
| 71 | golden labels may have drifted from what you'd write today | D71 §2 |
| 74 | `WATCHED` hashes all of `src/`, so a docstring edit forces a re-record | D74 §4 |
| 75 | your spans and LangChain's spans duplicate when hosted tracing is on | D75 §4 |
| 76 | context pruning is the cheap keep-first-and-last version | D76 §4.3 |

**Pick two.** Not five. A consolidation day that tries to clear the whole list produces five
half-finished changes and a red gate. The two to prefer are the ones that make *tomorrow* harder if
left: Day 74's re-record friction (you will re-record constantly during the capstone) and Day 70's
prose-not-code leash rules (Day 82 adds a write path and you want the table complete).

The second half of the day is the gate, and its middle criterion — *traces flow to one place* — is
the one to take literally. Right now you plausibly have: OTel spans in `.traces/`, SDK traces from
Day 14, CrewAI's own output from Day 28, and LangSmith when enabled. **Four places is zero places.**
The gate is passed by making one of them the place everything lands, and being able to demonstrate a
single ticket's full journey from it.

---

## §2 Setup — run this

```bash
touch docs/adr/gate-phase-11.md
touch docs/EVAL_POLICY.md
mkdir -p days/day-77/lab
touch days/day-77/lab/debts.md
touch days/day-77/lab/one_ticket_end_to_end.py
touch scripts/daily_report.py
```

No new dependencies. Fourth time this phase — worth noticing: **Phase 11 added exactly two packages
(`langsmith`, `opentelemetry-sdk`) in seven days.** Observability is mostly decisions.

---

## §3 Consolidation — the two you picked

### 3.1 Suggested debt A — make the leash generatable

Move the browser's constraints out of prose and into data the Day-70 generator can read:

```python
# src/mandala/computer/leash.py — add near the top
CONSTRAINTS: dict[str, str] = {
    "allowed_origins": ", ".join(sorted(ALLOWED_ORIGINS)),
    "max_steps": str(MAX_STEPS),
    "action_vocabulary": ", ".join(sorted(ActionKind.__args__)),
    "irreversible_hints": ", ".join(IRREVERSIBLE_HINTS),
    "downloads": "disabled at the browser context",
    "popups": "closed on open",
    "request_gate": "context.route('**/*') — blocks off-origin fetches by the PAGE",
}
```

Then in `scripts/gen_permission_table.py`, replace the hand-written prose section with a table built
from `CONSTRAINTS`. **The drift test now covers the leash too** — change `MAX_STEPS` without
regenerating and CI fails, which was the whole point of Day 70 and the one place it did not reach.

**Line by line:**

- `ActionKind.__args__` reads the `Literal`'s members at runtime, so the documented action vocabulary
  cannot diverge from the enforced one. If you add `"upload"` to the type and forget the docs, the
  docs update themselves.
- Keeping the values as **strings** matches the generator's existing shape and avoids inventing a
  second rendering path. Boring is correct here.
- Add `test_the_leash_constraints_appear_in_the_generated_table` — one assertion, and Day 82 inherits
  a complete table.

### 3.2 Suggested debt B — narrow the re-record trigger

```python
# tests/test_eval_gate.py — replace the coarse WATCHED
BEHAVIOURAL = ["src/mandala/graph/", "src/mandala/agents.py", "src/mandala/permissions.py",
               "src/mandala/router/", "src/mandala/schemas.py"]
DOCS_ONLY = ("__doc__",)


def _tree_hash() -> str:
    h = hashlib.sha256()
    for root in BEHAVIOURAL:
        for p in sorted(pathlib.Path(root).rglob("*.py")):
            src = ast.parse(p.read_text(encoding="utf-8"))
            h.update(ast.dump(_strip_docstrings(src)).encode("utf-8"))
    return h.hexdigest()[:12]
```

**Line by line:**

- Hashing the **AST with docstrings stripped** rather than the bytes means comments and docstrings no
  longer force a 20-request re-record. During the capstone you will edit docstrings constantly.
- `BEHAVIOURAL` is an explicit list, and **it is now a thing that can be wrong.** Add
  `test_every_behavioural_module_is_watched` asserting that every module imported by
  `run_experiment.py` appears under one of those roots — otherwise the narrowing quietly reintroduces
  the staleness bug you fixed on Day 74.
- If this feels like a lot of machinery for a small annoyance: it is, and it is still worth it,
  because the alternative is that you start skipping the re-record. **Every eval system dies of
  friction, not of wrongness.**

### 3.3 Write the debts you did not pay

In `days/day-77/lab/debts.md`, list the three you skipped, **each with the day it will bite**:

```markdown
| Debt | Bites on | Why deferred |
|---|---|---|
| golden labels may be stale | Day 84 (autonomy review needs trustworthy labels) | needs a full relabel sitting |
| duplicate spans with hosted tracing | Day 85 (deployment turns tracing on for real) | cosmetic until then |
| naive context pruning | Day 80 (research organ has long contexts) | Day 47 checkpointing gives a better fix |
```

**A deferred debt with a date is a plan. A deferred debt without one is a lie you told yourself.**
Same discipline as Day 70's accepted-risk table, and Day 84 should open by reading this file.

---

## §4 The gate — criterion by criterion

### 4.1 "Every Mandala behavior has a failing-able test"

This is a **coverage question about behaviours, not lines**. Build the map:

```python
# scripts/daily_report.py (part 1) — behaviour coverage
BEHAVIOURS = {
    "classifies severity from a ticket body": ["tests/test_eval_trajectory.py"],
    "never writes before escalating": ["escalated_before_any_external_write"],
    "never exceeds an agent's tool grant": ["no_agent_exceeded_its_permissions"],
    "terminates within its request budget": ["test_a_runaway_run_is_stopped"],
    "refuses off-origin browsing": ["test_off_leash_origins_are_refused"],
    "does not leak the canary to a customer draft": ["outcome_checks.no_canary_leak"],
    "does not leak the canary to a trace": ["test_the_canary_never_reaches_a_span"],
    "survives all twelve red-team attacks": ["tests/test_redteam.py"],
    "keeps the permission table current": ["test_the_checked_in_table_is_not_stale"],
    "blocks a merge on a per-example regression": ["test_a_swap_fails_even_when_the_aggregate_rises"],
}
```

**Line by line:**

- **Behaviours are written in the language of the system's promises**, not of its modules. "Never
  writes before escalating" is a promise; `test_rubric_3` is not.
- Each maps to a **named** test or rubric. If a behaviour has no test, that is the gate's finding and
  today's remaining work.
- Keep the list short and true. Twelve honest rows beat forty aspirational ones, and this table goes
  in the Day-89 portfolio where a reader will spot-check three of them.
- Add `test_every_declared_behaviour_names_a_real_test` — resolving each string against collected
  test IDs. **A behaviour map that drifts is worse than none**, because it is reassuring.

### 4.2 "Traces flow to one place"

Demonstrate it with a single ticket:

```bash
uv run python days/day-77/lab/one_ticket_end_to_end.py T-9001
```

It must show, from **one** trace source, the full journey: intake → triage → routing → research
(including which provider answered and any 429 rotation) → draft → approval gate → stop. If any leg
is missing, that framework is not yet emitting into the neutral layer, and wiring it is today's work.

**The honest version of this criterion**: you may find CrewAI's internals do not map cleanly onto
your spans. The gate is not "every framework's internals are perfectly represented" — it is **"a
single ticket's journey is reconstructible from one place."** Write in the ADR exactly which
internals are still opaque and which framework they belong to. That sentence is a genuine bake-off
input (Phase 9's "ops" column) and it is worth more than a green checkmark.

### 4.3 "The cost dashboard answers *what did today cost?*"

```bash
uv run python scripts/daily_report.py
```

One command, printing:

```
Mandala — 2026-__-__
  requests   groq 118/14400 🟩 · gemini 41/1500 🟨 · openrouter 0/200 🟩
  by phase   triage 44 · research 61 · draft 13 · judge 41
  retries    7 (5.9%)   cache hits 63%
  evals      trajectory 0.95 · outcome 0.87 · baseline triage-baseline-D73
  gate       green · 0 regressions · 12/12 red-team
```

**Line by line:**

- **One command, one screen.** A dashboard that needs three commands is a dashboard nobody runs.
- Costs *and* evals on the same screen, deliberately: the question you will actually have during the
  capstone is "did that change help, and what did it cost?", and separating them into two tools means
  you answer it half the time.
- `retries (5.9%)` as a percentage — an absolute retry count means nothing without the denominator,
  and a rising percentage is your early warning that a free tier is degrading.
- Make it a `make report` target today. Friction is the enemy; see §3.2.

### 4.4 The ADR

`docs/adr/gate-phase-11.md`, same shape as Day 70's:

```markdown
# Gate — Phase 11 (Evals & observability)

Date: 2026-__-__ · Days 71–77 · Reviewer: me (cold read: +1 day)

| Criterion | Evidence | Verdict |
|---|---|---|
| Every behavior has a failing-able test | behaviour map, 10 rows, each resolving to a named test | |
| Traces flow to one place | `one_ticket_end_to_end.py` reconstructs T-9001 from `.traces/` alone | |
| Cost dashboard answers "what did today cost?" | `make report` output, attached | |

## Instrument calibration (Day 72)
kappa per rubric line: … · position-bias flips: …/5

## What is still opaque
…

## Debts carried, with dates
(from days/day-77/lab/debts.md)

## What I would not yet trust these numbers for
…
```

**The last section again.** Day 70 asked what you would not deploy; today asks what you would not
*conclude*. Candidate honest answers: an outcome score built on a judge with kappa 0.71 should not be
quoted to three decimal places; a 20-example golden set cannot detect a 3% regression; a cache hit
rate of 63% means a third of your "cheap" re-runs still cost real quota.

### 4.5 Freshness, tag, cold read

```bash
# /freshness — one line per pin in docs/CHANGELOG_PLAN.md, including nil reports
git tag -a phase-11-complete -m "Phase 11: evals, tracing, CI gate, cost accounting"
```

Do **not** sign the ADR today. Read it cold tomorrow morning, before Day 78.

---

## §5 The tests

```python
# tests/test_gate_phase11.py
import pathlib
import subprocess

import pytest

pytestmark = pytest.mark.eval_unit


def test_every_declared_behaviour_names_a_real_test():
    """Flip it: delete this and the behaviour map becomes reassuring fiction."""
    from scripts.daily_report import BEHAVIOURS

    collected = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q"], capture_output=True, text=True
    ).stdout
    for behaviour, refs in BEHAVIOURS.items():
        assert any(ref.split("::")[-1] in collected or pathlib.Path(ref).exists() for ref in refs), behaviour


def test_every_behavioural_module_is_watched():
    """The Day-74 staleness guard must not have been narrowed into uselessness."""
    from tests.test_eval_gate import BEHAVIOURAL

    for mod in ("permissions.py", "schemas.py"):
        assert any(mod in b or pathlib.Path(b).is_dir() for b in BEHAVIOURAL), mod


def test_the_leash_constraints_appear_in_the_generated_table():
    table = pathlib.Path("docs/PERMISSION_TABLE.md").read_text(encoding="utf-8")
    from mandala.computer.leash import MAX_STEPS

    assert str(MAX_STEPS) in table


def test_the_daily_report_runs_offline():
    """0 requests, no network, or nobody will run it daily."""
    out = subprocess.run(["uv", "run", "python", "scripts/daily_report.py"], capture_output=True, text=True)
    assert out.returncode == 0 and "requests" in out.stdout


def test_the_gate_adr_records_calibration_numbers():
    adr = pathlib.Path("docs/adr/gate-phase-11.md").read_text(encoding="utf-8")
    assert "kappa" in adr and "position-bias" in adr


def test_debts_carry_a_date():
    debts = pathlib.Path("days/day-77/lab/debts.md").read_text(encoding="utf-8")
    assert "Day 8" in debts or "Day 7" in debts, "every deferred debt needs the day it bites"
```

**Line by line:**

- `test_every_declared_behaviour_names_a_real_test` is the day's headline. A behaviour map is a claim
  about your system; an unverified claim in a portfolio document is the worst artifact in the repo.
- `test_every_behavioural_module_is_watched` guards §3.2's narrowing against going too far — you
  removed friction, and this makes sure you did not remove the guarantee.
- `test_the_daily_report_runs_offline` protects the property that makes the dashboard get used.
- `test_debts_carry_a_date` is small and slightly crude and it enforces the §3.3 rule mechanically.

---

## §6 Traps

- **Treating the buffer day as a day off.** It is interest payment.
- **Trying to clear all five debts.** Two, finished, beats five, half-done.
- **Deferring a debt without a date.** That is not deferral, it is forgetting on purpose.
- **A behaviour map nobody verifies.** Reassuring fiction in your portfolio.
- **Behaviours named after modules** rather than promises.
- **Four trace destinations.** Four places is zero places.
- **Claiming full trace coverage** when a framework's internals are opaque. Name what is opaque.
- **A dashboard that needs three commands.** It will be run twice.
- **Costs and evals on separate screens.** You will answer half the question.
- **Narrowing the re-record trigger into uselessness.** Guard it with a test.
- **Signing the gate ADR the same day.** Cold read, tomorrow.
- **Quoting an outcome score to three decimals** when kappa is 0.71.

---

## §7 Request budget

**Declared: ~15 model requests — a consolidation day should be cheap.**

| What | Requests |
|---|---|
| All tests, the daily report, the behaviour map | **0** |
| `one_ticket_end_to_end.py` (gate demo) | ≤ 8 |
| Re-record after the §3 changes | ≤ 20 if `src/` changed behaviourally; **~0 if the cache is warm** |
| Spot-checks | ≤ 5 |

**Yesterday's cache changes the shape of today.** If the tiering experiment left a warm cache and you
changed no prompts, the re-record is nearly free — which is exactly the property that makes the
capstone's fast iteration possible. Note that in `docs/RATE_BUDGET.md` as the phase's closing line.

---

## §8 Verify before you code

Written **2026-08-21**:

- **`pytest --collect-only -q` output format** on 9.1.1 — the behaviour-map test parses it. If it
  changed, use `--collect-only --quiet` or the JSON report plugin instead of a fragile grep.
- **`ast.dump` stability across Python patch versions** — if it varies, the source hash churns and
  everyone re-records for nothing. Pin the approach or hash `ast.unparse` output instead.
- **`Literal.__args__`** — confirm it works on your `ActionKind` alias as written.
- **Whether `make report` should be in `./m`** rather than the Makefile — check what Day 0's tracker
  script already owns before adding a parallel entry point.
- **All Phase-11 pins** (`langsmith`, `opentelemetry-sdk`) re-verified for the freshness log.
- **The MCP spec revision and the four framework pins** — full `/freshness` sweep, nil reports
  included.

---

## §9 Say it in an interview

> "The consolidation day is where I paid down debts I'd flagged deliberately during the week rather
> than pretending they weren't there — I picked the two that would make the capstone harder if left,
> and wrote the other three into a table with the specific day each would bite. The gate had three
> criteria and the interesting one was 'traces flow to one place'. I had four sources of telemetry
> across four frameworks, and four places is zero places, so I proved it by reconstructing a single
> ticket's whole journey — intake, triage, routing, which provider answered, the retry, the draft,
> the approval stop — from one trace file. I also wrote down which framework internals are still
> opaque rather than claiming complete coverage, because that's a real input to the framework
> comparison I did earlier. The behaviour map is the artifact I'd show first: ten promises the system
> makes, each resolving to a named test, with a test that verifies every row resolves — because an
> unverified coverage claim in a portfolio is worse than no claim. And the gate ADR ends with 'what I
> would not yet conclude from these numbers': my judge's kappa is 0.71, my golden set is twenty
> examples, so I can detect a broken behaviour but not a three-percent quality regression, and saying
> that out loud is more useful than a dashboard with three decimal places on it."

---

## §10 Done when

```bash
./m check
./m done 77
```

Phase 11 closes here. **Cold-read `docs/adr/gate-phase-11.md` tomorrow morning before Day 78.**
