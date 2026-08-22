---
day: 50
phase: 7
phase_name: "LangGraph 1.x"
title: "Interrupts — HITL as a runtime feature"
ids: ["LG-09", "AG-20"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 50 — `interrupt()`: HITL as a runtime feature

**Phase 7 · LangGraph 1.x** · IDs: **LG-09 🛠️**, **AG-20 🛠️**

> **Yesterday:** failure semantics, and retry ownership settled across three layers.
> **Today:** the day Day 33 was a rehearsal for. `interrupt()` pauses a graph **durably** — the
> process exits, the human takes an hour, and `Command(resume=...)` continues from exactly where it
> stopped. You built this by hand seventeen days ago; today you get it as a runtime primitive and
> find out precisely what your hand-rolled version was missing.
> **Tomorrow:** time travel and forking — rewinding to any checkpoint.

```bash
./m start 50
./m scaffold 50
```

---

## §1 The story

**AG-20 completes today.** Four implementations of "a human decides before anything leaves":

| Framework | Mechanism | Pause is durable | Needs | Day |
|---|---|---|---|---|
| Agents SDK | tool approvals (OAI-23) | no — in-memory | a held process | 21 |
| CrewAI Flows | raise + checkpoint + exit (CR-19) | **yes**, via `@persist` | ~120 lines you wrote | 33 |
| LangChain | HITL middleware (LC-08) | only with a checkpointer | 3 lines | 39 |
| **LangGraph** | **`interrupt()` + `Command(resume=…)`** | **yes, natively** | **1 line** | **today** |

Day 33's §3.4 said this explicitly: *"you are building by hand what a later framework provides as a
runtime feature — Principle 2's 'naked before framework' applied between frameworks. When Day 50
arrives, you will know precisely what it saved you."* **Today you cash that in.**

And you should be precise about *what* it saved, because the honest answer has two halves:

- **The pausing is now one line.** `interrupt()` replaces the raise, the pending-file write, the
  decision-file poll, and the idempotent re-entry. That is a real and large saving.
- **The `Decision` record is still yours.** A framework primitive gives you control flow. It does not
  store *who* approved, *why*, or *what exactly they approved* — and Principle 12 is about
  accountability, not about control flow.

**So today's design is: LangGraph's mechanism, Day 33's record.** Getting that split right is the
lesson, and it is a pattern that recurs whenever a framework offers to take over something you have
already built properly.

---

## §2 Setup — run this

### 2.1 No new packages

```bash
grep -n 'langgraph' pyproject.toml
grep -n 'langgraph-checkpoint-sqlite' pyproject.toml
```

- **An interrupt without a checkpointer is not durable.** Day 47 installed the SQLite saver; today is
  the day it becomes load-bearing rather than demonstrative. If that second grep is empty, stop.

### 2.2 Create today's files

```bash
touch src/mandala/graph/approval.py
touch tests/test_graph_approval.py
mkdir -p days/day-50/lab
touch days/day-50/lab/pause_resume.py
touch days/day-50/lab/hitl_compare.md
```

- `graph/approval.py` **imports Day 33's `Decision` model unchanged.** That reuse is the point of the
  day; if you find yourself rewriting it, stop and ask why.

---

## §3 LG-09 — `interrupt()`

### 3.1 What it actually does

```python
from langgraph.types import interrupt

def await_approval(state) -> dict:
    answer = interrupt({"draft": state["draft"], "ticket_id": state["ticket_id"]})
    return {"decision": answer}
```

Three things happen, and the third is the surprising one:

1. **`interrupt(payload)` raises a special exception** that the runtime catches. The payload is stored
   in the checkpoint and surfaced to the caller.
2. The graph **stops**, the checkpoint holds everything, and the process can exit.
3. On `Command(resume=value)`, **the node re-runs from the top**, and this time `interrupt()`
   *returns* `value` instead of raising.

**Point 3 is the one that bites people, and it is a real constraint rather than a quirk.** The node
body before the `interrupt()` call executes **twice**. So:

- **Put nothing expensive before `interrupt()`.** A model call above it runs on both passes and costs
  double.
- **Put nothing with side effects before it.** A "notify reviewer" email above the interrupt sends
  twice.
- **Keep the node small**: gather the payload, interrupt, record the answer. That is all.

This is the same shape as Day 49's idempotence rule, arriving from a different direction: **a node
that may re-run must be safe to re-run.** Yesterday it was retries; today it is resumption. Two
mechanisms, one property.

### 3.2 `src/mandala/graph/approval.py`

```python
"""The approval gate, fourth framework: LangGraph's mechanism, Day 33's record.

The split matters and it is the lesson of the day:

  MECHANISM (framework)  interrupt() pauses durably; Command(resume=) continues.
  RECORD    (ours)       WHO decided, WHY, and WHAT they approved -- Day 33's
                         Decision model, imported unchanged.

A framework primitive gives you control flow. Principle 12 is about accountability,
which no primitive supplies. So we take the pausing and keep the record.

RE-ENTRY WARNING (LESSON §3.1): everything above interrupt() runs TWICE. Keep this
node tiny and side-effect free above the call.

Usage
-----
    >>> from mandala.graph.approval import await_approval_node
"""

from __future__ import annotations

import hashlib

from langgraph.types import interrupt

from mandala.flows.approval import Decision      # Day 33, imported UNCHANGED


def proposal_fingerprint(draft: str) -> str:
    """A stale decision must not authorise a changed draft (Day 33 §6, deferred to Day 82)."""
    return hashlib.sha256(draft.encode("utf-8")).hexdigest()[:16]


def await_approval_node(state) -> dict:
    """Pause until a human answers. Nothing above interrupt() may cost or mutate."""
    draft = state.get("draft") or ""
    fingerprint = proposal_fingerprint(draft)

    answer = interrupt({
        "ticket_id": state.get("ticket_id", ""),
        "draft": draft,
        "fingerprint": fingerprint,
    })

    decision = answer if isinstance(answer, Decision) else Decision(**answer)

    if answer_fingerprint := (answer.get("fingerprint")
                              if isinstance(answer, dict) else None):
        if answer_fingerprint != fingerprint:
            return {
                "stage": "escalated",
                "notes": [f"decision rejected: approved a different draft "
                          f"({answer_fingerprint} != {fingerprint})"],
            }

    if not decision.authorises_send():
        return {
            "stage": "escalated",
            "decision": decision,
            "notes": [f"decision:{decision.outcome}:{decision.reviewer}"],
        }

    return {
        "draft": decision.final_text(draft),
        "stage": "approved",
        "decision": decision,
        "notes": [f"decision:{decision.outcome}:{decision.reviewer}"],
    }
```

**Line by line:**

- `from mandala.flows.approval import Decision` — **Day 33's model, imported across framework
  namespaces.** `flows/` is CrewAI's directory and `graph/` is LangGraph's, and the shared thing is a
  Pydantic model with a validator. **That import is the plan's thesis in one line**: schemas and
  policies are portable; framework code is not. Note it for Day 89.
- `proposal_fingerprint(draft)` — **this closes an open item.** Day 33's §6 trap said *"letting a
  stale decision authorise a new draft… bind the decision to the request_id and to a hash of the
  proposed text if you can — and if you do not do it today, write it down for Day 82."* Today you
  can, cheaply, because the payload and the answer are one round trip. **Closing a deferred item
  seventeen days later, on the day it becomes easy, is the habit worth noticing.**
- `hashlib.sha256(...)[:16]` — 16 hex characters is 64 bits, ample for detecting an accidentally
  changed draft. This is a **change-detection** hash, not a security hash against an adversary who
  controls both sides; say that rather than implying more.
- Everything above `interrupt()` is: a `.get`, a string, and a hash. **Cheap and pure**, per §3.1's
  re-entry warning. No model call, no file write, no notification.
- `answer if isinstance(answer, Decision) else Decision(**answer)` — the resume value may arrive as a
  model or as a dict, depending on how the caller sends it. **Validate at the boundary either way**:
  going through `Decision(**answer)` means Day 33's validator (reason required on reject/edit,
  reviewer non-empty) runs on data that came from outside the process. A resume value is untrusted
  input and deserves the same treatment as a ticket body.
