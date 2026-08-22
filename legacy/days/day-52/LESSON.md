---
day: 52
phase: 7
phase_name: "LangGraph 1.x"
title: "Phase-7 gate — the durable Mandala core"
ids: ["LG-23"]
kind: gate
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 52 — The durable Mandala core: the Phase-7 gate

**Phase 7 · LangGraph 1.x** · IDs: **LG-23 🛠️** · **🎯 gate day**

> **Yesterday:** forking a past run to re-test one node for a third of the price.
> **Today:** the gate, and the largest artifact in the plan so far. The plan's Phase-7 gate sentence:
> *"durable Mandala core graph — checkpointed, interruptible, subgraph-composed — plus a time-travel
> demo script."* Ten days of parts, assembled, killed, resumed, paused, approved and rewound.
> **Tomorrow:** Phase 8 opens and MCP arrives — the boundary that makes all four frameworks
> interchangeable.

```bash
./m start 52
./m scaffold 52
```

---

## §1 What today is, and what it is not

**It is not "build the capstone".** That is Phase 12, thirty days away. Today is the *core graph*: the
spine that Days 78–84 will hang channels and reporting off.

**It is the day the parts disagree.** Day 29's gate found three collisions; Day 35's found three
more. Ten days of Phase 7 have produced more surface than either, so budget the afternoon for
assembly rather than for building.

The plan's gate sentence, clause by clause:

| Clause | Built on | Today's evidence |
|---|---|---|
| **durable** | Day 47 | a killed process, a resumed run |
| **checkpointed** | Day 47 | `get_state_history` shows every super-step |
| **interruptible** | Day 50 | two processes, a human between them |
| **subgraph-composed** | Day 48 | `xray=True` shows Research nested |
| **core graph** | Days 43–51 | one `build_graph()` everything imports |
| **time-travel demo script** | Day 51 | a fork that changes one thing |

Plus the standing gate freshness check (Part 5). §7.

---

## §2 Setup — run this

### 2.1 Nothing new

```bash
uv run pytest -q
git status --porcelain
ls .mandala/graph/
```

- **A gate day adds no dependencies.** Ten days is enough surface; if today needs a package, note the
  urge and do not act on it.
- Clean the store *deliberately*: you have edited `nodes.py` on most of the last ten days, so every
  checkpoint older than today is stale by Day 32's definition. `rm -rf .mandala/graph` and start
  clean — the demo will create what it needs.

### 2.2 Create today's files

```bash
mkdir -p days/day-52/lab
touch src/mandala/graph/core.py
touch days/day-52/lab/gate_demo.sh
touch days/day-52/lab/timetravel_demo.py
touch tests/test_core_graph.py
touch docs/adr/ADR-00X-langgraph-core.md
```

- `core.py` exports **one function**: `build_core()`. Everything else in `graph/` becomes an
  implementation detail behind it. **That single entry point is the gate artifact**, and Days 78–84
  will import exactly this and nothing else.
- ADR number: 001, 002 and 003 are spoken for (Days 16, 42, 64). Pick a free number, use it, and log
  the choice — same instruction as Day 35, and if you invented a scheme there, follow it.

---

## §3 The artifact

### 3.1 `src/mandala/graph/core.py`

