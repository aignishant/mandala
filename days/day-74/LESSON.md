---
day: 74
phase: 11
phase_name: "Evals & observability"
title: "The CI regression gate"
ids: ["AG-24"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-21"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 74 — The CI regression gate

**Phase 11 · Evals & observability** · IDs: **AG-24 🛠️**

> **Yesterday:** a versioned dataset, a pinned baseline, and a comparison script that already exits
> non-zero when something breaks.
> **Today:** you put that exit code in front of `main`. Evals run on every PR, a score drop blocks the
> merge, and — the part that makes it possible at all on $0 — **the gate calls no models.**
> **Tomorrow:** tracing. Today is about what happens automatically; tomorrow is about seeing it.

```bash
./m start 74
./m scaffold 74
```

---

## §1 The story

The plan's AG-24 row is one sentence: *evals run on every PR; a score drop blocks merge*, with the
example *triage-accuracy gate at ≥0.85 on the golden set*. Everything interesting is in the
constraints:

1. **No API keys in CI.** Day 2 established this and Phase 10 hardened it. A PR from a branch should
   not be able to spend your free tier, and a fork's PR cannot see your secrets anyway. So a gate
   that calls models is a gate that is either insecure or broken.
2. **No flakiness.** A gate that fails 1 run in 8 for reasons nobody controls gets bypassed within
   two weeks — first with `--no-verify`, then with a merge-queue exception, then it's deleted. **A
   flaky gate is worse than no gate**, because it teaches the team that red means "try again".
3. **A fixed threshold *and* a no-regression rule.** These are different. `≥ 0.85` catches absolute
   badness. "no example that passed in the baseline may now fail" catches swaps — and swaps are the
   failure mode that a threshold cannot see, as you proved yesterday.

Which gives the design, and it follows entirely from Day 71's recording decision:

> **CI replays recorded trajectories and recorded drafts. It grades them with deterministic rubrics.
> It never calls a model.** The expensive half — producing evidence — happens on your machine,
> deliberately, and the artifacts are committed.

That is why `pytest-recording` and `vcrpy` were pinned on Day 2, seventy-two days before you needed
them. Today they pay off.

---

## §2 Setup — run this

No new dependencies — `pytest-recording==0.13.4` and `vcrpy==8.3.0` arrived on Day 2.

```bash
touch .github/workflows/evals.yml
touch scripts/eval_gate.py
mkdir -p days/day-74/lab
touch days/day-74/lab/refresh_recordings.py
touch tests/test_eval_gate.py
```

Check what Day 2 already built before adding anything:

```bash
ls .github/workflows/
grep -n "record-mode\|vcr\|block_network" tests/conftest.py pyproject.toml
```

**You are extending Day 2's CI, not replacing it.** If `make check` already runs lint + offline
tests on push, today adds one job and one gate script beside it.

---

## §3 AG-24 — the gate script

### 3.1 `scripts/eval_gate.py`

```python
"""The merge gate. Two rules, both offline, both explained in the failure message.

Rule 1 (absolute):    trajectory pass rate >= HARD_FLOOR
Rule 2 (relative):    no example that passed in the baseline may fail now

Rule 2 is the one that catches swaps. Rule 1 alone lets a change fix four tickets,
break three, and merge.
"""

from __future__ import annotations

import json
import pathlib
import sys

BASELINE = pathlib.Path("tests/fixtures/experiments/triage-baseline-D73.json")
CANDIDATE = pathlib.Path("tests/fixtures/experiments/pr-candidate.json")
HARD_FLOOR = 0.85


def _passed(row: dict) -> bool:
    checks = {**row["trajectory"], **row["outcome"]}
    return all(ok for ok, _ in checks.values())


def main() -> int:
    if not CANDIDATE.exists():
        print("::error::no pr-candidate.json — run refresh_recordings.py and commit it")
        return 1

    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    cand = json.loads(CANDIDATE.read_text(encoding="utf-8"))

    if base["dataset_version"] != cand["dataset_version"]:
        print(
            f"::error::dataset changed ({base['dataset_version']} -> {cand['dataset_version']}). "
            "Re-pin the baseline in its own commit, then re-run."
        )
        return 1

    rate = cand["trajectory_rate"]
    failures: list[str] = []

    if rate < HARD_FLOOR:
        failures.append(f"trajectory pass rate {rate:.3f} < floor {HARD_FLOOR}")

    was = {r["id"]: _passed(r) for r in base["rows"]}
    broken = [r["id"] for r in cand["rows"] if was.get(r["id"]) and not _passed(r)]
    if broken:
        failures.append(f"{len(broken)} example(s) regressed: {broken}")
        for r in cand["rows"]:
            if r["id"] in broken:
                for name, (ok, why) in {**r["trajectory"], **r["outcome"]}.items():
                    if not ok:
                        print(f"::error file=tests/fixtures/golden_tickets.jsonl::{r['id']} {name}: {why}")

    fixed = [r["id"] for r in cand["rows"] if not was.get(r["id"], True) and _passed(r)]
    print(f"rate {base['trajectory_rate']:.3f} -> {rate:.3f} · fixed {fixed} · broken {broken}")

    if failures:
        print("::error::" + " ; ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Line by line:**

- **Both rules, and both reported before returning.** A gate that stops at the first problem makes
  you push three times to learn three things. Collect, then fail.
- `::error file=...::` is GitHub Actions' annotation syntax — it puts the message on the diff view
  rather than only in a log nobody opens. **The per-rubric `why` string from Day 71 lands right in
  the PR**, which is the entire reason that string exists.
- The dataset-version check comes **first** and produces a distinct message telling you the correct
  action ("re-pin the baseline in its own commit"). A gate that fails without naming the fix trains
  people to bypass it.
- `was.get(r["id"])` — an example present in the candidate but not in the baseline is treated as
  "not previously passing", so it cannot regress. New examples never block a merge on day one; they
  block it after the baseline is re-pinned. That is the right default, and it should be a conscious
  one.
- `fixed` is printed even on success. **A gate that only ever speaks when angry is one people
  resent.** One line of good news per run costs nothing.
- `HARD_FLOOR = 0.85` matches the plan's own example. Put it in one place; §5 has a test asserting
  nobody quietly lowers it.

### 3.2 The workflow

```yaml
# .github/workflows/evals.yml
name: evals
on: [pull_request, push]

permissions:
  contents: read

jobs:
  gate:
    runs-on: ubuntu-latest
    env:
      MANDALA_OFFLINE: "1"
      LANGSMITH_TRACING: "false"
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          version: "0.12.5"
      - run: uv sync --frozen
      - name: No secrets are needed and none are present
        run: |
          test -z "${GROQ_API_KEY:-}${GEMINI_API_KEY:-}${OPENROUTER_API_KEY:-}" \
            || (echo "::error::a model key reached CI — remove it" && exit 1)
      - name: Lint
        run: uv run ruff check .
      - name: Permission table is current
        run: uv run python scripts/gen_permission_table.py --check
      - name: Offline evals (unit + trajectory)
        run: uv run pytest -m "eval_unit or eval_trajectory" -q
      - name: Red team suite
        run: uv run pytest tests/test_redteam.py -q
      - name: Regression gate
        run: uv run python scripts/eval_gate.py
```

**Line by line:**

- `permissions: contents: read` — least privilege for the workflow token. Principle 6 applies to CI
  as much as to agents; a workflow that can write to the repo is a workflow an injected dependency
  can write to the repo with.
- **The "no secrets" step is the one to be proud of.** It *asserts the absence* of model keys. Most
  repos assert the presence of secrets; asserting absence is what proves the gate is genuinely
  offline and cannot silently start costing money when someone adds a key.
- `uv sync --frozen` — the lockfile is the environment. A gate that resolves fresh dependencies is a
  gate that can fail because someone else released a patch.
- `gen_permission_table.py --check` — **Day 70's drift check, now enforced**, exactly as that
  lesson's §8 asked. Adding a write tool without regenerating the table now fails a PR.
- The red-team suite runs here too. Twelve attacks, zero requests, every PR. **That is Phase 10
  becoming permanent**, and it is the highest-leverage line in this file.
- Ordering is cheapest-first: lint, then drift, then evals, then the gate. Fast feedback on trivial
  problems.

---

## §4 Keeping recordings honest

The gate replays recordings. So the question that decides whether any of this is real is: **when do
recordings get refreshed, and what stops them being stale forever?**

```python
# days/day-74/lab/refresh_recordings.py
"""Re-run Mandala over the golden set, record trajectories + drafts, write pr-candidate.json.

This is the ONLY step that costs money, it runs on your machine, and its output is
committed. Run it whenever you change anything that affects behaviour.
"""

from __future__ import annotations

import subprocess
import sys

from mandala.evals.dataset import version


def main() -> int:
    print(f"dataset version {version()}")
    subprocess.check_call(
        [sys.executable, "days/day-73/lab/run_experiment.py", "pr-candidate"]
    )
    print("recorded. Commit tests/fixtures/experiments/pr-candidate.json with your change.")
    return 0
```

And the staleness guard — the part people skip:

```python
# tests/test_eval_gate.py (excerpt)
import hashlib
import json
import pathlib

import pytest

pytestmark = pytest.mark.eval_trajectory

CAND = pathlib.Path("tests/fixtures/experiments/pr-candidate.json")
WATCHED = ["src/mandala/", "scripts/eval_gate.py"]


def _tree_hash() -> str:
    h = hashlib.sha256()
    for root in WATCHED:
        for p in sorted(pathlib.Path(root).rglob("*.py")):
            h.update(p.read_bytes())
    return h.hexdigest()[:12]


def test_recordings_were_refreshed_after_the_last_source_change():
    """Flip it: delete this test and stale recordings will pass the gate forever."""
    cand = json.loads(CAND.read_text(encoding="utf-8"))
    assert cand.get("source_hash") == _tree_hash(), (
        "src/mandala changed since the recordings were made — "
        "run days/day-74/lab/refresh_recordings.py and commit the result"
    )
```

**Line by line:**

- **This is the load-bearing test of the whole day.** Without it, the gate grades a snapshot of
  behaviour from three weeks ago and reports green forever. Every "our evals run in CI" story that
  turns out to be theatre dies exactly here.
- `_tree_hash` hashes the *source that can change behaviour*, and `run_experiment.py` must write it
  into the result JSON (add `"source_hash": _tree_hash()` there today).
- The assertion message names the exact command to run. Failure messages are UX.
- The cost: you must re-run ~20 model requests whenever you touch `src/mandala/`. That is the honest
  price of an offline gate, it is paid on your machine at a time you choose, and it is far cheaper
  than a gate that runs models on every push.
- **Consider narrowing `WATCHED` later** — hashing all of `src/` means a docstring edit forces a
  re-record. Day 77's buffer is the place to make it smarter; do not over-engineer it today.

---

## §5 The rest of the tests

```python
def test_the_floor_matches_the_plan():
    from scripts.eval_gate import HARD_FLOOR

    assert HARD_FLOOR == 0.85, "the plan's AG-24 example; changing it needs an amendment"


def test_a_regression_fails_the_gate(tmp_path, monkeypatch):
    base = {"dataset_version": "v1", "trajectory_rate": 1.0,
            "rows": [{"id": "T-1", "trajectory": {"r": [True, ""]}, "outcome": {}}]}
    cand = {"dataset_version": "v1", "trajectory_rate": 1.0,
            "rows": [{"id": "T-1", "trajectory": {"r": [False, "broke"]}, "outcome": {}}]}
    assert _run_gate(tmp_path, monkeypatch, base, cand) == 1


def test_a_swap_fails_even_when_the_aggregate_rises(tmp_path, monkeypatch):
    """The whole reason rule 2 exists."""
    base = _rows({"T-1": True, "T-2": True, "T-3": False, "T-4": False})
    cand = _rows({"T-1": False, "T-2": True, "T-3": True, "T-4": True})   # 2/4 -> 3/4
    assert _run_gate(tmp_path, monkeypatch, base, cand) == 1


def test_a_dataset_change_fails_with_a_distinct_message(capsys, tmp_path, monkeypatch):
    _run_gate(tmp_path, monkeypatch, {"dataset_version": "v1", ...}, {"dataset_version": "v2", ...})
    assert "Re-pin the baseline" in capsys.readouterr().out


def test_a_new_example_does_not_block_the_merge(tmp_path, monkeypatch):
    base = _rows({"T-1": True})
    cand = _rows({"T-1": True, "T-99": False})
    assert _run_gate(tmp_path, monkeypatch, base, cand) == 0


def test_the_workflow_asserts_no_model_keys_are_present():
    wf = pathlib.Path(".github/workflows/evals.yml").read_text(encoding="utf-8")
    assert "GROQ_API_KEY" in wf and "a model key reached CI" in wf


def test_the_workflow_runs_the_permission_table_drift_check():
    wf = pathlib.Path(".github/workflows/evals.yml").read_text(encoding="utf-8")
    assert "gen_permission_table.py --check" in wf
```

**Line by line:**

- `test_a_swap_fails_even_when_the_aggregate_rises` is the day's headline. 2/4 → 3/4 is an
  improvement by any dashboard, and T-1 broke. **The gate must fail.** If you write only one test
  today, write this one.
- `test_a_new_example_does_not_block_the_merge` locks in §3.1's deliberate default so a future reader
  does not "fix" it into an obstacle.
- The two workflow tests assert **properties of YAML from pytest**. That feels odd and is right:
  CI configuration is code that nothing else tests, and it is where a well-meaning change ("just add
  the key so the outcome layer runs") silently breaks the offline guarantee.

---

## §6 Traps

- **A gate that calls models.** Insecure on forks, expensive, flaky, and it will be disabled.
- **Threshold only, no swap rule.** Merges regressions with a smile.
- **Stale recordings.** The single most common way "evals in CI" becomes theatre. Hash the source.
- **Failing on the first problem.** Three pushes to learn three things.
- **Failure messages without the fix command.** Trains bypassing.
- **Silence on success.** No `fixed` line means the gate is only ever an obstacle.
- **`permissions: write-all`** on the workflow token.
- **Resolving dependencies fresh** instead of `--frozen`.
- **Lowering the floor to go green.** It needs an amendment, and §5 has a test.
- **Re-pinning the baseline in the same commit as a behaviour change.** Attribution gone.
- **Letting a new golden example block merges before the baseline is re-pinned.**

---

## §7 Request budget

**Declared: ~20 model requests, on your machine, once — and 0 in CI, forever.**

| What | Requests |
|---|---|
| CI run (every PR, every push) | **0** |
| `refresh_recordings.py` (after each behaviour change) | ≤ 20 |
| All tests | **0** |

**Write that first row into `docs/RATE_BUDGET.md` in bold.** A regression gate whose marginal cost is
zero is a regression gate that can run on every push forever, and that property — not the score — is
what makes evals matter. Compare against Day 72's judge (~60 requests) and note where the expense
sits: producing evidence, never checking it.

---

## §8 Verify before you code

Written **2026-08-21**:

- **`astral-sh/setup-uv` action version** and whether it caches by default. Pin the action to a
  major and pin `uv` to 0.12.5 inside it.
- **`uv sync --frozen`** behaviour when `uv.lock` is out of date — does it fail, or resolve? You want
  fail.
- **GitHub Actions annotation syntax** (`::error file=...,line=...::`) — confirm it still renders on
  the Files-changed tab.
- **Does `pytest -m "eval_unit or eval_trajectory"` actually exclude the outcome layer** in your
  config? Run it locally with `--collect-only` and count.
- **Are `env:` values visible to forked-PR runs?** Confirm that no secret context is exposed to
  `pull_request` (as opposed to `pull_request_target` — **do not use that trigger**).
- **Branch protection**: making the job *required* is a repo setting, not a YAML key. A gate that
  isn't required is a suggestion. Do it today.
- `https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions` — read today.

---

## §9 Say it in an interview

> "The regression gate runs on every PR and calls no models at all — the expensive half, producing
> trajectories and drafts, happens on my machine and the artifacts are committed, so CI just replays
> recordings and grades them with deterministic rubrics. That's what makes it affordable and what
> makes it safe: the workflow actually asserts that no model API key is present, which is the
> opposite of what most CI does. The gate has two rules, and the second is the one people miss: a
> hard floor catches absolute badness, but a per-example no-regression rule catches swaps. A change
> that fixes three tickets and breaks one raises the aggregate and still blocks the merge, and the
> failure annotation names the ticket and the rubric line that broke, right on the diff. The
> load-bearing piece is a staleness test: the recordings carry a hash of the source that produced
> them, so if `src/` changed without re-recording, the suite goes red and tells you which command to
> run. Without that, an offline eval gate grades three-week-old behaviour and reports green forever
> — that's how 'we run evals in CI' turns into theatre. I also made it refuse to compare across
> dataset versions and re-pin the baseline only in its own commit, so a score movement is always
> attributable to exactly one change."

---

## §10 Done when

```bash
./m check
./m done 74
```
