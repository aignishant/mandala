---
day: 73
phase: 11
phase_name: "Evals & observability"
title: "Datasets and experiments in LangSmith"
ids: ["LG-18"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-21"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 73 — Datasets and experiments in LangSmith

**Phase 11 · Evals & observability** · IDs: **LG-18 🛠️**

> **Yesterday:** a calibrated judge, a kappa, and a position-bias number you can quote.
> **Today:** the thing your rubrics have been missing — **history**. A dataset you can version, an
> experiment you can name, and a baseline you can pin, so "did that change help?" stops being a
> question you answer from memory.
> **Tomorrow:** the CI gate. Today's baseline is what tomorrow refuses to regress below.

```bash
./m start 73
./m scaffold 73
```

---

## §1 The story

You can already grade a run. What you cannot do is answer:

- Is 0.83 better than last week?
- Which of my last four changes moved it?
- Which *specific tickets* got worse when the aggregate went up?

That last one is the real reason for today. **Aggregates hide swaps.** A change that fixes four
tickets and breaks three shows as +1 and looks like progress. A per-example comparison against a
pinned baseline shows you the three, by ID, and one of them is the ticket where Mandala now closes
without escalating.

LangSmith gives you four primitives, and only four are worth learning today:

| Primitive | Is | Yours today |
|---|---|---|
| **Dataset** | versioned examples with expected outputs | your Day-2 golden set, uploaded |
| **Evaluator** | a function scoring one example | your Day-71 rubrics, wrapped |
| **Experiment** | one run of one system over one dataset version | `triage-baseline`, `triage-after-fix-D70` |
| **Baseline** | a named experiment you compare against | pinned today, defended tomorrow |

**Two warnings before you start, both structural.**

First: **this is a hosted service and the plan is zero-budget.** LangSmith's free tier has a monthly
trace cap. That is fine for evals — you send *results*, not every production run — but it means
today's design rule is: **the dataset and the evaluators live in your repo; LangSmith holds the
history.** If the free tier vanishes tomorrow, you lose the graphs, not the evals. §3.1 makes that
concrete and it is the single most important decision of the day.

Second: **LangSmith is optional infrastructure and your suite must run without it.** Day 74's CI gate
cannot depend on a network call to a third party. Build the local path first, then the upload.

---

## §2 Setup — run this

```bash
uv add "langsmith==0.11.1"
```

Verify the version is still live before adding it, per Principle 4. Then:

```bash
touch src/mandala/evals/dataset.py
touch src/mandala/evals/langsmith_sync.py
mkdir -p days/day-73/lab
touch days/day-73/lab/upload_dataset.py
touch days/day-73/lab/run_experiment.py
touch days/day-73/lab/compare.py
touch tests/test_dataset.py
```

And the key — **read-scoped where possible, never committed**:

```bash
# .env  (already gitignored since Day 1)
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=mandala
LANGSMITH_TRACING=false      # OFF by default. Day 75 turns it on deliberately.
```

**Line by line:**

- `LANGSMITH_TRACING=false` **today**. Setting it true silently sends every LangChain/LangGraph call
  you make to a hosted service — including ticket bodies. That is a data-flow decision, not a
  logging toggle, and it gets made on Day 75 with the trifecta table open. Add the variable to
  `.env.example` with the `false` default and a one-line comment explaining why.
- Add `LANGSMITH_API_KEY` to the Day-66 credential-scoping table. It is a third-party credential with
  read/write to your eval history.

---

## §3 LG-18 — datasets

### 3.1 `src/mandala/evals/dataset.py` — the repo is the source of truth

```python
"""The dataset lives HERE, in git. LangSmith holds a copy and the history.

Direction of truth matters: repo -> LangSmith, never the reverse. If the service
disappears, you lose graphs, not ground truth. Every example carries a stable id so
per-example comparison across experiments is possible at all.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import asdict, dataclass

GOLDEN = pathlib.Path("tests/fixtures/golden_tickets.jsonl")


@dataclass(frozen=True)
class Example:
    id: str
    ticket_body: str
    expected: dict[str, str]

    @property
    def input_hash(self) -> str:
        return hashlib.sha256(self.ticket_body.encode("utf-8")).hexdigest()[:12]


def load() -> list[Example]:
    rows = [json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [Example(id=r["id"], ticket_body=r["body"], expected=r["expected"]) for r in rows]


def version() -> str:
    """A content hash of the whole dataset. Changes when ANY example changes."""
    payload = json.dumps([asdict(e) for e in load()], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
```

**Line by line:**

- `GOLDEN` is Day 2's file. **You are not creating a new dataset today**; you are giving the existing
  one identity and versioning. Resist the urge to write fresh examples — a dataset that changes on
  the same day as the tooling is a dataset whose score movement means nothing.
- `Example.id` is **stable and human-meaningful** (`T-9002`), not a UUID. When tomorrow's CI says
  "3 examples regressed", you want to recognise them.
- `version()` is a content hash of the whole set. **Every experiment records it.** Comparing two
  experiments run against different dataset versions is the most common invalid comparison in eval
  work, and one 12-character string makes it detectable.
- `input_hash` per example lets you spot an example whose *text* was edited while its ID stayed the
  same — the sneakiest way a "regression" appears out of nowhere.
- `sort_keys=True, separators=(",", ":")` — same canonicalisation discipline as Day 70's
  fingerprint. Ordering must not change the hash.

### 3.2 Upload — repo to service, one direction

```python
# days/day-73/lab/upload_dataset.py
"""Push the repo's dataset into LangSmith. Idempotent. Never pulls."""

from __future__ import annotations

from langsmith import Client

from mandala.evals.dataset import load, version

NAME = "mandala-golden"


def main() -> None:
    client = Client()
    v = version()
    ds_name = f"{NAME}@{v}"
    if any(d.name == ds_name for d in client.list_datasets(dataset_name=ds_name)):
        print(f"{ds_name} already uploaded — nothing to do")
        return
    ds = client.create_dataset(ds_name, description=f"Mandala golden set, content version {v}")
    examples = load()
    client.create_examples(
        inputs=[{"ticket_body": e.ticket_body} for e in examples],
        outputs=[e.expected for e in examples],
        metadata=[{"mandala_id": e.id, "input_hash": e.input_hash} for e in examples],
        dataset_id=ds.id,
    )
    print(f"uploaded {len(examples)} examples to {ds_name}")


if __name__ == "__main__":
    main()
```

**Line by line:**

- **The dataset name embeds the content version.** Editing an example creates a *new* dataset rather
  than mutating one, so old experiments stay interpretable forever. This costs a little clutter and
  buys you the ability to trust a three-month-old number.
- **Idempotent**: re-running uploads nothing. You will run this from a script that you also run from
  a Makefile, twice, by accident.
- `metadata` carries `mandala_id` — the join key back to your repo. Without it, a LangSmith example
  is an opaque row and per-example comparison against your local results is guesswork.
- `client.create_examples(...)` in **one bulk call**, not a loop — free tiers rate-limit per request,
  and 20 sequential calls is how you meet a 429 on your first attempt. §8 asks you to confirm the
  bulk signature, which has changed between versions.

---

## §4 Experiments and the pinned baseline

```python
# days/day-73/lab/run_experiment.py
"""Run Mandala over the dataset, score with the LOCAL rubrics, then ship results.

Note the ordering: grade locally, upload the grades. The evaluators are your code
(Days 71-72) — LangSmith stores what they said. That keeps CI independent of the
service and keeps the evaluators reviewable in git.
"""

from __future__ import annotations

import json
import pathlib

from mandala.evals.dataset import load, version
from mandala.evals.rubric import ALL
from mandala.evals.scoring import aggregate, outcome_checks

RESULTS = pathlib.Path("tests/fixtures/experiments")


def run(experiment: str) -> dict:
    rows = []
    for ex in load():
        trajectory, draft = run_mandala(ex.ticket_body)     # TODO(me)
        rows.append(
            {
                "id": ex.id,
                "trajectory": {n: r(trajectory) for n, r in ALL.items()},
                "outcome": outcome_checks(draft, ex.expected),
            }
        )
    result = {
        "experiment": experiment,
        "dataset_version": version(),
        "trajectory_rate": aggregate([r["trajectory"] for r in rows], "trajectory").rate,
        "outcome_rate": aggregate([r["outcome"] for r in rows], "outcome").rate,
        "rows": rows,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{experiment}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
```

```python
# days/day-73/lab/compare.py
"""Per-example diff against the pinned baseline. This is the actual deliverable."""

from __future__ import annotations

import json
import pathlib
import sys

RESULTS = pathlib.Path("tests/fixtures/experiments")


def load(name: str) -> dict:
    return json.loads((RESULTS / f"{name}.json").read_text(encoding="utf-8"))


def compare(baseline: str, candidate: str) -> None:
    b, c = load(baseline), load(candidate)
    if b["dataset_version"] != c["dataset_version"]:
        sys.exit(f"REFUSING: different dataset versions ({b['dataset_version']} vs {c['dataset_version']})")
    bi = {r["id"]: r for r in b["rows"]}
    fixed, broken = [], []
    for r in c["rows"]:
        was = all(ok for ok, _ in {**bi[r["id"]]["trajectory"], **bi[r["id"]]["outcome"]}.values())
        now = all(ok for ok, _ in {**r["trajectory"], **r["outcome"]}.values())
        (fixed if now and not was else broken if was and not now else []).append(r["id"])
    print(f"aggregate: {b['outcome_rate']:.2f} -> {c['outcome_rate']:.2f}")
    print(f"fixed  ({len(fixed)}): {fixed}")
    print(f"BROKEN ({len(broken)}): {broken}")
    if broken:
        sys.exit(1)
```

**Line by line:**

- **`sys.exit` on a dataset-version mismatch.** Refusing to compare is the correct behaviour and
  almost nobody implements it. A silent comparison across dataset versions is how a team convinces
  itself a refactor improved quality.
- `fixed` and `broken` are **lists of IDs**, and the broken list is the point of the whole day.
  Aggregate first, names second — but the names are what you act on.
- `sys.exit(1)` when anything broke — this script is already CI-shaped, which is deliberate:
  **tomorrow you wire this exact exit code to a PR gate** rather than writing something new.
- Grading happens **locally, before upload**. If LangSmith is down, `run_experiment.py` and
  `compare.py` still work. This is the design rule from §1, made real.

**Pin the baseline today:**

```bash
uv run python days/day-73/lab/run_experiment.py triage-baseline-D73
git add tests/fixtures/experiments/triage-baseline-D73.json
```

Name it with the day. Tomorrow's gate compares against this file, and Day 77's consolidation asks
whether it is still the right baseline.

---

## §5 The tests

```python
# tests/test_dataset.py
import json
import pathlib

import pytest

from mandala.evals.dataset import load, version

pytestmark = pytest.mark.eval_unit
EXPERIMENTS = pathlib.Path("tests/fixtures/experiments")


def test_every_example_has_a_stable_human_readable_id():
    for e in load():
        assert e.id and not e.id.startswith(("uuid", "0x")), e.id


def test_example_ids_are_unique():
    ids = [e.id for e in load()]
    assert len(ids) == len(set(ids))


def test_the_dataset_version_is_deterministic():
    assert version() == version()


def test_the_version_changes_when_an_example_changes(tmp_path, monkeypatch):
    """Flip it: hash only the ids and an edited body slips through unnoticed."""
    before = version()
    monkeypatch.setattr("mandala.evals.dataset.GOLDEN", _copy_with_edit(tmp_path))
    assert version() != before


def test_every_example_has_the_labels_the_outcome_layer_needs():
    for e in load():
        assert "severity" in e.expected, e.id


def test_the_pinned_baseline_exists_and_records_its_dataset_version():
    b = json.loads((EXPERIMENTS / "triage-baseline-D73.json").read_text(encoding="utf-8"))
    assert b["dataset_version"] == version(), "baseline was run against a different dataset"


def test_the_suite_runs_without_langsmith(monkeypatch):
    """The whole point: no network, no key, evals still work."""
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    assert load() and version()


def test_tracing_is_off_by_default():
    example = pathlib.Path(".env.example").read_text(encoding="utf-8")
    assert "LANGSMITH_TRACING=false" in example
```

**Line by line:**

- `test_the_pinned_baseline_exists_and_records_its_dataset_version` is the one that will fail on you
  in three weeks, correctly: you edited a golden example and the baseline is now stale. The fix is to
  **re-run the baseline in its own commit**, and the failing test is what makes you do that rather
  than drift.
- `test_the_suite_runs_without_langsmith` encodes §1's second warning as code. Delete the key, run
  the evals. If this fails, tomorrow's CI gate cannot exist.
- `test_tracing_is_off_by_default` reads `.env.example` — a config default is a security property
  when the thing being sent is customer text.

---

## §6 Traps

- **Letting the service be the source of truth.** Repo → LangSmith, one direction, always.
- **Comparing across dataset versions.** Refuse, loudly.
- **Editing the dataset on the same day as the tooling.** You lose all attribution.
- **UUID example IDs.** "3 regressed" becomes unusable.
- **Aggregates without per-example diffs.** Swaps hide inside a +1.
- **`LANGSMITH_TRACING=true` by default.** Ticket bodies leave your machine without a decision.
- **Uploading examples in a loop.** 429 on your first run.
- **Evaluators that live only in the service.** They become unreviewable and CI can't use them.
- **A baseline nobody re-pins.** Six weeks later it's meaningless, and everyone knows it, and nobody
  says so.
- **Assuming the free tier's cap.** Look it up today and write it in `docs/RATE_BUDGET.md`.

---

## §7 Request budget

**Declared: ~20 model requests (one experiment run) + ~25 LangSmith API calls.**

| What | Requests |
|---|---|
| `tests/test_dataset.py` | **0** |
| `upload_dataset.py` | 0 model · ~2 API |
| `run_experiment.py` (20 golden tickets) | ≤ 20 model |
| Judge on the outcome layer (if enabled) | ≤ 20 (Gemini) |
| `compare.py` | **0** |

**Two budgets now, not one.** LangSmith's free tier has its own monthly ceiling, and it is consumed
by traces, not by model calls. Add a **LangSmith row** to `docs/RATE_BUDGET.md` today with the real
number from their pricing page — Day 75 turns tracing on and will eat it far faster than evals do.

---

## §8 Verify before you code

Written **2026-08-21** against `langsmith==0.11.1`:

- **`client.create_examples()` signature** — parallel lists vs. a list of dicts has changed across
  versions. Verify against the installed package (`uv run python -c "from langsmith import Client; help(Client.create_examples)"`).
- **`list_datasets(dataset_name=...)`** — exact match or prefix? The idempotency check depends on it.
- **Free-tier monthly trace/run cap**, and whether *examples* count against it. Write it into
  `docs/RATE_BUDGET.md`.
- **Does `langsmith` auto-instrument on import**, or only when `LANGSMITH_TRACING=true`? Confirm —
  this is a data-flow question, not a convenience one.
- **Region/data-residency options** on the free tier, and what is stored (inputs? outputs? both?).
- **Does installing `langsmith` change LangChain's default behaviour** in your pinned 1.3.16? It is a
  transitive dependency already; confirm the env var is the only switch.
- `https://docs.smith.langchain.com/evaluation` — read today.

---

## §9 Say it in an interview

> "The thing evals need that scoring alone doesn't give you is history, so I versioned the dataset by
> content hash and every experiment records which version it ran against — and my comparison script
> refuses to run if two experiments used different dataset versions, because comparing across them is
> the most common invalid comparison in eval work. The output I actually act on isn't the aggregate,
> it's the per-example diff: which specific tickets got worse. An aggregate that goes up by one point
> can be four fixes and three breaks, and one of the three is the ticket where the agent stopped
> escalating before a write. The architectural decision I'd defend is direction of truth: the dataset
> and the evaluators live in my repo, and the hosted service holds the history — so if the free tier
> disappears I lose graphs, not ground truth, and my CI gate doesn't depend on a third-party network
> call. I also kept tracing off by default, because turning it on means customer ticket bodies leave
> the machine, and that's a data-flow decision that belongs next to the permission table rather than
> in a logging config."

---

## §10 Done when

```bash
./m check
./m done 73
```