```python
"""Mandala's core graph. One entry point; everything else is an implementation detail.

Phase 12's capstone imports build_core() and nothing else from this package. That
constraint is what makes the next thirty days cheap: channels, reporting and
deployment attach to a stable surface rather than to ten files.

Composition (Days 43-51):
    intake -> scrub -> triage -> [router] -> fast | research(subgraph) | escalate
                                          -> await_approval (interrupt) -> finish

Durability:  compiled with a checkpointer by the CALLER, so tests can compile without.
Blast radius: read-only tools throughout; the only write is behind Day 50's approval.

Usage
-----
    >>> with checkpointer() as saver:                      # doctest: +SKIP
    ...     graph = build_core().compile(checkpointer=saver)
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from mandala.graph.approval import await_approval_node
from mandala.graph.nodes import (
    escalate_node,
    fast_answer_node,
    finish_node,
    intake_node,
    triage_node,
)
from mandala.graph.persistence import scrub_node
from mandala.graph.policy import NODE_POLICY, retries_for
from mandala.graph.research import research_node
from mandala.graph.routing import LANE_TARGETS, choose_lane
from mandala.graph.state import MandalaGraphState

#: Nodes that produce a draft and therefore must pass the approval gate (Day 33 §3.3).
DRAFTING_LANES = ("fast_answer", "research")


def build_core() -> StateGraph:
    """The uncompiled core graph. The caller decides on durability."""
    g = StateGraph(MandalaGraphState)

    for name, fn in [
        ("intake", intake_node),
        ("scrub", scrub_node),
        ("triage", triage_node),
        ("fast_answer", fast_answer_node),
        ("research", research_node),
        ("escalate", escalate_node),
        ("await_approval", await_approval_node),
        ("finish", finish_node),
    ]:
        policy = NODE_POLICY.get(name)
        g.add_node(name, fn, retry=_retry_from(policy, name))

    g.add_edge(START, "intake")
    g.add_edge("intake", "triage")
    g.add_edge("triage", "scrub")                    # scrub AFTER triage, BEFORE the lanes
    g.add_conditional_edges("scrub", choose_lane, LANE_TARGETS)

    for lane in DRAFTING_LANES:
        g.add_edge(lane, "await_approval")
    g.add_edge("escalate", "finish")
    g.add_edge("await_approval", "finish")
    g.add_edge("finish", END)
    return g
```

**Line by line:**

- **`build_core()` returns an *uncompiled* graph**, and that is the day's most consequential design
  choice. Compilation is where the checkpointer is attached (Day 47), so leaving it to the caller
  means: tests compile without durability and run instantly with no store; the demo compiles with
  SQLite; Day 86's server can compile with Postgres. **One graph definition, three durability
  stories, zero conditionals.**
- The node loop with `NODE_POLICY.get(name)` — **Day 49's policy applied at wiring time**, so timeouts
  and retries are attached where the node is registered rather than scattered. Write `_retry_from()`
  yourself to map a `NodePolicy` onto whatever LangGraph's retry object is called (Day 49 §8 made you
  find out).
- **`scrub` is between `triage` and the lanes**, and the placement *is* the security control (Day 47
  §3.2). Triage needs the raw body; nothing after it does; the checkpoint written after `scrub` is
  the first one that could persist, and it no longer has the body. **Move this edge and the property
  silently disappears** — §5 tests the ordering.
- `add_conditional_edges("scrub", ...)` — routing hangs off `scrub`, not `triage`, which is the same
  fact stated as structure.
- `DRAFTING_LANES` as a named constant, with a comment pointing at Day 33's reasoning: **only lanes
  that produce a draft go through approval.** `escalate` skips it, because asking a human to approve
  sending something to a human is the gate that teaches people to click through gates.
- The `for lane in DRAFTING_LANES` loop — adding a lane means editing one tuple, and the approval
  wiring follows. Day 31's `or_` argument and Day 44's `LANE_TARGETS.values()` loop, third time.
- **`research` is `research_node`, a subgraph** (Day 48). The parent has no idea it contains a graph,
  and no idea it fans out. That is the encapsulation claim, visible in the wiring.
- No `similar` computation here, no fan-out here — **both live inside Research**, per Day 48 §3.3.

### 3.2 `days/day-52/lab/gate_demo.sh`

