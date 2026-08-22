---
day: 86
phase: 13
phase_name: "Deployment & interop"
title: "LangGraph Server the $0 way; scaling stateful graphs"
ids: ["LG-20", "LG-21"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-21"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 86 — LangGraph Server the $0 way; scaling stateful graphs

**Phase 13 · Deployment & interop** · IDs: **LG-20 🛠️**, **LG-21 🛠️**

> **Yesterday:** a stateless API and three identical MCP replicas. You classified
> `.state/mandala.sqlite` as *must be external* and deferred it — to today.
> **Today:** the other half. Graphs as APIs — runs, threads, crons, webhooks — via `langgraph dev`
> and a self-hosted container, with the managed Platform as 🅿️ literacy only. Then the tension the
> plan set up deliberately: **a stateless service in front of checkpointer-backed workers.**
> **Tomorrow:** A2A — Mandala talks to a stranger's agent.

```bash
./m start 86
./m scaffold 86
```

---

## §1 The story

Yesterday's rule was "no request may depend on which process handles it". Today you meet the part of
the system where that is impossible: **a durable graph is state, by definition.** Day 82's approval
sits in a checkpoint for hours or days, and something must remember it.

The plan's LG-21 row names the resolution and tells you it is deliberate: *"the
stateless-service-vs-stateful-graph tension: checkpointer-backed workers behind a stateless API —
rhymes with MCP's stateless core on purpose."*

So the architecture, and it is worth drawing on paper before you type:

```
client → [stateless API, N replicas]  → enqueue(run_id)
                                         ↓
                        [workers, M processes] ←→ [checkpointer: ONE shared store]
                                         ↑
              approval CLI / webhook ────┘   (resumes by thread_id, any worker)
```

**The state moved down and out.** Not into a worker's memory — into a store both workers reach. Any
worker can pick up any thread, because the thread's state was never in a process. That is the same
property as yesterday's MCP replicas, achieved differently: MCP had no state to move, the graph moves
its state to a shared store.

One honest sentence to carry into the ADR: **SQLite on a shared local volume is not a production
checkpointer.** It works for M small, it is free, and it is the right choice for this plan. Postgres
is the real answer, and knowing *why* — concurrent writers, locking, connection pooling — is the
literacy part of today. Say which you would use and what would force the switch.

LG-19's managed Platform stays 🅿️ literacy (you wrote that paragraph on Day 76). LG-20 is explicit
that the **local dev server and a self-hosted container** are the hands-on parts.

---

## §2 Setup — run this

Check what `langgraph` 1.2.11 already gives you before adding anything:

```bash
uv run langgraph --help          # is the CLI bundled, or a separate `langgraph-cli` package?
```

If a separate CLI package is needed, **verify and pin it** (Principle 4) and add a row to
`docs/PINS.md`'s ledger for Day 86 — the ledger has no entry for today, which means you are adding a
dependency the plan did not anticipate. That is fine; log it.

```bash
touch langgraph.json
mkdir -p src/mandala/worker deploy
touch src/mandala/worker/__init__.py
touch src/mandala/worker/runner.py
touch src/mandala/worker/queue.py
touch deploy/docker-compose.workers.yml
mkdir -p days/day-86/lab .state/shared
touch days/day-86/lab/two_workers_one_thread.py
touch days/day-86/lab/cron_and_webhook.md
touch tests/test_worker.py
```

---

## §3 LG-20 — the graph as an API

```json
// langgraph.json
{
  "dependencies": ["."],
  "graphs": { "mandala": "./src/mandala/graph/spine.py:build_for_server" },
  "env": ".env"
}
```

```bash
uv run langgraph dev --port 2024
```

**Line by line:**

- `build_for_server` is a **new zero-argument entry point** that constructs the graph and lets the
  server supply the checkpointer. Do not point it at Day 79's `build(checkpointer)` — the server owns
  persistence, and passing your own would give you two checkpointers and a very confusing afternoon.
- `"env": ".env"` loads your keys into the dev server. **Confirm the dev server does not print them
  at startup**, and never run it with `LANGSMITH_TRACING=true` unless you decided that on Day 75.
- The dev server gives you four things worth exploring for ten minutes each, and they map exactly to
  things you built by hand:

| Server concept | You built it on | Keep yours or theirs? |
|---|---|---|
| **thread** | Day 79's `thread_id = run_id` | yours — the run id is your join key |
| **run** | one `invoke` | theirs |
| **cron** | nothing | theirs, for the Day-90 freshness job |
| **webhook** | nothing | theirs, for approval callbacks |

- **Try `interrupt` through the server.** Submit a ticket, watch the run suspend, and resume it via
  the server's API rather than your CLI. It should behave identically to Day 82 — and if it does not,
  you have learned something important about where your approval logic assumed a process.

### 3.1 Crons and webhooks — write down what they replace

In `days/day-86/lab/cron_and_webhook.md`, record two things:

1. **The cron you would schedule**: the weekly freshness check (Principle 13, and Day 90's standing
   habit). Note that a cron in a dev server that is not running is not a cron — this is exactly why
   Day 90 asks you to schedule it somewhere that outlives this repo.
2. **The webhook you would use**: an approval callback, so a human's "approve" from a chat client
   resumes the thread without polling. **Then note the security consequence**: a webhook is an
   unauthenticated network path that resumes a graph. Day 82's `check()` — hash binding, run binding
   — is what makes that survivable, and it is worth realising that you built the defence before you
   built the exposure.

---

## §4 LG-21 — the tension, resolved

```python
# src/mandala/worker/runner.py
"""A worker. Owns no state. Claims a run, executes it against the SHARED checkpointer.

The point: workers are interchangeable. Kill any one mid-run and another finishes
the thread, because the thread's state was never in the worker.
"""

from __future__ import annotations

import os
import time

from langgraph.checkpoint.sqlite import SqliteSaver

from mandala.graph.spine import build
from mandala.obs.tracing import span
from mandala.worker.queue import claim, complete, release

SHARED_DB = os.environ["MANDALA_CHECKPOINT_DB"]        # no default. See below.
WORKER = os.getenv("HOSTNAME", "worker-local")


def work_once() -> bool:
    job = claim(worker=WORKER, lease_seconds=120)
    if job is None:
        return False
    with span("mandala.worker.run", run_id=job.run_id, worker=WORKER):
        try:
            with SqliteSaver.from_conn_string(SHARED_DB) as cp:
                graph = build(cp)
                graph.invoke(None, config={"configurable": {"thread_id": job.run_id}})
        except Exception:
            release(job)                                # lease expires; another worker retries
            raise
        complete(job)
    return True


def loop() -> None:
    while True:
        if not work_once():
            time.sleep(2)
```

**Line by line:**

- **`os.environ[...]` with no default.** A defaulted checkpoint path is how a worker silently uses its
  own container-local SQLite file and appears to work — until the resume lands elsewhere. Crash at
  startup instead. This is the single most important line in the file.
- `graph.invoke(None, ...)` — passing `None` as input means **resume from the checkpoint** rather than
  start fresh. Confirm the exact idiom in 1.2.11 (§8); getting it wrong re-runs the ticket from
  scratch and, post-Day-82, re-enters the approval gate.
- `claim(..., lease_seconds=120)` — a lease, not a lock. **A worker that dies holding a lock blocks
  the thread forever; a worker that dies holding a lease blocks it for two minutes.** That difference
  is the whole reason distributed queues use leases, and it costs you one extra column.
- `release(job)` in `except`, then `raise`. The exception still propagates — the worker crashes loudly
  and the job becomes claimable. **Swallowing it here would give you a silent retry loop**, which,
  after Day 82, is a double-send risk in disguise.
- `worker=WORKER` on the span, so Day 83's report can answer "which worker ran this" — which is the
  first question you will have when two workers disagree.
- Note what the worker does **not** do: no queue of its own, no in-memory job list, no cached graph.
  It builds the graph per job. That is slightly wasteful and entirely correct — a cached graph object
  holding a checkpointer connection across jobs is the exact bug yesterday's AST test was written to
  catch, wearing different clothes.

### 4.1 The two-workers-one-thread drill

```bash
MANDALA_CHECKPOINT_DB=.state/shared/mandala.sqlite uv run python -m mandala.worker.runner &  # worker A
MANDALA_CHECKPOINT_DB=.state/shared/mandala.sqlite uv run python -m mandala.worker.runner &  # worker B
uv run python days/day-86/lab/two_workers_one_thread.py T-9201
```

Then, in `days/day-86/lab/`, write down the answers:

- Which worker started the run? Which finished it after you killed the first mid-node?
- Did the second worker **re-run** the completed node, or resume after it?
- What happened when you ran **both** workers against the same thread simultaneously? (Try it. SQLite
  will tell you something about concurrent writers, and that answer is your Postgres justification.)
- Did any node execute **twice**? Check the trace. **If a write executed twice, stop — that is a
  Phase-12 gate violation and Day 88 cannot pass with it outstanding.**

---

## §5 The eval that must be able to fail

```python
# tests/test_worker.py
import os
import pathlib

import pytest

pytestmark = pytest.mark.eval_trajectory


def test_the_checkpoint_path_has_no_default():
    """Flip it: add a default and a worker silently uses its own local file."""
    src = pathlib.Path("src/mandala/worker/runner.py").read_text(encoding="utf-8")
    assert 'os.environ["MANDALA_CHECKPOINT_DB"]' in src
    assert "getenv(\"MANDALA_CHECKPOINT_DB\"" not in src


def test_the_worker_holds_no_state_between_jobs():
    import ast

    tree = ast.parse(pathlib.Path("src/mandala/worker/runner.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, (ast.Dict, ast.List, ast.Set)):
            pytest.fail(f"module-level mutable at line {node.lineno}")


def test_a_failed_job_is_released_and_reraised():
    src = pathlib.Path("src/mandala/worker/runner.py").read_text(encoding="utf-8")
    assert "release(job)" in src and "raise" in src


def test_jobs_are_leased_not_locked():
    from mandala.worker.queue import claim
    import inspect

    assert "lease_seconds" in inspect.signature(claim).parameters


def test_an_expired_lease_becomes_claimable(tmp_path, monkeypatch):
    """A worker that died must not block the thread forever."""
    from mandala.worker.queue import claim, enqueue

    monkeypatch.setattr("mandala.worker.queue.DB", tmp_path / "q.sqlite")
    enqueue("T-1-a")
    a = claim(worker="A", lease_seconds=0)
    assert a is not None
    b = claim(worker="B", lease_seconds=60)
    assert b is not None and b.run_id == a.run_id


def test_a_live_lease_is_not_stealable(tmp_path, monkeypatch):
    from mandala.worker.queue import claim, enqueue

    monkeypatch.setattr("mandala.worker.queue.DB", tmp_path / "q.sqlite")
    enqueue("T-1-a")
    assert claim(worker="A", lease_seconds=600) is not None
    assert claim(worker="B", lease_seconds=600) is None


def test_the_server_entry_point_does_not_supply_its_own_checkpointer():
    """Two checkpointers is a very confusing afternoon."""
    import inspect

    from mandala.graph.spine import build_for_server

    src = inspect.getsource(build_for_server)
    assert "SqliteSaver" not in src and "MemorySaver" not in src


def test_langgraph_json_points_at_the_server_entry_point():
    import json

    cfg = json.loads(pathlib.Path("langgraph.json").read_text(encoding="utf-8"))
    assert "build_for_server" in cfg["graphs"]["mandala"]


def test_no_memory_saver_anywhere_outside_tests():
    hits = [p for p in pathlib.Path("src").rglob("*.py")
            if "MemorySaver" in p.read_text(encoding="utf-8")]
    assert not hits, f"in-process checkpointer in {hits}"


def test_resume_passes_none_as_input():
    src = pathlib.Path("src/mandala/worker/runner.py").read_text(encoding="utf-8")
    assert "invoke(None" in src, "resuming must not re-supply the original input"
```

**Line by line:**

- `test_the_checkpoint_path_has_no_default` is the day's headline. The failure it prevents — a worker
  quietly using its own file — passes every smoke test and breaks only on a resume that lands
  elsewhere, which is the worst possible discovery timing.
- The lease pair (`expired becomes claimable` / `live is not stealable`) specifies the queue's whole
  contract in six lines. Most hand-rolled job queues get exactly one of these right.
- `test_no_memory_saver_anywhere_outside_tests` catches the most common regression in this
  architecture: someone debugging swaps in `MemorySaver()` and forgets to swap it back.
- `test_resume_passes_none_as_input` guards the idiom that decides whether a resume re-enters the
  approval gate.

---

## §6 Traps

- **A default checkpoint path.** Workers use their own files; resumes land nowhere.
- **A lock instead of a lease.** A dead worker blocks a thread forever.
- **Swallowing a job exception.** Silent retry loop, and now you have writes.
- **Caching the graph across jobs.** Yesterday's bug in new clothes.
- **Two checkpointers** (server's and yours). Very confusing.
- **Re-supplying the original input on resume.** Re-runs the ticket, re-enters the gate.
- **`MemorySaver` left in after debugging.**
- **Treating SQLite-on-a-volume as production.** Say what would force Postgres.
- **A cron in a dev server nobody runs.** Not a cron.
- **A webhook without recalling that it resumes a graph.** Day 82's binding is what saves you.
- **Not checking whether a node ran twice** in the two-worker drill. That is the gate criterion.
- **Adding a CLI dependency without pinning and logging it.** The ledger has no Day-86 row yet.

---

## §7 Request budget

**Declared: ~12 model requests.**

| What | Requests |
|---|---|
| All tests, queue, leases, config | **0** |
| One ticket through `langgraph dev` to the gate | ≤ 6 |
| Two-workers-one-thread drill (partial runs + resumes) | ≤ 6 |

**Watch for accidental double-spend.** If the two-worker drill re-runs a completed node, you will see
it as extra requests before you see it in a trace. **Treat an unexpectedly high count today as a
correctness signal**, not a budgeting annoyance — that is a genuinely useful habit and this is a good
day to form it.

---

## §8 Verify before you code

Written **2026-08-21** against `langgraph==1.2.11`, `langgraph-checkpoint-sqlite==3.1.1`:

- **Is the `langgraph` CLI bundled or separate?** If separate, pin it and add the Day-86 ledger row.
- **`langgraph.json` schema** — key names (`graphs`, `dependencies`, `env`) have changed across
  versions. Verify against the installed CLI's docs, not memory.
- **Resume idiom**: is `invoke(None, config=...)` correct in 1.2.11, and does it differ from
  `Command(resume=...)` after an interrupt? **These are not the same thing** and today's worker needs
  the right one.
- **SQLite concurrent writers** — what does the checkpointer do on contention? Test it deliberately in
  §4.1; the answer is your Postgres argument.
- **Does the dev server print secrets at startup** when `"env": ".env"` is set?
- **Does the dev server enable LangSmith tracing by default?** Day 75 made that a decision, not a
  default.
- **Postgres checkpointer package name and pin**, for the literacy paragraph — you are not installing
  it, but name it correctly.
- `https://docs.langchain.com/oss/python/langgraph/persistence` — read today.

---

## §9 Say it in an interview

> "Yesterday's rule was that no request may depend on which process handles it, and a durable graph is
> the part where that's impossible — an approval can sit in a checkpoint for days, so something has to
> remember. The resolution is a stateless API in front of checkpointer-backed workers: state moved
> down and *out*, into a store every worker reaches, so any worker can pick up any thread because the
> thread's state was never in a process. The line I'd point at is the checkpoint path being read with
> no default — a defaulted path means a worker silently uses its own local file and everything passes
> until a resume lands on a different box, which is the worst possible discovery timing. Jobs are
> leased rather than locked, because a worker that dies holding a lock blocks a thread forever and one
> that dies holding a lease blocks it for two minutes. The drill I actually ran was two workers on one
> thread: kill one mid-node, watch the other finish it, and then check the trace to confirm no node —
> especially no write — executed twice, because that would violate the phase gate I'd just passed. And
> I'd be honest that SQLite on a shared volume isn't a production checkpointer; it's free, it's right
> for this project, and concurrent-writer contention is exactly what would force the move to
> Postgres."

---

## §10 Done when

```bash
./m check
./m done 86
```
