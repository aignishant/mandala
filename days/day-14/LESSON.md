---
day: 14
phase: 2
phase_name: "OpenAI Agents SDK core"
title: "Topologies and traces"
ids: ["OAI-11", "OAI-12"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 14 — Topologies and traces

**Phase 2 · OpenAI Agents SDK core** · IDs: **OAI-11 🛠️**, **OAI-12 🛠️**

> **Yesterday:** the two mechanisms — handoff (control transfers) and agent-as-tool (control returns).
> **Today:** assembling those mechanisms into the named shapes from Day 8, and finally being able to
> *see* what happened — for free, without OpenAI's dashboard.
> **Tomorrow:** search without a credit card.

```bash
./m start 14
./m scaffold 14
```

---

## §1 The story

Two things happen today and they look unrelated. They are not.

**First**, you build the two topologies the SDK actually supports — **pipeline** and **supervisor** —
on the same ticket, with the same agents. You have the vocabulary already (Day 8, AG-11); today you
find out which of those four shapes the framework gives you and which one is just *code you write*.

**Second**, you turn tracing on. On **Day 9** you wrote this line and moved on:

```python
set_tracing_disabled(True)     # (2) No OpenAI key exists in this project.
```

That was correct on Day 9 and it is wrong from today. It was never "we don't need tracing" — it was
"the SDK's default trace processor uploads spans to OpenAI's backend, that needs a paid key, and we
have $0" (Principle 5). Disabling was the cheapest way to stop the noise. But it also threw away
every span, which puts you in violation of **Principle 8: the trace is the truth.** For five days
you have been debugging by `print`.

Today you keep the spans and **change where they go.** One line — `set_trace_processors([...])` —
and the spans land in a local JSONL file instead of a service you cannot pay for.

Here is why the two halves belong in one day:

> **You cannot honestly compare two topologies you cannot see.**

Pipeline and supervisor produce the same *kind* of answer. What differs is the shape of the run —
how many model calls, in what order, with what nested inside what. That difference is invisible in
the final output and obvious in a span tree. And on a free tier, "how many model calls" is not a
performance footnote; **it is the budget** (Principle 5). By the end of today, `span_tree.py` prints
the price of a topology.

---

## §2 Setup — run this

No new packages. OpenTelemetry arrives on **Day 75** — today's exporter is thirty lines of stdlib,
and §4.6 shows the exact seam where OTel will drop in without touching anything else. (The
dependency ledger in `docs/PINS.md` says Day 75; adding it early is how a project ends up with
dependencies nobody can justify.)

```bash
mkdir -p days/day-14/lab
touch src/mandala/tracing.py
touch src/mandala/topologies.py
touch days/day-14/lab/pipeline_demo.py
touch days/day-14/lab/supervisor_demo.py
touch days/day-14/lab/span_tree.py
touch tests/test_tracing.py
touch tests/test_topologies.py
```

**Do this before your first traced run** — traces contain customer text:

```bash
printf '.mandala/\n' >> .gitignore
```

`.mandala/` has held your session database since Day 11 and was never ignored. Today it starts
holding trace files. Fix it now, before the commit, not after.

---

## §3 OAI-11 — Multi-agent patterns in the SDK

### 3.1 Four shapes, two primitives

Day 8 gave you the vocabulary. Day 13 gave you the primitives. Here is the mapping, and it is
shorter than you would expect:

| Topology (AG-11) | What builds it in the Agents SDK |
|---|---|
| **Peer handoff** | `handoffs=[...]` — yesterday |
| **Supervisor** | `agent.as_tool(...)` — yesterday |
| **Pipeline** | **nothing. You write a function.** |
| **Hierarchical** | a supervisor whose sub-agents are themselves supervisors |

Read the third row again. **The SDK has no pipeline construct.** If you want Researcher → Resolver,
in that order, every time, you write two `await Runner.run(...)` calls in a Python function with the
first result feeding the second.

That is not a gap in the SDK. It is the SDK's thesis showing through: *the model owns the loop.*
A pipeline is the one topology where the model owns nothing — the order is decided by you, at build
time, and no amount of model cleverness can change it. A framework built around model-driven control
has nothing to add to a `for` loop.

So today's real question is not "how do I build a pipeline in the SDK" — it is:

> **When the order matters, who should be enforcing it: my code, or my prompt?**

You are about to build both answers and compare them on the same ticket.

### 3.2 `src/mandala/topologies.py`

```python
"""Mandala's two SDK topologies. Neither one is a framework feature.

- pipeline   — a Python function. Researcher, then Resolver, in that order, always.
- supervisor — one agent holding the other two as tools. The MODEL picks the order.

The seam between the two pipeline steps is a Brief (Day 8), never a ticket body.
That is the Day-8 separation; run_pipeline() ENFORCES it rather than trusting it.

Usage
-----
    >>> from mandala.topologies import TOPOLOGIES
    >>> sorted(TOPOLOGIES)
    ['pipeline', 'supervisor']
"""

from __future__ import annotations

from agents import Agent, Runner, custom_span, trace
from pydantic import BaseModel

from mandala.agents import RESEARCHER_PROMPT, RESOLVER_PROMPT, Brief
from mandala.context import MandalaContext
from mandala.sdk import DEFAULT_SETTINGS, make_model
from mandala.sdk_tools import draft_customer_reply, get_ticket, search_tickets

READ_TOOLS = [get_ticket, search_tickets]
DRAFT_TOOLS = [draft_customer_reply]        # drafting is not writing — Day 8's split, kept


def researcher() -> Agent:
    """Reads untrusted ticket text. Holds no write tool. Returns a typed Brief."""
    return Agent(
        name="Researcher",
        instructions=RESEARCHER_PROMPT.render(),
        model=make_model("groq"),
        model_settings=DEFAULT_SETTINGS,
        tools=READ_TOOLS,
        output_type=Brief,
    )


def resolver() -> Agent:
    """Drafts a reply from a Brief. Has NO get_ticket — it must not be able to look."""
    return Agent(
        name="Resolver",
        instructions=RESOLVER_PROMPT.render(),
        model=make_model("groq"),
        model_settings=DEFAULT_SETTINGS,
        tools=DRAFT_TOOLS,
    )


class PipelineResult(BaseModel):
    ticket_id: str
    brief: Brief
    reply: str


def assert_no_raw_ticket(brief: Brief, ticket_id: str, *, context: MandalaContext) -> None:
    """Fail if the Brief smuggles the ticket body across the seam.

    The Researcher is TOLD not to quote (Day 8's prompt) and the Brief is
    length-capped (Day 8's schema). Neither is enforcement. This is enforcement.

    Write it like this:
      1. read the ticket body from context.tickets_path,
      2. slide a window of ~40 characters across it,
      3. raise ValueError if any window appears verbatim in brief.model_dump_json().

    Why 40 and not 10: short windows match ordinary English ("the customer said")
    and you would fail on every honest brief. Pick the number, then justify it.
    """
    raise NotImplementedError  # TODO(me): today's real rep. test_topologies.py is red until this works.


async def run_pipeline(ticket_id: str, *, context: MandalaContext) -> PipelineResult:
    """Pipeline topology: fixed order, decided by me at build time, not by a model."""
    with trace(workflow_name="mandala.pipeline", group_id=context.request_id):
        with custom_span(name="step.research"):
            research = await Runner.run(
                researcher(), f"Research ticket {ticket_id}.", context=context, max_turns=6
            )

        brief: Brief = research.final_output
        assert_no_raw_ticket(brief, ticket_id, context=context)

        with custom_span(name="step.resolve"):
            resolution = await Runner.run(
                resolver(), brief.model_dump_json(), context=context, max_turns=4
            )

    return PipelineResult(ticket_id=ticket_id, brief=brief, reply=str(resolution.final_output))


def build_supervisor() -> Agent:
    """Supervisor topology: agents-as-tools, and the MODEL picks the order."""
    return Agent(
        name="Supervisor",
        instructions=(
            "You own this ticket end to end. First call research_ticket. Then, using ONLY the "
            "brief it returned, call draft_resolution. Finish with a two-line report of what "
            "you did.\n"
            "Never call draft_resolution before research_ticket.\n"
            "Never pass a ticket id or ticket text to draft_resolution — pass the brief.\n"
            "You may call research_ticket a second time if the brief is insufficient."
        ),
        model=make_model("groq"),
        model_settings=DEFAULT_SETTINGS,
        tools=[
            researcher().as_tool(
                tool_name="research_ticket",
                tool_description=(
                    "Read a ticket and return a structured brief (JSON) with findings and a "
                    "recommended action. Call this first, before anything else."
                ),
            ),
            resolver().as_tool(
                tool_name="draft_resolution",
                tool_description=(
                    "Turn a brief (JSON) into a draft customer reply. "
                    "Do NOT call this with a ticket id or a ticket body — only with a brief."
                ),
            ),
        ],
    )


TOPOLOGIES = {
    "pipeline": "order enforced in Python; the model cannot reorder it",
    "supervisor": "order requested in a prompt; the model may reorder it",
}
```

**Line by line:**

- `researcher()` and `resolver()` are **factories, not module-level agents.** Yesterday's demos built
  agents at import time, which was fine for one script. Here the same agents are used by two
  topologies and by tests, and a shared mutable `Agent` is a shared surprise. Building a fresh one
  per run also means `as_tool` and `Runner.run` never accidentally share state.
- `tools=READ_TOOLS` / `tools=DRAFT_TOOLS` as named constants — so §5 can assert the split without
  reaching inside an agent. The permission table (Day 8) is still the source of truth; these lists
  must agree with it, and there is a test for that. **Note the name is `DRAFT_TOOLS`, not
  `WRITE_TOOLS`:** `draft_reply` has `writes=False` in the permission table because it returns text
  and sends nothing. Day 8 split drafting from posting on purpose; naming the constant carelessly is
  how that distinction quietly dies.
- **`resolver()` has no `get_ticket`.** This is the whole Day-8 design in one omission. It cannot see
  the raw ticket because it holds no tool that returns one — not because it was asked nicely.
- `output_type=Brief` on the researcher — the seam is typed (Day 11's mechanism, Day 8's schema).
- `def assert_no_raw_ticket(...)` — the **three-layer defence, completed.** The prompt says don't
  quote; the schema caps length; this raises. Yesterday you learned that a default can silently undo
  a security property. A check that runs on every pipeline call is how you find out on the day it
  breaks. Its body is yours to write.
- `with trace(workflow_name=..., group_id=...)` wrapping **both** runs — this is the line that makes
  the pipeline one workflow instead of two unrelated ones. Without it you get two separate traces and
  no way to see that one followed the other. See §4.1.
- `group_id=context.request_id` — the Day-12 `request_id` becomes the trace's group key, so the
  audit lines and the spans share one identifier. That is the pay-off for a field you added two days
  ago "for tracing" without yet having tracing.
- `custom_span(name="step.research")` — **your own span, nested inside the SDK's.** The SDK traces
  what it does; the two steps of *your* pipeline are yours to name. A trace of only framework
  internals reads like a stack trace; a trace with your vocabulary in it reads like your system.
- `brief.model_dump_json()` as the Resolver's input — the entire message it receives is the Brief.
  Not the ticket, not the conversation. Compare with a handoff, where you needed `input_filter` to
  achieve the same thing.
- `build_supervisor()` — the same two agents, wired the other way. Notice what carries the ordering
  constraint here: `"Never call draft_resolution before research_ticket."` **A sentence.** In
  `run_pipeline` that constraint is the fact that line 2 comes after line 1.
- The `draft_resolution` description contains a **"Do NOT"** clause — yesterday's routing rule,
  reused. This is the guardrail against the supervisor's characteristic failure: shortcutting
  straight to the writer with the raw ticket id.
- `TOPOLOGIES` — a small registry so §5 can assert the two exist and are described honestly, and so
  Day 59's bake-off has something to iterate.

### 3.3 `days/day-14/lab/pipeline_demo.py`

```python
"""The pipeline topology, traced end to end.

Run:
    uv run python days/day-14/lab/pipeline_demo.py T-1004
"""

from __future__ import annotations

import asyncio
import sys

from mandala.context import MandalaContext
from mandala.topologies import run_pipeline
from mandala.tracing import install_local_tracing


async def main() -> None:
    ticket_id = sys.argv[1] if len(sys.argv) > 1 else "T-1004"
    processor = install_local_tracing()

    context = MandalaContext(actor="agent:researcher", request_id=f"req-{ticket_id}")
    result = await run_pipeline(ticket_id, context=context)

    print(f"\n--- brief ---\n{result.brief.model_dump_json(indent=2)}")
    print(f"\n--- reply ---\n{result.reply}")

    processor.force_flush()
    print(f"\ntraces written to: {processor.directory}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- `install_local_tracing()` is called **in the demo, not in the library.** `mandala.tracing` provides
  the capability; the entry point decides to use it. A library that installs a global processor on
  import is a library that fights every other library in the process. (Day 9's
  `set_tracing_disabled` at import was the opposite call, and §4.2 explains why that one earned its
  exception and this one does not.)
- `actor="agent:researcher"` — the pipeline *starts* as the researcher. Note the honest wrinkle: one
  context object, two agents with different permissions. That is a real limitation of a single
  `MandalaContext` per run and you should notice it now; Day 19 and Phase 7 both come back to it.
- `processor.force_flush()` before exit — harmless here because our writer appends synchronously, but
  written explicitly so the habit survives the day you swap in a batching exporter. **The classic
  first tracing bug is an empty file at exit.**

### 3.4 `days/day-14/lab/supervisor_demo.py`

```python
"""The supervisor topology, traced end to end. Same ticket, same agents, different shape.

Run:
    uv run python days/day-14/lab/supervisor_demo.py T-1004
"""

from __future__ import annotations

import asyncio
import sys

from agents import Runner, trace

from mandala.context import MandalaContext
from mandala.topologies import build_supervisor
from mandala.tracing import install_local_tracing


async def main() -> None:
    ticket_id = sys.argv[1] if len(sys.argv) > 1 else "T-1004"
    processor = install_local_tracing()

    context = MandalaContext(actor="agent:supervisor", request_id=f"req-{ticket_id}")

    with trace(workflow_name="mandala.supervisor", group_id=context.request_id):
        result = await Runner.run(
            build_supervisor(),
            f"Handle ticket {ticket_id} end to end.",
            context=context,
            max_turns=10,
        )

    print(f"\nfinished with: {result.last_agent.name}")      # Supervisor — control never left
    print(f"\n{result.final_output}")

    print("\n--- tool calls, in the order the MODEL chose ---")
    for item in result.new_items:
        name = getattr(getattr(item, "raw_item", None), "name", None)
        if name:
            print(f"  {name}")

    processor.force_flush()


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- `with trace(workflow_name="mandala.supervisor")` around a **single** `Runner.run` — strictly
  unnecessary (a single run creates its own trace) but done anyway, so the workflow name is *yours*
  and the two demos are comparable in the same trace directory. Naming your workflows is what makes a
  trace directory searchable in eleven weeks.
- `max_turns=10` versus the pipeline's `6 + 4` — the same work, but the supervisor spends turns
  *deciding* as well as doing. That difference has a price and §4.5 measures it.
- The tool-call loop prints the order **the model chose**. Run it three or four times. On a good day
  the order is `research_ticket`, `draft_resolution`. Sooner than you expect, it will not be — and
  that is the finding, not a bug in your code.
- `getattr(getattr(item, "raw_item", None), "name", None)` — defensive because `new_items` holds
  several item types and only some carry a tool name. **TODO(me): find the precise item types in
  0.22.0 and replace this with an `isinstance` check.** Defensive `getattr` is what you write while
  you are learning a library; it is not what you leave behind.

### 3.5 The comparison — this is the deliverable

Run both on the same ticket, back to back:

```bash
uv run python days/day-14/lab/pipeline_demo.py T-1004
uv run python days/day-14/lab/supervisor_demo.py T-1004
```

| Property | **pipeline** (Python) | **supervisor** (model) |
|---|---|---|
| Who decides the order | you, at build time | the model, at run time |
| Ordering guarantee | **structural** — unbreakable | **prompt-level** — best effort |
| Adapts to a weird ticket | no | yes |
| Model calls | fixed (2 agents, ~5 calls) | variable (~8 and up) |
| What crosses the seam | exactly a `Brief` | whatever the model passes |
| Characteristic failure | the right shape, the wrong answer | the right answer, in the wrong order |
| How you find out | **a test** | **a trace** |

That last row is the one to keep. A structural property can be asserted before you ship. A
behavioural property can only be *observed*, which is why the second half of today exists.

### 3.6 Where the SDK stops

The OAI-11 note in the plan says: *"where the SDK stops and you want a graph instead."* Here is the
honest boundary. If you catch yourself writing any of these, you have started building a graph
engine, badly:

| If you find yourself needing… | You want… | Arrives |
|---|---|---|
| to resume a run after the process died | durable checkpoints | Day 47 (LangGraph), Day 20 (Temporal) |
| to branch, run two paths, and re-join | conditional edges + fan-in | Day 43–44 |
| to loop "until the brief is good enough" | a cyclic graph with a condition | Day 43 |
| to pause for a human and resume later | interrupts | Day 33 (Flows), Day 49 (LangGraph) |
| to inspect or rewrite state mid-run | explicit state | Day 43 |
| to replay from step 3 with one value changed | time travel | Day 50 |

None of these are *impossible* in the Agents SDK — they are all possible, the way anything is
possible in Python. The point is that you would be hand-rolling the thing LangGraph is. **Write this
table into your Day-16 ADR-001 draft ("what the SDK owns vs. what I own") while it is fresh.** It is
the strongest section that ADR will have, and today is the day you can write it from experience
rather than from a blog post.

---

## §4 OAI-12 — Tracing

### 4.1 The vocabulary, and the one thing that matters

- A **trace** is one workflow run, start to finish. It has a `trace_id`, a `workflow_name`, and
  optionally a `group_id`.
- A **span** is one unit of work inside it: an agent turn, a model call, a tool call, a handoff, a
  guardrail. Spans nest via `parent_id`, so a trace is a tree.
- The SDK creates spans for you automatically: **agent**, **generation** (the model call),
  **function** (a tool call), **handoff**, **guardrail**. You add your own with `custom_span`.

The one thing that matters today:

> **By default, each `Runner.run()` is its own trace.** Wrapping several runs in
> `with trace(workflow_name=...)` makes them **one** trace.

That is precisely the pipeline's problem. Two `Runner.run` calls with no `trace()` around them
produce two unrelated trees and you cannot see that one followed the other. One `with trace(...)` and
the whole pipeline is a single readable object. **This is why the tracing half of today is attached
to the topology half.**

`group_id` is the other identifier worth knowing: it links *separate* traces that belong to the same
conversation — the same thing Day 11's session id does for history. One trace per turn, one group per
conversation.

### 4.2 The zero-budget problem, and the exact fix

The SDK ships a default trace processor that batches spans to **OpenAI's traces backend**. That needs
an OpenAI API key, which this project does not have and will never have (Principle 5). Hence Day 9's
`set_tracing_disabled(True)`.

Three functions, and picking the wrong one is today's trap:

| Function | What it does | Right for us? |
|---|---|---|
| `set_tracing_disabled(True)` | no spans are produced at all | Day 9's stopgap. **No** — it throws away the data |
| `add_trace_processor(p)` | **adds** `p` alongside the default | **No** — the OpenAI exporter is still there, still trying |
| `set_trace_processors([p])` | **replaces** the whole list | **Yes** — nothing leaves the machine |

`add_trace_processor` is the one that looks right and is not. Your spans would arrive in your file
*and* an exporter would keep trying to reach a service you have no key for — noisy at best, and a
project whose spans leave the building at worst.

**So make these two edits to Day 9's file.** In `src/mandala/sdk.py`:

```python
# DELETE this line, and its (2) comment:
set_tracing_disabled(True)
```

Tracing is now installed by the entry point that wants it (`install_local_tracing()`), not disabled
globally at import. And in `tests/test_sdk_agent.py`, Day 9's `test_tracing_is_disabled_on_import`
no longer describes the invariant you care about. Replace it — the new invariant is in §5:
**no processor may point at OpenAI.**

Notice what made this edit safe: Day 9's line had a comment saying *why* it was there. A decision
with its reason attached is a decision you can revisit. One without is a line nobody dares touch.

### 4.3 `src/mandala/tracing.py`

```python
"""Local, free tracing. Spans go to a JSONL file on this machine. Nothing is uploaded.

Principle 8 says the trace is the truth. Principle 5 says $0. The SDK's default
processor uploads spans to OpenAI, which needs a paid key — so Day 9 disabled
tracing entirely. Today we keep the spans and change their destination.

Principle 6 also applies, and it pulls the other way: a trace file is a place
where customer text goes to live on disk forever. So everything written here
passes an ALLOWLIST and a length cap. A trace records the SHAPE of a run, not
its contents.

Usage
-----
    >>> from mandala.tracing import install_local_tracing
    >>> processor = install_local_tracing()
    >>> processor.directory.name
    'traces'
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

from agents import set_trace_processors
from agents.tracing import TracingProcessor

TRACE_DIR = Path(os.environ.get("MANDALA_TRACE_DIR", ".mandala/traces"))

# An ALLOWLIST. Anything not named here never reaches disk.
SAFE_SPAN_FIELDS = (
    "name", "type", "from_agent", "to_agent", "model",
    "tool_name", "triggered", "handoffs", "tools", "output_type",
)

MAX_VALUE_CHARS = 200


def _shrink(value: Any) -> Any:
    """Every value that reaches disk passes through here."""
    if value is None or isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, str):
        return value[:MAX_VALUE_CHARS]
    if isinstance(value, (list, tuple)):
        return [_shrink(v) for v in value[:10]]
    return f"<{type(value).__name__}>"


def summarise(span_data: Any) -> dict:
    """Pull only the allowlisted fields off a span's data object."""
    record = {"data_type": type(span_data).__name__}
    for field in SAFE_SPAN_FIELDS:
        if hasattr(span_data, field):
            record[field] = _shrink(getattr(span_data, field))
    return record


class JsonlTraceProcessor(TracingProcessor):
    """One file per trace, one JSON object per line. No network, no key, no cost."""

    def __init__(self, directory: Path = TRACE_DIR) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _write(self, trace_id: str, record: dict) -> None:
        try:
            path = self.directory / f"{trace_id}.jsonl"
            with self._lock, path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, default=str) + "\n")
        except Exception as exc:                      # noqa: BLE001 — deliberate, see below
            print(f"[tracing] dropped a record: {type(exc).__name__}: {exc}")

    def on_trace_start(self, trace) -> None:
        self._write(trace.trace_id, {
            "kind": "trace_start",
            "trace_id": trace.trace_id,
            "workflow_name": getattr(trace, "name", None),
            "group_id": getattr(trace, "group_id", None),
        })

    def on_trace_end(self, trace) -> None:
        self._write(trace.trace_id, {"kind": "trace_end", "trace_id": trace.trace_id})

    def on_span_start(self, span) -> None:
        return                                        # nothing is known yet that is worth a line

    def on_span_end(self, span) -> None:
        self._write(span.trace_id, {
            "kind": "span",
            "trace_id": span.trace_id,
            "span_id": span.span_id,
            "parent_id": span.parent_id,
            "started_at": span.started_at,
            "ended_at": span.ended_at,
            "error": _shrink(getattr(span, "error", None)),
            "data": summarise(span.span_data),
        })

    def force_flush(self) -> None:
        return                                        # we append synchronously; nothing is buffered

    def shutdown(self) -> None:
        return


def install_local_tracing(directory: Path = TRACE_DIR) -> JsonlTraceProcessor:
    """REPLACE the processor list. add_trace_processor() would keep OpenAI's exporter."""
    processor = JsonlTraceProcessor(directory)
    set_trace_processors([processor])
    return processor
```

**Line by line:**

- `TRACE_DIR` reads `MANDALA_TRACE_DIR` with a default — so tests write to `tmp_path` and never
  pollute your real trace directory. Same dependency-injection instinct as Day 12's `tickets_path`.
- `SAFE_SPAN_FIELDS` is an **allowlist, and that choice is the security content of this file.** A
  denylist ("write everything except the ticket body") loses the day someone adds a new span type
  with a new field. An allowlist fails closed: an unknown field is simply not written. Yesterday you
  proved a leak with a canary; today you make the leak structurally impossible in a second place.
- `MAX_VALUE_CHARS = 200` — the same judgement as Day 5's `result_len`, for the same reason: **a
  trace you can print in full is a trace you will actually read.** Storing whole payloads produces a
  file you will never open.
- `_shrink` returns `f"<{type(value).__name__}>"` for anything unrecognised — the *shape* survives,
  the *content* does not. When you read `<ResponseOutputMessage>` in a trace you know something was
  there and you know it did not get written to disk.
- `value[:10]` on lists — an unbounded list of tool names is fine; an unbounded list of messages is
  a leak with extra steps. Cap both.
- `class JsonlTraceProcessor(TracingProcessor)` — you implement the SDK's processor interface, which
  is the same shape OTel's span exporter wants. That is not a coincidence and §4.6 uses it.
- **`_write` swallows every exception, and this is the most important design decision in the file.**
  A tracing bug must never kill a run. Ruff will flag the bare `except Exception` — the `# noqa` with
  a reason is the honest way to keep it. Instrumentation that can take down the thing it instruments
  is worse than no instrumentation; you will believe this the first time a `json.dumps` of an
  unserialisable object ends a ten-minute run.
- `threading.Lock` — the SDK may end spans from more than one thread. Two interleaved half-lines in a
  JSONL file are unparseable, and you will blame the parser.
- `on_span_start` returns immediately — at start you know almost nothing; duration and error are
  only known at the end. Writing both doubles the file for no information.
- `"error": _shrink(getattr(span, "error", None))` — **record failures.** The traces you actually
  read are the ones where something went wrong. A tracer that only records success is a tracer for
  demos.
- `default=str` in `json.dumps` — the last line of defence against a value the allowlist let through
  that is not JSON-serialisable. Combined with the `try`, an unexpected type degrades to a string
  instead of an exception.
- `def install_local_tracing(...)` — one function, one job, and the docstring names the wrong
  alternative. When the wrong call is one keystroke away from the right one, say so where someone
  will read it.

**TODO(me):** the attribute names on `span` and `span_data` — `started_at`, `span_data`, `error` —
are the surface most likely to have moved in 0.22.0. Print one span object before you trust this
file:

```python
from agents import custom_span
with custom_span(name="probe") as span:
    pass
print(vars(span))
print(vars(span.span_data))
```

Fix the field names from what you see, not from what this lesson says. §8 lists the docs page.

### 4.4 `days/day-14/lab/span_tree.py` — the artifact of the day

```python
"""Read a trace file back and print it as a tree. Zero model calls.

Run:
    uv run python days/day-14/lab/span_tree.py                # newest trace
    uv run python days/day-14/lab/span_tree.py <trace_id>
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

from mandala.tracing import TRACE_DIR


def load(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def newest() -> Path:
    files = sorted(TRACE_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise SystemExit(f"no traces in {TRACE_DIR} — run a demo first")
    return files[-1]


def duration_ms(span: dict) -> float:
    """TODO(me): started_at/ended_at — ISO strings? floats? Find out, then convert."""
    raise NotImplementedError


def model_calls(records: list[dict]) -> int:
    """How many times did we hit a provider? On a free tier this is the price."""
    return sum(
        1 for r in records
        if r["kind"] == "span" and "Generation" in r["data"]["data_type"]
    )


def render(records: list[dict]) -> str:
    spans = [r for r in records if r["kind"] == "span"]
    children: dict[str | None, list[dict]] = defaultdict(list)
    for span in spans:
        children[span["parent_id"]].append(span)

    lines: list[str] = []

    def walk(parent_id: str | None, depth: int) -> None:
        for span in children[parent_id]:
            data = span["data"]
            label = data.get("name") or data.get("tool_name") or data["data_type"]
            flag = "   <- ERROR" if span.get("error") else ""
            lines.append(f"{'  ' * depth}{label:<30} {duration_ms(span):>7.0f}ms{flag}")
            walk(span["span_id"], depth + 1)

    walk(None, 0)
    return "\n".join(lines)


def main() -> None:
    path = TRACE_DIR / f"{sys.argv[1]}.jsonl" if len(sys.argv) > 1 else newest()
    records = load(path)
    header = next((r for r in records if r["kind"] == "trace_start"), {})

    print(f"workflow    : {header.get('workflow_name')}")
    print(f"group_id    : {header.get('group_id')}")
    print(f"model calls : {model_calls(records)}")
    print(f"spans       : {sum(1 for r in records if r['kind'] == 'span')}\n")
    print(render(records))


if __name__ == "__main__":
    main()
```

**Line by line:**

- `children[span["parent_id"]]` with a `defaultdict` and `walk(None, 0)` — the root spans are the ones
  whose parent is `None`. Six lines to turn a flat log into a tree, and this is the whole reason
  `parent_id` was worth writing.
- `duration_ms` is a **TODO(me)** and it is deliberate: you cannot write it without discovering what
  `started_at` actually is in 0.22.0. That discovery is the rep. Guessing gets you a `TypeError`;
  printing one span gets you the answer in ten seconds. **Instrument first, debug second** applies to
  your instrumentation too.
- `model_calls` counts generation spans, and the docstring says why in the only currency that
  matters here. Note it counts **calls, not tokens** — `include_usage=True` from Day 9 is what gets
  you tokens, and Day 71 joins the two.
- `label = name or tool_name or data_type` — a readable label with a fallback chain, because not
  every span type carries the same fields. When the label reads `AgentSpanData`, that is your
  allowlist telling you it has no `name` field and you should look again.
- `flag = "   <- ERROR"` — failures are visually loud. You will scan this output, not read it.
- The lab reads a file and makes **zero model calls.** You can iterate on the renderer as many times
  as you like for free, which is exactly why the exporter and the reader are separate programs.

### 4.5 What you should see

Roughly this, for the pipeline:

```
workflow    : mandala.pipeline
group_id    : req-T-1004
model calls : 5
spans       : 11

step.research                      3120ms
  Researcher                       3110ms
    GenerationSpanData              820ms
    get_ticket                       12ms
    GenerationSpanData             1180ms
    search_tickets                   18ms
    GenerationSpanData             1090ms
step.resolve                       1640ms
  Resolver                         1630ms
    GenerationSpanData              900ms
    draft_customer_reply              4ms
    GenerationSpanData              720ms
```

And for the supervisor:

```
workflow    : mandala.supervisor
group_id    : req-T-1004
model calls : 8
spans       : 15

Supervisor                         7400ms
  GenerationSpanData                760ms
  research_ticket                  3210ms
    Researcher                     3200ms
      GenerationSpanData            810ms
      get_ticket                     11ms
      GenerationSpanData           1170ms
  GenerationSpanData                690ms
  draft_resolution                 1680ms
    Resolver                       1670ms
      GenerationSpanData            900ms
      draft_customer_reply            4ms
  GenerationSpanData                640ms
```

**Read the difference, not the numbers.**

- The pipeline's tree has **two roots**, side by side, in the order you wrote them. The supervisor's
  has **one root** with everything nested inside it — because control never left. That is
  yesterday's `last_agent` distinction, drawn as a picture.
- The supervisor makes **more model calls for the same work**: one to decide to research, one to
  decide to draft, one to write the report. On Groq's free tier that is the entire cost of
  flexibility, stated in the only unit you have.
- The sub-agents appear as *tool spans* in the supervisor's tree. An agent-as-tool is a tool, all the
  way down to the trace.

Now do the thing that makes this a lab rather than a demo: **run the supervisor five times and count
how often the model calls the tools in the order you asked for.** Write the number in your
CHECKLIST. That number is what §3.5's "prompt-level, best effort" row actually means, measured on
your machine, with your model pin. An interview answer with a number in it is worth ten without.

### 4.6 Portability — Principle 8's actual point

Principle 8 is not "use a tracing vendor". It is **the trace is the truth**, and a truth you can only
read inside one vendor's dashboard is a truth you lose when you switch frameworks — which this plan
does four times.

Look at what you built: a class with four hooks that receives spans and writes them somewhere. That
is the same shape as an OpenTelemetry span exporter, which is why the swap is small and already
planned:

| Day | Destination | Cost |
|---|---|---|
| **14 (today)** | `.mandala/traces/*.jsonl` | $0, no deps |
| 73 | LangSmith free tier | $0, watch the monthly trace quota |
| 75 | OTLP → any OTel backend | $0 self-hosted |

Nothing above the processor changes on those days: the `custom_span` calls, the workflow names, the
`group_id` convention all survive. **That is what "portable" buys you** — and it is the reason today's
file is thirty lines of stdlib rather than a dependency you would have to unpick.

---

## §5 The eval that must be able to fail

### `tests/test_topologies.py`

```python
"""The topologies, and the separation they must preserve."""

import pytest

from mandala.permissions import TOOLS, tools_for
from mandala.topologies import TOPOLOGIES, build_supervisor, researcher, resolver


def _tool_names(agent) -> set[str]:
    return {getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.tools}


def test_resolver_cannot_read_tickets():
    """The Day-8 separation, asserted on the SDK agent rather than on the plan."""
    assert "get_ticket" not in _tool_names(resolver())
    assert "search_tickets" not in _tool_names(resolver())


def test_researcher_holds_no_write_tool():
    for name in _tool_names(researcher()):
        assert not TOOLS[name].writes, f"researcher was granted the write tool {name}"


def test_agent_tools_match_the_permission_table():
    """Two sources of truth is zero sources of truth."""
    assert _tool_names(researcher()) <= set(tools_for("researcher"))


def test_supervisor_exposes_both_agents_as_tools():
    assert {"research_ticket", "draft_resolution"} <= _tool_names(build_supervisor())


def test_supervisor_warns_against_passing_raw_tickets():
    """A prose lint, like Day 13's. The 'do NOT' clause is load-bearing."""
    for tool in build_supervisor().tools:
        if getattr(tool, "name", "") == "draft_resolution":
            assert "do not" in tool.description.lower()
            break
    else:
        pytest.fail("draft_resolution not found")


def test_both_topologies_are_registered():
    assert set(TOPOLOGIES) == {"pipeline", "supervisor"}


def test_assert_no_raw_ticket_catches_a_quoting_brief(quoting_brief, mandala_context):
    """The check that makes the seam real. Red until you write the TODO(me)."""
    from mandala.topologies import assert_no_raw_ticket

    with pytest.raises(ValueError):
        assert_no_raw_ticket(quoting_brief, "T-9002", context=mandala_context)


def test_assert_no_raw_ticket_accepts_an_honest_brief(honest_brief, mandala_context):
    from mandala.topologies import assert_no_raw_ticket

    assert_no_raw_ticket(honest_brief, "T-9002", context=mandala_context)   # must not raise
```

### `tests/test_tracing.py`

```python
"""The tracer must be honest, harmless, and silent about customer text."""

import json

import pytest

from mandala.tracing import JsonlTraceProcessor, install_local_tracing, summarise


def test_a_broken_record_does_not_kill_the_run(tmp_path):
    """Instrumentation that can take down the run is worse than none."""
    processor = JsonlTraceProcessor(tmp_path)
    processor._write("t-1", {"kind": "span", "data": {1, 2, 3}})    # a set: not JSON
    assert True                                                      # got here = did not raise


def test_every_record_is_one_json_line(tmp_path):
    processor = JsonlTraceProcessor(tmp_path)
    processor._write("t-1", {"kind": "span", "n": 1})
    processor._write("t-1", {"kind": "span", "n": 2})
    lines = (tmp_path / "t-1.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["n"] for line in lines] == [1, 2]


def test_summarise_drops_unknown_fields():
    """The allowlist fails CLOSED. This is the test that survives a new span type."""

    class SpanData:
        name = "get_ticket"
        ticket_body = "PINEAPPLE-7731 my card was charged twice"

    record = summarise(SpanData())
    assert record["name"] == "get_ticket"
    assert "ticket_body" not in record
    assert "PINEAPPLE" not in json.dumps(record)


def test_long_values_are_capped():
    class SpanData:
        name = "x" * 5_000

    assert len(summarise(SpanData())["name"]) <= 200


def test_no_processor_points_at_openai():
    """Replaces Day 9's test_tracing_is_disabled_on_import. Principle 5, asserted."""
    install_local_tracing()
    # TODO(me): find the accessor for the installed processor list in 0.22.0,
    # then assert every entry is a JsonlTraceProcessor.
    raise AssertionError("write this assertion")


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_a_pipeline_is_one_trace_not_two(tmp_path):
    """Remove the `with trace(...)` in run_pipeline and this must go RED with 2 files."""
    from mandala.context import MandalaContext
    from mandala.topologies import run_pipeline

    install_local_tracing(tmp_path)
    context = MandalaContext(actor="agent:researcher", request_id="req-T-1004")
    await run_pipeline("T-1004", context=context)

    assert len(list(tmp_path.glob("*.jsonl"))) == 1


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_the_trace_file_never_contains_the_canary(tmp_path):
    """Yesterday: the canary must not reach the Resolver. Today: nor the disk."""
    from mandala.context import MandalaContext
    from mandala.topologies import run_pipeline

    install_local_tracing(tmp_path)
    context = MandalaContext(actor="agent:researcher", request_id="req-T-9002")
    await run_pipeline("T-9002", context=context)

    written = "".join(p.read_text(encoding="utf-8") for p in tmp_path.glob("*.jsonl"))
    assert "PINEAPPLE-7731" not in written
```

**Line by line:**

- `test_resolver_cannot_read_tickets` — the Day-8 separation, asserted against the **SDK agent you
  actually run**, not against the permission table's description of it. The table was tested on
  Day 8; today's risk is that the agent drifts from the table.
- `test_agent_tools_match_the_permission_table` — **two sources of truth is zero sources of truth.**
  Write this even though it feels redundant; it is the test that catches "I added one tool to unblock
  myself" on Day 62.
- `test_assert_no_raw_ticket_*` — **the pair, again.** One proves the check fires, one proves it does
  not fire on honest input. A check that always raises would pass the first test alone. You need
  `quoting_brief`, `honest_brief` and `mandala_context` fixtures in `tests/conftest.py`.
- `test_a_broken_record_does_not_kill_the_run` — asserts an *absence of an exception*, which looks
  like a nothing-test and is the most valuable one in the file. **Flip it:** delete the `try` in
  `_write` and watch it go red.
- `test_summarise_drops_unknown_fields` — the allowlist, proved with yesterday's canary string. Note
  it asserts on `json.dumps(record)`, not on one field: it checks the canary is nowhere in the
  serialised output, which is the property you actually want.
- `test_no_processor_points_at_openai` — **Day 9's TODO, finally answerable.** It ships as a failing
  test on purpose: `raise AssertionError` until you find the accessor. A test that fails loudly is
  better than a `pass` you will never revisit.
- `test_a_pipeline_is_one_trace_not_two` — this is the **flip-it test** of the day, and the flip is
  written into the docstring. Remove the `with trace(...)` and you get two files; that is how you
  prove the line does something rather than believing this lesson.
- `test_the_trace_file_never_contains_the_canary` — yesterday's canary, one layer deeper. Yesterday
  you kept it out of an agent's context; today out of a file that persists after the process ends.
  **The second one is the more dangerous leak**, because it survives.
- Every test above except the last two costs **0 model requests.** The configuration and redaction
  properties live in data structures and pure functions, which is exactly why they were worth putting
  there.

---

## §6 Traps

- **Leaving Day 9's `set_tracing_disabled(True)` in place.** You install your processor, it receives
  nothing, and you spend forty minutes debugging the processor. **The trap of the day.**
- **`add_trace_processor` instead of `set_trace_processors`.** The OpenAI exporter is still installed
  and still trying. Free-tier project, spans heading for a service you have no key for.
- **No `with trace(...)` around the pipeline.** Two `Runner.run` calls, two traces, and no way to see
  that one followed the other. The pipeline becomes invisible exactly where it is interesting.
- **No flush before exit.** Harmless with today's synchronous writer, fatal the day you swap in a
  batching exporter. Empty trace file, working code.
- **Writing tool output verbatim into the trace.** You spent yesterday keeping the ticket body away
  from the Resolver, then wrote it to a file that outlives the process. Allowlist, always.
- **`.mandala/` not in `.gitignore`.** Now you have committed customer text to a public repo. Do this
  in §2, before the first run.
- **Raising inside a processor hook.** A tracing bug ends a real run. Swallow, log, continue.
- **Comparing topologies without `temperature=0.0`.** Day 9 pinned it; if you unpin it to "make the
  supervisor smarter", your comparison measures noise.
- **Reading a span tree as a cost report.** Spans count *calls*. Tokens need `include_usage=True`
  (Day 9) and arrive properly on Day 71. A short span can be an expensive one.
- **`max_turns` sized for the pipeline, reused for the supervisor.** The supervisor spends turns
  deciding; too low a budget and it dies mid-plan, which reads like a model failure and is not.
- **Concluding the supervisor "works" from one run.** Run it five times and count. One sample of a
  probabilistic router is not a result.
- **Building a state machine out of `custom_span` and helper functions.** When you notice you are
  writing edges, stop and re-read §3.6.

---

## §7 Request budget

| Activity | Requests |
|---|---|
| `pipeline_demo.py` | ~5 (Groq) |
| `supervisor_demo.py` | ~8 (Groq) |
| The ordering experiment — supervisor × 5 | ~40 (Groq) |
| Cassette recording for the two traced tests | ~13 |
| **Total** | **≈ 66, Groq** |

The heaviest day of the phase so far, and all of it in one place: the ×5 ordering experiment. **Do
not skip it** — it is the only part of today that produces a number rather than an opinion. If your
Groq budget is tight, drop the cassette re-records instead and reuse yesterday's.

`span_tree.py` and every configuration/redaction test cost **0** — they read a file.

---

## §8 Verify before you code

Written **2026-08-20** against `openai-agents` **0.22.0**.

- `https://openai.github.io/openai-agents-python/tracing/` — the trace/span model, which spans the
  SDK creates automatically, and the `trace()` signature (`workflow_name`, `trace_id`, `group_id`,
  `metadata`). **Confirm that wrapping several `Runner.run` calls in one `trace()` is still the
  documented way to make them one workflow.**
- `https://openai.github.io/openai-agents-python/ref/tracing/processor_interface/` — the
  `TracingProcessor` method names. If `force_flush`/`shutdown` are abstract, you must implement them
  even as no-ops.
- `https://openai.github.io/openai-agents-python/ref/tracing/span_data/` — **the field names per span
  data type.** This is the surface today's code is most likely to be wrong about. Print
  `vars(span.span_data)` and trust that over this lesson.
- `https://openai.github.io/openai-agents-python/ref/tracing/setup/` — `set_trace_processors` vs.
  `add_trace_processor`, and **the accessor for the currently installed processors** (that is the
  `TODO(me)` in `test_no_processor_points_at_openai`, and the answer to Day 9's open question).
- `https://openai.github.io/openai-agents-python/multi_agent/` — the SDK's own words on
  orchestration-by-LLM vs. orchestration-by-code. Compare with §3.6 and note where you disagree;
  that disagreement is ADR-001 material.
- **A real one to check:** we run through `LitellmModel`, not OpenAI's Responses API. Confirm what
  the model call produces — a **generation** span or a **response** span. `model_calls()` in
  `span_tree.py` matches on `"Generation"`, and if your provider produces the other kind, your count
  is silently zero. **Check this before you trust any number you write in the CHECKLIST.**
- If any of the above differs from this lesson: log one line in `docs/CHANGELOG_PLAN.md`. If a whole
  mechanism has moved, stop and write an addendum first (Principle 14).

---

## §9 Say it in an interview

> "The Agents SDK gives you two orchestration primitives — handoffs and agents-as-tools — and those
> get you peer-handoff and supervisor topologies. A pipeline isn't a framework feature at all; it's
> two `Runner.run` calls in a function, because a pipeline is the one shape where the model owns no
> control, and the SDK's whole thesis is that the model owns the loop. So the real design question is
> where the ordering constraint lives: in my Python, or in a sentence in a prompt. I built both on
> the same ticket. The pipeline's guarantee is structural — I can assert it in a unit test. The
> supervisor's is best-effort — I can only observe it in a trace. I ran the supervisor five times and
> counted how often it called the tools in the order I asked for."

> "Tracing on this project had a constraint: zero budget, and the SDK's default processor uploads
> spans to OpenAI, which needs a paid key. Early on I'd just called `set_tracing_disabled(True)`,
> which stopped the noise and also threw away every span — so I was violating 'the trace is the
> truth' to save a key I was never going to buy. The fix was `set_trace_processors`, replacing the
> list rather than adding to it, with a thirty-line JSONL processor. Two things I'd defend: the
> processor swallows every exception, because instrumentation that can kill a run is worse than no
> instrumentation; and what it writes is an allowlist, not a denylist, because a trace file is
> customer text living on disk forever. I have a test asserting that a canary token from a ticket
> body never appears in a trace file. And because a processor is the same shape as an OTel exporter,
> the destination is one class swap — the workflow names, custom spans and group ids all survive."

---

## §10 Done when

```bash
./m check
./m done 14
```

Tomorrow: web and file search — the hosted versions are paid, so you build the free equivalents and
find out what you actually lose.
