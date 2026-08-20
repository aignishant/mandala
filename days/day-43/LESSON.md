---
day: 43
phase: 7
phase_name: "LangGraph 1.x"
title: "Graph thinking: state, nodes, edges, reducers"
ids: ["LG-01", "LG-02"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 43 — Graph thinking: state, nodes, edges, reducers

**Phase 7 · LangGraph 1.x** · IDs: **LG-01 🛠️**, **LG-02 🛠️**

> **Yesterday:** the Phase-6 gate. You built a `StateGraph` with three nodes, one of which was an
> entire LangChain agent — and you noticed `notes` clobbering itself.
> **Today:** that clobbering is the lesson. Nodes, edges, and **reducers** — the piece that makes
> graph state something other than a shared mutable dict. Plus the deliberate comparison the plan has
> been setting up for thirteen days: LangGraph state vs. CrewAI flow state.
> **Tomorrow:** conditional edges, `Command`, and the Send API.

```bash
./m start 43
./m scaffold 43
```

---

## §1 The story

The plan's thesis, one more time: *who owns the loop?* Three answers so far — the model (SDK), roles
(Crews), you-in-decorators (Flows). LangGraph's answer is the most literal: **you own it, and you
draw it.**

You have already met the pieces:

| Piece | Where you met it |
|---|---|
| a typed state object | Day 30, `MandalaState` (CrewAI flow state) |
| steps as functions over state | Day 30, `@start` / `@listen` |
| an agent as one step | Day 31 (`organs.py`), Day 42 (`triage_node`) |
| a `StateGraph` with nodes and edges | Day 42, §3.2 |

**So Phase 7 does not start from zero, and that is by design.** The plan's CR-15 row said, thirteen
days ago, *"mirrors LangGraph state, Day 43 — compare deliberately."* Day 30's checklist made you
start a comparison table with the CrewAI column filled in. **Go and get that table now**, before you
read further. Today you fill in the second column, and comparing what you predicted against what is
actually here is worth more than reading either.

The one genuinely new idea today is the **reducer**, and yesterday handed you the motivation on a
plate: `notes: list[str]` in `WorkflowState` replaced instead of appending, so the second node's note
wiped out the first's. A reducer is the answer, and understanding it properly explains why LangGraph
can do things — parallel branches, durable resume, time travel — that Day 30's global mutable state
never could.

---

## §2 Setup — run this

### 2.1 Already pinned — check §1 of Day 42

```bash
grep -n 'langgraph' pyproject.toml
uv run python -c "import langgraph; print(langgraph.__version__)"
```

- Day 42 §1 pulled the `langgraph` pin forward and logged the amendment. **If that grep prints
  nothing, go back and do it** — Phase 7 on an unpinned transitive dependency is ten days of
  Principle-4 violation.
- Confirm the installed version matches the pin. A mismatch means a stale environment; `uv sync`.

### 2.2 Create today's files

```bash
touch src/mandala/graph/__init__.py
touch src/mandala/graph/state.py
touch src/mandala/graph/nodes.py
touch tests/test_graph_state.py
mkdir -p days/day-43/lab
touch days/day-43/lab/reducer_trap.py
touch days/day-43/lab/first_graph.py
touch days/day-43/lab/state_compare.md
```

- `src/mandala/graph/` as the fourth framework namespace, beside `crew/`, `flows/` and `lc/`.
- `reducer_trap.py` costs **0 requests** and is today's most important file. It is the direct
  descendant of Day 30's `state_trap.py`, and running them back to back is the day's best five
  minutes.
- `state_compare.md` is where Day 30's half-filled table gets completed.

---

## §3 LG-01 — nodes, edges, and the drawn loop

### 3.1 The three primitives

| Primitive | Is | Mandala's |
|---|---|---|
| **node** | a function `state -> partial update` | `triage`, `route`, `research`, `draft` |
| **edge** | "what runs next" | `START → triage → route → …` |
| **state** | the typed thing every node reads and writes | `MandalaGraphState` |

**Two properties fall out of this and they are the whole of LangGraph:**

1. **A node returns an update, it does not mutate.** Day 42 §3.2 already made you do this. The graph
   applies the update using the reducers. That indirection is what lets the runtime checkpoint
   (Day 47), replay (Day 51) and run branches in parallel (Day 44) — **none of which are possible
   over a shared mutable object.** Day 30's flow mutated `self.state`, and that is exactly why
   CrewAI's answer to "what happens on concurrent writes" was, per your Day-30 checklist, possibly
   "the framework has no answer".
2. **The loop is data.** Nodes and edges are a structure you can draw, walk, and reason about before
   running. Day 42 printed one with `draw_ascii()`.

### 3.2 `src/mandala/graph/state.py`

```python
"""Mandala's graph state. The fourth typed seam, and the first one with reducers.

Read this beside src/mandala/flows/state.py (Day 30). They are the same idea in
two frameworks, and the differences are the point:

  - Flow state:  a Pydantic model you MUTATE. One writer at a time, by construction.
  - Graph state: a TypedDict you return UPDATES to, merged by per-field reducers.

The second is more machinery and it buys: parallel writes with defined semantics,
checkpointing (Day 47), and time travel (Day 51). None of those are possible when
"the state" is an object several steps hold a reference to.

Usage
-----
    >>> from mandala.graph.state import MandalaGraphState, append
    >>> append(["a"], ["b"])
    ['a', 'b']
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from mandala.schemas import TriageResult

MAX_NOTES = 32
MAX_FINDINGS = 6


def append(existing: list, incoming: list) -> list:
    """Concatenate, bounded. An unbounded reducer is an unbounded prompt (AG-04)."""
    return (existing + incoming)[-MAX_NOTES:]


def keep_first(existing: str, incoming: str) -> str:
    """Write-once. The ticket body is set by intake and never overwritten."""
    return existing or incoming


def take_max_severity(existing: str, incoming: str) -> str:
    """Two branches may both classify. The WORSE severity wins -- fail safe."""
    order = ["low", "normal", "high", "critical"]
    if existing not in order:
        return incoming
    if incoming not in order:
        return existing
    return max(existing, incoming, key=order.index)


class MandalaGraphState(TypedDict, total=False):
    """Everything the graph knows. Every collection field names its reducer."""

    # --- identity: written once ------------------------------------------
    ticket_id: str
    request_id: str
    ticket_body: Annotated[str, keep_first]

    # --- the agent's own conversation ------------------------------------
    messages: Annotated[list[AnyMessage], add_messages]

    # --- results: several nodes may contribute ---------------------------
    triage: TriageResult | None
    severity: Annotated[str, take_max_severity]
    findings: Annotated[list[str], operator.add]
    notes: Annotated[list[str], append]

    # --- position --------------------------------------------------------
    stage: Literal["new", "classified", "researched", "drafted", "escalated"]
```

**Line by line:**

- `Annotated[str, keep_first]` — **the reducer is attached to the field, in the type.** That
  placement is the design: merge semantics are a property of the data, not of whichever node happens
  to write it. Day 30's flow state had no equivalent, which is why its only scoping tool was deletion.
- `append()` with `[-MAX_NOTES:]` — **bounded concatenation.** `operator.add` on a list appends
  forever, and state is prompt material (Day 30 made this argument, Day 39 made it again about
  scrubbing). A graph with a cycle plus an unbounded list reducer is a context-window leak that grows
  every loop. Keeping the last N rather than the first N is deliberate: recent notes are the useful
  ones.
- `findings: Annotated[list[str], operator.add]` — the **stdlib** reducer, used where the bound is
  enforced elsewhere (`MAX_FINDINGS` at the writing node). Two different list fields, two different
  policies, and the difference is visible in the type. Note the inconsistency honestly: bounding in
  the reducer is safer than bounding at the writer, and `findings` is the weaker of the two. Decide
  today whether to make it `append`-style too, and write down why you chose what you chose.
- `take_max_severity` — **a domain reducer, and the most interesting line in the file.** When Day 44
  fans out two classifiers, both write `severity`. Last-write-wins would make the answer depend on
  scheduling. This makes the merge *deterministic and fail-safe*: worse wins. **A reducer is where
  concurrency policy lives**, and writing one yourself is the moment reducers stop being a framework
  detail.
- `messages: Annotated[list[AnyMessage], add_messages]` — LangGraph's built-in message reducer. It
  does more than append: it de-duplicates by message id and supports updates. **Use the built-in;
  hand-rolling message merging is a known source of duplicated turns.**
- `TypedDict` rather than Pydantic. Note the trade honestly: no runtime validation, no `max_length`,
  no validators — everything Day 30's `MandalaState` had. What you get instead is cheap partial
  updates and reducer support. **LangGraph does accept Pydantic state; find out today whether you can
  have both** (§8), because "typed *and* reduced" would be strictly better and the answer belongs in
  `state_compare.md`.
- `stage` as a `Literal` — Day 30's habit, carried. Day 71 counts these.

### 3.3 `days/day-43/lab/reducer_trap.py` — 0 model requests

The direct sequel to Day 30's `state_trap.py`.

```python
"""What happens without a reducer, and with one. No models involved.

Run:
    uv run python days/day-43/lab/reducer_trap.py

Budget: 0 requests.
"""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


class NoReducer(TypedDict, total=False):
    notes: list[str]


class WithReducer(TypedDict, total=False):
    notes: Annotated[list[str], operator.add]


def alpha(state) -> dict:
    return {"notes": ["alpha ran"]}


def beta(state) -> dict:
    return {"notes": ["beta ran"]}


def build(schema):
    g = StateGraph(schema)
    g.add_node("alpha", alpha)
    g.add_node("beta", beta)
    g.add_edge(START, "alpha")
    g.add_edge("alpha", "beta")
    g.add_edge("beta", END)
    return g.compile()


print(f"no reducer   : {build(NoReducer).invoke({})}")
print(f"with reducer : {build(WithReducer).invoke({})}")
```

**Line by line:**

- Two identical graphs, **one difference: the annotation.** That is the cleanest possible isolation of
  the concept, and it is why this file has no ticket, no model and no Mandala imports.
- `build(schema)` parameterised over the state type — the same three nodes twice.
- Expected output: `{'notes': ['beta ran']}` versus `{'notes': ['alpha ran', 'beta ran']}`. **Run it
  and look**, because yesterday you hit the first case as a bug and the fix is one annotation.
- **Then extend it yourself:** make `alpha` and `beta` both run from `START` (two edges out of
  `START`) so they execute in the same super-step, and see what the no-reducer version does. That is
  the concurrent-write question your Day-30 checklist raised about CrewAI and could not answer.
  LangGraph's answer is: **without a reducer it raises**, or it clobbers — find out which, and write
  it in `state_compare.md`. **That single experiment is the strongest argument in Phase 7.**

### 3.4 `days/day-43/lab/first_graph.py`

```python
"""Mandala's first hand-built graph. Four nodes, drawn before it is run.

Run:
    uv run python days/day-43/lab/first_graph.py T-9002

Budget: <= 6 requests -- only the triage node calls a model.
"""

import sys

from mandala.graph.nodes import build_graph
from mandala.sdk_tools import RAW_TICKETS

ticket_id = sys.argv[1] if len(sys.argv) > 1 else "T-9002"

graph = build_graph()
print(graph.get_graph().draw_ascii())

final = graph.invoke({
    "ticket_id": ticket_id,
    "request_id": f"req-{ticket_id}",
    "ticket_body": RAW_TICKETS[ticket_id]["body"],
    "stage": "new",
})

print(f"\nstage     {final.get('stage')}")
print(f"severity  {final.get('severity')!r}")
print(f"notes     {final.get('notes')}")
print(f"findings  {len(final.get('findings', []))}")
print(f"body kept {len(final.get('ticket_body', ''))} chars")
```

**Line by line:**

- `draw_ascii()` **before** `invoke()` — a habit worth keeping for the whole phase. The picture is
  free and it is the artifact that makes a graph reviewable.
- The initial state supplies `stage: "new"` explicitly rather than relying on a default. `TypedDict`
  has no defaults, which is one of the costs §3.2 named; being explicit at the entry point is the
  workaround, and it is worth feeling once.
- `final.get('notes')` should now contain **one line per node**, because of `append`. Yesterday it
  contained one line total. **That diff is the day.**
- Write `nodes.py` yourself: a `triage_node` (reuse Day 42's, importing `triage_agent`), a
  `route_node` (no model — third time), a `research_node` and a `draft_node` that ship raising
  `NotImplementedError` with the shape prescribed. **Keep the node bodies thin**; today is about the
  wiring.

---

## §4 LG-02 — the comparison the plan promised

### 4.1 `days/day-43/lab/state_compare.md`

Complete the table you started on Day 30.

```markdown
# Flow state vs. graph state — Mandala, 2026-08-__

| Dimension | CrewAI flow state (D30) | LangGraph state (D43) | Which I prefer, and why |
|---|---|---|---|
| Type | Pydantic model | TypedDict (Pydantic possible? §8) | |
| Runtime validation | yes — `max_length`, `Literal` | | |
| How a step writes | mutates `self.state` | returns a partial update | |
| Concurrent writes | ? (D30 could not answer) | **experiment in §3.3** | |
| Merge semantics | last write wins, implicitly | per-field reducer, explicitly | |
| Scoping a field away | deletion (`drop_body`) | write-once reducer | |
| Bounded collections | `Field(max_length=…)` | inside the reducer | |
| Persistence | `@persist`, D32 | checkpointers, D47 | |
| Can I see the shape before running? | read the class | **draw the graph** | |

## The concurrent-write experiment
<what actually happened when two nodes wrote the same unreduced key>

## The prediction I made on Day 30 vs. what is here
<I expected ___; what is actually here is ___>

## Which security control is better: deletion (D30) or write-once (D43)?
<one paragraph — and name the failure mode each one still has>
```

**Why the last question is the one that matters.** Day 30 protected the raw ticket body by *deleting*
it before the research step, which made **ordering a security property** — your Day-30 checklist made
you write that down and be uncomfortable about it. A `keep_first` reducer makes the field
*unoverwritable* but does not make it *invisible*: a later node can still read `ticket_body`. So:

- **Deletion** protects against reading, and depends on ordering.
- **Write-once** protects against tampering, and does not depend on ordering.

**They defend different things, and Mandala needs both.** Getting to that conclusion yourself, from
two implementations you built two weeks apart, is worth more than any framework's documentation.
Day 48's subgraphs give you the third option — a node that simply is not given the field — and that
is the one that finally solves it.

---

## §5 The eval that must be able to fail

### `tests/test_graph_state.py`

```python
"""Reducers are concurrency policy. Test them like policy. 0 model requests."""

from typing import get_args, get_type_hints

import pytest

from mandala.graph.state import (
    MAX_NOTES,
    MandalaGraphState,
    append,
    keep_first,
    take_max_severity,
)


def test_append_concatenates():
    assert append(["a"], ["b"]) == ["a", "b"]


def test_append_is_bounded():
    """An unbounded reducer plus a cycle is a context-window leak (AG-04)."""
    out = append(["x"] * MAX_NOTES, ["newest"])
    assert len(out) == MAX_NOTES
    assert out[-1] == "newest"


def test_append_keeps_the_recent_end():
    """Flip it: change the slice to [:MAX_NOTES] and this goes red."""
    assert append(["old"], ["new"] * MAX_NOTES)[-1] == "new"


def test_keep_first_refuses_to_overwrite():
    assert keep_first("original ticket", "injected replacement") == "original ticket"


def test_keep_first_accepts_the_first_write():
    assert keep_first("", "intake wrote this") == "intake wrote this"


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ("low", "critical", "critical"),
        ("critical", "low", "critical"),
        ("normal", "high", "high"),
        ("high", "high", "high"),
    ],
)
def test_severity_merges_fail_safe(a, b, expected):
    """THE reducer test. Flip it: use min() and watch a critical ticket get downgraded."""
    assert take_max_severity(a, b) == expected


def test_severity_merge_is_order_independent():
    """A reducer that depends on argument order makes results depend on scheduling."""
    for a in ("low", "normal", "high", "critical"):
        for b in ("low", "normal", "high", "critical"):
            assert take_max_severity(a, b) == take_max_severity(b, a)


def test_unknown_severity_does_not_crash_the_graph():
    assert take_max_severity("", "high") == "high"
    assert take_max_severity("high", "banana") == "high"


def test_every_collection_field_declares_a_reducer():
    """Flip it: drop the Annotated on `notes` and this goes red."""
    hints = get_type_hints(MandalaGraphState, include_extras=True)
    for name in ("messages", "findings", "notes"):
        assert get_args(hints[name]), f"{name} has no reducer"


def test_the_body_is_write_once():
    hints = get_type_hints(MandalaGraphState, include_extras=True)
    assert keep_first in get_args(hints["ticket_body"])


def test_the_schema_is_still_day_4s():
    from mandala.schemas import TriageResult

    assert TriageResult.__module__ == "mandala.schemas"
```

**Line by line:**

- Every test calls a **plain function**. Reducers are pure functions of two arguments, which is why
  they are the most testable thing in LangGraph — and a good reason to put real policy in them rather
  than in nodes.
- `test_append_is_bounded` and `test_append_keeps_the_recent_end` are a pair: the first asserts the
  cap, the second asserts *which end survives*. The second's flip-it instruction names the exact
  wrong slice, because `[:MAX_NOTES]` is the natural typo and it silently keeps the oldest notes
  forever.
- `test_severity_merges_fail_safe` is today's headline flip-it test, and the failure it describes is
  the one that matters: **a critical ticket silently downgraded by a merge.**
- `test_severity_merge_is_order_independent` brute-forces all 16 pairs to assert **commutativity**.
  This is the deep property: in a parallel super-step you do not control which update is `existing`
  and which is `incoming`, so a non-commutative reducer makes your results depend on the scheduler.
  **Most people never think about this, and it is the single most valuable thing on the page.**
- `test_unknown_severity_does_not_crash_the_graph` — reducers run inside the runtime, so a raising
  reducer takes the whole graph down, including the checkpoint write. Defensive here is correct.
- `test_every_collection_field_declares_a_reducer` uses `get_type_hints(..., include_extras=True)` —
  **`include_extras=True` is required** or the `Annotated` metadata is stripped and the test passes
  vacuously. That flag is the kind of detail that turns a real test into a decorative one.
- `test_the_schema_is_still_day_4s` — fifth framework, same one-line assertion.

---

## §6 Traps

- **Mutating state inside a node.** It sometimes works and it breaks checkpointing, replay and
  parallelism. Return an update.
- **Forgetting `Annotated` on a collection field.** Yesterday's bug. It replaces, silently.
- **`operator.add` on an unbounded list in a cyclic graph.** Grows every loop; that is your context
  window and your budget.
- **Slicing the wrong end in a bounded reducer.** `[:N]` keeps the oldest forever.
- **A non-commutative reducer.** Results become scheduler-dependent, and it will be intermittent.
- **A reducer that raises.** It takes the graph down mid-super-step.
- **Hand-rolling message merging** instead of using `add_messages`. Duplicate turns.
- **`get_type_hints` without `include_extras=True`.** A test that passes for the wrong reason.
- **Assuming `TypedDict` validates anything.** It does not. That is the trade; know it and check §8
  for whether Pydantic state is available.
- **Skipping the Day-30 table.** The comparison is half the ID, and you wrote the first column
  thirteen days ago specifically for today.

---

## §7 Request budget

**Declared: ~6 model requests, Groq.**

| What | Requests |
|---|---|
| `reducer_trap.py` | **0** |
| `tests/test_graph_state.py` | **0** |
| `state_compare.md` | **0** |
| `first_graph.py` (only the triage node calls a model) | ≤ 6 |

**Phase 7 opens cheap for a structural reason worth naming:** in a graph, most of what you build is
wiring, and wiring is free. Compare Day 30 (~38 requests) and Day 23 (CrewAI's opening day). Put the
number in the bake-off — *"how much does it cost to learn this framework?"* is a real scorecard row
on a $0 budget, and you now have four data points.

---

## §8 Verify before you code

Written **2026-08-20** against `langgraph==1.2.11`:

- **`StateGraph`, `START`, `END` import paths** — `langgraph.graph` is the assumption.
- **Is `add_messages` in `langgraph.graph.message`?** It has moved between versions.
- **Can state be a Pydantic model instead of a `TypedDict`**, and do reducers still work if it is?
  This is the biggest open question in §3.2 and the answer decides whether you get validation *and*
  reducers. Write it into `state_compare.md` either way.
- **What happens on a concurrent write to a field with no reducer** — raise, or last-write-wins?
  §3.3's extension is the experiment; the answer is the strongest line in your comparison.
- **Are reducers called with `(existing, incoming)` in that order**, and is order guaranteed? Your
  commutativity test makes this moot, which is the point of writing it.
- **`DeltaChannel`** — the plan's Part 2 names it as a 1.2 feature for cheaper checkpoints on long
  threads. You do not need it today; know the name before Day 47.
- **Node-level timeouts, error recovery, graceful shutdown** — also 1.2 features per Part 2, and Day
  49's subject. Confirm they exist in 1.2.11 so Day 49 does not open with a surprise.
- `https://docs.langchain.com/oss/python/langgraph/graph-api` — read today.

---

## §9 Say it in an interview

> "A LangGraph node returns a partial state update rather than mutating shared state, and every field
> declares a reducer that says how two writes merge. That indirection is what makes checkpointing,
> replay and parallel branches possible at all — it's not ceremony. The reducer I'd point at is the
> severity one: when two branches both classify a ticket, last-write-wins would make the answer depend
> on scheduling, so mine takes the worse severity and there's a test asserting it's commutative,
> because in a parallel super-step you don't control which update arrives as `existing`. I'd built
> the same typed-seam idea in CrewAI Flows two weeks earlier with a mutable Pydantic object, and the
> comparison is instructive: that version protected the raw ticket body by deleting it before the
> research step, which made ordering a security property. The graph version makes the field write-once
> instead, which protects against tampering rather than reading — different guarantees, and a real
> system wants both."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 43
```
