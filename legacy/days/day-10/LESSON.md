---
day: 10
phase: 2
phase_name: "OpenAI Agents SDK core"
title: "Tools and the Runner"
ids: ["OAI-03", "OAI-04"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 10 — Tools and the Runner

**Phase 2 · OpenAI Agents SDK core** · IDs: **OAI-03 🛠️**, **OAI-04 🛠️**

> **Yesterday:** the first `Agent`, running free on Groq, and you saw the Chat Completions request
> on the wire.
> **Today:** the two primitives you will use every single day — how a Python function becomes a
> tool, and exactly what `Runner` does with it. Including what happens when a tool raises.
> **Tomorrow:** structured output and sessions.

```bash
./m start 10
./m scaffold 10
```

---

## §1 The story

Yesterday you got a result. Today you get **control**, and control is mostly about failure.

Here is the question that separates a demo from a system: **what happens when a tool raises?**

On Day 3 you decided this yourself, and you decided well — you caught the exception and returned
`{"error": "..."}` so the model could see what went wrong and recover. You wrote three lines and
moved on.

The SDK made that same decision for you. It has a default error handler, and by default it does
something reasonable. But "reasonable by default" is precisely the kind of thing Principle 4 warns
about: a decision somebody else made, that you inherited, that they can change in a minor release.

So today you find out what the default actually is, then you replace it with one you chose.

There is a second, sharper reason to care. Consider a tool that raises `PermissionDenied` — Day 8's
security boundary. If the SDK's default handler catches it and feeds "an error occurred" back to the
model as an observation, then **your security boundary has become a hint**. The model reads it,
thinks "hmm, that didn't work", and tries something else. That is exactly the behaviour you do not
want from a permission check.

Some errors are observations. Some errors must stop the run. Knowing which is which — and making the
framework agree with you — is today.

---

## §2 Setup — run this

No new packages.

```bash
mkdir -p days/day-10/lab
touch src/mandala/sdk_tools.py
touch days/day-10/lab/tool_shapes.py
touch days/day-10/lab/runner_anatomy.py
touch days/day-10/lab/failure_modes.py
touch tests/test_sdk_tools.py
touch tests/test_runner.py
```

---

## §3 OAI-03 — Function tools and the `@tool` decorator

### 3.1 What the decorator actually reads

Three sources become one JSON Schema:

| Source | Becomes |
|---|---|
| **function name** | the tool's `name` |
| **type hints** | the parameter types, via a generated Pydantic model |
| **docstring summary** | the tool's `description` |
| **docstring `Args:`** | each parameter's `description` |
| **Pydantic `Field(...)`** | constraints: min/max, patterns, lengths |

The docstring is parsed by **`griffe`**, which understands **google, sphinx and numpy** formats. You
will use google style (`Args:` / `Returns:`) because it is the most readable of the three.

You can turn docstring parsing off with `use_docstring_info=False`. **Do not** — that throws away
your parameter descriptions, and Day 3 taught you what happens then.

### 3.2 `src/mandala/sdk_tools.py`

```python
"""Mandala's tools, SDK-flavoured — with the error policy we chose, not inherited.

Two classes of failure, deliberately handled differently:

  * EXPECTED failures (no such ticket, bad argument) -> return a value the model
    can read and recover from. This is Day 3's decision, kept.
  * BOUNDARY failures (PermissionDenied) -> must NOT be caught. A security check
    that reaches the model as text has become a hint rather than a boundary.

Usage
-----
    >>> from mandala.sdk_tools import get_ticket
    >>> get_ticket.name
    'get_ticket'
"""

from __future__ import annotations

import json
from typing import Annotated

from agents import RunContextWrapper, function_tool
from pydantic import Field

from mandala.permissions import PermissionDenied
from tools import TOOLS as RAW_TOOLS

MAX_SEARCH_RESULTS = 5


def tool_error(ctx: RunContextWrapper, error: Exception) -> str:
    """Our error policy. Returned text goes back to the model as the tool result."""
    if isinstance(error, PermissionDenied):
        raise error                      # boundary: stop the run, do not negotiate
    return json.dumps({
        "error": type(error).__name__,
        "detail": str(error)[:200],
        "hint": "Check the arguments and try a different approach, or say you cannot proceed.",
    })


@function_tool(failure_error_function=tool_error)
def get_ticket(ticket_id: str) -> str:
    """Fetch one support ticket by its exact id.

    Use this whenever the user names a ticket id. Do NOT use this if you do not
    have an exact id — use search_tickets instead.

    Args:
        ticket_id: The ticket id, in the form 'T-1001'.

    Returns:
        A JSON object with id, severity, category and body.
    """
    result = RAW_TOOLS["get_ticket"](ticket_id)
    if "error" in result:
        raise LookupError(f"no ticket with id {ticket_id}")
    return json.dumps(result)


@function_tool(failure_error_function=tool_error)
def search_tickets(
    query: str,
    limit: Annotated[int, Field(ge=1, le=MAX_SEARCH_RESULTS)] = 3,
) -> str:
    """Find tickets whose body contains a literal phrase.

    Use when you do NOT have an exact ticket id. Matches literal substrings only —
    it does not understand synonyms or spelling variants.

    Args:
        query: A literal phrase to look for, e.g. 'login'.
        limit: How many results to return, 1 to 5.

    Returns:
        A JSON array of matching tickets, possibly empty.
    """
    return json.dumps(RAW_TOOLS["search_tickets"](query, limit))


@function_tool(name_override="draft_reply", failure_error_function=tool_error)
def draft_customer_reply(ticket_id: str, body: str) -> str:
    """Draft a reply to a customer. Does NOT send anything.

    Args:
        ticket_id: The ticket being replied to.
        body: The reply text. Plain prose, no markdown.
    """
    return json.dumps({"ticket_id": ticket_id, "draft": body, "sent": False})
```

**Line by line:**

- `def tool_error(ctx, error) -> str:` — the signature the SDK's `failure_error_function` expects: a
  `RunContextWrapper` and the exception. Whatever string you return becomes the tool result the
  model sees.
- `if isinstance(error, PermissionDenied): raise error` — **the most important two lines today.**
  Re-raising propagates out of the tool call and stops the run. Everything else is converted to text.
  This is your Day-8 distinction, now enforced inside a framework that would otherwise have made the
  choice for you.
- `str(error)[:200]` — truncate. An unbounded exception message is unbounded context (Day 4), and a
  stack-trace-laden message is also an information leak if it ever reaches a customer.
- `"hint": "...try a different approach, or say you cannot proceed."` — **give the model a way out.**
  Day 6's refusals lesson: without a permitted failure, it invents a success.
- `@function_tool(failure_error_function=tool_error)` — the decorator takes arguments here, so the
  policy is attached per tool. Same policy on all three today; on Day 21 the write tool gets a
  stricter one.
- The `get_ticket` docstring — note the **"Do NOT use this if..."** line, carried over from Day 3.
  It lives in the summary paragraph, which becomes the tool `description`.
- `if "error" in result: raise LookupError(...)` — **deliberately converting a Day-3 error *value*
  into an exception.** Why undo yesterday's design? Because you now have a central error policy, and
  routing all failures through it means one place decides how failures look. `tool_error` turns it
  straight back into a value — but now consistently, for every tool, in a shape you control.
- `Annotated[int, Field(ge=1, le=MAX_SEARCH_RESULTS)]` — `Annotated[T, metadata]` attaches metadata
  to a type hint. The SDK reads the `Field` constraints and puts them in the JSON Schema, so the
  model is told the valid range **and** a bad value fails validation before your code runs. Compare
  Day 3, where you wrote `{"type": "integer"}` by hand and had no bounds at all.
- `= 3` — a default, so `limit` is not in the schema's `required` list.
- `name_override="draft_reply"` — the function is `draft_customer_reply` (readable in Python) but the
  model sees `draft_reply` (matching `mandala.permissions`). **Use this when your internal naming and
  your permission-table naming would otherwise drift.**

### 3.3 Look at the generated schema — `days/day-10/lab/tool_shapes.py`

```python
"""Print the JSON Schema the decorator generated, and compare it with Day 3's hand-written one.

Budget: 0 requests. This is pure introspection.

Run:
    uv run python days/day-10/lab/tool_shapes.py
"""

from __future__ import annotations

import json

from mandala.sdk_tools import draft_customer_reply, get_ticket, search_tickets
from tools import TOOL_SCHEMAS as HAND_WRITTEN

for tool in (get_ticket, search_tickets, draft_customer_reply):
    print("=" * 70)
    print(f"name:        {tool.name}")
    print(f"description: {tool.description}")
    print("params:")
    print(json.dumps(tool.params_json_schema, indent=2))

print("\n" + "=" * 70)
print("Day 3, hand-written, for comparison:")
print(json.dumps(HAND_WRITTEN[0], indent=2))
```

**Line by line:**

- `tool.name`, `tool.description`, `tool.params_json_schema` — the attributes on a `FunctionTool`.
  **Verify these attribute names against 0.22.0** — if one has been renamed, that is a finding, and
  finding it here costs nothing.
- The comparison print — put them side by side. Look specifically for:
  1. your docstring summary as `description`;
  2. your `Args:` entries as per-parameter `description`s;
  3. `ge`/`le` from the `Annotated[..., Field(...)]` appearing as `minimum`/`maximum`;
  4. whether the SDK emits `additionalProperties: false` (you added that by hand on Day 3 for a
     reason — check whether the SDK does it for you).

**Zero requests, five minutes, and the decorator stops being magic.**

---

## §4 OAI-04 — The Runner, in depth

### 4.1 Three ways to run

| Method | Returns | Use when |
|---|---|---|
| `Runner.run(agent, input, ...)` | awaitable `RunResult` | default — async everywhere |
| `Runner.run_sync(agent, input, ...)` | `RunResult` | quick scripts, no event loop |
| `Runner.run_streamed(agent, input, ...)` | a streaming result you iterate | Day 17 |

### 4.2 What "one turn" means — and why it matters for your budget

**A turn is one model call, plus any tool calls it requested.** Not one tool call. Not one message.

That distinction is a budgeting fact (Principle 5). A run with `max_turns=6` costs **at most 6
requests** to the provider, regardless of how many tools were invoked — because a single turn can
request three tools in parallel and they all execute before the next model call.

So `max_turns` is a **request budget**, expressed as a loop cap. Set it deliberately per agent.

### 4.3 `days/day-10/lab/runner_anatomy.py`

```python
"""Take a RunResult apart until Runner.run stops being a black box.

Budget: ~4 requests. Groq.

Run:
    uv run python days/day-10/lab/runner_anatomy.py
"""

from __future__ import annotations

import asyncio

from agents import Agent, Runner

from mandala.prompts import TRIAGE
from mandala.sdk import DEFAULT_SETTINGS, make_model
from mandala.sdk_tools import get_ticket, search_tickets

agent = Agent(
    name="Triage",
    instructions=TRIAGE.render(),
    model=make_model("groq"),
    model_settings=DEFAULT_SETTINGS,
    tools=[get_ticket, search_tickets],
)


async def main() -> None:
    result = await Runner.run(
        agent,
        "Find tickets about invoices, then tell me the severity of the worst one.",
        max_turns=6,
    )

    print("=== final_output ===")
    print(result.final_output)

    print("\n=== new_items (this is your Day-3 transcript) ===")
    for i, item in enumerate(result.new_items, start=1):
        kind = type(item).__name__
        detail = ""
        if hasattr(item, "raw_item"):
            raw = item.raw_item
            detail = getattr(raw, "name", "") or str(getattr(raw, "content", ""))[:80]
        print(f"  {i:>2}. {kind:<24} {detail}")

    print("\n=== turns ===")
    print(f"  last_agent : {result.last_agent.name}")
    print(f"  input      : {str(result.input)[:80]}")

    print("\n=== usage (your budget line) ===")
    print(f"  {result.context_wrapper.usage}")

    print("\n=== to_input_list() — this is how you continue a conversation manually ===")
    continued = result.to_input_list()
    print(f"  {len(continued)} messages ready to be passed back in")


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- `for i, item in enumerate(result.new_items, start=1)` — walk the transcript. You will see item
  types like `MessageOutputItem`, `ToolCallItem`, `ToolCallOutputItem`. **Map each one onto a line
  from your Day-3 loop**; the correspondence is exact and seeing it is the point of the file.
- `hasattr(item, "raw_item")` — defensive, because item types differ in shape. `raw_item` holds the
  underlying API object.
- `result.context_wrapper.usage` — **the budget line.** This is only populated because
  `include_usage=True` was set yesterday. If it prints `None`, that is a finding: some LiteLLM
  backends omit usage entirely, and you need to know which of yours do before you rely on it.
- `result.to_input_list()` — **the method that matters most in this file.** It converts the whole run
  into a list of messages suitable for passing straight back into another `Runner.run(...)`. That is
  manual multi-turn conversation, and it is exactly Day 7's `session.load()` in SDK clothing.
  Tomorrow you will meet `Session`, which does it for you — and you will know precisely what it is
  doing because you saw `to_input_list()` first.
- `result.last_agent` — the agent that produced the final output. Uninteresting today; **essential
  on Day 13**, when handoffs mean the agent that finished is not the agent that started.

### 4.4 `days/day-10/lab/failure_modes.py` — the day's real lab

```python
"""Four failure modes, and what the Runner does with each.

Budget: ~10 requests. Groq.

Run:
    uv run python days/day-10/lab/failure_modes.py
"""

from __future__ import annotations

import asyncio

from agents import Agent, Runner, function_tool
from agents.exceptions import MaxTurnsExceeded

from mandala.permissions import PermissionDenied
from mandala.sdk import DEFAULT_SETTINGS, make_model
from mandala.sdk_tools import get_ticket, tool_error


@function_tool(failure_error_function=tool_error)
def flaky_lookup(ticket_id: str) -> str:
    """Look up a ticket in the archive.

    Args:
        ticket_id: The ticket id.
    """
    raise ConnectionError("archive unreachable")


@function_tool(failure_error_function=tool_error)
def restricted_export(ticket_id: str) -> str:
    """Export a ticket to the external system.

    Args:
        ticket_id: The ticket id.
    """
    raise PermissionDenied("agent 'triage' may not use 'restricted_export'")


@function_tool
def unhandled_boom(ticket_id: str) -> str:
    """Look something up. This tool has NO failure_error_function.

    Args:
        ticket_id: The ticket id.
    """
    raise ValueError("something went wrong inside the tool")


def build(tools: list) -> Agent:
    return Agent(
        name="FailureLab",
        instructions="Answer the question. Use the tools available to you.",
        model=make_model("groq"),
        model_settings=DEFAULT_SETTINGS,
        tools=tools,
    )


async def main() -> None:
    # 1. expected failure -> the model sees text and recovers
    result = await Runner.run(
        build([flaky_lookup, get_ticket]),
        "Look up T-1001 in the archive; if that fails, use the normal lookup.",
        max_turns=5,
    )
    print(f"[1] recovered      : {result.final_output[:120]}")

    # 2. boundary failure -> the run must STOP
    try:
        await Runner.run(build([restricted_export]), "Export ticket T-1001.", max_turns=3)
        print("[2] LEAKED         : the run continued past a permission boundary!")
    except PermissionDenied as exc:
        print(f"[2] boundary held  : {exc}")

    # 3. no failure handler -> find out what the SDK's default actually is
    try:
        result = await Runner.run(build([unhandled_boom]), "Look up T-1001.", max_turns=3)
        print(f"[3] default handler: run completed -> {result.final_output[:100]}")
    except Exception as exc:
        print(f"[3] default handler: raised {type(exc).__name__}: {exc}")

    # 4. turn cap
    try:
        await Runner.run(build([get_ticket]), "Summarise every ticket, one at a time.", max_turns=1)
    except MaxTurnsExceeded as exc:
        print(f"[4] cap held       : {exc}")


if __name__ == "__main__":
    asyncio.run(main())
```

**What each case teaches:**

1. **Expected failure.** `ConnectionError` becomes text, the model reads it, switches to the other
   tool. This is graceful degradation and it is what you want by default.
2. **Boundary failure.** `PermissionDenied` propagates out of `Runner.run` and the run dies. **If
   this prints `LEAKED`, stop and fix it before doing anything else today** — it means your security
   boundary is being handed to the model as a suggestion.
3. **No handler.** This is the one you are here to find out. **Whatever it prints, write it in your
   notes and in ADR-001.** You are discovering an inherited default, which is precisely what
   Principle 4 exists to stop you doing by accident.
4. **Turn cap.** `MaxTurnsExceeded`, the SDK's version of your Day-3 `RuntimeError`.

---

## §5 The eval that must be able to fail

### `tests/test_sdk_tools.py`

```python
"""Tool-schema tests. 0 model requests — this is all introspection."""

import pytest

from mandala.permissions import PermissionDenied
from mandala.sdk_tools import draft_customer_reply, get_ticket, search_tickets, tool_error


@pytest.mark.parametrize("tool", [get_ticket, search_tickets, draft_customer_reply])
def test_every_tool_has_a_description(tool):
    assert tool.description and len(tool.description) > 20, f"{tool.name} description too thin"


@pytest.mark.parametrize("tool", [get_ticket, search_tickets, draft_customer_reply])
def test_every_parameter_has_a_description(tool):
    """The docstring Args: section IS the prompt. A missing entry is a missing prompt."""
    props = tool.params_json_schema.get("properties", {})
    for name, prop in props.items():
        assert prop.get("description"), f"{tool.name}.{name} has no description"


def test_name_override_is_applied():
    assert draft_customer_reply.name == "draft_reply"


def test_field_constraints_reach_the_schema():
    """Annotated[..., Field(ge=1, le=5)] must appear as minimum/maximum."""
    prop = search_tickets.params_json_schema["properties"]["limit"]
    assert prop.get("minimum") == 1
    assert prop.get("maximum") == 5


def test_negative_guidance_is_present_in_the_description():
    """Day 3's lesson, still true: 'do not use this when' disambiguates overlapping tools."""
    assert "do not use" in get_ticket.description.lower()


def test_error_policy_converts_expected_failures_to_text():
    out = tool_error(None, LookupError("no ticket T-9999"))
    assert "LookupError" in out
    assert "hint" in out


def test_error_policy_reraises_permission_denied():
    """A security boundary must not become a hint the model can route around."""
    with pytest.raises(PermissionDenied):
        tool_error(None, PermissionDenied("nope"))


def test_error_policy_truncates_long_messages():
    out = tool_error(None, ValueError("x" * 5000))
    assert len(out) < 600
```

**Line by line:**

- `@pytest.mark.parametrize("tool", [...])` — the same assertion across all tools, three named
  results. **Add a tool on Day 40 without a docstring and these go red**, which is the cheapest
  possible enforcement of "docstrings are prompts".
- `test_field_constraints_reach_the_schema` — **verifies a framework claim.** The docs say `Field`
  constraints flow into the schema; this asserts it for your actual version. Framework behaviour you
  depend on but have not tested is behaviour that can change in a patch release.
- `test_error_policy_reraises_permission_denied` — the security test. **Two lines, and it is the most
  valuable test in the file.**
- `tool_error(None, ...)` — passing `None` for the context, because this policy does not use it. If
  you later make it context-dependent, this test tells you immediately.

### `tests/test_runner.py`

```python
"""Runner behaviour. Cassette-backed."""

import pytest


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_a_turn_is_one_model_call_not_one_tool_call():
    """max_turns is a REQUEST budget. Prove it by counting."""
    from agents import Runner
    from runner_anatomy import agent

    result = await Runner.run(agent, "Find tickets about invoices.", max_turns=3)
    tool_calls = [i for i in result.new_items if "ToolCall" in type(i).__name__]
    assert len(tool_calls) >= 1
    # more tool calls than turns is legal and expected when the model batches
    assert result.context_wrapper.usage.requests <= 3


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_to_input_list_can_continue_a_conversation():
    """This is what Session automates tomorrow."""
    from agents import Runner
    from runner_anatomy import agent

    first = await Runner.run(agent, "What severity is T-1001?", max_turns=4)
    followup = await Runner.run(
        agent, first.to_input_list() + [{"role": "user", "content": "and its category?"}],
        max_turns=4,
    )
    assert "auth" in followup.final_output.lower()


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_permission_denied_escapes_the_runner():
    from agents import Runner
    from failure_modes import build, restricted_export
    from mandala.permissions import PermissionDenied

    with pytest.raises(PermissionDenied):
        await Runner.run(build([restricted_export]), "Export T-1001.", max_turns=3)
```

- `result.context_wrapper.usage.requests` — **verify this attribute exists and is populated on your
  provider.** If it is `None`, the assertion is meaningless and you must find another way to count
  requests. Discovering that now is far better than discovering it on Day 76 when the whole day is
  about request budgets.
- `test_to_input_list_can_continue_a_conversation` — asserts the manual multi-turn path works, so
  tomorrow's `Session` has something to be compared against.
- `test_permission_denied_escapes_the_runner` — the same boundary test, now at the `Runner` level
  rather than the policy-function level. **Test a security property at every layer it must hold**;
  one of them is where a regression will actually appear.

---

## §6 Traps

- **Letting the default error handler swallow `PermissionDenied`.** Your boundary becomes a hint.
- **No `failure_error_function`.** You inherit a default you have not read (Principle 4). Run
  `failure_modes.py` case 3 and find out what it is.
- **Returning an unbounded exception message.** Unbounded context, and potentially a leak.
- **Thinking `max_turns` counts tool calls.** It counts model calls. Three parallel tools are one
  turn.
- **`use_docstring_info=False`.** Throws away every parameter description.
- **Missing type hints.** The schema is generated from them.
- **A docstring in a format `griffe` does not parse.** Use google style (`Args:`), consistently.
- **`name_override` on some tools and not others.** Now the model sees names that do not match your
  permission table. Pick one naming convention.
- **Assuming usage is populated.** Check `result.context_wrapper.usage` on *your* provider today.

---

## §7 Request budget

| Activity | Requests |
|---|---|
| `tool_shapes.py` | **0** — pure introspection |
| `runner_anatomy.py` | ~4 (Groq) |
| `failure_modes.py` — four cases | ~10 (Groq) |
| Cassettes + iteration | ~15 |
| **Total** | **≈ 29, Groq** |

Note that the entire `test_sdk_tools.py` suite costs **0 requests**. Schema correctness is checkable
offline, and that is where most tool bugs live.

---

## §8 Verify before you code

Written **2026-08-20** against `openai-agents` **0.22.0**.

- `https://openai.github.io/openai-agents-python/tools/` — `@function_tool` parameters:
  `name_override`, `failure_error_function`, `use_docstring_info`, `timeout`, `defer_loading`,
  `allowed_callers`. Also confirm `@tool` is still the equivalent short alias.
- `https://openai.github.io/openai-agents-python/running_agents/` — `Runner.run` / `run_sync` /
  `run_streamed`, `max_turns`, and the `RunResult` attributes.
- `https://openai.github.io/openai-agents-python/results/` — the exact names:
  `final_output`, `new_items`, `last_agent`, `to_input_list()`, and where usage lives.
- The installed source under `agents/tool.py` — confirm `params_json_schema` is the attribute name.
- **Note the docs' standing warning** that the LiteLLM adapter is best-effort/beta and that you
  should validate tool calling on your specific backend. Today is that validation.

---

## §9 Say it in an interview

> "The decorator turns type hints and the docstring into the JSON Schema, so the docstring is
> effectively a prompt — I write the `Args:` section for the model, not for a reader. What I actually
> spend care on is the error policy. The framework has a default that turns tool exceptions into text
> the model can read and recover from, which is right for expected failures like a missing record.
> But I override it, because a `PermissionDenied` must not be converted to text — the moment a
> security boundary reaches the model as a tool result, it's a hint the model will try to route
> around rather than a boundary. So expected failures return a value with a suggested next step, and
> boundary failures re-raise and kill the run."

> "And `max_turns` is a request budget, not a tool-call budget. One turn is one model call plus
> however many tools it requested in parallel — which matters a lot when your budget is a free
> tier's requests-per-day rather than dollars."

---

## §10 Done when

```bash
./m check
./m done 10
```

Tomorrow: `output_type` and `Session` — Day 4's schema and Day 7's session, handed to you.
