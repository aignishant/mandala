---
day: 3
phase: 1
phase_name: "Agents from first principles"
title: "The loop, naked"
ids: ["AG-01", "AG-02"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 3 — The loop, naked

**Phase 1 · Agents from first principles** · IDs: **AG-01 🛠️**, **AG-02 🛠️**

> **Yesterday:** the workshop is built — pins, keys, CI, ten invented tickets.
> **Today:** you write an agent. About forty lines. No framework is allowed near this repo yet.
> **Tomorrow:** you make its output a shape your code can trust.

```bash
./m start 3
./m scaffold 3
```

---

## §1 The story

Everyone talks about agents like they are a new kind of thing. They are not. An agent is a
**while-loop with a model in it**, and once you have written one by hand you will never again be
confused by a framework, because you will recognise every framework as *a wrapper around this loop*.

Here is the whole idea, in the plan's own words: an agent is a loop where the model
**thinks → acts → observes → repeats** until it is done.

Let me tell it as a story instead.

You hire an assistant. They are extremely well-read, quick, and articulate. But they sit in a sealed
room. No internet, no phone, no filing cabinet. They can do exactly one thing: you slide a note under
the door, and they slide one back.

Now you want them to answer *"what is the severity of ticket T-1001?"*

They cannot know. They are sealed in a room, and T-1001 is a file on your laptop. So you make a
deal — a **protocol**:

> "If you need something from outside, don't guess. Write me a note in this exact format:
> `CALL get_ticket WITH {"ticket_id": "..."}`. I'll go look it up, and slide the answer back."

That is it. That is function calling (AG-02). The assistant never reads the file. **The assistant
asks your code to read the file.** Your code reads it and slides the result back in. Then the
assistant, now holding a fact it did not have a moment ago, writes the final answer.

And the loop (AG-01) is just: *keep sliding notes under the door until the note that comes back is an
answer rather than a request.*

Every agent framework in the world is a nicer envelope for that note. That is the entire secret, and
you get to know it on Day 3 instead of Day 40.

---

## §2 Setup — run this

No new packages today. `openai` from Day 1 is all you need — which is itself the point.

```bash
mkdir -p days/day-03/lab
touch days/day-03/lab/tools.py
touch days/day-03/lab/naked_agent.py
touch days/day-03/lab/demo.py
touch src/mandala/loop.py
touch tests/test_naked_agent.py
```

Confirm yesterday's work still holds before you build on it:

```bash
./m check
```

---

## §3 AG-01 — What an agent actually is

### The plain idea

A loop with four beats:

1. **Think** — send the conversation so far to the model; it decides what to do next.
2. **Act** — if it asked for a tool, run that tool in *your* code.
3. **Observe** — append the tool's result to the conversation as a new message.
4. **Repeat** — back to 1, until the model answers instead of asking, or you hit a cap.

Three things are worth noticing immediately, because they are the source of every agent bug you will
ever debug.

**First: the model is stateless.** It does not "remember" the last turn. Every single time you call
it, you resend the *entire* conversation. What looks like memory is you, re-reading the whole
transcript out loud, every time. (This is why context windows are a budget — that is tomorrow.)

**Second: the model never executes anything.** It emits *a request to execute*. Your code decides
whether to honour it. This is not a technicality — it is your entire security model. When you reach
the lethal trifecta on Day 65, the reason you can defend anything at all is that **the execution
decision was always yours.**

**Third: the loop must have a cap.** Without one, a confused model can ask for the same tool forever.
You will meet that failure properly on Day 5 (AG-05). Today, just put the cap in.

### Why Mandala needs it

Mandala's pipeline — Intake → Triage → Research → Resolve → Report — is this loop, five times, with
different tools and different permissions bolted on. If you understand today, you understand the
capstone. The remaining 87 days are about *control*, *durability* and *safety*, not about the loop.

---

## §4 AG-02 — Tool / function calling

### The plain idea

You describe a function to the model as **JSON Schema**: its name, what it does, what arguments it
takes. The model reads that description the way you read an API doc, and when it decides the
function would help, it emits a structured call — name plus arguments — instead of prose.

The single most important sentence about this: **the description field is a prompt.** It is not
documentation for humans. It is the only thing the model knows about your function. Compare:

```python
"description": "Gets a ticket."                       # vague -> the model guesses wrong

"description": ("Fetch one support ticket by its id, e.g. 'T-1001'. "
                "Use this whenever the user mentions a ticket id. "
                "Returns id, severity, category and body. Read-only.")   # this one works
```

Same function. Wildly different reliability. When a tool "does not get called", nine times out of ten
the description is the bug, not the model.

### Why Mandala needs it

Every capability Mandala will ever have — look up a ticket, search the docs, draft a reply, post that
reply — arrives as a tool. And because tools are how capability arrives, **tools are also how
permission is expressed.** On Day 8 the Researcher gets read tools and the Resolver gets write tools,
and neither gets both. That is Principle 6 and the lethal-trifecta defence in embryo. It starts here,
with a dictionary of functions.

---

## §5 The code

### 5.1 `days/day-03/lab/tools.py` — the tools and their schemas

```python
"""Day-3 tools. Both READ-ONLY (Principle 6).

A "tool" here is two things that must stay in sync:
  1. an ordinary Python function, and
  2. a JSON-Schema description the model reads to decide when to call it.

Usage
-----
    >>> from tools import TOOLS, TOOL_SCHEMAS
    >>> TOOLS["get_ticket"](ticket_id="T-1001")["severity"]
    'high'
"""

from __future__ import annotations

import json
import pathlib

TICKETS_PATH = pathlib.Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "tickets.json"


def _load_tickets() -> list[dict]:
    return json.loads(TICKETS_PATH.read_text(encoding="utf-8"))


def get_ticket(ticket_id: str) -> dict:
    """Fetch one ticket by id. Returns an error dict rather than raising."""
    for ticket in _load_tickets():
        if ticket["id"] == ticket_id:
            return ticket
    return {"error": f"no ticket with id {ticket_id}"}


def search_tickets(query: str, limit: int = 3) -> list[dict]:
    """Dumb substring search over ticket bodies. Deliberately dumb — see the note below."""
    needle = query.lower()
    hits = [t for t in _load_tickets() if needle in t["body"].lower()]
    return hits[:limit]


TOOLS = {
    "get_ticket": get_ticket,
    "search_tickets": search_tickets,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_ticket",
            "description": (
                "Fetch one support ticket by its exact id, e.g. 'T-1001'. "
                "Use this whenever the user names a ticket id. "
                "Returns id, severity, category and body. Read-only. "
                "Do NOT use this if you do not have an exact id — use search_tickets instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "The ticket id, in the form 'T-1001'.",
                    }
                },
                "required": ["ticket_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_tickets",
            "description": (
                "Find tickets whose body contains a phrase. Use when you do NOT have an exact "
                "ticket id. Matches literal substrings only — it does not understand synonyms. "
                "Read-only."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "A literal phrase to look for."},
                    "limit": {"type": "integer", "description": "Max results. Default 3."},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
]
```

**Line by line:**

- `TICKETS_PATH = pathlib.Path(__file__).resolve().parents[3] / ...` — build the path to the golden
  set from *this file's* location.
  - `__file__` is `days/day-03/lab/tools.py`.
  - `.resolve()` makes it absolute.
  - `.parents` is a sequence walking upwards: `parents[0]` = `lab`, `[1]` = `day-03`, `[2]` = `days`,
    `[3]` = the repo root.
  - Then `/ "tests" / "fixtures" / "tickets.json"`.
  - **Why not just `"tests/fixtures/tickets.json"`?** Because that is relative to wherever you happen
    to run the script from, and it will break the first time you run it from another folder. Paths
    anchored to `__file__` never do.
- `def _load_tickets()` — the leading underscore marks it private to this module. It re-reads the
  file on every call, which is deliberately wasteful and deliberately simple: today you want zero
  caching subtleties between you and understanding the loop.
- `return {"error": f"no ticket with id {ticket_id}"}` — **the tool returns an error value, it does
  not raise.** This is a real design decision. A raised exception kills your loop; an error *value*
  goes back to the model as an observation, and the model can react to it — by apologising, by
  trying `search_tickets`, by asking the user. Tool errors are information, not crashes. You will
  formalise this on Day 6 (AG-08) and industrialise it on Day 49 (LG-14).
- `needle = query.lower()` and `... in t["body"].lower()` — case-insensitive substring match.
- `hits[:limit]` — slice the first `limit` results. Slicing past the end is safe in Python; no
  bounds check needed.
- **Why `search_tickets` is deliberately dumb:** it matches literal substrings and nothing else. On
  Day 46 you replace it with embeddings, and the comparison — "*login loop*" failing to find an
  "*auth redirect bug*" ticket — is what makes the RAG day land. Building the weak version first is
  Principle 2.
- `TOOLS = {...}` — the name→function lookup. The loop uses this to dispatch. **The key must exactly
  match the schema's `name`**; a mismatch is the single most common Day-3 bug.
- `"type": "function"` — the wrapper the API expects around each tool definition.
- `"description"` on the *function* — the prompt. Note the closing sentence on `get_ticket`:
  *"Do NOT use this if you do not have an exact id."* **Negative guidance disambiguates overlapping
  tools better than positive guidance does.** With two search-ish tools, that one line is what stops
  the model flipping a coin.
- `"parameters"` — a JSON Schema object describing the arguments.
- `"properties"` — one entry per argument, each with its own `description`. Argument descriptions are
  prompts too; an undescribed argument gets filled by vibe.
- `"required": ["ticket_id"]` — arguments the model must supply. `limit` is absent from
  `search_tickets`' required list, so the model may omit it and Python's default applies.
- `"additionalProperties": False` — reject arguments you did not declare. Without it, some models
  invent an extra field, your `fn(**args)` raises `TypeError`, and you spend twenty minutes on it.

### 5.2 `days/day-03/lab/naked_agent.py` — the loop

```python
"""The agent loop, written by hand. No framework. About forty lines.

Run:
    uv run python days/day-03/lab/demo.py "What severity is ticket T-1001?"
"""

from __future__ import annotations

import json

from openai import OpenAI

from mandala.config import load_keys
from mandala.models import PROVIDERS
from tools import TOOL_SCHEMAS, TOOLS

SYSTEM_PROMPT = (
    "You are Mandala's support assistant. "
    "You answer questions about support tickets using the tools provided. "
    "NEVER invent a ticket id, a severity, or ticket contents. "
    "If a ticket does not exist, say so plainly. "
    "If you do not have enough information, say what you would need."
)

_provider = PROVIDERS["groq"]
_client = OpenAI(api_key=load_keys().groq, base_url=_provider.base_url)


def run(user_message: str, max_turns: int = 6, verbose: bool = False) -> str:
    """Run the think->act->observe loop until the model answers, or max_turns is hit."""
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    for turn in range(1, max_turns + 1):
        # ---- THINK -------------------------------------------------------
        response = _client.chat.completions.create(
            model=_provider.default_model,
            messages=messages,
            tools=TOOL_SCHEMAS,
        )
        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        if verbose:
            _print_turn(turn, message)

        # ---- did it answer, or did it ask? -------------------------------
        if not message.tool_calls:
            return message.content or ""

        # ---- ACT + OBSERVE ------------------------------------------------
        for call in message.tool_calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments)
                result = TOOLS[name](**args)
            except (KeyError, TypeError, json.JSONDecodeError) as exc:
                result = {"error": f"{type(exc).__name__}: {exc}"}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result),
                }
            )
            if verbose:
                print(f"      -> {json.dumps(result)[:160]}")

    raise RuntimeError(f"agent did not finish within {max_turns} turns")


def _print_turn(turn: int, message) -> None:
    print(f"\n[turn {turn}] assistant")
    if message.content:
        print(f"      says: {message.content[:200]}")
    for call in message.tool_calls or []:
        print(f"      calls: {call.function.name}({call.function.arguments})")
```

**Line by line — the setup:**

- `from tools import TOOL_SCHEMAS, TOOLS` — a plain import because `demo.py` runs from the same
  folder. (In `src/mandala/` you will use package-relative imports; lab files stay simple.)
- `SYSTEM_PROMPT = (...)` — Python concatenates adjacent string literals, so several quoted lines
  inside parentheses become one string with no `+` and no stray newlines.
- *"NEVER invent a ticket id"* — this line is **load-bearing**. It is what makes the second test in
  §7 pass, and getting it right is a prompt-engineering exercise, not a coding one. This is the
  honest introduction to the fact that in this field **the prompt is part of the source code**.
- `_provider = PROVIDERS["groq"]` / `_client = OpenAI(...)` — module-level, so the client is built
  once. Groq for the dev loop: fastest iteration, most generous request-per-day allowance.
  `model=` comes from the pinned constants — never a string literal (Principle 4).

**Line by line — the loop:**

- `messages: list[dict] = [...]` — the conversation. **This list is the agent's entire memory.** It
  grows as the loop runs, and it is resent in full on every call.
- `{"role": "system", ...}` — instructions that apply to the whole conversation.
- `{"role": "user", ...}` — the request.
- `for turn in range(1, max_turns + 1):` — the cap. `range(1, 7)` gives 1…6, so turn numbers read
  naturally in the output.
- `_client.chat.completions.create(...)` — **THINK.** Send everything; get back the model's next move.
- `tools=TOOL_SCHEMAS` — tells the model which tools exist. Omit it and the model has no door to the
  outside world (see §6, experiment 1).
- `response.choices[0].message` — `choices` is a list because the API can return several candidates;
  you asked for one.
- `messages.append(message.model_dump(exclude_none=True))` — **append the assistant's own message
  before appending any tool result.** The conversation must read *assistant asks → tool answers*.
  Drop the ask and the model sees an answer to a question nobody posed, and behaves bizarrely.
  - `model_dump()` converts the Pydantic response object into a plain dict, which is what the API
    expects on the way back in.
  - `exclude_none=True` strips fields that are `None`. Some providers reject `{"content": null}`
    even though they sent it to you. This one flag prevents a genuinely baffling class of 400s.
- `if not message.tool_calls: return message.content or ""` — **the exit condition.** No tool calls
  means the model answered. The `or ""` guards against `content` being `None`, so the function
  always returns a string as its type hint promises.
- `for call in message.tool_calls:` — a model may request **several tools in one turn**. Handle all
  of them; do not assume one.
- `args = json.loads(call.function.arguments)` — the arguments arrive as a **JSON string**, not a
  dict. You must parse it.
- `TOOLS[name](**args)` — look the function up by name and call it. `**args` unpacks the dict into
  keyword arguments, so `{"ticket_id": "T-1001"}` becomes `get_ticket(ticket_id="T-1001")`.
- `except (KeyError, TypeError, json.JSONDecodeError) as exc:` — the three ways this realistically
  fails: the model invented a tool name (`KeyError`), invented an argument (`TypeError`), or emitted
  malformed JSON (`JSONDecodeError`).
- `result = {"error": ...}` — again: **feed the failure back as an observation.** The model gets to
  see what it did wrong and correct itself on the next turn. That single decision is the difference
  between an agent that recovers and one that crashes.
- `"tool_call_id": call.id` — **copy the id from the call you are answering.** It is the thread
  connecting "you asked" to "here is the answer". Get it wrong and the model loses track (§6,
  experiment 2).
- `"content": json.dumps(result)` — tool results must be **strings**. Returning a dict raises a
  validation error inside the client library.
- `raise RuntimeError(f"agent did not finish within {max_turns} turns")` — reached only if the loop
  runs out. Failing loudly is right: a loop that cannot terminate is worse than one that gives up.

**Line by line — the printer:**

- `for call in message.tool_calls or []:` — `tool_calls` is `None` when the model answered rather
  than asked. `or []` turns that into an empty list so the `for` is always safe. This idiom appears
  constantly in agent code.
- `message.content[:200]` — truncate for readability. You want to *see* the loop, not drown in it.

### 5.3 `days/day-03/lab/demo.py`

```python
"""Print the whole conversation so you can see the loop happen.

Run:
    uv run python days/day-03/lab/demo.py "What severity is ticket T-1001?"
    uv run python days/day-03/lab/demo.py "Any tickets about invoices?"
    uv run python days/day-03/lab/demo.py "Summarise ticket T-9999."
"""

import sys

from naked_agent import run

question = " ".join(sys.argv[1:]) or "What severity is ticket T-1001?"
print(f"user: {question}")

answer = run(question, max_turns=6, verbose=True)

print("\n--- final answer ---")
print(answer)
```

**Line by line:**

- `import sys` — for `sys.argv`, the list of command-line arguments.
- `sys.argv[1:]` — everything after the script name. The slice drops `argv[0]`.
- `" ".join(...)` — rejoin the words, so you do not have to quote the question in the shell (though
  quoting is still safer if it contains `?` or `*`).
- `or "What severity is ticket T-1001?"` — an empty list joins to `""`, which is falsy, so this
  supplies a default when you run the script bare.
- `verbose=True` — **print every turn.** You cannot debug what you cannot see. This is Principle 8
  ("the trace is the truth") in its cheapest possible form; on Day 14 it becomes real tracing.

Run it:

```bash
cd days/day-03/lab
uv run python demo.py "What severity is ticket T-1001?"
cd ../../..
```

- `cd days/day-03/lab` first, because `demo.py` does `from naked_agent import run` and Python looks
  for modules alongside the script being run.

---

## §6 Watch it break

Three experiments. They take five minutes and teach more than the happy path.

**1. Remove the model's door.** Delete `tools=TOOL_SCHEMAS` from the `create(...)` call and ask about
T-1001 anyway.

The model will cheerfully **invent** a ticket. This is your first hallucination, and it is not a
model defect: you asked a sealed-room assistant a question about the outside world and gave it no
door. Put the line back.

**2. Break the thread.** Change `"tool_call_id": call.id` to `"tool_call_id": "wrong"`.

Most providers return a 400. Some silently confuse the conversation and produce nonsense. Either way
you now know what that id is for.

**3. Cap it at one.** Run with `max_turns=1` and ask something requiring a lookup.

You get the `RuntimeError`. Good. Now imagine that `for` were a `while True` — that is a few hundred
requests and your daily quota, gone, in about ninety seconds.

**4. (Optional, and the most instructive.)** Give both tools the *same* vague description
(`"Finds tickets."`) and ask three questions. Watch the model pick badly or call both. Then restore
the *"Do NOT use this if you do not have an exact id"* line and watch it fix itself.

That last one is the beginning of AG-07 (Day 6). Tool descriptions are API design for a reader who
is fast, literal, and has never met your codebase.

---

## §7 The eval that must be able to fail

First promote the loop into the package so later days can import it:

```python
# src/mandala/loop.py
"""The naked agent loop, reusable. Days 4-8 build on this file.

Usage
-----
    >>> from mandala.loop import run_loop
    >>> run_loop(messages=[...], tools={...}, schemas=[...], model="...", client=client)
"""
```

Copy `run()` from `naked_agent.py` into `run_loop()` here, but **take the client, tools, schemas and
model as parameters** rather than reading them from module-level globals. That single change is what
makes it testable and reusable — and it is the same refactor every framework has already made for
you, which is exactly why you should do it once by hand.

### `tests/test_naked_agent.py`

```python
"""Day-3 behaviour tests. Cassette-backed, so they replay free and offline."""

import pytest


@pytest.mark.vcr
def test_agent_uses_the_tool_rather_than_inventing():
    """The severity must come from the fixture file, not from the model's imagination."""
    from naked_agent import run

    answer = run("What severity is ticket T-1001?", max_turns=6)
    assert "high" in answer.lower()


@pytest.mark.vcr
def test_agent_refuses_unknown_tickets():
    """T-9999 does not exist. An honest agent says so; a flattering one makes something up."""
    from naked_agent import run

    answer = run("Summarise ticket T-9999 for me.", max_turns=6).lower()
    assert any(
        phrase in answer
        for phrase in ("no ticket", "not found", "doesn't exist", "does not exist", "could not find")
    ), f"agent did not admit the ticket is missing. It said: {answer!r}"


def test_loop_gives_up_rather_than_spinning(monkeypatch):
    """A capped loop that cannot finish must raise, not loop forever. No network needed."""
    from mandala.loop import run_loop

    class AlwaysAsksForATool:
        """A fake client that always requests a tool, so the loop can never exit normally."""

        class _Call:
            id = "call_1"

            class function:  # noqa: N801 - mimicking the SDK's shape
                name = "get_ticket"
                arguments = '{"ticket_id": "T-1001"}'

        def create(self, **kwargs):
            raise NotImplementedError("wire this to your run_loop signature")

    with pytest.raises(RuntimeError, match="did not finish"):
        run_loop(..., max_turns=2)
```

**Line by line:**

- `@pytest.mark.vcr` — from `pytest-recording`. On the first run **with `-m live`** it records the
  HTTP exchange into `tests/fixtures/cassettes/<test_name>.yaml`; on every run after, it replays.
  Your Day-2 `vcr_config` strips the auth headers before anything is written.
- `from naked_agent import run` **inside** the test — a local import. Importing at module level
  would construct the OpenAI client at collection time, which would fail on a machine with no keys
  and break CI. Deferring the import to inside the test keeps collection free of side effects.
- `assert "high" in answer.lower()` — check the fact, case-insensitively.
- `any(phrase in answer for phrase in (...))` — accept several honest phrasings. Testing a language
  model's output means testing a *set* of acceptable answers, never one exact string. Over-specific
  assertions are the number-one cause of flaky agent tests.
- `f"...It said: {answer!r}"` — put the actual answer in the failure message. When this goes red at
  11pm you want to see what it said, not go and re-run it by hand.
- `test_loop_gives_up_rather_than_spinning` — **no marker, no network.** A pure unit test of your
  own control flow, using a fake client that always requests a tool so the loop can never exit
  normally.
- `with pytest.raises(RuntimeError, match="did not finish"):` — assert both the type and the message.
- `raise NotImplementedError("wire this to your run_loop signature")` — **this is yours to finish.**
  The fake client's `create()` must return an object shaped like the SDK's response
  (`.choices[0].message.tool_calls`), and the exact shape depends on the `run_loop` signature you
  chose. Writing this stub is the rep: it forces you to notice precisely which parts of the SDK
  response your loop actually depends on. That is a genuinely useful thing to know about your own
  code.

The second test — `test_agent_refuses_unknown_tickets` — will probably be **red on your first
attempt.** Making it green is prompt work: your system prompt must forbid inventing tickets clearly
enough that the model complies.

Record the cassettes once, then run free forever:

```bash
uv run pytest tests/test_naked_agent.py -m live        # records; costs ~2 requests
uv run pytest tests/test_naked_agent.py               # replays; costs 0
grep -ril "gsk_\|sk-\|AIza" tests/fixtures/cassettes/ # must print NOTHING
```

- `grep -ril` — `-r` recursive, `-i` case-insensitive, `-l` list filenames only. **Run this every
  time you record a cassette.** A leaked key in a committed fixture is the worst outcome available
  today.

---

## §8 Build brief

| File | What goes in it | Yours to write? |
|---|---|---|
| `days/day-03/lab/tools.py` | `get_ticket`, `search_tickets`, `TOOLS`, `TOOL_SCHEMAS` | Type it out — do not paste blindly |
| `days/day-03/lab/naked_agent.py` | `SYSTEM_PROMPT`, `run()`, `_print_turn()` | **Yes** — this is the day |
| `days/day-03/lab/demo.py` | the CLI wrapper | Given above |
| `src/mandala/loop.py` | `run_loop()` — the same loop, but parameterised | **Yes** — the refactor is the lesson |
| `tests/test_naked_agent.py` | the three tests | **Yes**, especially the fake client |

**Constraints today** (these are the reps):

- No framework imports. `openai`, `json`, `pathlib`, stdlib. That is the list.
- Both tools **read-only** (Principle 6). Nothing writes to disk or the network.
- `max_turns` never defaults above 6.
- The model id comes from `mandala.models`, never a literal (Principle 4).
- `demo.py` prints the **whole** conversation, tool messages included.

---

## §9 Request budget

| Activity | Requests |
|---|---|
| Getting the loop working | ~15–25 (Groq) |
| The four break-it experiments | ~8 (Groq) |
| Recording two cassettes | 2 |
| **Total** | **≈ 35, all Groq** |

Groq's daily allowance covers this comfortably. **Do not develop this loop against Gemini** — you
need Gemini's requests-per-day on heavier days, and Groq is faster to iterate against anyway.
Routing by shape rather than by preference is AG-26 in miniature.

Log the actual number in `docs/RATE_BUDGET.md` §3.

---

## §10 Traps

- **Appending the tool result without first appending the assistant's message.** The conversation
  must read *assistant asks → tool answers*.
- **`tool_call_id` mismatch.** Copy it from the call you are answering. Always.
- **Returning a Python object as tool content.** `json.dumps` it. Content must be a string.
- **A `while True` with no cap.** Ten minutes and a few hundred requests later, you will care.
- **Assuming one tool call per turn.** Models batch. Loop over `message.tool_calls`.
- **Forgetting `exclude_none=True`.** Produces 400s that read like nothing is wrong.
- **Letting a tool raise.** Catch it and return an error *value* so the model can recover.
- **Making the tools clever.** Today's tools are dumb lookups. Cleverness in tools hides agent
  failures — the agent looks smart because the tool did the thinking.
- **Reaching for a framework "just to see".** Not yet. Principle 2 exists precisely because the
  naked version is only interesting *before* you have seen the convenient one.

---

## §11 Verify before you code

Written **2026-08-20** against `openai` **3.3.1**.

- `https://platform.openai.com/docs/guides/function-calling` — the tool-call message shape. This is
  the part most likely to have drifted; confirm the `tool_calls` / `tool_call_id` field names and
  whether `additionalProperties: false` is still accepted.
- `https://console.groq.com/docs/tool-use` — which Groq models support tool calling, and which
  parameters Groq silently ignores.
- `src/mandala/models.py` — is `FAST_LOOP` still a live model id? Rosters rotate.

If any shape differs from this lesson, **that is a finding.** Log it in `docs/CHANGELOG_PLAN.md`
(Principle 14) rather than silently patching around it.

---

## §12 Say it in an interview

> "An agent is a loop: the model proposes, my code disposes. The model never touches anything — it
> emits a structured request and my code decides whether to run it. That separation is the whole
> security story. And tool descriptions are prompts, not comments: when a tool isn't being called
> reliably I rewrite the description before I touch the model, usually by adding an explicit
> 'don't use this when…' line, because negative guidance disambiguates overlapping tools better
> than positive guidance does."

---

## §13 Done when

```bash
./m check
./m done 3
```

Tomorrow you stop accepting prose from the model and start demanding a shape.
