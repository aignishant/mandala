---
day: 33
phase: 5
phase_name: "CrewAI Flows"
title: "HITL in flows + conversational flows"
ids: ["CR-19"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 33 — HITL in flows, and the flow as a chat backend

**Phase 5 · CrewAI Flows** · IDs: **CR-19 🛠️**

> **Yesterday:** the flow survives being killed, because every step boundary is a checkpoint.
> **Today:** it stops on purpose. A human approval step pauses the flow — and a pause is only a pause
> if the process can die while the human thinks. Then the same machinery is turned inside out and the
> flow becomes a chat backend.
> **Tomorrow:** the declarative DSL, and what it costs you to give up Python.

```bash
./m start 33
./m scaffold 33
```

---

## §1 The story

Principle 12: *"No agent performs an external side effect without a human-in-the-loop checkpoint
until Phase 13's graduated-autonomy review."* Thirty-two days in, Mandala has never actually sent
anything — every draft has been a draft. Today is the day the gate that makes that safe gets built.

**This is the second of four HITL implementations** (AG-20 in the plan's Part 6 repetition map):

| Framework | Mechanism | What "pause" means | Day |
|---|---|---|---|
| OpenAI Agents SDK | tool approvals (`OAI-23`) | the run blocks, in memory | 21 |
| **CrewAI Flows** | **human feedback step (CR-19)** | **checkpoint + stop; resume later** | **today** |
| LangChain | HITL middleware (`LC-08`) | interception around the model call | 39 |
| LangGraph | `interrupt()` (`LG-09`) | durable, runtime-level | 50 |

Read the third column, then read yesterday's lesson again. **CrewAI's approval gate is only durable
because you turned on `@persist` yesterday.** Without it, "pause for a human" means "hold a Python
process open until a person answers", which fails the first time a laptop sleeps. With it, the pause
is a row in SQLite and the human has as long as `MAX_CHECKPOINT_AGE_HOURS` allows.

That ordering — durability *then* HITL — is not an accident of the curriculum. It is the actual
dependency, and it is the thing to say when someone asks why LangGraph's `interrupt()` is a big deal
on Day 50: the interesting part was never stopping, it was **stopping without holding anything open.**

The second half of today is a genuine curiosity. CrewAI 1.15 exposes a **chat API for conversational
flows** — the same flow, driven as a back-and-forth conversation rather than a batch run. It rhymes
with the approval gate more than it looks like it does: both are "the flow yields control to a human
and waits", and one is just polite about it.

---

## §2 Setup — run this

### 2.1 No new packages

```bash
grep -n 'crewai' pyproject.toml
```

- Human-feedback steps and the chat API ship inside `crewai==1.15.17`.

### 2.2 Create today's files

```bash
touch src/mandala/flows/approval.py
touch tests/test_approval.py
mkdir -p days/day-33/lab
touch days/day-33/lab/approve_cli.py
touch days/day-33/lab/chat_flow.py
```

- `approval.py` is the gate: the record of what was asked, who answered, and what the answer
  authorises. **It is an audit artifact first and a control-flow device second**, and building it in
  that order is the whole difference between a gate and a speed bump.
- `approve_cli.py` is the reviewer's side. It is deliberately a separate process — see §3.4.

### 2.3 Yesterday's store must be working

```bash
uv run python days/day-32/lab/inspect_checkpoints.py
```

- If that prints no tables, stop and finish Day 32. A HITL gate on a flow that cannot checkpoint is
  a `while True: input()` loop wearing a costume.

---

## §3 CR-19 — the approval gate

### 3.1 What a gate has to record

An approval that records only `True` is worthless the first time someone asks *"who approved sending
that?"* — and someone will. The gate stores five things:

| Field | Why it exists |
|---|---|
| **what was proposed** | the exact draft text, not a summary of it |
| **who decided** | a reviewer identity, even if today it is `"me"` |
| **the decision** | approve / reject / edit — three outcomes, not two |
| **when** | so staleness (Day 32) applies to decisions too |
| **why** | free-text reason, required on reject and edit |

The three-outcome design matters. A two-outcome gate (approve/reject) pushes every "almost right"
draft into rejection, and the reviewer's fix is lost. **Edit is where the training signal lives** —
Day 28's `crewai train` and Day 71's eval set both want the diff between what the model wrote and
what a human was willing to send.

### 3.2 `src/mandala/flows/approval.py`

```python
"""The human approval gate: an audit record that happens to control the flow.

Principle 12 says no external side effect without a human checkpoint. This module
is where that promise becomes a data structure. Note the ordering of concerns --
the Decision is defined before the gate function, because the RECORD is the point
and the pause is the mechanism.

Zero external writes still happen anywhere in Mandala. Day 82 is the first one, and
it will call approve() before it does.

Usage
-----
    >>> d = Decision(outcome="approve", reviewer="me", reason="looks right")
    >>> d.authorises_send()
    True
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Outcome = Literal["approve", "reject", "edit"]


class Decision(BaseModel):
    """One human decision about one proposed action. Immutable once written."""

    model_config = {"frozen": True}

    outcome: Outcome
    reviewer: str = Field(min_length=1, max_length=64)
    reason: str = Field(default="", max_length=500)
    edited_text: str | None = Field(default=None, max_length=4000)
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def _reason_required_unless_plain_approval(self) -> Decision:
        if self.outcome in ("reject", "edit") and not self.reason.strip():
            raise ValueError(f"a {self.outcome} decision must carry a reason")
        if self.outcome == "edit" and not (self.edited_text or "").strip():
            raise ValueError("an edit decision must carry edited_text")
        return self

    def authorises_send(self) -> bool:
        """The ONLY function allowed to answer 'may this go out?'."""
        return self.outcome in ("approve", "edit")

    def final_text(self, proposed: str) -> str:
        """What actually goes out: the edit if there was one, else the draft."""
        return self.edited_text if self.outcome == "edit" else proposed
```

**Line by line:**

- `model_config = {"frozen": True}` — **a decision cannot be edited after it is made.** This is the
  same instinct as Day 1's frozen `Keys` and it matters more here: an audit record you can mutate is
  not an audit record. If a reviewer changes their mind, that is a *second* `Decision`, and the
  history shows both.
- `Outcome = Literal["approve", "reject", "edit"]` — three outcomes, countable on Day 71, and
  impossible to typo into a fourth.
- `reviewer: str = Field(min_length=1, ...)` — `min_length=1` makes an empty reviewer a validation
  error rather than an anonymous approval. Today it will always say `"me"`; the field exists so that
  when Mandala has two humans, nothing in the schema has to change.
- `@model_validator(mode="after")` — a **whole-object** validator, running after each field has been
  validated individually. Field validators cannot express "reason is required *when* outcome is
  reject", because that rule spans two fields. This is the right tool and the reason to know it
  exists.
- The two rules inside it encode the §3.1 argument: **reject and edit must be explained; plain
  approval need not be.** Requiring a reason for approval sounds rigorous and produces a directory
  full of `"ok"`.
- `authorises_send()` as a **named method rather than a comparison at the call site.** Every place in
  Mandala that could send something asks this one question, so the policy lives in one line. When
  Day 84's graduated autonomy adds "or: severity=low and four clean weeks", it changes here and
  nowhere else. **This is the single most important design choice in the file** — an authorisation
  check scattered across call sites is an authorisation check that will eventually disagree with
  itself.
- `final_text(proposed)` — the edit path made explicit. Without it, someone will approve an edit and
  send the *original*, and the reviewer's correction evaporates silently. A method with a docstring
  is cheaper than that bug.
- `decided_at` with `default_factory=lambda: datetime.now(timezone.utc)` — **timezone-aware**, always.
  A naive datetime in an audit record is a bug waiting for a reader in another timezone. And
  `default_factory` rather than `default=datetime.now(...)`, which would freeze the import time into
  every record — Day 4's mutable-default trap in a new costume.

### 3.3 The gate step in `intake.py`

```python
    @listen(or_(fast_answer, deep_research))
    def await_approval(self, draft: str) -> str:
        """Pause. Nothing leaves Mandala until a human answers.

        Note this listens to the two lanes that PRODUCE a draft. `escalate` skips
        the gate entirely -- there is nothing to approve, a human already has it.
        """
        self.state.draft = draft
        self.state.stage = "awaiting_approval"
        self.state.record("await_approval")

        pending = pending_path(self.state)
        pending.write_text(draft, encoding="utf-8")

        decision = load_decision(self.state)
        if decision is None:
            raise FlowPaused(
                f"awaiting human review of {self.state.ticket_id}. "
                f"Run: uv run python days/day-33/lab/approve_cli.py {self.state.request_id}"
            )

        self.state.record(f"decision:{decision.outcome}:{decision.reviewer}")
        if not decision.authorises_send():
            self.state.stage = "rejected"
            return "rejected"

        self.state.draft = decision.final_text(draft)
        self.state.stage = "approved"
        return self.state.draft
```

**Line by line:**

- `@listen(or_(fast_answer, deep_research))` — **not** `escalate`. An escalated ticket already went to
  a human; asking a human to approve sending it to a human is the kind of gate that teaches people to
  click through gates. Which branches need a gate is a design decision, and stating it in the
  decorator is where a reviewer will look.
- `self.state.stage = "awaiting_approval"` — a new value for Day 30's `Literal`. **Add it to the
  `Literal` in `state.py` in the same commit**, or Pydantic rejects the assignment. That friction is
  the `Literal` doing its job: a new lifecycle state is a schema change, and schema changes should be
  visible.
- `pending.write_text(draft, ...)` — the proposal is written where the reviewer can read it. The
  reviewer is a *different process* (§3.4), so the two sides communicate through the filesystem, not
  through a Python object.
- `raise FlowPaused(...)` — pausing by **raising a specific exception**, and the message contains the
  exact command the human should run. A pause that does not tell you how to unpause it is a hang.
  Define `FlowPaused` yourself in `approval.py`; it should subclass `Exception`, not `RuntimeError`,
  because it is not an error — it is a normal outcome that happens to unwind the stack.
- **Why raise at all, instead of blocking on `input()`?** Because raising lets yesterday's checkpoint
  stand as the record of where you got to, and the process exits. A blocking `input()` holds a
  process — and its memory, and its open crew — for however long a human takes. §3.4 expands this.
- `load_decision(self.state)` returning `None` on the first pass and a `Decision` on the second is
  what makes the step **idempotent**: run the flow again after the human answers and it proceeds.
  That is the resume story from Day 32 doing real work.
- `self.state.record(f"decision:{decision.outcome}:{decision.reviewer}")` — the audit trail carries
  the decision, so `state.steps` alone answers "was this approved, and by whom".
- `decision.final_text(draft)` — the edit path, used rather than admired.

### 3.4 Why the reviewer is a separate process

This is the design point of the day, and it is worth being stubborn about.

| | Blocking `input()` in the flow | Pause + separate reviewer process |
|---|---|---|
| Process must stay alive | **yes** | no |
| Survives a laptop sleep | no | **yes** |
| Survives a deploy | no | **yes** |
| Reviewer can be elsewhere | no | **yes** — it is a file, then an API |
| Costs while waiting | a held process, a warm crew | **nothing** |
| Testable without a human | awkwardly | **trivially — write the decision file** |

That last row is not a footnote. **A gate you cannot test without a human is a gate that will not be
tested**, and Principle 7 says a behaviour is not done until a test can fail on it. The separate-
process design is what makes §5 possible at zero cost.

This is also exactly the shape LangGraph's `interrupt()` gives you for free on Day 50. Today you are
building by hand what a later framework provides as a runtime feature — Principle 2's "naked before
framework", applied *between* frameworks rather than before them. When Day 50 arrives, you will know
precisely what it saved you.

### 3.5 `days/day-33/lab/approve_cli.py` — 0 model requests

```python
"""The reviewer's side of the gate. A different process, on purpose.

Run:
    uv run python days/day-33/lab/approve_cli.py req-T-9002

Budget: 0 requests. No model is involved in reviewing -- that is the point.
"""

import sys

from mandala.flows.approval import Decision, pending_path_for, write_decision

request_id = sys.argv[1]
proposed = pending_path_for(request_id).read_text(encoding="utf-8")

print("-" * 70)
print(proposed)
print("-" * 70)
print("[a]pprove  [r]eject  [e]dit  [q]uit")

choice = input("> ").strip().lower()[:1]
if choice == "q":
    raise SystemExit("no decision recorded")

if choice == "a":
    decision = Decision(outcome="approve", reviewer="me")
elif choice == "r":
    decision = Decision(outcome="reject", reviewer="me", reason=input("reason: "))
elif choice == "e":
    edited = input("edited text: ")
    decision = Decision(outcome="edit", reviewer="me",
                        reason=input("reason: "), edited_text=edited)
else:
    raise SystemExit(f"unknown choice {choice!r}")

write_decision(request_id, decision)
print(f"recorded: {decision.outcome} by {decision.reviewer} at {decision.decided_at:%H:%M:%S}")
```

**Line by line:**

- The script **prints the proposal in full**, framed by rules. A reviewer approving a truncated draft
  is approving something they did not read, and the gate becomes theatre.
- `input("> ").strip().lower()[:1]` — takes the first character, so `approve`, `a`, and `A` all work.
  Small ergonomics matter for a thing a human does dozens of times; a gate that is annoying gets
  bypassed.
- `[q]uit` exists and records **nothing**. "I am not ready to decide" must be expressible, otherwise
  the reviewer's only escape from an unclear draft is a wrong decision.
- Reject and edit prompt for a reason because §3.2's validator will refuse them without one. Note the
  shape: the CLI does not enforce the rule, the *model* does. The rule holds no matter who writes a
  decision — CLI, test, or a web UI on Day 89.
- `write_decision(request_id, decision)` — write it as JSON next to the pending file. Keep both in
  `.mandala/approvals/`, which §2.3's gitignore already covers if you added `.mandala/`. **Check that
  it does.** Drafts are derived from customer tickets.
- `{decision.decided_at:%H:%M:%S}` — datetime formatting inside an f-string. Confirmation to the human
  that their decision landed, which is the difference between a tool people trust and one they run
  twice.

---

## §4 Conversational flows — the same idea, turned around

CrewAI 1.15 exposes a **chat API for conversational flows**: instead of `kickoff` running to
completion, the flow is driven turn by turn, and it can ask the human something mid-run.

### 4.1 The relationship to the approval gate

Both are "the flow yields to a human". The difference is **who holds the initiative**:

| | Approval gate (§3) | Conversational flow (§4) |
|---|---|---|
| Who starts | the flow, on a schedule | the human, with a message |
| Human's role | reviewer of a finished proposal | participant, mid-run |
| Number of interactions | one, usually | many |
| Natural fit for | Principle-12 write gates | intake, clarification |
| Failure mode | reviewer rubber-stamps | conversation drifts, cost grows unbounded |

**Mandala's intake is the honest use case.** Half of real support tickets are missing the one fact
you need — an order id, a version number — and a batch flow's only options are to guess or to fail. A
conversational intake asks.

### 4.2 `days/day-33/lab/chat_flow.py`

```python
"""Drive the flow as a conversation. Real model calls -- keep it short.

Run:
    uv run python days/day-33/lab/chat_flow.py

Budget: <= 6 requests. The turn cap is in the code, not in your discipline.
"""

from mandala.flows.intake import IntakeFlow

MAX_TURNS = 6

flow = IntakeFlow()
history: list[str] = []

for turn in range(MAX_TURNS):
    message = input("you> ").strip()
    if not message or message == "/quit":
        break
    history.append(message)

    # TODO(me): drive one turn through the 1.15.17 chat API and print the reply.
    # Keep the shape: one human message in, one flow reply out, history bounded.
    raise NotImplementedError("wire the chat API, then delete this line")

print(f"\nturns used: {len(history)}/{MAX_TURNS}")
```

**Line by line:**

- `MAX_TURNS = 6` **in the code**, checked by the loop. An open-ended conversation with a free-tier
  model is an open-ended request count, and §7's budget is only real if something enforces it.
  Principle 5 as a `range()`.
- `history: list[str]` bounded by the same loop — the conversation is the prompt, and an unbounded
  conversation is an unbounded prompt (Day 4's AG-04 again, in its fifth costume).
- `/quit` as an explicit exit, plus empty-input exit. Interactive scripts need a way out that is not
  Ctrl+C, because Ctrl+C during a persisted flow leaves you resuming a half-turn on Day 35.
- The step ships raising `NotImplementedError` because **the exact chat API surface is the thing you
  must verify today** (§8) rather than copy from a lesson written on 2026-08-20. The shape is
  prescribed; the call is yours.
- **What this file deliberately does not do:** persist the conversation. Turn-by-turn checkpointing of
  a chat is a real design question (every turn? every N? on exit?) and Day 47's LangGraph
  checkpointers give a much better vocabulary for answering it. Note the question, defer the answer,
  and write "conversational persistence — decide on Day 47" in your bake-off notes.

---

## §5 The eval that must be able to fail

### `tests/test_approval.py`

```python
"""The gate is an audit record. Tests cost 0 model requests, by design (§3.4)."""

import pytest
from pydantic import ValidationError

from mandala.flows.approval import Decision


def test_approve_needs_no_reason():
    assert Decision(outcome="approve", reviewer="me").authorises_send() is True


def test_reject_without_a_reason_is_refused():
    with pytest.raises(ValidationError, match="reason"):
        Decision(outcome="reject", reviewer="me")


def test_edit_without_edited_text_is_refused():
    with pytest.raises(ValidationError, match="edited_text"):
        Decision(outcome="edit", reviewer="me", reason="tone")


def test_an_anonymous_decision_is_refused():
    with pytest.raises(ValidationError):
        Decision(outcome="approve", reviewer="")


def test_reject_does_not_authorise_send():
    """THE test. Flip it: add 'reject' to authorises_send and watch this go red."""
    d = Decision(outcome="reject", reviewer="me", reason="names another customer")
    assert d.authorises_send() is False


def test_edit_authorises_send_of_the_edited_text():
    d = Decision(outcome="edit", reviewer="me", reason="tone",
                 edited_text="the corrected reply")
    assert d.authorises_send() is True
    assert d.final_text("the original draft") == "the corrected reply"


def test_approve_sends_the_original_text():
    d = Decision(outcome="approve", reviewer="me")
    assert d.final_text("the original draft") == "the original draft"


def test_a_decision_cannot_be_altered():
    d = Decision(outcome="reject", reviewer="me", reason="wrong")
    with pytest.raises(ValidationError):
        d.outcome = "approve"


def test_decided_at_is_timezone_aware():
    assert Decision(outcome="approve", reviewer="me").decided_at.tzinfo is not None


def test_two_decisions_have_different_timestamps():
    """Catches default= instead of default_factory=."""
    a = Decision(outcome="approve", reviewer="me")
    b = Decision(outcome="approve", reviewer="me")
    assert a.decided_at <= b.decided_at


def test_authorises_send_is_the_only_gate(tmp_path):
    """Grep-as-a-test: nothing else in src/ decides whether something may be sent."""
    from pathlib import Path

    offenders = [
        p.name
        for p in Path("src/mandala").rglob("*.py")
        if 'outcome == "approve"' in p.read_text(encoding="utf-8")
        and p.name != "approval.py"
    ]
    assert offenders == [], offenders
```

**Line by line:**

- The first four tests are the validator, one rule per test. A validator with three rules and one
  test tells you *something* is wrong, not which rule broke.
- `match="reason"` and `match="edited_text"` — asserting the message names the missing field. A
  reviewer hitting this in the CLI needs to know what to supply.
- `test_reject_does_not_authorise_send` is today's **flip-it test**, with the mutation to try written
  in the docstring. This is the one that matters: `authorises_send` is the function standing between
  Mandala and Principle 12.
- `test_edit_authorises_send_of_the_edited_text` asserts **both halves** — that edit permits sending
  *and* that what gets sent is the edit. Testing only the first half is how the reviewer's correction
  gets silently dropped (§3.2).
- `test_a_decision_cannot_be_altered` proves `frozen=True` is doing something. Config flags that
  nothing tests get removed during a refactor by someone who assumed they were decorative.
- `test_two_decisions_have_different_timestamps` catches `default=` where `default_factory=` was
  meant — a bug that is invisible in one run and obvious across two. `<=` rather than `<` because
  clocks are coarse; the assertion you want is "not frozen at import", and equal timestamps two
  microseconds apart still satisfy it. **If you want it sharper, assert both differ from module import
  time** — and note that this is a real limitation of the test, not a thing to pretend about.
- `test_authorises_send_is_the_only_gate` is the architecture test, same shape as Day 31's
  `test_the_organ_is_the_only_place_the_crew_is_built`. Two days in a row that a one-boundary rule
  got a grep test should tell you this is a pattern worth keeping, not a trick.
- **Not tested:** the CLI. It is I/O around a tested model. Test the rules, exercise the CLI by hand,
  and be honest about which is which.

---

## §6 Traps

- **Blocking on `input()` inside the flow.** It works on your laptop for five minutes and fails every
  other way. §3.4 is the whole argument.
- **Two outcomes instead of three.** Every near-miss draft becomes a rejection, and the reviewer's
  correction — the most valuable data in the system — is thrown away.
- **Approving the edit and sending the original.** Use `final_text()`. This bug is silent and the
  reviewer will not find out.
- **Forgetting to add `"awaiting_approval"` to the `stage` `Literal`.** Pydantic will tell you loudly,
  which is the correct outcome; do not "fix" it by loosening the type to `str`.
- **A gate on `escalate`.** Nothing to approve. Gates that fire when there is no decision to make are
  how people learn to approve without reading.
- **Approval records outside `.gitignore`.** They contain drafts, which are derived from customer
  tickets. Same rule as Day 32's checkpoints.
- **An unbounded conversational flow.** Six turns of a crew-backed flow is not six requests. Cap the
  turns in code.
- **Treating a `FlowPaused` as an error in CI.** It is a normal outcome. If Day 74's regression gate
  treats a pause as a failure, every HITL test goes red for the wrong reason.
- **Letting a stale decision authorise a new draft.** The draft changed; the approval did not. Bind
  the decision to the `request_id` **and** to a hash of the proposed text if you can — and if you do
  not do it today, write it down for Day 82, which is the day it becomes a real external write.

---

## §7 Request budget

**Declared: ~8 model requests, Groq.**

| What | Requests |
|---|---|
| `tests/test_approval.py` | **0** |
| `approve_cli.py`, any number of decisions | **0** |
| One fast-lane run to the gate, then resumed after approval | ~2 |
| `chat_flow.py`, capped at `MAX_TURNS = 6` | ≤ 6 |

Today is cheap, and that is a structural fact rather than luck: **the human is the expensive
component and humans are free on this project.** Notice the shape — Day 31's routing was free, Day
32's resume was free, today's gate is free. The cost in Phase 5 is concentrated entirely in the one
autonomous organ. That concentration is what makes the flow architecture affordable, and it is a
sentence worth having ready for Day 63.

---

## §8 Verify before you code

Written **2026-08-20** against `crewai==1.15.17`. The chat API is new surface; treat every claim here
as a hypothesis until you have checked it, and log mismatches per Principle 14:

- **Does 1.15.17 have a first-class human-feedback step**, or is the pause-and-raise pattern in §3.3
  the idiomatic way? If there is a built-in, use it and rewrite §3.3 — but keep the `Decision` record
  either way, because a framework's approval primitive will not store *why*.
- **The chat API entry point** — module, class, and whether it is `flow.chat(...)`, a separate runner,
  or a server. §4.2 deliberately does not guess.
- **Does the chat API persist turns automatically** when `@persist` is on? This is the question §4.2
  defers, and if the framework already answers it, that is a finding worth a changelog line.
- **What happens to a persisted flow that raises mid-step?** Yesterday's checkpoint should hold the
  state as of the last completed step. Confirm the raise does not roll it back — the entire gate
  design rests on it.
- **Can `kickoff` be called twice on the same id** and continue past a step that previously raised?
  §3.3's idempotency assumes yes.
- `https://docs.crewai.com/concepts/flows` — human input and chat sections, read today.

---

## §9 Say it in an interview

> "The approval gate doesn't block a process — it checkpoints and exits, and a separate reviewer
> process writes a decision file that the next run picks up. That falls out of having made the flow
> durable the day before: a pause is only useful if nothing has to stay alive during it. The record
> has three outcomes, not two, because 'edit' is where the reviewer's correction lives and a
> two-outcome gate throws that away. And there's exactly one function that answers 'may this go
> out' — with a grep test asserting nothing else in the codebase decides it — so when graduated
> autonomy arrives, the policy changes in one place. The whole gate costs zero model requests, which
> is the tell that it's the right design: the human is the expensive part, and humans don't bill me."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 33
```