- The fingerprint mismatch branch returns `escalated` **rather than raising.** A human approved
  something; the something changed; that is a situation for a person, not a crash.
- `decision.authorises_send()` — **Day 33's single authorisation function, still the only place that
  answers "may this go out".** Its grep test (`test_authorises_send_is_the_only_gate`) now spans two
  frameworks, which is the strongest form that test has taken.

### 3.3 `days/day-50/lab/pause_resume.py`

```python
"""Pause a graph, kill the process, and resume it from another one.

Run:
    uv run python days/day-50/lab/pause_resume.py T-9002 a1 start
    # ... process exits, nothing is running ...
    uv run python days/day-50/lab/pause_resume.py T-9002 a1 approve

Budget: ~8 for the start run, 0 for the resume. Zero. That is the point.
"""

import sys

from langgraph.types import Command

from mandala.flows.approval import Decision
from mandala.graph.nodes import build_graph
from mandala.graph.persistence import checkpointer, thread_id
from mandala.sdk_tools import RAW_TICKETS

ticket, attempt, mode = sys.argv[1], sys.argv[2], sys.argv[3]
config = {"configurable": {"thread_id": thread_id(ticket, attempt)}}

with checkpointer() as saver:
    graph = build_graph().compile(checkpointer=saver)

    if mode == "start":
        result = graph.invoke(
            {
                "ticket_id": ticket,
                "request_id": f"req-{ticket}",
                "ticket_body": RAW_TICKETS[ticket]["body"],
                "stage": "new",
            },
            config=config,
        )
        pending = result.get("__interrupt__")
        print(f"PAUSED. the human is being asked:\n  {pending}")
        print(f"\nnothing is running now. resume with:\n"
              f"  uv run python days/day-50/lab/pause_resume.py {ticket} {attempt} approve")
    else:
        snapshot = graph.get_state(config)
        print(f"resuming; next = {snapshot.next}")
        payload = snapshot.tasks[0].interrupts[0].value
        decision = Decision(outcome="approve", reviewer="me")

        final = graph.invoke(
            Command(resume={**decision.model_dump(mode="json"),
                            "fingerprint": payload["fingerprint"]}),
            config=config,
        )
        print(f"stage  {final.get('stage')}")
        print(f"notes  {final.get('notes')}")
        print(f"draft  {(final.get('draft') or '')[:100]}")
```

