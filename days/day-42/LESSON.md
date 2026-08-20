---
day: 42
phase: 6
phase_name: "LangChain 1.x"
title: "The LangChain↔LangGraph seam + ADR-002"
ids: ["LC-13", "LC-14"]
kind: gate
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 42 — The seam, and the Phase-6 gate

**Phase 6 · LangChain 1.x** · IDs: **LC-13 🛠️**, **LC-14 🛠️** · **🎯 gate day**

> **Yesterday:** two scoping decisions, written down, with tests that enforce them.
> **Today:** the gate. `create_agent` returns a graph (Day 38 proved it), so today you drop that graph
> **into a bigger graph** as a single node — and Phase 7 stops feeling like a new framework and starts
> feeling inevitable. Then ADR-002: middleware vs. guardrails vs. task validation, one table, three
> frameworks.
> **Tomorrow:** Phase 7 opens and you build the outer graph yourself.

```bash
./m start 42
./m scaffold 42
```

---

## §1 ⚠️ A plan-internal inconsistency to resolve first

**Stop and read this before installing anything.** (Principle 14.)

LC-13's row says: *"`create_agent` returns a graph: drop it into a larger `StateGraph` as a node."*
That requires `langgraph` — but `docs/PINS.md`'s ledger adds `langgraph==1.2.11` on **Day 43**, not
today.

**What is actually true on your machine:** `langgraph` is almost certainly already installed, as a
transitive dependency of `langchain`, because `create_agent` builds a compiled graph. Day 38's
`what_is_it.py` printed a class whose module contained `langgraph`. Check:

```bash
uv run python -c "import langgraph; print(langgraph.__version__)"
grep -n 'langgraph' pyproject.toml || echo "NOT a direct dependency"
```

**So the code will run today and the pin is not yours.** That is precisely the situation Principle 4
exists to prevent: *"every package is version-pinned in pyproject.toml. Never rely on framework
defaults."* A transitively-installed, unpinned `langgraph` can move under you when `langchain` bumps.

**Resolution taken by this lesson:** pull the `langgraph` pin forward to **Day 42**, since today is
the day it is first *used directly*.

```bash
printf "%-12s " langgraph
curl -s --max-time 30 "https://pypi.org/pypi/langgraph/json" \
  | python -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"

uv add "langgraph==1.2.11"     # or the patch you just verified
```

- Update the `docs/PINS.md` ledger row from Day 43 to Day 42.
- Log the amendment in `docs/CHANGELOG_PLAN.md` as a plan-internal fix, in the same shape as the ten
  logged on 2026-08-20.
- **This is overrulable.** If you would rather Day 42 demonstrate the seam without importing
  `langgraph` directly — possible, but it means not building a `StateGraph`, which is most of LC-13 —
  say so and record that instead. Day 43 is unaffected either way: its teaching is the same, and only
  the ledger row moves.

The habit being trained is not "spot the bug". It is: **the ecosystem or the plan disagrees with
reality → the plan is amended in writing → then the code changes.**

---

## §2 Setup — run this

### 2.1 After §1

```bash
uv run pytest -q
git status --porcelain
```

- A gate day adds no dependencies *except* the one §1 just argued for. That exception is documented,
  which is the difference between an amendment and a drift.

### 2.2 Create today's files

```bash
mkdir -p days/day-42/lab
touch src/mandala/lc/seam.py
touch tests/test_seam.py
touch days/day-42/lab/seam_demo.py
touch docs/adr/ADR-002-extension-mechanisms.md
```

- `seam.py` in `src/`, not in `days/` — **this one is not an experiment.** Day 48's subgraphs and Day
  78's capstone both consume the same pattern, and the plan's LC-13 row calls it "the bridge lab that
  makes Phase 7 feel inevitable".
- ADR-002 is named in the plan's Phase-6 gate sentence. The number is fixed; use it.

---

## §3 LC-13 — the seam

### 3.1 The idea in one paragraph

