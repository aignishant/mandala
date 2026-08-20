---
day: 9
phase: 2
phase_name: "OpenAI Agents SDK core"
title: "First Agent, borrowed engine"
ids: ["OAI-01", "OAI-02"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 9 — First `Agent`, borrowed engine

**Phase 2 · OpenAI Agents SDK core** · IDs: **OAI-01 🛠️**, **OAI-02 🅿️**

> **Yesterday:** two agents, two credential sets, ten golden tickets passing. Phase 1 done.
> **Today:** the first framework. Your two hundred lines become about ten — running on **Groq**, with
> **no OpenAI key**, for **$0**.
> **Tomorrow:** tools and the Runner, in depth.

```bash
./m start 9
./m scaffold 9
```

---

## §1 The story

There is a specific pleasure available today that is only available *because* of the last six days.

You are about to write this:

```python
agent = Agent(name="Triage", instructions=TRIAGE.render(), model=model, tools=[get_ticket])
result = await Runner.run(agent, "What severity is T-1001?")
```

Four lines. And you will look at them and know — precisely, not vaguely — that inside `Runner.run`
there is a `for` loop, that it appends the assistant message before the tool message, that it copies
`tool_call_id` across, that it caps the turns, and that if `max_turns` is exceeded it raises.

You know that because you wrote it on Day 3. **That is the entire purpose of Principle 2.** People
who start with the framework experience `Runner.run` as magic, and magic is unfixable — when it
misbehaves at 11pm you have no model of what it is doing. You have one.

The second thing today is the awkward, useful bit: **this is OpenAI's SDK and you have no OpenAI
key, and you never will** (Principle 5). So today you learn something most tutorials skip — how to
run the SDK's *primitives* on someone else's free models, and exactly where the paid boundary sits.

That boundary is not a footnote. It is an interview answer. When someone asks "what do you think of
the Agents SDK?", "I ran its primitives on Groq and Gemini via LiteLLM for three months, and here is
precisely which parts required a paid key" is a much better answer than a summary of the docs.

---

## §2 Setup — run this

```bash
uv add "openai-agents[litellm]==0.22.0"
```

**Line by line:**

- `openai-agents` — the SDK package. The import name is **`agents`**, not `openai_agents`. That
  mismatch catches everyone once.
- `[litellm]` — an **extra**: an optional dependency group declared by the package. This one pulls in
  `litellm`, which is the adapter that lets the SDK talk to Gemini, Groq, OpenRouter and Ollama.
  Without the extra you get the SDK but not the ability to use free models, which is the whole point
  here.
- `==0.22.0` — the pin verified on 2026-08-20 (`docs/PINS.md`). Re-verify before you install; this
  package released on 2026-08-19, so it moves.

Check it landed and see what came with it:

```bash
uv run python -c "import agents; print(agents.__file__)"
uv pip list | grep -i "openai-agents\|litellm"
```

Create today's files:

```bash
mkdir -p days/day-09/lab
touch src/mandala/sdk.py
touch days/day-09/lab/first_agent.py
touch days/day-09/lab/wire_shapes.py
touch tests/test_sdk_agent.py
```

---

## §3 OAI-01 — Install, project shape, first `Agent`

### The SDK's whole vocabulary, in one table

The Agents SDK is deliberately small. Learning it is learning five nouns:

| Primitive | What it is | You built this on |
|---|---|---|
| **Agent** | instructions + model + tools + output type | Day 3 (the loop's inputs) |
| **Runner** | the loop that drives it | Day 3 (`run()`) |
| **Tool** | a Python function the model can request | Day 3 (`TOOLS` + schemas) |
| **Guardrail** | a fast check that trips before/after a run | Day 12 |
| **Session** | conversation state across turns | Day 7 (`JsonSession`) |
| **Handoff** | transfer of control to another agent | Day 13 |

Six nouns. That is the SDK. Everything else is arrangement.

### 3.1 The three things that make it work on $0

This is the part no tutorial covers, so read it slowly.

**(1) The model must be a `LitellmModel`, constructed explicitly.**

```python
from agents.extensions.models.litellm_model import LitellmModel

model = LitellmModel(model="groq/llama-3.3-70b-versatile", api_key=KEYS.groq)
```

The `model=` string is a **LiteLLM provider string**: `provider/model-id`. `groq/...`, `gemini/...`,
`openrouter/...`, `ollama/...`. That prefix is what routes the call.

There is also a string form — `Agent(model="litellm/gemini-pro")` — but it requires you to pass a
`MultiProvider` in a `RunConfig`, and it hides which key is being used. **Use explicit
`LitellmModel`.** Principle 4 is about not inheriting decisions, and an explicitly constructed model
object with an explicitly passed key inherits nothing.

**(2) Tracing must be switched off, or every run tries to upload to OpenAI.**

```python
from agents import set_tracing_disabled

set_tracing_disabled(True)
```

By default the SDK exports traces to OpenAI's dashboard, which needs a paid key. Without this line
you get warnings or errors on every single run. Day 14 replaces this with a console/OTel exporter so
you keep traces — just not *theirs*.

**(3) Usage metrics need asking for.**

```python
from agents import ModelSettings

model_settings = ModelSettings(include_usage=True)
```

The SDK docs are explicit that some providers reached through the LiteLLM adapter do not populate
usage metrics by default. On a $0 project, **usage is your budget** (Principle 5) — a run whose token
count you cannot see is a run you cannot budget. Turn it on from day one.

### 3.2 `src/mandala/sdk.py` — one place for all three

```python
"""Agents SDK wiring for a zero-budget project.

Three things must be true for the SDK to work here, and all three are easy to
forget in one lab and then debug for an hour in another:

  1. the model is an explicitly constructed LitellmModel with an explicit key
  2. OpenAI trace upload is disabled (we have no OpenAI key)
  3. usage reporting is requested (on $0, usage IS the budget)

Every later SDK day imports from here rather than repeating them.

Usage
-----
    >>> from mandala.sdk import make_model, DEFAULT_SETTINGS
    >>> model = make_model("groq")
    >>> model.model
    'groq/llama-3.3-70b-versatile'
"""

from __future__ import annotations

from agents import ModelSettings, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel

from mandala.config import load_keys
from mandala.models import PROVIDERS

# (2) No OpenAI key exists in this project. Do this once, at import.
set_tracing_disabled(True)

# (3) Ask for usage explicitly; several LiteLLM backends omit it otherwise.
DEFAULT_SETTINGS = ModelSettings(include_usage=True, temperature=0.0)

_LITELLM_PREFIX = {
    "gemini": "gemini",
    "groq": "groq",
    "openrouter": "openrouter",
    "ollama": "ollama_chat",
}


def make_model(provider: str = "groq") -> LitellmModel:
    """Build a pinned LitellmModel for one of our free providers. (1)"""
    if provider not in PROVIDERS:
        raise ValueError(f"unknown provider {provider!r}; known: {sorted(PROVIDERS)}")

    spec = PROVIDERS[provider]
    key = getattr(load_keys(), spec.key_attr)
    prefix = _LITELLM_PREFIX[provider]

    return LitellmModel(model=f"{prefix}/{spec.default_model}", api_key=key)
```

**Line by line:**

- `set_tracing_disabled(True)` **at module level** — runs once when `mandala.sdk` is first imported.
  Putting it in a function you might forget to call is how you end up with one lab that warns on
  every run. Module-level side effects are usually a smell; this is the exception, and the comment
  says why.
- `ModelSettings(include_usage=True, temperature=0.0)` — `temperature=0.0` makes runs as reproducible
  as the provider allows, which matters because your cassettes and golden set assume stable
  behaviour. **A default temperature is a default you did not choose** (Principle 4).
- `_LITELLM_PREFIX` — mapping *your* provider names to *LiteLLM's* provider names. They mostly match,
  and `ollama` → `ollama_chat` is the one that does not. Keeping the mapping explicit means the one
  exception is visible rather than being a bug you meet in eleven weeks.
- `if provider not in PROVIDERS: raise ValueError(...)` — fail on a typo immediately, listing the
  valid options.
- `getattr(load_keys(), spec.key_attr)` — the Day-1 indirection again. The model pin comes from
  `mandala.models`, the key from `mandala.config`, and this function just assembles them.
- `f"{prefix}/{spec.default_model}"` — the LiteLLM provider string, built from pinned parts. **No
  model id is written in this file**, which is what makes a roster rotation a one-line fix in
  `models.py`.
- **What is deliberately NOT here:** a fallback chain. Day 6's `Router` handles fallback for raw
  calls, but the SDK owns its own loop and will not consult your router. That is a real trade-off,
  it is the first thing you have *lost* by adopting a framework, and it goes in ADR-001 on Day 16.
  Notice it now.

### 3.3 `days/day-09/lab/first_agent.py`

```python
"""Day 3's agent, rebuilt in the Agents SDK. Same behaviour, ~10 lines.

Run:
    uv run python days/day-09/lab/first_agent.py "What severity is ticket T-1001?"
"""

from __future__ import annotations

import asyncio
import json
import sys

from agents import Agent, Runner, function_tool

from mandala.prompts import TRIAGE
from mandala.sdk import DEFAULT_SETTINGS, make_model
from tools import TOOLS as RAW_TOOLS


@function_tool
def get_ticket(ticket_id: str) -> str:
    """Fetch one support ticket by its exact id.

    Args:
        ticket_id: The ticket id, in the form 'T-1001'.
    """
    return json.dumps(RAW_TOOLS["get_ticket"](ticket_id))


@function_tool
def search_tickets(query: str, limit: int = 3) -> str:
    """Find tickets whose body contains a literal phrase. Use when you lack an exact id.

    Args:
        query: A literal phrase to look for.
        limit: Maximum number of results.
    """
    return json.dumps(RAW_TOOLS["search_tickets"](query, limit))


triage_agent = Agent(
    name="Triage",
    instructions=TRIAGE.render(),
    model=make_model("groq"),
    model_settings=DEFAULT_SETTINGS,
    tools=[get_ticket, search_tickets],
)


async def main() -> None:
    question = " ".join(sys.argv[1:]) or "What severity is ticket T-1001?"
    result = await Runner.run(triage_agent, question, max_turns=6)

    print(result.final_output)
    print(f"\nnew items: {len(result.new_items)}")
    for item in result.new_items:
        print(f"  {type(item).__name__}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- `import asyncio` — `Runner.run` is a coroutine. There is a synchronous `Runner.run_sync` if you
  prefer, but async is what streaming (Day 17) and everything past Phase 3 uses, so start as you mean
  to continue.
- `from agents import Agent, Runner, function_tool` — the import is **`agents`**. Note `function_tool`;
  the SDK also exposes `@tool` as a shorter alias for the same thing. This lesson uses
  `@function_tool` because it is the explicit spelling and greps better.
- `@function_tool` — turns the function into a tool. **Compare with Day 3**: you hand-wrote a JSON
  Schema with `properties`, `required` and descriptions. The decorator generates all of it from your
  **type hints** and your **docstring**.
- The docstring's `Args:` section — this is **not decoration.** The SDK parses docstrings with
  `griffe` (google, sphinx and numpy formats supported) and turns each `Args:` entry into that
  parameter's `description` in the schema. So on Day 3 you learned "descriptions are prompts"; today
  that same truth is expressed as "**your docstring is a prompt**". Write it for the model.
- `-> str` and `return json.dumps(...)` — returning a string. The SDK can serialise richer types, but
  returning JSON text keeps the wire shape identical to Day 3, so the comparison is honest.
- `RAW_TOOLS["get_ticket"]` — reusing Day 3's actual implementation. **The tool logic did not
  change.** Only the plumbing did, and seeing that concretely is the point of rebuilding rather than
  rewriting.
- `Agent(...)` — the five arguments map exactly onto Day 3: `instructions` is your system message,
  `model` is the pinned model, `tools` is your `TOOLS` dict, `model_settings` is the parameters you
  passed to `create()`.
- `instructions=TRIAGE.render()` — **your Day-6 prompt object, unchanged.** Prompts survive framework
  changes; that is why they live in a module and not in string literals.
- `await Runner.run(triage_agent, question, max_turns=6)` — the loop. `max_turns=6` is the same cap
  you wrote by hand. It raises `MaxTurnsExceeded` when hit — the SDK's version of your
  `RuntimeError`.
- `result.final_output` — the answer.
- `result.new_items` — **look at this closely.** It is the list of everything that happened:
  message outputs, tool calls, tool outputs, handoffs. It is your Day-3 `messages` list, typed. The
  loop printing `type(item).__name__` is there so you can *see* the correspondence with your own
  `_print_turn`.
- `asyncio.run(main())` — start the event loop, run the coroutine, shut it down.

Run it and compare with Day 3 side by side:

```bash
cd days/day-09/lab
uv run python first_agent.py "What severity is ticket T-1001?"
cd ../../..
```

### 3.4 The comparison you must actually write down

Open `days/day-09/lab/first_agent.py` and `days/day-03/lab/naked_agent.py` next to each other and
fill this in. It becomes part of ADR-001 on Day 16.

| Day-3 line you wrote | Who does it now | Can you still control it? |
|---|---|---|
| `for turn in range(max_turns)` | `Runner.run` | yes — `max_turns=` |
| appending the assistant message | `Runner` | no |
| copying `tool_call_id` | `Runner` | no |
| `json.loads(call.function.arguments)` | `Runner` | no |
| `TOOLS[name](**args)` | `Runner` | partly — `failure_error_function` |
| hand-written JSON Schema | `@function_tool` + type hints + docstring | yes — `name_override`, Pydantic `Field` |
| `except ...: return {"error": ...}` | SDK default error handler | yes — `failure_error_function` |
| provider fallback (Day 6 router) | **nobody** | ❌ **lost** |
| `ContextBudget` accounting | `result` usage, if `include_usage=True` | partly |

**The two ❌/partly rows are the interesting ones.** A framework is a trade: you gained six days of
plumbing and lost your fallback chain. Whether that is a good trade is exactly what Phase 9's
bake-off decides, and you now have a concrete thing to weigh instead of a vibe.

---

## §4 OAI-02 🅿️ — The Responses API underneath

This is a **concept ID** — no lab. But it is an interview question, so learn it properly.

### Two API shapes, and why there are two

OpenAI has two ways to talk to a model:

| | **Chat Completions** | **Responses** |
|---|---|---|
| Shape | you send the whole `messages` array every time | you send input and may reference a previous response by id |
| State | entirely yours | the server can hold it |
| Tools | function calling | function calling **plus server-side hosted tools** |
| Who supports it | everyone (it is the de-facto standard) | OpenAI |
| Used by | your Day-3 loop, Groq, Gemini-compat, OpenRouter | the Agents SDK, natively |

**Why OpenAI built a second one.** Chat Completions has a structural limit: because you resend
everything and the server holds nothing, anything that needs to *live server-side* is impossible.
Hosted web search, a hosted code interpreter, server-managed conversation state, the long-horizon
harness — none fit into "here is my whole transcript, reply once". Responses is a stateful,
tool-hosting substrate designed for agents rather than for chat.

### What that means for you, on $0

The Agents SDK is built for Responses. But through **LiteLLM**, your calls are translated to whatever
your provider actually speaks — which for Groq, Gemini's compatibility endpoint and OpenRouter is
**Chat Completions**.

So the honest statement of your situation is:

> *The SDK's agent-loop primitives work over Chat Completions via the LiteLLM adapter. The parts of
> the SDK that depend on Responses-specific server-side features — hosted tools, server-held state,
> the harness/sandbox line — do not, and those are exactly the parts that need a paid OpenAI key.*

That sentence is worth memorising. It maps the free/paid boundary precisely, and it explains **why**
the boundary falls where it does rather than just listing what is behind it.

### 4.1 See it on the wire — `days/day-09/lab/wire_shapes.py`

Concept IDs are still worth ten minutes of looking.

```python
"""Print the actual HTTP requests the SDK makes, so 'Responses vs Chat Completions'
stops being a docs claim and becomes something you have seen.

Budget: 2 requests. Groq.

Run:
    uv run python days/day-09/lab/wire_shapes.py
"""

from __future__ import annotations

import asyncio
import logging

import litellm

from first_agent import triage_agent
from agents import Runner

# LiteLLM will print the exact provider request/response it constructs.
litellm.set_verbose = True
logging.basicConfig(level=logging.INFO)


async def main() -> None:
    result = await Runner.run(triage_agent, "What severity is ticket T-1001?", max_turns=4)
    print("\n=== final ===")
    print(result.final_output)
    usage = getattr(result, "context_wrapper", None)
    print(f"usage: {getattr(usage, 'usage', None)}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- `litellm.set_verbose = True` — makes LiteLLM log the request it builds and the response it gets.
  This is the layer where translation happens, so it is the right place to look. (If this attribute
  has been renamed in `litellm` 1.97, check their docs for the current verbose flag — and log the
  drift per Principle 14.)
- `logging.basicConfig(level=logging.INFO)` — without configuring the root logger, library log
  records are discarded and you see nothing.
- `getattr(result, "context_wrapper", None)` — defensive access, because the exact attribute holding
  usage differs across SDK versions. **Find where usage actually lives in 0.22.0 and write it down**
  — you need it for the budget line in every later lab.

**What to look for in the output:**

1. The request LiteLLM sends contains a `messages` array and a `tools` array — **Chat Completions
   shape**, exactly what you hand-built on Day 3.
2. The tool schema in it was generated from your docstring. Find your `Args:` text in the JSON.
3. Compare the message sequence with your Day-3 transcript. It is the same conversation.

Ten minutes here permanently removes the mystery from `Runner.run`.

---

## §5 The eval that must be able to fail

### `tests/test_sdk_agent.py`

```python
"""Day-9 guardrails: the SDK agent behaves like the naked one, and stays free."""

import pytest

from mandala import sdk


def test_tracing_is_disabled_on_import():
    """No OpenAI key exists. Trace upload must never be attempted."""
    import agents

    assert agents.  # TODO(me): find the accessor for the tracing flag in 0.22.0
```

That `TODO(me)` is deliberate and it is today's real rep: **find out how to assert that tracing is
off.** The SDK exposes a setter (`set_tracing_disabled`); locating the corresponding state — or
deciding that monkeypatching the setter and asserting it was called is the honest test — is exactly
the kind of question you will answer a hundred times over these 90 days. Read the source under
`agents/` if the docs do not say. **Reading a framework's source is a skill, and this is a small,
safe place to practise it.**

The rest:

```python
def test_model_string_is_a_pinned_litellm_provider_string():
    model = sdk.make_model("groq")
    assert model.model.startswith("groq/")
    assert "<" not in model.model, "model pin is still a placeholder"


def test_unknown_provider_fails_loudly():
    with pytest.raises(ValueError, match="unknown provider"):
        sdk.make_model("anthropic")


def test_usage_reporting_is_requested():
    """On $0, usage IS the budget. A run you cannot measure is a run you cannot budget."""
    assert sdk.DEFAULT_SETTINGS.include_usage is True


def test_temperature_is_pinned():
    """Principle 4: a default temperature is a default you did not choose."""
    assert sdk.DEFAULT_SETTINGS.temperature == 0.0


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_sdk_agent_matches_the_naked_agent_on_T_1001():
    """Same question, same tools, same answer — the framework changed the plumbing, not the result."""
    from agents import Runner
    from first_agent import triage_agent

    result = await Runner.run(triage_agent, "What severity is ticket T-1001?", max_turns=6)
    assert "high" in result.final_output.lower()


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_sdk_agent_actually_calls_the_tool():
    """A trajectory assertion (Day 5): the path matters, not just the destination."""
    from agents import Runner
    from first_agent import triage_agent

    result = await Runner.run(triage_agent, "What severity is ticket T-1004?", max_turns=6)
    kinds = [type(item).__name__ for item in result.new_items]
    assert any("ToolCall" in k for k in kinds), f"answered with no tool call. Items: {kinds}"


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_max_turns_is_enforced():
    from agents import Runner
    from agents.exceptions import MaxTurnsExceeded
    from first_agent import triage_agent

    with pytest.raises(MaxTurnsExceeded):
        await Runner.run(triage_agent, "Summarise every ticket one at a time.", max_turns=1)
```

**Line by line:**

- `@pytest.mark.asyncio` — needed to run an `async def` test. **This requires `pytest-asyncio`**, so
  add it: `uv add --dev "pytest-asyncio==1.4.0"`, and set `asyncio_mode = "auto"` under
  `[tool.pytest.ini_options]` in `pyproject.toml` if you would rather not repeat the marker.
- `test_model_string_is_a_pinned_litellm_provider_string` — asserts both the provider prefix and the
  absence of a placeholder. The second half is Day 1's placeholder test following you forward.
- `test_usage_reporting_is_requested` and `test_temperature_is_pinned` — **tests on configuration.**
  They look trivial and they are exactly the tests that catch a "cleanup" commit on Day 40 that
  removes `ModelSettings` because "the defaults are fine".
- `test_sdk_agent_matches_the_naked_agent_on_T_1001` — the **equivalence test**, and the most
  important one today. It asserts the framework did not change the answer. When you rebuild the same
  slice four times in Phase 9, this is the test that keeps all four honest.
- `test_max_turns_is_enforced` — pins that the SDK's cap behaves like yours. Note the exception is
  `MaxTurnsExceeded` from `agents.exceptions`; **verify that import path in 0.22.0** before
  assuming it.

---

## §6 Traps

- **`import openai_agents`.** The package is `openai-agents`; the module is `agents`.
- **Forgetting `set_tracing_disabled(True)`.** Every run tries to reach OpenAI, and the errors do not
  obviously say "tracing".
- **Using the `model="litellm/..."` string form** without a `MultiProvider` in a `RunConfig`. It
  fails, and the failure does not point at the missing provider.
- **Assuming usage is populated.** Several LiteLLM backends omit it unless you pass
  `include_usage=True`. On $0 that is your budget line going dark.
- **A tool docstring written for humans.** It is the model's schema description. Write it for the
  model, in `Args:` form.
- **Missing type hints on a tool.** The schema is generated from them; without hints you get
  something useless or an error.
- **Expecting your Day-6 router to be used.** It is not. The SDK owns its loop. Record that in
  ADR-001 rather than being surprised in Phase 9.
- **Forgetting `pytest-asyncio`.** Async tests silently skip or error in a confusing way.
- **Not reading `result.new_items`.** It is the SDK's version of your transcript, and it is where
  every trajectory test comes from.

---

## §7 Request budget

| Activity | Requests |
|---|---|
| Getting `first_agent.py` running | ~15 (Groq) |
| `wire_shapes.py` | 2 (Groq) |
| Cassette recording (4 tests) | ~6 |
| Iteration | ~10 |
| **Total** | **≈ 33, Groq** |

---

## §8 Verify before you code

Written **2026-08-20** against `openai-agents` **0.22.0**, checked live that day. Confirm before you
rely on any of it:

- `https://openai.github.io/openai-agents-python/models/` — the **third-party adapters** section:
  `LitellmModel` import path, constructor arguments, and the `ModelSettings(include_usage=True)`
  note. The docs describe the adapter as **best-effort and beta**, and explicitly say to validate
  your provider for structured output, tool calling and usage reporting. Do that on Day 11.
- `https://openai.github.io/openai-agents-python/tools/` — `@function_tool` vs `@tool` (equivalent),
  docstring formats parsed by `griffe` (google/sphinx/numpy), `name_override`,
  `failure_error_function`, `timeout`.
- `https://openai.github.io/openai-agents-python/quickstart/` — the current `Runner` surface.
- `https://platform.openai.com/docs/api-reference/responses` — skim the Responses shape for OAI-02.
  You will not call it; you need to be able to describe it.
- `agents/exceptions.py` in the installed package — confirm `MaxTurnsExceeded`'s import path.

Anything that differs from this lesson is a **finding**: log it in `docs/CHANGELOG_PLAN.md`
(Principle 14).

---

## §9 Say it in an interview

> "I ran the Agents SDK for three months without an OpenAI key. The primitives — agents, tools,
> handoffs, guardrails, sessions, structured output — all work over the LiteLLM adapter against Groq
> and Gemini, which speak Chat Completions. What doesn't work is anything that depends on Responses
> being stateful and hosting tools server-side: hosted web search, the code interpreter, server-held
> conversation state, the harness. That's not an arbitrary paywall — it's structural. You can't host
> a tool on a server that doesn't hold your session. Knowing *why* the boundary is where it is has
> been more useful to me than knowing where it is."

> "The one thing I lost by adopting the framework was my own provider-fallback router. The SDK owns
> the loop, so my Gemini→Groq→OpenRouter chain doesn't get consulted. I wrote that down in a decision
> record on the day I noticed, and it became a scoring row when I later compared four frameworks."

---

## §10 Done when

```bash
./m check
./m done 9
```

Tomorrow: tools and the Runner, properly — including what happens when a tool raises.
