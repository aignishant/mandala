---
day: 37
phase: 6
phase_name: "LangChain 1.x"
title: "Messages, content blocks, and schema-first tools"
ids: ["LC-03", "LC-04"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 37 — Messages, content blocks, and schema-first tools

**Phase 6 · LangChain 1.x** · IDs: **LC-03 🛠️**, **LC-04 🛠️**

> **Yesterday:** three providers behind one factory, and an honest note about what the abstraction
> does not cover.
> **Today:** the other half of the abstraction. `content` stops being a string and becomes a list of
> **typed blocks** — text, reasoning, citations, tool calls — with one shape across vendors. Then
> tools, defined schema-first, with runtime injection instead of prompt stuffing.
> **Tomorrow:** `create_agent` ties the two together, and `TriageResult` runs for the fourth time.

```bash
./m start 37
./m scaffold 37
```

---

## §1 The story

Yesterday's `provider_swap.py` printed `content=...` for three providers and you probably saw three
strings. That is the compatible-but-shallow view. Underneath, the three providers sent you quite
different things:

- Gemini may return **safety metadata** alongside text.
- Groq's `openai/gpt-oss-20b` is a **reasoning model** — Day 1 watched it burn a whole `max_tokens`
  budget on reasoning and return `content=''`.
- OpenRouter's Nemotron does the same, and leaks reasoning into text when truncated
  (`docs/RATE_BUDGET.md` §1b).

**A `str` cannot represent that.** "Reasoning" is not text you show a user, a citation is not prose,
and a tool call is not content at all. Pre-1.0 LangChain flattened everything into a string and made
you regex it back out. **Standard content blocks (LC-03) are 1.x's answer**, and they are the piece
of LangChain most worth stealing conceptually even if you never use the framework: *a model's reply
is a heterogeneous list, and pretending otherwise costs you on the day you need citations.*

The second half is LC-04, and it lands on something you have hit in three frameworks already. Day 12
called it context objects and dependency injection. Day 27 hit it as CrewAI's closure limitation. Day
31 solved it by passing typed state explicitly. The recurring problem:

> **A tool needs to know something the model must not be told.**

A ticket-lookup tool needs a database handle and a `request_id`. Put those in the prompt and you have
handed the model — and therefore anything that injects into the model — control over them. LangChain
1.x's answer is **runtime injection**: arguments the schema hides from the model and the runtime
fills in. §4 builds it and §5 tests that the model genuinely cannot see them.

---

## §2 Setup — run this

### 2.1 No new packages

```bash
grep -n 'langchain' pyproject.toml
```

- Everything today is in `langchain-core==1.6.0` and `langchain==1.3.16`, installed yesterday.

### 2.2 Create today's files

```bash
touch src/mandala/lc/tools.py
touch tests/test_lc_tools.py
mkdir -p days/day-37/lab
touch days/day-37/lab/block_survey.py
touch days/day-37/lab/injection_demo.py
```

- `lc/tools.py` is Mandala's tool surface for the fourth framework. **The functions underneath are
  not new** — `RAW_TICKETS` and the handbook have been there since Days 10 and 27. What is new is the
  declaration layer, and that is exactly the comparison the bake-off wants.
- `block_survey.py` costs 3 requests and is the LC-03 lab. `injection_demo.py` costs 0.

---

## §3 LC-03 — messages and content blocks

### 3.1 The four message types

| Class | Who wrote it | Mandala's use |
|---|---|---|
| `SystemMessage` | you | the behaviour contract (Day 6, AG-07) |
| `HumanMessage` | the user, or **untrusted input** | the ticket body |
| `AIMessage` | the model | replies, and **tool calls** |
| `ToolMessage` | your code | a tool's result, tagged with its call id |

**The row to stare at is `HumanMessage`.** In Mandala a "human" message is usually a *customer
ticket*, which is untrusted text written by a stranger (Day 29's task descriptions say so explicitly).
The class name suggests trust; the content deserves none. **The type system will not protect you
here** — that is Day 65's whole subject — and noticing the gap today is cheaper than noticing it
during a red-team exercise.

`ToolMessage` carries a `tool_call_id` linking it to the `AIMessage` that requested it. That id is
what turns a flat message list into a call graph, and it is what Day 75's tracing will hang spans off.

### 3.2 What a content block is

In 1.x, `message.content` may be a string *or* a list of typed blocks:

```python
[
    {"type": "reasoning", "reasoning": "the 500 affects all customers, so severity is high"},
    {"type": "text", "text": "This is a critical outage."},
    {"type": "citation", "url": "kb://outage-policy", "title": "Outage policy"},
]
```

**Line by line, and why each type earns its place:**

- `{"type": "text", ...}` — the part a user sees. If you only ever read this block type, you have the
  pre-1.0 behaviour and you have lost nothing.
- `{"type": "reasoning", ...}` — the model's thinking. **This is the block that matters most for
  Mandala**, and for a reason that is concrete rather than philosophical: Day 1 recorded that both
  `openai/gpt-oss-20b` and the Nemotron judge emit reasoning, and that a small `max_tokens` yields
  `content=''`. With blocks, "the model reasoned and produced no text" is *distinguishable* from "the
  model returned nothing". Those are different bugs and you have been unable to tell them apart for
  thirty-six days.
- `{"type": "citation", ...}` — a source, structured. Day 29's crew guardrail
  (`must_cite_a_ticket`) parses citations **out of prose with a regex** because that was the only
  option. A typed citation block is the same requirement without the regex. Whether the free models
  actually emit these is an open question and §3.3 answers it empirically.
- Tool calls live on `message.tool_calls`, not in `content`. Know that; it is a common confusion and
  it will bite you on Day 38.

**The claim to test:** one shape across providers. Yesterday found the abstraction leaking mildly at
the key-argument level. Today asks whether it holds where it matters more.

### 3.3 `days/day-37/lab/block_survey.py`

```python
"""What does each provider actually put in `content`? Ask, do not assume.

Run:
    uv run python days/day-37/lab/block_survey.py

Budget: 3 requests, one per provider.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from mandala.lc.chat import fast_loop, judge, workhorse

PROMPT = [
    SystemMessage(
        "You are a support triage analyst. Think briefly, then answer in one sentence, "
        "and cite the source you relied on."
    ),
    HumanMessage("Checkout returns HTTP 500 for every customer since the 14:02 deploy."),
]

for name, factory in [("workhorse", workhorse), ("fast_loop", fast_loop), ("judge", judge)]:
    try:
        reply = factory(temperature=0.0).invoke(PROMPT)
    except Exception as exc:                     # noqa: BLE001 - surveying failure modes
        print(f"{name:<10} FAILED {type(exc).__name__}: {str(exc)[:80]}")
        continue

    content = reply.content
    if isinstance(content, str):
        print(f"{name:<10} content is a STR ({len(content)} chars) -- no blocks")
    else:
        kinds = [block.get("type", "?") if isinstance(block, dict) else type(block).__name__
                 for block in content]
        print(f"{name:<10} content is a LIST of {len(content)}: {kinds}")

    print(f"{'':<10} tool_calls={len(reply.tool_calls)}  "
          f"finish={reply.response_metadata.get('finish_reason')}  "
          f"usage={reply.usage_metadata}")
```

**Line by line:**

- The system prompt asks for **three things** — think, answer, cite — because that is what maximises
  the chance of seeing three block types. If a provider returns a bare string anyway, that is the
  answer to today's question and it is worth knowing.
- `isinstance(content, str)` first — **1.x did not make `content` always a list.** Handling both is
  not defensive clutter; it is the actual contract, and any code you write that assumes a list will
  crash on the first provider that sends a string.
- `block.get("type", "?")` with an `isinstance(block, dict)` fallback — blocks may arrive as dicts or
  as typed objects depending on version and provider. Printing the class name when it is not a dict
  tells you which world you are in rather than raising.
- `reply.tool_calls` printed even though nothing was bound — confirms it is a **separate attribute**
  from `content` (§3.2's common confusion), and that it is an empty list rather than `None`.
- `finish_reason` — **this is the Day-1 mystery solved.** When Groq returned `content=''`, the
  distinguishing fact was `finish_reason='length'`. Print it every time you print content and the
  empty-reply confusion never recurs.
- `usage_metadata` — LangChain's normalised token counts. **Compare its keys across providers**: if it
  is genuinely uniform, that is a stronger vendor-neutrality result than anything yesterday produced,
  because token accounting is where vendors differ most and where `RATE_BUDGET.md` needs consistency.

### 3.4 What to write down

1. Which providers returned a **list**, and which a **string**?
2. Did any emit a `reasoning` block? A `citation` block?
3. Is `usage_metadata` the same shape for all three?
4. **If citations do not arrive as blocks on free models**, Day 29's regex guardrail stays necessary.
   Write that down as a finding, not a disappointment: *the abstraction is real, and the free-tier
   models do not exercise all of it.* That distinction is exactly the kind of nuance a bake-off
   scorecard needs.

---

## §4 LC-04 — schema-first tools and runtime injection

### 4.1 `src/mandala/lc/tools.py`

```python
"""Mandala's tools, LangChain-flavoured. Fourth framework, same functions.

Two things are new here and neither is the function bodies:

  1. SCHEMA-FIRST -- the argument schema is a Pydantic model, not inferred from
     the signature. The model sees the schema; the schema is the contract.
  2. RUNTIME INJECTION -- some arguments are filled by the runtime and are
     invisible to the model. That is where the request_id and the permission
     check live, and it is why the model cannot forge either.

Blast radius (Principle 6): every tool here is READ-ONLY. Mandala's first write
is Day 82, behind the Day-33 approval gate.

Usage
-----
    >>> from mandala.lc.tools import READ_TOOLS
    >>> [t.name for t in READ_TOOLS]
    ['lookup_ticket', 'search_handbook']
"""

from __future__ import annotations

from typing import Annotated

from langchain_core.tools import InjectedToolArg, tool
from pydantic import BaseModel, Field

from mandala.kb import search_handbook as _search_handbook
from mandala.sdk_tools import RAW_TICKETS


class LookupTicketArgs(BaseModel):
    """What the MODEL is allowed to choose. Nothing else reaches the function."""

    ticket_id: str = Field(
        pattern=r"^T-\d{4}$",
        description="A Mandala ticket id such as T-1004. Never invent one.",
    )


@tool("lookup_ticket", args_schema=LookupTicketArgs)
def lookup_ticket(
    ticket_id: str,
    request_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Return the summary of one ticket. Read-only."""
    record = RAW_TICKETS.get(ticket_id)
    if record is None:
        return f"no ticket {ticket_id}"
    return f"[{request_id}] {ticket_id}: {record['summary']}"


class SearchHandbookArgs(BaseModel):
    query: str = Field(min_length=3, max_length=200, description="A policy question.")
    k: int = Field(default=3, ge=1, le=5, description="How many passages to return.")


@tool("search_handbook", args_schema=SearchHandbookArgs)
def search_handbook(
    query: str,
    k: int = 3,
    request_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Search Mandala's support handbook. Read-only."""
    hits = _search_handbook(query, k=k)
    return "\n".join(f"[{request_id}] {h}" for h in hits)


READ_TOOLS = [lookup_ticket, search_handbook]
```

**Line by line:**

- `@tool("lookup_ticket", args_schema=LookupTicketArgs)` — **the name is explicit**, not inferred from
  the function. Rename the Python function and the model-facing tool name does not change, so a
  refactor cannot silently break a prompt or a trace query. Day 1's "pin everything" instinct applied
  to an identifier.
- `args_schema=` — **schema-first, and this is the LC-04 distinction.** LangChain *can* infer a schema
  from type hints. Supplying an explicit Pydantic model buys three things: field descriptions the
  model actually reads, validators that run before your code does, and a schema you can print, diff,
  and test. Compare Day 10 (SDK inferred it from the signature) and Day 25 (CrewAI's `BaseTool`) and
  write the ergonomics down.
- `pattern=r"^T-\d{4}$"` on `ticket_id` — **the single highest-value line in this file.** Day 29's
  Triage Analyst was told "invent nothing" in prose. Here it is a regex, enforced before the function
  runs. Prose is a request; a pattern is a wall. A hallucinated `T-9999` fails validation and the
  model gets a typed error back, which it can usually recover from — better than a lookup returning
  "not found" and the model concluding the ticket does not exist.
- `description=` on every field — this text goes **into the model's prompt**. It is not a docstring
  for humans. "Never invent one" is instruction, delivered where the model reads it.
- `k: int = Field(default=3, ge=1, le=5)` — bounded. Without `le=5` a model that asks for `k=500`
  gets 500 passages into your context window, and Day 4's AG-04 budget is gone in one tool call. **A
  numeric tool argument without a ceiling is a context-window vulnerability.**
- `request_id: Annotated[str, InjectedToolArg] = ""` — **the runtime-injection line.** `Annotated`
  attaches metadata to a type; `InjectedToolArg` is the marker telling LangChain to *strip this
  argument from the schema the model sees* and let the caller supply it. So the model cannot pass a
  `request_id`, cannot see one, and cannot forge one — while your function still receives it for
  correlation and tracing.
- Note `request_id` is **not** in `LookupTicketArgs`. That is the mechanism: the args schema is the
  model's view, the signature is the runtime's view, and they differ on purpose. §5 tests that they
  differ in the direction you intended.
- `from mandala.kb import search_handbook as _search_handbook` — aliased with a leading underscore so
  the tool can take the good name. Fourth framework wrapping the *same* underlying function, and that
  is the point: **the framework layer is a declaration, and the logic beneath it has not moved since
  Day 27.**
- `READ_TOOLS` as an exported list — one importable object naming the read-only set. Day 38's agent
  takes it wholesale, and Day 65 will ask "which tools does this agent hold?" and get an answer from
  one grep.

### 4.2 Why injection beats the prompt

The three alternatives you have already lived through:

| Approach | Where you met it | What goes wrong |
|---|---|---|
| Put it in the system prompt | Day 6 | the model can be talked into changing it (Day 65) |
| Close over it in a factory | Day 27 | one closure per request; CrewAI's limitation |
| Pass it in shared state | Day 31 | works, but *everything* sees it (state is global) |
| **Inject at call time** | **today** | the model never sees it; the runtime supplies it |

**Injection is the first of the four where the model's view and your view are genuinely different
objects.** That difference is a security boundary, and it is small enough to be worth stating
plainly: an argument the model cannot see is an argument the model cannot attack.

This is also where LangChain's answer is cleaner than what you built on Day 31. Say so in the
bake-off. Honest comparison means recording the wins too.

### 4.3 `days/day-37/lab/injection_demo.py` — 0 model requests

```python
"""Show the two views of the same tool: the model's, and the runtime's.

Run:
    uv run python days/day-37/lab/injection_demo.py

Budget: 0 requests. This is introspection, not inference.
"""

import json

from mandala.lc.tools import READ_TOOLS

for tool_obj in READ_TOOLS:
    schema = tool_obj.args_schema.model_json_schema()
    print(f"=== {tool_obj.name} ===")
    print(f"description : {tool_obj.description}")
    print(f"model sees  : {sorted(schema['properties'])}")
    print(f"required    : {sorted(schema.get('required', []))}")
    print(f"runtime sees: {sorted(tool_obj.func.__annotations__) - {'return'}}")
    print(json.dumps(schema, indent=2)[:400])
    print()
```

**Line by line:**

- `tool_obj.args_schema.model_json_schema()` — **the exact JSON Schema sent to the model.** Printing it
  is the single best habit in this lesson: it is the same technique whatever the framework, it
  answers "why did the model call that wrong" instantly, and it works with no key and no quota.
- `sorted(schema['properties'])` vs. `sorted(tool_obj.func.__annotations__)` side by side — **the two
  views, printed together.** `request_id` should appear in the second and not the first. If it appears
  in both, injection is not wired and every claim in §4.2 is false.
- `sorted(...) - {'return'}` — set difference; `__annotations__` includes the return annotation and
  you do not want it in the comparison. (Note this only works because `sorted()` is being subtracted
  as a set — write `set(tool_obj.func.__annotations__) - {"return"}` if that reads better to you, and
  prefer clarity over compactness in a teaching file.)
- `tool_obj.description` printed — it is assembled from the docstring and goes to the model. Reading
  it back is how you catch a docstring that describes the implementation rather than the contract.
- `json.dumps(schema, indent=2)[:400]` — truncated, because you are checking shape and the field
  descriptions, not reading a wall of JSON.

---

## §5 The eval that must be able to fail

### `tests/test_lc_tools.py`

```python
"""The model's view of a tool is a security surface. 0 model requests."""

import pytest
from pydantic import ValidationError

from mandala.lc.tools import READ_TOOLS, LookupTicketArgs, SearchHandbookArgs, lookup_ticket


def schema_of(name: str) -> dict:
    tool_obj = next(t for t in READ_TOOLS if t.name == name)
    return tool_obj.args_schema.model_json_schema()


def test_the_model_cannot_see_the_request_id():
    """THE injection test. Flip it: drop InjectedToolArg and watch this go red."""
    for name in ("lookup_ticket", "search_handbook"):
        assert "request_id" not in schema_of(name)["properties"], name


def test_the_runtime_still_receives_the_request_id():
    """The other half. Injection that drops the value is not injection."""
    out = lookup_ticket.func(ticket_id="T-1004", request_id="req-42")
    assert "req-42" in out


def test_a_hallucinated_ticket_id_is_refused():
    with pytest.raises(ValidationError):
        LookupTicketArgs(ticket_id="T-99999")


def test_a_prose_ticket_id_is_refused():
    with pytest.raises(ValidationError):
        LookupTicketArgs(ticket_id="the checkout one")


def test_k_is_bounded():
    """An unbounded k is a context-window vulnerability (AG-04)."""
    with pytest.raises(ValidationError):
        SearchHandbookArgs(query="refund policy", k=500)


def test_every_tool_field_has_a_description():
    """Field descriptions ARE the prompt. An undescribed field is an unprompted one."""
    for tool_obj in READ_TOOLS:
        props = tool_obj.args_schema.model_json_schema()["properties"]
        missing = [k for k, v in props.items() if not v.get("description")]
        assert missing == [], (tool_obj.name, missing)


def test_tool_names_are_explicit_not_inferred():
    assert {t.name for t in READ_TOOLS} == {"lookup_ticket", "search_handbook"}


def test_the_read_set_is_read_only():
    """Blast radius (Principle 6). Mandala's first write is Day 82, behind an approval."""
    for tool_obj in READ_TOOLS:
        source = tool_obj.func.__doc__ or ""
        assert "Read-only" in source, tool_obj.name


def test_no_tool_takes_a_free_text_identifier():
    """Every id-shaped argument must be pattern-constrained, not just typed str."""
    props = schema_of("lookup_ticket")["properties"]
    assert "pattern" in props["ticket_id"]
```

**Line by line:**

- `schema_of()` helper — the JSON Schema is fetched the same way in five tests, so it becomes a named
  function. Same habit as Day 31's `route_for()`.
- `test_the_model_cannot_see_the_request_id` is today's **flip-it test** and the most important one.
  Remove `InjectedToolArg` and the field reappears in the schema, which means the model can supply
  it, which means it can forge a correlation id in a trace. Small blast radius today, real one on Day
  75 when traces are how you know what happened.
- `test_the_runtime_still_receives_the_request_id` — the **negative-space sibling** (Day 32's rule
  again). A `request_id` that is hidden *and* dropped would pass the first test and be useless.
- `test_a_hallucinated_ticket_id_is_refused` and its prose sibling — two shapes of the same failure,
  tested separately so a failure report says which one broke. `T-99999` has too many digits;
  `"the checkout one"` is what a model actually produces when it does not know the id.
- `test_k_is_bounded` cites AG-04 in its docstring. **Tests are documentation with teeth**; a
  docstring naming the principle means the next reader knows why the bound exists and does not
  "helpfully" widen it.
- `test_every_tool_field_has_a_description` — the prompt-quality test. It will fail the day someone
  adds a field in a hurry, which is exactly the day the model starts guessing at its meaning.
- `test_the_read_set_is_read_only` greps the docstring, which is **weak and honest**: it asserts the
  declaration, not the behaviour. Real enforcement is `permissions.py` from Day 12 and the
  `blast_radius` field from Day 21. This test's job is to make the *claim* mandatory so its absence is
  visible. Say that limitation out loud rather than over-claiming.
- `test_no_tool_takes_a_free_text_identifier` generalises the `pattern` rule into a policy that a
  future tool must satisfy too.
- **No test invokes a model.** Everything here reads schemas and calls `.func` directly, which is why
  the whole file runs offline in CI with no keys — the property Day 74's regression gate depends on.

---

## §6 Traps

- **Assuming `content` is always a list.** It is not, and 1.x does not promise it is. Handle both.
- **Assuming `content` is always a string.** The pre-1.0 habit, and it silently drops reasoning and
  citations the day a provider starts sending them.
- **Looking for tool calls inside `content`.** They live on `message.tool_calls`.
- **Trusting `HumanMessage` because of its name.** In Mandala it is usually a stranger's text.
- **Letting the schema be inferred.** You lose descriptions, validators, and the ability to diff the
  contract. Inference is fine for a demo and wrong for a boundary.
- **Putting `request_id` in the args schema.** Then the model can set it, and your correlation id is
  model output.
- **An unbounded `k`, `limit`, or `count`.** One tool call eats the context window (AG-04).
- **A `str` id with no `pattern`.** The model will invent one; the regex is the only thing that says
  no.
- **Believing `"Read-only"` in a docstring makes a tool read-only.** It makes the claim greppable.
  Enforcement is `permissions.py`.
- **Concluding "no citation blocks on free models" means the feature is fake.** It means your models
  do not emit them. Record the distinction — the bake-off cares about it.

---

## §7 Request budget

**Declared: 3 model requests, Groq/Gemini/OpenRouter — one each.**

| What | Requests |
|---|---|
| `injection_demo.py` | **0** |
| `tests/test_lc_tools.py` | **0** |
| `block_survey.py` | 3 |

The pattern from yesterday holds: **schema and policy work is free; only the survey costs.** Three
days running now (Days 31, 36, 37) the expensive part has been a single deliberate probe. That is not
a coincidence, it is a design stance — and on a 50-request-a-day provider it is the difference
between finishing the phase and rationing it.

---

## §8 Verify before you code

Written **2026-08-20** against `langchain-core==1.6.0` / `langchain==1.3.16`:

- **`InjectedToolArg` import path** — `langchain_core.tools` is the assumption. Confirm; if it moved,
  log it (Principle 14).
- **Does `args_schema=` coexist with an injected arg not in the schema?** §4.1 depends on this exact
  combination working. If 1.3.16 requires the injected field *in* the schema and strips it later,
  §5's test still holds but the mechanism explanation in §4.1 needs correcting.
- **Are content blocks dicts or typed objects** in 1.6.0? `block_survey.py` handles both, but write
  the answer down — Day 40's streaming will care.
- **Is `usage_metadata` populated by all three adapters?** If one leaves it `None`, that is a
  `RATE_BUDGET.md` note: you cannot account for tokens you are not told about.
- **Is `reasoning` a standard block type**, or provider-specific in disguise? This is the strongest
  version of the LC-03 claim; check the docs rather than inferring from one run.
- **`@tool` vs. `@tool(...)`** — decorator and decorator factory both exist. Get the form right.
- `https://docs.langchain.com/oss/python/langchain/messages` and `.../tools` — read today.

---

## §9 Say it in an interview

> "LangChain 1.x makes a model's reply a list of typed content blocks — text, reasoning, citations —
> instead of one string, and that mattered concretely for me: two of my three free models are
> reasoning models that return empty text when the token budget is tight, and blocks plus
> `finish_reason` are what let me tell 'it thought and ran out' apart from 'it returned nothing'.
> On tools I went schema-first with an explicit Pydantic args schema, so ticket ids are
> pattern-constrained rather than politely requested in a prompt, and every numeric argument has a
> ceiling because an unbounded `k` is a context-window vulnerability. The part I'd call the real win
> is injected arguments: the request id is in the function signature but not in the schema the model
> sees, so it can't be forged. I'd built the same idea three other ways earlier in the project — a
> prompt variable, a closure, and shared state — and this is the first one where the model's view and
> the runtime's view are genuinely different objects."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 37
```