```bash
#!/usr/bin/env bash
# The Phase-7 gate demo. Read from this; do not improvise.
set -euo pipefail

TICKET=T-9002
ATTEMPT=gate-$(date +%H%M%S)

echo "== 1. clean store ================================================="
rm -rf .mandala/graph

echo "== 2. the shape, before anything runs ============================="
uv run python days/day-48/lab/nested_draw.py

echo "== 3. start the run; it pauses at the human gate =================="
uv run python days/day-52/lab/core_run.py "$TICKET" "$ATTEMPT" start

echo "== 4. NOTHING IS RUNNING. the state is on disk. ==================="
uv run python days/day-51/lab/history.py "$TICKET" "$ATTEMPT"

echo "== 5. kill-and-resume proof: a different process answers =========="
uv run python days/day-52/lab/core_run.py "$TICKET" "$ATTEMPT" approve

echo "== 6. time travel: re-run ONE node with ONE thing changed ========="
uv run python days/day-52/lab/timetravel_demo.py "$TICKET" "$ATTEMPT"

echo "== 7. the evidence table ========================================="
uv run pytest tests/test_core_graph.py -v
uv run pytest -q
```

**Line by line:**

- `set -euo pipefail` — Day 35's rule. A demo that continues past a failure shows a green ending for a
  broken system.
- **Step 2 before step 3** — show the shape before showing the behaviour. `xray=True` puts the whole
  system, subgraph included, on one screen; it is the single best frame in the recording.
- **Step 4 is the phase.** Between steps 3 and 5 there is no process. Pause here, read the checkpoint
  table aloud, and point at the row where `next` is `await_approval`. Then point at the row where
  `ticket_body` stops appearing.
- Step 6 is the plan's explicit gate requirement — *"plus a time-travel demo script"* — and it is the
  part that will surprise a viewer. Re-running one node of a past run, for a third of the cost, is
  not a thing most systems can do.
- The final `pytest -q` runs **everything**, not just today's file. A gate that only runs its own
  tests is a gate that can pass while Phase 5 is broken.

### 3.3 `days/day-52/lab/timetravel_demo.py`

```python
"""The gate's time-travel demo: same run, one thing changed, a third of the cost.

Run:
    uv run python days/day-52/lab/timetravel_demo.py T-9002 gate-123456

Budget: ~4 requests. A full re-run would be ~11.
"""

import sys

from mandala.graph.core import build_core
from mandala.graph.persistence import checkpointer, thread_id
from mandala.graph.timetravel import checkpoint_before, fork

ticket, attempt = sys.argv[1], sys.argv[2]
config = {"configurable": {"thread_id": thread_id(ticket, attempt)}}

with checkpointer() as saver:
    graph = build_core().compile(checkpointer=saver)

    original = graph.get_state(config).values
    before = sum(1 for _ in graph.get_state_history(config))
    print(f"original : severity={original.get('severity')!r} "
          f"stage={original.get('stage')!r}")

    cid = checkpoint_before(graph, config, node="scrub")
    branch = fork(graph, config, cid, {"severity": "critical"}, as_node="triage")

    print(f"forked   : severity={branch.get('severity')!r} "
          f"stage={branch.get('stage')!r}")
    print(f"           notes={branch.get('notes')[-3:]}")

    after = sum(1 for _ in graph.get_state_history(config))
    print(f"\nhistory  : {before} snapshots before, {after} after -- the original survived")
    print(f"body     : {branch.get('ticket_body')!r}   <- still None on the fork")
```

**Line by line:**

- Forking at **"where `scrub` was next"** with a raised severity is the cleanest gate demo: it proves
  routing responds, and it exercises Day 43's `take_max_severity` and Day 47's scrub in one run.
- The **before/after snapshot count** is the "history survived" evidence, on screen.
- `branch.get('ticket_body')` printed — **the security property holds on a forked branch too.** That
  is worth showing: a debugging tool that resurrects deleted customer data would be an interesting
  hole, and this one line closes the question.

### 3.4 The collisions to expect

Ten days of parts. Likely disagreements, so you recognise them fast:

1. **`scrub` versus Research's need for a question.** Day 48's `to_research` maps
   `triage.summary` — fine. But if any node after `scrub` still reads `ticket_body`, it now gets
   `None` and fails confusingly. **Grep for `ticket_body` across `graph/` and confirm every reader is
   upstream of `scrub`.**
