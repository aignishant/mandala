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

> **Yesterday:** the workshop is built — pins, keys, CI, golden set.
> **Today:** you write an agent. About forty lines. No framework is allowed near this repo yet.
> **Tomorrow:** you make its output a shape your code can trust.

---

## §1 The story

Everyone talks about agents like they are a new kind of thing. They are not. An agent is a
**while-loop with a model in it**, and once you have written one by hand you will never again be
confused by a framework, because you will recognise every framework as *a wrapper around this loop*.

Here is the whole idea, in the plan's own words: an agent is a loop where the model
**thinks → acts → observes → repeats** until it is done.

Let me tell it as a story instead.

You hire an assistant. They are extremely well-read, quick, and articulate. But they sit in a sealed
room. No internet, no phone, no filing cabinet. They can only do one thing: you slide a note under
the door, and they slide one back.

Now you want them to answer "what is the weather in Pune?"

They cannot know. They are sealed in a room. So you make a deal — a **protocol**:

> "If you need something from the outside world, don't guess. Write me a note in this exact format:
> `CALL get_weather WITH {"city": "..."}`. I'll go find out, and slide the answer back under the door."

That is it. That is function calling (AG-02). The assistant never fetches the weather. **The
assistant asks your code to fetch the weather.** Your code does the fetching, and slides the result
back in. Then the assistant, now holding a fact it did not have a moment ago, writes the final
answer.

And the loop (AG-01) is just: *keep sliding notes under the door until the note that comes back is
an answer rather than a request.*

Every agent framework in the world is a nicer envelope for that note. That is the entire secret, and
you get to know it on Day 3 instead of Day 40.

---

## §2 AG-01 — What an agent actually is

### The plain idea

A loop with four beats:

1. **Think** — send the conversation so far to the model; it decides what to do next.
2. **Act** — if it asked for a tool, run that tool in *your* code.
3. **Observe** — append the tool's result to the conversation as a new message.
4. **Repeat** — go back to 1, until the model answers instead of asking, or you hit a cap.

Three things are worth noticing immediately, because they are the source of every agent bug you will
ever debug.

**First: the model is stateless.** It does not "remember" the last turn. Every single time you call
it, you resend the *entire* conversation. What looks like memory is you, re-reading the whole
transcript out loud, every time. (This is why context windows are a budget — that is tomorrow.)

**Second: the model never executes anything.** It emits *a request to execute*. Your code decides
whether to honour it. This is not a technicality — it is your entire security model. When you get to
the lethal trifecta on Day 65, the reason you can defend anything at all is that **the execution
decision was always yours**.

**Third: the loop must have a cap.** Without one, a confused model can ask for the same tool forever.
You will meet that failure on Day 5 (AG-05). Today, just put the cap in.

### Why Mandala needs it

Mandala's whole pipeline — Intake → Triage → Research → Resolve → Report — is this loop, five times,
with different tools and different permissions bolted on. If you understand today, you understand
the capstone; the remaining 87 days are about *control*, *durability*, and *safety*, not about the
loop.

### The smallest thing that works

Here is the shape. Note what it is *not* doing: no framework, no abstraction, no clever base class.

```python
# days/day-03/lab/naked_agent.py
import json
from openai import OpenAI
from mandala.config import load_keys
from mandala.models import FAST_LOOP        # pinned. Principle 4.

KEYS = load_keys()

# The plain `openai` library, pointed at Groq's OpenAI-compatible endpoint.
# Same client, free model, no OpenAI key. This is the $0 trick from plan §2.1.
client = OpenAI(api_key=KEYS.groq, base_url="https://api.groq.com/openai/v1")

# ---- 1. The tool: ordinary Python. Nothing magic about it. -------------------
def get_ticket(ticket_id: str) -> dict:
    """Look up one ticket from the golden set. READ-ONLY (Principle 6)."""
    tickets = json.loads(open("tests/fixtures/tickets.json").read())
    for t in tickets:
        if t["id"] == ticket_id:
            return t
    return {"error": f"no ticket {ticket_id}"}

TOOLS = {"get_ticket": get_ticket}

# ---- 2. The schema: how the model learns the tool exists ---------------------
TOOL_SCHEMAS = [{
    "type": "function",
    "function": {
        "name": "get_ticket",
        "description": "Fetch one support ticket by its id, e.g. 'T-1001'.",
        "parameters": {
            "type": "object",
            "properties": {"ticket_id": {"type": "string"}},
            "required": ["ticket_id"],
        },
    },
}]

# ---- 3. The loop ------------------------------------------------------------
def run(user_message: str, max_turns: int = 6) -> str:
    messages = [
        {"role": "system", "content": "You are Mandala's support assistant. "
                                      "Never invent ticket ids or ticket contents."},
        {"role": "user", "content": user_message},
    ]

    for turn in range(max_turns):
        # THINK
        response = client.chat.completions.create(
            model=FAST_LOOP, messages=messages, tools=TOOL_SCHEMAS,
        )
        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        # Did it answer, or did it ask?
        if not message.tool_calls:
            return message.content          # it answered. Loop ends.

        # ACT + OBSERVE
        for call in message.tool_calls:
            fn = TOOLS[call.function.name]
            args = json.loads(call.function.arguments)
            result = fn(**args)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,     # ← must match, or the model loses the thread
                "content": json.dumps(result),
            })

    raise RuntimeError(f"agent did not finish within {max_turns} turns")
```