**Line by line:**

- **Two separate process invocations.** That is the demonstration, and it is what Day 21's SDK
  approvals could not do at all. Say it out loud while recording: *between these two commands, nothing
  is running.*
- `result.get("__interrupt__")` — the paused payload surfaces on the returned state. **Confirm the key
  name in 1.2.11** (§8); it has been `__interrupt__` and has also been reachable only via
  `get_state()`.
- `snapshot.tasks[0].interrupts[0].value` — reading the pending interrupt from a **new process**. This
  is the resumption path proper: the second process learns what was asked entirely from the
  checkpoint. Verify these attribute names (§8) — this is the most version-sensitive line in the file.
- `Command(resume={...})` — the resume value. Note it is a **dict**, serialised from the `Decision`,
  because it has to survive being passed through the runtime. `model_dump(mode="json")` handles the
  `datetime` field.
- The fingerprint is echoed back from the payload, which is what makes §3.2's staleness check
  meaningful. **Try tampering with it by hand** — change one character and re-run — and watch the
  graph escalate instead of approving. That five-second experiment is the best proof the check works.
- `snapshot.next` printed before resuming — Day 47's inspectability, now doing something genuinely
  useful: you can see the graph is parked on `await_approval` before you answer.
- **Resume costs zero model requests** because the approval node makes no model call and the nodes
  before it are already checkpointed. Compare Day 33's CrewAI resume (0–2) and Day 21's SDK approval
  (a held process, so the question does not even apply).