`create_agent` returns a `CompiledStateGraph`. A `CompiledStateGraph` is a **Runnable**. A node in a
`StateGraph` is any callable over state. Therefore an agent is a node.

That chain is short and it is the whole of LC-13. What it buys is the answer to a question every one
of the four frameworks eventually raises: **what do I do when the agent is right for one step and
wrong for the whole workflow?** Days 30–35 answered it in CrewAI by putting a crew inside a flow
step. Today's answer is the same shape with better typing — and Phase 7 is that answer taken
seriously.

### 3.2 `src/mandala/lc/seam.py`

```python
"""The bridge: a create_agent agent, running as ONE node of a larger graph.

Why this file is in src/ and not days/
--------------------------------------
This is the pattern Mandala keeps. Day 48 composes subgraphs, Day 78 assembles the
capstone, and both do exactly what this file does: put an agent-shaped thing inside
a workflow-shaped thing and translate state at the boundary.

The translation is the interesting part, and it is the same asymmetry Day 31 found
at the crew boundary: going IN you choose fields; coming OUT you must interpret.

Usage
-----
    >>> graph = build_triage_graph()
    >>> graph.invoke({"ticket_id": "T-9002", "ticket_body": "..."})   # doctest: +SKIP
"""

from __future__ import annotations

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from mandala.lc.agent import triage_agent
from mandala.schemas import TriageResult


def keep_first(existing: str, incoming: str) -> str:
    """Reducer: the ticket body is written once, by intake, and never overwritten."""
    return existing or incoming


class WorkflowState(TypedDict, total=False):
    """The OUTER graph's state. Deliberately not the agent's message list."""

    ticket_id: str
    ticket_body: Annotated[str, keep_first]
    triage: TriageResult | None
    lane: Literal["fast", "deep", "escalate"] | None
    notes: list[str]


def triage_node(state: WorkflowState) -> dict:
    """Run the LangChain agent as one step. Translate in, translate out."""
    agent = triage_agent()
    result = agent.invoke({
        "messages": [HumanMessage(
            f"<ticket id={state['ticket_id']}>\n{state['ticket_body']}\n</ticket>"
        )]
    })

    triage = result.get("structured_response")
    turns = sum(1 for m in result["messages"] if type(m).__name__ == "AIMessage")
    return {
        "triage": triage,
        "notes": [f"triage_node: {turns} model turns"],
    }


def route_node(state: WorkflowState) -> dict:
    """Plain Python. No model. Day 31's router, third framework."""
    triage = state.get("triage")
    if triage is None or triage.severity == "critical":
        return {"lane": "escalate", "notes": ["route: escalate"]}
    if triage.severity == "low":
        return {"lane": "fast", "notes": ["route: fast"]}
    return {"lane": "deep", "notes": ["route: deep"]}


def build_triage_graph():
    """Three nodes, one of which is an entire LangChain agent."""
    graph = StateGraph(WorkflowState)
    graph.add_node("triage", triage_node)
    graph.add_node("route", route_node)
    graph.add_edge(START, "triage")
    graph.add_edge("triage", "route")
    graph.add_edge("route", END)
    return graph.compile()
```

**Line by line:**

- `class WorkflowState(TypedDict, total=False)` — **the outer graph has its own state, and it is not
  the agent's message list.** This is the design decision of the day. The agent thinks in messages;
  the workflow thinks in `ticket_id` / `triage` / `lane`. Collapsing them — making the outer state
  just `messages` — is the mistake that turns a workflow into a very long conversation, and it is the
  most common one.
- `total=False` means keys are optional, which is what you want for state that fills up as the graph
  runs.
- `Annotated[str, keep_first]` — **a reducer**, and this is your first one (LG-02 formally arrives on
  Day 43). A reducer says *how* two writes to the same key combine. Default is replace; `keep_first`
  means the ticket body cannot be overwritten by a later node. **Write-once state is a security
  primitive**, and it is a nicer answer than Day 30's `drop_body()`, because deletion required
  ordering discipline and this does not.
