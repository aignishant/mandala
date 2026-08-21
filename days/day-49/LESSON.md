---
day: 49
phase: 7
phase_name: "LangGraph 1.x"
title: "Durable execution and in-graph retry policy"
ids: ["LG-08", "LG-14", "AG-27"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 49 — Durable execution, and retry as graph policy

**Phase 7 · LangGraph 1.x** · IDs: **LG-08 🛠️**, **LG-14 🛠️**, **AG-27 🛠️**

> **Yesterday:** subgraphs with their own schemas, and a supervisor that costs nothing to decide.
> **Today:** what happens when things fail. Node-level timeouts, error recovery, graceful shutdown,
> `DeltaChannel` — and **retry as a property of the graph rather than of your code.** This is where
> AG-27 gets its reference implementation, and where Day 36's `max_retries=0` decision finally gets
> its counterpart.
> **Tomorrow:** interrupts — HITL as a runtime feature.

```bash
./m start 49
./m scaffold 49
```

---

## §1 The story

**AG-27 — durable execution — completes today**, and you have now seen all four implementations the
plan named:

| Implementation | Unit | What survives a crash | Day |
|---|---|---|---|
| CrewAI `@persist` | a step | the flow's state | 32 |
| Agents SDK + Temporal | an activity | the workflow's history | 20 |
| MCP Tasks | a task handle | the task's status | 57 |
| **LangGraph** | **a super-step** | **the whole graph state** | 47, **today** |

Day 47 gave you the storage. Today gives you the **semantics** — which is the harder and more
interesting half:

- What happens when a node raises **mid-super-step**? Do its siblings' updates apply?
- What happens when a node **hangs**? (A free-tier provider under load will do this.)
- Where does **retry** belong, now that the graph can express it?
- What does **graceful shutdown** actually mean for a running graph?

And there is a decision to revisit. On **Day 36 you set `max_retries=0` on every model** and wrote
down why: Day 6's router already owns retries and provider fallback, and two stacked layers silently
multiply your request count. **LangGraph now offers a third place to put retries.** Today you decide,
deliberately, which layer owns what — and the answer is not "none", because a graph-level retry can
do something the router cannot.

---

## §2 Setup — run this

### 2.1 No new packages

```bash
grep -n 'langgraph' pyproject.toml
```

### 2.2 Create today's files

```bash
touch src/mandala/graph/policy.py
touch tests/test_graph_policy.py
mkdir -p days/day-49/lab
touch days/day-49/lab/failure_zoo.py
touch days/day-49/lab/retry_layers.md
```

- `failure_zoo.py` costs **0 requests** — it breaks a graph five different ways with fake nodes and
  prints what survives. **This is the highest-value file of the day**, because failure semantics are
  the one thing you cannot learn from documentation with any confidence.

---

## §3 LG-08 — failure semantics

### 3.1 The five questions, and how to answer them

Do not read the answers anywhere. Run `failure_zoo.py` and write them down.

| # | Question | Why it matters for Mandala |
|---|---|---|
| 1 | A node raises. Do sibling nodes' updates in the same super-step apply? | Day 44's fan-out: does one bad branch lose the other four? |
| 2 | A node raises. Is the *previous* super-step's checkpoint intact? | Day 47's whole resume story rests on it |
| 3 | A node hangs. Is there a timeout, and at what level? | free tiers stall; a hung graph holds a thread forever |
| 4 | The process gets SIGINT mid-super-step. What is written? | "graceful shutdown" is a claim; this is the test |
| 5 | Resume after a raise — does the failed node re-run, or is it skipped? | re-running a node that already spent 5 requests is a budget event |

**Question 1 is the one with real money attached.** A five-way fan-out where one branch's 429 discards
the other four's results costs you four wasted requests every time it happens.

### 3.2 `days/day-49/lab/failure_zoo.py` — 0 model requests

```python
"""Break a graph five ways and record what survives. No models involved.

Run:
    uv run python days/day-49/lab/failure_zoo.py

Budget: 0 requests. Every node here is a fake that raises, hangs, or returns.
"""

import operator
import time
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send


class S(TypedDict, total=False):
    seen: Annotated[list[str], operator.add]
    plan: list[str]


def fan(state):
    return [Send("branch", {"which": w}) for w in state["plan"]]


def branch(state):
    which = state["which"]
    if which == "boom":
        raise RuntimeError("branch exploded")
    if which == "slow":
        time.sleep(30)
    return {"seen": [which]}


def collect(state):
    return {"seen": ["collect"]}


def build():
    g = StateGraph(S)
    g.add_node("branch", branch)
    g.add_node("collect", collect)
    g.add_conditional_edges(START, fan, ["branch"])
    g.add_edge("branch", "collect")
    g.add_edge("collect", END)
    return g.compile(checkpointer=MemorySaver())


graph = build()
cfg = {"configurable": {"thread_id": "zoo-1"}}

print("--- Q1: one branch raises, do the siblings' updates survive? ---")
try:
    graph.invoke({"plan": ["a", "b", "boom", "c"]}, config=cfg)
except Exception as exc:
    print(f"  raised: {type(exc).__name__}: {str(exc)[:60]}")

snapshot = graph.get_state(cfg)
print(f"  state after the failure : {snapshot.values.get('seen')}")
print(f"  next nodes              : {snapshot.next}")

print("\n--- Q5: resume. Does the failed branch re-run? ---")
# TODO(me): remove the poison, resume with invoke(None, config=cfg), and record
# whether 'a', 'b' and 'c' run AGAIN or are skipped. That answer is a budget fact.

print("\n--- Q3: does a hanging node time out? ---")
# TODO(me): run with plan=["slow"] and a node timeout configured. Record the
# parameter name you used and whether it fired.
```

**Line by line:**

- `MemorySaver` — an in-memory checkpointer, so the zoo leaves nothing on disk and runs instantly.
  **Confirm the import path** (§8); this is the third checkpointer package name in two days.
- `branch` raises on one input and sleeps on another — **two failure modes from one fake node**, which
  keeps the file short enough to actually read.
- `graph.get_state(cfg)` **after** catching the exception is the whole experiment. `snapshot.values`
  answers Q1 and `snapshot.next` answers Q2 and Q5.
- `add_conditional_edges(START, fan, ["branch"])` — fanning out directly from `START`, so all branches
  are in one super-step. That is the configuration that makes Q1 meaningful.
- **The two TODOs are the assignment**, and they are deliberately not answered here. Q5's answer is a
  budget fact: if resume re-runs the *whole* super-step, then a five-branch fan-out where branch 3
  fails costs you five requests again on every retry, and **that changes how wide you are willing to
  fan out.** Write the number, not the impression.
- `time.sleep(30)` is a stand-in for a stalled provider. It is not exotic: a free-tier endpoint under
  load holding a connection open is the single most common way an agent run dies quietly.

### 3.3 `src/mandala/graph/policy.py`

```python
"""Failure policy for Mandala's graph: timeouts, retries, and what is fatal.

Day 36 set max_retries=0 on every model because Day 6's router already owns retry
and provider fallback, and two stacked layers silently multiply the request count.
LangGraph offers a THIRD place. The rule we settle on today:

    Layer            Owns                             Why
    -----            ----                             ---
    router (D6)      429s and provider fallback       it knows the rate budget
    graph (D49)      node-level timeouts + ONE retry  it can retry a node, not a call
    node body        nothing                          no bare try/except retry loops

The middle row is the new capability and it is worth having: the router can retry a
CALL, but only the graph can retry a NODE -- meaning the tool lookup, the prompt
assembly and the model call together. For a node whose failure is transient and whose
work is idempotent, that is the right unit.

Usage
-----
    >>> from mandala.graph.policy import NODE_POLICY
    >>> NODE_POLICY["summarise"].max_attempts
    2
"""

from __future__ import annotations

from dataclasses import dataclass

#: Seconds. A free-tier endpoint under load will hold a connection open forever.
DEFAULT_TIMEOUT_S = 45
FANOUT_TIMEOUT_S = 30


@dataclass(frozen=True)
class NodePolicy:
    """What may be retried, how often, and how long it may take."""

    timeout_s: int = DEFAULT_TIMEOUT_S
    max_attempts: int = 1          # 1 = no retry. Retry is opt-in, per node.
    idempotent: bool = True        # a node with side effects must NEVER be retried


NODE_POLICY: dict[str, NodePolicy] = {
    # read-only, cheap, transient failures are common -> one retry
    "search":     NodePolicy(timeout_s=20, max_attempts=2, idempotent=True),
    "summarise":  NodePolicy(timeout_s=FANOUT_TIMEOUT_S, max_attempts=2, idempotent=True),
    "triage":     NodePolicy(timeout_s=DEFAULT_TIMEOUT_S, max_attempts=2, idempotent=True),
    # decisions and side effects -> never retried
    "route":      NodePolicy(timeout_s=5, max_attempts=1, idempotent=True),
    "supervisor": NodePolicy(timeout_s=5, max_attempts=1, idempotent=True),
    "await_approval": NodePolicy(timeout_s=5, max_attempts=1, idempotent=False),
    "post_reply": NodePolicy(timeout_s=30, max_attempts=1, idempotent=False),
}


def retries_for(node: str) -> int:
    """Retry count for a node. Non-idempotent nodes are never retried, ever."""
    policy = NODE_POLICY.get(node, NodePolicy())
    if not policy.idempotent:
        return 0
    return policy.max_attempts - 1
```

**Line by line:**

- `NodePolicy` as a **frozen dataclass with three fields**, and the third one is the important one.
  `timeout_s` and `max_attempts` are ordinary; **`idempotent` is a safety interlock.**
- `retries_for()` returns 0 for anything non-idempotent **regardless of `max_attempts`.** That belt
  is deliberate: someone will eventually set `max_attempts=3` on a node that sends an email, and the
  function refuses rather than trusting the table. **Day 6 (AG-08) established that retries must be
  safe to repeat; this is where that becomes a structural guarantee rather than a habit.**
- `"post_reply": ... idempotent=False` — Mandala's future external write (Day 82). It is in the table
  *before* it exists, marked non-retryable, so the day it is built the policy is already correct.
  **Writing the policy for a component before writing the component is cheap and it is the only time
  you will get it right without an incident first.**
- `"await_approval": idempotent=False` — Day 50's interrupt. Retrying a node that asks a human is
  asking twice.
- `"route"` and `"supervisor"` get **5-second timeouts** because they make no model call. A pure
  function that takes five seconds has hung, and a tight timeout on a fast node turns a mysterious
  stall into an immediate error.
- `FANOUT_TIMEOUT_S = 30` is **shorter than the default** — with five branches in parallel, the
  super-step takes as long as the slowest, so one stalled branch holds the entire fan-out. Fan-out
  nodes should time out sooner than serial ones. **That is a non-obvious consequence of Day 44 and
  it is exactly the kind of thing you only notice by writing the policy down.**
- `max_attempts: int = 1` as the default, with `1` meaning no retry — **retry is opt-in.** The
  opposite default is how systems end up retrying things they should not.
- **Wiring:** LangGraph exposes retry and timeout configuration on `add_node` (a `retry` / `retry_policy`
  argument) and/or at compile time. **Find the actual API (§8) and wire `NODE_POLICY` into it** rather
  than reimplementing retries by hand — a hand-rolled retry inside a node body is the exact thing the
  §3.3 table forbids.

---

## §4 LG-14 — retry as graph policy, and the three-layer decision

### 4.1 `days/day-49/lab/retry_layers.md`

```markdown
# Where retries live in Mandala — decided 2026-08-__

| Layer | Owns | Retries what | Knows the budget? | Visible in a trace? |
|---|---|---|---|---|
| `router.py` (D6) | 429s, provider fallback | one model **call** | **yes** | |
| graph policy (D49) | transient node failure, timeouts | one **node** | no | |
| node body | **nothing** | — | — | — |

## Why the node body owns nothing
<a bare try/except retry loop inside a node is invisible to the graph, invisible to
 the trace, and multiplies with both layers above it>

## What a node retry can do that a call retry cannot
<the tool lookup + prompt assembly + model call, as one unit>

## The multiplication check
router retries R times, graph retries G times -> worst case R x G requests for one node.
With my numbers that is ___ x ___ = ___. Is that acceptable against RATE_BUDGET.md §1?

## The idempotence rule
<why non-idempotent nodes are never retried, and how the interlock enforces it>
```

**The multiplication check is the section that matters.** If Day 6's router retries three times and a
graph node retries twice, one node failing repeatedly costs **six requests**. On OpenRouter's 50 RPD
that is 12% of a day for one stuck node. **Do the arithmetic, decide whether you are comfortable, and
if you are not, lower one of the numbers today** — this is precisely the kind of quiet multiplication
that turns into "why did my quota vanish" at 11pm.

### 4.2 Poison-input quarantine

The plan's LG-14 row names three things: retries as graph policy, fallback edges, and **poison-input
quarantine.** The third is the one nobody builds and it is cheap:

> **A node that fails the same way twice on the same input should not be retried a third time. It
> should route the input somewhere else.**

For Mandala that is a `quarantine` edge: a ticket whose triage node fails twice goes to `escalate`
with a note, rather than retrying forever or crashing the graph. **A ticket that reliably breaks your
pipeline is a support problem, not a systems problem**, and the graph is the right place to make that
call.

```python
def after_triage(state) -> str:
    """Fallback edge: two failures on the same ticket means a human gets it."""
    if state.get("triage_failures", 0) >= 2:
        return "quarantine"
    return "route"
```

- `triage_failures` is incremented by the node's error handler and lives in state, so it **survives a
  checkpoint** — a retry counter in a local variable does not survive the crash it exists for.
- Routing to `quarantine` rather than raising keeps the run alive and auditable. Compare crashing:
  you lose the state and learn nothing about *which* tickets break.
- **This closes a loop from Day 31**, where you added `guard_progress` and wrote "routers loop". A
  quarantine edge is what a loop bound should *do* when it trips, rather than merely raising.

---

## §5 The eval that must be able to fail

### `tests/test_graph_policy.py`

```python
"""Retry policy is a budget decision with a safety interlock. 0 model requests."""

import pytest

from mandala.graph.policy import (
    DEFAULT_TIMEOUT_S,
    FANOUT_TIMEOUT_S,
    NODE_POLICY,
    NodePolicy,
    retries_for,
)


def test_non_idempotent_nodes_are_never_retried():
    """THE interlock. Flip it: return max_attempts-1 unconditionally and this goes red."""
    for name, policy in NODE_POLICY.items():
        if not policy.idempotent:
            assert retries_for(name) == 0, name


def test_a_side_effecting_node_stays_non_idempotent():
    """post_reply is Mandala's first external write (Day 82). It must not be retried."""
    assert NODE_POLICY["post_reply"].idempotent is False
    assert retries_for("post_reply") == 0


def test_the_approval_node_is_not_retryable():
    """Retrying a node that asks a human is asking twice."""
    assert retries_for("await_approval") == 0


def test_an_unknown_node_gets_the_safe_default():
    assert retries_for("a_node_added_next_week") == 0


def test_retry_is_opt_in():
    assert NodePolicy().max_attempts == 1


def test_every_node_has_a_timeout():
    for name, policy in NODE_POLICY.items():
        assert 0 < policy.timeout_s <= 120, name


def test_pure_nodes_time_out_fast():
    """A routing function taking 5s has hung. Tight timeouts turn stalls into errors."""
    for name in ("route", "supervisor"):
        assert NODE_POLICY[name].timeout_s <= 10, name


def test_fanout_nodes_time_out_sooner_than_serial_ones():
    """Day 44's consequence: one stalled branch holds the whole super-step."""
    assert FANOUT_TIMEOUT_S < DEFAULT_TIMEOUT_S


def test_the_worst_case_multiplication_is_bounded():
    """router retries x graph retries. Flip it: raise either and watch this go red."""
    from mandala.router import MAX_ATTEMPTS as ROUTER_ATTEMPTS

    worst = max(p.max_attempts for p in NODE_POLICY.values()) * ROUTER_ATTEMPTS
    assert worst <= 6, f"one stuck node could cost {worst} requests"


def test_the_policy_covers_every_node_in_the_graph():
    """A node with no policy silently gets the default. Make that a deliberate choice."""
    from mandala.graph.nodes import build_graph

    nodes = set(build_graph().get_graph().nodes) - {"__start__", "__end__"}
    missing = nodes - set(NODE_POLICY)
    assert missing == set(), missing


def test_no_node_body_retries_by_hand():
    """Grep-as-a-test: retries live in the policy, not in try/except loops."""
    from pathlib import Path

    source = Path("src/mandala/graph/nodes.py").read_text(encoding="utf-8")
    assert "for attempt in range" not in source
    assert "while True" not in source
```

**Line by line:**

- `test_non_idempotent_nodes_are_never_retried` is today's headline flip-it test, and the mutation
  named in the docstring is the obvious "simplification" someone will make.
- `test_a_side_effecting_node_stays_non_idempotent` pins a policy for a node **that does not exist
  yet.** That is unusual and it is the point: Day 82 will build `post_reply`, and this test means the
  policy is already there and already right.
- `test_an_unknown_node_gets_the_safe_default` — a node added next week gets **zero retries**, not
  the default `NodePolicy()`'s implied one. Read `retries_for` again: `NodePolicy()` has
  `max_attempts=1`, so `retries_for` returns 0. **Fail closed.**
- `test_the_worst_case_multiplication_is_bounded` imports the router's own attempt count and asserts
  the product. **This is §4.1's arithmetic as a test**, and it is the single best guard against the
  quiet-multiplication failure mode. If `router.MAX_ATTEMPTS` is not exported, export it today.
- `test_the_policy_covers_every_node_in_the_graph` walks the actual compiled graph. **A cross-file
  invariant**: add a node without a policy and a test tells you, rather than the node silently
  inheriting a default nobody chose.
- `test_no_node_body_retries_by_hand` is the grep test enforcing §4.1's third row. Sixth or seventh
  appearance of grep-as-a-test in this plan; it is a house pattern now.

---

## §6 Traps

- **Reading the failure semantics instead of running them.** `failure_zoo.py` is the only reliable
  source, and it costs nothing.
- **Not answering Q5.** Whether resume re-runs a whole super-step is a budget fact that changes how
  wide you fan out.
- **Retrying a non-idempotent node.** Two emails. The interlock exists because this happens.
- **Stacking retries without doing the multiplication.** R × G requests for one stuck node.
- **A `try/except` retry loop inside a node body.** Invisible to the graph, invisible to the trace,
  and it multiplies with both layers above it.
- **No timeout on a fast node.** A five-second router has hung and you will spend an hour finding it.
- **The same timeout for serial and fan-out nodes.** One stalled branch holds the whole super-step.
- **A retry counter in a local variable.** It does not survive the crash it exists for. Put it in
  state.
- **Crashing on poison input instead of quarantining.** You lose the state and learn nothing about
  which tickets break.
- **Deleting `max_retries=0` from Day 36** because "the graph handles retries now". Now you have two
  layers again, and the trace still lies about the request count.

---

## §7 Request budget

**Declared: ~8 model requests, Groq.**

| What | Requests |
|---|---|
| `failure_zoo.py` (all fakes) | **0** |
| `tests/test_graph_policy.py` | **0** |
| One real run with a forced transient failure, to watch a retry happen | ≤ 8 |

**Do the real run once, with the retry deliberately triggered.** Force it by pointing one node at a
nonexistent model id for a single attempt — a `NotFoundError` is transient-looking, cheap, and it
proves the wiring without burning a real 429. Then **count the requests in the trace and check the
number against §4.1's multiplication.** A retry policy you have never watched fire is a retry policy
you do not have.

---

## §8 Verify before you code

Written **2026-08-20** against `langgraph==1.2.11`. Part 2 of the plan names node-level
timeouts, error recovery and graceful shutdown as **1.2 features**, so all of this is recent surface:

- **The retry API** — is it `add_node(..., retry=RetryPolicy(...))`, `retry_policy=`, or a compile-time
  setting? Find the real name and wire `NODE_POLICY` into it.
- **`RetryPolicy` fields** — max attempts, backoff, and **which exception types are retried**. That
  last one matters: retrying a `ValidationError` is pointless, retrying a timeout is not.
- **The timeout API** — per node, per graph, or both? Is it wall-clock or per-attempt?
- **Q1's answer:** does a raising node discard sibling updates in the same super-step?
- **Q5's answer:** on resume, does the failed node re-run alone, or does the whole super-step re-run?
- **Graceful shutdown** — what does it actually do on SIGINT, and is there an API to request it?
- **`DeltaChannel`** — Day 47 asked; today it matters more, because a long retry loop on a long thread
  is exactly the case it exists for. Automatic or opt-in?
- **`MemorySaver` import path** — `langgraph.checkpoint.memory` is the assumption.
- `https://docs.langchain.com/oss/python/langgraph/durable-execution` — read today.

---

## §9 Say it in an interview

> "Retries end up in three places and the whole job is deciding which layer owns what. My provider
> router owns 429s and cross-provider fallback because it's the only layer that knows the rate budget.
> The graph owns node-level timeouts and at most one retry, because it can retry a *node* — the tool
> lookup, the prompt assembly and the model call as one unit — which a call-level retry can't. And
> node bodies own nothing: a bare try/except loop inside a node is invisible to the graph and to the
> trace, and it multiplies with both layers above it. I did that multiplication explicitly — router
> attempts times graph attempts is the worst-case request cost of one stuck node — and there's a test
> asserting the product stays bounded, because that's the kind of thing that quietly eats a day's
> quota. The interlock I'd point at is that every node declares whether it's idempotent, and the
> retry function returns zero for anything that isn't, regardless of what the table says — so the day
> someone sets three attempts on the node that sends a customer email, it still doesn't retry. And
> the piece nobody builds is quarantine: a ticket that fails the same way twice routes to a human
> instead of retrying forever, because a ticket that reliably breaks your pipeline is a support
> problem, not a systems problem."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 49
```