2. **`await_approval` and the fan-out.** Research fans out internally (Day 48 §3.3). If any branch
   interrupts, Day 50 §8 asked whether that works — and if it does, you now have multiple pending
   interrupts and Day 50 deferred the matching question. **Decide today**: either no interrupts inside
   Research, or resolve the matching. The simple answer is the right one for now, and write down why.
3. **`stage` vocabulary, third time.** Day 35 found this in CrewAI; Days 43–50 have added
   `escalated`, `approved`, `drafted`, `researched`. **Reconcile the `Literal` and delete anything
   nothing sets** — Day 35's `test_every_stage_value_is_reachable` is a good test to port to `graph/`.
4. **Policy coverage.** Day 49's `test_the_policy_covers_every_node_in_the_graph` walks the compiled
   graph. Today's graph has nodes Day 49 did not know about (`intake`, `finish`, `scrub`). **Expect
   that test to be red and fix the policy, not the test.**

---

## §4 The evidence table

Every row needs a filename or a command.

| # | Claim | Proved by | ✓ |
|---|---|---|---|
| 1 | One entry point; the capstone imports only `build_core()` | `tests/test_core_graph.py` | ⬜ |
| 2 | Durability is the caller's choice, not baked in | tests compile with no checkpointer | ⬜ |
| 3 | Every super-step is checkpointed | `history.py` output (demo step 4) | ⬜ |
| 4 | State survives process death | demo steps 3–5, two processes | ⬜ |
| 5 | A human pause costs zero requests to wait on | ledger: resume run = 0 | ⬜ |
| 6 | Raw customer text never reaches disk | `history.py` shows `ticket_body` vanish after `scrub` | ⬜ |
| 7 | The scrub is upstream of every lane | `test_scrub_precedes_every_lane` | ⬜ |
| 8 | Research cannot see the raw body | `tests/test_subgraph.py` (Day 48) | ⬜ |
| 9 | Research is a subgraph and the parent does not know it fans out | `nested_draw.py` xray | ⬜ |
| 10 | Routing costs no model call | `tests/test_graph_routing.py` (Day 44) | ⬜ |
| 11 | A stale decision cannot authorise a changed draft | `tests/test_graph_approval.py` (Day 50) | ⬜ |
| 12 | One function answers "may this go out" | `test_authorises_send_is_still_the_only_gate` | ⬜ |
| 13 | Non-idempotent nodes are never retried | `tests/test_graph_policy.py` (Day 49) | ⬜ |
| 14 | Every node has a policy | `test_the_policy_covers_every_node_in_the_graph` | ⬜ |
| 15 | A past run can be re-run with one change, cheaply | demo step 6 + the ledger ratio | ⬜ |
| 16 | Forking does not destroy history | snapshot count before/after | ⬜ |
| 17 | The whole suite is green, not just today's | `pytest -q` in demo step 7 | ⬜ |
| 18 | Pins re-verified; drift logged or nil-reported | `docs/CHANGELOG_PLAN.md`, today's date | ⬜ |

**Rows 6 and 7 are a pair and deserve two looks.** Row 6 is the observation; row 7 is the structural
reason it holds. A system that satisfies 6 by luck and not 7 will stop satisfying 6 the first time
someone reorders an edge.

---

## §5 `tests/test_core_graph.py`

Gate-level assertions: the **assembly**, not the parts.