Read that once more and count the lines that are *the agent*. It is the `for` loop. Everything else
is plumbing you would write for any HTTP client.

### Watch it break

Do these three. They take five minutes and they teach more than the happy path.

1. **Delete `tools=TOOL_SCHEMAS` from the call.** The model no longer knows the tool exists. Ask it
   about T-1001 anyway. It will cheerfully *invent* a ticket. This is your first hallucination, and
   it is not a model defect — you asked a sealed-room assistant a question about the outside world
   and gave it no door.
2. **Remove `tool_call_id` from the tool message.** Most providers will error; some will silently
   confuse the conversation. That id is the thread connecting "you asked" to "here's the answer".
3. **Set `max_turns=1`** and ask something needing a lookup. You get the `RuntimeError`. Good — a
   loop that cannot terminate is worse than one that gives up.

### Say it in an interview

> "An agent is a loop: the model proposes, my code disposes. The model never touches anything — it
> emits a structured request, and my code decides whether to run it. That separation is the whole
> security story, and every framework I've used is a nicer wrapper around exactly that loop."

---

## §3 AG-02 — Tool / function calling

### The plain idea

You describe a function to the model as **JSON Schema**: its name, what it does, what arguments it
takes. The model reads that description the way you read an API doc, and when it decides the function
would help, it emits a structured call — name plus arguments — instead of prose.

The single most important sentence about this: **the description field is a prompt.** It is not
documentation for humans. It is the only thing the model knows about your function. Compare:

```python
"description": "Gets a ticket."                      # vague → the model guesses wrong
"description": ("Fetch one support ticket by its id, e.g. 'T-1001'. "
                "Use this whenever the user mentions a ticket id. "
                "Returns severity, category and body. Read-only.")   # ← this one works
```

Same function. Wildly different reliability. When a tool "doesn't get called", nine times out of ten
the description is the bug, not the model.

### Why Mandala needs it

Every capability Mandala will ever have — look up a ticket, search the docs, draft a reply, post that
reply — arrives as a tool. And because tools are how capability arrives, **tools are also how
permission is expressed**. On Day 8 the Researcher agent will get read tools and the Resolver will
get write tools, and neither will get both. That is Principle 6 and the lethal-trifecta defence
(Day 65) in embryo. It starts here, with a dictionary of functions.

### Watch it break

Give the model *two* tools with overlapping descriptions — say `get_ticket` and
`find_ticket` — and watch it pick badly, or call both. Then rewrite one description to say exactly
when **not** to use it ("Do not use this if you already know the ticket id"). Watch it fix itself.

That exercise is the beginning of AG-07 (prompting as interface design, Day 6). Tool descriptions are
API design for a reader who is fast, literal, and has never met your codebase.

### Say it in an interview

> "Tool descriptions are prompts, not comments. When a tool isn't being called reliably, I rewrite
> the description before I touch the model or the temperature — including an explicit 'don't use this
> when…' line, because negative guidance disambiguates overlapping tools better than positive
> guidance does."

---

## §4 Build brief