- `notes: list[str]` — currently replace-on-write, which is almost certainly wrong: two nodes both
  returning `notes` will clobber each other. **Leave it wrong today and find out**, because Day 43's
  `add_messages`-style append reducer is the fix and discovering the need for it is worth more than
  being handed it. Note the observation in your ADR.
- `triage_node(state) -> dict` — a node **returns a partial state update**, not the whole state. The
  graph merges it using the reducers. Compare Day 31's flow steps, which mutated `self.state`
  directly: **returning an update is testable in a way that mutating shared state is not**, and §5
  exploits that.
- `agent = triage_agent()` **inside** the node — constructed per call. Simple, and slightly wasteful.
  Hoisting it to module level would be faster and would bind the model at import time, which breaks
  the monkeypatch-based tests from Days 36–39. **Correctness of the test surface beats a microsecond**;
  say so rather than leaving it looking accidental.
- The delimited ticket string — Day 38's hygiene, unchanged.
- `turns = sum(...)` folded into `notes` — **the request count, captured at the seam.** The outer
  graph now records what the inner agent cost, which is exactly what you will want on Day 76 and
  cannot recover later.
- `route_node` makes **no model call** — Day 31's rule, third implementation (SDK handoff Day 13,
  CrewAI `@router` Day 31, plain function today). Same business logic, three loci of control, and
  today's is the plainest of the three.
- `graph.add_edge(START, "triage")` — `START` and `END` are sentinels, not strings you invent.
- `graph.compile()` returns the same kind of object `create_agent` returned. **A graph containing an
  agent is a graph, and it composes again.** That closure property is why Phase 7 exists.

### 3.3 `days/day-42/lab/seam_demo.py`

```python
"""Run the outer graph and show the agent living inside it.

Run:
    uv run python days/day-42/lab/seam_demo.py T-9002

Budget: <= 6 requests (one agent run inside one graph run).
"""

import sys

from mandala.lc.seam import build_triage_graph
from mandala.sdk_tools import RAW_TICKETS

ticket_id = sys.argv[1] if len(sys.argv) > 1 else "T-9002"

graph = build_triage_graph()
print(graph.get_graph().draw_ascii())

final = graph.invoke({
    "ticket_id": ticket_id,
    "ticket_body": RAW_TICKETS[ticket_id]["body"],
})

print(f"\ntriage  {final.get('triage')}")
print(f"lane    {final.get('lane')}")
print(f"notes   {final.get('notes')}")
print(f"body    {len(final.get('ticket_body', ''))} chars (kept by the reducer)")
```

**Line by line:**

- `graph.get_graph().draw_ascii()` printed **before** invoking — three nodes, and the agent is one
  box. Put this next to Day 38's drawing of the agent's own internal graph. **Two pictures, one
  nested inside the other**, is the clearest statement of what LC-13 means, and it belongs in ADR-002.
- `graph.invoke({...})` with the **workflow's** keys, not `messages` — the outer contract in action.
- `final.get('notes')` — check whether both nodes' notes survived. Per §3.2 they probably did not,
  and that observation is deliberate.
- The `ticket_body` length line demonstrates `keep_first` actually kept it.

---

## §4 LC-14 — the gate

### 4.1 Gate criteria, from the plan

> *"middleware-hardened `create_agent` Triage; provider-swap test green; ADR-002 'middleware vs.
> guardrails vs. task validation — one comparison table.'"*