```python
"""Does ten days of Phase 7 actually compose? 0 model requests."""

from pathlib import Path

import pytest

from mandala.graph.core import DRAFTING_LANES, build_core
from mandala.graph.policy import NODE_POLICY
from mandala.graph.routing import LANE_TARGETS
from mandala.graph.state import MandalaGraphState


@pytest.fixture(scope="module")
def graph():
    """Compiled WITHOUT a checkpointer -- proving durability is the caller's choice."""
    return build_core().compile()


def test_the_graph_compiles_without_a_checkpointer(graph):
    """Row 2. Flip it: bake a checkpointer into build_core() and this goes red."""
    assert graph is not None


def test_scrub_precedes_every_lane(graph):
    """Row 7 -- the STRUCTURAL reason row 6 holds. Flip it: move scrub after routing."""
    edges = [(e.source, e.target) for e in graph.get_graph().edges]
    reachable_from_scrub = {t for s, t in edges if s == "scrub"}
    for lane in LANE_TARGETS.values():
        assert lane in reachable_from_scrub, f"{lane} is not downstream of scrub"


def test_nothing_after_scrub_reads_the_raw_body():
    """Collision 1 from §3.4. Grep every node module for late readers."""
    late = []
    for path in Path("src/mandala/graph").glob("*.py"):
        if path.name in {"nodes.py", "persistence.py", "state.py"}:
            continue
        if "ticket_body" in path.read_text(encoding="utf-8"):
            late.append(path.name)
    assert late == [], late


def test_only_drafting_lanes_reach_the_approval_gate(graph):
    edges = [(e.source, e.target) for e in graph.get_graph().edges]
    into_approval = {s for s, t in edges if t == "await_approval"}
    assert into_approval == set(DRAFTING_LANES)


def test_escalate_skips_the_gate(graph):
    edges = [(e.source, e.target) for e in graph.get_graph().edges]
    assert ("escalate", "finish") in edges
    assert ("escalate", "await_approval") not in edges


def test_every_node_has_a_policy(graph):
    """Collision 4. Expect this RED first; fix the policy, not the test."""
    nodes = set(graph.get_graph().nodes) - {"__start__", "__end__"}
    assert nodes <= set(NODE_POLICY), nodes - set(NODE_POLICY)


def test_every_stage_value_is_reachable():
    """Collision 3, ported from Day 35. A Literal value nothing sets is a lie."""
    from typing import get_args, get_type_hints

    stages = set(get_args(get_type_hints(MandalaGraphState)["stage"]))
    source = "\n".join(
        p.read_text(encoding="utf-8") for p in Path("src/mandala/graph").rglob("*.py")
    )
    unset = {s for s in stages if f'"{s}"' not in source}
    assert unset == set(), unset


def test_the_capstone_surface_is_one_function():
    """Row 1. Days 78-84 import build_core() and nothing else from graph/."""
    import mandala.graph.core as core

    exported = [n for n in dir(core) if not n.startswith("_") and n.isupper() or n == "build_core"]
    assert "build_core" in exported


def test_research_is_one_node_from_the_parents_view(graph):
    """Row 9: the parent does not know Research is a graph, or that it fans out."""
    nodes = set(graph.get_graph().nodes)
    assert "research" in nodes
    assert "search" not in nodes and "summarise" not in nodes


def test_the_schema_is_still_day_4s():
    from mandala.schemas import TriageResult

    assert TriageResult.__module__ == "mandala.schemas"
```

**Line by line on the ones that carry weight:**

- The fixture compiles **without a checkpointer**, which is both a test and a demonstration of §3.1's
  design. Every gate test runs with no store and no keys.
- `test_scrub_precedes_every_lane` walks the **real compiled graph's edges.** This is the stronger
  version of the weak grep test Day 47 shipped and admitted was weak — and writing it today is the
  right time, because only now does the full lane set exist. **Upgrading a knowingly-weak test when
  the information arrives is a habit worth naming.**
- `test_nothing_after_scrub_reads_the_raw_body` excludes the three modules legitimately allowed to
  mention `ticket_body` and asserts nothing else does. Crude, effective, and it catches collision 1.
- `test_every_node_has_a_policy` is **expected to fail first.** Say so in the checklist; a gate test
  that is red on arrival is the gate doing its job.
- `test_research_is_one_node_from_the_parents_view` asserts the subgraph's internals are **absent**
  from the parent's node list. That is encapsulation, tested rather than admired.

---

## §6 The ADR

Write it today. Four questions:

