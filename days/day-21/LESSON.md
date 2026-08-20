---
day: 21
phase: 3
phase_name: "OpenAI Agents SDK advanced"
title: "Guardrails + approvals composed; AgentKit literacy"
ids: ["OAI-23", "OAI-25"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 21 — Guardrails + approvals composed; AgentKit literacy

**Phase 3 · OpenAI Agents SDK advanced** · IDs: **OAI-23 🛠️**, **OAI-25 🅿️**

> **Yesterday:** durability — Temporal activities and a workflow that survives a crash, plus realtime
> awareness. Retries became safe because Day 6's idempotency keys became load-bearing.
> **Today:** the synthesis day. Every way Mandala has learned to say *no* — guardrails, the
> permission table, human approvals — stops being three separate files and becomes **one ordered
> policy** with a decision trace. The plan says it plainly: *"Mandala's Resolver gets its full
> permission story here."* Then AgentKit 🅿️: what the managed layer buys, and what it locks.
> **Tomorrow:** the **Phase-3 gate** — a long-horizon, file-touching agent running on free models
> inside the local Docker sandbox you built on Day 19, plus the written harness/sandbox explainer,
> good enough to give in an interview.

```bash
./m start 21
./m scaffold 21
```

> ⚠️ **One plan inconsistency was found writing this day** (Principle 14, logged — do not fix it
> here). The plan's **OAI-23** row is marked 🛠️ (buildable) and lists three ingredients: guardrails,
> human approvals, and *tool `allowed_callers`*. But `allowed_callers` belongs to **OAI-17**, which
> is marked 🅿️ and needs a paid Responses key. So one third of a 🛠️ row is not buildable here. §3.4
> handles that honestly rather than pretending: it teaches what `allowed_callers` is, states why we
> cannot run it, and shows the free equivalent Mandala has been carrying since Day 8.

---

## §1 The story

Read your own repo for a minute. By the end of Day 20, Mandala can refuse an action in **four
different places**, written on four different days, by four different mechanisms:

| Where | Built on | Mechanism |
|---|---|---|
| `guardrails.py` | Day 12 | `@input_guardrail` / `@output_guardrail`, tripwires |
| `permissions.py` | Day 8 | `check(agent, tool)` against a frozen table |
| `context.py` | Day 12 | `approvals_required=True`, a flag nothing reads yet |
| `mcp_mount.py` | Day 16 | `ApprovalGate`, guarding an MCP server with nothing to guard |

Four ways of saying no. And **no defined order between them**, no shared vocabulary, and no single
place where you could point at a refused action and say *which one refused it*. That is not a
policy. That is four opinions in a trench coat.

It matters more than it sounds, because the four are not equally expensive, and the expensive one
is a person:

- Asking `permissions.check("researcher", "post_reply")` costs a `frozenset` lookup. Free.
- Running `find_secrets(text)` costs six compiled regexes over a string. Microseconds.
- Asking a human whether this reply should go to a customer costs **a human**. Seconds if they are
  at their desk, hours if they are not, and — the part nobody budgets for — a slice of the finite
  attention they will still need tomorrow.

So there is exactly one sensible order, and once you see it you cannot unsee it:

> **Cheap checks run first, humans last. Never spend a person's attention on something a `set`
> membership test could have refused.**

That sentence is today's whole thesis, and today's lab is that sentence turned into a module with a
decision trace attached. The trace is the artifact: for any attempted action, you get back *which
layer allowed or refused it, and at what cost*. That is what you show a hiring panel, and it is what
you show your own security reviewer on the day someone asks "why did the agent post that?"

There is a failure mode waiting at the end of it, and it is not a bug — it is a design failure that
looks like diligence. **Approval fatigue**: a gate that fires on everything gets clicked through, and
a gate that gets clicked through is *worse than no gate*, because it manufactures a record of human
oversight that did not happen. §3.11 is about that, and it is the trap of the day.

Then §4, which costs nothing and is not optional: **AgentKit** — ChatKit, Agent Builder, the
connector registry. The managed layer around the SDK. The plan's framing is exact: *"know what it
buys and what it locks."* Both halves, honestly, in one table. You will be asked about it, and the
answer that gets respect is not "no-code is bad"; it is a priced comparison.

---

## §2 Setup — run this

**No new packages today. None.** Everything today needs has been installed since Day 12:
`openai-agents[litellm]` (Day 9), `pydantic` (Day 4), `pytest` (Day 0). `docs/PINS.md` has no
Day-21 ledger row and must not grow one.

That is not a coincidence and it is worth one sentence: **a permission story that needed a new
dependency would be a permission story you now have to audit somebody else's code for.** Today's
entire policy layer is a tuple, four pure functions, two dataclasses and a callable. That is on
purpose — see §7, where almost the whole day costs **0 model requests**.

```bash
mkdir -p days/day-21/lab
touch src/mandala/resolver_policy.py
touch days/day-21/lab/policy_demo.py
touch tests/test_resolver_policy.py
```

Today composes four earlier days, so all four must be green **before** you start:

```bash
uv run pytest tests/test_permissions.py tests/test_guardrails.py \
              tests/test_context.py tests/test_mcp_mount.py -q
```

- `test_permissions.py` — Day 8's table, and `trifecta_violations() == []`.
- `test_guardrails.py` — Day 12's four tripwires.
- `test_context.py` — `MandalaContext`, including `approvals_required` defaulting to `True`.
- `test_mcp_mount.py` — Day 16's `ApprovalGate`.

**If any of those are red, stop and fix them.** Today does not add a new capability; it adds an order
and a trace over capabilities that already exist. Composing broken parts produces a policy that is
confidently wrong, which is the only kind worse than none.

One thing you must have finished before the demo will do anything interesting: **Day 16's
`console_approver` `TODO(me)`.** It shipped unwritten because it had nothing real to guard — the
`ticket-db` server is read-only and `NEEDS_APPROVAL` was an empty `frozenset`. Today it guards
`post_reply`. Its three rules were the rep and all three bite today:

1. print the tool name **and** the arguments — approving a call you cannot see is theatre;
2. anything other than an explicit yes is a no, including EOF and Ctrl-D;
3. **if stdin is not a tty, return `False` without blocking** — a prompt that hangs a test suite is
   how approval gates get deleted.

Your fixtures are unchanged: **T-1001 … T-1010** (Day 2) plus **T-9002**, the canary carrying
`PINEAPPLE-7731` (Day 13). Today's battery uses T-1001, T-1004 and T-9002.

---

## §3 OAI-23 🛠️ — Three kinds of check, three different times

### 3.1 The distinction the whole day rests on

Guardrails, permissions and approvals get lumped together as "safety". They are not the same thing,
they do not run at the same moment, and they do not cost the same. **Confusing them is how systems
end up both unsafe and annoying at once** — unsafe because a check that should have been structural
was left to a regex, annoying because a check a `frozenset` could have made was handed to a person.

| Check | When | Cost | What it is for |
|---|---|---|---|
| **Guardrail** (Day 12) | before/after the run, in-process | cheap, milliseconds | catch the obviously-wrong input or output |
| **Permission** (Day 8) | at tool-call dispatch | free, a set lookup | this agent may not do that, ever |
| **Approval** (Principle 12) | before an external side effect | expensive — a human's time | a human owns this consequence |

Read the third column again, because it is the part people skip. The three answer **three different
questions**:

- A guardrail asks *"is this text obviously wrong?"* It is a **heuristic**. It has false positives
  and false negatives, it can be tuned, and it is allowed to be wrong occasionally.
- A permission asks *"is this agent allowed to hold this capability at all?"* It is **structural**.
  It has no false positives, because it is not a judgement — it is a lookup in a table you wrote
  down and reviewed (Day 8).
- An approval asks *"does a human accept this consequence?"* It is **authority**. It cannot be
  computed, only delegated, and Principle 12 says it is required before any external side effect
  until Phase 13's graduated-autonomy review.

A heuristic must never be asked to do a structural job. That is why `guardrails.py` does not contain
a rule like *"refuse if the reply looks like it is being sent by the Researcher"* — the Researcher
does not hold `post_reply`, full stop, and that fact lives in the permission table where it cannot
be argued with by a cleverly-worded ticket body (Day 15).

And a human must never be asked to do a heuristic's job. That is the ordering rule.

### 3.2 The order, and why it is the design

Here is the same three checks, ordered the second way — not by *when in a run* they live, but by
**what they cost when a single action is attempted**:

| # | Layer | Cost | Mechanism |
|---|---|---|---|
| 1 | `permission` | **free** | one `frozenset` membership test against Day 8's `AGENTS` |
| 2 | `guardrail:input` | **ms** | six compiled regexes plus a `len()` (Day 12) |
| 3 | `approval` | **a human** | seconds at best, hours at worst, attention forever |
| 4 | `guardrail:output` | **ms** | cheap — but it cannot run until the output exists |

> **Cheap checks run first, humans last. Never spend a person's attention on something a `set`
> membership test could have refused.**

Two things in that table are worth arguing about, so argue about them now rather than in review.

**Why does `permission` come before `guardrail:input`, when Day 12 attached guardrails to the agent
and Day 8's check runs at dispatch?** Because those are two different orderings and both are real:

- **In a run**, the order is fixed by *when the information exists*. Input guardrails run before the
  model is called, because that is the only moment the input exists and nothing has been spent.
  `permissions.check()` runs at dispatch, because a tool has to be named before you can check it.
- **For one attempted action** — the unit this module reasons about — the tool is already named.
  Every layer *can* run. So the only remaining ordering rule is cost, and cost says the `frozenset`
  goes first.

**Why is `guardrail:output` cheap and still last?** Because ordering by cost only applies among the
checks that *can* run right now. The output guardrail is gated by information availability, not by
price. Which produces the day's most uncomfortable case, and you should sit with it: **a human can
approve a write, and the output guardrail can still refuse it.** You spent the expensive thing and
got a refusal from the cheap thing anyway. That is not a bug in the ordering — it is the honest
shape of a pipeline where the last check depends on a result the earlier checks could not see. Case
7 of the battery in §3.9 shows it happening.

### 3.3 What today does *not* add

Look at what is missing from the setup block in §2: there is no edit to `permissions.py`. **Today
adds no capability to the table.** `post_reply` has been in `TOOLS` since Day 8 with
`writes=True` and `blast_radius="HIGH — visible to a customer, cannot be unsent"`, granted to the
Resolver, and in thirteen days nothing has ever called it — Day 8's version raises `AssertionError`
on purpose, a landmine that exists so the schema is honest.

Today is the day the landmine gets defused, and it is defused by **surrounding it with checks, not
by widening anything**. That is the shape of a real permission story: the capability was declared,
reviewed and blast-radius-documented long before it was reachable, and the day it becomes reachable
is a day of adding constraints rather than adding grants.

One honest blast-radius decision, stated up front (Principle 6): **today's `post_reply` writes to a
local outbox directory, not to a customer.** `.mandala/outbox/<ticket>.json`, gitignored. There is no
customer on the other end of this curriculum and inventing one would be a lie with a network call
attached. The write is real enough to need every layer — it is external to the process, it persists,
and it is keyed by Day 6's idempotency key so Day 20's retries cannot double-send — and it is
survivable enough that a student running the battery at midnight does not email a stranger.

### 3.4 `allowed_callers` 🅿️ — the paid feature is a narrower version of your table

The plan's OAI-23 row lists `allowed_callers` as the third ingredient. Per **OAI-17** (Day 18) it is
a **paid Responses-API feature** and we cannot run it. Here is the honest treatment.

**What it is.** On the Responses API you can attach `allowed_callers` to a tool definition to
declare *which caller may invoke that tool* — most usefully, whether the model-written program
inside the hosted code interpreter may call it, as opposed to only the model itself:

```python
# 🅿️ PAID — OpenAI Responses API. Reproduced for study only; we have no key (Principle 5).
tools=[
    {"type": "code_interpreter", "container": {"type": "auto"}},
    {"type": "function", "name": "get_ticket",  "allowed_callers": ["code_interpreter"]},
    {"type": "function", "name": "post_reply"},          # no program may ever call this
]
```

**Line by line:**

- Day 18 said it and it is still the sentence: **`allowed_callers` answers "who may call this tool",
  not "how fast is this tool".** It is a permission boundary that people file under performance
  because it arrived in a performance feature's release notes.
- Row two is the whole reason it belongs in a day about composing checks: the read tool is opened to
  the generated program, the **write tool is not**. A write stays a deliberate, single, visible tool
  call that the model has to make on the record — which is exactly what an approval gate needs in
  order to have something to attach to.
- Omitting the field is the interesting case, and §8 asks you to confirm it from the docs: **if
  omission means "any caller", it is a default-open permission field**, and a default-open
  permission field is the opposite of `MandalaContext.approvals_required=True` (Day 12), whose whole
  point is that the safe value is what you get when you forget.

**Why we cannot run it.** Same mechanism as Day 18 §3.5, unchanged: it is a Responses-API surface
with a hosted `code_interpreter` tool type, and we reach models through `LitellmModel` (Day 9)
pointed at Groq / Gemini / OpenRouter — OpenAI-*compatible* on the chat surface, not implementers of
OpenAI's hosted tool types. There is no paid key, today or on Day 90.

**And here is the line worth having ready.** Mandala already has the free equivalent, and it is not
an approximation — it is a **superset**:

| The paid field says | Mandala says | Where |
|---|---|---|
| this **tool** may be called by the **code interpreter** | this **agent** may hold this **tool** | `permissions.AGENTS[...].tools`, Day 8 |
| (nothing) | ...and here is what that tool can destroy | `ToolSpec.blast_radius`, Day 8 |
| (nothing) | ...and this batching caller may only run these **operations** | `coordinator.OPERATIONS`, Day 18 |
| (nothing) | ...and no operation may reach a tool its caller lacks | `run_plan`'s pre-flight `check()`, Day 18 |

> **The paid feature is a narrower version of the table you already keep.** `allowed_callers` is
> per-caller-per-tool, declared inside a request payload, enforced on their side, and invisible to
> your test suite. Day 8's table is per-agent-per-tool, declared in your repo, enforced by a function
> you can call from a unit test, and asserted every day by `trifecta_violations() == []`. Day 18's
> coordinator operation allowlist adds the layer `allowed_callers` does not have at all: not just
> *which caller may invoke a tool*, but *which operations that caller may compose*.

That is the interview answer. Not "I couldn't afford it" — **"I have it, plus two layers it does not
have, and mine is testable at zero cost."**

### 3.5 One approval mechanism, two attachment points

Before any code: Day 16 already built an approval mechanism, and **you are not allowed to build a
second one.** Two ways of asking a human is zero ways of auditing that a human was asked.

Day 16's `ApprovalGate` wraps an **MCP server** and intercepts `call_tool`. Today's need is a gate
at **function-tool dispatch**, inside the Resolver's own process. Different attachment point, same
question. So the thing to keep single is not the wrapper class — it is the **approver callable**:

```python
Approver = Callable[[str, Mapping[str, object]], bool]        # (tool_name, arguments) -> yes/no
```

That signature is Day 16's, unchanged. `console_approver` already implements it. Today's policy
layer consumes exactly the same callable, which means:

- there is **one** place a human is asked (`console_approver`, and its three rules);
- there is **one** place the "not a tty means no" behaviour lives, so tests cannot hang;
- an approver written for a web UI on Day 64 drops into both attachment points with no changes.

**Two extensions to existing files, both announced rather than smuggled.** In `src/mandala/context.py`,
one field:

```python
    approvals_required: bool = True                  # Day 12, unchanged
    approver: Approver | None = None                 # Day 21: WHO to ask. Default None = deny.
```

and in `src/mandala/mcp_mount.py`, `ApprovalGate.NEEDS_APPROVAL` stops being hand-written:

```python
-    NEEDS_APPROVAL: frozenset[str] = frozenset()          # Day 16: nothing to gate, yet
+    NEEDS_APPROVAL: frozenset[str] = frozenset(           # Day 21: derived, never listed
+        name for name, spec in TOOLS.items() if spec.writes
+    )
```

**Line by line:**

- `approver: Approver | None = None` is a **service, not a flag** — and services live in the context,
  which is precisely what Day 12 built `MandalaContext` for. `approvals_required` still decides
  *whether* to ask; `approver` decides *who*. This is not the "second flag" the brief warns about;
  adding a second boolean would have been.
- `= None` keeps Day 12's rule intact: **the safe value is the default.** No approver configured means
  no approval obtainable means the write is refused. Forgetting is safe.
- Deriving `NEEDS_APPROVAL` from `TOOLS[...].writes` is the fix to the one thing that was wrong with
  Day 16's gate: a hand-maintained frozenset of tool names is **a second source of truth about which
  tools write**, and the day it drifts from the table is the day a write slips past ungated. Day 8's
  table already carries `writes: bool` on every `ToolSpec`. Read it; do not restate it.
- Note what this derivation buys for free: the day someone adds a write tool to the table, it is
  gated **before** anyone remembers to gate it. That is the difference between a checklist and a
  mechanism.

### 3.6 `src/mandala/resolver_policy.py` — part one, the layers

```python
"""The Resolver's whole permission story, in one place and in cost order.

Why this file exists
--------------------
By Day 20 Mandala can refuse an action in four places, written on four days, with
no defined order between them:

    Day 8   permissions.check()          this agent may not hold that tool, ever
    Day 12  guardrails.*                 this input/output is obviously wrong
    Day 12  context.approvals_required   a human owns this consequence
    Day 16  ApprovalGate                 the same human, asked at the MCP boundary

Four ways of saying no and no order between them is not a policy; it is four
opinions. This file gives them an order, and THE ORDER IS THE DESIGN:

    CHEAP CHECKS RUN FIRST, HUMANS LAST.

Never spend a person's attention on something a set membership test could have
refused. Everything below exists to make that sentence executable and testable.

This module deliberately does NOT build an Agent. Constructing one calls
make_model() (Day 9), which needs provider keys; a policy you cannot unit-test
without keys is a policy that stops being tested. The lab wires it up instead.

Usage
-----
    >>> from mandala.context import MandalaContext
    >>> from mandala.resolver_policy import AttemptedAction, evaluate
    >>> ctx = MandalaContext(actor="agent:researcher", request_id="req-1")
    >>> evaluate(AttemptedAction(tool="post_reply"), context=ctx).refused_by
    'permission'
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from agents import RunContextWrapper, function_tool

from mandala import permissions
from mandala.context import MandalaContext
from mandala.guardrails import CUSTOMER_REF, MAX_INPUT_CHARS, find_secrets
from mandala.permissions import AGENTS, TOOLS, PermissionDenied
from mandala.sdk_tools import tool_error

Verdict = Literal["allow", "refuse", "skipped"]
Approver = Callable[[str, Mapping[str, object]], bool]      # Day 16's signature, unchanged

# THE LAYER ORDER IS THE POLICY. Index 0 is the cheapest thing that can say no.
# Reordering this tuple changes what Mandala spends a human on; see the flip-it test in §5.
LAYERS: tuple[tuple[str, str], ...] = (
    ("permission",       "free"),    # one frozenset lookup against Day 8's AGENTS table
    ("guardrail:input",  "ms"),      # Day 12's compiled regexes over the text we were handed
    ("approval",         "human"),   # Principle 12. Seconds at best, attention forever.
    ("guardrail:output", "ms"),      # cheap, but LAST: the output does not exist any earlier
)
LAYER_NAMES: tuple[str, ...] = tuple(name for name, _ in LAYERS)
LAYER_COST: dict[str, str] = dict(LAYERS)

# Derived from Day 8's table, never listed by hand. Day 16's ApprovalGate now reads this too.
NEEDS_APPROVAL: frozenset[str] = frozenset(n for n, spec in TOOLS.items() if spec.writes)

OUTBOX = Path(".mandala/outbox")     # the "external" side effect. Gitignored. Blast radius: local.


class PolicyRefused(PermissionDenied):
    """Refused by the composed policy. Carries the trace that explains which layer.

    Subclasses PermissionDenied ON PURPOSE: Day 10's tool_error re-raises
    PermissionDenied so a security failure stops the run instead of becoming a
    sentence the model reads and works around. Inheriting means today's refusals
    inherit that behaviour with no new escape hatch to remember.
    """

    def __init__(self, trace: DecisionTrace) -> None:
        self.trace = trace
        refusal = next(d for d in trace.decisions if d.verdict == "refuse")
        super().__init__(f"{trace.action.tool} refused by {refusal.layer}: {refusal.reason}")


class ApprovalRequired(PolicyRefused):
    """Refused specifically because no human said yes. Principle 12's exception type."""
```

**Line by line:**

- The docstring **names the four mechanisms with their day numbers and then states the order** — the
  same shape as Day 18's `coordinator.py`, where the docstring ranked the four defences. A reader
  arriving here in three months needs to know which line they are not allowed to move, and the
  `LAYERS` tuple is that line.
- *"This module deliberately does NOT build an Agent"* — say it in the file, because the temptation
  is real and the consequence is specific: `make_model()` needs `GEMINI_API_KEY` / `GROQ_API_KEY`, so
  a policy module that imports it is a policy module whose tests need keys, and tests that need keys
  are tests that get skipped in CI. **Everything in §5 costs 0 requests because of this line.**
- `Approver = Callable[[str, Mapping[str, object]], bool]` — Day 16's exact signature. Not
  `Mapping[str, Any]`: the arguments are opaque to the policy, and typing them as `object` says so.
- `LAYERS` as a tuple of `(name, cost)` pairs rather than two parallel structures — one declaration
  produces both the order and the price list, so they cannot disagree. `LAYER_NAMES` and `LAYER_COST`
  are derived views, in the same spirit as `MandalaContext.may_write` being derived rather than stored
  (Day 12).
- The cost values are `"free"`, `"ms"`, `"human"` — **words, not numbers.** A `cost_us: int` field
  would invite someone to compare `1200` with a human's time on the same axis, which is the exact
  category error the day is about. `blast_radius` being prose rather than a severity enum (Day 8) is
  the same call, made for the same reason.
- `("guardrail:output", "ms")` sitting *after* `("approval", "human")` with a comment explaining why —
  because it violates the sort order and a reader will assume it is a mistake. Any line that looks
  like a bug and is not needs a comment saying so.
- `NEEDS_APPROVAL` is a **comprehension over `TOOLS`, not a literal.** §3.5's argument, in code.
- `OUTBOX` is a module constant so tests can monkeypatch it and the demo can print it. Note it is
  *not* injected through the context like `tickets_path` is — an inconsistency you should notice.
  It is defensible for a lab (nothing reads the outbox back) and it is exactly the kind of thing that
  becomes a bug later; §6 lists it as a trap.
- `PolicyRefused(PermissionDenied)` — the inheritance is the design. Day 10 established that
  `tool_error` converts expected failures into text the model can read, **except** `PermissionDenied`,
  which is re-raised so it stops the run. Day 15 relied on it. Day 18 relied on it. Making today's
  refusals a subclass means that rule keeps holding without a single edit to `sdk_tools.py`. If
  `PolicyRefused` inherited from `RuntimeError` instead, every refusal today would become a polite
  string the model could try to route around.
- `self.trace = trace` on the exception — **the refusal carries its own explanation.** An exception
  whose message says "denied" and nothing else is a support ticket; one that carries the decision
  trace is a log line and a test assertion.
- `ApprovalRequired(PolicyRefused)` exists so a test can assert *which* layer refused without
  string-matching a message (§5), and so a caller can catch "a human is needed" separately from
  "this was never going to be allowed". Those deserve different UX.


### 3.7 `src/mandala/resolver_policy.py` — part two, the trace and the four layers

```python
@dataclass(frozen=True)
class Decision:
    """One layer's answer about one action. This is the unit of the audit trail."""

    layer: str
    verdict: Verdict
    reason: str

    @property
    def cost(self) -> str:
        return LAYER_COST[self.layer]


@dataclass(frozen=True)
class AttemptedAction:
    """What somebody is trying to do. Not what happened -- what was ATTEMPTED."""

    tool: str
    args: Mapping[str, object] = field(default_factory=dict)
    input_text: str = ""        # the untrusted text this action came from (Day 15)
    output_text: str = ""       # the answer, when there is one yet

    @property
    def writes(self) -> bool:
        spec = TOOLS.get(self.tool)
        return bool(spec) and spec.writes


@dataclass
class DecisionTrace:
    """Which layer allowed or refused this action, in the order they ran. THE artifact."""

    action: AttemptedAction
    decisions: list[Decision] = field(default_factory=list)

    @property
    def refused_by(self) -> str | None:
        return next((d.layer for d in self.decisions if d.verdict == "refuse"), None)

    @property
    def allowed(self) -> bool:
        return bool(self.decisions) and self.refused_by is None

    @property
    def layers_run(self) -> list[str]:
        return [d.layer for d in self.decisions]

    @property
    def asked_a_human(self) -> bool:
        """The number this policy exists to keep small."""
        return any(d.layer == "approval" and d.verdict != "skipped" for d in self.decisions)

    def audit_lines(self, context: MandalaContext) -> list[str]:
        """Day 12's audit format, one line per layer. Greppable by request_id."""
        return [
            context.audit(f"policy.{d.layer}", f"{d.verdict} {self.action.tool} <- {d.reason}")
            for d in self.decisions
        ]
```
```python
def _permission(action: AttemptedAction, context: MandalaContext) -> Decision:
    """Layer 1. Free. Day 8's table, asked the way every other caller asks it."""
    try:
        permissions.check(context.agent_name, action.tool)
    except PermissionDenied as exc:
        return Decision("permission", "refuse", str(exc))
    return Decision("permission", "allow", f"{context.agent_name} holds {action.tool}")


def _guardrail_input(action: AttemptedAction, context: MandalaContext) -> Decision:
    """Layer 2. Milliseconds. Day 12's predicates, called directly."""
    found = find_secrets(action.input_text)
    if found:
        return Decision("guardrail:input", "refuse", f"secret in input: {', '.join(found)}")
    if len(action.input_text) > MAX_INPUT_CHARS:
        return Decision(
            "guardrail:input", "refuse",
            f"input is {len(action.input_text)} chars, limit {MAX_INPUT_CHARS}",
        )
    return Decision("guardrail:input", "allow", "no secrets, within budget")


def _guardrail_output(action: AttemptedAction, context: MandalaContext) -> Decision:
    """Layer 4. Milliseconds, and still last: the output did not exist any earlier."""
    found = find_secrets(action.output_text)
    if found:
        return Decision("guardrail:output", "refuse", f"secret in output: {', '.join(found)}")
    subject = getattr(context, "customer_id", None)
    leaked = sorted(
        {m for m in CUSTOMER_REF.findall(action.output_text)
         if subject is not None and m != str(subject)}
    )
    if leaked:
        return Decision("guardrail:output", "refuse", f"names other customers: {leaked}")
    return Decision("guardrail:output", "allow", "no secrets, no other customers")


def approval_required(action: AttemptedAction, context: MandalaContext) -> bool:
    """Two flags, one answer, and THE TABLE ALWAYS WINS.

    AgentSpec.requires_approval_for_writes (Day 8) is reviewed policy, in the repo,
    per agent. MandalaContext.approvals_required (Day 12) is a runtime switch. A
    runtime switch may TIGHTEN the table and may never loosen it, so this is `or`,
    not `and`, and getting that backwards is a one-character security bug.
    """
    if action.tool not in NEEDS_APPROVAL:
        return False
    spec = AGENTS.get(context.agent_name)
    return bool(spec and spec.requires_approval_for_writes) or context.approvals_required


def _approval(action: AttemptedAction, context: MandalaContext) -> Decision:
    """Layer 3. A human. The only layer that can spend something irreplaceable."""
    if not approval_required(action, context):
        return Decision("approval", "allow", f"{action.tool} is not a gated write; nobody asked")
    if context.approver is None:
        return Decision("approval", "refuse", "no approver configured; default deny (Day 12)")
    if context.approver(action.tool, dict(action.args)):
        return Decision("approval", "allow", "a human approved this consequence")
    return Decision("approval", "refuse", "a human declined")
```

**Line by line:**

- `Decision` is `frozen=True` — an audit record that can be edited after the fact is not an audit
  record. Same instinct as `MandalaContext` being frozen so a tool cannot rewrite `actor` (Day 12).
- `Decision.cost` is a **property reading `LAYER_COST`**, not a stored field. Stored, someone could
  construct `Decision("approval", ..., cost="free")` and the entire ordering argument would be
  undone by a keyword argument. Derive facts you already know — Day 12's `may_write`, again.
- `AttemptedAction` carries `input_text` and `output_text` **as data on the action**, so one object
  can be evaluated at any point in a run. The rejected alternative was four functions each taking
  whatever they needed, which makes `evaluate()` impossible to write as a loop — and a loop over
  `LAYERS` is what puts the order in exactly one visible place.
- `output_text: str = ""` defaults empty, so an action evaluated *before* the model answers passes
  the output layer trivially. Correct, and a hole worth naming aloud: **an empty output is not a
  checked output.** §5 asserts the run-time path re-evaluates once the answer exists.
- `DecisionTrace.refused_by` takes the **first** refusal in order. With the default short-circuit
  there is only ever one; in audit mode (§3.8) there can be several, and then "first" reads as
  "cheapest", which is precisely the reading you want a reviewer to take.
- `asked_a_human` is a property, and it is the metric this module exists to keep small. **If you
  instrument one thing today, instrument this**: actions-evaluated over humans-asked predicts
  approval fatigue (§3.11) months before anyone complains about it.
- `audit_lines()` reuses `context.audit()` from Day 12 instead of inventing a format, so today's
  refusals grep by `request_id` next to every other line the system has emitted since Day 12. One
  line **per layer**, not per action: "who said no" is only useful beside "who said yes first".
- `_permission` catches `PermissionDenied` and returns a `Decision` rather than letting it fly. That
  looks like it contradicts Day 10's "never degrade a security failure" and it does not — the
  distinction is the day's second-best idea. **`evaluate()` is an inspector; `enforce()` (§3.8) is
  the thing that raises.** Separating *decide* from *act* is what makes the demo battery possible at
  all, and what lets a UI grey a button out with a reason instead of only failing on click.
- `_guardrail_input` calls `find_secrets` and `MAX_INPUT_CHARS` — **Day 12's predicates**, not Day
  12's decorated guardrail objects. The decorator is an attachment mechanism for the SDK's run loop;
  the logic underneath is a plain function, and today needs that logic at a second attachment point.
  One predicate, two wrappers. §5 has a `TODO(me)` pinning the two together, because "one predicate"
  is a claim and claims deserve tests.
- `_guardrail_output` repeats Day 12's `getattr(context, "customer_id", None)` degrade: no such
  field exists yet, so the check is inert until it does. Inert-by-default beats crashing-by-default
  for a field that arrives later.
- `approval_required` is the function to read twice. The two flags are **not** redundant:
  `AgentSpec.requires_approval_for_writes` is reviewed policy in the repo,
  `MandalaContext.approvals_required` is a runtime switch. The `or` means **the switch can tighten
  and can never loosen.** Someone will eventually pass `approvals_required=False` to make a test
  faster, and that must not silently disarm the Resolver's write gate.
- `if action.tool not in NEEDS_APPROVAL: return False` runs first — reads are never gated. A gate
  that fires on `get_ticket` is §3.11's failure mode arriving on day one.
- `context.approver is None` returns **refuse** — not an exception, not an allow. Default deny,
  fourth appearance in this curriculum after Day 12's `approvals_required=True`, Day 13's
  `filtered=True` and Day 16's `console_approver` returning `False` at EOF. The safe value is what
  you get when you forget.

### 3.8 `src/mandala/resolver_policy.py` — part three, the loop and the gated write

```python
def evaluate(
    action: AttemptedAction,
    *,
    context: MandalaContext,
    audit_all: bool = False,
) -> DecisionTrace:
    """Run the layers in cost order and return the trace. NEVER raises, never acts.

    audit_all=True keeps evaluating past a refusal so you can see every layer that
    WOULD have objected -- useful for a policy review, and it still never asks a
    human. Once a cheaper layer has said no, spending a person is indefensible.
    """
    trace = DecisionTrace(action=action)
    for layer in LAYER_NAMES:
        if trace.refused_by and not audit_all:
            break
        if layer == "approval" and trace.refused_by:
            trace.decisions.append(
                Decision("approval", "skipped", "already refused by a cheaper layer")
            )
            continue
        trace.decisions.append(_LAYER_FN[layer](action, context))
    return trace


_LAYER_FN: dict[str, Callable[[AttemptedAction, MandalaContext], Decision]] = {
    "permission": _permission,
    "guardrail:input": _guardrail_input,
    "approval": _approval,
    "guardrail:output": _guardrail_output,
}


def enforce(action: AttemptedAction, *, context: MandalaContext) -> DecisionTrace:
    """Evaluate, and raise if any layer refused. This is what a write tool calls."""
    trace = evaluate(action, context=context)
    if trace.refused_by == "approval":
        raise ApprovalRequired(trace)
    if trace.refused_by:
        raise PolicyRefused(trace)
    return trace


def worst_cost(trace: DecisionTrace) -> str:
    """TODO(me): the single word describing what this decision cost. 'free'/'ms'/'human'.

    Why this is the rep: it is three lines and one genuinely contested judgement.
    Is the cost of a decision the MAX of the layers that ran, or the SUM? Does a
    'skipped' approval cost anything -- you did not ask a person, but you did build
    and maintain the machinery that decided not to. And what does a refusal at layer 1
    cost, given it saved you layers 2-4? Pick one, write the reason in a comment, and
    make the battery in policy_demo.py print it. There is no single right answer; there
    is only the one you can defend when someone asks why the number moved.
    """
    raise NotImplementedError


def group_for_approval(actions: list[AttemptedAction]) -> dict[str, list[AttemptedAction]]:
    """TODO(me): batch actions that are ONE consequence into ONE approval request.

    Why this is the rep: this function is the mechanical answer to approval fatigue
    (§3.11), and writing it forces the question nobody wants to answer -- what makes two
    writes "the same consequence"? Same ticket? Same customer? Same tool within one
    request_id? Each choice trades a real risk against a real amount of human attention,
    and the batching key you pick IS your policy on that trade. Return a dict keyed by
    whatever you choose; §5 asserts only that two writes to the SAME ticket in one
    request land in one group and two different tickets do not.
    """
    raise NotImplementedError


@function_tool(name_override="post_reply", failure_error_function=tool_error)
def post_reply_gated(ctx: RunContextWrapper[MandalaContext], ticket_id: str, text: str) -> str:
    """Send a reply to the customer on a ticket. Requires human approval.

    Args:
        ticket_id: The ticket this reply belongs to, e.g. "T-1001".
        text: The exact message the customer will receive. Say what will be sent.
    """
    context = ctx.context
    action = AttemptedAction(
        tool="post_reply", args={"ticket_id": ticket_id, "text": text}, output_text=text
    )
    trace = enforce(action, context=context)          # raises PolicyRefused / ApprovalRequired

    OUTBOX.mkdir(parents=True, exist_ok=True)
    key = f"{context.request_id}:{ticket_id}"          # Day 6's idempotency key, Day 20's retries
    path = OUTBOX / f"{ticket_id}.json"
    if path.exists() and json.loads(path.read_text(encoding="utf-8")).get("key") == key:
        return f"already sent (idempotent): {path}"
    path.write_text(json.dumps({"key": key, "text": text}, indent=2), encoding="utf-8")

    for line in trace.audit_lines(context):
        print(line)
    return f"sent to outbox: {path}"
```

**Line by line:**

- `evaluate` is **a loop over `LAYER_NAMES`**, not four hand-written calls in sequence. That is the
  point of the whole module: the order lives in one tuple, a reader can check it in two seconds, and
  the flip-it test in §5 can break it by editing one line. Four inlined calls would have worked and
  would have hidden the design in control flow.
- `if trace.refused_by and not audit_all: break` — **the short circuit is the thesis, mechanised.**
  Layer 1 costs a `frozenset` lookup; if it says no, layers 2 to 4 never run and nobody is ever asked
  anything. On the researcher-attempts-`post_reply` case this saves six regexes and one human.
- `if layer == "approval" and trace.refused_by:` records a **`"skipped"`** decision rather than
  silently omitting the layer. In audit mode you need to see that approval was *considered and
  deliberately not spent*; an absent row reads as "we forgot". And note what the branch guarantees:
  **`audit_all` never asks a human.** A policy-review mode that pinged an on-call engineer for every
  historical action would be a spectacular own goal.
- `_LAYER_FN` is a dict of layer name to function, defined **after** the functions it names —
  necessary, and also the one place today where dispatch-by-string is right. Day 18 argued hard for
  `isinstance` chains over string dispatch in the coordinator, and the difference is who supplies the
  key: there, `step.op` came from **the model**; here, the keys come from `LAYERS`, a module constant
  no external input can influence. **String dispatch is safe exactly when the string is yours.**
- `evaluate` **never raises and never acts.** `enforce` raises. Two functions instead of one flag,
  because a boolean parameter that decides whether a function has side effects is a function you
  will eventually call wrong. This is also what lets §5 test every layer at zero cost with no
  `pytest.raises` scaffolding around the cases that should pass.
- `enforce` checks `refused_by == "approval"` **first**, so "a human is needed" is catchable
  separately from "this was never going to be allowed". Different situations, different UX: one is a
  queue, the other is a bug report.
- `worst_cost` is a `TODO(me)` and the demo calls it, so the battery **ships red** until you write it
  — Day 18's `plan_cost` precedent, deliberately repeated. Three lines of code, one real argument.
- `group_for_approval` is the second `TODO(me)` and nothing calls it yet. That is on purpose: it is
  the mechanism §3.11 says you need, and leaving it unwired means you have to decide *when* batching
  applies before you get to use it.
- `@function_tool(name_override="post_reply", ...)` — the tool's model-facing name is `post_reply`,
  matching `permissions.TOOLS` **exactly**. Day 15's rule: a `name_override` that drifts from the
  table is a capability your safety check cannot see. The Python function is `post_reply_gated` so
  nobody imports it thinking it is the raw Day 8 landmine.
- `failure_error_function=tool_error` — and this is where §3.6's inheritance pays. `tool_error`
  converts expected failures into text the model can read, **except** `PermissionDenied`, which it
  re-raises. `PolicyRefused` is a `PermissionDenied`, so a refused write **stops the run** instead of
  becoming a sentence the model reads and tries to route around. Zero edits to `sdk_tools.py`.
- The docstring says *"Requires human approval"* and *"Say what will be sent"* — the model is told
  the gate exists. Not as a boundary (prompts are never boundaries — Day 15, Day 18) but because a
  model that knows a human will read the text writes better text, and a model surprised by a refusal
  burns a turn recovering from it.
- `output_text=text` on the action — the reply **is** the output, so the output guardrail inspects the
  exact string that would land in the outbox. This is the case Day 12 called the mirror: a secret
  can arrive from a looked-up ticket and leave in an answer, and T-9002's `PINEAPPLE-7731` canary
  (Day 13) is in the fixtures precisely so you can prove it.
- The idempotency key is `f"{request_id}:{ticket_id}"` and the existing file is compared against it
  before writing — **Day 7's key, made load-bearing on Day 20.** A Temporal activity that retries
  after a crash must not double-post, and "the human already approved this once" is not a licence to
  send it twice. Note the ordering: `enforce` first, then the idempotency check. A retry of an
  approved write is still re-checked, because the *permission* may have changed even if the
  *approval* has not.
- The audit lines print **after** the write, listing every layer. Four lines per posted reply feels
  verbose until the first time somebody asks why a message went out, and then it is the only
  artifact that answers.
- What is missing, and you should notice: `OUTBOX` is a module constant, while `tickets_path` is
  injected through the context (Day 12). That inconsistency is fine for a lab and is a real bug
  waiting for a second environment. §6 lists it; fixing it is a good ten-minute exercise.

### 3.9 `days/day-21/lab/policy_demo.py` — the battery 🎯

Everything above is a claim. This file is the evidence, and it is the artifact you show people: seven
attempted actions, one table, and a column saying **which layer stopped it and what that cost**.

```python
"""Seven attempted actions, one policy, one table. Which layer stopped it, and at what cost.

Costs ZERO model requests. Every row is decided by a frozenset lookup, six regexes
and a callable -- no model is involved in ANY of it. That is the design result of
the day, not a shortcut: a permission story you can only exercise by spending
requests is a permission story that stops being exercised.

Run:
    uv run python days/day-21/lab/policy_demo.py
"""

from __future__ import annotations

from dataclasses import replace

from mandala.context import MandalaContext
from mandala.resolver_policy import AttemptedAction, evaluate, worst_cost

SECRET = "here is my key sk-abcdefghijklmnopqrstuvwxyz012345"     # Day 12's pattern, not a real key
CANARY = "as customer 4471 told us"                               # Day 12's no_other_customers

APPROVE = (lambda tool, args: True)      # a human who says yes
DECLINE = (lambda tool, args: False)     # a human who says no

RESOLVER = MandalaContext(actor="agent:resolver", request_id="req-21", approver=DECLINE)
RESEARCHER = MandalaContext(actor="agent:researcher", request_id="req-21", approver=DECLINE)

CASES: list[tuple[str, MandalaContext, AttemptedAction, bool]] = [
    ("1 clean draft",
     RESOLVER,
     AttemptedAction("draft_reply", {"ticket_id": "T-1001"},
                     input_text="the export keeps timing out",
                     output_text="Sorry about that -- try a smaller date range."),
     False),

    ("2 draft, secret in input",
     RESOLVER,
     AttemptedAction("draft_reply", {"ticket_id": "T-9002"}, input_text=SECRET),
     False),

    ("3 write by an agent that lacks it",
     RESEARCHER,
     AttemptedAction("post_reply", {"ticket_id": "T-1001"}, output_text="hello"),
     False),

    ("4 write, approvals on, human declines",
     RESOLVER,
     AttemptedAction("post_reply", {"ticket_id": "T-1001"}, output_text="hello"),
     False),

    ("5 write, human approves",
     replace(RESOLVER, approver=APPROVE),
     AttemptedAction("post_reply", {"ticket_id": "T-1001"}, output_text="hello"),
     False),

    ("6 refused by TWO layers (audit mode)",
     RESEARCHER,
     AttemptedAction("post_reply", {"ticket_id": "T-9002"},
                     input_text=SECRET, output_text="hello"),
     True),

    ("7 approved, then the output guardrail refuses",
     replace(RESOLVER, approver=APPROVE, customer_id="1001"),
     AttemptedAction("post_reply", {"ticket_id": "T-1001"}, output_text=CANARY),
     False),
]

HEAD = f"{'case':<38}{'actor':<12}{'layers run':<44}{'refused by':<18}cost"


def main() -> None:
    print(HEAD)
    print("-" * len(HEAD))
    for label, context, action, audit_all in CASES:
        trace = evaluate(action, context=context, audit_all=audit_all)
        refused = trace.refused_by or "-- allowed --"
        print(
            f"{label:<38}{context.agent_name:<12}"
            f"{','.join(trace.layers_run):<44}{refused:<18}{worst_cost(trace)}"
        )

    print("\n--- audit lines for case 6, the double refusal ---")
    label, context, action, _ = CASES[5]
    for line in evaluate(action, context=context, audit_all=True).audit_lines(context):
        print(" ", line)

    humans = sum(evaluate(a, context=c, audit_all=x).asked_a_human for _, c, a, x in CASES)
    print(f"\nactions evaluated: {len(CASES)}   humans asked: {humans}")
    print("Record every row in days/day-21/CHECKLIST.md.")

    # TODO(me): send these decisions to Day 14's tracer instead of stdout. JsonlTraceProcessor
    # writes spans through SAFE_SPAN_FIELDS, an allowlist -- so ask the real question before you
    # wire it: is `reason` safe to export? It quotes permission errors and guardrail findings.
    # find_secrets() returns pattern NAMES and never the secret (Day 12), so the input layer is
    # fine; `names other customers: ['4471']` is a customer id in a trace file. Decide, then
    # widen the allowlist deliberately or redact in audit_lines(). Deciding is the rep.


if __name__ == "__main__":
    main()
```

**Line by line:**

- The module docstring leads with **"Costs ZERO model requests"** because that is the finding, not a
  footnote. Every refusal in Mandala is now decided by data structures, which is why the whole
  permission story can be re-run on every commit. Compare Day 18, where half the request budget went
  on *demonstrating* the naive path.
- `APPROVE` / `DECLINE` as one-line lambdas — deterministic humans, so the battery is reproducible
  and needs nobody at a keyboard. The interactive version is Day 16's `console_approver`; run the
  demo once with `approver=console_approver` after the table works, because **a gate you have never
  personally been stopped by is a gate you do not understand.**
- `RESOLVER` and `RESEARCHER` differ only in `actor`, and every identity comes from the context —
  never from the action, never from a prompt (Day 12, Day 15). The model cannot influence which row
  of Day 8's table it is measured against.
- Case 3 is the one to look at hardest: a `post_reply` attempted by the **Researcher**. It is refused
  at layer 1 by a `frozenset` lookup, **before a single regex runs and before anyone is asked
  anything**. This is the concrete form of the day's thesis, and note that it is also the *most
  dangerous* attempted action in the battery — an agent that reads the open web (Day 15) trying to
  write to a customer. **The cheapest layer catches the worst case**, which is not a coincidence:
  structural checks catch structural problems, and privilege escalation is structural.
- Case 5 uses `replace(RESOLVER, approver=APPROVE)` — `MandalaContext` is frozen (Day 12), so a
  variant is a new object rather than a mutation. Cases cannot leak into each other.
- Case 6 passes `audit_all=True` and is the only row that does. In production the run stops at layer
  1; audit mode keeps going so you can see that the input guardrail **would also** have refused, and
  that approval was `skipped` rather than asked. **Two independent reasons to refuse is a good sign,
  not a redundant one** — defence in depth means the second layer holds when the first is
  misconfigured.
- Case 7 sets `customer_id="1001"` and an output naming customer 4471, with an approver that says
  yes. The human approves and the output guardrail refuses anyway. **You spent the expensive thing
  and the cheap thing still said no.** That is §3.2's uncomfortable case, and the honest reading is
  that the ordering rule is about *not wasting* human attention, not about *guaranteeing* it is the
  last word.
- `humans = sum(... .asked_a_human ...)` — the day's metric, printed. Seven actions, and if your
  policy is right the humans-asked count is **2** (cases 4 and 5). Everything else was decided for
  free. Write that ratio in the CHECKLIST; it is the sentence you will say out loud.
- The trailing `TODO(me)` is a genuine question and not a chore: Day 14's `SAFE_SPAN_FIELDS` is an
  allowlist, and today's `reason` strings sometimes contain a customer id. **An audit trail that
  leaks the thing it was auditing is a new incident.** Decide, then widen deliberately or redact.

### 3.10 What you should see

```
case                                  actor       layers run                                  refused by        cost
-------------------------------------------------------------------------------------------------------------------
1 clean draft                         resolver    permission,guardrail:input,approval,guar... -- allowed --     ms
2 draft, secret in input              resolver    permission,guardrail:input                  guardrail:input   ms
3 write by an agent that lacks it     researcher  permission                                  permission        free
4 write, approvals on, human declines resolver    permission,guardrail:input,approval         approval          human
5 write, human approves               resolver    permission,guardrail:input,approval,guar... -- allowed --     human
6 refused by TWO layers (audit mode)  researcher  permission,guardrail:input,approval,guar... permission        free
7 approved, then output refuses       resolver    permission,guardrail:input,approval,guar... guardrail:output  human

actions evaluated: 7   humans asked: 2
```

**Read the `layers run` column, not just the verdict.** Row 3 ran **one** layer. Row 2 ran two. Rows
4 and 5 ran three and four, and only those two spent a person. That column is the proof that the
ordering is real rather than aspirational — and it is the difference between a system that asks for
approval seven times and one that asks twice.

Row 6 is worth staring at: in audit mode every layer reports, `approval` says `skipped`, and
`refused_by` is still `permission` because it was **first**, which here means **cheapest**.


### 3.11 Approval fatigue — the honest failure mode 🎯

A permission story has one characteristic way of failing, and it is not "the gate did not fire". It
is this:

> **A gate that fires on everything gets clicked through, and a gate that gets clicked through is
> worse than no gate at all — because it manufactures a record of human oversight that did not
> happen.**

Worse than no gate for two specific reasons, and you should be able to give both. First, the audit
log now says *approved by alice@* on an action nobody read, so the one artifact you would use to
investigate an incident is actively lying to you. Second, it launders responsibility: everyone
downstream — the reviewer, the auditor, the person who signed off the architecture — reasonably
believes a human considered this, and none of them did.

Four things you do about it, in the order they help:

1. **Gate on consequence, not on action count.** `NEEDS_APPROVAL` is derived from
   `TOOLS[...].writes` (§3.5), which came from Day 8's blast-radius review. Reads are never gated.
   If your gate fires on `get_ticket`, you have not built oversight, you have built a captcha.
2. **Batch what is one consequence.** Eight replies on one ticket in one request is **one** decision
   for a human, not eight. That is what `group_for_approval` is for, and why choosing its key is the
   rep: the key you pick is your policy on how much risk a single "yes" may cover.
3. **Make the diff readable.** Day 16's `console_approver` rule — print the tool name **and** the
   arguments — is the whole of this. `Approve post_reply? [y/N]` teaches people to type `y`. Showing
   the exact 200 characters that will reach a customer teaches them to read.
4. **Measure it.** `DecisionTrace.asked_a_human` exists so the ratio is a number you can watch. A
   rising approvals-per-request curve is the leading indicator; the lagging indicator is somebody
   holding down the return key.

And the thing you do *not* do: relax the gate because it is annoying. If it is annoying, either the
gate is on the wrong thing (fix 1), or the unit is wrong (fix 2), or the agent is genuinely not
ready for the autonomy you want to hand it — which is real information, and exactly what **Phase
13's graduated-autonomy review** exists to weigh. Principle 12 says humans gate writes *until* that
review; it does not say forever, and it does not say the review is a rubber stamp. The evidence you
carry into it is this trace: how often the gate fired, how often a human said no, and what they
caught. **An approval gate that has never once been declined is not evidence of safety; it is
evidence you have not learned anything from it yet.**

---

## §4 OAI-25 🅿️ — AgentKit and the platform layer

No lab today. This is a **literacy row**: the zero-budget addendum's Part 5 is explicit that
visual/no-code builders (Agent Builder, Crew Studio, Fleet) are literacy rows only, because *"this
plan is code-first"*. You still have to talk about it fairly, in both directions.

### 4.1 What is in the box

**AgentKit** is OpenAI's managed layer *around* the Agents SDK you have used for thirteen days.
Three pieces worth knowing by name:

- **Agent Builder** — a visual canvas for composing agents, tools and handoffs. The nodes are
  concepts you already know: an agent, a guardrail, a handoff, a tool.
- **ChatKit** — an embeddable chat UI: streaming, tool-call display, threads, attachments. It is the
  front end for Day 17's streaming work, that you did not have to write.
- **Connector registry** — a managed catalogue of connections to third-party systems (drives, ticket
  systems, wikis) with auth handled centrally instead of per-integration.

### 4.2 What it buys and what it locks

| | What it buys 🎁 | What it locks 🔒 |
|---|---|---|
| **UI** | A production chat surface — streaming, retries, attachments, mobile — you did not build and do not maintain. Day 17 took a day to get a progress reducer right; this is that, finished. | Your UX is theirs. A custom affordance — an approval rendered as a readable diff (§3.11) — exists only if they built one. |
| **Integrations** | Connectors you did not write, with auth you do not store. Genuinely weeks of work. | Their catalogue is your integration list; anything outside it is a custom build, so you now maintain two integration styles. |
| **Authoring** | A visual surface a non-engineer can edit — a support lead changes a prompt without a PR. A real organisational unlock, not a toy. | **Your agent definitions live in their console, not your git history.** No `git blame` on a prompt, no bisect on a behaviour change. |
| **Review** | Changes ship in minutes. | Review no longer goes through pull requests. Today's `LAYERS` tuple is reviewable because it is four lines in a repo; a layer order inside a console is reviewed by whoever has the tab open. |
| **Evals** | Built-in eval and trace views on the platform. | Evals are hard to run in CI — and Principle 7 says a behaviour is not done until a test can fail. A test that exists only in a dashboard cannot fail your build. |
| **Ops** | They run it, scale it, patch it. | Migration cost, unpriced. Exporting a visually-authored graph back into code is not a button. |
| **Cost** | Fast start. | Paid. This project has no key (Principle 5), so it is 🅿️ concept-only here. |

### 4.3 The third column on ADR-001's axis

ADR-001 (Day 16) drew one axis: **what the SDK owns vs. what I own.** The platform layer is not a
new axis — it is a **third column on the same one**: *what someone else runs.*

| | What I own | What the SDK owns | What the platform owns |
|---|---|---|---|
| Agent definition | a Python file, in git | the `Agent` class | a node on a canvas, in their database |
| Guardrails | `guardrails.py`, tested at 0 cost | the tripwire plumbing | a checkbox and their implementation |
| Approvals | today's `LAYERS`, four reviewable lines | `RunContextWrapper` | their approval UI, if they have one |
| Traces | `.mandala/traces/*.jsonl` | span types | their dashboard, their retention |

Reading down the last column gives you the real question, which is not "is no-code bad?" but:
**when this vendor's roadmap and mine disagree, which of these can I take with me?** Column one
comes with you. Column three does not.

### 4.4 When a team should genuinely reach for it

Be fair here, because the unfair version is easy and it is what everyone expects you to say.

A small team shipping an internal assistant, where the hard part is the *integrations and the UI*
rather than the agent logic, should probably use the managed layer and be glad. If your
differentiator is your triage taxonomy and not your streaming implementation, writing a chat client
from scratch is a way of feeling productive while shipping nothing. The connector registry alone can
be worth a month. And a visual surface that lets the support lead who actually understands the
domain edit the prompt beats a repo only three engineers can change.

The rule is: **price the exit before you take the entrance.** Adopt the platform layer when the
thing it owns is not the thing you are differentiating on — and before you adopt, write the one page
that says what a migration would cost: which definitions would live only in their console, what your
eval story becomes in CI, and who reviews a change. That page takes an afternoon beforehand and is
impossible to write honestly two years in.

### 4.5 What to be able to say

- The three pieces (Agent Builder, ChatKit, connector registry) and which SDK concept each wraps.
- **One genuine buy and one genuine lock, without flinching at either.** The strongest pairing:
  *"it buys me a chat UI and connectors I did not write; it locks my agent definitions out of git
  and my evals out of CI."*
- Why this plan treats it as literacy only — code-first, `$0`, and Principle 7's requirement that a
  test can fail *in CI*.
- The ADR-001 framing: **what I own, what the SDK owns, what someone else runs** — and that the last
  column is the one you cannot take with you.

---

## §5 The eval that must be able to fail

### `tests/test_resolver_policy.py`

Every test below costs **0 model requests**. That is not thrift, it is the design of §3.6 paying out:
the policy is a tuple, four pure functions and a callable, so the entire permission story of the
system is exercisable on every commit without touching a provider.

```python
"""Four layers, one order. These tests are why the order can be trusted."""

import pytest

from mandala.context import MandalaContext
from mandala.permissions import PermissionDenied, TOOLS, trifecta_violations
from mandala.resolver_policy import (
    LAYER_NAMES,
    NEEDS_APPROVAL,
    ApprovalRequired,
    AttemptedAction,
    DecisionTrace,
    PolicyRefused,
    approval_required,
    enforce,
    evaluate,
    group_for_approval,
)

SECRET = "sk-abcdefghijklmnopqrstuvwxyz012345"
YES = (lambda tool, args: True)
NO = (lambda tool, args: False)


def resolver(**kw) -> MandalaContext:
    return MandalaContext(actor="agent:resolver", request_id="req-t", **kw)


def researcher(**kw) -> MandalaContext:
    return MandalaContext(actor="agent:researcher", request_id="req-t", **kw)


class Spy:
    """An approver that records whether a human was ever asked."""

    def __init__(self, answer: bool) -> None:
        self.answer, self.calls = answer, []

    def __call__(self, tool, args) -> bool:
        self.calls.append(tool)
        return self.answer


# --- one test per layer: each refuses exactly what it is for -----------------------
def test_the_permission_layer_refuses_what_the_table_never_granted():
    """Day 8. The researcher has never held post_reply and never will."""
    trace = evaluate(AttemptedAction("post_reply"), context=researcher())
    assert trace.refused_by == "permission"


def test_the_input_guardrail_layer_refuses_a_secret():
    """Day 12's find_secrets, at a second attachment point."""
    action = AttemptedAction("draft_reply", input_text=f"my key is {SECRET}")
    assert evaluate(action, context=resolver()).refused_by == "guardrail:input"


def test_the_approval_layer_refuses_when_the_human_says_no():
    trace = evaluate(AttemptedAction("post_reply"), context=resolver(approver=NO))
    assert trace.refused_by == "approval"


def test_the_output_guardrail_layer_refuses_another_customers_name():
    """Day 12's mirror: a secret can arrive as data and leave as an answer."""
    action = AttemptedAction("post_reply", output_text="as customer 4471 told us")
    context = resolver(approver=YES, customer_id="1001")
    assert evaluate(action, context=context).refused_by == "guardrail:output"
```

```python
# --- the order, asserted rather than intended --------------------------------------
def test_the_layers_are_declared_in_cost_order():
    """A change-detector, on purpose. Reordering LAYERS is a policy change."""
    assert LAYER_NAMES == ("permission", "guardrail:input", "approval", "guardrail:output")


def test_a_clean_action_runs_every_layer_in_that_exact_order():
    trace = evaluate(AttemptedAction("draft_reply", input_text="hi"), context=resolver())
    assert trace.layers_run == list(LAYER_NAMES)
    assert trace.allowed


def test_no_human_is_asked_after_a_cheaper_layer_refuses():
    """THE THESIS, asserted. Layer 1 says no; the approver is never called."""
    spy = Spy(True)
    trace = evaluate(AttemptedAction("post_reply"), context=researcher(approver=spy))
    assert trace.refused_by == "permission"
    assert spy.calls == [], "a human was asked about an action already refused for free"
    assert trace.asked_a_human is False


def test_audit_mode_reports_every_layer_and_still_never_asks_a_human():
    spy = Spy(True)
    action = AttemptedAction("post_reply", input_text=f"key {SECRET}")
    trace = evaluate(action, context=researcher(approver=spy), audit_all=True)
    assert trace.layers_run == list(LAYER_NAMES)
    assert {d.layer for d in trace.decisions if d.verdict == "refuse"} == {
        "permission", "guardrail:input",
    }
    assert spy.calls == []


def test_a_human_is_never_asked_before_the_permission_check():
    """FLIP IT: swap 'permission' and 'approval' in LAYERS and watch this go red.

    Reorder the tuple so approval comes first, re-run, and the spy records a call
    for an action the permission table was always going to refuse. That red is the
    whole day: it is what spending a person's attention on a frozenset lookup looks
    like in a test. Put the tuple back.
    """
    spy = Spy(True)
    evaluate(AttemptedAction("post_reply"), context=researcher(approver=spy))
    assert spy.calls == []


# --- approvals: the default is the safe value (fourth time) ------------------------
def test_a_write_with_approvals_required_and_no_approver_raises():
    """Days 12, 13, 15 and now 21. Forgetting must be safe."""
    with pytest.raises(ApprovalRequired):
        enforce(AttemptedAction("post_reply"), context=resolver())


def test_an_approved_write_proceeds():
    trace = enforce(AttemptedAction("post_reply"), context=resolver(approver=YES))
    assert trace.allowed
    assert trace.asked_a_human is True


def test_the_context_switch_can_tighten_approval_but_never_loosen_it():
    """AgentSpec.requires_approval_for_writes is policy; the context is a switch."""
    context = resolver(approvals_required=False, approver=NO)
    assert approval_required(AttemptedAction("post_reply"), context) is True
    assert evaluate(AttemptedAction("post_reply"), context=context).refused_by == "approval"


def test_reads_are_never_gated():
    """Fatigue prevention, as an assertion: a gate on get_ticket is a captcha."""
    assert approval_required(AttemptedAction("get_ticket"), resolver()) is False


def test_needs_approval_is_derived_from_the_permission_table():
    assert NEEDS_APPROVAL == frozenset(n for n, s in TOOLS.items() if s.writes)
    assert "post_reply" in NEEDS_APPROVAL and "get_ticket" not in NEEDS_APPROVAL
```

```python
# --- the trace is the artifact -----------------------------------------------------
def test_the_decision_trace_records_which_layer_fired_and_why():
    trace = evaluate(AttemptedAction("post_reply"), context=researcher())
    refusal = next(d for d in trace.decisions if d.verdict == "refuse")
    assert refusal.layer == "permission"
    assert refusal.cost == "free"
    assert "post_reply" in refusal.reason


def test_the_trace_produces_greppable_audit_lines():
    """Day 12's audit format, so today's refusals grep beside everything else."""
    context = researcher()
    lines = evaluate(AttemptedAction("post_reply"), context=context).audit_lines(context)
    assert lines and all("req-t" in line and "policy." in line for line in lines)


def test_a_refusal_carries_its_own_trace():
    with pytest.raises(PolicyRefused) as exc:
        enforce(AttemptedAction("post_reply"), context=researcher())
    assert isinstance(exc.value.trace, DecisionTrace)
    assert exc.value.trace.refused_by == "permission"


def test_policy_refused_is_a_permission_denied():
    """So Day 10's tool_error re-raise already stops the run. No new escape hatch."""
    assert issubclass(PolicyRefused, PermissionDenied)
    assert issubclass(ApprovalRequired, PolicyRefused)


# --- the invariant, re-asserted on a day capability became reachable ---------------
def test_trifecta_violations_is_still_empty():
    """Twenty-one days running (Day 8). Re-assert it exactly when reach grows."""
    assert trifecta_violations() == []


# --- the reps ----------------------------------------------------------------------
def test_two_writes_to_one_ticket_are_one_approval():
    """Red until group_for_approval() is written (§3.11's fix 2)."""
    same = [AttemptedAction("post_reply", {"ticket_id": "T-1001", "text": t}) for t in "ab"]
    other = AttemptedAction("post_reply", {"ticket_id": "T-1004", "text": "c"})
    groups = group_for_approval([*same, other])
    assert len(groups) == 2
    assert sorted(len(v) for v in groups.values()) == [1, 2]


def test_the_policy_layer_and_the_attached_guardrail_agree():
    """TODO(me): make this real, because 'one predicate, two wrappers' is a CLAIM.

    §3.7 calls find_secrets() directly rather than invoking Day 12's decorated
    guardrail object, so nothing stops the two drifting. Drive BOTH paths with the
    same inputs -- a clean string, a string with a key, a string at MAX_INPUT_CHARS+1
    -- and assert they reach the same verdict. Working out how to invoke a decorated
    guardrail outside a run (see §8) is most of the rep; the assertion is three lines.
    """
    from mandala.guardrails import find_secrets
    assert bool(find_secrets(SECRET)) is True          # placeholder: one half only
```

**Line by line:**

- **One test per layer, four tests, and each one names the day it came from.** That structure is the
  point: if `test_the_input_guardrail_layer_refuses_a_secret` goes red, you know Day 12 broke, not
  Day 21. Composition tests that only assert "something refused" tell you a system is broken without
  telling you which part.
- `test_the_layers_are_declared_in_cost_order` is a **change-detector, deliberately** — the same call
  Day 18 made for `OPERATIONS`. Normally you avoid these. Here going red *is the feature*: reordering
  `LAYERS` changes what Mandala spends a human on, and that should never sail through CI silently.
- `test_a_clean_action_runs_every_layer_in_that_exact_order` asserts `layers_run == list(LAYER_NAMES)`
  — the order is **observed from a real evaluation**, not just read off the constant. The pair of
  tests is deliberate: one pins the declaration, one pins the behaviour, and a bug that changes only
  one of them is exactly the bug you want caught.
- `test_no_human_is_asked_after_a_cheaper_layer_refuses` is **the thesis as an assertion**, and the
  `Spy` class exists only for it. Note it asserts the *negative* — `spy.calls == []` — which is the
  hard kind to remember to write and the only kind that can catch "we ask, then discard the answer".
- `test_audit_mode_reports_every_layer_and_still_never_asks_a_human` guards the feature most likely
  to grow a hole: a policy-review mode that pings on-call for every historical action would be a
  spectacular own goal, so the spy runs there too.
- `test_a_human_is_never_asked_before_the_permission_check` is **the flip-it test.** Swap two entries
  in `LAYERS`, re-run, and watch it go red — then put the tuple back. It is a near-duplicate of the
  test above it on purpose: one documents the property, one documents the *experiment*, and the
  docstring is the instruction.
- `test_a_write_with_approvals_required_and_no_approver_raises` — **the fourth time** this curriculum
  has asserted that the safe value is the default (Day 12's `approvals_required=True`, Day 13's
  `filtered=True`, Day 15's default-deny search envelope, today's `approver=None`). Four is where it
  stops being a habit and becomes a property of the codebase you can claim out loud.
- `test_the_context_switch_can_tighten_approval_but_never_loosen_it` is the one-character-bug test:
  it constructs the context someone will eventually write to speed up a test suite
  (`approvals_required=False`) and proves the write is still gated. If `approval_required` used `and`
  instead of `or`, everything else in this file would still pass.
- `test_reads_are_never_gated` turns §3.11's fix 1 into an assertion — **when a design sentence can
  become a test, make it one** (Day 15's rule, restated).
- `test_the_decision_trace_records_which_layer_fired_and_why` asserts on `.cost` as well as `.layer`,
  which is what stops `cost` quietly becoming a settable field later.
- `test_policy_refused_is_a_permission_denied` is two `issubclass` lines and it protects a piece of
  behaviour three files away: Day 10's `tool_error` re-raise. **An inheritance relationship that
  load-bearing deserves a test, because a future refactor "cleaning up" the exception hierarchy would
  otherwise turn every refusal into text the model can argue with.**
- `test_trifecta_violations_is_still_empty` — re-asserted today because today is the day a `writes=True`
  tool became reachable for the first time. **Invariants are worth re-asserting exactly when reach
  grows**, same as Day 15 and Day 18.
- `test_two_writes_to_one_ticket_are_one_approval` ships **red** until `group_for_approval` is
  written, and it asserts only the relationship — two groups, sizes 1 and 2 — not the key you chose.
  A test that hard-coded `"T-1001"` as the key would forbid you from deciding the key is the customer
  or the request.
- `test_the_policy_layer_and_the_attached_guardrail_agree` is the fourth `TODO(me)` and it ships as a
  placeholder that passes, which is the worst kind of test — **so it is labelled.** The gap between
  what it asserts and what its name promises is the rep; noticing that gap is a skill this project
  keeps asking for (Day 18 left the same trap on purpose).
- **All of it costs 0 model requests.** Say that in the interview: the entire permission story of a
  multi-agent system, exercisable on every commit, on a free tier, in under a second.

---

## §6 Traps

- **A gate that fires on everything.** It gets clicked through, and then your audit log records human
  oversight that did not happen — a false record is worse than a missing one.
  **🎯 The trap of the day.** It arrives disguised as thoroughness, and the tell is an approvals
  count that rises with traffic instead of with consequence.
- **Asking a human before checking the permission table.** A `frozenset` lookup costs nothing; a
  person costs the scarcest thing in the system. Any ordering that spends the second to learn what
  the first already knew is indefensible, and it is the flip-it test in §5.
- **Letting a guardrail do a permission's job.** A regex that tries to detect "the Researcher is
  posting a reply" is a heuristic standing where a table belongs. Heuristics have false negatives;
  structure does not.
- **Letting a permission do a guardrail's job.** The opposite error: you cannot enumerate every
  wrong-looking input in a table, and trying produces a table nobody will review.
- **Two approval mechanisms.** Day 16's `ApprovalGate` and a new one in the policy layer would mean
  two places a human can be asked and no single place that proves they were. One approver callable,
  two attachment points (§3.5).
- **Hand-maintaining the list of tools that need approval.** `NEEDS_APPROVAL` must be derived from
  `TOOLS[...].writes`. A hand-written frozenset is a second source of truth about which tools write,
  and it drifts silently on the day someone adds one.
- **`and` where §3.7 has `or`.** `approval_required` must let the runtime switch *tighten* and never
  *loosen* the table. One character, and the Resolver's write gate is disarmed by any caller who
  passes `approvals_required=False` to make a test faster.
- **Making `PolicyRefused` a plain `RuntimeError`.** Day 10's `tool_error` re-raises
  `PermissionDenied` and converts everything else to text. Break the inheritance and every refusal
  becomes a sentence the model reads and routes around.
- **Evaluating with an empty `output_text` and calling the output layer checked.** An empty string
  passes every output guardrail. Re-evaluate once the answer exists, or you have four layers of
  which one is decorative.
- **Approving once and replaying forever.** A retried write must be re-checked, not waved through
  because it carries an old approval. Day 20's retries are why `enforce` runs *before* the
  idempotency comparison in `post_reply_gated`, not after.
- **Putting the refusal `reason` into a trace without reading it.** Day 14's `SAFE_SPAN_FIELDS` is an
  allowlist for a reason, and `names other customers: ['4471']` is a customer id. An audit trail that
  leaks what it audits is a new incident (the demo's `TODO(me)`).
- **`OUTBOX` as a module constant while `tickets_path` is injected.** Fine in a lab, wrong the moment
  there are two environments, and the kind of asymmetry that becomes a production bug six months out.
- **Treating AgentKit as a values question.** "No-code is bad" is not an answer. The answer is a
  priced comparison: what it buys, what it locks, and what a migration costs (§4.2).

---

## §7 Request budget

| Activity | Model requests | Notes |
|---|---|---|
| `policy_demo.py` — the whole seven-case battery | **0** | a frozenset, six regexes, a callable |
| Every test in `tests/test_resolver_policy.py` | **0** | no `make_model()` anywhere in the module |
| Re-running Day 8 / 12 / 16 suites as prerequisites | **0** | they were free on their own days too |
| Writing `worst_cost` and `group_for_approval` | **0** | pure functions |
| One end-to-end Resolver run, approved, to the outbox | ~3 (Groq) | prove the gate works inside a real run |
| One end-to-end run where the input guardrail trips | **0** | the tripwire fires *before* the model is called |
| Prompt iteration so the Resolver stops arguing with a refusal | ~6 (Groq) | budget for it; the first attempt talks back |
| **Total** | **≈ 9, Groq** | log it in `docs/RATE_BUDGET.md` |

**Nine requests for the day that composes the entire permission story — and that is a design
achievement, not a shortcut.** It is the direct consequence of two decisions: §3.6 keeps `Agent` and
`make_model()` out of `resolver_policy.py`, and §3.7 separates `evaluate` (decide) from `enforce`
(act). Together they mean every refusal path is reachable without a provider.

Notice the second-cheapest row and what it teaches: **a tripped input guardrail costs 0 requests**,
because the tripwire fires before the model is ever called. Day 12 made that argument
(*"a guardrail must be cheaper than the run it protects"*); today it shows up as a literal zero in a
budget table. On a free tier, where rate limits are the currency (Principle 5), a check that refuses
before spending is not just safe — it is the cheapest thing in the system.

If your Groq ceiling is tight, drop the prompt-iteration row and run the end-to-end once. **Do not
drop the battery** — it costs nothing and it is the day's artifact.

---

## §8 Verify before you code

Written **2026-08-20** against `openai-agents` **0.22.0**. **Two things today cannot be run here** —
`allowed_callers` (§3.4) and AgentKit (§4) both need a paid key, so their shape must be **read**, not
tested. Read them carefully and quote them accurately; a 🅿️ claim you got from memory is the one that
embarrasses you in an interview.

- `https://openai.github.io/openai-agents-python/guardrails/` — input and output guardrails. **Confirm
  in 0.22.0** that `GuardrailFunctionOutput(output_info=..., tripwire_triggered=...)` and the
  `InputGuardrailTripwireTriggered` / `OutputGuardrailTripwireTriggered` exception names are
  unchanged since Day 12. Also confirm the claim §7 makes money on: **input guardrails run before the
  first model call**, so a tripped one really does cost 0 requests.
- `https://openai.github.io/openai-agents-python/ref/guardrail/` — **the §5 `TODO(me)` lives here.**
  Find out how to invoke a decorated guardrail object directly (the callable the decorator wrapped,
  and its exact attribute name) so the policy layer and the attached guardrail can be tested against
  each other instead of trusting that they agree.
- `https://openai.github.io/openai-agents-python/tools/` and
  `https://openai.github.io/openai-agents-python/mcp/` — **the important freshness item today.**
  Recent Agents SDK lines have grown *native* human-in-the-loop support for tool calls — approval
  requests surfaced as run interruptions rather than raised exceptions. **Confirm whether 0.22.0
  exposes an approval hook on `function_tool` or only on hosted/MCP tools.** If it does, today's
  hand-rolled `enforce()` should eventually re-point at it, and that is a **Part-4 matrix fact**:
  one line in `docs/CHANGELOG_PLAN.md` today, an amendment before the next approvals day (AG-20,
  Day 50). **Do not silently adapt** (Principle 14).
- `https://openai.github.io/openai-agents-python/ref/tool/` — **confirm in 0.22.0** that
  `function_tool` still takes `name_override` and `failure_error_function` (unchanged since Day 10),
  since `post_reply_gated` depends on both.
- `https://platform.openai.com/docs/api-reference/responses/create` — `allowed_callers` 🅿️: which
  object it attaches to, the legal values, and **what omitting it means**. If omission is
  "any caller", write that down — a default-open permission field is the exact opposite of
  `approvals_required=True`, and the contrast is worth a sentence in §9.
- `https://openai.com/agentkit/` plus the Agent Builder, ChatKit and connectors guides on
  `https://platform.openai.com/docs/` — 🅿️, read-only. Confirm the three component names in §4.1 are
  still the current ones; product surfaces get renamed (the plan itself notes LangSmith's Agent
  Builder became Fleet). **A renamed product in an interview answer reads as second-hand knowledge.**
- **Confirm in 0.22.0** that `RunContextWrapper[MandalaContext]` still exposes `.context` (Day 12) —
  `post_reply_gated` reads the approver off it.
- Anything that differs: one line in `docs/CHANGELOG_PLAN.md`, today, before you forget which version
  you believed.

---

## §9 Say it in an interview

> "Most systems have several ways to say no and no order between them, which is how you end up both
> unsafe and annoying. I gave mine three kinds and one order. A **guardrail** is a cheap heuristic
> over text and it runs in-process. A **permission** is a structural fact — this agent may not hold
> this tool, ever — and it is a set lookup against a table I reviewed. An **approval** is authority:
> a human owning a consequence, and it is the only check that costs something irreplaceable. So the
> rule is **cheap checks run first, humans last** — I never spend a person's attention on something
> a `frozenset` could have refused. The proof is a battery of seven attempted actions that prints
> which layer stopped each one: a write attempted by an agent that lacks the permission is refused by
> the free layer, before any regex runs and before anybody is asked anything. Seven actions, two
> humans asked. And the whole thing costs zero model requests to test, because the policy is a tuple
> and four pure functions — so the entire permission story runs on every commit."

> "The failure mode I care about is **approval fatigue**. A gate that fires on everything gets
> clicked through, and that is *worse* than no gate, because now the audit log claims a human
> reviewed something nobody read — you have manufactured a false record of oversight and laundered
> the responsibility along with it. So I gate on consequence rather than action count: the list of
> tools needing approval is derived from the `writes` flag in my permission table, not hand-written,
> which means reads are never gated and a new write tool is gated before anyone remembers to. I batch
> what is really one consequence, I make the approver print the exact text that will be sent, and I
> track the ratio of actions evaluated to humans asked as a leading indicator. The related thing I'd
> say about the managed platform layer — AgentKit — is the same shape of argument: it genuinely buys
> you a chat UI and connectors you did not write, and it locks your agent definitions out of git and
> your evals out of CI. My layer order was reviewable because it was four lines in a repo. In a
> console, it is reviewable by whoever has the tab open."

---

## §10 Done when

```bash
./m check
./m done 21
```

- The battery prints seven rows, and you can name the layer that stopped each one **and its cost**.
- `worst_cost` and `group_for_approval` are written, and you can defend both judgement calls.
- The flip-it test has been run red — swap `permission` and `approval` in `LAYERS`, watch a human get
  asked about an action that was never going to be allowed, then put the tuple back.
- Every test in `tests/test_resolver_policy.py` is green at **0 model requests**, and
  `trifecta_violations()` is still `[]` on the day a `writes=True` tool became reachable.

**Tomorrow is the Phase-3 gate**, and it is a whole day, not a formality: a long-horizon,
file-touching agent running on free models inside the Day-19 Docker sandbox, plus the written
harness/sandbox explainer. Two things to check tonight so tomorrow is not spent on setup:

1. **Docker Desktop is running** and `days/day-19`'s sandbox tests pass. A gate day that starts with
   a container that will not start is a gate day you lose.
2. **`docs/explainers/paid-harness-and-sandbox.md` is finished** — you drafted it on Day 19 and the
   gate requires it: *"a one-page written explainer of the paid harness/sandbox good enough to give
   in an interview."* Read it out loud once. If any sentence is one you could not defend, fix it
   tonight while today's honesty about 🅿️ features is still fresh — you have now written two of them
   (Day 18's `allowed_callers`, today's AgentKit), and the same standard applies: name what it buys,
   name what it locks, and say precisely why you cannot run it.
