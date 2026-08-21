---
day: 44
phase: 7
phase_name: "LangGraph 1.x"
title: "Conditional edges, `Command`, and the Send API"
ids: ["LG-03", "LG-04"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 44 — Conditional edges, `Command`, and fan-out with `Send`

**Phase 7 · LangGraph 1.x** · IDs: **LG-03 🛠️**, **LG-04 🛠️**

> **Yesterday:** state, nodes, edges and reducers — and a commutativity test whose reason
> ("you don't control which update arrives first in a parallel super-step") was a promise about today.
> **Today:** the promise is kept. Conditional edges and `Command` give you the **fourth and final**
> severity router. Then `Send` fans out dynamic parallel branches — and every reducer you wrote
> yesterday starts doing real work.
> **Tomorrow:** streaming a graph, and `create_agent` as a node.

```bash
./m start 44
./m scaffold 44
```

---

## §1 The story

**The severity router completes today.** Part 6's repetition map, finished:

| Framework | Mechanism | Who decides | Where the decision lives | Day |
|---|---|---|---|---|
| Agents SDK | handoff | the **model** | a tool call | 13 |
| CrewAI Flows | `@router` | your code | a decorated method returning a label | 31 |
| LangChain | middleware / a plain node | your code | a function around the loop | 39, 42 |
| **LangGraph** | **conditional edge, or `Command`** | **your code** | **the edge itself, or inside the node** | **today** |

Four implementations of one business rule. **On Day 63 you will be asked to compare frameworks and
you will have this table, built from code you wrote, instead of a feature matrix you read.** That is
the whole reason the plan repeats itself.

Today's genuinely new idea is the second one. `Send` lets a node fan out **N parallel branches whose
number is not known until runtime** — research five similar tickets at once, reduce to one brief.
That is map-reduce inside a graph, and it is the first thing in this plan that Days 30–35's flows
could not express at all.

And it is where yesterday stops being theory. Five parallel branches all writing `findings` is the
concurrent-write case. Your `operator.add` reducer is what makes it defined. Your commutativity test
is what makes it deterministic. **Today the machinery earns its keep.**

---

## §2 Setup — run this

### 2.1 No new packages

```bash
grep -n 'langgraph' pyproject.toml
```

### 2.2 Create today's files

```bash
touch src/mandala/graph/routing.py
touch src/mandala/graph/fanout.py
touch tests/test_graph_routing.py
touch tests/test_fanout.py
mkdir -p days/day-44/lab
touch days/day-44/lab/two_routers.py
touch days/day-44/lab/fan_out.py
```

- Two source files because the two IDs are genuinely separate concerns, and because Day 48's
  supervisor will import `routing.py` while Day 80's research organ will import `fanout.py`.
- `two_routers.py` costs **0 requests** — it builds the same routing two ways and prints both graphs.

---

## §3 LG-03 — conditional edges and `Command`

### 3.1 Two ways to route, and they are not equivalent

```python
# Way 1: a conditional edge. The decision is on the EDGE.
graph.add_conditional_edges("triage", choose_lane, {"fast": "fast_answer", ...})

# Way 2: Command. The decision is INSIDE the node, together with a state update.
def triage_node(state) -> Command:
    return Command(update={"severity": "high"}, goto="deep_research")
```

| | Conditional edge | `Command` |
|---|---|---|
| Where the decision lives | the graph structure | the node body |
| Visible in `draw_ascii()` | **yes** — all branches drawn | partly; targets are dynamic |
| Can update state at the same time | no — separate node | **yes**, atomically |
| Testable without running the graph | **yes** — it is a plain function | yes, assert on the returned `Command` |
| Reviewable as a picture | **yes** | less so |

**Mandala uses conditional edges for the severity router**, and the reason is the row about pictures.
Day 34 spent a whole day on "orchestration as data versus code" and concluded that the strongest
argument for declarative structure is **who can safely read it**. A conditional edge keeps the
routing table in the graph, where `draw_ascii()` shows it and a reviewer sees every branch. A
`Command` hides the target inside a function body.

**Use `Command` when the update and the jump are one atomic decision** — Day 48's supervisor is the
canonical case: "record which subagent I chose *and* go there" should not be two nodes that could
interleave.

### 3.2 `src/mandala/graph/routing.py`

```python
"""The severity router, fourth and final framework.

Same policy as days/day-31 (CrewAI @router) and days/day-42 (a plain node). The
test file is deliberately a near-copy of tests/test_routes.py -- a policy test you
can port unchanged between frameworks is evidence the policy is framework-independent,
which is the plan's whole thesis (Part 0).

Design note: the decision is on the EDGE, not in a Command, so every branch shows up
in draw_ascii(). See LESSON §3.1.

Usage
-----
    >>> from mandala.graph.routing import choose_lane
    >>> choose_lane({"severity": "critical"})
    'escalate'
"""

from __future__ import annotations

from typing import Final, Literal

Lane = Literal["fast", "deep", "escalate"]

FAST_LANE_CATEGORIES: Final[frozenset[str]] = frozenset({"password_reset", "how_to"})

#: Request budget per lane. Same numbers as flows/routes.py -- a test asserts they agree.
LANE_BUDGET: Final[dict[str, int]] = {"fast": 1, "deep": 20, "escalate": 0}

#: The conditional-edge mapping. Passed to add_conditional_edges so the graph
#: structure and the return values cannot drift apart.
LANE_TARGETS: Final[dict[str, str]] = {
    "fast": "fast_answer",
    "deep": "deep_research",
    "escalate": "escalate",
}


def choose_lane(state) -> Lane:
    """Pure function of state. No model, no side effects, no state update."""
    triage = state.get("triage")
    if triage is None:
        return "escalate"
    if triage.severity == "critical":
        return "escalate"
    if triage.severity == "low" and triage.category in FAST_LANE_CATEGORIES:
        return "fast"
    return "deep"
```

**Line by line:**

- `Lane = Literal[...]` as a module-level alias — the return type is the set of legal values, checkable
  by a type checker and importable by tests. Day 31 used `Final` strings on a class; this is the same
  intent with less ceremony, because here the values never leave Python (LangGraph matches them
  against `LANE_TARGETS` keys, not across a wire).
- `LANE_TARGETS` as a **dict passed to `add_conditional_edges`** — this is the important one. The
  alternative is a bare `add_conditional_edges("triage", choose_lane)`, where LangGraph uses the
  returned string as a node name directly. Supplying an explicit mapping means **the router's
  vocabulary and the graph's node names are decoupled**, so renaming a node does not silently break
  routing. Day 31's whole `routes.py` argument, one framework later.
- `choose_lane(state)` takes state and returns a label — **no `Command`, no update, no side effect.**
  A pure function is testable, printable and free, and §5's test file is nearly a copy of Day 31's
  because of it.
- `state.get("triage")` — `.get`, because `TypedDict` with `total=False` means the key may be absent
  (Day 43's cost). `state["triage"]` would raise on the first unclassified ticket.
- **The `None` branch is first, again.** Fourth framework, fourth time, same reason: a router with no
  fallback silently stops, and "the classifier returned nothing" is what a 429 looks like.
- `LANE_BUDGET` duplicated from `flows/routes.py` **on purpose**, with a test asserting the two agree.
  You could import one from the other; you should not, because the frameworks are meant to be
  independently deletable. **A test that pins two independent copies together is better than a
  coupling that makes the bake-off impossible.**

### 3.3 Wiring it

```python
    graph.add_node("triage", triage_node)
    graph.add_node("fast_answer", fast_answer_node)
    graph.add_node("deep_research", deep_research_node)
    graph.add_node("escalate", escalate_node)

    graph.add_conditional_edges("triage", choose_lane, LANE_TARGETS)

    for lane_node in LANE_TARGETS.values():
        graph.add_edge(lane_node, "finish")
```

**Line by line:**

- `add_conditional_edges(source, fn, mapping)` — three arguments: where the branch starts, the
  function that decides, and label → node.
- The `for` loop adding the rejoin edges — **this is `or_` from Day 31, spelled out.** LangGraph does
  not need a special combinator: several edges into one node *is* the join. Iterating
  `LANE_TARGETS.values()` means adding a lane requires editing one dict, and the wiring follows.
  Compare Day 31, where forgetting `or_` produced a silent dead end.
- **What `draw_ascii()` now shows:** a diamond. Three branches out of `triage`, three back into
  `finish`. Print it, put it beside Day 42's three-node line, and note that the picture got more
  informative while the code got shorter. That is the LG-03 argument.

### 3.4 `days/day-44/lab/two_routers.py` — 0 model requests

```python
"""The same routing, both ways. Compare the pictures.

Run:
    uv run python days/day-44/lab/two_routers.py

Budget: 0 requests -- no node calls a model.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


class S(TypedDict, total=False):
    severity: str
    picked: str


def by_edge(state):
    return "hot" if state.get("severity") == "critical" else "cold"


def start_edge(state):
    return {}


def by_command(state) -> Command:
    lane = "hot" if state.get("severity") == "critical" else "cold"
    return Command(update={"picked": lane}, goto=lane)


def hot(state):
    return {"picked": "hot"}


def cold(state):
    return {"picked": "cold"}


edge_graph = StateGraph(S)
edge_graph.add_node("start", start_edge)
edge_graph.add_node("hot", hot)
edge_graph.add_node("cold", cold)
edge_graph.add_edge(START, "start")
edge_graph.add_conditional_edges("start", by_edge, {"hot": "hot", "cold": "cold"})
edge_graph.add_edge("hot", END)
edge_graph.add_edge("cold", END)

cmd_graph = StateGraph(S)
cmd_graph.add_node("start", by_command)
cmd_graph.add_node("hot", hot)
cmd_graph.add_node("cold", cold)
cmd_graph.add_edge(START, "start")
cmd_graph.add_edge("hot", END)
cmd_graph.add_edge("cold", END)

print("=== conditional edge ===")
print(edge_graph.compile().get_graph().draw_ascii())
print("=== Command ===")
print(cmd_graph.compile().get_graph().draw_ascii())

for name, g in [("edge", edge_graph), ("command", cmd_graph)]:
    out = g.compile().invoke({"severity": "critical"})
    print(f"{name:<8} -> {out}")
```

**Line by line:**

- Two graphs, same behaviour, **different pictures.** That is the entire file and it is worth the ten
  minutes: the edge version draws both branches; the `Command` version draws fewer edges because the
  targets are decided at runtime.
- `Command(update={...}, goto=...)` — **one object carrying both a state update and a jump**, applied
  atomically. That atomicity is the real feature, not the brevity.
- `from langgraph.types import Command` — confirm the import path (§8); it has moved.
- **Look at the two ASCII drawings side by side and decide which one you would rather hand a
  reviewer.** Write the answer in your bake-off notes; that judgement is LG-03.

---

## §4 LG-04 — `Send` and map-reduce

### 4.1 The problem `Send` solves

Mandala's research step wants: *"find the five most similar past tickets and summarise each."* Five is
not known when you draw the graph — it depends on the ticket.

Everything you have built so far handles this by **looping in one node**: five sequential model calls
inside `research_node`. That works, and it is slow, and a failure at ticket three loses tickets one
and two.

`Send` makes each one a **real parallel branch**: separately scheduled, separately checkpointed (Day
47), separately retryable (Day 49).

### 4.2 `src/mandala/graph/fanout.py`

```python
"""Fan out one research task per similar ticket, then reduce to one brief.

This is the first thing in the plan that CrewAI Flows could not express: N parallel
branches where N is discovered at runtime. Days 30-35 would have written a for-loop
in one step, which is sequential and loses everything on a mid-loop failure.

Every branch writes `findings`. That works ONLY because Day 43 gave `findings` an
`operator.add` reducer -- without it the branches would clobber each other, and with
a non-commutative reducer the result would depend on scheduling. Yesterday's
commutativity test was for today.

Blast radius (Principle 6): each branch gets ONE ticket id and no raw body.

Usage
-----
    >>> from mandala.graph.fanout import plan_research
    >>> len(plan_research({"similar": ["T-1", "T-2"]}))
    2
"""

from __future__ import annotations

from langgraph.types import Send

#: Hard ceiling on fan-out width. N branches = N model requests, in parallel,
#: which is the fastest way to hit a per-minute rate limit that exists.
MAX_BRANCHES = 5


def plan_research(state) -> list[Send]:
    """Turn a list of similar ticket ids into N parallel branch invocations."""
    similar = (state.get("similar") or [])[:MAX_BRANCHES]
    return [
        Send("research_one", {"ticket_id": tid, "request_id": state.get("request_id", "")})
        for tid in similar
    ]


def research_one(state) -> dict:
    """One branch. Runs MAX_BRANCHES times concurrently, so keep it small."""
    ticket_id = state["ticket_id"]
    # TODO(me): one lookup + one summarise call. Budget: 1 request per branch.
    raise NotImplementedError("wire one branch, then delete this line")
```

**Line by line:**

- `plan_research(state) -> list[Send]` — a **conditional edge that returns `Send` objects instead of
  labels.** Same wiring point (`add_conditional_edges`), different return type. That reuse is elegant
  and slightly confusing the first time; say it out loud once.
- `Send("research_one", {...})` — **node name plus that branch's private state.** The second argument
  is *not* the whole graph state; it is what this branch sees. **That is a blast-radius control**
  (Principle 6): the branch gets a ticket id and a request id, and cannot see `ticket_body`,
  `triage`, or the other branches' findings. Compare Day 30's global flow state, where every step saw
  everything and the only defence was deletion. **This is the third and best answer to the question
  §4 of Day 43 left open.**
- `MAX_BRANCHES = 5` and the `[:MAX_BRANCHES]` slice — **the most important line for Principle 5.**
  N parallel branches are N simultaneous requests. Groq's ceiling is 8000 TPM (`RATE_BUDGET.md` §1),
  and a 20-wide fan-out is the fastest way to discover that. Fan-out width is a rate-limit decision
  before it is a performance decision.
- The slice happens **before** the list comprehension, so the cap cannot be bypassed by a long
  `similar` list.
- `state.get("similar") or []` — handles both "key absent" and "key present but `None`". Two failure
  shapes, one expression.
- `research_one` **ships raising**, with its budget in the docstring. The rep is yours; the shape and
  the cost are prescribed.
- **What is not here:** any merging code. Branches write `findings`, and the reducer merges them. The
  absence of merge logic is the payoff of Day 43, and it is worth noticing that the elegant part of
  map-reduce here is that the "reduce" was declared a day earlier as a type annotation.

### 4.3 `days/day-44/lab/fan_out.py`

```python
"""Fan out research over similar tickets and watch the reducer merge them.

Run:
    uv run python days/day-44/lab/fan_out.py T-9002

Budget: <= 5 requests (one per branch). Note they arrive in PARALLEL -- if you see
a 429, that is the per-minute limit, not a bug.
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
    "similar": [t for t in RAW_TICKETS if t != ticket_id][:5],
    "stage": "new",
})

print(f"\nbranches asked : 5")
print(f"findings back  : {len(final.get('findings', []))}")
print(f"notes          : {final.get('notes')}")
print(f"severity       : {final.get('severity')!r}")
```

**Line by line:**

- The docstring's 429 note is real advice: **parallel branches make you hit per-minute limits that
  sequential code never touches.** Day 6's router with backoff is what absorbs it, and today is the
  first time it will actually fire in anger. If it does, that is a good thing to have seen before
  Day 80's capstone research organ.
- `findings back` compared against `branches asked` — **if they differ, a branch failed silently.**
  That comparison is the whole diagnostic, and it works because the reducer concatenates.
- `notes` will show the branches' notes interleaved in **nondeterministic order**. Look at that and
  connect it to yesterday's commutativity test: order varies, and a well-chosen reducer means the
  *result* does not.
- `severity` printed because if two branches ever write it, `take_max_severity` decides — the domain
  reducer, doing its job.

---

## §5 The eval that must be able to fail

### `tests/test_graph_routing.py`

**Open `tests/test_routes.py` (Day 31) beside this.** It is nearly the same file, and that is the
finding.

```python
"""The severity router, fourth framework. Near-identical to Day 31's test file."""

import pytest

from mandala.graph.routing import (
    FAST_LANE_CATEGORIES,
    LANE_BUDGET,
    LANE_TARGETS,
    choose_lane,
)
from mandala.schemas import TriageResult


def lane_for(severity: str, category: str) -> str:
    return choose_lane({"triage": TriageResult(
        severity=severity, category=category, summary="fixture")})


@pytest.mark.parametrize(
    ("severity", "category", "expected"),
    [
        ("low", "password_reset", "fast"),
        ("low", "billing", "deep"),
        ("normal", "billing", "deep"),
        ("high", "outage", "deep"),
        ("critical", "outage", "escalate"),
    ],
)
def test_the_routing_table(severity, category, expected):
    assert lane_for(severity, category) == expected


def test_an_unclassified_ticket_escalates():
    """Fourth framework, same flip-it test. Delete the None branch and this goes red."""
    assert choose_lane({}) == "escalate"


def test_every_lane_has_a_target_and_a_budget():
    assert set(LANE_TARGETS) == set(LANE_BUDGET)


def test_the_four_frameworks_agree_on_the_budget():
    """Two independent copies, pinned together. Flip it: change one, see red."""
    from mandala.flows.routes import ROUTE_BUDGET

    assert LANE_BUDGET == ROUTE_BUDGET


def test_the_four_frameworks_agree_on_the_fast_lane():
    from mandala.flows.routes import FAST_LANE_CATEGORIES as CREW_FAST

    assert FAST_LANE_CATEGORIES == CREW_FAST


def test_the_router_makes_no_model_call(monkeypatch):
    import mandala.lc.chat as chat

    monkeypatch.setattr(chat, "fast_loop",
                        lambda *a, **k: pytest.fail("the router built a model"))
    assert lane_for("low", "password_reset") == "fast"
```

### `tests/test_fanout.py`

```python
"""Fan-out width is a rate-limit decision. 0 model requests."""

import pytest

from mandala.graph.fanout import MAX_BRANCHES, plan_research
from mandala.graph.state import MAX_NOTES


def test_one_send_per_similar_ticket():
    sends = plan_research({"similar": ["T-1", "T-2", "T-3"], "request_id": "r"})
    assert len(sends) == 3
    assert {s.node for s in sends} == {"research_one"}


def test_fanout_is_capped():
    """THE budget test. Flip it: drop the slice and watch 50 branches fire at once."""
    sends = plan_research({"similar": [f"T-{i}" for i in range(50)]})
    assert len(sends) == MAX_BRANCHES


def test_a_branch_sees_only_its_own_ticket():
    """Blast radius (Principle 6). Flip it: pass the whole state, see red."""
    state = {
        "similar": ["T-1"],
        "request_id": "r",
        "ticket_body": "RAW CUSTOMER TEXT that must not reach a branch",
        "triage": object(),
    }
    payload = plan_research(state)[0].arg
    assert set(payload) == {"ticket_id", "request_id"}
    assert "ticket_body" not in payload


def test_no_similar_tickets_means_no_branches():
    assert plan_research({}) == []
    assert plan_research({"similar": None}) == []


def test_the_cap_is_below_the_notes_bound():
    """Each branch writes a note; a fan-out must not blow the audit trail in one step."""
    assert MAX_BRANCHES < MAX_NOTES
```

**Line by line:**

- `test_the_four_frameworks_agree_on_the_budget` imports Day 31's `ROUTE_BUDGET` and asserts equality.
  **Two deliberately independent copies, pinned by a test** — §3.2's argument, enforced. If one
  framework's numbers drift, the bake-off's comparison is invalid, and this is the cheapest possible
  guard against that.
- `test_an_unclassified_ticket_escalates` — **the fourth identical copy** of this test across four
  frameworks. When you can port a policy test unchanged, the policy is genuinely framework-independent.
  That is the plan's thesis with evidence attached; note it in the bake-off.
- `test_a_branch_sees_only_its_own_ticket` is the day's most important test and the one people would
  not think to write. It asserts the `Send` payload is exactly two keys — so a branch cannot see raw
  ticket text. **`Send` is an access-control mechanism and this test is what makes that claim real.**
  The flip-it instruction names the exact wrong move (passing the whole state), which is what someone
  will do the first time a branch needs one more field.
- `test_fanout_is_capped` uses 50 to make the failure vivid. Fifty simultaneous requests would hit
  every per-minute limit you have.
- `test_the_cap_is_below_the_notes_bound` — a **cross-constant** invariant, connecting today's cap to
  yesterday's bound. One fan-out must not fill the audit trail in a single super-step, or the notes
  from every other node get evicted.
- `s.node` and `s.arg` — the `Send` object's attributes. **Confirm these names in 1.2.11** (§8); if
  they differ, fix the tests, and note that a test reaching into a framework object's attributes is
  slightly fragile by nature.

---

## §6 Traps

- **Using `Command` for the severity router.** It works and it hides every branch from the picture.
- **`add_conditional_edges` without an explicit mapping.** The router's return values become node
  names, and a node rename silently breaks routing.
- **`state["triage"]` instead of `.get`.** `total=False` means absent keys, and the first unclassified
  ticket raises.
- **Forgetting the rejoin edges.** Lanes end nowhere. Iterate `LANE_TARGETS.values()`.
- **An uncapped fan-out.** N branches are N simultaneous requests; this is the fastest possible route
  to a 429 and, on Gemini, to a day's quota.
- **Slicing after building the `Send` list.** The cap has to come first.
- **Passing whole state into a `Send`.** You have just handed every branch the raw ticket body and
  undone the day's best security property.
- **Expecting deterministic branch ordering.** It is not. Your reducers make the *result*
  deterministic; the order of arrival is not.
- **Writing merge logic in a node.** The reducer already did it. If you are merging by hand, you have
  the wrong reducer.
- **Assuming a partial fan-out failed loudly.** Compare `len(findings)` against the branch count;
  that comparison is your only signal.

---

## §7 Request budget

**Declared: ~11 model requests, Groq.**

| What | Requests |
|---|---|
| `two_routers.py` | **0** |
| `tests/test_graph_routing.py` + `tests/test_fanout.py` | **0** |
| `first_graph.py` re-run through the new routing | ≤ 6 |
| `fan_out.py`, 5 branches | 5 |

**The fan-out's 5 requests arrive within a second or two of each other.** That is a different shape of
spend from anything so far, and it is the shape that trips per-minute limits. Log not just the count
but **whether you saw a 429** — the ledger's "429s hit" column exists for exactly this, and today is
the day it is likely to be non-zero for the first time.

---

## §8 Verify before you code

Written **2026-08-20** against `langgraph==1.2.11`:

- **`Command` and `Send` import paths** — `langgraph.types` is the assumption for both. They have
  lived in `langgraph.graph` and elsewhere historically.
- **`Send` attribute names** — `.node` and `.arg` are what §5 asserts. Confirm.
- **Does `add_conditional_edges` accept a function returning `list[Send]`** on the same API as one
  returning a label? §4.2 depends on it.
- **Is fan-out width limited by anything in the framework**, or purely by your slice? If there is a
  concurrency setting, that is a `RATE_BUDGET.md` note.
- **Does a failing branch abort the whole super-step**, or do the survivors' updates still apply?
  This decides whether `len(findings) < branches` is even possible, and it is Day 49's subject
  arriving early. Write the answer down.
- **Can a `Command` target a node in a parent graph?** Not needed today; Day 48's subgraphs will ask.
- `https://docs.langchain.com/oss/python/langgraph/graph-api` — the branching and `Send` sections.

---

## §9 Say it in an interview

> "I built the same severity router in four frameworks, and in LangGraph I deliberately used a
> conditional edge rather than `Command`, because the edge keeps the routing table in the graph
> structure where it shows up in the drawing and a reviewer can see every branch — `Command` hides
> the target in a function body. I'd use `Command` where the state update and the jump are one atomic
> decision, like a supervisor recording which subagent it picked. The part I'd actually demo is the
> fan-out: `Send` gives you N parallel branches where N is discovered at runtime, and each branch gets
> its own private payload rather than the whole state — so a research branch structurally cannot see
> the raw customer text, and there's a test asserting the payload has exactly two keys. That's a
> better answer than the two I'd built earlier: deleting the field before the risky step made ordering
> a security property, and a write-once reducer stops tampering but not reading. And the fan-out only
> works because every branch writes to a field with a commutative reducer — otherwise five parallel
> writes would either clobber each other or make the result depend on the scheduler."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 44
```
