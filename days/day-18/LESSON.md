---
day: 18
phase: 3
phase_name: "OpenAI Agents SDK advanced"
title: "Programmatic tool calling & the free coordinator"
ids: ["OAI-17"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 18 — Programmatic tool calling & the free coordinator

**Phase 3 · OpenAI Agents SDK advanced** · IDs: **OAI-17 🅿️+🛠️**

> **Yesterday:** streaming — `run_streamed`, the event types, and a progress UX that shows a user
> what an agent is doing while it does it.
> **Today:** the opposite problem. Not *how do I show the round trips*, but *how do I stop making
> them* — the paid feature that lets the model write a program, and the free coordinator that gets
> you the same economics for $0.
> **Tomorrow:** the model-native harness 🅿️ and the local Docker sandbox — the $0 lab
> (OAI-18/19/20).

```bash
./m start 18
./m scaffold 18
```

---

## §1 The story

Ask your Researcher to triage eight tickets and watch what happens. It calls `get_ticket("T-1001")`.
The result comes back. It calls `get_ticket("T-1002")`. The result comes back. Eight times. Then one
more call to write the summary. That is **nine model round trips to do one job**, and every one of
them re-sends the whole conversation so far — including the eight ticket bodies you already paid to
put there (Day 4's context budget, spent on purpose once and by accident seven times).

On a paid platform this is a bill. Here it is worse:

> **On a free tier, round trips are literally the budget.** Not a proxy for it, not a performance
> footnote — the actual unit that runs out (Principle 5). Nine calls against a requests-per-day
> ceiling is nine, and `docs/RATE_BUDGET.md` is the file that says how many you had.

OpenAI's answer is a paid Responses feature: **Programmatic Tool Calling**. Instead of calling your
tools one at a time, the model writes a small program that calls them, the program runs on their
side, and only its *result* comes back. You control which tools the program may invoke with
**`allowed_callers`**.

You cannot run it — it needs a paid Responses key, and this project has none and never will. So §3
teaches it properly (the shape, the economics, and the part everybody gets wrong about
`allowed_callers`), and §4 builds the free half:

> **One coordinator function tool that takes a typed plan the model filled in, and executes the whole
> batch in your Python, in one tool call.**

And then you **measure it**, using the tracer you built on Day 14. `model_calls()` from
`days/day-14/lab/span_tree.py` counts generation spans; you run the same eight-ticket job twice and
print the two numbers next to each other. **That is the strongest possible payoff for Day 14** — four
days ago you wrote a thirty-line JSONL exporter that felt like plumbing, and today it is the
instrument that proves this day's central claim. A lesson that asserts "fewer round trips" is a blog
post. A lesson that prints `naive: 9 / coordinator: 2` is an engineering result.

There is a catch, and it is the security content of the day. A coordinator is a **small
interpreter**, and an interpreter that will run whatever the model hands it is `eval()` with extra
steps. §4.2 is the rules; do not skim it.

---

## §2 Setup — run this

**No new packages today.** Everything today needs is already installed: `pydantic` (Day 4),
`openai-agents[litellm]` (Day 9). The dependency ledger in `docs/PINS.md` has no Day-18 row and
should not grow one — a coordinator that needs a library is a coordinator doing too much.

```bash
mkdir -p days/day-18/lab
touch src/mandala/coordinator.py
touch days/day-18/lab/coordinator_demo.py
touch days/day-18/lab/roundtrip_count.py
touch tests/test_coordinator.py
```

```bash
uv run pytest tests/test_permissions.py tests/test_tracing.py -q
```

Day 8's permission table and Day 14's tracer are today's two dependencies — one is the boundary the
coordinator must not escape, the other is the instrument that measures it. **If either is red, fix
that first**; today has nothing to stand on without them.

Your fixtures hold **T-1001 … T-1010** (Day 2) plus **T-9002**, the canary added on Day 13. Today's
batch is **T-1001 … T-1008**. If you trimmed the fixture file at some point, add rows back — a batch
of two proves nothing about round-trip economics.

---

## §3 OAI-17 🅿️ — Programmatic Tool Calling, the feature you cannot buy

### 3.1 The problem it solves: round-trip economics

The ordinary agent loop (Day 10), drawn as cost, next to what the paid feature does instead:

```
NAIVE                                        PROGRAMMATIC TOOL CALLING
turn 1  model call -> get_ticket(T-1001)     turn 1  model call -> emits a PROGRAM
        tool runs (2ms)                              program runs on OpenAI's side,
turn 2  model call -> get_ticket(T-1002)             calling get_ticket 8 times
  ... x8, one round trip each ...            turn 2  model call -> answer, from the
turn 9  model call -> final answer                   program's RESULT
```

Nine model calls for **8 x 2ms of actual work.** The model is not thinking between tickets; it is
being used as a very expensive `for` loop, and each iteration re-sends every previous ticket body as
conversation history. The paid version costs **two model calls**, and the eight tool results never
enter the model's context at all — they live in the program's variables, and only what the program
returns comes back. That is the second, quieter win: **a context saving as much as a round-trip
saving**, and on a free tier those are the same currency wearing different hats (Day 4).

### 3.2 The shape of the API 🅿️

You will not run this. Read it the way you read a spec: for the shape, not the syntax.

```python
# 🅿️ PAID — OpenAI Responses API. Needs a paid key. Reproduced for study only.
response = client.responses.create(
    model="<a paid OpenAI model>",
    input="Triage tickets T-1001 through T-1008 and tell me the severity spread.",
    tools=[
        {
            "type": "code_interpreter",          # the sandbox the program runs in
            "container": {"type": "auto"},
        },
        {
            "type": "function",
            "name": "get_ticket",
            "parameters": {...},                 # your ordinary function-tool schema
            "allowed_callers": ["code_interpreter"],   # <- the line that matters
        },
    ],
)
```

**Line by line:**

- `"type": "code_interpreter"` — programmatic tool calling is not a separate product; it is the
  **hosted code sandbox** (OAI-14, Day 15's concept-only section) given the ability to call *your*
  functions. Which is why it is paid twice over: their sandbox, their model. If you skipped Day 15's
  code-interpreter paragraph, read it now — this feature is that paragraph plus one permission field.
- `"allowed_callers": ["code_interpreter"]` — this tool may be called **by the program**, and the
  list is the set of callers permitted to call it. §3.3 is entirely about this field, because it is
  the part that is routinely described as a performance switch and is not one.
- The model still gets one shot to write the program and one shot to interpret the result. **Two
  turns, not one.** Anyone who tells you it is one turn has not counted.
- Notice what is *absent*: any way for you to review the program before it runs. The model writes it,
  their sandbox executes it, you see the output. Remember that when you get to §3.4.

> ⚠️ **Read this from the live docs before you repeat it in an interview.** The plan's OAI-17 row
> says the model writes "a small **JS** program"; hosted code execution on this platform has
> historically been Python. **We cannot test either claim** — that is what 🅿️ means — so §8 lists the
> two doc pages, and the language, the exact field names and where `allowed_callers` is attached are
> all *read*, not verified. If the docs and the plan disagree, that is a Part-4 matrix fact: one line
> in `docs/CHANGELOG_PLAN.md` (Principle 14), today, before you forget which one you believed.

### 3.3 `allowed_callers` is a permission boundary, not an optimisation

This is the sentence to take out of §3:

> **`allowed_callers` answers "who may call this tool", not "how fast is this tool". It is Day 8's
> permission table, expressed one layer down — per caller instead of per agent.**

Without it, a tool is either exposed or not. With it you can say:

| Tool | `allowed_callers` | What that means |
|---|---|---|
| `get_ticket` | `["code_interpreter"]` | only the generated program may read tickets; the model may not read one directly |
| `post_reply` | *(omitted / model only)* | the **program may never send anything** — a write stays a deliberate, visible, single tool call |
| `kb_search` | `["code_interpreter", "model"]` | both, because it is cheap and read-only |

Read row two twice. The instinct, once tool calls are cheap, is to make **every** tool available to
the program — that is where the speed is. And that is precisely how you end up with a model-written
program you never reviewed, running in a sandbox you cannot inspect, holding your `post_reply` tool.
**The blast radius of a batch is the blast radius of its worst operation, multiplied by the batch
size** (Principle 6).

So: Day 8 says *which agent may hold which tool*; `allowed_callers` says *which caller inside that
agent may invoke it*. Both are allowlists, both fail closed, and every claim in §4 about the free
coordinator is an attempt to reproduce that row in Python against `mandala.permissions.TOOLS`.

### 3.4 Paid vs. free — the comparison

The rule of this project is that you never say "I built the free version" without being able to
finish the sentence (Day 15, §3.2). So:

| | Programmatic Tool Calling 🅿️ | Your coordinator 🛠️ (§4) |
|---|---|---|
| What the model produces | **a program** — arbitrary control flow, invented at runtime | **a plan** — a bounded list of typed operations |
| Where it executes | OpenAI's sandbox | your Python process |
| Round trips for an 8-ticket job | ~2 | ~2 |
| Tool results in the model's context | no — they stay in program variables | no — they stay in `run_plan`'s locals |
| **New operations you did not anticipate** | **yes — the model composes them** | **no. If it is not in `OPERATIONS`, it cannot happen** |
| **Branching, retries, loops mid-job** | **yes, the model writes them** | only what your plan schema can express |
| Schema you must maintain | none | `Plan` and every `Step` — forever |
| Can you review what will run, before it runs? | no | **yes — the plan is data. Print it, log it, test it, diff it** |
| Permission boundary | `allowed_callers`, theirs | `permissions.check()`, yours, against Day 8's table |
| Determinism / replay | model-written code, different every time | same plan, same result |
| Cost | paid key, per call | **$0** |

**What the paid version genuinely does better** — say this out loud, it is the credible half of the
answer:

1. **It handles jobs you did not design for.** "Fetch these eight, and for any that mention a refund,
   also search the handbook, and if that returns nothing, search the web" is a program the model can
   write and a plan schema you would have had to anticipate. A real capability gap, and not a small one.
2. **There is no schema to maintain.** Your `Plan` is long-lived surface area: every new operation is
   a schema change, a test, and a migration for any stored plan.
3. **Their sandbox is hardened by people whose job it is.** Yours is `run_plan`, and the only reason
   it is safe is that it cannot execute anything you did not write.

And the one thing the free version is better at, which is not a consolation prize:

> **The paid feature emits code. Ours emits data. Code is more expressive; data is more reviewable.**
> You can `print(plan)` before you run it, assert on it in a unit test, store it in an audit line,
> and diff two of them. You cannot do any of that with a program you never see.

### 3.5 Why we cannot run it, precisely

Not "we chose not to". The mechanism:

- It is a **Responses API** feature, and the hosted `code_interpreter` tool type is server-side
  OpenAI. We reach models through `LitellmModel` (Day 9) pointed at Groq / Gemini / OpenRouter, which
  are OpenAI-*compatible* on the chat surface and do not implement OpenAI's hosted tool types.
- Even with a Responses-shaped endpoint, the sandbox that runs the program is theirs and metered.
- Principle 5 is not a budget preference; it is a project invariant. There is no paid key, today or
  on Day 90.

So OAI-17's paid half is **read, not run** — and the whole point of the day is that the *economics*
were never the paid part. Those you can have for free.

---

## §4 The free coordinator — one tool call instead of nine

### 4.1 The idea, stated as a number

Same job, two shapes:

| | naive | coordinator |
|---|---|---|
| Model call 1 | "call `get_ticket(T-1001)`" | "call `coordinate(plan={...8 ids, filter, count_by...})`" |
| Model calls 2–8 | one per remaining ticket | — |
| Model call 9 / 2 | final answer | final answer, from one summarised result |
| **Total** | **~9** | **~2** |
| Ticket bodies in the transcript | 8 | 0 |
| Who decides the order | the model, one step at a time | the model, once, up front |

The last row is the honest trade and §4.8 comes back to it. The model still plans — it just plans
**once**, and then your Python is trusted to carry it out without asking again.

### 4.2 The rule: a plan is data, not code 🎯

This is the security heart of the day, and it is easy to get wrong in a way that looks fine.

A coordinator is an **interpreter**. It receives a description of work from an untrusted-ish source
(a model, which may itself be reading attacker-controlled text — Day 15) and performs it. The failure
mode is not "the model writes a bad plan". The failure mode is:

> **A coordinator that accepts an operation nobody granted becomes a way to reach tools the calling
> agent does not have — and it does it *inside* a tool call, where Day 8's table is not looking.**

So, the rules. Every one of them is implemented in §4.3, and every one has a test in §5:

1. **An allowlist of operations, never a denylist.** `OPERATIONS` is a closed set. An unknown `op` is
   a `ValidationError` *before anything runs* — not a warning, not a skip. A denylist ("anything
   except `delete_*`") loses on the day someone adds `purge_*`.
2. **Typed, validated arguments.** Every field is a Pydantic type with a bound. `extra="forbid"` on
   every step, so an argument you did not define is a rejection rather than a silently ignored key.
3. **Hard caps, checked before execution.** `MAX_STEPS`, `MAX_ITEMS`, `MAX_OUTPUT_CHARS`. A cap you
   check *while* executing is a cap you check after doing the expensive thing.
4. **No reach beyond existing tools.** No filesystem paths in the schema, no URLs, no shell, no
   `getattr` dispatch. The coordinator's only contact with the world is through the same data paths
   the existing function tools use.
5. **Every operation that touches a tool names that tool, the tool exists in
   `mandala.permissions.TOOLS`, and `permissions.check()` runs for the calling agent before step
   one.** This is the rule the other four exist to support.

Rule 5 has a corollary worth stating separately, because it is the one people bargain with:

> **A coordinator may never widen a grant. If the Researcher cannot call `post_reply` directly, no
> plan, no operation and no batch may cause `post_reply` to happen.** The coordinator is a *client*
> of Day 8's table, never a bypass of it.

Which is also why **today's coordinator is read-only** (Principle 6). Its operations reach
`get_ticket` and `search_tickets` and nothing else. Writes stay where Day 8 and Principle 12 put
them: one at a time, behind an approval, visible in a trace.

### 4.3 `src/mandala/coordinator.py`

```python
"""One tool call instead of N. The model plans; your Python executes.

Programmatic Tool Calling (OAI-17) is a paid Responses feature: the model writes a
program that calls your tools inside OpenAI's sandbox, so a job that costs N model
round-trips costs about two. We have no paid key (Principle 5), so we take the half
of the idea that is free — plan the whole job in ONE model call — and drop the half
that is paid: the model writes a TYPED PLAN, not code, and we execute it.

THE PLAN IS DATA, NOT CODE. That sentence is the entire security design.
--------------------------------------------------------------------
A coordinator is a small interpreter, and an interpreter that accepts arbitrary
operations is eval() with extra steps. In order of how much each one protects you:

  1. Every op that touches a tool declares `requires`, and run_plan() calls
     permissions.check() for the CALLING agent before any step runs.  <- the boundary
  2. OPERATIONS is a closed ALLOWLIST; an unknown op is a ValidationError.  <- structural
  3. Arguments are typed and bounded; steps are extra="forbid".            <- structural
  4. MAX_STEPS / MAX_ITEMS / MAX_OUTPUT_CHARS, checked before execution.   <- bounds damage

(1) is why this file may exist at all: the coordinator must never be a way to reach
a tool the calling agent was not granted. Read-only (Principle 6).

Usage
-----
    >>> from mandala.coordinator import Plan
    >>> p = Plan(goal="spread", steps=[{"op": "fetch_tickets", "ticket_ids": ["T-1001"]}])
    >>> [s.op for s in p.steps]
    ['fetch_tickets']
"""

from __future__ import annotations

import json
from typing import Annotated, ClassVar, Literal, Union

from agents import RunContextWrapper, function_tool
from pydantic import BaseModel, ConfigDict, Field

from mandala import permissions
from mandala.context import MandalaContext
from mandala.sdk_tools import tool_error

MAX_STEPS = 6            # a plan longer than this is a program, and we do not run programs
MAX_ITEMS = 25           # the working set never exceeds this, at any point
MAX_OUTPUT_CHARS = 4_000  # what comes back to the model. Day 4's budget, enforced.
MAX_FIELD_CHARS = 400     # any single value, before it is rendered


class Step(BaseModel):
    """Base for every operation. `requires` names the permission-table tool it needs."""

    model_config = ConfigDict(extra="forbid")
    requires: ClassVar[str | None] = None


class FetchTickets(Step):
    """Read named tickets into the working set."""

    op: Literal["fetch_tickets"]
    ticket_ids: list[str] = Field(min_length=1, max_length=MAX_ITEMS)
    requires: ClassVar[str] = "get_ticket"


class SearchTickets(Step):
    """Add tickets matching a literal phrase to the working set."""

    op: Literal["search_tickets"]
    query: str = Field(max_length=200)
    limit: int = Field(default=5, ge=1, le=MAX_ITEMS)
    requires: ClassVar[str] = "search_tickets"


class FilterRows(Step):
    """Pure. Narrows the working set. Reaches nothing."""

    op: Literal["filter"]
    field: Literal["severity", "category"]
    equals: list[str] = Field(min_length=1, max_length=8)
    requires: ClassVar[None] = None


class TakeFields(Step):
    """Pure. Projects each row down to the named fields — the context-budget step."""

    op: Literal["take_fields"]
    fields: list[Literal["id", "severity", "category", "body"]] = Field(min_length=1, max_length=4)
    requires: ClassVar[None] = None


class CountBy(Step):
    """Pure. Replaces rows with a tally. The cheapest possible answer shape."""

    op: Literal["count_by"]
    field: Literal["severity", "category"]
    requires: ClassVar[None] = None


StepUnion = Annotated[
    Union[FetchTickets, SearchTickets, FilterRows, TakeFields, CountBy],
    Field(discriminator="op"),
]

OPERATIONS: dict[str, type[Step]] = {
    "fetch_tickets": FetchTickets,
    "search_tickets": SearchTickets,
    "filter": FilterRows,
    "take_fields": TakeFields,
    "count_by": CountBy,
}


class Plan(BaseModel):
    """The whole job, in one object, filled in by the model in ONE model call."""

    model_config = ConfigDict(extra="forbid")

    goal: str = Field(max_length=200, description="One sentence: what this plan is for.")
    steps: list[StepUnion] = Field(min_length=1, max_length=MAX_STEPS)


class CoordinatorResult(BaseModel):
    """What comes back. Bounded on every axis, because it lands in a context window."""

    goal: str
    steps_run: int
    rows: list[dict] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


def plan_cost(plan: Plan) -> int:
    """TODO(me): worst-case number of ITEMS this plan will touch, computed BEFORE it runs.

    Why this is the rep: a cap enforced during execution is a cap enforced after you
    already did the expensive thing. Sum the bound each step can add to the working
    set — fetch_tickets contributes len(ticket_ids), search_tickets contributes
    limit, the pure steps contribute 0 — and run_plan() refuses the plan outright if
    the total exceeds MAX_ITEMS. Deciding what counts as an "item" is the actual work
    here and there is no single right answer; write down the one you chose and why.
    """
    raise NotImplementedError


def _tickets(context: MandalaContext) -> list[dict]:
    """The same data path Day 12's get_ticket uses. Not a second one."""
    return json.loads(context.tickets_path.read_text(encoding="utf-8"))


def _apply(
    step: Step, rows: list[dict], counts: dict[str, int],
    *, context: MandalaContext, errors: list[str],
) -> tuple[list[dict], dict[str, int]]:
    """Execute exactly one allowlisted operation. No dispatch by string lookup."""
    if isinstance(step, FetchTickets):
        by_id = {t["id"]: t for t in _tickets(context)}
        for ticket_id in step.ticket_ids[:MAX_ITEMS]:
            try:
                rows.append(by_id[ticket_id])
            except KeyError:
                errors.append(f"fetch_tickets: no ticket {ticket_id}")
        return rows[:MAX_ITEMS], counts

    if isinstance(step, SearchTickets):
        needle = step.query.lower()
        hits = [t for t in _tickets(context) if needle in t.get("body", "").lower()]
        return (rows + hits[: step.limit])[:MAX_ITEMS], counts

    if isinstance(step, FilterRows):
        wanted = {v.lower() for v in step.equals}
        return [r for r in rows if str(r.get(step.field, "")).lower() in wanted], counts

    if isinstance(step, TakeFields):
        return [{f: r.get(f) for f in step.fields} for r in rows], counts

    if isinstance(step, CountBy):
        tally: dict[str, int] = {}
        for row in rows:
            key = str(row.get(step.field, "unknown"))
            tally[key] = tally.get(key, 0) + 1
        return rows, tally

    raise ValueError(f"unreachable: {type(step).__name__} is not an allowlisted operation")


def run_plan(plan: Plan, *, context: MandalaContext) -> CoordinatorResult:
    """Execute a validated plan. Permission first, caps second, work third."""
    for step in plan.steps:
        if step.requires is not None:
            permissions.check(context.agent_name, step.requires)   # raises PermissionDenied

    cost = plan_cost(plan)
    if cost > MAX_ITEMS:
        raise ValueError(f"plan would touch {cost} items; the cap is {MAX_ITEMS}")

    rows: list[dict] = []
    counts: dict[str, int] = {}
    errors: list[str] = []

    for step in plan.steps:
        try:
            rows, counts = _apply(step, rows, counts, context=context, errors=errors)
        except permissions.PermissionDenied:
            raise                                  # boundary: never degrade a security failure
        except Exception as exc:                   # noqa: BLE001 — one bad step must not lose the batch
            errors.append(f"{step.op}: {type(exc).__name__}: {str(exc)[:200]}")

    return CoordinatorResult(
        goal=plan.goal, steps_run=len(plan.steps),
        rows=rows[:MAX_ITEMS], counts=counts, errors=errors[:MAX_ITEMS],
    )


def render(result: CoordinatorResult) -> str:
    """Bounded JSON. This string is the only thing the model ever sees."""
    payload = result.model_dump()
    payload["rows"] = [
        {k: (v[:MAX_FIELD_CHARS] if isinstance(v, str) else v) for k, v in row.items()}
        for row in payload["rows"]
    ]
    text = json.dumps(payload, indent=2, default=str)
    if len(text) > MAX_OUTPUT_CHARS:
        text = text[:MAX_OUTPUT_CHARS] + '\n... TRUNCATED. Narrow the plan with take_fields.'
    return text


@function_tool(name_override="coordinate", failure_error_function=tool_error)
def coordinate(ctx: RunContextWrapper[MandalaContext], plan: Plan) -> str:
    """Run a whole batch job in one call instead of one tool call per item.

    Use this whenever you need the SAME operation over MORE THAN TWO tickets — fetch
    several, narrow them, and tally them. Do NOT use it for a single ticket; call
    get_ticket for that.

    Args:
        plan: The complete job. `goal` is one sentence. `steps` run in order: start
            with fetch_tickets or search_tickets to load rows, then narrow with
            filter, shrink with take_fields, and finish with count_by if you want a
            tally rather than rows.
    """
    result = run_plan(plan, context=ctx.context)
    print(ctx.context.audit("coordinate", f"steps={result.steps_run} rows={len(result.rows)}"))
    return render(result)
```

**Line by line:**

- The docstring **ranks the four defences and says which one is the boundary** — the same shape as
  Day 15's `search.py`. A flat list reads as "we did four things"; a ranked list tells the next
  reader which line they are not allowed to delete.
- `MAX_STEPS = 6` with the comment *"a plan longer than this is a program"* — the cap is not
  arbitrary, it is a **definition**. The moment a plan needs twelve steps with conditionals you have
  re-invented the paid feature badly, and the right move is to go back to ordinary tool calls.
- `class Step` with `model_config = ConfigDict(extra="forbid")` — **inherited by every operation.**
  Without it an unknown key validates fine and is silently dropped. Forbidding extras is how a typo
  becomes an error instead of a surprise.
- `requires: ClassVar[str | None]` — the permission a step needs, attached **to the operation class,
  not to a lookup table elsewhere** (two sources of truth is zero, Day 14). `ClassVar` keeps it out of
  the JSON schema, so the model cannot set it — which would obviously be the whole ballgame. The pure
  operations declare `requires = None` **explicitly**: a `None` you have to write is a `None` you have
  to justify; one you inherit silently is a hole nobody reviews.
- `TakeFields.fields` includes `"body"`, and that is deliberate. It would look better to exclude it —
  "the coordinator can never return a raw ticket body!" — and it would be **security theatre**: the
  calling agent already holds `get_ticket`, so the body is one ordinary tool call away. A boundary
  that does not bound anything is worse than no boundary, because it earns trust it has not paid for.
  The coordinator inherits `get_ticket`'s reach exactly: no more, and no less.
- `Field(discriminator="op")` plus `OPERATIONS` as a dict — Pydantic picks the model by the `op`
  literal, so an unknown `op` is a **`ValidationError` naming the field**, not a baffling "no union
  member matched"; and the allowlist sits in one greppable place, so a reviewer can answer "what can
  this thing do?" by reading five lines.
- `Plan.goal` is required and length-capped — **a plan that cannot say what it is for is a plan you
  cannot audit.** It costs the model six words and it is the field you will actually read in a log.
- `def plan_cost(...)` is a **TODO(me)**, and note *where it is called*: before the first step, after
  the permission loop. That ordering is the lesson; the arithmetic is the rep.
- `_tickets()` reads `context.tickets_path` — **Day 12's injected path, not a second data path.** Two
  alternatives were rejected: importing Day 3's `tools.py` helpers (they read a module-level fixture
  constant and would ignore the `tmp_path` your tests inject), and calling `sdk_tools.get_ticket`
  itself, which is a `FunctionTool` object — a model-facing schema plus an invoker, not a Python
  callable — and would nest a tool call inside a tool call, which is the round trip you came to remove.
- `_apply` dispatches with `isinstance`, **not** with `OPERATIONS[step.op](...)` or `getattr`. String
  dispatch into a namespace is how allowlists rot: it works, and then someone adds a helper to the
  module and it becomes callable. `isinstance` chains are boring and boring is the point. The final
  `raise ValueError("unreachable: ...")` keeps it a total function: add a `Step` subclass without
  teaching `_apply` about it and you get a loud error, not a silent no-op.
- **`run_plan` checks every permission before running any step.** Not per step, as you go. A plan
  that would be denied at step 4 must not have executed steps 1–3 — a partially-executed denied plan
  is the worst of both outcomes, and this is a *flip-it* test in §5.
- `permissions.check(context.agent_name, step.requires)` — `agent_name` is Day 12's derived property
  (`"agent:researcher"` -> `"researcher"`), read off an immutable context the model cannot influence.
  **The identity comes from your code; the plan comes from the model.** Never the other way around.
- `except permissions.PermissionDenied: raise` **before** the broad `except` — Day 10's error policy,
  third appearance. Getting these two clauses in the wrong order turns a security check into a log
  line. The broad clause below it is **one bad step must not lose the batch** — the same call Day 14
  made for the trace processor and Day 15 made for a malformed hit. §4.8 names the pattern.
- `render()` is separate from `run_plan()` — the executor returns a typed object; the renderer turns
  it into the bounded string the model sees. Tests assert on the object; the cap is asserted on the
  string. Same seam as Day 15's `web_hits` / `search_the_web`. And the truncation suffix is **advice,
  not just an ellipsis**: *"Narrow the plan with take_fields."* Day 15's rule that an empty result
  should be a sentence, applied to an overflowing one.
- `@function_tool(name_override="coordinate", ...)` — §4.4 adds `"coordinate"` to the permission table
  under exactly this string; a `name_override` that drifts from the table is a capability your safety
  check cannot see (Day 15). The tool docstring then says **when not to use it** — *"Do NOT use it for
  a single ticket"* — which is Day 3's tool-description discipline, and what stops the model routing
  everything through the new shiny tool and paying plan-writing tokens to fetch one row.
- `plan: Plan` as a typed parameter means **the SDK generates the plan's JSON schema for the model**,
  and the field descriptions become the model's instructions (Day 4, Day 11). See §8 — discriminated
  unions under strict-schema mode are the single most likely thing in this file to need a fallback.
- `ctx.context.audit(...)` — Day 12's audit line, one per coordinated batch. **A batch that leaves one
  line in the log where nine tool calls would have left nine is a real observability loss**, and this
  is the minimum repayment.

### 4.4 The permission table learns one new capability — before the agent does

Day 8's table is the source of truth, and Day 15 established the order: **table first, agent second.**
In `src/mandala/permissions.py`:

```python
    "coordinate": ToolSpec(
        name="coordinate",
        writes=False,
        reads_untrusted=True,       # it returns ticket bodies — same untrusted text as get_ticket
        blast_radius=(
            "none beyond the tools its operations already require (get_ticket, "
            "search_tickets) — it is a batcher, never a widener"
        ),
    ),
```

and grant it in `AGENTS["researcher"].tools`:

```python
        tools=frozenset({"get_ticket", "search_tickets", "kb_search", "web_search", "coordinate"}),
```

**Line by line:**

- `writes=False` and it must stay that way. The day someone adds a `post_replies` operation, this
  field is what `trifecta_violations()` reads, and the Researcher — which reads the open web since
  Day 15 — would light up as a lethal-trifecta risk. **That is the alarm working**, not a nuisance.
- `reads_untrusted=True` — obviously, because the rows are ticket bodies. The interesting bit is
  *why it is not worse than `get_ticket`*: identical text, arriving in bulk. Volume is not a new
  trust class.
- The `blast_radius` sentence is doing real work: **"it is a batcher, never a widener."** Day 8 asked
  for plain English rather than a severity enum precisely so that a sentence like that could be
  written down and later held against the code.
- The grant list now has five entries and **zero write tools.** Look at it and check it against
  §4.3's `requires` values: `get_ticket` ✓, `search_tickets` ✓. Every tool the coordinator can reach
  is already in that set, which is the invariant §5 asserts.
- Run `uv run pytest tests/test_permissions.py -q` now. `trifecta_violations()` must still be `[]`.
  Fifteen days of that function returning `[]` is not a formality; it is the reason this project can
  add a batching primitive on day 18 without a two-hour security discussion.

### 4.5 `days/day-18/lab/coordinator_demo.py`

```python
"""Triage eight tickets in one tool call. Watch the plan the model wrote.

Run:
    uv run python days/day-18/lab/coordinator_demo.py
"""

from __future__ import annotations

import asyncio

from agents import Agent, Runner

from mandala.context import MandalaContext
from mandala.coordinator import coordinate
from mandala.sdk import DEFAULT_SETTINGS, make_model
from mandala.sdk_tools import get_ticket, search_tickets
from mandala.tracing import install_local_tracing

BATCH = [f"T-100{n}" for n in range(1, 9)]          # T-1001 .. T-1008, from Day 2's fixtures

JOB = (
    f"Triage this batch: {', '.join(BATCH)}. "
    "I want the severity spread across the whole batch, and the ids of everything "
    "that is high or critical. Do it in ONE coordinate call."
)


def batcher() -> Agent:
    return Agent(
        name="Researcher",
        instructions=(
            "You handle batches of tickets. When a job names more than two tickets, write ONE "
            "plan and send it to the coordinate tool — do not call get_ticket in a loop.\n"
            "A good plan for a spread question is: fetch_tickets, then count_by severity.\n"
            "A good plan for 'which ones are high' is: fetch_tickets, filter on severity, "
            "then take_fields with just id and severity.\n"
            "Report the numbers you got back. Never invent a ticket the coordinator did not "
            "return, and if the result has an errors list, say what failed."
        ),
        model=make_model("groq"),
        model_settings=DEFAULT_SETTINGS,
        tools=[coordinate, get_ticket, search_tickets],
        # ^ coordinate does NOT replace the single-item tools. See the line-by-line.
    )


async def main() -> None:
    processor = install_local_tracing()
    context = MandalaContext(actor="agent:researcher", request_id="req-batch-18")

    result = await Runner.run(batcher(), JOB, context=context, max_turns=6)

    print("\n--- tool calls, in order ---")
    for item in result.new_items:
        name = getattr(getattr(item, "raw_item", None), "name", None)
        if name:
            print(f"  {name}")

    print(f"\n--- answer ---\n{result.final_output}")
    processor.force_flush()
    print(f"\ntraces: {processor.directory}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- `BATCH = [f"T-100{n}" ...]` — eight ids, and they are real. Day 2 built ten tickets with deliberate
  variety (T-1006 is "it's broken", T-1008 is the never-auto-resolve one, T-1007 is the ambiguous
  billing/data case). A batch over *those* eight is a batch with a genuine severity spread, which is
  what makes `count_by` produce something worth reading rather than `{"high": 8}`.
- The prompt says **"Do it in ONE coordinate call"** — and you should be suspicious of that, because
  §3.3's whole argument was that prompts are not boundaries. It is not a boundary here either; it is
  a *routing hint*, exactly like Day 15's "use kb_search for OUR policy". The boundary is that
  `coordinate` cannot reach a tool the Researcher lacks. Two different jobs, two different mechanisms,
  and confusing them is how you end up trusting a sentence.
- The instructions **give worked plan shapes** — "fetch_tickets, then count_by severity". A schema the
  model has never seen buys you one wasted round trip of guessing; two example plans in the prompt is
  cheaper than a retry, and it is the same instinct as putting judgement criteria in field
  descriptions (Day 4).
- *"Never invent a ticket the coordinator did not return"* is the batching version of Day 15's
  hallucination guard — a model handed a tally will happily narrate ids that were not in it. And
  *"if the result has an errors list, say what failed"* exists because **surfacing partial failure is
  a prompt job while producing it honestly is a code job.** You need both.
- `tools=[coordinate, get_ticket, search_tickets]` — **the coordinator is added, not substituted.**
  One ticket should still cost one ordinary tool call; forcing a plan for a single row spends more
  tokens writing the plan than the fetch would have cost. The tool description's "Do NOT use it for a
  single ticket" is what makes this list safe to hand over.
- `max_turns=6` — this job needs about two. Six leaves room for one bad plan and a retry, and it is
  still Day 10's request budget expressed as a loop cap. If you find yourself raising it, the model is
  looping and you should read the trace, not the number.
- `install_local_tracing()` in the **demo**, not in `coordinator.py` — Day 14's rule. A library that
  installs a global processor at import fights every other library in the process.
- The tool-call loop reprints Day 14's `getattr(getattr(...))` idiom, still marked there as a
  `TODO(me)`. **You now have two places to fix once you find the real item types** — a small, honest
  argument for going back and doing it.

### 4.6 `days/day-18/lab/roundtrip_count.py` — the measurement 🎯

This is the day's deliverable. Everything above is a claim; this file is the evidence.

```python
"""The same job, twice, with the model calls counted. This is the proof.

Naive path      : the agent calls get_ticket once per ticket.
Coordinator path: the agent writes one plan and calls coordinate once.

Counted with Day 14's tracer — install_local_tracing() writes spans to a JSONL file
and model_calls() counts the generation spans. Four days ago that looked like
plumbing; it is the instrument that makes today a result instead of an assertion.

Run:
    uv run python days/day-18/lab/roundtrip_count.py
"""

from __future__ import annotations

import asyncio
import shutil
import sys
from dataclasses import replace
from pathlib import Path

from agents import Agent, Runner

from mandala.context import MandalaContext
from mandala.coordinator import coordinate
from mandala.sdk import DEFAULT_SETTINGS, make_model
from mandala.sdk_tools import get_ticket
from mandala.tracing import install_local_tracing

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "day-14" / "lab"))
from span_tree import load, model_calls          # noqa: E402 — reuse, do not rewrite

BATCH = [f"T-100{n}" for n in range(1, 9)]
JOB = (
    f"For each of these tickets — {', '.join(BATCH)} — tell me its severity, then give me "
    "the count of how many are at each severity level."
)

# TODO(me): before you believe either number, confirm that model_calls() actually matches
# YOUR provider's span type. Day 14 §8 flagged this and left it open: model_calls() looks
# for "Generation" in data_type, and we go through LitellmModel, not OpenAI's Responses
# API. If your spans say something else, the count is silently 0 and this whole lab is a
# lie that prints. Run span_tree.py on one trace and read the labels FIRST.

NAIVE_SETTINGS = replace(DEFAULT_SETTINGS, parallel_tool_calls=False)   # see §8


def naive() -> Agent:
    return Agent(
        name="Researcher",
        instructions=(
            "Answer the question. You have get_ticket, which reads exactly one ticket. "
            "Read the tickets you need, one at a time, then answer."
        ),
        model=make_model("groq"),
        model_settings=NAIVE_SETTINGS,
        tools=[get_ticket],
    )


def coordinated() -> Agent:
    return Agent(
        name="Researcher",
        instructions=(
            "Answer the question. You have coordinate, which runs a whole batch in one call. "
            "Write ONE plan: fetch_tickets for every id, then count_by severity, and read the "
            "severities off the rows. Then answer."
        ),
        model=make_model("groq"),
        model_settings=DEFAULT_SETTINGS,
        tools=[coordinate],
    )


async def measure(label: str, agent: Agent, *, max_turns: int) -> int:
    directory = Path(".mandala/roundtrip") / label
    shutil.rmtree(directory, ignore_errors=True)     # a stale trace makes a flattering number
    processor = install_local_tracing(directory)

    context = MandalaContext(actor="agent:researcher", request_id=f"req-rt-{label}")
    result = await Runner.run(agent, JOB, context=context, max_turns=max_turns)
    processor.force_flush()

    calls = sum(model_calls(load(path)) for path in directory.glob("*.jsonl"))
    print(f"\n=== {label} ===\n{str(result.final_output)[:400]}")
    return calls


async def main() -> None:
    naive_calls = await measure("naive", naive(), max_turns=14)
    coord_calls = await measure("coordinator", coordinated(), max_turns=6)

    print("\n" + "=" * 46)
    print(f"  tickets in the job     : {len(BATCH)}")
    print(f"  naive model calls      : {naive_calls}")
    print(f"  coordinator model calls: {coord_calls}")
    if coord_calls:
        print(f"  ratio                  : {naive_calls / coord_calls:.1f}x")
    print("=" * 46)
    print("\nWrite both numbers in days/day-18/CHECKLIST.md. On a free tier these ARE the budget.")


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- `sys.path.insert(...)` then `from span_tree import load, model_calls` — **reuse Day 14's reader; do
  not rewrite it.** Copying twelve lines of `model_calls` here would be faster today and would leave
  you two counters that can disagree, which is the exact failure that makes a measurement worthless.
  The ugly `sys.path` line is the honest price of keeping labs as scripts, and worth paying to keep
  one definition of "a model call". Note `newest()` is *not* imported: it is bound to the default
  `TRACE_DIR`, and we trace each run into its own directory. **The reusable parts of a module are the
  pure ones** — a design observation you can now make about your own code from four days ago.
- `shutil.rmtree(directory, ignore_errors=True)` before each run — **a stale trace file makes a
  flattering number.** The classic version of this bug is running the coordinator twice and reporting
  the sum as the naive count. Clear the directory or you are measuring your history.
- `NAIVE_SETTINGS = replace(DEFAULT_SETTINGS, parallel_tool_calls=False)` — the honest knob, and you
  must understand it. If your provider can emit **eight tool calls in one assistant message**, the
  naive path collapses to two or three model calls and today's headline shrinks. That does not make
  the coordinator pointless — the eight ticket bodies still land in the transcript, a Day-4 context
  cost the coordinator does not pay — but it changes the number. Turning batching off measures *round
  trips per tool call*, which is what OAI-17 is about. **Measure both ways and write down both**; §8
  tells you to confirm the field exists in 0.22.0 first.
- `max_turns=14` for naive vs `6` for coordinated — sized for what each shape actually needs (Day 10:
  `max_turns` is a request budget). Giving both the same generous budget would be "fair" in a way that
  hides the point: the naive path *needs* the bigger budget, and that need is the finding.
- Both agents get the **same `JOB` string**, same model pin, `temperature=0.0` from Day 9. If you tune
  the wording per path you are benchmarking prose. That is Day 14's topology-bake-off hygiene, reused.
- `sum(model_calls(load(path)) for path in directory.glob("*.jsonl"))` — summed across files, because
  a run that produced two traces (Day 14's `with trace(...)` lesson) would otherwise report half.
- The final block prints a **ratio**, because the ratio is the sentence you will say in an interview.
  And none of it is asserted here — §5 turns it into a cassette-backed test, because a number you
  observed once is an anecdote and a number CI re-derives is a regression test.

### 4.7 What you should see

Roughly, on Groq, with the batch of eight:

```
==============================================
  tickets in the job     : 8
  naive model calls      : 9
  coordinator model calls: 2
  ratio                  : 4.5x
==============================================
```

And the span trees, side by side, via `uv run python days/day-14/lab/span_tree.py`:

```
naive                                   coordinator
-----------------------------------     -----------------------------------
Researcher                              Researcher
  GenerationSpanData                      GenerationSpanData
  get_ticket                              coordinate            <- 8 tickets, 1 span
  GenerationSpanData                      GenerationSpanData
  get_ticket
  GenerationSpanData
  get_ticket
  ... x8 ...
  GenerationSpanData
```

**Read the shape, not just the number.** The naive tree is a staircase — model, tool, model, tool —
and every step of it is one request against your daily ceiling, having re-sent the whole conversation
to get there. The coordinator's is three spans.

Three things to check, because a number you did not interrogate is a number you cannot defend:

1. **Did `model_calls()` return a plausible number, or zero?** Zero means the `TODO(me)` at the top of
   the file caught you: your provider's spans are not named what Day 14 guessed. Fix that first.
2. **Run it three times.** The naive count will wobble (the model may re-read a ticket, or answer
   early); the coordinator count should be steady at two. **The variance is itself a finding** — the
   naive path's cost depends on model behaviour, the coordinator's on your code.
3. **Turn `parallel_tool_calls` back on and re-measure the naive path.** Write both numbers down.
   "9 vs 2, or 4 vs 2 if the provider batches tool calls, and either way zero ticket bodies in the
   transcript" is the answer of someone who actually ran it.

### 4.8 What the coordinator costs you — honestly

Three real costs. None of them are fatal; all of them are yours now.

**1. Less model adaptivity mid-job.** The naive loop lets the model react to ticket 3 before it asks
for ticket 4. The coordinator does not: the plan is fixed at the moment it is written. If T-1006 turns
out to say "it's broken" and nothing else (and it does — Day 2 built it that way), the naive path can
notice and go look for a related ticket. The coordinator returns a row and moves on. **You traded
adaptivity for round trips, and that is a trade, not a win.** The mitigation is the boring one: the
model can call `coordinate` again with a second plan. Two plans is still two, not nine.

**2. A plan schema you must maintain, forever.** `Plan` is public API for a model. Every new operation
is a schema change, a `_apply` branch, a test, and a prompt that has to teach the model the new shape.
The paid feature has none of that because the model writes code. **This is the maintenance cost of
choosing data over code, and it is the honest price of being able to review what will run.**

**3. Failure handling is now yours.** In the naive path, a missing ticket produces a tool error the
model reads and reacts to (Day 10's `tool_error`). In the coordinator, eight fetches happen inside one
call, and you have to decide what happens when one of them fails. Today's answer:

> **One bad ticket must not lose the batch.** The failure goes into `errors`, the other seven rows
> come back, and the model is told to mention what failed.

Notice that **this is the third time the curriculum has made exactly this call**:

| Day | The thing that could have exploded | What we did instead |
|---|---|---|
| 14 | a `json.dumps` failure inside the trace processor | swallow, log the drop, keep the run alive |
| 15 | one malformed search hit inside `web_hits` | `continue`, keep the other four |
| **18** | one missing ticket inside an eight-item batch | append to `errors`, return the other seven |

Three times is a pattern, so name it: **partial-failure isolation — the batch survives the item.** And
name its limit too, which all three share: it applies to *ingestion and instrumentation*, never to
*boundaries*. That is why `PermissionDenied` is re-raised in all three places rather than collected.
An eval that degrades is fine; a security check that degrades is a security check you do not have.

---

## §5 The eval that must be able to fail

### `tests/test_coordinator.py`

```python
"""A coordinator is an interpreter. These tests are the reason it is a safe one."""

import pytest
from pydantic import ValidationError

from mandala.context import MandalaContext
from mandala.coordinator import (
    MAX_ITEMS, MAX_OUTPUT_CHARS, MAX_STEPS, OPERATIONS,
    CoordinatorResult, Plan, render, run_plan,
)
from mandala.permissions import TOOLS, PermissionDenied, tools_for, trifecta_violations


def _plan(*steps, goal="test") -> Plan:
    return Plan(goal=goal, steps=list(steps))


# --- the allowlist ---------------------------------------------------------------
def test_the_plan_schema_rejects_an_unknown_operation():
    """The allowlist, proved. An op nobody wrote must not validate, let alone run."""
    with pytest.raises(ValidationError):
        _plan({"op": "delete_everything", "confirm": True})


def test_a_step_cannot_carry_an_argument_nobody_defined():
    """extra='forbid'. A typo is an error, not a silently ignored key."""
    with pytest.raises(ValidationError):
        _plan({"op": "count_by", "field": "severity", "and_also": "rm -rf"})


def test_the_operation_registry_is_exactly_the_five_we_reviewed():
    """If this goes red, someone added a capability. That should require a conversation."""
    assert set(OPERATIONS) == {
        "fetch_tickets", "search_tickets", "filter", "take_fields", "count_by"
    }

# --- the caps ----------------------------------------------------------------------
def test_a_plan_longer_than_max_steps_is_rejected():
    steps = [{"op": "count_by", "field": "severity"}] * (MAX_STEPS + 1)
    with pytest.raises(ValidationError):
        _plan(*steps)


def test_a_plan_that_would_touch_too_many_items_is_refused_before_it_runs(mandala_context):
    """Red until plan_cost() is written. The cap must fire BEFORE the first fetch."""
    huge = {"op": "fetch_tickets", "ticket_ids": [f"T-{n}" for n in range(MAX_ITEMS + 5)]}
    with pytest.raises((ValidationError, ValueError)):
        run_plan(_plan(huge), context=mandala_context)


def test_the_rendered_output_is_bounded():
    """Whatever happens, the string that reaches a context window has a ceiling (Day 4)."""
    result = CoordinatorResult(
        goal="x", steps_run=1, rows=[{"id": "T-1", "body": "y" * 50_000}] * 30
    )
    assert len(render(result)) <= MAX_OUTPUT_CHARS + 60      # + the truncation notice

# --- the permission boundary -------------------------------------------------------
def test_every_operation_that_touches_a_tool_names_a_real_permission():
    """No operation may require a capability the table has never heard of."""
    for name, step_cls in OPERATIONS.items():
        if step_cls.requires is not None:
            assert step_cls.requires in TOOLS, f"{name} requires an unknown tool"
            assert TOOLS[step_cls.requires].writes is False, f"{name} reaches a write tool"


def test_the_coordinator_can_reach_nothing_its_caller_lacks():
    """Every tool any operation needs is already granted to the researcher."""
    granted = tools_for("researcher")
    needed = {c.requires for c in OPERATIONS.values() if c.requires is not None}
    assert needed <= granted, f"coordinate would widen the grant by {needed - granted}"


def test_a_caller_without_the_tool_is_denied():
    """The resolver holds no get_ticket (Day 8). A plan must not be a way around that."""
    context = MandalaContext(actor="agent:resolver", request_id="req-x")
    with pytest.raises(PermissionDenied):
        run_plan(_plan({"op": "fetch_tickets", "ticket_ids": ["T-1001"]}), context=context)


def test_permission_is_checked_before_any_step_runs(tmp_path):
    """FLIP IT: move the permission loop inside the execution loop and this goes red.

    A denied plan must not have executed its earlier steps. Here step 1 is pure and
    step 2 is denied; if you see the marker file, your check runs too late.
    """
    marker = tmp_path / "ran.txt"
    context = MandalaContext(actor="agent:resolver", request_id="req-x")
    plan = _plan(
        {"op": "count_by", "field": "severity"},
        {"op": "fetch_tickets", "ticket_ids": ["T-1001"]},
    )
    with pytest.raises(PermissionDenied):
        run_plan(plan, context=context)
    assert not marker.exists()
    # TODO(me): make this test actually prove it — monkeypatch mandala.coordinator._tickets
    # to write `marker`, so a late check leaves evidence. As written it only asserts the
    # raise. Deciding what a test really proves is the rep.


def test_the_coordinator_grants_no_write_ability():
    assert TOOLS["coordinate"].writes is False
    assert "coordinate" in tools_for("researcher")
    assert trifecta_violations() == []          # still [], fifteen days running (Day 8)

# --- partial failure ---------------------------------------------------------------
def test_one_bad_ticket_does_not_lose_the_batch(mandala_context):
    """Day 14's processor, Day 15's search loop, and now this. Same call, third time."""
    plan = _plan({"op": "fetch_tickets", "ticket_ids": ["T-1001", "T-DOES-NOT-EXIST", "T-1002"]})
    result = run_plan(plan, context=mandala_context)
    assert len(result.rows) == 2
    assert any("T-DOES-NOT-EXIST" in e for e in result.errors)


def test_filter_and_count_agree(mandala_context):
    """The one behavioural property of the executor worth asserting."""
    plan = _plan(
        {"op": "fetch_tickets", "ticket_ids": ["T-1001", "T-1002", "T-1004"]},
        {"op": "count_by", "field": "severity"},
    )
    result = run_plan(plan, context=mandala_context)
    assert sum(result.counts.values()) == len(result.rows)

# --- the economics -----------------------------------------------------------------
@pytest.mark.vcr
@pytest.mark.asyncio
async def test_the_coordinator_path_costs_strictly_fewer_model_calls(tmp_path):
    """The day's claim, asserted. Same job, both paths, counted with Day 14's tracer."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "days/day-14/lab"))
    from span_tree import load, model_calls

    from mandala.tracing import install_local_tracing
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "days/day-18/lab"))
    from roundtrip_count import JOB, coordinated, naive

    from agents import Runner

    async def count(agent, label, max_turns):
        directory = tmp_path / label
        processor = install_local_tracing(directory)
        context = MandalaContext(actor="agent:researcher", request_id=f"req-{label}")
        await Runner.run(agent, JOB, context=context, max_turns=max_turns)
        processor.force_flush()
        return sum(model_calls(load(p)) for p in directory.glob("*.jsonl"))

    naive_calls = await count(naive(), "naive", 14)
    coord_calls = await count(coordinated(), "coord", 6)

    assert coord_calls > 0, "model_calls() found nothing — check the span type (Day 14 §8)"
    assert coord_calls < naive_calls, f"coordinator {coord_calls} !< naive {naive_calls}"
```

**Line by line:**

- `test_the_plan_schema_rejects_an_unknown_operation` — **the allowlist proof, and the first test to
  write.** Note what it asserts: not that `run_plan` refuses `delete_everything`, but that the plan
  containing it never becomes a `Plan` object at all. Rejection at the schema boundary means every
  later line of code is allowed to assume the operation set is closed.
- `test_a_step_cannot_carry_an_argument_nobody_defined` — the `extra="forbid"` half. Without this
  test, someone removes the `model_config` line during a refactor and nothing goes red for months.
- `test_the_operation_registry_is_exactly_the_five_we_reviewed` — a **change-detector test, on
  purpose.** Normally you avoid these. Here, going red *is the feature*: adding a coordinator
  operation is a capability change, and a capability change should not sail through CI silently. Same
  spirit as Day 8's `test_every_tool_declares_a_blast_radius`.
- `test_a_plan_that_would_touch_too_many_items_is_refused_before_it_runs` — ships **red**, because
  `plan_cost` is your `TODO(me)`. The `pytest.raises((ValidationError, ValueError))` accepts either
  because a big enough list is caught by `max_length` first; the interesting case is the one that
  slips past the field cap and must be caught by the pre-flight sum.
- `test_the_rendered_output_is_bounded` — a 50 KB body, thirty rows. This is the **Day 4 test**: the
  worst input you can imagine must still produce a string that fits in a context window. It asserts
  on `render()`, not on `run_plan()`, because the cap belongs to the thing that talks to the model.
- `test_every_operation_that_touches_a_tool_names_a_real_permission` — **the trap of the day, turned
  into an assertion.** It also asserts `writes is False`, which is what catches the future day
  somebody adds a `post_replies` op "just for the batch". You want that to be red before it is
  reviewed, not after it is merged.
- `test_the_coordinator_can_reach_nothing_its_caller_lacks` — the subset assertion, and the
  `blast_radius` sentence ("a batcher, never a widener") turned into code. Day 15's rule: **when a
  design sentence can become a test, make it one.** Its partner
  `test_a_caller_without_the_tool_is_denied` is the *negative* demonstration, using Day 8's real
  agents: the resolver was built with no `get_ticket` so it could never see a raw ticket body
  (Day 14's `test_resolver_cannot_read_tickets`), and this proves the coordinator did not hand it one.
- `test_permission_is_checked_before_any_step_runs` — **the flip-it test.** Move the permission loop
  into the execution loop, and a plan whose fourth step is denied will have run its first three. The
  embedded `TODO(me)` is deliberate: as written the test only proves the raise, and noticing the gap
  between "what I asserted" and "what I meant" is a skill this project keeps asking for.
- `test_the_coordinator_grants_no_write_ability` re-asserts `trifecta_violations() == []` on the day a
  new capability was added. **Invariants are worth re-asserting exactly when capability grows** —
  same line as Day 15.
- `test_one_bad_ticket_does_not_lose_the_batch` asserts *both* halves: the rows survived **and** the
  failure was reported. A test that only checked `len(rows) == 2` would pass an implementation that
  swallows errors silently, which is the version of this pattern that gets people fired.
- `test_filter_and_count_agree` — the only behavioural test of `_apply`, and it is a **relationship**
  (`sum(counts) == len(rows)`) rather than a hard-coded tally. A relationship survives you editing
  the fixture file; a hard-coded `{"high": 2}` does not.
- `test_the_coordinator_path_costs_strictly_fewer_model_calls` — the cassette-backed one, and the only
  test in the file that costs anything. It asserts **`coord_calls > 0` first**, because a comparison
  against a broken counter is worse than no comparison: `0 < 9` passes and proves nothing. **Assert
  your instrument before you assert your result.** Its import gymnastics are ugly and honest —
  **TODO(me): move the lab-path insertion into `tests/conftest.py`**, since you now do it in two
  files, which is exactly one more than you should.
- **Every test above except the last costs 0 model requests.** The whole security design lives in a
  Pydantic model, a dict, and a pure function, which is why it is free to test — and that is not a
  coincidence, it is why those were the right places to put it.

---

## §6 Traps

- **A coordinator operation that reaches a tool not in the permission table.** You have built a
  privilege-escalation path around Day 8, inside a tool call, where nothing is looking.
  **🎯 The trap of the day** — and it arrives disguised as "I'll just add a `post_replies` op so the
  batch can finish the job".
- **Dispatching operations by string** (`OPERATIONS[step.op]`, `getattr(module, step.op)`). It works
  today, and the day someone adds a helper to the module, the allowlist has a new member nobody
  granted. `isinstance` chains are boring; boring is the point.
- **A denylist instead of an allowlist.** "Any op except the dangerous ones" is a list you have to
  keep complete forever, against an adversary who only has to find one you forgot.
- **Checking caps during execution instead of before it.** By the time you notice the plan was too
  big, you have already fetched twenty-five tickets. Pre-flight, always.
- **Letting the plan carry a path, a URL, or a shell fragment.** The moment a plan field is a string
  that names something outside the working set, you have written a remote-execution primitive with a
  Pydantic model in front of it.
- **Forgetting `extra="forbid"`.** Unknown keys are silently dropped, and your careful schema becomes
  advisory.
- **Swallowing `PermissionDenied` in the batch loop.** Partial-failure isolation is for ingestion, not
  for boundaries. A degraded security check is not a security check (Day 10, third time).
- **Trusting the naive count without checking `model_calls()` first.** If the counter reads zero, the
  ratio is infinity and the lab prints a lie with a straight face. Day 14 §8 left this open on
  purpose; today is when it bites.
- **Comparing paths with different prompts.** Same `JOB` string, same model pin, `temperature=0.0`. If
  you tune one side's wording you are benchmarking prose.
- **Ignoring `parallel_tool_calls`.** If your provider batches tool calls, the naive path collapses and
  your headline number is wrong. Measure both, report both — the context saving survives either way.
- **Replacing `get_ticket` with `coordinate`.** One ticket through a plan costs more tokens than it
  saves. Add the coordinator; do not amputate the simple path.
- **Losing observability.** Nine tool calls left nine spans; one coordinate call leaves one. If you do
  not put the batch's shape into the audit line and the result's `errors`, you have traded round trips
  for blindness (Principle 8).

---

## §7 Request budget

| Activity | Model requests | Notes |
|---|---|---|
| Plan-schema iteration (`Plan.model_json_schema()`, printing tool schemas) | **0** | pure Pydantic |
| Every test except the last one | **0** | schema, caps, permissions, partial failure |
| `coordinator_demo.py` × 2 | ~4 (Groq) | the coordinator path is ~2 calls per run |
| **`roundtrip_count.py` × 2** | **~24 (Groq)** | ~11 naive + ~2 coordinated, twice |
| `roundtrip_count.py` × 1 with `parallel_tool_calls=True` | ~6 (Groq) | the honest second measurement |
| Prompt iteration to get a clean plan out of the model | ~14 (Groq) | budget for this; the first plan is usually wrong |
| Cassette recording for `test_..._strictly_fewer_model_calls` | ~13 (Groq) | records both paths |
| **Total** | **≈ 61, Groq** | log it in `docs/RATE_BUDGET.md` |

**The expensive part of today is the naive path, and that is the joke.** Roughly half of this budget
is spent *demonstrating* the thing you are here to stop doing. That is unavoidable and it is worth
paying once — but only once. After you have the two numbers, run the demo through the coordinator path
only.

If your Groq daily ceiling is tight: drop the `parallel_tool_calls=True` re-measurement first (note in
the CHECKLIST that you skipped it), then drop `coordinator_demo.py` and read the trace from the
roundtrip run instead. **Do not drop `roundtrip_count.py`** — it is the only part of today that
produces a number rather than an opinion.

Everything in `mandala.coordinator` that matters for safety is testable at **0 requests**. That is a
design result, not a coincidence.

---

## §8 Verify before you code

Written **2026-08-20** against `openai-agents` **0.22.0**. **The paid half of today cannot be run
here** — its API shape must be *read*, not tested, so read it carefully and quote it accurately.

- `https://platform.openai.com/docs/guides/tools` — the hosted-tool surface, including the code
  interpreter / programmatic tool calling section. **Confirm the language the generated program is
  written in** (the plan's OAI-17 row says JS) and how a job is expressed.
- `https://platform.openai.com/docs/api-reference/responses/create` — the Responses `tools` array.
  **Find `allowed_callers`: which object it lives on, what the legal values are, and what happens when
  it is omitted.** If omission means "any caller", say so in your notes — a default-open permission
  field is worth knowing about.
- `https://openai.github.io/openai-agents-python/tools/` — how the Agents SDK exposes hosted tools,
  and whether the SDK surfaces programmatic tool calling at all in **0.22.0**. If it does, that is
  news and belongs in `docs/CHANGELOG_PLAN.md`.
- `https://openai.github.io/openai-agents-python/ref/tool/` — **confirm in 0.22.0** that
  `function_tool` still accepts `name_override` and `failure_error_function` (unchanged since Day 10),
  and that `tool.params_json_schema` is the attribute name (Day 15 left this a `TODO(me)`).
- **Confirm in 0.22.0: a Pydantic `BaseModel` as a function-tool parameter.** Print
  `coordinate.params_json_schema` and look at what the model will actually receive. If strict-schema
  mode rejects the `anyOf` a discriminated union produces, the fallback is
  `def coordinate(ctx, plan_json: str)` plus `Plan.model_validate_json(plan_json)` — same validation,
  same allowlist, uglier schema. **This is the single most likely thing in today's code to need
  changing**, so check it before you write the demo, not after.
- **Confirm in 0.22.0: `ModelSettings.parallel_tool_calls`** exists and that LiteLLM forwards it to
  Groq. `roundtrip_count.py` depends on it for an honest naive baseline. If it does not exist or is
  ignored, record the batched number instead and say so in the CHECKLIST — a measurement with a
  documented caveat beats a measurement you fudged.
- `https://openai.github.io/openai-agents-python/ref/tracing/span_data/` — **the span-data type your
  provider actually produces.** `model_calls()` matches on `"Generation"`. Day 14 §8 flagged this and
  it is unresolved; today it is load-bearing. Print one span's labels before you trust a ratio.
- If any of the above differs from this lesson: one line in `docs/CHANGELOG_PLAN.md`. If the paid
  feature's shape has moved materially, that is a Part-4 matrix fact and needs an addendum before the
  next 🅿️ day (Principle 14) — **do not silently adapt.**

---

## §9 Say it in an interview

> "Programmatic tool calling is OpenAI's paid answer to round-trip economics: instead of the model
> calling your tools one at a time, it writes a small program that calls them inside their sandbox, and
> only the result comes back — so an eight-ticket job goes from about nine model calls to two, and the
> eight tool results never enter the context at all. The field people underrate is `allowed_callers`,
> which decides *which caller* may invoke each tool. That is a permission boundary, not a performance
> switch: it is how you let the generated program read tickets while making sure it can never send a
> reply. I couldn't run it — it needs a paid Responses key and my project is zero-budget — so I built
> the free analog: one coordinator function tool where the model fills in a typed Pydantic plan and my
> Python executes it. I measured both paths with my own tracer: **nine model calls naive, two through
> the coordinator, on the same eight-ticket job with the same prompt.** On a free tier, round trips
> *are* the budget, so that ratio is the whole win."

> "The compare/contrast I'd actually give is this: **their model emits code, mine emits data.** Code
> is more expressive — it can branch, retry and compose operations I never anticipated, and that is a
> genuine capability gap I'd concede. Data is more reviewable: I can print the plan before I run it,
> assert on it in a unit test, and put it in an audit line. And because it is data, I could enforce a
> rule that a program can't enforce for you — every operation declares the permission it needs, and
> the coordinator calls the same permission check my ordinary tools use, with the calling agent's
> identity, *before any step runs*. That matters because a coordinator is an interpreter, and an
> interpreter that accepts arbitrary operations is `eval()` with extra steps. So it is an allowlist of
> five operations, typed arguments, hard caps checked pre-flight, and no reach past tools the agent
> already had. The costs I'd name up front: the model loses adaptivity mid-job, I own a plan schema
> forever, and I own partial failure — one missing ticket goes into an `errors` list and the other
> seven come back, which is the third time on that project I've made the same call."

---

## §10 Done when

```bash
./m check
./m done 18
```

Tomorrow: the model-native harness 🅿️ — the paid Codex-style filesystem/memory layer you will only
ever read about — paired with the free lab that gives you its actual guarantee: agent-generated code
running in a **local Docker container** with no network, a read-only mount and a hard timeout
(OAI-18/19/20). Today you bounded what a plan may *do*; tomorrow you bound where code may *run*.