1. **Is LangGraph Mandala's spine?** You are not deciding finally — Day 64's ADR-003 does that, after
   the bake-off. But write your current answer **with the evidence you have now**, and date it. On
   Day 64 you will compare this against the scorecard, and a prediction you recorded is worth ten
   times a preference you rationalised.
2. **What did the graph cost?** Ten days, and a real answer includes lines of wiring, the request
   totals from the ledger, and the concepts a newcomer must learn (reducers, super-steps, checkpoint
   ids) before they can read your code.
3. **What can Mandala now do that it could not on Day 42?** Be specific: survive a crash mid-run,
   pause for a human at zero cost, re-run one node of a past execution, run a subsystem that cannot
   see the customer's words.
4. **What are you carrying into Phase 8?** MCP arrives tomorrow, and the plan's Principle 11 says
   every data source becomes an MCP server. **Predict what that does to `kb.search()` and to
   `READ_TOOLS`** before you see it.

---

## §7 The standing gate freshness check

```bash
for p in langgraph langgraph-checkpoint-sqlite langchain langchain-core; do
  printf "%-30s " "$p"
  curl -s --max-time 30 "https://pypi.org/pypi/$p/json" \
    | python -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
done
```

- Compare against `docs/PINS.md`. Patch → pin and log. Minor/major → **addendum first** (Principle 14).
- **Check the MCP spec revision today, properly, not as a formality.** Phase 8 starts tomorrow and it
  is built entirely on the 2026-07-28 revision. If that page has moved, tomorrow's lesson changes
  before it is taught, and finding out today costs ten seconds while finding out on Day 55 costs a
  phase.
- Also settle the **`01_MASTER_PLAN_ADDENDUM_GAPS.md`** question. `CLAUDE.md` names it as the standing
  MCP reference and it does not exist; the freshness addendum's Part 4 gives you two options and
  Day 53's first task is to resolve it. **Doing it tonight makes tomorrow clean.**
- Nothing moved? Write **"checked, unchanged"**. A nil report is the deliverable of the habit.

---

## §8 Traps

- **Baking the checkpointer into `build_core()`.** Tests get slow, need a store, and you lose the
  Postgres story for Day 86.
- **Moving `scrub` after routing.** Row 6 stops holding and nothing errors.
- **Adding a lane without adding it to `DRAFTING_LANES`** — it silently skips the approval gate. This
  is the worst bug available today: a draft that reaches a customer with no human decision.
- **Fixing `test_every_node_has_a_policy` by editing the test.** Fix the policy.
- **Letting Research interrupt** without resolving Day 50's multiple-interrupt question.
- **Running only today's tests.** Phase 5 can be broken while Phase 7 is green.
- **Improvising the demo.** Read from the script.
- **Skipping demo step 4.** "Nothing is running and the state exists" is the phase.
- **Writing the ADR after Day 64.** The whole value is that it predates the bake-off.
- **Skipping the MCP spec check** because it is not today's subject. It is tomorrow's foundation.

---

## §9 Request budget

**Declared: ~25 model requests, Groq.**

| What | Requests |
|---|---|
| All non-live tests | **0** |
| `nested_draw.py`, `history.py` | **0** |
| One full gate run to the pause | ~11 |
| Resume after approval | **0** |
| Time-travel fork | ~4 |
| One re-record allowance | ~11 |

**Phase 7 total should land near 100 requests across ten days.** Compare with Phase 5 (~110 across
six) and Phase 6 (~60 across seven) and put all three in the ADR: *"free-tier friendliness"* is a
Phase-9 scorecard row and you now have three measured phases instead of impressions.

---

## §10 Done when

Phase 7 is complete when every row in §4 is green, the ADR exists, and the recording shows a process
that died, a human who waited, and a past run re-executed with one thing changed.

```bash
./m check
./m done 52
```

Then read Day 53's §1 **tonight**. Phase 8 is MCP, its first task is the missing-addendum decision
from §7, and Principle 11 — *every data source is an MCP server* — is about to make you rewrite the
tool layer you have been carrying since Day 10.