---

## §4 AG-20 — `days/day-50/lab/hitl_compare.md`

The four-way comparison, and it is the last of the plan's repeated builds to complete.

```markdown
# Human-in-the-loop, four ways — Mandala, 2026-08-__

| | SDK approvals (D21) | CrewAI (D33) | LC middleware (D39) | LangGraph (D50) |
|---|---|---|---|---|
| Lines I wrote | | ~120 | ~3 | |
| Pause survives process death | no | yes | with a checkpointer | **yes** |
| Reviewer in a separate process | no | yes | | **yes** |
| Cost to resume (requests) | n/a | 0–2 | | **0** |
| Does the node re-run on resume? | n/a | no | | **yes — above the interrupt** |
| Records WHO decided | no | **yes** | no | **yes (ours)** |
| Records WHY | no | **yes** | no | **yes (ours)** |
| Binds the decision to the draft | no | no (deferred) | no | **yes — fingerprint** |
| Can inspect the pause before answering | no | no | | **yes — get_state().next** |

## What the framework gave me, and what it did not
<mechanism vs. record -- one paragraph, and be precise>

## The re-entry constraint
<what "everything above interrupt() runs twice" forbids, and how it rhymes with
 yesterday's idempotence rule>

## What Day 33 was worth
<Principle 2: was hand-building it first actually useful? Answer honestly -- and note
 that the Decision model I wrote then is the part that survived>

## Which I would ship
<and under what constraints -- including "no checkpointer available">
```

**The "what Day 33 was worth" section deserves a real answer rather than a polite one.** Principle 2
says build naked before framework. Seventeen days ago you wrote 120 lines to do what one line does
today. Was that waste?

The evidence says no, and specifically: **the 120 lines you wrote are not the 120 lines the framework
replaced.** The framework replaced the *pausing* — the raise, the file, the poll, the idempotent
re-entry. The `Decision` model, the three outcomes, the reason validator, the single authorisation
function: **all of that survived unchanged and is imported by today's file.** You built the durable
half by hand and the framework took it over; you built the accountable half by hand and it is still
yours, because no framework was ever going to supply it.

**That is the most concrete demonstration of Principle 2 in the whole plan.** Write it in the ADR and
again on Day 89.

---

## §5 The eval that must be able to fail

### `tests/test_graph_approval.py`

