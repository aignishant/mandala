---
day: 30
phase: 5
phase_name: "CrewAI Flows"
title: "Flows: @start, @listen, and typed state"
ids: ["CR-14", "CR-15"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 30 — Flows: `@start`, `@listen`, and typed state

**Phase 5 · CrewAI Flows** · IDs: **CR-14 🛠️**, **CR-15 🛠️**

> **Yesterday:** the Phase-4 gate — Mandala-mini, and three collisions that only existed once the
> parts were assembled.
> **Today:** the same framework's *other* answer to who owns the loop, and a seam that is finally
> typed — but global, which is a new problem you have not had before.
> **Tomorrow:** routers, and crews running inside flows.

```bash
./m start 30
./m scaffold 30
```

---

## §1 The story

The thesis this whole plan hangs on is *who owns the loop?* You have three answers so far:

- **OpenAI Agents SDK** — the model owns it.
- **CrewAI Crews** — roles own it.
- **LangGraph** — you own it (Phase 7, still ahead).

Today something odd and genuinely interesting happens: **CrewAI gives a second answer.** Flows are
not crews with extra steps. They are an event-driven state machine where *you* write the steps, *you*
decide what follows what, and no model chooses control flow at all.

| | **Crews** (Days 23–29) | **Flows** (today) |
|---|---|---|
| Who decides order | the process, or a manager LLM | **you**, in decorators |
| Unit | Task | a Python method |
| State between steps | previous task's output text | **a typed object you define** |
| Model involvement in control flow | total (hierarchical) or none (sequential) | **none** |
| What it resembles | a team | **a state machine** |
| Closest thing in this plan | — | **LangGraph (Day 43)** |

**That last row is the one to hold on to.** The plan's CR-15 row says explicitly: *"mirrors LangGraph
state, Day 43 — compare deliberately."* You are going to meet this exact design twice, thirteen days
apart, in two different frameworks. Everything you notice today is a free head start, so write it in
the bake-off list as you go.

And there is a seam story, which by now you should expect. Day 24 found the crew seam was **untyped
and unfiltered**. Day 26 typed it. Day 27 gave it a mechanical check. Flow state arrives **typed from
the start** — a Pydantic model you wrote — which is a real improvement.

But it is **global to the run**. Every step sees the whole state object. The crew seam was narrow and
untyped; flow state is wide and typed. Those are different trades, not a strict upgrade, and §4.4 is
about the one place that matters: Day 8's rule that the Writer never sees the raw ticket.

---

## §2 Setup — run this

No new packages — Flows ship inside `crewai==1.15.17`.

```bash
mkdir -p days/day-30/lab
mkdir -p src/mandala/flows
touch src/mandala/flows/__init__.py
touch src/mandala/flows/state.py
touch src/mandala/flows/intake.py
touch days/day-30/lab/first_flow.py
touch days/day-30/lab/state_trap.py
touch tests/test_flow_state.py
```

**Do yesterday's freshness note first if you skipped it.** The plan's Part 2 warns that CrewAI's
declarative-flow surface is the fastest-moving thing in this project, and you are now standing on it:

```bash
uv run python -c "import crewai; print(crewai.__version__)"
uv run python -c "from crewai.flow.flow import Flow, listen, start; print('flow API ok')"
```

**TODO(me):** confirm the import path for 1.15.17. `crewai.flow.flow` is what this lesson assumes;
it has also lived at `crewai.flow`. If yours differs, fix it once here and note it — the rest of
Phase 5 imports from wherever you land.

---

## §3 CR-14 — `@start`, `@listen`, and the shape of a flow

### 3.1 The two decorators

```python
class MyFlow(Flow[MyState]):

    @start()
    def intake(self):
        self.state.ticket_id = "T-1004"
        return "loaded"

    @listen(intake)
    def classify(self, previous):
        ...
```

- `@start()` — an entry point. A flow may have more than one; they all run when you `kickoff()`.
- `@listen(method)` — runs **when that method finishes**, receiving its return value.
- `self.state` — the shared, typed object every step reads and writes.
- `kickoff()` — runs the flow and returns the last method's result.

Two things are worth noticing immediately, because they are what make a flow *readable*:

1. **The graph is in the decorators.** You do not write a scheduler or an order list; the wiring is
   declared next to each step. `@listen(classify)` says "after classify" at the place where it
   matters.
2. **A method receives the previous return value *and* can read all of `self.state`.** Two channels,
   and choosing between them per step is a real design decision — §4.4 argues you should prefer the
   return value for the *result* and state for *accumulated context*, and be deliberate about it.

### 3.2 `src/mandala/flows/state.py`

```python
"""The flow's state: one typed object, and the contract between every step.

Why this file matters more than intake.py
-----------------------------------------
In a Crew, what crossed between tasks was the previous task's output TEXT -- untyped
and, until Day 27, unchecked. In a Flow the seam is this class. That is better in
every way except one: state is GLOBAL to the run. Every step sees all of it.

So the design rule for Mandala is not "put everything useful in state". It is:

    state holds what LATER steps legitimately need, and nothing else.

The raw ticket body is the test case. The classifier needs it. The writer must
never see it (Day 8). If the body lives in state for the whole run, the writer
sees it -- typed, validated, and just as leaked as it would have been in prose.
See intake.py's `drop_body()` and §4.4.

Usage
-----
    >>> s = MandalaState(ticket_id="T-1004")
    >>> s.ticket_body is None
    True
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from mandala.schemas import TriageResult          # Day 4. Fourth framework, same schema.


class MandalaState(BaseModel):
    """Everything the flow knows. Typed, bounded, and deliberately small."""

    # --- identity -------------------------------------------------------
    ticket_id: str = Field(default="", max_length=20)
    request_id: str = Field(default="", max_length=64)

    # --- transient: present only while a step needs it ------------------
    ticket_body: str | None = Field(
        default=None,
        max_length=20_000,
        description="RAW CUSTOMER TEXT. Dropped as soon as classification is done.",
    )

    # --- accumulated results --------------------------------------------
    triage: TriageResult | None = None
    findings: list[str] = Field(default_factory=list, max_length=6)
    sources: list[str] = Field(default_factory=list, max_length=8)
    draft: str | None = Field(default=None, max_length=4000)

    # --- audit -----------------------------------------------------------
    steps: list[str] = Field(default_factory=list, max_length=32)
    stage: Literal["new", "classified", "researched", "drafted", "failed"] = "new"

    def record(self, step: str) -> None:
        """Append to the audit trail. The flow's own trace (Principle 8)."""
        self.steps.append(step)
```

**Line by line:**

- **The comment headers are load-bearing.** `# transient` versus `# accumulated results` is not
  decoration; it is the classification that tells the next reader which fields are supposed to
  disappear. A state model without that distinction becomes a bag where everything survives forever.
- `ticket_body: str | None` with the **shouting description** — `"RAW CUSTOMER TEXT. Dropped as soon
  as classification is done."` The field's docstring is where a future you will look before deciding
  whether it is safe to read it in a new step.
- `max_length` on every string and list — Day 4's context budget and Day 8's `Field(max_length=5)`
  instinct, applied to the seam. **State is prompt material**; an unbounded state field is an
  unbounded prompt.
- `triage: TriageResult | None` — the Day-4 schema, now in its **fourth** framework (raw client, SDK
  `output_type`, CrewAI `output_pydantic`, flow state). At this point the claim that the schema was
  the durable artifact is not a rhetorical flourish; it is an observation with four data points.
- `stage: Literal[...]` — a countable state machine position rather than free text. Day 13 made the
  same call for `HandoffReason.reason`, and for the same reason: **Day 71 counts things, and a
  `Literal` can be counted.**
- `steps: list[str]` and `record()` — the flow keeps its own audit trail *inside* state. Cheap, and it
  means `state.steps` answers "what actually ran" without a debugger. Compare Day 5's naked `Trace`:
  the same idea, four weeks later, in a framework.
- `default_factory=list` — Day 4's mutable-default rule. Fourth framework, same trap, still there.

### 3.3 `src/mandala/flows/intake.py`

```python
"""Mandala's intake flow: load -> classify -> research -> draft, deterministically.

No model decides what happens next in this file. That is the whole point of a Flow,
and it is the opposite of the hierarchical crew you built on Day 25.

Usage
-----
    >>> flow = IntakeFlow()
    >>> result = flow.kickoff(inputs={"ticket_id": "T-1004"})
"""

from __future__ import annotations

from crewai.flow.flow import Flow, listen, start

from mandala.flows.state import MandalaState
from mandala.sdk_tools import RAW_TICKETS


class IntakeFlow(Flow[MandalaState]):
    """A typed state machine you can read top to bottom."""

    @start()
    def load(self) -> str:
        """Fetch the ticket. This is the only step allowed to touch the raw body."""
        self.state.ticket_id = self.state.ticket_id or "T-1004"
        self.state.request_id = f"req-{self.state.ticket_id}"
        self.state.ticket_body = RAW_TICKETS[self.state.ticket_id]["body"]
        self.state.record("load")
        return self.state.ticket_id

    @listen(load)
    def classify(self, ticket_id: str) -> str:
        """Classify from the raw body -- then DROP it. See §4.4."""
        body = self.state.ticket_body or ""

        # TODO(me): call the Day-29 triage agent here instead of this placeholder.
        # Keep the shape: read body, write self.state.triage, then drop_body().
        raise NotImplementedError("wire the classifier, then call self.drop_body()")

    @listen(classify)
    def research(self, category: str) -> list[str]:
        """Gather findings. Reads state.triage, NOT state.ticket_body (it is gone)."""
        assert self.state.ticket_body is None, "the body must be dropped before research"
        self.state.stage = "researched"
        self.state.record("research")
        # TODO(me): call the Day-29 researcher; append cited findings to state.findings
        return self.state.findings

    @listen(research)
    def draft(self, findings: list[str]) -> str:
        """Write the customer reply from findings only. Day 8's rule, enforced by absence."""
        assert self.state.ticket_body is None, "the writer must never see raw ticket text"
        self.state.stage = "drafted"
        self.state.record("draft")
        # TODO(me): call the Day-29 writer with state.findings and state.sources
        return self.state.draft or ""

    # --- helpers ---------------------------------------------------------

    def drop_body(self) -> None:
        """Remove the raw ticket from state the moment nothing legitimately needs it.

        This is the whole security design of the flow, and it is one line. State is
        global to the run, so the ONLY way to keep the writer from seeing raw text is
        for the raw text not to be there.
        """
        self.state.ticket_body = None
        self.state.record("drop_body")
```

**Line by line:**

- `class IntakeFlow(Flow[MandalaState])` — the state type is a **generic parameter**, so `self.state`
  is typed and your editor knows the fields. That is a genuine ergonomic win over the crew seam, and
  it is the same shape LangGraph uses on Day 43.
- Reading the class top to bottom **is** reading the graph: `load` → `classify` → `research` →
  `draft`. Compare Day 25's hierarchical crew, where the order was decided at runtime by a manager
  you did not write. **A flow you can read is a flow you can review**, and reviewability is the thing
  the plan's Part 0 keeps returning to.
- `@start()` on `load` with the comment *"the only step allowed to touch the raw body"* — a rule
  stated at the place it is enforceable, then tested in §5.
- `drop_body()` and the two `assert`s in `research` and `draft` — **this is the day's security
  design.** Because state is global, scoping is achieved by *deletion*, not by access control. The
  asserts are cheap, run on every flow execution, and turn Day 8's promise into a runtime property
  rather than a convention.
- Using `assert` here is a deliberate choice worth flagging: asserts can be stripped with `python -O`.
  **TODO(me): decide whether these should be real `if ... raise`.** For a security property, "it
  vanishes under an optimisation flag" is a real objection — Day 22 made the same call about path
  checks and chose to raise.
- `classify` **ships raising `NotImplementedError`** with the required shape in the comment. It is the
  day's main rep: wire yesterday's gate crew agents into flow steps. The shape is prescribed; the
  wiring is yours.
- Each step calls `self.state.record(...)` — the audit trail accumulates as a side effect of doing the
  work, which is the only kind of audit trail people actually maintain.
- Each `@listen` takes the previous return value **and** reads state. Note the discipline: `research`
  receives `category` but reads `self.state.triage` for detail. §4.4 explains why both channels exist.

---

## §4 CR-15 — Structured state, and why unstructured is a trap

### 4.1 Flows accept either

CrewAI lets you use an untyped dict as state (`Flow` with no type parameter, `self.state["key"]`) or
a Pydantic model. **The plan's CR-15 row is unambiguous about which**: *"Pydantic state models; why
unstructured state is a trap."*

Here is the trap, in one runnable file:

```python
"""days/day-30/lab/state_trap.py -- unstructured state, and the bug it hides.

Run:
    uv run python days/day-30/lab/state_trap.py      # 0 model calls
"""

from __future__ import annotations

from pydantic import ValidationError

from mandala.flows.state import MandalaState

print("=== unstructured (dict) ===")
state: dict = {"ticket_id": "T-1004", "severity": "high"}

state["serverity"] = "low"          # a typo. Nothing complains.
print(f"keys now: {sorted(state)}")
print(f"reading state['severity'] -> {state['severity']}  (the typo is a SECOND key)")

state["ticket_id"] = 1004           # wrong type. Nothing complains.
print(f"ticket_id is now {state['ticket_id']!r} ({type(state['ticket_id']).__name__})")

print("\n=== structured (Pydantic) ===")
typed = MandalaState(ticket_id="T-1004")

try:
    typed.serverity = "low"         # type: ignore[attr-defined]
except (ValidationError, AttributeError) as exc:
    print(f"typo rejected: {type(exc).__name__}")

try:
    MandalaState(ticket_id=1004, stage="banana")
except ValidationError as exc:
    print(f"bad types rejected: {len(exc.errors())} error(s)")

print(f"\nfields are discoverable: {sorted(MandalaState.model_fields)[:5]} ...")
```

**Line by line:**

- `state["serverity"] = "low"` — **the trap in one line.** A dict silently accepts a misspelled key, a
  later step reads the correctly-spelled one, gets a stale value, and the flow produces a plausible
  wrong answer with no error anywhere. This is not hypothetical; it is the single most common bug in
  dict-state systems.
- `state["ticket_id"] = 1004` — wrong type, accepted, and it fails three steps later inside a string
  operation with a message about `int`.
- The Pydantic half rejects both **at the point of the mistake**, which is the only place a mistake is
  cheap to fix.
- `MandalaState.model_fields` — the state is **introspectable**, which is what lets §5 test properties
  of the state model itself rather than of the flow that uses it.

Four reasons, in the order that matters:

| # | Reason | What it costs you without types |
|---|---|---|
| 1 | **Typos become new keys** | a wrong answer with no error |
| 2 | **No validation at the boundary** | the failure surfaces steps later, somewhere unrelated |
| 3 | **State is the contract between steps** | nothing documents what a step may rely on |
| 4 | **You cannot test the shape** | no test can fail when the shape regresses (Principle 7) |

Reason 3 is the deepest. Day 24 taught that the seam between steps is where design lives; **flow
state is that seam, and an untyped seam is an undocumented API between every pair of steps you will
ever write.**

### 4.2 The LangGraph comparison — start it today

The plan says compare deliberately, so start the table now and finish it on Day 43:

| | **CrewAI Flow state** | **LangGraph state** (Day 43 — fill in) |
|---|---|---|
| Definition | a Pydantic model, `Flow[State]` | ? |
| Mutation | steps assign to `self.state` | ? |
| Concurrent writes | ? — see §6 | reducers |
| Persistence | `@persist` (Day 32) | checkpointers (Day 47) |
| Reading the graph | decorators on methods | explicit edges |
| Time travel | ? | Day 50 |

**Fill in the `?`s on the CrewAI side today** while the framework is in front of you — especially the
concurrent-write row, which is the one LangGraph makes a whole concept out of (reducers) and which
CrewAI may simply not address. Finding out that a framework *has no answer* to something is a real
finding and belongs in the bake-off.

### 4.3 `days/day-30/lab/first_flow.py`

```python
"""Run the flow, print the state, and look at the picture.

Run:
    uv run python days/day-30/lab/first_flow.py T-1004
"""

from __future__ import annotations

import sys

from mandala.flows.intake import IntakeFlow


def main() -> None:
    ticket_id = sys.argv[1] if len(sys.argv) > 1 else "T-1004"

    flow = IntakeFlow()
    result = flow.kickoff(inputs={"ticket_id": ticket_id})

    state = flow.state
    print(f"result      : {str(result)[:200]}")
    print(f"stage       : {state.stage}")
    print(f"steps ran   : {state.steps}")
    print(f"body dropped: {state.ticket_body is None}")
    print(f"findings    : {len(state.findings)}")

    # TODO(me): confirm plot() exists in 1.15.17 and what it writes.
    flow.plot("days/day-30/lab/intake_flow")      # an HTML graph of the flow
    print("\nwrote intake_flow.html -- open it")


if __name__ == "__main__":
    main()
```

**Line by line:**

- `flow.state` **after** `kickoff()` — the state object is the run's record. Printing `state.steps`
  answers "what actually ran" with no instrumentation, which is the payoff for §3.2's `record()`.
- `body dropped: True` printed on every run — **the security property, surfaced in the demo output.**
  A property you see on every run is a property you notice breaking.
- `flow.plot(...)` — Flows can render themselves as a graph. This is a real advantage over Crews,
  where the order was either implicit in a list or decided by a manager at runtime. **A picture of the
  control flow, generated from the code, is the strongest form of the "readable" claim** — and it is
  the same thing LangGraph Studio does on Day 43, so note the parallel.
- The `inputs={...}` dict populates state fields by name. **TODO(me): confirm whether unknown input
  keys are rejected or silently ignored in 1.15.17.** If they are ignored, a typo in `inputs` is
  §4.1's trap arriving through the front door, and §5 needs a test for it.

### 4.4 Typed but global — the new problem

This is the section to remember, and it is the one thing about Flows that is genuinely *worse* than
Crews.

| | Crew `context` (Day 24) | Flow state (today) |
|---|---|---|
| Typed | no (until `output_pydantic`) | **yes** |
| Scope | only tasks that declare `context=[...]` | **every step, always** |
| Can a later step see an earlier step's raw input? | only if it was passed forward | **yes, unless deleted** |
| How you narrow it | declare fewer dependencies | **delete the field** |

The crew seam was narrow by default and you widened it deliberately. **Flow state is wide by default
and you narrow it deliberately.** Both are workable; the failure modes are opposite, and the flow one
is quieter — nothing errors when a step reads a field it had no business reading.

For Mandala this lands exactly on Day 8's rule. The Writer must never see raw ticket text. In a flow,
the only enforcement available is **absence**: `drop_body()` after classification, plus an assert in
every downstream step.

Three properties that makes true, and one it does not:

- ✅ The Writer cannot read the body, because there is nothing to read.
- ✅ The check runs on every execution, not in review.
- ✅ It is one line, in one place, testable.
- ❌ **It does not protect against a step that runs before the drop.** Ordering is now a security
  property, which is a sentence worth being uncomfortable about. `@listen` makes ordering explicit
  and readable, so this is defensible — but it is defended by structure, not by a permission.

Write that in the bake-off list: *"Day 30: flow state is typed (better than crew context) but global
(worse). Scoping is achieved by deletion, and ordering becomes a security property."*

---

## §5 The eval that must be able to fail

### `tests/test_flow_state.py`

```python
"""The state model is the contract. Test it directly. 0 model requests."""

import pytest
from pydantic import ValidationError

from mandala.flows.state import MandalaState


def test_a_typo_is_rejected():
    """§4.1's trap. FLIP IT: use a dict for state and watch this become impossible to write."""
    state = MandalaState(ticket_id="T-1004")
    with pytest.raises((ValidationError, AttributeError, ValueError)):
        state.serverity = "low"          # type: ignore[attr-defined]


def test_wrong_types_are_rejected_at_the_boundary():
    with pytest.raises(ValidationError):
        MandalaState(ticket_id="T-1", stage="banana")


def test_the_raw_body_starts_empty():
    """It is transient. Nothing should be able to construct a state that already holds it
    by accident -- you must set it on purpose, in load()."""
    assert MandalaState(ticket_id="T-1").ticket_body is None


def test_every_string_field_is_bounded():
    """State is prompt material (Day 4). An unbounded field is an unbounded prompt."""
    for name, field in MandalaState.model_fields.items():
        if field.annotation in (str, "str") or "str" in str(field.annotation):
            assert "max_length" in str(field), f"{name} is unbounded"


def test_stage_is_countable():
    """A Literal can be counted on Day 71. Free text cannot."""
    with pytest.raises(ValidationError):
        MandalaState(ticket_id="T-1", stage="mostly done")


def test_the_schema_is_still_day_4s():
    """Fourth framework, same TriageResult. No flow-flavoured copy."""
    import mandala.schemas as schemas
    from mandala.flows.state import MandalaState as S

    assert S.model_fields["triage"].annotation.__args__[0].__module__ == schemas.__name__


def test_record_accumulates_an_audit_trail():
    state = MandalaState(ticket_id="T-1")
    state.record("load")
    state.record("classify")
    assert state.steps == ["load", "classify"]


def test_the_audit_trail_is_bounded():
    """A flow that loops must not grow state without limit."""
    state = MandalaState(ticket_id="T-1")
    with pytest.raises(ValidationError):
        state.steps = [f"s{i}" for i in range(64)]
```

### `tests/test_intake_flow.py`

```python
"""The flow's security property: the writer never sees raw ticket text. 0 model requests."""

import pytest

from mandala.flows.intake import IntakeFlow
from mandala.flows.state import MandalaState


def test_drop_body_removes_it():
    flow = IntakeFlow()
    flow.state.ticket_body = "raw customer text with PINEAPPLE-7731"
    flow.drop_body()
    assert flow.state.ticket_body is None


def test_drop_body_is_recorded():
    """A security action that leaves no trace is one you cannot audit."""
    flow = IntakeFlow()
    flow.drop_body()
    assert "drop_body" in flow.state.steps


def test_downstream_steps_refuse_to_run_with_the_body_present():
    """The assert in research/draft. FLIP IT: remove it, and a reordering silently
    exposes the writer to raw ticket text with nothing failing."""
    flow = IntakeFlow()
    flow.state.ticket_body = "raw text"
    with pytest.raises(AssertionError):
        flow.research(category="billing")


def test_the_step_order_is_declared_in_the_class():
    """A flow you can read is a flow you can review. TODO(me): assert the @listen graph
    programmatically once you find where CrewAI exposes it -- then this test protects
    the ORDER, which §4.4 says is now a security property."""
    import inspect

    source = inspect.getsource(IntakeFlow)
    assert source.index("def load") < source.index("def classify") < source.index("def draft")


@pytest.mark.skip(reason="TODO(me): wire the Day-29 agents, then assert end-to-end")
def test_a_full_run_ends_with_no_raw_text_anywhere():
    """The real test: kickoff on T-9002, then assert the canary appears in no state field."""
```

**Line by line:**

- `test_a_typo_is_rejected` is the direct test of §4.1's trap, and its flip is instructive because it
  is **impossible to write against a dict.** That is the argument for typed state in one sentence:
  the untyped version has no failure to test.
- `test_the_raw_body_starts_empty` — asserts the *transient* field is transient by default. It
  encodes the `# transient` comment from §3.2 as something that can break.
- `test_every_string_field_is_bounded` — a reflection test that is honestly a bit crude (**TODO(me):
  read the Pydantic metadata properly rather than string-matching the repr**). It catches the real
  failure, which is someone adding an unbounded `notes: str` field in six weeks.
- `test_the_schema_is_still_day_4s` — provenance again, fourth framework. Cheap insurance against the
  flow-flavoured copy.
- `test_the_audit_trail_is_bounded` — Day 31 introduces routers, and routers introduce loops. A
  bounded `steps` list means a runaway loop fails loudly instead of eating memory.
- `test_downstream_steps_refuse_to_run_with_the_body_present` is **the security test**, and its flip
  is the sharpest one today: remove the assert, and reordering the flow silently exposes the Writer.
  §4.4 said ordering is now a security property; this is what defends it.
- `test_the_step_order_is_declared_in_the_class` is deliberately crude (source-position comparison)
  with a `TODO(me)` to do it properly. **A weak test of an important property beats no test**, as long
  as its weakness is written down.

---

## §6 Traps

- **Using a dict for state because it is quicker.** A typo becomes a second key, a later step reads
  the original, and the flow produces a confident wrong answer with no error. **The trap of the day**,
  and it is the whole reason CR-15 exists.
- **Leaving the raw ticket body in state for the whole run.** Every subsequent step can read it,
  typed and validated and just as leaked. Delete it the moment nothing needs it.
- **Relying on `assert` for a security property.** `python -O` strips asserts. Decide whether these
  should raise, and write the decision down.
- **Putting everything useful in state.** State is prompt material and is global; every field you add
  is a field every future step can read.
- **Unbounded state fields.** A flow with a loop (Day 31) plus an unbounded list is a memory leak
  wearing a schema.
- **Assuming `inputs={...}` validates its keys.** If unknown keys are ignored, a typo there is §4.1's
  trap arriving through the front door. Verify.
- **Forgetting that ordering is now a security property.** In a crew, the Writer's isolation came from
  what it was passed. In a flow it comes from *when* it runs relative to `drop_body()`.
- **Not looking at `plot()`.** A generated picture of your control flow is the cheapest review tool in
  the phase, and it exists.
- **Treating Flows as "Crews but manual".** They are a different answer to who owns the loop, from the
  same vendor, and the bake-off needs them as separate rows.
- **Skipping the LangGraph comparison table.** You meet this design again on Day 43. Notes taken today
  are free; notes reconstructed on Day 43 are not.
- **Assuming concurrent writes to state are safe.** Find out. If the framework has no answer, that is
  a finding, not an omission on your part.

---

## §7 Request budget

| Activity | Requests |
|---|---|
| `state_trap.py` | **0** — pure Python |
| `first_flow.py` before the TODOs are wired | **0** — steps raise or are stubs |
| `first_flow.py` after wiring the Day-29 agents | ~18 (Groq) |
| Iterating the step wiring | ~20 (Groq) |
| **Total** | **≈ 38, Groq** |

**A cheap day after an expensive one, and that is not an accident:** flows are control flow, and
control flow costs nothing to run. Every model call today comes from the agents you wired *into* the
steps, not from the flow machinery. This is worth noticing as a design property — **the deterministic
skeleton is free; only the autonomous organs cost** — and it is exactly the argument for tomorrow's
production pattern (CR-17: deterministic flow, crew organs).

Both test files cost **0**.

---

## §8 Verify before you code

Written **2026-08-20** against `crewai` **1.15.17**.

- **The Flow import path.** `crewai.flow.flow` is assumed here; it has also lived at `crewai.flow`.
  Settle it once — the rest of Phase 5 depends on it.
- `https://docs.crewai.com/concepts/flows` — confirm `@start()` takes parentheses, whether `@listen`
  accepts a method reference **and** a string name, and what a `@listen` method receives when its
  source returns `None`.
- **Confirm `Flow[StateModel]` is how you attach a Pydantic state**, and what happens with no type
  parameter (the dict path §4.1 warns about).
- **Does `kickoff(inputs={...})` reject unknown keys?** If not, §4.1's trap has a second entrance and
  §5 needs a test. This is the most consequential small question today.
- Confirm `flow.plot()` exists, what it writes, and whether it needs an extra dependency. If it
  pulls one in, that is a ledger row and a `docs/CHANGELOG_PLAN.md` line, not a silent install.
- **Concurrent state writes** — if two `@listen` methods can run in parallel, what happens when both
  write the same field? Fill in §4.2's row. LangGraph answers this with reducers on Day 43; find out
  whether CrewAI answers it at all.
- Check whether `Flow` exposes its graph programmatically (for §5's `TODO(me)`), since that is what
  turns the crude source-order test into a real one.

---

## §9 Say it in an interview

> "CrewAI ships two answers to the same question. Crews are autonomous — you describe a team and
> roles own the loop. Flows are a typed, event-driven state machine where `@start` and `@listen`
> declare the graph and no model decides control flow at all. What I found interesting is that Flows
> look much more like LangGraph than like Crews, so one vendor spans two positions on the axis I use
> to compare frameworks. And the state model is the seam: in a crew, what crossed between tasks was
> the previous task's output text, untyped; in a flow it's a Pydantic object I define, so a typo is
> a validation error instead of a silently-created second key."

> "The catch is that flow state is global. Every step can read all of it, so it's typed but wide,
> where the crew seam was narrow but untyped — opposite failure modes rather than a straight upgrade.
> For my system that mattered in one specific place: the agent that writes customer-facing text must
> never see the raw ticket body. In a flow the only enforcement available is absence, so I delete the
> body from state the moment classification is done and assert it's gone at the top of every
> downstream step. That makes step *ordering* a security property, which is an uncomfortable sentence
> — but `@listen` makes the ordering explicit and readable, and I've got a test that fails if someone
> removes the assert."

---

## §10 Done when

```bash
./m check
./m done 30
```

Tomorrow: **`@router` and crews inside flows** — routing on state, and the production pattern the plan
has been building toward since Day 23: *a deterministic flow skeleton with autonomous crew organs.*
Yesterday's Mandala-mini becomes one of those organs, and today's `classify` step is where it plugs
in. Make sure `drop_body()` still runs before the organ that must not see raw text.
