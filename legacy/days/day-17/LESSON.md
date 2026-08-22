---
day: 17
phase: 3
phase_name: "OpenAI Agents SDK advanced"
title: "Streaming, and why users forgive latency they can see"
ids: ["OAI-16", "AG-28"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 17 — Streaming, and why users forgive latency they can see

**Phase 3 · OpenAI Agents SDK advanced** · IDs: **OAI-16 🛠️**, **AG-28 🅿️**

> **Yesterday:** the Phase-2 gate — the first MCP mount, and ADR-001 *"what the SDK owns vs. what I
> own"*.
> **Today:** Phase 3 opens with the feature that looks like polish and is actually architecture —
> `run_streamed`, its three event families, and the three things streaming quietly breaks.
> **Tomorrow:** programmatic tool calling 🅿️ and the free coordinator tool that does the same job.

```bash
./m start 17
./m scaffold 17
```

---

## §1 The story

Phase 2 was about making an agent *correct*. Phase 3 is about making it *survivable* — long runs,
sandboxes, durability, and the surfaces a human watches while it works. Today is the first of those,
and it is the one people mistake for a UI ticket.

Here is the fact that makes it not a UI ticket. Your Day-14 pipeline takes somewhere around five to
eight seconds on Groq. A supervisor run takes more. In a terminal that is fine. In front of a support
operator with forty tickets to clear, eight seconds of a blank screen is the difference between a
tool they use and a tool they alt-tab away from — and the *identical* eight seconds, with a line
appearing that says `calling get_ticket…`, is a tool that feels fast.

> **Streaming does not make anything faster. It moves the moment the user stops wondering whether it
> is broken.**

That is AG-28 in one sentence, and it is worth saying out loud because it also tells you what
streaming costs. Nothing about the run changes: same tokens, same requests, same rate limit
(Principle 5). What changes is that **partial, unvalidated output leaves your process.** And that
collides, hard, with three things you built in the last week:

- **Day 11's `output_type=Brief`.** You cannot render half of a validated object.
- **Day 12's output guardrails.** They run *after* the output exists. If you already streamed it, a
  tripped guardrail is a retraction, not a block.
- **Day 6's router and Principle 5.** A 429 that used to arrive before anything was displayed now
  arrives in the middle of a sentence.

§3 builds the streaming. §4 is about those three collisions, and §4 is the part that makes this a
senior answer instead of a demo.

---

## §2 Setup — run this

One new package. It has no key, no account, and no network:

```bash
uv add "rich==15.0.0"
```

`rich` is in the `docs/PINS.md` dependency ledger at **Day 17** already — no ledger change needed
today. Pin whatever actually resolves and log one line if it differs (Principle 4).

```bash
mkdir -p days/day-17/lab
touch src/mandala/streaming.py
touch days/day-17/lab/naked_stream.py
touch days/day-17/lab/stream_demo.py
touch days/day-17/lab/first_token.py
touch tests/test_streaming.py
touch tests/test_stream_guardrails.py
```

Nothing else moves today. `src/mandala/sdk.py`, `topologies.py`, `guardrails.py` and yesterday's MCP
mount are all untouched — **streaming is additive**, and one of the nicer things about the SDK is
that you do not rewrite an agent to stream it. You change the call site.

---

## §3 OAI-16 — `run_streamed` and the three event families

### 3.1 Naked first — streaming is a `for` loop over chunks

Principle 2: before the framework version, the raw one. Day 3 built the agent loop with the plain
`openai` client pointed at Groq. Streaming is that same call with one extra keyword.

`days/day-17/lab/naked_stream.py`:

```python
"""Streaming with no framework at all. One keyword argument and a for-loop.

Day 3 built the loop with the plain openai client against Groq's OpenAI-compatible
endpoint. This is that call with stream=True, so that when the SDK hands you an
"event stream" you already know what is underneath it: an HTTP response that has
not finished, being read a chunk at a time.

Run:
    uv run python days/day-17/lab/naked_stream.py
"""

from __future__ import annotations

import time

from openai import OpenAI

from mandala.config import load_keys
from mandala.models import PROVIDERS

PROMPT = "In four sentences, explain what a refund hold is to a support agent."


def main() -> None:
    provider = PROVIDERS["groq"]
    client = OpenAI(
        api_key=getattr(load_keys(), provider.key_attr),
        base_url=provider.base_url,
    )

    started = time.monotonic()
    first_token_at: float | None = None
    chunks = 0
    text: list[str] = []

    stream = client.chat.completions.create(
        model=provider.default_model,
        messages=[{"role": "user", "content": PROMPT}],
        temperature=0.0,
        stream=True,
    )

    for chunk in stream:
        piece = chunk.choices[0].delta.content or ""
        chunks += 1
        if piece and first_token_at is None:
            first_token_at = time.monotonic()
        text.append(piece)
        print(piece, end="", flush=True)

    total = time.monotonic() - started
    ttft = (first_token_at - started) if first_token_at else total

    print(f"\n\nchunks           : {chunks}")
    print(f"time to first tok: {ttft * 1000:>7.0f} ms")
    print(f"total            : {total * 1000:>7.0f} ms")
    print(f"characters       : {len(''.join(text))}")


if __name__ == "__main__":
    main()
```

**Line by line:**

- `stream=True` and nothing else. **That is the entire mechanism.** The server stops sending one JSON
  body at the end and starts sending server-sent events as it generates. Everything the Agents SDK
  does today is layered on this one flag, and knowing that stops you treating `stream_events()` as
  magic.
- `getattr(load_keys(), provider.key_attr)` — Day 6 put `key_attr` on the provider spec exactly so
  that code does not hard-code `.groq`. Day 3's demo did hard-code it; this is the corrected habit.
- `chunk.choices[0].delta.content or ""` — **`delta`, not `message`.** A streamed chunk carries the
  *difference*, and the difference is very often empty (role-only first chunk, finish-reason last
  chunk). The `or ""` is not defensive noise; it is the shape of the protocol. Remember this in §3.5
  when the SDK's raw events do the same thing.
- `first_token_at` is set on the first **non-empty** piece. If you set it on the first chunk you will
  measure the role chunk and report a time-to-first-token that is a lie by 200 ms. Small bug, and it
  is the exact bug that makes benchmark blog posts disagree.
- `print(piece, end="", flush=True)` — without `flush=True` Python's buffering hides the whole point
  of the exercise and you conclude streaming does not work.
- `text.append(piece)` then `"".join(...)` at the end — **the reducer, in its most primitive form.**
  Streaming always has two consumers: the thing that renders each piece, and the thing that
  reassembles the whole. §3.5 turns that observation into a module.
- `temperature=0.0` — Day 9's pin. §3.8 compares a streamed and a non-streamed run and that
  comparison is meaningless if the sampler is free to disagree with itself.

Run it. Watch the text appear. **Then note the number you cannot get any other way:** the gap between
time-to-first-token and total is the amount of waiting you are about to give back to the user.

### 3.2 `run` vs. `run_sync` vs. `run_streamed`

Day 10 built this table and left the third row for today:

| Call | Returns | You await… | Notes |
|---|---|---|---|
| `Runner.run(agent, input, ...)` | awaitable `RunResult` | **the whole run** | the default everywhere |
| `Runner.run_sync(agent, input, ...)` | `RunResult` | nothing, it blocks | quick scripts |
| `Runner.run_streamed(agent, input, ...)` | a **streaming result object** | **nothing — it returns immediately** | today |

Read row three carefully, because it is the single most common `run_streamed` bug:

> **`Runner.run_streamed(...)` is not awaited.** It returns a result object straight away and the run
> happens *while you consume* `result.stream_events()`. Nothing progresses until you start iterating,
> and `result.final_output` is only meaningful once the iterator is exhausted.

```python
# WRONG — this is the mistake everybody makes once
result = await Runner.run_streamed(agent, "Research T-1004")   # TypeError, or worse: silence

# RIGHT
result = Runner.run_streamed(agent, "Research T-1004", context=ctx, max_turns=8)
async for event in result.stream_events():
    ...
print(result.final_output)      # valid only now
```

**Line by line:**

- The wrong version fails loudly if the object is not awaitable, and fails *quietly* if you wrapped it
  in something that swallows it. Either way you get a "streaming does nothing" bug whose cause is one
  keyword.
- `result.final_output` after the loop — the SDK still gives you the same finished `RunResult` surface
  you know from Day 10 (`final_output`, `new_items`, `last_agent`). **Streaming is a second view of
  the same run, not a different run.** §5 asserts exactly that.
- `max_turns=8` is still a request budget (Day 10). Streaming does not change how many model calls the
  loop makes; see §4.4.

### 3.3 The three event families

Everything `stream_events()` yields belongs to one of three families. Learn them by *audience*, not
by class name:

| Family | `event.type` | Granularity | Who it is for | Arrives |
|---|---|---|---|---|
| **Raw model deltas** | `raw_response_event` | one token / one chunk | **the eyeball** | continuously, hundreds per run |
| **Run items** | `run_item_stream_event` | one *completed* thing — a tool was called, a tool returned, a message was produced, a handoff happened | **the program** | a handful per run |
| **Agent updated** | `agent_updated_stream_event` | control moved to a different agent | both | once per handoff |

The third family is Day 13 and Day 14, live. `agent_updated_stream_event` is the streaming form of
`result.last_agent` — instead of finding out at the end which agent was driving, you find out at the
moment it changes. In a Day-14 supervisor topology it never fires (control never leaves); in a Day-13
handoff it fires exactly when the transfer happens. **If you want to see a topology's shape at run
time rather than in a span tree, this is the event.**

And now the distinction that is the actual content of §3:

> **Raw deltas are for the eyeball. Run-item events are for the program.**

Most people render the first and log the second. Mixing them up produces two specific failures, and
you will recognise both:

| Mistake | What it looks like |
|---|---|
| Driving your **program** off raw deltas | you parse tool names out of streamed JSON fragments, your UI flickers between half-written words, and one retry doubles a line |
| Driving your **display** off run items only | correct, queryable, and the screen sits still for four seconds at a time — you have rebuilt the spinner with extra steps |
| Logging raw deltas | a log with 900 lines per run that you cannot query and that contains every token of customer-facing text on disk (Day 14's allowlist, undone) |

**Render deltas. Log items. Never the other way round.**

### 3.4 The seam — why you do not hand SDK events to a renderer

You have now built this twice:

- **Day 14**, `tracing.summarise()`: the SDK's span objects never reach your JSONL file. An allowlist
  converts them into *your* record shape first.
- **Day 15**, `kb.search()`: a fixed signature over a body that Day 46 will replace entirely.

Today is the third, and by now it should feel automatic:

> **`mandala.streaming` converts the SDK's event stream into Mandala's own bounded, typed progress
> events. The renderer and the tests consume *your* type, never the SDK's.**

Three concrete reasons, in order of how much they will actually bite you:

1. **Testability.** You cannot construct an SDK stream event in a unit test without either a model
   call or a pile of mocks. You can construct a `TokenDelta(text="hi")` in one line. Everything
   downstream of the classifier is therefore testable at **0 model requests** — and §5 is 0 requests
   except for one cassette.
2. **Version drift.** The exact event class names and attribute paths are the least stable surface in
   the SDK. Day 14 already taught you this with `span_data`. One function knows them; §8 tells you to
   verify that one function.
3. **Boundedness.** A raw delta stream is unbounded by construction. Every field of yours is capped
   before anything accumulates — Day 4's context-budget discipline, applied to a buffer that grows one
   token at a time.

### 3.5 `src/mandala/streaming.py`

```python
"""Mandala's own progress events. The SDK's stream is an input, not an interface.

Runner.run_streamed() yields three families of event: raw model deltas
(token-level), run-item events (a tool was called, a message was produced, a
handoff happened) and agent-updated events (which agent is driving now).
Different granularity, different audience, different lifetime.

This module is a SEAM, the same one tracing.summarise() is (Day 14) and
kb.search() is (Day 15): one function converts the vendor's stream into OUR
typed events, and the renderer, the tests and tomorrow's coordinator all consume
ours. The SDK's class names appear in exactly one place in this project — below.

Two rules the classifier keeps, and §5 asserts both:

  1. NOTHING IS DROPPED SILENTLY. An event this module has no opinion about
     becomes an Unclassified carrying its type name, and the reducer counts it.
     A version bump then shows up as a number on screen instead of as silence.
  2. NOTHING IS UNBOUNDED. Deltas, labels and the accumulated answer are all
     capped. A stream is the one place where "it is only a string" is false.

Usage
-----
    >>> from mandala.streaming import ProgressReducer, TokenDelta
    >>> reducer = ProgressReducer()
    >>> reducer.apply(TokenDelta(text="hello "))
    >>> reducer.apply(TokenDelta(text="world"))
    >>> reducer.answer
    'hello world'
"""

from __future__ import annotations

import time
from collections import Counter
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

MAX_DELTA_CHARS = 2_000        # one chunk. Generous; a hostile provider is still bounded.
MAX_LABEL_CHARS = 120          # a tool name plus a hint, not a payload.
MAX_ANSWER_CHARS = 20_000      # the whole accumulated answer. Day 4's budget, streamed.


class TokenDelta(BaseModel):
    """A fragment of model text. FOR THE EYEBALL. Never log these individually."""

    kind: Literal["token"] = "token"
    text: str = Field(max_length=MAX_DELTA_CHARS)


class ItemDone(BaseModel):
    """One completed thing: a tool call, a tool output, a message, a handoff.

    FOR THE PROGRAM. This is what you log, count, assert on and alert from.
    """

    kind: Literal["item"] = "item"
    item_type: str = Field(max_length=64)
    label: str = Field(default="", max_length=MAX_LABEL_CHARS)


class AgentSwitched(BaseModel):
    """Control moved. The streaming form of RunResult.last_agent (Day 13)."""

    kind: Literal["agent"] = "agent"
    agent_name: str = Field(max_length=64)


class Unclassified(BaseModel):
    """An event this module has no opinion about. Counted, never dropped."""

    kind: Literal["unclassified"] = "unclassified"
    raw_type: str = Field(max_length=120)
    detail: str = Field(default="", max_length=120)


ProgressEvent = Annotated[
    TokenDelta | ItemDone | AgentSwitched | Unclassified,
    Field(discriminator="kind"),
]


def label_for(item: Any) -> str:
    """A short human label for a run item — usually the tool name.

    TODO(me): today's rep. In 0.22.0, a run item wraps a raw_item whose shape
    differs per item type: a tool call carries a name, a message output carries
    content, a handoff carries a target. Print one of each:

        async for event in result.stream_events():
            if event.type == "run_item_stream_event":
                print(type(event.item).__name__, vars(event.item))

    Then write the lookup. Rules: return "" rather than raising, and slice to
    MAX_LABEL_CHARS — a label is a caption, and a caption that can contain a
    customer's sentence is Day 14's allowlist lesson unlearned.
    """
    raise NotImplementedError


def _delta_text(data: Any) -> str | None:
    """Pull the text fragment out of a raw response event's payload, or None.

    TODO(me): the second rep, and the least stable line in this project. In
    0.22.0 a raw_response_event's `data` is an OpenAI Responses streaming event;
    only some of them carry text. Confirm the discriminator (data.type ==
    "response.output_text.delta"?) and the attribute (data.delta?) against a
    LIVE run through LitellmModel on Groq — see §8, because the Responses event
    names are the surface most likely to differ per provider.

    Return None for anything that is not text. Returning "" would make an empty
    delta indistinguishable from a non-text event, and §5 tests the difference.
    """
    raise NotImplementedError


def classify(event: Any) -> ProgressEvent:
    """The ONLY function in Mandala that knows the SDK's event vocabulary."""
    event_type = str(getattr(event, "type", "") or type(event).__name__)

    if event_type == "raw_response_event":
        data = getattr(event, "data", None)
        text = _delta_text(data)
        if text is None:
            return Unclassified(raw_type=event_type, detail=type(data).__name__[:120])
        return TokenDelta(text=text[:MAX_DELTA_CHARS])

    if event_type == "run_item_stream_event":
        item = getattr(event, "item", None)
        return ItemDone(
            item_type=str(getattr(item, "type", "unknown_item"))[:64],
            label=label_for(item)[:MAX_LABEL_CHARS],
        )

    if event_type == "agent_updated_stream_event":
        agent = getattr(event, "new_agent", None)
        return AgentSwitched(agent_name=str(getattr(agent, "name", "?"))[:64])

    return Unclassified(raw_type=event_type[:120])


class ProgressReducer:
    """Folds a stream of ProgressEvents into the state a surface needs.

    The renderer asks it questions; the tests assert on it; neither of them ever
    touches an SDK object. It is deliberately synchronous and deliberately dumb:
    a reducer that can raise is a reducer that can kill a run mid-render.
    """

    def __init__(self, *, max_answer_chars: int = MAX_ANSWER_CHARS) -> None:
        self._max = max_answer_chars
        self.started_at = time.monotonic()
        self.answer = ""
        self.truncated = False
        self.items: list[ItemDone] = []
        self.agents: list[str] = []
        self.unclassified: Counter[str] = Counter()
        self.first_token_at: float | None = None
        self.first_progress_at: float | None = None

    def feed(self, event: Any) -> ProgressEvent:
        """Classify one SDK event and fold it in. Returns OUR type, for rendering."""
        progress = classify(event)
        self.apply(progress)
        return progress

    def apply(self, progress: ProgressEvent) -> None:
        """Fold one already-classified event. Pure; no SDK, no IO, no raise."""
        if self.first_progress_at is None and not isinstance(progress, Unclassified):
            self.first_progress_at = time.monotonic()

        match progress:
            case TokenDelta(text=text):
                if self.first_token_at is None:
                    self.first_token_at = time.monotonic()
                room = self._max - len(self.answer)
                if room <= 0:
                    self.truncated = True
                else:
                    self.answer += text[:room]
                    self.truncated = self.truncated or len(text) > room
            case ItemDone():
                self.items.append(progress)
            case AgentSwitched(agent_name=name):
                self.agents.append(name)
            case Unclassified(raw_type=raw):
                self.unclassified[raw] += 1

    @property
    def tool_calls(self) -> list[str]:
        """Tool names, read from RUN ITEMS — never parsed out of token deltas."""
        return [i.label for i in self.items if i.item_type == "tool_call_item" and i.label]

    @property
    def ttft_ms(self) -> float | None:
        """Time to first *token*. None until the model has emitted text."""
        if self.first_token_at is None:
            return None
        return (self.first_token_at - self.started_at) * 1000

    @property
    def first_progress_ms(self) -> float | None:
        """Time to the first thing worth showing a human. Usually earlier than ttft."""
        if self.first_progress_at is None:
            return None
        return (self.first_progress_at - self.started_at) * 1000

    def elapsed_ms(self) -> float:
        return (time.monotonic() - self.started_at) * 1000


# --- Where streamed text is allowed to go (Principle 12) ----------------------

STREAM_SINKS: dict[str, bool] = {
    "operator": True,     # a human reviewer, inside the building
    "customer": False,    # never. See §4.3.
}


class StreamWithheld(RuntimeError):
    """Raised when text would reach a customer before its guardrails have spoken."""


def may_stream(channel: str) -> bool:
    """Unknown channels are NOT streamable. The safe thing must be the default."""
    return STREAM_SINKS.get(channel, False)


def deliver(text: str, *, channel: str, guardrails_ran: bool, tripped: bool) -> str:
    """The only function allowed to hand model text to a channel.

    Day 12's output guardrails run AFTER the output exists. Streaming to a
    customer therefore means publishing text that has not been checked yet, and
    a tripped guardrail becomes a retraction instead of a block. Mandala's
    answer is the one Principle 12 already implies: drafts stream to the
    operator; the customer receives a message a human released.
    """
    if may_stream(channel):
        return text
    if not guardrails_ran:
        raise StreamWithheld(f"{channel}: text released before output guardrails ran")
    if tripped:
        raise StreamWithheld(f"{channel}: output guardrail tripped; nothing is released")
    return text
```

**Line by line:**

- The module docstring **numbers the two rules and says §5 asserts both.** Day 15's `search.py` ranked
  its defences for the same reason: a reader six weeks from now needs to know which line is load
  bearing before they optimise it away.
- Four Pydantic models rather than one with an `Optional` everything — **a discriminated union makes
  "what kind of event is this" a type question instead of a `None` check.** The renderer's `match`
  statement in §3.6 is exhaustive because of this choice; a single wide model would have given you
  `if event.text is not None` and no exhaustiveness at all.
- The docstrings on `TokenDelta` and `ItemDone` carry **FOR THE EYEBALL** / **FOR THE PROGRAM** in
  capitals. §3.3's rule is the kind of thing people forget in three weeks, so it lives in the type,
  where a reader meets it while making the mistake.
- `MAX_DELTA_CHARS`, `MAX_LABEL_CHARS`, `MAX_ANSWER_CHARS` as module constants — same shape as Day
  15's `MAX_SNIPPET_CHARS`. **A stream is the one place where "it's only a string" is false**: the
  answer buffer is the only object in this project that grows on every single model chunk.
- `Unclassified` **is the decision, and it is deliberate.** The alternative — dropping events the
  classifier does not recognise — is what everyone writes, and it means the day the SDK renames
  `raw_response_event` your UI simply goes blank and you debug the renderer. Note the honest wrinkle:
  ordinary lifecycle chunks (a response-created event, a finish chunk) land here too. That is fine.
  `Unclassified` means *this module has no opinion*, not *this is a bug* — and because the reducer
  keeps a `Counter` by `raw_type`, "no opinion" is a printable histogram rather than silence.
- `label_for` and `_delta_text` are **`TODO(me)`, and they are the two reps of the day.** They are the
  only two functions whose correctness depends on 0.22.0's exact class and attribute names, which is
  precisely why they are yours to discover rather than mine to assert. Guessing gets you an
  `AttributeError`; printing one event gets you the answer in ten seconds. This is Day 14's
  `vars(span.span_data)` lesson, second occurrence.
- `_delta_text` returns **`None`, not `""`**, for a non-text event — and the docstring says why. An
  empty delta is a real thing (models emit them); "this event carries no text at all" is a different
  thing. Collapsing the two makes §5's exhaustiveness test unwritable.
- `classify` is **the only function in the project that names an SDK event type.** Count the string
  literals: three. That number is the migration cost of the next SDK version, and you can see it.
- `getattr(event, "type", "") or type(event).__name__` — a fallback so that even a completely foreign
  object produces a *named* `Unclassified` rather than an exception. Rule 1, enforced at the boundary.
- `ProgressReducer` is **synchronous and cannot raise**, and that is a copy of Day 14's decision that
  `_write` swallows everything. Instrumentation and rendering must degrade, never explode; the
  difference is that a tracing bug loses a file and a renderer bug kills a run the user is watching.
- `first_progress_at` is set for anything that is **not** `Unclassified`. This is the number AG-28
  actually cares about: not "when did text appear" but "when did the screen stop being a lie". In a
  tool-using run the first run-item event beats the first token by seconds, and §3.7 measures it.
- `room = self._max - len(self.answer)` — bounded accumulation with an explicit `truncated` flag. A
  silent truncation in a streamed answer is invisible: the user sees text that just… stops. **Set the
  flag, and make the renderer show it.**
- `match progress: case TokenDelta(text=text)` — structural pattern matching on the union. If you add
  a fifth event type later and forget a `case`, the reducer silently ignores it — which is why §5's
  exhaustiveness test enumerates the union's members rather than trusting this `match`.
- `tool_calls` reads `item_type == "tool_call_item"` — **the program's view, sourced from run items.**
  The tempting alternative is scanning `self.answer` for tool JSON. Do not; that is §3.3's first
  failure mode, and it breaks the first time a model writes the word "get_ticket" in prose.
- `ttft_ms` returns `None` before the first token instead of `0.0`. `0.0` means "instant"; `None`
  means "has not happened". §5 asserts this because a dashboard that reports 0 ms is a dashboard that
  gets believed.
- `STREAM_SINKS` / `may_stream` / `deliver` at the bottom look like they belong in `guardrails.py`,
  and they are here on purpose: **the rule about where streamed text may go is part of the streaming
  contract, not an afterthought bolted on by a caller.** `may_stream` uses `.get(channel, False)` —
  an unknown channel is not streamable. That is the fourth appearance of "the safe thing is what
  happens when you forget" (Day 12's `approvals_required=True`, Day 13's `filtered=True`, Day 15's
  autouse offline fixture, now this).
- `deliver` raises rather than returning `""` — Day 12's tripwire model. A caller that ignores a
  return value is common; a caller that ignores an exception is not.

### 3.6 `days/day-17/lab/stream_demo.py` — the surface

```python
"""Watch a run happen: tool calls as they fire, tokens as they arrive.

Run:
    uv run python days/day-17/lab/stream_demo.py T-1004

Note what this agent does NOT have: output_type=Brief. You cannot render a
partial validated object (§4.2), so the streaming demo runs the prose Researcher
and the Day-14 pipeline keeps the typed one. That is a real trade, not a
simplification for the demo.
"""

from __future__ import annotations

import asyncio
import sys

from agents import Agent, Runner
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from mandala.agents import RESEARCHER_PROMPT
from mandala.context import MandalaContext
from mandala.sdk import DEFAULT_SETTINGS, make_model
from mandala.sdk_tools import get_ticket, search_tickets
from mandala.streaming import ProgressReducer
from mandala.tracing import install_local_tracing

console = Console()


def streaming_researcher() -> Agent:
    """Day 14's Researcher, minus output_type. Same tools, same blast radius."""
    return Agent(
        name="Researcher",
        instructions=RESEARCHER_PROMPT.render(),
        model=make_model("groq"),
        model_settings=DEFAULT_SETTINGS,
        tools=[get_ticket, search_tickets],
    )


def frame(reducer: ProgressReducer) -> Group:
    """Build the whole display from reducer state. Pure; called ~10x a second."""
    ttft = f"{reducer.ttft_ms:.0f}ms" if reducer.ttft_ms else "--"
    first = f"{reducer.first_progress_ms:.0f}ms" if reducer.first_progress_ms else "--"
    header = Text(
        f"agent {reducer.agents[-1] if reducer.agents else 'Researcher':<12}"
        f"elapsed {reducer.elapsed_ms() / 1000:5.1f}s   "
        f"first progress {first:>8}   first token {ttft:>8}",
        style="dim",
    )

    steps = Text()
    for item in reducer.items:
        steps.append(f"  * {item.item_type:<22} {item.label}\n", style="cyan")
    if reducer.unclassified:
        steps.append(f"  ? unclassified: {dict(reducer.unclassified)}\n", style="yellow")

    body = Text(reducer.answer or "waiting for the model...")
    if reducer.truncated:
        body.append("\n[TRUNCATED at the answer cap]", style="bold red")

    return Group(header, steps, Panel(body, title="draft (operator surface only)"))


async def main() -> None:
    ticket_id = sys.argv[1] if len(sys.argv) > 1 else "T-1004"
    processor = install_local_tracing()

    context = MandalaContext(actor="agent:researcher", request_id=f"req-{ticket_id}")
    reducer = ProgressReducer()

    result = Runner.run_streamed(          # NOT awaited
        streaming_researcher(),
        f"Research ticket {ticket_id}.",
        context=context,
        max_turns=8,
    )

    with Live(frame(reducer), console=console, refresh_per_second=10) as live:
        async for event in result.stream_events():
            reducer.feed(event)
            live.update(frame(reducer))

    processor.force_flush()

    console.print(f"\ntool calls (from run items): {reducer.tool_calls}")
    console.print(f"unclassified event types   : {dict(reducer.unclassified)}")
    console.print(f"reducer answer == final_output: "
                  f"{reducer.answer.strip() == str(result.final_output).strip()}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- `streaming_researcher()` deliberately **drops `output_type=Brief`**, and the module docstring says
  so before you can wonder. This is not a shortcut — it is §4.2 arriving early. The moment an agent
  has a typed output there is nothing meaningful to stream token-by-token, so the day's demo and the
  day's pipeline are genuinely different agents. Notice what did *not* change: the tool list, and
  therefore the blast radius (Day 8, Day 14). **Streaming changed the view, not the permissions.**
- `RESEARCHER_PROMPT.render()` reused from Day 8's `prompts.py` — the prompt is versioned there and
  copying it into a lab file would fork it. One prompt, one home.
- `frame()` is a **pure function of reducer state**, and that is the whole reason `rich.Live` behaves.
  `Live` re-renders whatever you hand it; if your frame function has side effects or reads a global,
  you get flicker and duplicated lines and you blame `rich`. Build the frame from state, every time.
- `refresh_per_second=10` — **not per event.** Groq will hand you hundreds of deltas a second; a
  terminal repaint per delta is how you turn a fast model into a slow-looking UI. Ten frames a second
  is above the threshold where a human perceives continuous motion and far below the rate at which a
  terminal struggles.
- `reducer.first_progress_ms` and `reducer.ttft_ms` are **both on screen**, side by side. Watch a
  tool-using run: `first progress` lands while `first token` is still `--`, sometimes for two or three
  seconds. That gap is AG-28's entire product argument, rendered.
- The `unclassified` line is printed in yellow in the *live* frame, not hidden in a log. Rule 1 of the
  module, made visible: if a version bump reclassifies half the stream, you see a yellow line the
  first time you run it instead of six weeks later.
- `Panel(..., title="draft (operator surface only)")` — the title is a **label on a security
  property**, in the place where someone might be tempted to pipe this into a customer chat widget.
  §4.5 is the argument; this is the reminder at the point of temptation.
- `Runner.run_streamed(...)` with **no `await`**, and the comment says so. §3.2's bug, immunised.
- `async for event in result.stream_events()` **inside** the `with Live(...)` block — leaving the
  block finalises the display. Also: `stream_events()` is a one-shot async iterator. Consume it once;
  a second `async for` over the same result gets you nothing and a confusing hour.
- `processor.force_flush()` **after** the `Live` block, not inside — Day 14's tracing still runs, and
  streaming does not change what gets traced. Nice property to notice: a streamed run produces the
  same span tree as a blocking one, so `span_tree.py` still works today unchanged.
- `console.print(...)` rather than `print(...)` — mixing bare `print` with a live display is the
  classic `rich` mess, and it happens *after* the block here anyway. Keep one output channel.
- The last line asserts, informally, the property §5 tests properly: **your reducer rebuilt exactly
  what the SDK produced.** If that prints `False`, your `_delta_text` is dropping something and you
  want to know now, not in a test at the end of the day.

### 3.7 `days/day-17/lab/first_token.py` — today's number

Day 14 made you run the supervisor five times and count orderings. Day 15 made you count injection
relays. Today's number is **time-to-first-anything versus total**, and you must write it in the
CHECKLIST.

```python
"""Measure what streaming actually buys: the wait, not the work.

Run:
    uv run python days/day-17/lab/first_token.py T-1004

Costs 2 full runs per repeat. Read §7 before you raise REPEATS.
"""

from __future__ import annotations

import asyncio
import sys
import time

from agents import Runner
from rich.console import Console
from rich.table import Table

from mandala.context import MandalaContext
from mandala.streaming import ProgressReducer

from stream_demo import streaming_researcher   # same agent, same tools, same pins

REPEATS = 2
console = Console()


async def blocking_run(ticket_id: str) -> dict:
    """The Day-10 call. Nothing is visible until everything is finished."""
    context = MandalaContext(actor="agent:researcher", request_id=f"req-{ticket_id}")
    started = time.monotonic()
    result = await Runner.run(
        streaming_researcher(), f"Research ticket {ticket_id}.",
        context=context, max_turns=8,
    )
    total_ms = (time.monotonic() - started) * 1000
    return {
        "mode": "Runner.run",
        "first_progress_ms": total_ms,   # by definition: the first thing you see IS the answer
        "ttft_ms": total_ms,
        "total_ms": total_ms,
        "chars": len(str(result.final_output)),
    }


async def streamed_run(ticket_id: str) -> dict:
    """The same run, watched."""
    context = MandalaContext(actor="agent:researcher", request_id=f"req-{ticket_id}")
    reducer = ProgressReducer()
    result = Runner.run_streamed(
        streaming_researcher(), f"Research ticket {ticket_id}.",
        context=context, max_turns=8,
    )
    async for event in result.stream_events():
        reducer.feed(event)
    return {
        "mode": "Runner.run_streamed",
        "first_progress_ms": reducer.first_progress_ms,
        "ttft_ms": reducer.ttft_ms,
        "total_ms": reducer.elapsed_ms(),
        "chars": len(reducer.answer),
    }


def render(rows: list[dict]) -> Table:
    table = Table(title="what streaming buys (ms)")
    for column in ("mode", "first progress", "first token", "total", "chars"):
        table.add_column(column, justify="right")
    for row in rows:
        table.add_row(
            row["mode"],
            f"{row['first_progress_ms']:.0f}" if row["first_progress_ms"] else "--",
            f"{row['ttft_ms']:.0f}" if row["ttft_ms"] else "--",
            f"{row['total_ms']:.0f}",
            str(row["chars"]),
        )
    return table


async def main() -> None:
    ticket_id = sys.argv[1] if len(sys.argv) > 1 else "T-1004"
    rows: list[dict] = []
    for _ in range(REPEATS):
        rows.append(await blocking_run(ticket_id))
        rows.append(await streamed_run(ticket_id))
    console.print(render(rows))

    # TODO(me): the third rep. Decide what "first progress" MEANS for a blocking
    # run and defend it. This file says "the total, because nothing is visible
    # until the end" — which flatters streaming. The other defensible answer is
    # "undefined, print n/a". Pick one, write two sentences of justification in
    # the CHECKLIST, and make the table say what you chose. A benchmark whose
    # definitions are not written down is a benchmark that flatters whoever ran it.


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- `from stream_demo import streaming_researcher` — the two labs share **one agent definition**. If the
  benchmark built its own agent, the first person to tweak `max_turns` in one file would be comparing
  two different systems and would not notice. Same-agent, same-pins, same-temperature (Day 9) is what
  makes the two rows comparable at all.
- `blocking_run` sets `first_progress_ms = ttft_ms = total_ms` — and the **TODO(me)** at the bottom
  makes you argue with that choice. It is the honest reading (with `Runner.run` the first thing a user
  sees *is* the finished answer), and it is also the reading that makes streaming look best, which is
  exactly why you should have to defend it in writing. **Benchmarks are arguments; label your
  assumptions.**
- Two `Runner` calls per repeat, `REPEATS = 2` — four full agent runs, roughly sixteen model requests.
  §7 budgets for it. The docstring says the cost at the top because Principle 5 means a lab that
  quietly loops is a lab that eats your day's quota.
- `reducer.elapsed_ms()` as the streamed total rather than a second `time.monotonic()` — the reducer
  already started its clock at construction, and having *one* clock removes a whole class of
  off-by-a-few-hundred-milliseconds confusion.
- Alternating blocking and streamed runs rather than doing all of one then all of the other —
  **interleaving cancels drift.** Free-tier latency varies by the minute; two blocks of runs measure
  the minute as much as the mode.
- `chars` in the table is a sanity column, not a result. If the two modes produce wildly different
  lengths, you are not measuring latency, you are measuring two different answers, and §5's
  equivalence test is about to fail.

### 3.8 What you should see

Roughly this, on Groq's free tier with a two-tool research run:

```
                what streaming buys (ms)
  mode                 first progress  first token   total  chars
  Runner.run                     6120         6120    6120   842
  Runner.run_streamed             410         3980    6210   839
  Runner.run                     5980         5980    5980   842
  Runner.run_streamed             395         4050    6180   839
```

**Read the columns, not the numbers.**

- **`total` barely moved**, and the streamed row is very slightly *worse* — you added per-event Python
  work to a network-bound run. Streaming is not an optimisation. Say that in an interview before
  anyone asks.
- **`first token` is roughly two seconds earlier than `total`**, because the model spent the first
  part of the run calling tools and there was no text to emit yet.
- **`first progress` is an order of magnitude earlier than `first token`.** That is `run_item` and
  `agent_updated` events firing while the model is still deciding. In a tool-using agent, **the
  run-item stream is the progress surface and the token stream is the garnish** — which is the
  opposite of what a chatbot demo teaches you.
- `chars` differs by three. Trailing whitespace, usually. §5's equivalence test normalises for exactly
  this and you should look at *why* yours differs rather than widening the comparison until it passes.

Write your four numbers into the CHECKLIST. **A ratio you measured beats an adjective you read.**

---

## §4 AG-28 🅿️ — Streaming UX, and what the demo tempts you to forget

AG-28 is marked 🅿️ in the plan because its full treatment lands on **Day 45**, streaming a LangGraph.
Today you get the concept and the three tensions, because you have just built the thing that creates
them and the lesson does not survive being read cold in nine weeks.

### 4.1 Perceived latency is a different quantity from latency

Two runs take 6.1 seconds. One shows nothing for 6.1 seconds; the other shows `calling get_ticket…`
at 400 ms. Users report the second as faster. They are not confused — they are measuring a different
thing, and it is the thing that matters:

> **Latency is how long the work takes. Perceived latency is how long the user is uncertain. A
> progress surface does not reduce the first and can nearly eliminate the second.**

The surfaces, honestly ranked:

| What the user sees | Uncertainty ends… | Costs you | Verdict |
|---|---|---|---|
| nothing | at the answer | nothing | worst, and it also looks broken |
| a spinner | at the answer | nothing | **worse than a partial answer, better than nothing** — it proves the process is alive and says nothing else |
| named steps (`run_item` events) | at ~400 ms | the classifier you wrote | **the sweet spot for an agent** — informative, bounded, loggable, safe |
| tokens arriving | at the first token | everything in §4.2–4.4 | best for prose; impossible for a typed output |

Why a spinner is worse than a partial answer: a spinner is a **liveness** signal with zero
information content. It cannot tell you the agent is stuck in a tool retry, cannot tell you it picked
the wrong tool, and cannot be read as an answer-in-progress. Why it is better than nothing: a blank
screen is indistinguishable from a crash, and users resolve that ambiguity by pressing the button
again — which on a free tier is a second full run against your quota.

Notice that the third row is where an *agent* differs from a *chatbot*. A chatbot has nothing to
report but tokens. Your agent has a tool call at 400 ms, a tool result at 900 ms, and a handoff at
2 s — **real, discrete, true statements about the work**, all available before a single token of prose
exists.

### 4.2 Tension one — streaming vs. structured output (Day 11)

Day 11 gave the Researcher `output_type=Brief`, and Day 14 made that `Brief` the seam between the two
pipeline steps. Now try to stream it.

> **You cannot render a partial validated object.** Halfway through, the model has emitted
> `{"triage": {"category": "billing", "sever` — which is not a `Brief`, is not valid JSON, and cannot
> be shown to anyone. Validation is a step function: there is nothing, and then there is a `Brief`.

The three things people actually do, and what each really costs:

| Approach | What streams | What it costs |
|---|---|---|
| **Stream run-item / progress events only** | "calling get_ticket", "calling search_tickets", "brief produced" | you never stream prose. **This is Mandala's answer** and it is why §3.5's `ItemDone` exists |
| **Stream a prose channel, validate separately** | the model narrates, then produces the object in a second call | a second model call — on a free tier that is a doubling of the request budget (Principle 5) |
| **Partial-JSON parsing** | a progressively-filled object | you have written a streaming JSON parser and a "is this field final?" heuristic; every consumer now handles half-objects. Real products do this; it is a genuine engineering project, not a flag |

The reason `stream_demo.py` uses a Researcher **without** `output_type` is this row, and it is worth
seeing as a design fact rather than a demo convenience: **the typed pipeline and the streamed surface
are two different agents on purpose.** Day 14's pipeline still runs typed and unstreamed; today's
surface streams prose and is not part of the pipeline.

If that feels unsatisfying, good — it is. Partial-structured-output streaming is an unsolved-in-
practice problem that every agent product hits, and "I know exactly why it is hard" is a much better
interview position than a hand-wave.

### 4.3 Tension two — streaming vs. output guardrails (Day 12) 🎯

This is **the trap of the day** and the reason §4 exists at all.

Day 12 gave you `no_secrets_in_output` and `no_other_customers` as `@output_guardrail`s. Read the
name again: **output** guardrails. They run on the output. The output does not exist until the run
finishes.

> **A guardrail that runs after the text is on screen is not a block. It is a retraction — and a
> retraction is a disclosure with an apology attached.**

If `no_other_customers` trips on a run you streamed live to a customer, the customer has already read
the other customer's name. Deleting the message afterwards does not undo that; it merely tells them it
was important.

The mitigations, with the trade of each stated honestly:

| Mitigation | The user gets | The cost | Right when |
|---|---|---|---|
| **Buffer, then release** | the whole answer at once, after guardrails pass | you lose token streaming entirely — you keep run-item progress, which is most of the benefit (§4.1) | the default for any customer-facing channel |
| **Stream only after guardrails** | identical to buffer-then-release, with a fake typing animation on top | the same, plus a UI that pretends | when someone insists on the aesthetic; be honest that it is aesthetic |
| **Stream to an **operator**, gate the send** | the operator sees everything live; the customer receives a message a human released | you need an operator, and an approval step | **Mandala's answer** — Principle 12 already required the human, so the surface is free |
| **Stream live and retract on trip** | fastest possible feel | a retraction is a disclosure. Unacceptable for secrets, PII, or another customer's name | narrow internal cases only, never for the guardrails you actually wrote |
| **Stream a safe sub-channel only** | step names, never model prose | you must classify what is safe — which is exactly what `ItemDone` vs. `TokenDelta` already does | always worth combining with the above |

Rows three and one are not in tension: Mandala streams **to the operator** (row three) and the customer
gets **buffer-then-release behind an approval** (row one). That is what `deliver()` encodes in §3.5,
and §5 asserts it at **0 model requests**.

Two more things this tension teaches, both worth carrying:

- **Input guardrails are unaffected.** `no_secrets_in_input` and `input_is_within_budget` (Day 12) run
  before the model is called and are just as effective on a streamed run. The asymmetry is entirely on
  the output side, and knowing *which half* breaks is what separates a real answer from a worry.
- **Errors arrive mid-frame now.** A tripped input guardrail, a `MaxTurnsExceeded`, or a 429 raises
  out of your `async for` loop while `rich.Live` owns the terminal. Your renderer must handle an
  exception mid-stream and leave the screen readable. That is a real bug class that does not exist in
  a blocking run.

### 4.4 Tension three — streaming vs. the free tier (Principle 5)

> **Streaming does not reduce tokens or requests. It changes when you see them.**

Three consequences that are specific to a $0 project:

1. **The budget is identical.** Same `max_turns`, same number of generation spans in Day 14's trace,
   same rows in `docs/RATE_BUDGET.md`. If anything, the streamed row in §3.8 is a few milliseconds
   slower. Anyone who tells you streaming saves quota is confusing it with caching.
2. **Usage arrives last.** Day 9 pinned `ModelSettings(include_usage=True)`. In a streamed response
   the usage block is on the *final* chunk, so a progress surface can show you elapsed time and step
   count but **cannot** show you token spend until the run is over. Do not build a live cost meter on
   Day 71 without remembering this.
3. **A 429 now arrives mid-render — and the router cannot save you.** This is the sharp one. Day 6's
   `Router` falls back Gemini → Groq → OpenRouter → Ollama on a 429, and that works beautifully for a
   blocking call: nobody ever saw the failed attempt. But **you cannot un-emit tokens.** If Groq
   throttles you 300 tokens into a streamed answer, a retry on OpenRouter produces a *different*
   continuation, and you must either restart the visible answer from scratch (a visible glitch) or
   splice two models' prose together (worse). Streaming and transparent provider fallback are in
   genuine tension, and the honest resolution on this project is: **stream the run-item events, which
   are cheap to restart, and buffer the prose, which is not.**

That third point is the deepest thing on this page. Write it down.

### 4.5 Mandala's rule, in one line

> **Drafts stream to the operator. Nothing streams to a customer.**

Principle 12 already says no external side effect happens without a human checkpoint, and Day 8 split
`draft_reply` (writes nothing) from `post_reply` (writes). Streaming slots into that split without any
new policy: the operator watching a draft appear is *inside* the approval gate, and the customer is on
the far side of it. **A security property you already have is a security property you do not have to
argue for** — which is why §3.5's `deliver()` is fifteen lines and not a design document.

Nothing to run for AG-28. Write four sentences into your notes — one per tension, one for the rule —
and carry them to Day 45, where the same three tensions reappear in LangGraph with different
mechanics and identical consequences.

---

## §5 The eval that must be able to fail

### `tests/test_streaming.py`

```python
"""The classifier and the reducer. Everything here but the last two costs 0 requests."""

from types import SimpleNamespace

import pytest

from mandala.streaming import (
    MAX_ANSWER_CHARS,
    AgentSwitched,
    ItemDone,
    ProgressReducer,
    TokenDelta,
    Unclassified,
    classify,
)


def fake_event(event_type: str, **kwargs) -> SimpleNamespace:
    """An SDK-shaped object with no SDK in it. Costs nothing, never flakes."""
    return SimpleNamespace(type=event_type, **kwargs)


def test_an_unknown_event_kind_does_not_crash_and_is_not_dropped():
    """THE decided behaviour: unknown -> Unclassified, counted by raw_type.

    We could have dropped it, or raised. Dropping makes an SDK rename invisible;
    raising makes a cosmetic event kill a run. Counting is the third option and
    the only one that fails loudly without failing fatally.
    """
    reducer = ProgressReducer()
    progress = reducer.feed(fake_event("ufo_stream_event"))

    assert isinstance(progress, Unclassified)
    assert progress.raw_type == "ufo_stream_event"
    assert reducer.unclassified["ufo_stream_event"] == 1
    assert reducer.answer == ""


def test_a_foreign_object_with_no_type_still_classifies():
    """Rule 1 at the boundary: even garbage gets a name, never an exception."""
    progress = classify(object())
    assert isinstance(progress, Unclassified)
    assert progress.raw_type == "object"


def test_every_progress_family_is_reachable_from_classify():
    """Flip it: delete the agent_updated_stream_event branch in classify() and
    this must go RED. Exhaustiveness is the property; the branches are details.
    """
    events = [
        fake_event("raw_response_event", data=SimpleNamespace(
            type="response.output_text.delta", delta="hi")),
        fake_event("run_item_stream_event", item=SimpleNamespace(type="tool_call_item")),
        fake_event("agent_updated_stream_event", new_agent=SimpleNamespace(name="Resolver")),
        fake_event("something_new_in_0_23"),
    ]
    kinds = {classify(e).kind for e in events}
    assert kinds == {"token", "item", "agent", "unclassified"}


def test_progress_events_are_ours_not_the_sdks():
    """The seam, asserted. Day 14 did this for spans; Day 15 for search results."""
    progress = classify(fake_event("agent_updated_stream_event",
                                   new_agent=SimpleNamespace(name="Resolver")))
    assert type(progress).__module__.startswith("mandala.")


def test_the_answer_buffer_is_bounded():
    """A stream is the one place 'it is only a string' is false."""
    reducer = ProgressReducer(max_answer_chars=50)
    for _ in range(100):
        reducer.apply(TokenDelta(text="0123456789"))
    assert len(reducer.answer) == 50
    assert reducer.truncated is True


def test_ttft_is_none_before_any_token_not_zero():
    """0.0 means 'instant'. None means 'has not happened'. A dashboard believes 0."""
    reducer = ProgressReducer()
    reducer.apply(ItemDone(item_type="tool_call_item", label="get_ticket"))
    assert reducer.ttft_ms is None
    assert reducer.first_progress_ms is not None


def test_tool_calls_come_from_run_items_never_from_token_text():
    """§3.3's rule, asserted. Prose that mentions a tool is not a tool call."""
    reducer = ProgressReducer()
    reducer.apply(TokenDelta(text="I will now call get_ticket and search_tickets."))
    assert reducer.tool_calls == []

    reducer.apply(ItemDone(item_type="tool_call_item", label="get_ticket"))
    assert reducer.tool_calls == ["get_ticket"]


def test_an_agent_switch_is_recorded_in_order():
    """The streaming form of Day 13's last_agent."""
    reducer = ProgressReducer()
    reducer.apply(AgentSwitched(agent_name="Researcher"))
    reducer.apply(AgentSwitched(agent_name="Resolver"))
    assert reducer.agents == ["Researcher", "Resolver"]


def test_the_default_answer_cap_is_not_absurd():
    assert 1_000 <= MAX_ANSWER_CHARS <= 100_000


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_the_reducer_rebuilds_exactly_what_the_sdk_produced():
    """Equivalence, part one: my fold == the SDK's own final_output."""
    from agents import Runner

    from mandala.context import MandalaContext
    from stream_demo import streaming_researcher

    context = MandalaContext(actor="agent:researcher", request_id="req-T-1004")
    reducer = ProgressReducer()
    result = Runner.run_streamed(
        streaming_researcher(), "Research ticket T-1004.", context=context, max_turns=8
    )
    async for event in result.stream_events():
        reducer.feed(event)

    assert reducer.answer.strip() == str(result.final_output).strip()
    assert reducer.truncated is False


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_streaming_does_not_change_the_answer():
    """Equivalence, part two: same agent, same input, two call styles, one answer.

    temperature=0.0 (Day 9) plus a cassette is what makes this assertable at all.
    If it is flaky, do not widen the comparison — find out which pin came loose.
    """
    from agents import Runner

    from mandala.context import MandalaContext
    from stream_demo import streaming_researcher

    def normalise(text: str) -> str:
        return " ".join(str(text).split())

    context = MandalaContext(actor="agent:researcher", request_id="req-T-1004")
    blocking = await Runner.run(
        streaming_researcher(), "Research ticket T-1004.", context=context, max_turns=8
    )

    reducer = ProgressReducer()
    streamed = Runner.run_streamed(
        streaming_researcher(), "Research ticket T-1004.", context=context, max_turns=8
    )
    async for event in streamed.stream_events():
        reducer.feed(event)

    assert normalise(reducer.answer) == normalise(blocking.final_output)
    assert reducer.tool_calls == [
        n for n in (getattr(getattr(i, "raw_item", None), "name", None)
                    for i in blocking.new_items) if n
    ]
```

### `tests/test_stream_guardrails.py`

```python
"""Where streamed text is allowed to go. Zero model requests, by construction."""

import pytest

from mandala.streaming import StreamWithheld, deliver, may_stream


def test_the_customer_channel_is_never_a_live_stream_sink():
    """Principle 12, as a boolean. §4.3's whole argument in one assertion."""
    assert may_stream("operator") is True
    assert may_stream("customer") is False


def test_an_unknown_channel_is_not_streamable():
    """The safe thing must be what happens when someone forgets to declare a sink."""
    assert may_stream("slack") is False
    assert may_stream("") is False


def test_customer_text_cannot_be_released_before_guardrails_ran():
    with pytest.raises(StreamWithheld):
        deliver("your refund is approved", channel="customer",
                guardrails_ran=False, tripped=False)


def test_a_tripped_output_guardrail_is_a_block_not_a_retraction():
    """Flip it: make deliver() return the text on a trip and watch this go red.

    This is the day's trap, asserted. A retraction is a disclosure with an
    apology attached (§4.3).
    """
    with pytest.raises(StreamWithheld):
        deliver("hello Ms Other-Customer", channel="customer",
                guardrails_ran=True, tripped=True)


def test_the_operator_surface_may_see_a_draft_live():
    """The operator is INSIDE the approval gate (Day 8's draft/post split)."""
    text = deliver("draft: we will refund you", channel="operator",
                   guardrails_ran=False, tripped=False)
    assert text.startswith("draft:")


def test_a_clean_customer_release_still_works():
    """The pair, again: prove the check fires AND that it does not always fire."""
    assert deliver("we have refunded you", channel="customer",
                   guardrails_ran=True, tripped=False)
```

**Line by line:**

- `fake_event` with `SimpleNamespace` — **the payoff of the seam, in one helper.** Because `classify`
  only reads attributes, a three-line stub stands in for an SDK event object, and eight of today's
  tests run with no model, no network and no mocking library. Compare with what it would take to test
  a renderer that consumed SDK types directly.
- `test_an_unknown_event_kind_does_not_crash_and_is_not_dropped` — the spec said *decide one behaviour
  and assert it*, and the docstring names the two rejected options and why. **A test docstring that
  records the alternatives is a design record you cannot lose.**
- `test_a_foreign_object_with_no_type_still_classifies` — passing a bare `object()` is not paranoia;
  it is the shape of what happens when a library yields a wrapper you did not expect. The boundary
  either names it or explodes, and this asserts which.
- `test_every_progress_family_is_reachable_from_classify` — **the flip-it test of the day**, with the
  flip in the docstring. It asserts on the *set* of kinds rather than four separate `isinstance`
  checks, which is why deleting a branch turns it red instead of leaving three green tests and one
  missing one.
- `test_progress_events_are_ours_not_the_sdks` — asserting on `__module__` looks pedantic and is the
  cheapest possible guard against the most likely regression: somebody "simplifying" `classify` into
  a passthrough. Day 14 and Day 15 both have a version of this test; that is the pattern, not a
  coincidence.
- `test_ttft_is_none_before_any_token_not_zero` — a two-line test for a distinction that will
  eventually reach a dashboard. **A metric that defaults to zero gets averaged.**
- `test_tool_calls_come_from_run_items_never_from_token_text` — this one is a genuine trap-catcher.
  Feed it prose that *names* two tools and assert `tool_calls == []`. If someone ever reimplements
  `tool_calls` by scanning the answer, this goes red immediately.
- The two `@pytest.mark.vcr` tests are the **only** ones in either file that cost model requests, and
  they are the two the spec demands: the reducer rebuilds the SDK's own output, and streaming does not
  change the answer. Record the cassettes once; after that both are free and offline.
- `normalise()` collapses whitespace and nothing else. **Resist widening it.** A comparison that has
  been loosened until it passes is a comparison that no longer tests anything — if the two modes
  genuinely differ, that is a finding about `_delta_text`, not a formatting problem.
- The second assertion in `test_streaming_does_not_change_the_answer` compares your `tool_calls`
  against the blocking run's `new_items` — that `getattr` chain is Day 14's defensive shape, and it
  is fine *here* (a test asserting on a foreign object) in a way it was not fine in library code.
- `tests/test_stream_guardrails.py` is **entirely configuration**: booleans, a dict and a function
  with four branches. Every one of today's most important safety properties is asserted at 0 model
  requests, which is the whole reason `deliver()` is a pure function instead of a method on a
  streaming session.
- `test_a_clean_customer_release_still_works` — **the pair, again** (Day 14's
  `assert_no_raw_ticket_*`). A `deliver()` that raised unconditionally would pass every other test in
  the file.

---

## §6 Traps

- **Streaming customer-facing text before an output guardrail has run.** The guardrail becomes a
  retraction, and a retraction is a disclosure with an apology attached. **The trap of the day** 🎯 —
  and it will look like a two-line change to "improve the UX".
- **`await Runner.run_streamed(...)`.** It is not awaited. You get a `TypeError` if you are lucky and
  a silent no-op if you wrapped it, and either way you conclude that streaming does not work.
- **Reading `result.final_output` before the stream is exhausted.** The run has not happened yet.
  Consume `stream_events()` to completion first.
- **Iterating `stream_events()` twice.** One-shot async iterator. The second loop yields nothing and
  you will blame the model.
- **Repainting the terminal on every delta.** Hundreds of frames a second, a terminal that looks
  broken, and a "slow" verdict on a fast model. `refresh_per_second=10` and a pure frame function.
- **Mixing bare `print()` with `rich.Live`.** Interleaved half-frames. One output channel while the
  display is live.
- **Parsing tool names out of streamed token text.** That is what `run_item_stream_event` is for. Prose
  that mentions `get_ticket` is not a tool call, and one retry duplicates your line.
- **Logging raw deltas.** Nine hundred lines per run that you cannot query, containing every token of
  customer-facing text on disk — Day 14's allowlist, undone in a single `logger.debug`.
- **Dropping event kinds the classifier does not recognise.** The day the SDK renames one, your UI
  goes blank and nothing tells you. Count them; print the counter.
- **An unbounded answer buffer.** It grows on every chunk of every run, and the failure mode is a
  memory graph, not an exception. Cap it and set a `truncated` flag the renderer shows.
- **Expecting to stream `output_type=Brief`.** There is nothing valid to render until it validates
  (§4.2). Stream progress events instead, and know why you are doing it.
- **Assuming streaming saves quota.** Same tokens, same requests, same rate limit. It also means a 429
  arrives mid-sentence, where Day 6's router cannot transparently retry — you cannot un-emit tokens.
- **Building a live token-cost meter.** `include_usage=True` (Day 9) reports on the *final* chunk.
  Elapsed time and step counts are live; spend is not, until the end.
- **Leaving `_delta_text` guessed rather than verified.** It is one attribute path and it is the single
  most provider-dependent line in the project. §8.

---

## §7 Request budget

| Activity | Model requests | Notes |
|---|---|---|
| `naked_stream.py` — the raw `stream=True` loop | **1** (Groq) | one prompt, no tools |
| `stream_demo.py` × 3 (you will want to watch it more than once) | ~12 (Groq) | ~4 per research run |
| `first_token.py` — `REPEATS=2`, alternating blocking/streamed | ~16 (Groq) | **today's number-producing experiment** |
| Iterating on `_delta_text` / `label_for` until the events print right | ~8 (Groq) | keep runs short; use `max_turns=4` while probing |
| Cassette recording for the two equivalence tests | ~8 (Groq) | record once |
| **Total** | **≈ 45, Groq** | log the actual figure in `docs/RATE_BUDGET.md` |

**What costs 0:** every test in `tests/test_stream_guardrails.py`; every test in
`tests/test_streaming.py` except the two `@pytest.mark.vcr` ones; every re-run of those two once the
cassettes exist; and every re-render of `frame()` while you tune the display, because the reducer is
a plain object you can populate by hand:

```python
r = ProgressReducer()
r.apply(ItemDone(item_type="tool_call_item", label="get_ticket"))
r.apply(TokenDelta(text="The customer was charged twice."))
console.print(frame(r))          # tune the UI for free, forever
```

**Do that.** Tuning a live display against real model calls is how a lab that declared 45 requests
spends 200. The seam you built in §3.5 is what makes free iteration possible — that is the same
argument Day 14 made for keeping `span_tree.py` a separate program from the exporter.

---

## §8 Verify before you code

Written **2026-08-20** against `openai-agents` **0.22.0** and `rich` **15.0.0**.

- `https://openai.github.io/openai-agents-python/streaming/` — the guide. Confirm that
  `Runner.run_streamed()` is **not** awaited, that `.stream_events()` is the async iterator, and that
  the three `event.type` discriminators are still `raw_response_event`, `run_item_stream_event` and
  `agent_updated_stream_event`. Those three strings are the only SDK vocabulary in `streaming.py`.
- `https://openai.github.io/openai-agents-python/ref/stream_events/` — **the exact class names**
  (`RawResponsesStreamEvent`, `RunItemStreamEvent`, `AgentUpdatedStreamEvent` — confirm the spelling,
  including whether it is `RawResponses` plural) and the attribute each carries: `.data`, `.item`,
  `.new_agent`. Confirm the `run_item` sub-type strings you match on — `tool_call_item`,
  `tool_call_output_item`, `message_output_item`, `handoff_call_item` — because
  `ProgressReducer.tool_calls` matches one of them literally.
- `https://openai.github.io/openai-agents-python/ref/items/` — the run-item classes and their
  `raw_item` shapes. This is what `label_for`'s `TODO(me)` needs.
- ⚠️ **The real one, and it is a genuine unknown: does streaming behave the same through
  `LitellmModel` on Groq as it does through OpenAI's own Responses API?** Mandala has no OpenAI key
  (Principle 5), so every event you will ever see comes through LiteLLM. The SDK's streaming
  documentation is written against the Responses API, and the raw-delta payloads are the layer most
  likely to differ — different event names, a different `delta` attribute, or coarser chunking. **This
  lesson does not assert that it works identically; verify it before you trust `_delta_text`.** Run
  the probe in §3.5's docstring and print the first ten raw events. If the shape differs materially
  from the docs, that is a Part-4 fact about OAI-16 on a zero-budget stack: log one line in
  `docs/CHANGELOG_PLAN.md`, and if run-item streaming works but token streaming does not, **stop and
  propose a plan amendment** rather than quietly rewriting the day (Principle 14).
- Confirm whether `ModelSettings(include_usage=True)` (Day 9) still delivers usage on a streamed run
  through LiteLLM, and on which event. §4.4 claims "the final chunk"; check it.
- `https://rich.readthedocs.io/en/stable/live.html` — `Live`'s constructor: `refresh_per_second`,
  `console`, `transient`, and whether `Live` still wants `live.update(renderable)` rather than a
  `refresh()` call. Also confirm `Group` is imported from `rich.console` in 15.0.0.
- Re-read your `docs/PINS.md` ledger row for Day 17 after installing, and pin what actually resolved.

---

## §9 Say it in an interview

> "Streaming in the Agents SDK is `run_streamed`, which — unlike `run` — isn't awaited: it hands you a
> result object immediately and the run advances while you consume `stream_events()`. That stream has
> three families: raw model deltas, run-item events, and agent-updated events. The distinction I
> actually build around is that **raw deltas are for the eyeball and run-item events are for the
> program**. So I wrote a classifier that turns the SDK's events into my own typed, capped progress
> events, and the renderer and the tests both consume mine — the SDK's class names appear in exactly
> one function in my codebase, which is also the only function I have to fix on a version bump. It
> made the surface testable at zero model cost too, which matters because I'm on free tiers. And the
> number that convinced me it was worth doing: on a two-tool research run, time-to-first-token was
> about four seconds but time-to-first-*progress-event* was about four hundred milliseconds. For an
> agent, the run-item stream is the progress surface; the tokens are the garnish."

> "The thing streaming tempts you to forget is that output guardrails run *after* the output exists.
> I had an output guardrail that blocks answers naming other customers — if I'm streaming that answer
> live to a customer, the guardrail can no longer block anything, it can only retract, and a
> retraction is a disclosure with an apology attached. So I made where streamed text may go part of
> the streaming contract rather than a caller's decision: one function owns delivery, unknown channels
> are not streamable, and releasing customer text before guardrails have run raises. Operationally the
> rule is 'drafts stream to the operator, nothing streams to a customer' — which cost me nothing to
> adopt, because I already had a human approval gate before any external write, and the operator sits
> inside it. Two related things I'd flag in a design review: you can't stream a validated structured
> output at all, because there's nothing to render until it validates; and streaming breaks
> transparent provider fallback, because you can retry a blocking call but you cannot un-emit tokens."

---

## §10 Done when

```bash
./m check
./m done 17
```

Tomorrow: programmatic tool calling — the paid Responses feature where the model writes a small
program to coordinate tools 🅿️ — and the free coordinator function tool that buys you the same
round-trip economics for $0.