| # | Claim | Proved by | ✓ |
|---|---|---|---|
| 1 | The agent is middleware-hardened | `MIDDLEWARE[0]` is the scrubber (Day 39 test) | ⬜ |
| 2 | Secrets never reach a provider | `test_each_pattern_redacts` + one real run | ⬜ |
| 3 | The same agent runs on two providers | **provider-swap test, green** (§4.2) | ⬜ |
| 4 | The loop is capped | `test_the_loop_is_capped` (Day 38) | ⬜ |
| 5 | Structured output is `TriageResult`, unmodified | `test_the_schema_is_still_day_4s` | ⬜ |
| 6 | The model cannot forge a `request_id` | `test_the_model_cannot_see_the_request_id` | ⬜ |
| 7 | Progress never leaks model text | `test_model_text_is_never_yielded_verbatim` | ⬜ |
| 8 | The agent runs as a node in a bigger graph | `seam_demo.py` output + `tests/test_seam.py` | ⬜ |
| 9 | Scope decisions are enforced | `tests/test_scope.py` (Day 41) | ⬜ |
| 10 | ADR-002 written | `docs/adr/ADR-002-extension-mechanisms.md` | ⬜ |
| 11 | Pins re-verified; drift logged or nil-reported | `docs/CHANGELOG_PLAN.md`, today's date | ⬜ |
| 12 | The §1 amendment is written down | `docs/CHANGELOG_PLAN.md` + `docs/PINS.md` | ⬜ |

### 4.2 The provider-swap test — the row that is uniquely Phase 6's

This is the gate criterion no other phase has, and it is the one that tests LangChain's actual claim.

```python
@pytest.mark.live
@pytest.mark.parametrize("factory_name", ["fast_loop", "workhorse"])
def test_the_same_agent_answers_on_two_providers(factory_name):
    """LC-02's claim, at agent level. 2 requests -- excluded from the default run."""
    from mandala.lc import chat
    from langchain.agents import create_agent
    from langchain_core.messages import HumanMessage

    from mandala.lc.tools import READ_TOOLS
    from mandala.prompts import TRIAGE_SYSTEM
    from mandala.schemas import TriageResult

    agent = create_agent(
        model=getattr(chat, factory_name)(),
        tools=READ_TOOLS,
        system_prompt=TRIAGE_SYSTEM,
        response_format=TriageResult,
    )
    out = agent.invoke({"messages": [HumanMessage("Checkout returns 500 for everyone.")]})
    result = out["structured_response"]

    assert isinstance(result, TriageResult)
    assert result.severity in {"low", "normal", "high", "critical"}
```

**Line by line:**

- `@pytest.mark.live` — the marker `pyproject.toml` declared on Day 0: *"hits a real provider; costs
  free-tier quota; excluded from the default run"*. **This is the first test in the plan that earns
  it.** `./m check` runs `pytest -q` without `-m live`, so the gate's expensive test does not fire on
  every check — which is exactly why the marker was defined before anything needed it.
- Two providers, **not three.** The judge is OpenRouter at 50 RPD and it is reserved for evals (plan
  §2.1 rule 1). Swapping across two proves the claim; the third would spend a scarce resource on a
  point already made.
- **The assertions are about shape, not content.** Two different models will classify differently, and
  asserting `severity == "high"` would make this a flaky test about model behaviour instead of a
  stable test about the abstraction. **Assert what the framework promises; never assert what the model
  chose.** That distinction is the single most useful testing lesson in the whole plan, and today is
  where it becomes concrete.
- Build the agent inline rather than calling `triage_agent()` — because the point is *swapping the
  model*, and the factory pins one. Say so in a comment.

### 4.3 ADR-002

The plan names the table: **middleware vs. guardrails vs. task validation.** You have built all
three.

```markdown
# ADR-002 — Extension mechanisms across three frameworks

Status: accepted · Date: 2026-08-__ · Context: end of Phase 6

## The comparison

| | SDK guardrails (D12) | CrewAI task guardrails (D27) | LC middleware (D39) |
|---|---|---|---|
| Where it runs | run boundary | after a task's output | inside the loop, per turn |
| Can it stop the run? | | | |
| Can it *rewrite* the payload? | | | |
| Does it see every model call? | | | |
| Cost per agent run | | | |
| Retries on failure? | | | |
| Testable without a provider? | | | |
| What it cannot do | | | |

## Decision
<which mechanism Mandala uses for which job, and why not one mechanism for all three>

## The thing that surprised me
<one paragraph>

## Consequences
<what this commits Phase 7 and the capstone to>
```