```python
"""Approval is accountability, not control flow. 0 model requests."""

from pathlib import Path

import pytest

from mandala.flows.approval import Decision
from mandala.graph.approval import await_approval_node, proposal_fingerprint


class FakeInterrupt(Exception):
    pass


def run_node(state, answer, monkeypatch) -> dict:
    """Drive the node with a canned resume value, without a graph or a runtime."""
    import mandala.graph.approval as approval

    monkeypatch.setattr(approval, "interrupt", lambda payload: answer)
    return approval.await_approval_node(state)


def approved(**over) -> dict:
    base = Decision(outcome="approve", reviewer="me").model_dump(mode="json")
    return {**base, **over}


def test_an_approval_lets_the_draft_through(monkeypatch):
    state = {"ticket_id": "T-1", "draft": "the reply"}
    out = run_node(state, approved(fingerprint=proposal_fingerprint("the reply")), monkeypatch)
    assert out["stage"] == "approved"
    assert out["draft"] == "the reply"


def test_a_rejection_escalates(monkeypatch):
    state = {"ticket_id": "T-1", "draft": "the reply"}
    rejected = Decision(outcome="reject", reviewer="me",
                        reason="names another customer").model_dump(mode="json")
    out = run_node(state, {**rejected, "fingerprint": proposal_fingerprint("the reply")},
                   monkeypatch)
    assert out["stage"] == "escalated"


def test_an_edit_sends_the_edited_text(monkeypatch):
    state = {"ticket_id": "T-1", "draft": "the original"}
    edited = Decision(outcome="edit", reviewer="me", reason="tone",
                      edited_text="the corrected reply").model_dump(mode="json")
    out = run_node(state, {**edited, "fingerprint": proposal_fingerprint("the original")},
                   monkeypatch)
    assert out["draft"] == "the corrected reply"


def test_a_stale_decision_does_not_authorise_a_changed_draft(monkeypatch):
    """THE test, and it closes Day 33's deferred trap. Flip it: drop the check, see red."""
    state = {"ticket_id": "T-1", "draft": "the NEW draft"}
    out = run_node(state, approved(fingerprint=proposal_fingerprint("the OLD draft")), monkeypatch)
    assert out["stage"] == "escalated"
    assert "different draft" in out["notes"][0]


def test_an_anonymous_resume_value_is_refused(monkeypatch):
    """A resume value is untrusted input. Day 33's validator must still run."""
    with pytest.raises(Exception):
        run_node({"ticket_id": "T-1", "draft": "d"},
                 {"outcome": "approve", "reviewer": ""}, monkeypatch)


def test_a_reject_without_a_reason_is_refused(monkeypatch):
    with pytest.raises(Exception):
        run_node({"ticket_id": "T-1", "draft": "d"},
                 {"outcome": "reject", "reviewer": "me"}, monkeypatch)


def test_the_decision_is_recorded_in_the_notes(monkeypatch):
    state = {"ticket_id": "T-1", "draft": "d"}
    out = run_node(state, approved(fingerprint=proposal_fingerprint("d")), monkeypatch)
    assert "decision:approve:me" in out["notes"][0]


def test_nothing_expensive_happens_above_the_interrupt():
    """§3.1: the node re-runs above interrupt(). Flip it: add a model call, see red."""
    source = Path("src/mandala/graph/approval.py").read_text(encoding="utf-8")
    head = source.split("interrupt(")[0]
    for banned in ("fast_loop", "workhorse", "judge", "invoke(", "open(", "write_text"):
        assert banned not in head, f"{banned} appears above interrupt() and will run twice"


def test_the_decision_model_is_day_33s():
    """Framework code is not portable; the record is. Flip it: define a second Decision."""
    assert Decision.__module__ == "mandala.flows.approval"


def test_authorises_send_is_still_the_only_gate():
    offenders = [
        p.relative_to("src").as_posix()
        for p in Path("src/mandala").rglob("*.py")
        if 'outcome == "approve"' in p.read_text(encoding="utf-8")
        and p.name != "approval.py"
    ]
    assert offenders == [], offenders
```

**Line by line:**

- `run_node()` **monkeypatches `interrupt` itself** to return the canned answer. That is the whole
  testing trick for interrupts, and it is worth internalising: **an interrupt is a function that
  returns a value on resume, so a fake that just returns the value tests the entire node.** No graph,
  no checkpointer, no runtime, no keys, instant.
- `test_a_stale_decision_does_not_authorise_a_changed_draft` is today's headline test and it closes an
  item that has been open since Day 33. **Note in the checklist that a deferred trap was closed** —
  that is the sort of thing that quietly never happens without a ledger.
- `test_an_anonymous_resume_value_is_refused` and its sibling assert that **Day 33's validator runs on
  resume input.** This is the "a resume value is untrusted input" claim, made real.
- `test_nothing_expensive_happens_above_the_interrupt` is a **grep test on the top half of a file**,
  which is unusual and effective. It splits the source at `interrupt(` and scans only what precedes
  it. Crude, cheap, and it directly enforces §3.1's constraint — which is otherwise the kind of thing
  that is true when written and false three commits later.
- `test_the_decision_model_is_day_33s` asserts the module path, so **defining a second `Decision` for
  LangGraph fails.** Same shape as Day 38's `test_the_schema_is_still_day_4s`, and for the same
  reason: two records means no accountability.
