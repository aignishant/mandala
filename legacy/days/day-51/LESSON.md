---
day: 51
phase: 7
phase_name: "LangGraph 1.x"
title: "Time travel, forking, and the Functional API"
ids: ["LG-10", "LG-16"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 51 — Time travel, forking, and the Functional API

**Phase 7 · LangGraph 1.x** · IDs: **LG-10 🛠️**, **LG-16 🅿️+lab-lite**

> **Yesterday:** a durable pause that costs nothing to wait on, and the accountability record that no
> framework supplies.
> **Today:** the capability that only exists because every super-step was checkpointed. **Rewind to
> any point in a past run, change the state, and re-run from there** — replay yesterday's bad triage
> with a fixed prompt, on the same inputs, for free. Then the Functional API, which asks whether you
> needed to draw a graph at all.
> **Tomorrow:** the Phase-7 gate.

```bash
./m start 51
./m scaffold 51
```

---

## §1 The story

Here is the problem time travel solves, and it is a problem you have had for weeks.

You change a prompt. Did it help? The honest way to find out is to run the *same* ticket through the
*same* pipeline with only the prompt changed. But a re-run from scratch costs eleven requests, and
the model is nondeterministic even at `temperature=0`, so some of what you see is noise rather than
your change.

**Time travel gives you the surgical version:** rewind to the checkpoint *just before* the triage
node, swap the prompt, and re-run only from there. Everything upstream is replayed from the
checkpoint at zero cost. **You are comparing one node's behaviour, not two whole runs.**

That is a debugging tool, and it is also something more useful: it is the mechanism behind **Day 73's
experiments** and **Day 51 → Day 74's regression gate**. A system where you can re-run any past
execution from any point, with one thing changed, is a system where "did that change help?" has an
answer instead of an opinion.

**It exists only because of Day 47.** Every super-step wrote a checkpoint; the history is those
checkpoints in order. Nothing here is a separate feature — **time travel is what a complete
checkpoint history lets you do**, which is worth saying because it reframes Day 47's cost as an
investment rather than an overhead.

LG-16 is 🅿️+lab-lite and asks an uncomfortable question: `@entrypoint` / `@task` give you
checkpointing, durability and interrupts **without drawing a graph at all.** Port one small thing and
find out what the graph was buying you.

---

## §2 Setup — run this

### 2.1 No new packages

```bash
grep -n 'langgraph' pyproject.toml
```

### 2.2 Create today's files

```bash
touch src/mandala/graph/timetravel.py
touch tests/test_timetravel.py
mkdir -p days/day-51/lab
touch days/day-51/lab/history.py
touch days/day-51/lab/fork_and_compare.py
touch days/day-51/lab/functional_port.py
touch days/day-51/lab/functional_compare.md
```

- You need **a completed run in the store** before any of this works. Re-run Day 50's
  `pause_resume.py` start-and-approve if `.mandala/graph/` is empty. Today reads history; it does not
  create much.

---

## §3 LG-10 — time travel

### 3.1 The three operations

| Operation | Call | What it gives you |
|---|---|---|
| **List history** | `graph.get_state_history(config)` | every checkpoint, newest first |
| **Rewind** | `graph.invoke(None, config={... "checkpoint_id": …})` | re-run from that point |
| **Fork** | `graph.update_state(config, values, as_node=…)` then invoke | a *new* branch of history |

**Rewind and fork are different and the difference matters.** Rewinding re-runs from a past
checkpoint. Forking first *changes the state* at that checkpoint and then re-runs — creating a second
branch, so the original history is not destroyed. **You always want fork**, because a debugging tool
that overwrites the evidence is not a debugging tool.

### 3.2 `days/day-51/lab/history.py` — 0 model requests

Look at the history before you use it.

```python
"""Print the checkpoint history of a past run. Read before you rewind.

Run:
    uv run python days/day-51/lab/history.py T-9002 a1

Budget: 0 requests. Reading history costs nothing.
"""

import sys

from mandala.graph.nodes import build_graph
from mandala.graph.persistence import checkpointer, thread_id

ticket, attempt = sys.argv[1], sys.argv[2]
config = {"configurable": {"thread_id": thread_id(ticket, attempt)}}

with checkpointer() as saver:
    graph = build_graph().compile(checkpointer=saver)

    print(f"{'checkpoint_id':<38} {'next':<24} {'stage':<12} keys")
    for snap in graph.get_state_history(config):
        cid = snap.config["configurable"].get("checkpoint_id", "?")
        nxt = ",".join(snap.next) or "(end)"
        stage = snap.values.get("stage", "-")
        keys = ",".join(sorted(k for k in snap.values if snap.values[k])) [:60]
        print(f"{cid:<38} {nxt:<24} {stage:<12} {keys}")
```

**Line by line:**

- `get_state_history(config)` yields snapshots **newest first**. Each one is a complete state plus the
  metadata needed to resume from it.
- `snap.config["configurable"]["checkpoint_id"]` — **this is the address you rewind to.** Printing it
  is the whole reason for the file; you cannot fork to a checkpoint whose id you do not have.
- `snap.next` — which nodes were about to run at that point. **This is how you find the checkpoint
  you want:** to re-run triage, you want the snapshot whose `next` contains `triage`.
- `snap.values.get("stage")` and the non-empty key list give you a human-readable sense of what the
  state contained then. Watching `findings` appear and `ticket_body` disappear as you read down the
  list is Day 47's scrub node, visible as history.
- **Count the snapshots.** One per super-step, so a run with a fan-out has fewer than you might guess
  (Day 47 §3.1). If the count surprises you, your model of super-steps is off and this is a cheap way
  to find that out.

### 3.3 `src/mandala/graph/timetravel.py`

```python
"""Fork a past run at a chosen point. The tool behind 'did that change help?'.

This exists because Day 47 checkpointed every super-step. Time travel is not a
separate feature -- it is what a complete history lets you do, which is why the
checkpointing cost was an investment rather than an overhead.

Design rule: FORK, never overwrite. A debugging tool that destroys the evidence is
not a debugging tool. update_state() creates a new branch; the original history
stays readable.

Usage
-----
    >>> cid = checkpoint_before(graph, config, node="triage")
    >>> fork(graph, config, cid, {"severity": "critical"})   # doctest: +SKIP
"""

from __future__ import annotations


def checkpoint_before(graph, config, *, node: str) -> str:
    """Find the checkpoint id at which `node` was about to run. Newest match wins."""
    for snap in graph.get_state_history(config):
        if node in snap.next:
            return snap.config["configurable"]["checkpoint_id"]
    raise LookupError(f"no checkpoint found where {node!r} was next")


def fork(graph, config, checkpoint_id: str, values: dict | None = None, *, as_node: str | None = None):
    """Branch history at `checkpoint_id`, optionally editing state, then re-run.

    Returns the final state of the NEW branch. The original branch is untouched
    and still readable via get_state_history().
    """
    at = {"configurable": {**config["configurable"], "checkpoint_id": checkpoint_id}}
    if values:
        at = graph.update_state(at, values, as_node=as_node)
    return graph.invoke(None, config=at)
```

**Line by line:**

- `checkpoint_before(graph, config, node=...)` — **finding the checkpoint by *what was about to run*
  rather than by index.** Indices shift the moment the graph changes; "the checkpoint where triage
  was next" is stable and readable. This function is eight lines and it is the difference between
  time travel being usable and being a party trick.
- **Newest match wins**, because history is newest-first and a node may have run several times in a
  looping graph. Document that choice; "the most recent time triage was about to run" is usually what
  you mean, and when it is not you want to know the rule.
- `raise LookupError` with the node name — a missing checkpoint is a programmer error (wrong node
  name, wrong thread), not a normal outcome. Day 32's distinction, again.
- `at = {"configurable": {**config["configurable"], "checkpoint_id": ...}}` — **spread the existing
  configurable and add the checkpoint id.** Dropping `thread_id` here is the most common mistake and
  it produces a confusing "no such checkpoint" rather than an obvious error.
- `graph.update_state(at, values, as_node=...)` — **this is the fork.** It writes a *new* checkpoint
  whose parent is the one you named, and returns a config pointing at it. `as_node` tells the runtime
  which node the update should be attributed to, which matters because reducers are applied as if
  that node had written the values. **Get `as_node` wrong and your update goes through the wrong
  reducer** — with `keep_first` on `ticket_body`, an update attributed to the wrong node may silently
  do nothing.
- `graph.invoke(None, config=at)` — resume from the forked point. `None` because state comes from the
  checkpoint (Day 47's API, reused).
- **`values` is optional.** With no values it is a pure re-run from that point — useful for "was that
  failure deterministic?", which is a question you will ask on Day 69's red-team day.

### 3.4 `days/day-51/lab/fork_and_compare.py`

```python
"""Re-run one node with one thing changed. The 'did that help?' tool.

Run:
    uv run python days/day-51/lab/fork_and_compare.py T-9002 a1

Budget: ~4 requests -- only the nodes from the fork point onward re-run.
"""

import sys

from mandala.graph.nodes import build_graph
from mandala.graph.persistence import checkpointer, thread_id
from mandala.graph.timetravel import checkpoint_before, fork

ticket, attempt = sys.argv[1], sys.argv[2]
config = {"configurable": {"thread_id": thread_id(ticket, attempt)}}

with checkpointer() as saver:
    graph = build_graph().compile(checkpointer=saver)

    original = graph.get_state(config).values
    print(f"original  severity={original.get('severity')!r} "
          f"findings={len(original.get('findings', []))}")

    cid = checkpoint_before(graph, config, node="route")
    print(f"forking at {cid} (route was next)")

    branch = fork(graph, config, cid, {"severity": "critical"}, as_node="triage")
    print(f"forked    severity={branch.get('severity')!r} "
          f"stage={branch.get('stage')!r} notes={branch.get('notes')[-2:]}")

    print("\n--- original history is still intact ---")
    print(f"snapshots now: {sum(1 for _ in graph.get_state_history(config))}")
```

**Line by line:**

- Forking at **"where `route` was next"** with `severity="critical"` is a deliberately clean
  experiment: it tests Day 44's routing policy on a real past run, without re-running triage and
  without paying for it. **You should see the branch escalate.**
- `as_node="triage"` — attributing the change to the node that would legitimately have written
  `severity`. **Here is where yesterday's reducer knowledge pays**: `severity` uses
  `take_max_severity`, so writing `"critical"` merges to `"critical"` regardless of order. Try
  writing `"low"` instead and watch the reducer refuse to downgrade — **that is your Day-43
  commutativity work defending you inside a debugging tool**, which is a genuinely satisfying thing
  to observe.
- The final snapshot count proves **the original history survived**. Forking added checkpoints; it
  destroyed nothing.
- `~4 requests` because only `route` onward re-runs. Compare a full re-run at ~11. **That ratio is the
  cost argument for time travel** and it belongs in the ledger.

---

## §4 LG-16 — the Functional API

### 4.1 The uncomfortable question

```python
from langgraph.func import entrypoint, task


@task
def classify(ticket_body: str) -> dict:
    ...


@entrypoint(checkpointer=saver)
def triage(payload: dict) -> dict:
    triage = classify(payload["ticket_body"]).result()
    findings = research(triage).result()
    return {"triage": triage, "findings": findings}
```

**That gets checkpointing, durability, retries and interrupts — with no graph, no state schema, and
no reducers.** It is ordinary Python with two decorators.

So: **what was the graph buying you?**

### 4.2 `days/day-51/lab/functional_port.py`

Port the **triage → route → lane** slice. That is all — one small piece you can finish.

```python
"""The same slice, written as functions instead of a graph.

Run:
    uv run python days/day-51/lab/functional_port.py T-9002

Budget: <= 6 requests. Port a SLICE, not the system.
"""

import sys

from langgraph.func import entrypoint, task

from mandala.graph.persistence import checkpointer
from mandala.graph.routing import choose_lane
from mandala.sdk_tools import RAW_TICKETS


@task
def classify(ticket_body: str):
    # TODO(me): reuse the SAME triage agent. If you rewrite it here, the comparison is void.
    raise NotImplementedError("wire the Day-38 agent, then delete this line")


with checkpointer() as saver:

    @entrypoint(checkpointer=saver)
    def triage_flow(payload: dict) -> dict:
        triage = classify(payload["ticket_body"]).result()
        lane = choose_lane({"triage": triage})
        return {"triage": triage, "lane": lane}

    ticket = sys.argv[1] if len(sys.argv) > 1 else "T-9002"
    cfg = {"configurable": {"thread_id": f"func-{ticket}"}}
    print(triage_flow.invoke({"ticket_body": RAW_TICKETS[ticket]["body"]}, config=cfg))
```

**Line by line:**

- `@task` marks a **checkpointed unit of work**; `.result()` waits for it. Calling two tasks before
  awaiting either gives you parallelism — **that is this API's answer to `Send`**, and it is arguably
  more natural to read.
- `choose_lane` **imported unchanged from `routing.py`.** The routing policy does not care which API
  drives it, which is the same finding as every other portability observation in this plan. Note that
  `choose_lane` has now been reused across a graph and a functional entrypoint without modification.
- `@entrypoint(checkpointer=saver)` — durability, declared once. **Same checkpointer, same store.** Go
  and look: the functional run's checkpoints land in `.mandala/graph/` beside the graph runs, which
  tells you these are two front-ends over one runtime.
- The `TODO` insisting you reuse the same agent is the integrity of the comparison. Rewriting it here
  would measure your rewrite, not the API.
- **What is conspicuously absent:** no `StateGraph`, no `TypedDict`, no reducers, no `add_edge`. The
  control flow is `if`/`await`/`return`.

### 4.3 `days/day-51/lab/functional_compare.md`

```markdown
# Graph API vs. Functional API — Mandala, 2026-08-__

Ported: triage -> route -> lane. Not ported: the Research subgraph, the approval gate, the fan-out.

| | Graph API | Functional API |
|---|---|---|
| Lines for the slice | | |
| Checkpointing | yes | yes |
| Durable interrupts | yes | ? |
| Parallelism | `Send` | call, then `.result()` |
| Can I DRAW it before running? | **yes** | |
| Can a reviewer see every branch? | | |
| State is | a typed schema with reducers | local variables |
| Concurrent writes to one field | reducers decide | ? |
| Where a subgraph fits | a node | a function call |
| Time travel to an arbitrary point | | |

## What the graph was actually buying me
<be specific -- and note that "I can draw it" appeared in Day 34's DSL comparison too>

## Where I would use the Functional API
<one paragraph. Hint: the shape of the workflow, not the size>

## The one that surprised me
```

**"Can I draw it?" is the row that recurs.** Day 34 compared code-vs-data orchestration and concluded
that the strongest argument for declarative structure is **who can safely read it**. Today the same
row appears between two APIs of the same library. **When a criterion shows up twice, in different
comparisons, it is probably the criterion that matters** — and that is a genuinely useful thing to
have noticed by Day 63.

Do not conclude "the graph is better". A linear workflow with no branching, no fan-out and no
supervisor is **worse** as a graph: you have written twenty lines of wiring to express what four
lines of Python said. **The honest answer is about the shape of the workflow, not the size.**

---

## §5 The eval that must be able to fail

### `tests/test_timetravel.py`

```python
"""Forking must never destroy history. 0 model requests -- fake snapshots."""

from dataclasses import dataclass, field

import pytest

from mandala.graph.timetravel import checkpoint_before, fork


@dataclass
class Snap:
    next: tuple
    checkpoint_id: str
    values: dict = field(default_factory=dict)

    @property
    def config(self):
        return {"configurable": {"thread_id": "t", "checkpoint_id": self.checkpoint_id}}


class FakeGraph:
    def __init__(self, snaps):
        self.snaps = snaps
        self.updated_with = None
        self.invoked_with = None

    def get_state_history(self, config):
        return iter(self.snaps)

    def update_state(self, config, values, as_node=None):
        self.updated_with = (config, values, as_node)
        return {"configurable": {**config["configurable"], "checkpoint_id": "forked-1"}}

    def invoke(self, payload, config=None):
        self.invoked_with = (payload, config)
        return {"stage": "escalated"}


CONFIG = {"configurable": {"thread_id": "T-9002:a1"}}
SNAPS = [
    Snap(next=(), checkpoint_id="c4"),
    Snap(next=("finish",), checkpoint_id="c3"),
    Snap(next=("route",), checkpoint_id="c2"),
    Snap(next=("triage",), checkpoint_id="c1"),
]


def test_finds_the_checkpoint_where_a_node_was_next():
    assert checkpoint_before(FakeGraph(SNAPS), CONFIG, node="route") == "c2"


def test_the_newest_match_wins():
    """A looping graph runs a node several times. Document the rule with a test."""
    snaps = [Snap(next=("route",), checkpoint_id="new"),
             Snap(next=("route",), checkpoint_id="old")]
    assert checkpoint_before(FakeGraph(snaps), CONFIG, node="route") == "new"


def test_a_missing_node_raises_with_its_name():
    with pytest.raises(LookupError, match="nope"):
        checkpoint_before(FakeGraph(SNAPS), CONFIG, node="nope")


def test_forking_preserves_the_thread_id():
    """THE bug. Flip it: build the config from scratch and watch this go red."""
    g = FakeGraph(SNAPS)
    fork(g, CONFIG, "c2", {"severity": "critical"}, as_node="triage")
    sent_config, _, _ = g.updated_with
    assert sent_config["configurable"]["thread_id"] == "T-9002:a1"
    assert sent_config["configurable"]["checkpoint_id"] == "c2"


def test_forking_passes_as_node_through():
    """Wrong as_node means the update goes through the wrong reducer."""
    g = FakeGraph(SNAPS)
    fork(g, CONFIG, "c2", {"severity": "critical"}, as_node="triage")
    assert g.updated_with[2] == "triage"


def test_forking_without_values_is_a_pure_rerun():
    g = FakeGraph(SNAPS)
    fork(g, CONFIG, "c2")
    assert g.updated_with is None, "update_state called with no values to write"
    assert g.invoked_with[0] is None


def test_resume_passes_none_as_input():
    g = FakeGraph(SNAPS)
    fork(g, CONFIG, "c2", {"severity": "critical"})
    assert g.invoked_with[0] is None, "state must come from the checkpoint, not the input"


def test_the_severity_reducer_still_protects_a_fork():
    """A fork writes through the reducers. Downgrading a critical must not work."""
    from mandala.graph.state import take_max_severity

    assert take_max_severity("critical", "low") == "critical"
```

**Line by line:**

- `FakeGraph` and `Snap` — **twenty lines that replace LangGraph, a checkpointer and a completed
  run.** Sixth day running that the framework is a fixture. Note that the fake also *records* what it
  was called with, which is how you test a function whose whole job is to call something correctly.
- `test_the_newest_match_wins` documents the §3.3 tie-break rule. **A rule stated only in a docstring
  is a rule that drifts**; a test pins it.
- `test_forking_preserves_the_thread_id` is today's flip-it test and it names the exact bug: building
  a fresh config instead of spreading the existing one. The failure mode is a confusing "no such
  checkpoint", which is much harder to diagnose than a red test.
- `test_forking_passes_as_node_through` guards the reducer-attribution trap from §3.3.
- `test_forking_without_values_is_a_pure_rerun` asserts `update_state` is **not** called when there is
  nothing to write. Otherwise a pure re-run would create a pointless fork and pollute the history you
  came to read.
- `test_the_severity_reducer_still_protects_a_fork` connects Day 43 to Day 51 in one assertion: **your
  reducers defend you even when you are the one editing state by hand.** That is a nice property and
  it is worth a test to notice it.

---

## §6 Traps

- **Rewinding instead of forking.** You overwrite the evidence you came to look at.
- **Dropping `thread_id` when building the checkpoint config.** Confusing "no such checkpoint".
- **The wrong `as_node`.** Your edit goes through the wrong reducer and may silently do nothing.
- **Locating a checkpoint by index.** Indices shift; `next` does not.
- **Forgetting `invoke(None)`.** Passing state re-seeds the run instead of resuming it.
- **Assuming one checkpoint per node.** It is one per super-step; a fan-out is one.
- **Concluding a change helped from one forked run.** The model is still nondeterministic. Fork three
  times, or wait for Day 73's experiments — and know that this is a *cheaper* comparison, not a
  *rigorous* one.
- **Porting the whole system to the Functional API.** A slice, and finish it.
- **Rewriting the agent inside the functional port.** Then you are measuring your rewrite.
- **Concluding "the graph is better".** For a linear workflow it is twenty lines of wiring for
  nothing.

---

## §7 Request budget

**Declared: ~10 model requests, Groq.**

| What | Requests |
|---|---|
| `history.py` | **0** |
| `tests/test_timetravel.py` | **0** |
| `fork_and_compare.py` | ~4 |
| `functional_port.py` | ≤ 6 |

**Record the fork cost against the full-run cost** (≈4 vs. ≈11). That ratio is the reason time travel
matters on a free tier: **it makes "did that change help?" cost a third of what it used to.** Over the
forty days remaining, that is a real budget line, not a nicety.

---

## §8 Verify before you code

Written **2026-08-20** against `langgraph==1.2.11`:

- **`get_state_history` ordering** — newest first? §3.3's tie-break assumes so.
- **The snapshot shape** — `.next`, `.values`, `.config["configurable"]["checkpoint_id"]`. Three
  attribute assumptions in one file; verify all three.
- **`update_state` return value** — does it return a config pointing at the new checkpoint? §3.3
  depends on it.
- **`as_node` semantics** — does the update genuinely go through that node's reducers? **Test it:**
  fork with `severity="low"` attributed to `triage` and confirm `take_max_severity` refuses the
  downgrade. That experiment answers the question definitively.
- **Does forking create a new branch or move the thread's head?** The entire "history survives" claim
  rests on this. Prove it with the snapshot count.
- **`langgraph.func` import path**, and `@entrypoint` / `@task` signatures.
- **Do interrupts work in the Functional API?** A row in §4.3's table, and it matters for whether the
  API is a real alternative or a subset.
- **Do the two APIs share a checkpoint store cleanly?** §4.2 puts them in the same database.
- `https://docs.langchain.com/oss/python/langgraph/time-travel` — read today.

---

## §9 Say it in an interview

> "Because every super-step is checkpointed, I can list the history of a past run, find the
> checkpoint where a particular node was about to execute, edit the state there, and re-run from that
> point — so 'did that prompt change help?' costs about four requests instead of eleven, and I'm
> comparing one node's behaviour rather than two whole nondeterministic runs. I always fork rather
> than rewind, because a debugging tool that overwrites the evidence isn't one, and there's a test
> asserting the original history survives. Two details are easy to get wrong: you locate the
> checkpoint by *which node was next*, not by index, because indices shift when the graph changes;
> and you have to attribute the edit to a node, because the update goes through that node's reducer —
> which I proved by forking with a lower severity and watching my fail-safe merge refuse the
> downgrade. That was satisfying: the concurrency policy I'd written for parallel branches also
> defended me when I was the one editing state by hand. I also ported a slice to the Functional API,
> which gets checkpointing and durability from two decorators with no graph at all — and the honest
> conclusion is that the graph earns its wiring when there's branching, fan-out or a supervisor, and
> costs you twenty lines for nothing when the workflow is linear."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 51
```