```
days/day-03/lab/
  naked_agent.py       # TODO(me): the loop, from scratch. Do not copy-paste blindly —
                       #           type it, and get the tool_call_id wiring wrong once.
  tools.py             # TODO(me): get_ticket + search_tickets(query) — both READ-ONLY
  demo.py              # prints each turn: what the model asked, what came back
src/mandala/
  loop.py              # TODO(me): promote the loop here once it works.
                       #           Signature: run(messages, tools, model, max_turns) -> str
                       #           Days 4-8 all build on this file.
tests/
  test_naked_agent.py  # cassette-backed; see §5
```

**Constraints for today** (these are the reps):

- No framework imports. `openai`, `json`, stdlib. That's the list.
- Both tools are **read-only** (Principle 6). Nothing writes to disk or the network.
- `max_turns` is a required argument with no default over 6.
- The model id comes from `mandala.models`, never a literal string (Principle 4).
- `demo.py` must **print the whole conversation**, including the tool messages. You cannot debug
  what you cannot see (Principle 8, in its cheapest possible form).

---

## §5 The eval that must be able to fail

Two tests. One is about correctness, one is about honesty.

```python
# tests/test_naked_agent.py
import pytest
from mandala.loop import run

@pytest.mark.cassette
def test_agent_uses_the_tool_rather_than_inventing(cassette):
    """The severity must come from the fixture file, not from the model's imagination."""
    out = run("What severity is ticket T-1001?", ...)
    assert "high" in out.lower()
    assert cassette.tool_calls_made == ["get_ticket"]     # ← it actually looked it up

@pytest.mark.cassette
def test_agent_refuses_unknown_tickets(cassette):
    """T-9999 does not exist. An honest agent says so; a flattering one makes something up."""
    out = run("Summarise ticket T-9999.", ...)
    assert any(w in out.lower() for w in ("no ticket", "not found", "doesn't exist", "does not exist"))
```

The second test is the valuable one, and it will probably be **red on your first attempt**. Making
it green is a prompt-engineering exercise, not a code one: your system prompt has to forbid inventing
tickets clearly enough that the model complies. That is AG-07 arriving early, and it is the honest
introduction to the fact that in this field, *the prompt is part of the source code*.

**Record a cassette** for both (`pytest -m live` once to record, then it replays free forever).

---

## §6 Request budget

| Activity | Requests |
|---|---|
| Getting the loop working | ~15–25 (Groq — this is what Groq is for) |
| The three "watch it break" experiments | ~6 |
| Recording two cassettes | 2 |
| **Total** | **≈ 30, all on Groq** |

Groq's daily allowance comfortably covers this. Do **not** develop this loop against Gemini — you
will need Gemini's request-per-day budget on heavier days, and Groq is faster for iteration anyway.
Routing by shape rather than by preference is AG-26 in miniature.

---

## §7 Traps

- **Forgetting to append the assistant's own message** before appending the tool result. The
  conversation must read: *assistant asks → tool answers*. If you drop the ask, the model sees an
  answer to a question nobody posed, and behaves bizarrely.
- **`tool_call_id` mismatch.** Copy it from the call you are responding to. Always.
- **Returning a Python object from a tool.** Tool results must be strings — `json.dumps` them.
- **A `while True` with no cap.** Ten minutes and a few hundred requests later you will care.
- **Making the tool do something clever.** Today's tools are dumb lookups. Cleverness in tools hides
  agent failures — the agent looks smart because the tool is doing the thinking.
- **Reaching for a framework "just to see".** Not yet. Principle 2 exists precisely because the naked
  version is only interesting *before* you've seen the convenient one.

---

## §8 Verify before you code

This lesson was written **2026-08-20** against `openai` **3.3.1**. Check:

- `https://platform.openai.com/docs/guides/function-calling` — the tool-call message shape. This is
  the part most likely to have drifted; confirm the `tool_calls` / `tool_call_id` field names.
- `https://console.groq.com/docs/openai` — Groq's OpenAI-compatibility notes, including which
  parameters it ignores. Some providers quietly drop `parallel_tool_calls` or `strict`.
- `src/mandala/models.py` — is `FAST_LOOP` still a live model id? Rosters rotate.

If any shape differs from this lesson: **that's a finding.** Log it in `docs/CHANGELOG_PLAN.md`
(Principle 14) rather than silently patching around it.

---

## §9 Done when

See `CHECKLIST.md`. Tomorrow you stop accepting prose from the model and start demanding a shape.