- `test_authorises_send_is_still_the_only_gate` — Day 33's grep test, now spanning two framework
  directories. It gets stronger every time a framework is added, which is a nice property for a
  four-line test.

---

## §6 Traps

- **An `interrupt()` with no checkpointer.** The pause is not durable and you have reinvented Day 21.
- **Expensive work above `interrupt()`.** It runs twice. This is the trap of the day.
- **Side effects above `interrupt()`.** Two notification emails.
- **Trusting the resume value.** It came from outside the process. Validate it through `Decision`.
- **Skipping the fingerprint.** A human approved draft A; the graph sends draft B; nothing errors.
- **Writing a second `Decision` model** because "the graph one needs different fields". Two records,
  no accountability.
- **Raising on a fingerprint mismatch.** Escalate — a person needs to look, and a crash loses the
  state.
- **`{"thread_id": ...}` outside `configurable`.** Third time this trap has appeared; it silently
  starts a fresh thread and the resume finds nothing.
- **Resuming with `invoke(None)` instead of `Command(resume=...)`.** `None` continues *without*
  supplying the interrupt's value, which is a different operation.
- **Concluding Day 33 was wasted.** The half that survived is the half no framework supplies.

---

## §7 Request budget

**Declared: ~8 model requests, Groq.**

| What | Requests |
|---|---|
| `tests/test_graph_approval.py` | **0** |
| `pause_resume.py ... start` | ≤ 8 |
| `pause_resume.py ... approve` | **0** |
| The tampered-fingerprint experiment | **0** |

**The resume costs nothing, and that is worth stating plainly in the bake-off**: across four HITL
implementations, the cost of a human decision ranges from "a held process" to zero. On a $0 project
the gate you can afford to put everywhere is the one that costs nothing to wait on.

---

## §8 Verify before you code

Written **2026-08-20** against `langgraph==1.2.11`:

- **`interrupt` import path** — `langgraph.types` is the assumption.
- **Does the node really re-run from the top on resume?** §3.1 is the whole design constraint. Prove
  it: put a `print` at the top of the node and count how many times it appears across both processes.
- **How is a pending interrupt surfaced?** `result["__interrupt__"]`, or only via
  `get_state().tasks[...].interrupts[...]`? §3.3 uses both; confirm which is current.
- **The `Interrupt` object's attributes** — `.value` is assumed. This is the most version-sensitive
  line in the lab.
- **`Command(resume=...)` with multiple pending interrupts** — if two nodes interrupt in one
  super-step, how are the resume values matched to them? Not needed today; you will want it on Day 82.
- **Is `interrupt()` allowed inside a subgraph** (Day 48), and does the parent see it? Day 83's
  assembly depends on the answer.
- **Does a `Send` branch support `interrupt()`?** Approving one of five parallel research branches is
  a real future case.
- `https://docs.langchain.com/oss/python/langgraph/human-in-the-loop` — read today.

---

## §9 Say it in an interview

> "LangGraph makes a human pause a runtime primitive: `interrupt()` stores a payload in the
> checkpoint, the process exits, and `Command(resume=…)` continues from exactly there — so the resume
> costs zero model requests and nothing is held open while a person thinks. The constraint people
> miss is that the node re-runs from the top on resume, so everything above the interrupt executes
> twice; I keep that node to a `get`, a string, and a hash, and there's a grep test that scans the top
> half of the file and fails if a model call or a file write appears there. The design decision I'd
> defend is splitting mechanism from record: the framework gives me durable control flow, and it
> gives me nothing about who approved, why, or what exactly they approved — so I import the decision
> model I'd written by hand in a different framework two weeks earlier, unchanged, across the
> namespace boundary. I also used the round trip to close something I'd deferred: the payload carries
> a fingerprint of the draft and the resume echoes it back, so a decision made against an older draft
> escalates instead of silently authorising a different reply. And that's the honest answer to whether
> hand-building it first was worth it — the framework replaced the pausing, and the accountability
> half is the part that survived, because no framework was ever going to supply it."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 50
```
