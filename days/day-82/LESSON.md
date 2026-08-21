---
day: 82
phase: 12
phase_name: "Capstone build"
title: "Capstone V — the durable approval gate and the first external write"
ids: []
kind: capstone
plan_version: "v1.1.0"
generated: "2026-08-21"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 82 — Capstone V: the durable approval gate and the first external write

**Phase 12 · Capstone build** · IDs: **—** (capstone assembly; realises AG-20's approval-gate design
from ADR-003 and LG-09's interrupts)

> **Yesterday:** a validated `Resolution` with a `content_hash`, and three tests that already decided
> which changes should invalidate an approval.
> **Today:** the most consequential day in the plan. **Mandala gets a write tool** — the first
> capability that can affect the world outside this repo — and a durable human approval gate in front
> of it that survives the process dying. Day 70's drift test will fire. That is the system working.
> **Tomorrow:** end-to-end assembly on twenty unseen tickets.

```bash
./m start 82
./m scaffold 82
```

---

## §1 The story

Eighty-one days of read-only. Today that ends, and the plan's Phase-12 gate says what must remain
true after it: **zero unapproved external writes in the trace log.**

Three things make that hard, and all three are ignored by the tutorial version of "human in the
loop":

1. **An approval must survive a restart.** `input("approve? y/n")` in a loop is not an approval
   system; it is a synchronous block that dies with the process and re-runs everything on restart.
   Day 50's `interrupt` plus Day 47's checkpointer is the real mechanism, and Day 79's kill-and-resume
   drill is why you can trust it today.
2. **An approval must bind to a specific artifact.** "The human said yes" is a confused-deputy
   machine: approve draft A, the state changes, the write sends draft B. The binding is yesterday's
   `content_hash`, and Day 68 already taught you this shape with per-target browser approvals.
3. **An approval must be a record, not a flag.** Who, when, what hash, on which run. A boolean tells
   you nothing at 3am and proves nothing to anyone. The Phase-12 gate is evidence-based; a boolean is
   not evidence.

And the mechanical consequence you were promised: adding a write tool changes `permissions.py`, which
changes the generated permission table, which fails `test_the_checked_in_table_is_not_stale` and
blocks CI until you regenerate. **Day 70 §4.2 predicted this exact moment.** When it fires, do not
groan — read the diff. It is the system making you look at a new write capability, which is precisely
the mechanism you built it for.

---

## §2 Setup — run this

No new dependencies.

```bash
touch src/mandala/organs/approval.py
touch src/mandala/organs/write.py
mkdir -p days/day-82/lab .state/approvals
touch days/day-82/lab/approve_cli.py
touch days/day-82/lab/kill_at_the_gate.md
touch tests/test_approval.py
touch tests/test_external_write.py
```

**Before you write any code, do this in order:**

```bash
uv run pytest tests/test_permission_table_is_current.py -q   # green now
# ... add the write tool to permissions.py ...
uv run pytest tests/test_permission_table_is_current.py -q   # RED — read the failure
uv run python scripts/gen_permission_table.py
git diff docs/PERMISSION_TABLE.md                            # <- look at this properly
```

**Read that diff before continuing.** A new row with `✍️ yes`, a blast-radius sentence you had to
write, and a changed trifecta table. If any agent now shows ❌ VIOLATION, stop everything — the
capstone has just re-armed the lethal trifecta and no approval gate fixes that.

---

## §3 The write tool, declared before it is built

```python
# src/mandala/permissions.py — the new row
TOOLS["post_reply"] = ToolSpec(
    name="post_reply",
    writes=True,
    reads_untrusted=False,
    blast_radius=(
        "HIGH — visible to a customer, cannot be unsent, and closes the ticket. "
        "One call per approved draft; no retries without a fresh approval."
    ),
)

AGENTS["resolver"] = AgentSpec(
    name="resolver",
    tools=frozenset({"post_reply"}),
    sees_untrusted_text=False,          # <- the load-bearing field
)
```

**Line by line:**

- **`sees_untrusted_text=False` on the Resolver is the entire separation argument.** The agent that
  can write does not read the ticket body or the search snippets; it receives an already-validated
  `Resolution` and an approval record. If you cannot honestly set this to `False`, your architecture
  has the trifecta and the fix is structural, not procedural.
- `blast_radius` in prose, per Principle 6, and Day 70's
  `test_every_write_tool_has_a_non_empty_blast_radius` enforces it mechanically. Note the second
  sentence — it states the retry policy, which matters more than people expect (see §5).
- `reads_untrusted=False` on the tool: `post_reply` returns a delivery receipt, not stranger-written
  text. If your real channel returned a customer's auto-reply, that would flip to `True` and the
  trifecta table would change. Think it through rather than copying.
- The write tool is a **local, free, fake channel**: it appends to `outbox/` and marks the ticket
  closed in a local file. Zero budget, and — more importantly — **you should not point a
  freshly-built agent at a real customer channel on day one anyway.** Say that in the notes; it is
  the honest reason, not the budget.

---

## §4 The durable gate

```python
# src/mandala/organs/approval.py
"""A durable approval. Record, not flag. Bound to a hash, not to a run.

The interrupt suspends the graph and the checkpointer persists it. The human can
approve tomorrow, from a different process, and the graph resumes exactly here.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
from dataclasses import asdict, dataclass

from langgraph.types import interrupt

from mandala.schemas_resolution import Resolution

APPROVALS = pathlib.Path(".state/approvals")


@dataclass(frozen=True)
class Approval:
    run_id: str
    draft_hash: str
    decided_by: str
    decided_at: str
    decision: str            # "approve" | "reject"
    reason: str = ""

    @property
    def granted(self) -> bool:
        return self.decision == "approve"


class ApprovalMismatch(RuntimeError):
    """The approval does not match the draft about to be written. Confused deputy, blocked."""


def record(a: Approval) -> None:
    APPROVALS.mkdir(parents=True, exist_ok=True)
    (APPROVALS / f"{a.run_id}.json").write_text(json.dumps(asdict(a), indent=2), encoding="utf-8")


def load(run_id: str) -> Approval | None:
    p = APPROVALS / f"{run_id}.json"
    return Approval(**json.loads(p.read_text(encoding="utf-8"))) if p.exists() else None


def check(approval: Approval | None, resolution: Resolution, run_id: str) -> Approval:
    if approval is None:
        raise ApprovalMismatch(f"no approval on file for {run_id}")
    if approval.run_id != run_id:
        raise ApprovalMismatch(f"approval belongs to {approval.run_id}, not {run_id}")
    if approval.draft_hash != resolution.content_hash:
        raise ApprovalMismatch(
            f"draft changed since approval ({approval.draft_hash} -> {resolution.content_hash})"
        )
    if not approval.granted:
        raise ApprovalMismatch(f"approval was a rejection: {approval.reason!r}")
    return approval


def approve_node(state) -> dict:
    resolution = Resolution(**state["draft"])
    existing = load(state["run_id"])
    if existing is not None:
        check(existing, resolution, state["run_id"])
        return {"approval": asdict(existing), "notes": ["approval already on file"]}

    decision = interrupt(
        {
            "run_id": state["run_id"],
            "ticket_id": state["ticket_id"],
            "draft_hash": resolution.content_hash,
            "body": resolution.body,
            "citations": resolution.citations,
            "confident": resolution.confident,
        }
    )
    a = Approval(
        run_id=state["run_id"],
        draft_hash=resolution.content_hash,
        decided_by=decision["by"],
        decided_at=dt.datetime.now(dt.UTC).isoformat(),
        decision=decision["decision"],
        reason=decision.get("reason", ""),
    )
    record(a)
    check(a, resolution, state["run_id"])
    return {"approval": asdict(a)}
```

**Line by line:**

- **`check()` is called even on the freshly-made approval.** Redundant today; correct forever. It
  means there is exactly one code path that decides whether a write may proceed, and no way to reach
  the write by a route that skipped validation. Fifth application of the chokepoint pattern.
- The `existing is not None` branch is what makes the gate **idempotent across resumes**: re-invoking
  a resumed graph must not re-ask the human. Without it, every restart produces a fresh interrupt and
  your approver learns to click through.
- **`interrupt()` payload contains the `draft_hash` and the customer-facing text — and nothing
  internal.** The human sees what will be sent. Do not put agent reasoning, findings, or the raw
  ticket body in here; the approver's attention is a scarce resource and irrelevant context is how
  approval fatigue starts (Day 69's `gated` verdict, remember).
- `decided_by` is a string the CLI supplies. On a solo project it is your name — **put it in
  anyway.** An approval record without an approver is not an audit trail, and Day 89's portfolio
  reader will notice.
- `ApprovalMismatch` distinguishes four causes with four messages. When this fires at 3am, "draft
  changed since approval (a1b2 -> c3d4)" is a diagnosis; "approval failed" is a night.
- Timezone-aware timestamp again.

### 4.1 The approver CLI

```python
# days/day-82/lab/approve_cli.py
"""Resume a graph waiting at the gate. Separate process, possibly a different day."""
```

It must:

- list runs currently interrupted (from the checkpointer, not from a list you maintain),
- print the draft **exactly as the customer would see it**,
- take `approve` / `reject` plus a reason, and a `--by` name,
- resume the graph with `Command(resume={...})`.

**Line by line:**

- Listing from the checkpointer is the point: **the graph's own state is the queue.** A parallel list
  of pending approvals is a second source of truth that will drift.
- Printing exactly what the customer sees — no truncation, no "..." — because an approval of a
  summary is not an approval.
- `--by` is required, not defaulted. Friction on purpose.

### 4.2 The kill-at-the-gate drill

Record verbatim in `days/day-82/lab/kill_at_the_gate.md`:

```bash
uv run python days/day-79/lab/run_spine.py T-9004      # stops at the gate
# kill the terminal entirely. Close it. Reboot if you like.
uv run python days/day-82/lab/approve_cli.py --list
uv run python days/day-82/lab/approve_cli.py T-9004-<suffix> approve --by "you"
ls outbox/
```

Then answer, in writing: did anything before the gate re-run? Where did the draft come from — the
model again, or the checkpoint? What is in `.state/approvals/`? **What happens if you approve
twice?**

That last one is the important one. **Run it.** Approving twice must produce one write, not two.

---

## §5 The write, and the retry problem

```python
# src/mandala/organs/write.py
"""The only place in Mandala that affects the outside world."""

from __future__ import annotations

import json
import pathlib

from mandala.obs.tracing import span
from mandala.organs.approval import Approval, check
from mandala.permissions import check as permission_check
from mandala.schemas_resolution import Resolution

OUTBOX = pathlib.Path("outbox")


class AlreadySent(RuntimeError):
    """This approved draft was already delivered. Not an error to retry through."""


def post_reply(resolution: Resolution, approval: Approval, *, agent: str = "resolver") -> str:
    permission_check(agent, "post_reply")
    check(approval, resolution, approval.run_id)

    OUTBOX.mkdir(parents=True, exist_ok=True)
    receipt_path = OUTBOX / f"{approval.run_id}.json"
    if receipt_path.exists():
        raise AlreadySent(f"{approval.run_id} already delivered")

    with span("mandala.write.post_reply", run_id=approval.run_id,
              draft_hash=resolution.content_hash, approved_by=approval.decided_by):
        receipt_path.write_text(
            json.dumps({"run_id": approval.run_id, "draft_hash": resolution.content_hash,
                        "body": resolution.body, "approved_by": approval.decided_by,
                        "approved_at": approval.decided_at}, indent=2),
            encoding="utf-8",
        )
    return receipt_path.name
```

**Line by line:**

- **Three gates before anything happens**: permission check (Day 8), approval check (today), and
  already-sent check. In that order — cheapest and most categorical first.
- **`AlreadySent` raises rather than returning quietly.** This is the retry problem, and it is worth
  a paragraph: Day 49 taught you retry policy, and Day 71's `did_not_retry_a_write` rubric exists
  because a framework-level retry around a write is a double-send. Here the write is
  **naturally idempotent** (the receipt file's existence is the record), and the exception makes a
  retry loud instead of silent. **A write that is not idempotent must not be retried at all**, and
  the blast-radius sentence you wrote in §3 says exactly that.
- The span records `draft_hash` and `approved_by` — so the trace log, which the Phase-12 gate audits,
  can prove every write had an approval and which draft it was for. **That is what "zero unapproved
  external writes in the trace log" is checked against**, and it only works because you put the
  attributes in.
- `permission_check` is called with the agent name, which is hard-coded to `"resolver"` here as a
  default. Consider whether it should be a required argument — a default that grants the right
  permission is convenient and slightly wrong. Decide, and write down why.

---

## §6 The eval that must be able to fail

```python
# tests/test_approval.py + tests/test_external_write.py
import pytest

from mandala.organs.approval import Approval, ApprovalMismatch, check
from mandala.organs.write import AlreadySent, post_reply

pytestmark = pytest.mark.eval_trajectory


def _appr(**kw):
    base = dict(run_id="T-1-a", draft_hash="abc123", decided_by="you",
                decided_at="2026-08-21T00:00:00+00:00", decision="approve")
    return Approval(**{**base, **kw})


def test_no_approval_means_no_write(res):
    with pytest.raises(ApprovalMismatch):
        check(None, res, "T-1-a")


def test_an_approval_for_a_different_run_is_refused(res):
    with pytest.raises(ApprovalMismatch, match="belongs to"):
        check(_appr(run_id="T-9-z"), res, "T-1-a")


def test_a_changed_draft_invalidates_the_approval(res):
    """The confused-deputy test. Flip it: drop the hash check and approve A, send B."""
    with pytest.raises(ApprovalMismatch, match="draft changed"):
        check(_appr(draft_hash="stale000"), res, "T-1-a")


def test_a_rejection_is_not_an_approval(res):
    with pytest.raises(ApprovalMismatch, match="rejection"):
        check(_appr(decision="reject", reason="tone"), res, "T-1-a")


def test_reordering_citations_does_not_invalidate_an_approval(res_a, res_b):
    """Yesterday's hash decisions, load-bearing today."""
    assert res_a.content_hash == res_b.content_hash


def test_writing_twice_raises_rather_than_duplicating(tmp_path, monkeypatch, res):
    monkeypatch.setattr("mandala.organs.write.OUTBOX", tmp_path)
    a = _appr(draft_hash=res.content_hash)
    post_reply(res, a)
    with pytest.raises(AlreadySent):
        post_reply(res, a)
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_an_agent_without_the_grant_cannot_write(res):
    a = _appr(draft_hash=res.content_hash)
    with pytest.raises(Exception):
        post_reply(res, a, agent="researcher")


def test_the_researcher_still_holds_no_write_tool():
    from mandala.permissions import AGENTS, TOOLS

    assert not any(TOOLS[t].writes for t in AGENTS["researcher"].tools)


def test_no_agent_holds_the_lethal_trifecta_after_adding_a_write_tool():
    """Day 8's assertion, on the day it finally has something to catch."""
    from mandala.permissions import trifecta_violations

    assert trifecta_violations() == []


def test_the_permission_table_was_regenerated():
    from scripts.gen_permission_table import render

    import pathlib

    assert pathlib.Path("docs/PERMISSION_TABLE.md").read_text(encoding="utf-8") == render()


def test_every_write_span_carries_an_approval_attribute():
    """Flip it: drop `approved_by` from the span and the Phase-12 gate becomes unprovable."""
    import inspect

    from mandala.organs import write

    src = inspect.getsource(write.post_reply)
    assert "approved_by" in src and "draft_hash" in src
```

**Line by line:**

- `test_a_changed_draft_invalidates_the_approval` is the day's headline and the whole confused-deputy
  defence in one assertion.
- `test_no_agent_holds_the_lethal_trifecta_after_adding_a_write_tool` — that test has been green for
  74 days with nothing to catch. **Today it finally has teeth**, and it is worth pausing on: this is
  what it looks like when a control written early pays off late.
- `test_writing_twice_raises_rather_than_duplicating` asserts *both* the exception and the file count.
  Asserting only the exception would pass while a second file was written.
- `test_every_write_span_carries_an_approval_attribute` inspects source — crude, and it protects the
  evidence that tomorrow's gate audit depends on.

---

## §7 Traps

- **`input()` as the approval.** Dies with the process, re-runs everything.
- **Approval as a boolean.** No who, no when, no what. Not evidence.
- **Approval bound to a run rather than a draft hash.** Approve A, send B.
- **Re-asking on resume.** Trains your approver to click through.
- **Internal context in the approval payload.** Fatigue, and eventually a leaked note.
- **A parallel list of pending approvals.** The checkpointer is the queue.
- **A defaulted `--by`.** An audit trail with no approver.
- **Retrying a write.** Idempotent here by luck of design; name it, don't rely on it.
- **Returning quietly on already-sent.** Silent retries are how doubles happen.
- **Forgetting `approved_by`/`draft_hash` on the write span.** Tomorrow's gate becomes unprovable.
- **Groaning at the drift-test failure instead of reading the diff.** That failure is the feature.
- **A Resolver that reads the ticket body.** You just rebuilt the trifecta.
- **Pointing at a real channel today.** Local outbox; say why in the notes.

---

## §8 Request budget

**Declared: ~12 model requests, Groq — the gate itself is free.**

| What | Requests |
|---|---|
| All tests | **0** |
| Approval + write path | **0** |
| Two full spine runs to reach the gate | ≤ 10 |
| Kill-at-the-gate drill (resume costs almost nothing) | ≤ 2 |

**Notice that the most consequential capability in the system costs nothing to exercise.** The write
path, the approval check, the permission check and the idempotency guard are all deterministic. That
means Day 74's free CI gate covers your riskiest code completely — which is exactly the property you
want, and it is not an accident: it is the result of keeping decisions in code rather than in
prompts, phase after phase.

---

## §9 Verify before you code

Written **2026-08-21** against `langgraph==1.2.11`:

- **`interrupt()` import path and semantics** — `langgraph.types.interrupt`? What does it return on
  resume, and does the **whole node re-execute** or only resume after the call? This decides whether
  `approve_node` can double-record. **Today's biggest risk**; Day 79 §9 asked you to check it.
- **`Command(resume=...)`** — the current resume API and how it maps to the interrupt's return value.
- **Listing interrupted threads** from `SqliteSaver` — is there a supported way to enumerate pending
  interrupts, or do you need `graph.get_state(config)` per thread? The CLI's `--list` depends on it.
- **Does an interrupt inside a node persist mid-node state**, or does the node restart from its top?
  If it restarts, your `existing is not None` branch is doing more work than you think.
- **`asdict()` on a frozen dataclass into graph state** — confirm it round-trips through the
  checkpointer.
- `https://docs.langchain.com/oss/python/langgraph/human-in-the-loop` — read today.

---

## §10 Say it in an interview

> "This is where the system got its first write capability, and three things had to be true. The
> approval had to survive a restart, so it's a LangGraph interrupt persisted by the checkpointer
> rather than a blocking prompt — I killed the process at the gate, approved from a different process
> the next day, and the graph resumed without re-running anything or re-asking. The approval had to
> bind to a specific artifact, so it records the content hash of the exact draft; if the draft changes
> at all the approval is refused, which blocks the confused-deputy case where you approve one thing
> and something else gets sent. And it had to be a record rather than a flag: who, when, which hash,
> which run — because the phase gate is 'zero unapproved external writes in the trace log', and you
> can't audit a boolean. The moment I liked best was mechanical: adding the write tool changed the
> permission table, which failed a drift test I'd written twelve days earlier and blocked CI until I
> regenerated the doc and looked at the diff — a new row with a blast-radius sentence and a
> recomputed trifecta table. And the trifecta assertion I'd been carrying green since week two finally
> had something to catch, because the writing agent is the one agent that never reads the ticket body
> or the search results."

---

## §11 Done when

```bash
./m check
./m done 82
```