**Why these rows:**

- **"Can it rewrite the payload?"** is the row that actually separates them. Guardrails and task
  validators *judge*; middleware *edits*. That is more power and a larger blast radius — a buggy
  validator rejects a good answer, a buggy middleware silently changes every prompt.
- **"Cost per agent run"** — a guardrail runs once, middleware runs per turn. On a free tier that
  multiplier is the design constraint, and putting a number in this cell is worth more than an
  adjective.
- **"Testable without a provider?"** — Days 36–40 answered yes for LangChain, using
  `FakeListChatModel` and monkeypatching. Answer it honestly for the other two.
- **The decision section must not be "middleware, it's the newest".** Mandala genuinely uses
  different mechanisms in different places, and the ADR is where you justify the mix.

---

## §5 `tests/test_seam.py`

```python
"""The seam is a translation layer. Test the translation. 0 model requests."""

from pathlib import Path

import pytest

from mandala.lc import seam
from mandala.lc.seam import WorkflowState, build_triage_graph, keep_first, route_node
from mandala.schemas import TriageResult


def triaged(severity: str) -> WorkflowState:
    return {
        "ticket_id": "T-9002",
        "triage": TriageResult(severity=severity, category="billing", summary="fixture"),
    }


@pytest.mark.parametrize(
    ("severity", "lane"),
    [("low", "fast"), ("normal", "deep"), ("high", "deep"), ("critical", "escalate")],
)
def test_the_router_is_the_same_policy_as_day_31(severity, lane):
    assert route_node(triaged(severity))["lane"] == lane


def test_an_unclassified_ticket_escalates():
    """Third framework, same flip-it test. Delete the None branch and this goes red."""
    assert route_node({"ticket_id": "T-9002"})["lane"] == "escalate"


def test_the_router_makes_no_model_call(monkeypatch):
    monkeypatch.setattr(seam, "triage_agent",
                        lambda *a, **k: pytest.fail("route_node built an agent"))
    assert route_node(triaged("low"))["lane"] == "fast"


def test_the_body_is_write_once():
    """The reducer IS the security control here -- nicer than Day 30's deletion."""
    assert keep_first("original ticket text", "injected replacement") == "original ticket text"
    assert keep_first("", "first write") == "first write"


def test_the_outer_state_is_not_a_message_list():
    """The design decision of the day, asserted."""
    assert "messages" not in WorkflowState.__annotations__
    assert {"ticket_id", "triage", "lane"} <= set(WorkflowState.__annotations__)


def test_the_graph_has_the_expected_shape():
    graph = build_triage_graph().get_graph()
    assert {"triage", "route"} <= set(graph.nodes)


def test_the_seam_records_what_the_agent_cost(monkeypatch):
    """Principle 5: the outer graph must capture the inner agent's turn count."""
    class FakeAgent:
        def invoke(self, payload):
            from langchain_core.messages import AIMessage
            return {"messages": [AIMessage("x"), AIMessage("y")], "structured_response": None}

    monkeypatch.setattr(seam, "triage_agent", lambda *a, **k: FakeAgent())
    out = seam.triage_node({"ticket_id": "T-1", "ticket_body": "b"})
    assert any("2 model turns" in note for note in out["notes"])


def test_langgraph_is_a_direct_dependency():
    """§1's amendment, enforced. Flip it: remove the pin and this goes red."""
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "langgraph==" in text, "Principle 4: pin it directly, do not inherit it"
```

**Line by line:**

- `test_the_router_is_the_same_policy_as_day_31` — **the same four rows as Day 31's table**, third
  framework. Running an identical policy test across frameworks is how the bake-off gets an
  apples-to-apples row instead of an impression.
- `test_an_unclassified_ticket_escalates` — the same flip-it test, third time. **A test you can port
  unchanged between frameworks is a sign your policy is genuinely framework-independent**, which is
  the plan's whole thesis and now has evidence.
