---
day: 13
phase: 2
phase_name: "OpenAI Agents SDK core"
title: "Handoffs vs. agents-as-tools"
ids: ["OAI-09", "OAI-10"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 13 — Handoffs vs. agents-as-tools

**Phase 2 · OpenAI Agents SDK core** · IDs: **OAI-09 🛠️**, **OAI-10 🛠️**

> **Yesterday:** context injection and guardrails — identity the model cannot forge, checks that cost
> nothing.
> **Today:** the two ways one agent involves another, and the single question that tells you which to
> use. Plus the parameter that turns a handoff into a security boundary.
> **Tomorrow:** topologies and tracing.

```bash
./m start 13
./m scaffold 13
```

---

## §1 The story

Two agents need to work together. The SDK gives you two mechanisms, and people pick between them by
feel, which is why their systems end up strange.

Here is the question that decides it:

> **After the second agent finishes, does the first agent still have something to do?**

- **Yes** → **agent-as-tool.** The second agent runs, returns a value, and the first agent carries
  on with that value in hand. Delegate-and-return. The conversation never leaves the first agent.
- **No** → **handoff.** Control *transfers*. The second agent takes over the conversation and its
  answer becomes the answer. The first agent is finished.

That is it. Everything else follows.

Think of it as the difference between **asking a colleague a question** and **transferring the phone
call**. If you need their answer to finish your own work, you ask them — that is a tool call. If they
are simply the right person to handle this customer, you transfer the call and go do something else
— that is a handoff.

And now the part that makes today matter more than it looks.

On Day 8 you established Mandala's security shape: the Researcher reads untrusted ticket text and
holds no write tools; the Resolver can write and **never sees the raw ticket**. When you implement
that with a handoff, there is a real danger — **by default, a handoff carries the whole conversation
history to the receiving agent.** Which means the Resolver would receive every raw ticket body the
Researcher ever read, and your Day-8 separation would be silently undone by a default.

The fix is one parameter: `input_filter`. Today you learn what it is *for*, not just that it exists.

---

## §2 Setup — run this

No new packages.

```bash
mkdir -p days/day-13/lab
touch src/mandala/handoffs.py
touch days/day-13/lab/handoff_demo.py
touch days/day-13/lab/as_tool_demo.py
touch days/day-13/lab/leak_check.py
touch tests/test_handoffs.py
```

---

## §3 OAI-09 — Handoffs

### 3.1 How it works underneath

A handoff is **a tool call in disguise**. The SDK gives the parent agent a synthetic tool — named
something like `transfer_to_billing_agent` — and when the model calls it, the Runner switches which
agent is driving the loop.

Everything you learned on Day 3 still applies: it is a tool, so it has a name and a description, and
**that description is a prompt**. A vague handoff description means bad routing, exactly as a vague
tool description meant bad tool choice.

### 3.2 The parameters, and what each is really for

```python
handoff(
    agent=billing_agent,
    tool_name_override="escalate_to_billing",
    tool_description_override="Transfer when the ticket is about charges, invoices or refunds.",
    on_handoff=log_the_transfer,
    input_type=HandoffReason,
    input_filter=handoff_filters.remove_all_tools,
    is_enabled=True,
)
```

| Parameter | What it is really for |
|---|---|
| `tool_name_override` | routing quality — a clear verb beats `transfer_to_agent_2` |
| `tool_description_override` | **routing quality — this is the prompt.** Say when *not* to transfer |
| `on_handoff` | your audit hook: log it, count it, fire a side effect |
| `input_type` | force the model to *state a reason*, validated by Pydantic |
| **`input_filter`** | **what the receiving agent is allowed to see. This is the security control.** |
| `is_enabled` | runtime gating — e.g. disable escalation outside business hours |

### 3.3 `src/mandala/handoffs.py`

```python
"""Mandala's handoffs — with the input filter that keeps Day 8's separation intact.

The danger
----------
By default a handoff passes the whole conversation to the receiving agent. For
Mandala that would hand the Resolver every raw ticket body the Researcher read,
silently re-assembling the lethal trifecta (Day 8, AG-16) via a DEFAULT.

So every handoff into a write-capable agent MUST specify an input_filter.
`assert_filtered()` below makes that a testable rule rather than a good intention.

Usage
-----
    >>> from mandala.handoffs import to_resolver
    >>> to_resolver.tool_name
    'hand_off_to_resolver'
"""

from __future__ import annotations

from typing import Literal

from agents import Agent, RunContextWrapper, handoff
from agents.extensions import handoff_filters
from pydantic import BaseModel, Field


class HandoffReason(BaseModel):
    """Force the model to say WHY it is transferring. Auditable, and it improves routing."""

    reason: Literal["billing", "auth", "data", "needs_human", "ready_to_reply"] = Field(
        description="The single best reason for this transfer."
    )
    summary: str = Field(
        max_length=300,
        description=(
            "One-sentence factual summary for the receiving agent. "
            "Summarise — do NOT quote the ticket body."
        ),
    )


async def on_transfer(ctx: RunContextWrapper, payload: HandoffReason) -> None:
    """Audit hook. Fires when the handoff is invoked, before the receiver runs."""
    context = getattr(ctx, "context", None)
    line = f"handoff reason={payload.reason} summary={payload.summary[:80]}"
    print(context.audit("handoff", line) if context else line)


def make_handoff(
    agent: Agent,
    *,
    name: str,
    description: str,
    filtered: bool = True,
):
    """Build a handoff. `filtered=True` strips tool history from what the receiver sees."""
    return handoff(
        agent=agent,
        tool_name_override=name,
        tool_description_override=description,
        on_handoff=on_transfer,
        input_type=HandoffReason,
        input_filter=handoff_filters.remove_all_tools if filtered else None,
    )


def assert_filtered(handoff_obj, receiver_may_write: bool) -> None:
    """A handoff into a write-capable agent must not carry raw tool output."""
    if receiver_may_write and getattr(handoff_obj, "input_filter", None) is None:
        raise ValueError(
            f"handoff {handoff_obj.tool_name!r} targets a write-capable agent with no "
            "input_filter — the receiver would see raw ticket text (Day 8, AG-16)"
        )
```

**Line by line:**

- `class HandoffReason(BaseModel)` — **`input_type` turns a handoff into a structured statement of
  intent.** Without it, a transfer is a silent jump; with it, the model must name a reason from a
  fixed list and write a summary. Two benefits: the audit log becomes meaningful, and the act of
  justifying the transfer measurably improves routing (same effect as Day 5's `thought` field).
- `reason: Literal[...]` — five fixed strings. A free-text reason is unanalysable; a `Literal` can be
  counted, and on Day 71 you will count them.
- `summary: str = Field(max_length=300, description="...do NOT quote the ticket body.")` — **a second
  layer of the same defence as `input_filter`.** The filter stops tool output mechanically; this
  discourages the model from smuggling raw text through the summary. Layers, not a wall (Day 7).
- `async def on_transfer(ctx, payload)` — the `on_handoff` callback receives the context wrapper and
  the validated `input_type` object. When `input_type` is set, the callback takes two arguments;
  without it, one. **Verify that signature in 0.22.0** — it is a common source of a confusing
  `TypeError`.
- `getattr(ctx, "context", None)` and the conditional — degrade gracefully when there is no
  `MandalaContext` (as in unit tests) rather than crashing the audit hook.
- `def make_handoff(agent, *, name, description, filtered=True)` — everything after `*` is
  keyword-only, so a call site cannot accidentally swap `name` and `description`.
- `filtered: bool = True` — **the safe value is the default.** Same principle as
  `approvals_required=True` yesterday: forgetting must be safe.
- `input_filter=handoff_filters.remove_all_tools if filtered else None` — the SDK's built-in filter
  strips tool calls and tool outputs from the history the receiver sees. **Since raw ticket bodies
  arrive as tool output, removing tool history is exactly what keeps them away from the Resolver.**
- `def assert_filtered(...)` — turns the rule into something a test can enforce. A convention only a
  human enforces is a convention that lapses on a busy Tuesday.

### 3.4 `days/day-13/lab/handoff_demo.py`

```python
"""Triage hands off to a specialist. Control transfers; the specialist finishes.

Run:
    uv run python days/day-13/lab/handoff_demo.py T-1003     # billing
    uv run python days/day-13/lab/handoff_demo.py T-1001     # auth
"""

from __future__ import annotations

import asyncio
import sys

from agents import Agent, Runner
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from mandala.context import MandalaContext
from mandala.handoffs import make_handoff
from mandala.sdk import DEFAULT_SETTINGS, make_model
from mandala.sdk_tools import get_ticket, search_tickets

billing = Agent(
    name="Billing",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are Mandala's billing specialist. You have been handed a ticket about "
        "charges, invoices or refunds. Give the customer a clear next step.\n"
        "Never promise a refund amount or a date. Say what will be checked and by whom."
    ),
    model=make_model("groq"),
    model_settings=DEFAULT_SETTINGS,
)

auth = Agent(
    name="Auth",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are Mandala's authentication specialist. Give the customer a clear next step "
        "for a login, SSO or access problem.\n"
        "Never ask the customer to send a password, token or key."
    ),
    model=make_model("groq"),
    model_settings=DEFAULT_SETTINGS,
)

triage = Agent(
    name="Triage",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are Mandala's triage agent. Read the ticket, then transfer it to the right "
        "specialist. Do not attempt to answer the customer yourself.\n"
        "If no specialist fits, answer briefly saying which team should look at it."
    ),
    model=make_model("groq"),
    model_settings=DEFAULT_SETTINGS,
    tools=[get_ticket, search_tickets],
    handoffs=[
        make_handoff(
            billing,
            name="hand_off_to_billing",
            description=(
                "Transfer when the ticket is about charges, invoices, refunds or plan pricing. "
                "Do NOT transfer here for login or access problems."
            ),
        ),
        make_handoff(
            auth,
            name="hand_off_to_auth",
            description=(
                "Transfer when the ticket is about login, SSO, sessions, permissions or access. "
                "Do NOT transfer here for billing questions, even urgent ones."
            ),
        ),
    ],
)


async def main() -> None:
    ticket_id = sys.argv[1] if len(sys.argv) > 1 else "T-1003"
    context = MandalaContext(actor="agent:triage", request_id=f"req-{ticket_id}")

    result = await Runner.run(triage, f"Handle ticket {ticket_id}.", context=context, max_turns=8)

    print(f"\nstarted with : Triage")
    print(f"finished with: {result.last_agent.name}")
    print(f"\n{result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- `RECOMMENDED_PROMPT_PREFIX` — the SDK ships a prompt fragment that explains handoffs to the model.
  **Read what it actually says** (`print(RECOMMENDED_PROMPT_PREFIX)`) — it is a worked example of
  prompt-as-interface (Day 6) written by the framework authors, and worth studying for that alone.
- Each handoff description contains a **"Do NOT transfer here for…"** clause. Day 3's negative-guidance
  lesson, now applied to routing. With two similar-sounding destinations, this is what stops the
  coin-flip.
- `"Do not attempt to answer the customer yourself"` in the triage instructions — without this, the
  model frequently answers *and* transfers, and you pay for both.
- `result.last_agent.name` — **this is why `last_agent` exists** (you noted it on Day 10). It prints
  `Billing`, not `Triage`. Control genuinely moved.
- `max_turns=8` — a handoff consumes turns in the parent's budget too. Handoff chains need more
  headroom than a single agent.

### 3.5 `days/day-13/lab/leak_check.py` — the security experiment

**Do not skip this.** It is the difference between knowing the parameter exists and knowing what it
is for.

```python
"""Prove that a handoff WITHOUT input_filter leaks raw ticket text to the receiver.

Budget: ~10 requests. Groq.

Run:
    uv run python days/day-13/lab/leak_check.py
"""

from __future__ import annotations

import asyncio

from agents import Agent, Runner

from mandala.context import MandalaContext
from mandala.handoffs import make_handoff
from mandala.sdk import DEFAULT_SETTINGS, make_model
from mandala.sdk_tools import get_ticket

CANARY = "PINEAPPLE-7731"       # a phrase that appears ONLY in the raw ticket body


def receiver() -> Agent:
    return Agent(
        name="Resolver",
        instructions=(
            "You have been handed a ticket. Before answering, list every distinct "
            "identifier or code word you can see anywhere in your context. Be exhaustive."
        ),
        model=make_model("groq"),
        model_settings=DEFAULT_SETTINGS,
    )


def sender(filtered: bool) -> Agent:
    return Agent(
        name="Researcher",
        instructions="Read the ticket, then hand off to the Resolver.",
        model=make_model("groq"),
        model_settings=DEFAULT_SETTINGS,
        tools=[get_ticket],
        handoffs=[
            make_handoff(
                receiver(),
                name="hand_off_to_resolver",
                description="Transfer once you have read the ticket.",
                filtered=filtered,
            )
        ],
    )


async def main() -> None:
    # T-9002 must exist in tests/fixtures/tickets.json with CANARY in its body.
    context = MandalaContext(actor="agent:researcher", request_id="req-leak")

    for filtered in (False, True):
        result = await Runner.run(
            sender(filtered), "Handle ticket T-9002.", context=context, max_turns=8
        )
        leaked = CANARY in result.final_output
        label = "filtered  " if filtered else "unfiltered"
        print(f"[{label}] canary visible to receiver: {leaked}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- `CANARY = "PINEAPPLE-7731"` — **a canary token.** A distinctive string that exists only in one
  place, so its appearance anywhere else is proof of a path. This is a genuinely useful technique;
  you will use it again on Day 65 to trace injection paths and on Day 69 for red-teaming.
- The receiver's instructions ask it to **enumerate everything it can see** — turning an invisible
  question ("what is in its context?") into visible output.
- `for filtered in (False, True)` — run both, print both. **A/B against yourself is how you turn a
  documentation claim into a fact you have observed.**
- Expected output:
  ```
  [unfiltered] canary visible to receiver: True
  [filtered  ] canary visible to receiver: False
  ```
  If both are `False`, your prompt did not make the receiver enumerate hard enough — strengthen it
  before concluding the filter was unnecessary. **A negative result you did not try hard to produce
  is not a negative result.**

**Add `T-9002` to your fixtures**, with the canary embedded in a realistic body, marked as a
handoff-leak test case.

---

## §4 OAI-10 — Agents as tools

### 4.1 The plain idea

`agent.as_tool(...)` turns an agent into a `FunctionTool`. The parent calls it like any other tool,
gets a value back, and **keeps the conversation**.

```python
research_tool = researcher.as_tool(
    tool_name="research_ticket",
    tool_description="Research a ticket and return a factual brief. Returns JSON.",
)
```

### 4.2 The comparison table — memorise this

| | **Handoff** | **Agent as tool** |
|---|---|---|
| Control after it runs | transferred — parent is done | returns — parent continues |
| Who produces the final answer | the receiver | the parent |
| What the callee sees | conversation history (**filtered by `input_filter`**) | only the arguments you passed |
| `result.last_agent` | the receiver | the parent |
| Can the parent call several? | one transfer, then it is over | **yes — several, even in parallel** |
| Natural topology (AG-11) | peer handoff | supervisor |
| Context isolation | needs `input_filter` | **isolated by construction** |

**Read that last row twice.** An agent-as-tool receives *only the arguments you chose to pass*. There
is no history to leak, because there is no history. For Mandala's Researcher → Resolver boundary,
that makes agent-as-tool the **structurally safer** choice, and the handoff the one that needs a
parameter to be safe.

Which does not make handoffs wrong — it makes them a different tool with a different failure mode,
and knowing which failure mode you have adopted is the job.

### 4.3 `days/day-13/lab/as_tool_demo.py`

```python
"""Researcher as a tool inside Triage. Triage keeps the conversation.

Run:
    uv run python days/day-13/lab/as_tool_demo.py T-1004
"""

from __future__ import annotations

import asyncio
import sys

from agents import Agent, Runner

from mandala.agents import Brief
from mandala.context import MandalaContext
from mandala.sdk import DEFAULT_SETTINGS, make_model
from mandala.sdk_tools import get_ticket, search_tickets

researcher = Agent(
    name="Researcher",
    instructions=(
        "Read the ticket and any similar tickets, then produce a factual brief. "
        "Summarise; never quote the ticket body verbatim. Cite ticket ids."
    ),
    model=make_model("groq"),
    model_settings=DEFAULT_SETTINGS,
    tools=[get_ticket, search_tickets],
    output_type=Brief,
)

research_ticket = researcher.as_tool(
    tool_name="research_ticket",
    tool_description=(
        "Research one ticket and return a structured brief with findings and a "
        "recommended action. Use this before drafting any reply."
    ),
)

triage = Agent(
    name="Triage",
    instructions=(
        "You own this conversation. Use research_ticket to gather facts, then decide "
        "what should happen next and say so in one short paragraph.\n"
        "You may call research_ticket more than once if the brief is insufficient.\n"
        "Never invent facts that are not in a brief."
    ),
    model=make_model("groq"),
    model_settings=DEFAULT_SETTINGS,
    tools=[research_ticket],
)


async def main() -> None:
    ticket_id = sys.argv[1] if len(sys.argv) > 1 else "T-1004"
    context = MandalaContext(actor="agent:triage", request_id=f"req-{ticket_id}")

    result = await Runner.run(triage, f"What should we do about {ticket_id}?",
                              context=context, max_turns=8)

    print(f"finished with: {result.last_agent.name}")     # Triage — control never left
    print(f"\n{result.final_output}")

    print("\n=== items ===")
    for item in result.new_items:
        print(f"  {type(item).__name__}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- `output_type=Brief` on the researcher — Day 8's schema, Day 11's mechanism. **The tool returns a
  typed brief, not prose**, so the parent receives something with a known shape. Compare with a
  handoff, where what crosses the boundary is conversation.
- `researcher.as_tool(tool_name=..., tool_description=...)` — the description is a prompt, again.
  *"Use this before drafting any reply"* tells the parent *when*.
- `"You may call research_ticket more than once"` — the capability handoffs do not have. This is the
  supervisor topology (AG-11) in three lines.
- `result.last_agent.name` prints **`Triage`** — contrast directly with `handoff_demo.py`, which
  printed `Billing`. **Run both back to back.** That one line of output is the whole distinction made
  concrete.
- The item-type loop — the sub-agent's run appears as a tool call and a tool output in the parent's
  transcript, not as a change of agent.

### 4.4 The decision, as a flowchart you can say out loud

```
Does the parent need the result to finish its own work?
├── yes → agent-as-tool
│         └── and the callee sees ONLY your arguments (safe by construction)
└── no  → handoff
          └── does the receiver have write tools?
              ├── yes → input_filter is MANDATORY (assert_filtered)
              └── no  → input_filter still recommended (context budget, Day 4)
```

---

## §5 The eval that must be able to fail

### `tests/test_handoffs.py`

```python
"""Handoff configuration and the separation it must preserve."""

import pytest

from mandala.handoffs import HandoffReason, assert_filtered, make_handoff


def test_handoff_reason_rejects_free_text():
    """A Literal reason can be counted on Day 71. Free text cannot."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        HandoffReason(reason="the customer seemed cross", summary="x")


def test_handoff_summary_is_length_capped():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        HandoffReason(reason="billing", summary="x" * 301)


def test_filtered_is_the_default(dummy_agent):
    h = make_handoff(dummy_agent, name="h", description="d")
    assert h.input_filter is not None, "the SAFE value must be the default"


def test_unfiltered_handoff_into_a_writer_is_rejected(dummy_agent):
    """assert_filtered turns a convention into an enforced rule."""
    unfiltered = make_handoff(dummy_agent, name="h", description="d", filtered=False)
    with pytest.raises(ValueError, match="input_filter"):
        assert_filtered(unfiltered, receiver_may_write=True)


def test_filtered_handoff_into_a_writer_is_accepted(dummy_agent):
    filtered = make_handoff(dummy_agent, name="h", description="d")
    assert_filtered(filtered, receiver_may_write=True)          # must not raise


def test_every_handoff_description_says_when_not_to_use_it():
    """Negative guidance is what stops a coin-flip between two similar destinations."""
    from handoff_demo import triage

    for h in triage.handoffs:
        description = getattr(h, "tool_description", "") or ""
        assert "do not" in description.lower(), f"{h.tool_name} has no negative guidance"


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_handoff_transfers_control():
    from agents import Runner
    from handoff_demo import triage

    result = await Runner.run(triage, "Handle ticket T-1003.", max_turns=8)
    assert result.last_agent.name != "Triage", "control did not transfer"


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_as_tool_keeps_control():
    from agents import Runner
    from as_tool_demo import triage

    result = await Runner.run(triage, "What should we do about T-1004?", max_turns=8)
    assert result.last_agent.name == "Triage", "control leaked to the sub-agent"


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_filtered_handoff_does_not_leak_the_canary():
    """The Day-8 separation, asserted rather than assumed."""
    from agents import Runner
    from leak_check import CANARY, sender

    result = await Runner.run(sender(filtered=True), "Handle ticket T-9002.", max_turns=8)
    assert CANARY not in result.final_output
```

**Line by line:**

- `dummy_agent` — a fixture you add to `tests/conftest.py` returning a minimal `Agent` with no tools.
  Keeps these tests free of model calls.
- `test_filtered_is_the_default` — asserts the **default is the safe one**. This is the test that
  catches a "simplification" that flips the default in six weeks.
- `test_every_handoff_description_says_when_not_to_use_it` — a **prose lint**, like Day 6's negative-
  instruction test. It enforces the routing-quality rule mechanically.
- `test_handoff_transfers_control` and `test_as_tool_keeps_control` — **the pair.** Together they
  assert the one distinction the whole day is about, from opposite directions. Either alone would
  pass with a broken implementation of the other.
- `test_filtered_handoff_does_not_leak_the_canary` — the security test, using the canary from §3.5.
  **This is the most valuable test today** and it is three lines.

---

## §6 Traps

- **Handing off into a write-capable agent with no `input_filter`.** Day 8's separation, undone by a
  default. This is the trap of the day.
- **`filtered=False` as a default anywhere.** The safe value is the default. Always.
- **Handoff descriptions with no "do NOT" clause.** Two similar destinations become a coin flip.
- **Forgetting `RECOMMENDED_PROMPT_PREFIX`.** The model routes noticeably worse without it.
- **Not telling triage "do not answer yourself".** It answers *and* transfers; you pay twice.
- **`max_turns` too low for a chain.** The handoff consumes turns from the same budget.
- **`on_handoff` signature mismatch.** With `input_type` it takes two arguments; without, one.
- **Using a handoff where you needed the result.** Control is gone and the parent never resumes.
- **Assuming agent-as-tool is always safer.** It is more isolated, but you also lose the receiver's
  ability to ask a follow-up question about the conversation. Different tool, different trade.
- **Concluding "no leak" from a weak probe.** Make the receiver enumerate hard before believing it.

---

## §7 Request budget

| Activity | Requests |
|---|---|
| `handoff_demo.py` × 2 tickets | ~10 (Groq) |
| `as_tool_demo.py` | ~6 (Groq) |
| `leak_check.py` — both branches | ~10 (Groq) |
| Cassettes + routing iteration | ~20 |
| **Total** | **≈ 46, Groq** |

The configuration tests cost **0** — because the security property lives in a data structure, which
is exactly why it was worth putting it there.

---

## §8 Verify before you code

Written **2026-08-20** against `openai-agents` **0.22.0**.

- `https://openai.github.io/openai-agents-python/handoffs/` — the `handoff()` signature, including
  `nest_handoff_history` (new-ish; read what it does, it interacts with `input_filter`).
- `https://openai.github.io/openai-agents-python/ref/extensions/handoff_filters/` — **what
  `remove_all_tools` actually removes.** Confirm it strips tool *outputs*, not just tool *calls* —
  the ticket body arrives as an output, so that distinction is the whole security property.
- `https://openai.github.io/openai-agents-python/ref/agent/#agents.agent.Agent.as_tool` —
  `as_tool` parameters: `parameters`, custom output extraction, approval gates, `is_enabled`.
- `print(RECOMMENDED_PROMPT_PREFIX)` — read it. It is a well-written prompt and you can learn from it.
- Confirm the `on_handoff` callback signature for both the with- and without-`input_type` cases.

---

## §9 Say it in an interview

> "The question I ask is: after the second agent finishes, does the first one still have work to do?
> If yes, it's an agent-as-tool — delegate and return, the parent keeps the conversation. If no, it's
> a handoff — control transfers and the receiver's answer is the answer. You can tell which you got
> by looking at `last_agent` on the result."

> "The thing that actually bit me was the default. A handoff carries the conversation to the
> receiving agent, so if you hand off from an agent that reads untrusted ticket text to one that can
> write externally, you've silently re-assembled the lethal trifecta — through a default, not a
> mistake. The fix is an `input_filter` that strips tool output. I proved it with a canary token in a
> ticket body: unfiltered, the receiver could see it; filtered, it couldn't. And I made
> 'unfiltered handoff into a write-capable agent' a `ValueError` in my own factory, so it's an
> enforced rule rather than something I have to remember at 6pm."

---

## §10 Done when

```bash
./m check
./m done 13
```

Tomorrow: assembling these into real topologies, and making the whole thing traceable without
OpenAI's dashboard.