- `test_the_body_is_write_once` tests the **reducer as a security control**, with an injection-flavoured
  second argument. Two assertions: it keeps an existing value, and it accepts a first write.
- `test_the_outer_state_is_not_a_message_list` asserts the §3.2 design decision. It will fail the day
  someone "simplifies" the workflow state into a conversation, which is the exact wrong turn.
- `test_the_seam_records_what_the_agent_cost` uses a **hand-rolled fake agent** — nine lines, no
  framework, no key. Fourth day running that the test surface is stubbed rather than live.
- `test_langgraph_is_a_direct_dependency` — **§1's amendment, made executable.** If you overruled §1
  and chose not to pin `langgraph` today, delete this test *and write down that you did*. A gate is
  where decisions get recorded, not quietly reversed.
- **Zero model requests.** The one live test in the gate is §4.2's, and it is marked.

---

## §6 The standing gate freshness check

Every gate carries it (Part 5). Do it now:

```bash
for p in langchain langchain-core langgraph langchain-google-genai langchain-groq langchain-openai; do
  printf "%-26s " "$p"
  curl -s --max-time 30 "https://pypi.org/pypi/$p/json" \
    | python -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
done
```

- Compare against `docs/PINS.md`. Patch → pin and log. Minor/major → **addendum first** (Principle 14).
- **This phase has form.** `langchain` moved 1.2 → 1.3 before the plan started and 1.3.15 → 1.3.16
  during Day 1. Expect movement; the discipline is what makes it uneventful.
- Check the MCP spec revision too. Not used yet, ten seconds, and Day 53 will thank you.
- **Nothing moved? Write "checked, unchanged".** A nil report is the deliverable of the habit
  (Principle 13).

---

## §7 Traps

- **Installing `langgraph` without writing the amendment.** §1 is the day's first lesson and the
  easiest to skip.
- **Making the outer state a message list.** The workflow becomes a conversation and Phase 7 loses
  its point.
- **Assuming `notes` accumulates.** It replaces. Find that out today; it is the motivation for Day
  43's reducers.
- **Hoisting the agent to module level** for speed, and breaking every monkeypatched test.
- **Asserting model output in the provider-swap test.** It becomes a flaky test about model behaviour
  rather than a stable test about the abstraction.
- **Running the live test in `./m check`.** That is what `@pytest.mark.live` prevents; confirm the
  default run skips it.
- **Swapping across all three providers.** The judge is 50 RPD and reserved for evals.
- **Writing ADR-002 as a feature list.** The plan asked for a comparison table with a decision under
  it.
- **Concluding "middleware wins" in the ADR.** Mandala uses all three mechanisms; the ADR justifies
  the mix.
- **Skipping the freshness check because the gate ran long.** Smallest item, only compounding one.

---

## §8 Request budget

**Declared: ~10 model requests, Groq + Gemini.**

| What | Requests |
|---|---|
| All non-live tests | **0** |
| `seam_demo.py` | ≤ 6 |
| `pytest -m live` — provider-swap, two providers | 2 |
| One re-run allowance | ≤ 2 |

Phase 6 total should land near **60 requests across seven days** — the cheapest framework phase so
far. Compare against Phase 5 in the ledger and put the number in ADR-002: **"free-tier friendliness"
is a scorecard row in the plan's Phase-9 bake-off**, and you now have real numbers for two frameworks
instead of impressions.

---

## §9 Done when

Phase 6 is complete when every row in §4.1 is green and ADR-002 exists.

```bash
./m check
./m done 42
```

Then read Day 43's §1. Phase 7 is ten days of LangGraph, and you arrive already holding three things
from today: a `StateGraph`, a reducer, and the knowledge that an agent is just a node. **Write down
today what you expect Days 43, 47 and 50 to feel like** — you made predictions on Day 35 about the
same three days, and comparing your two guesses against the reality is worth more than either.
