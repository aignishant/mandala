---
day: 5
phase: 1
phase_name: "Agents from first principles"
title: "ReAct and its ceiling — reacting vs. planning"
ids: ["AG-05", "AG-06"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 5 — ReAct and its ceiling

**Phase 1 · Agents from first principles** · IDs: **AG-05 🛠️**, **AG-06 🛠️**

> **Yesterday:** the output has a shape, and you know where your tokens go.
> **Today:** you give the loop a job big enough to make it wander, watch it wander, and then fix it
> two different ways — with a cap, and with a plan.
> **Tomorrow:** prompts as APIs, and the router every later phase reuses.

```bash
./m start 5
./m scaffold 5
```

---

## §1 The story

Day 3's agent answered one question with one lookup. That is not an agent working; that is a
function call with extra steps.

Today you give it something harder: *"Which of our open tickets are probably the same underlying
problem, and what should we tell those customers?"*

Now it has to search, read several tickets, compare them, notice a pattern, and write a conclusion.
Several steps, and it must choose them itself. That is where the interesting failure lives.

The pattern it uses has a name — **ReAct**, short for *Reason + Act*. The model thinks out loud
("I should look for tickets mentioning login"), acts (calls `search_tickets`), observes the result,
thinks again. You already built this on Day 3; you just did not name it. Today you name it, and more
importantly you find its **ceiling**.

Here is the ceiling, in one sentence: **a reacting agent has no memory of its own intent.**

Every turn it re-derives what it is doing from the transcript. Usually that is fine. But when a tool
returns something unexpected, the model can quietly re-derive a *different* goal, chase that for
three turns, come back, and start over. It looks like thinking. It is closer to a person who keeps
walking into a room and forgetting why.

You will watch this happen today. It is genuinely one of the more useful things in these 90 days,
because it is the reason LangGraph exists, and on Day 43 you will understand that framework in about
ten minutes instead of two days.

Then you fix it two ways. The cheap fix is a **cap** — six turns and stop. The real fix is
**planning**: make the model write the steps down *first*, then execute them. A plan is memory of
intent that survives a confusing observation.

---

## §2 Setup — run this

No new packages.

```bash
mkdir -p days/day-05/lab
touch days/day-05/lab/react_agent.py
touch days/day-05/lab/plan_execute.py
touch days/day-05/lab/wander.py
touch src/mandala/trace.py
touch tests/test_react_limits.py
```

---

## §3 AG-05 — The ReAct pattern and its limits

### The plain idea

ReAct interleaves two things the model is good at:

- **Reason** — a sentence of plain-text thinking about what to do next.
- **Act** — a tool call.

The transparency is the selling point. When it goes wrong you can read *why*, because the reasoning
is right there in the transcript. Compare that with a model that silently emits a tool call: you can
see *what* it did but not what it believed.

Two ways to get the reasoning out of the model:

| Style | How | Trade-off |
|---|---|---|
| **Implicit** | just let it produce `content` alongside `tool_calls` | free, but many models return `content=None` when calling a tool |
| **Explicit** | add a required `thought` argument to every tool schema | always present, costs a few tokens, and **it makes the model think before choosing** |

The second is the interesting one and it is what you will build. Forcing a `thought` field is not
just instrumentation — models produce measurably better tool choices when required to justify the
call in the same breath as making it.

### The three failure modes you must see

| Failure | What it looks like | Today's fix |
|---|---|---|
| **The loop** | calls `search_tickets("login")` four times with the same arguments | detect repeats, feed the repetition back as an observation |
| **The drift** | asked about duplicates, ends up summarising one ticket | a plan (§4) |
| **The premature stop** | answers after one search, having read nothing | tighten the task contract in the prompt |

### 3.1 `src/mandala/trace.py` — see the wandering

Before you can fix wandering you must be able to see it. Principle 8: *the trace is the truth.*

```python
"""A tiny in-memory trace. Not observability — just enough to see the loop think.

Real tracing lands on Day 14 (SDK) and Day 75 (OTel). This exists so Day 5 has
something to look at, and so the tests can assert on behaviour instead of prose.

Usage
-----
    >>> t = Trace()
    >>> t.record(turn=1, thought="look for login tickets",
    ...          tool="search_tickets", args={"query": "login"}, result_len=412)
    >>> t.repeated_calls()
    []
    >>> t.tool_names()
    ['search_tickets']
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class Step:
    turn: int
    thought: str
    tool: str
    args: dict
    result_len: int

    def signature(self) -> str:
        """What makes two calls 'the same call'. Sorted keys so ordering never matters."""
        return f"{self.tool}:{json.dumps(self.args, sort_keys=True)}"


@dataclass
class Trace:
    steps: list[Step] = field(default_factory=list)

    def record(self, **kwargs) -> None:
        self.steps.append(Step(**kwargs))

    def tool_names(self) -> list[str]:
        return [s.tool for s in self.steps]

    def repeated_calls(self) -> list[str]:
        """Signatures called more than once — the loop-detector."""
        seen: dict[str, int] = {}
        for step in self.steps:
            sig = step.signature()
            seen[sig] = seen.get(sig, 0) + 1
        return [sig for sig, count in seen.items() if count > 1]

    def render(self) -> str:
        return "\n".join(
            f"  [{s.turn}] {s.thought[:70]}\n      -> {s.tool}({json.dumps(s.args)}) "
            f"[{s.result_len} chars]"
            for s in self.steps
        )
```

**Line by line:**

- `@dataclass class Step` — one row per tool call. Five fields, no behaviour beyond `signature()`.
- `def signature(self)` — the identity of a call. `json.dumps(self.args, sort_keys=True)` is the key
  detail: **without `sort_keys=True`**, `{"query": "a", "limit": 3}` and `{"limit": 3, "query": "a"}`
  would serialise differently and your loop detector would miss a genuine repeat. Dict ordering is
  insertion-ordered in Python, and the model does not always emit keys in the same order.
- `result_len: int` — the *length* of the result, not the result itself. A trace you can print in
  full is a trace you will actually read. Storing the whole payload here would make `render()`
  unreadable and the object huge.
- `def record(self, **kwargs)` — accepts keyword arguments and forwards them to `Step`. Calling it
  as `t.record(turn=1, thought=..., ...)` reads well at the call site, and a typo'd field name
  raises immediately rather than being silently stored.
- `repeated_calls()` — builds a count per signature, then returns those seen more than once. This is
  your loop detector, and it is nine lines. You do not need anything cleverer.
- `seen.get(sig, 0) + 1` — the standard counting idiom, defaulting to zero for a new key.
- `render()` — a generator expression inside `"\n".join(...)`, so the whole trace is built in one
  expression. `s.thought[:70]` truncates so each step stays on two lines.

### 3.2 `days/day-05/lab/react_agent.py`

The Day-3 loop, plus three things: an explicit `thought`, a trace, and loop detection.

```python
"""ReAct with visible reasoning and a loop detector.

Run:
    uv run python days/day-05/lab/react_agent.py \
        "Which open tickets are probably the same underlying problem?"
"""

from __future__ import annotations

import json
import sys

from openai import OpenAI

from mandala.config import load_keys
from mandala.models import PROVIDERS
from mandala.trace import Trace
from tools import TOOLS

SYSTEM = (
    "You are Mandala's support analyst.\n"
    "Work in small steps. Before EVERY tool call, state your reasoning in the "
    "'thought' argument: what you are trying to learn and why this call helps.\n"
    "Do not repeat a call you have already made with the same arguments — if you "
    "already have the result, use it.\n"
    "When you have enough evidence, answer directly without calling a tool.\n"
    "Never invent ticket ids or ticket contents."
)


def _with_thought(schema: dict) -> dict:
    """Add a required 'thought' argument to an existing tool schema."""
    schema = json.loads(json.dumps(schema))          # deep copy, stdlib only
    params = schema["function"]["parameters"]
    params["properties"]["thought"] = {
        "type": "string",
        "description": "Why you are making this call, in one sentence. Required.",
    }
    params["required"] = [*params.get("required", []), "thought"]
    return schema


def run(question: str, max_turns: int = 6, verbose: bool = True) -> tuple[str, Trace]:
    from tools import TOOL_SCHEMAS

    schemas = [_with_thought(s) for s in TOOL_SCHEMAS]
    provider = PROVIDERS["groq"]
    client = OpenAI(api_key=load_keys().groq, base_url=provider.base_url)
    trace = Trace()

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]

    for turn in range(1, max_turns + 1):
        response = client.chat.completions.create(
            model=provider.default_model, messages=messages, tools=schemas
        )
        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            if verbose:
                print(trace.render())
            return (message.content or ""), trace

        for call in message.tool_calls:
            args = json.loads(call.function.arguments)
            thought = args.pop("thought", "(no thought given)")
            name = call.function.name

            try:
                result = TOOLS[name](**args)
            except (KeyError, TypeError) as exc:
                result = {"error": f"{type(exc).__name__}: {exc}"}

            payload = json.dumps(result)
            trace.record(turn=turn, thought=thought, tool=name, args=args,
                         result_len=len(payload))

            # loop detection: tell the model, do not just log it
            if trace.repeated_calls():
                payload = json.dumps({
                    "warning": "You already made this exact call. Use the earlier result "
                               "or try a different approach.",
                    "result": result,
                })

            messages.append({"role": "tool", "tool_call_id": call.id, "content": payload})

    if verbose:
        print(trace.render())
    raise RuntimeError(f"did not converge in {max_turns} turns")


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Which open tickets share an underlying problem?"
    answer, trace = run(question)
    print("\n--- answer ---")
    print(answer)
    print(f"\ntool calls: {trace.tool_names()}")
    print(f"repeats:    {trace.repeated_calls()}")
```

**Line by line — the new parts:**

- `SYSTEM` as a multi-line string with `\n` — four separate instructions, each on its own line.
  **Instructions in a numbered or line-separated list are followed more reliably than the same
  instructions in a paragraph.** This is AG-07 arriving a day early.
- *"Do not repeat a call you have already made"* — stating the rule in the prompt is your first line
  of defence. The loop detector is the second. You want both: prompts reduce the frequency, code
  handles the residue.
- `def _with_thought(schema)` — **decorating a schema rather than rewriting your tools.** Day 3's
  `TOOL_SCHEMAS` stays untouched; this function adds one argument to a copy. Now Day 3's tests still
  pass and Day 5's agent gets reasoning, with no duplicated schema definitions.
- `json.loads(json.dumps(schema))` — a **deep copy** using only the standard library. Why deep?
  Because `schema["function"]["parameters"]["properties"]` is a nested dict; a shallow `dict(schema)`
  would share that inner dict, and mutating it would corrupt the original module-level
  `TOOL_SCHEMAS`. (`copy.deepcopy` also works; this idiom is common and makes the intent obvious.)
- `params["required"] = [*params.get("required", []), "thought"]` — unpack the existing required list
  into a new list and append. Creating a new list rather than `.append()`-ing avoids mutating a list
  that might be shared.
- `thought = args.pop("thought", "(no thought given)")` — **`pop` removes it as it reads it.** This
  is essential: `thought` is for you, not for the tool. If it stayed in `args`, the very next line's
  `TOOLS[name](**args)` would raise `TypeError: got an unexpected keyword argument 'thought'`.
- `trace.record(...)` before the loop check — record first, then decide, so the trace is complete
  even for the call that triggers the warning.
- The `if trace.repeated_calls():` block — **this is the key design decision of the day.** When the
  model repeats itself you do not raise, and you do not silently log. You **wrap the result in a
  warning and send it back as the observation.** The model reads "you already did this" as part of
  its next input and course-corrects. Feeding problems back into the loop as observations, rather
  than handling them outside it, is the single most transferable technique in agent engineering —
  and you will see all four frameworks do exactly this in different clothes.
- `return (message.content or ""), trace` — returning the trace alongside the answer is what lets
  tests assert on *behaviour* ("did it call the right tools in a sane order?") rather than on prose.
  That is a trajectory eval, and it is Day 71's whole subject arriving early.

---

## §4 AG-06 — Planning vs. reacting

### The plain idea

**Reacting:** decide the next step from what you know right now. Cheap, flexible, and it forgets its
own intent.

**Planning:** decide all the steps first, then execute them. More expensive up front, and the plan is
a written record of intent that survives a confusing observation.

Neither is better. They win in different situations:

| Situation | Better | Why |
|---|---|---|
| One lookup, obvious answer | **React** | a plan is pure overhead |
| Unknown terrain, each step depends on the last | **React** | you cannot plan what you cannot foresee |
| Several known steps over several sources | **Plan** | drift is the main risk, and a plan pins intent |
| Anything a human must approve before it runs | **Plan** | you cannot approve a plan that does not exist |

That last row is the one that matters for Mandala. On Day 50 a human approves an action before it
happens. **You cannot show a reviewer a plan the agent has not written.** Planning is not just an
accuracy technique — it is a prerequisite for human oversight, which is Principle 12.

### 4.1 `days/day-05/lab/plan_execute.py`

```python
"""Plan-then-execute: write the steps down first, then run them.

Run:
    uv run python days/day-05/lab/plan_execute.py \
        "Which open tickets share an underlying problem, and what should we tell those customers?"
"""

from __future__ import annotations

import json
import sys
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field

from mandala.config import load_keys
from mandala.models import PROVIDERS
from mandala.trace import Trace
from tools import TOOLS


class PlanStep(BaseModel):
    tool: Literal["get_ticket", "search_tickets", "answer"] = Field(
        description="Which tool this step uses. Use 'answer' for the final synthesis step."
    )
    args: dict = Field(default_factory=dict, description="Arguments for the tool. {} for 'answer'.")
    why: str = Field(description="What this step is for, in one sentence.")


class Plan(BaseModel):
    goal: str = Field(description="Restate the user's goal in your own words.")
    steps: list[PlanStep] = Field(
        min_length=1, max_length=6,
        description="Ordered steps. The LAST step must use the 'answer' tool.",
    )


PLANNER_SYSTEM = (
    "You are Mandala's planner. Given a question, produce a short ordered plan.\n"
    "Use search_tickets when you do not have exact ids; get_ticket when you do.\n"
    "Six steps maximum. The last step must be 'answer'.\n"
    "Do not attempt to answer the question here — only plan."
)

_provider = PROVIDERS["groq"]
_client = OpenAI(api_key=load_keys().groq, base_url=_provider.base_url)

PLAN_TOOL = {
    "type": "function",
    "function": {
        "name": "submit_plan",
        "description": "Submit your plan. Calling this is how you finish planning.",
        "parameters": Plan.model_json_schema(),
    },
}


def make_plan(question: str) -> Plan:
    response = _client.chat.completions.create(
        model=_provider.default_model,
        messages=[
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": question},
        ],
        tools=[PLAN_TOOL],
        tool_choice={"type": "function", "function": {"name": "submit_plan"}},
    )
    return Plan.model_validate_json(response.choices[0].message.tool_calls[0].function.arguments)


def execute(plan: Plan, question: str) -> tuple[str, Trace]:
    trace = Trace()
    observations: list[str] = []

    for i, step in enumerate(plan.steps, start=1):
        if step.tool == "answer":
            break
        try:
            result = TOOLS[step.tool](**step.args)
        except (KeyError, TypeError) as exc:
            result = {"error": f"{type(exc).__name__}: {exc}"}
        payload = json.dumps(result)
        trace.record(turn=i, thought=step.why, tool=step.tool, args=step.args,
                     result_len=len(payload))
        observations.append(f"step {i} ({step.tool}): {payload[:600]}")

    synthesis = _client.chat.completions.create(
        model=_provider.default_model,
        messages=[
            {"role": "system", "content": "Answer the question using ONLY the observations "
                                          "below. Cite ticket ids. If the observations are "
                                          "insufficient, say what is missing."},
            {"role": "user", "content": f"Question: {question}\n\nObservations:\n"
                                        + "\n".join(observations)},
        ],
    )
    return synthesis.choices[0].message.content or "", trace


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Which open tickets share an underlying problem?"
    plan = make_plan(question)

    print(f"goal: {plan.goal}\n")
    for i, step in enumerate(plan.steps, start=1):
        print(f"  {i}. {step.tool}({json.dumps(step.args)})  — {step.why}")

    input("\npress enter to execute this plan, or ctrl-c to abandon it > ")

    answer, trace = execute(plan, question)
    print("\n--- answer ---")
    print(answer)
```

**Line by line:**

- `class PlanStep(BaseModel)` with `tool: Literal[...]` — **the plan itself is a validated schema.**
  Yesterday's lesson applied to a new object: if the model invents a tool named `lookup_ticket`, the
  plan fails validation before a single step executes.
- `"answer"` included in the `Literal` — a pseudo-tool marking the synthesis step. Modelling "and
  then answer" as a step keeps the plan a complete description of what will happen.
- `args: dict = Field(default_factory=dict, ...)` — `default_factory` again, for the same
  mutable-default reason as Day 4.
- `min_length=1, max_length=6` on `steps` — the cap, **enforced by the schema instead of by a
  counter**. A plan of 40 steps is rejected before it costs you 40 requests. Compare with Day 3's
  `max_turns`, which only stops you after you have already spent.
- `PLANNER_SYSTEM` ends with *"Do not attempt to answer the question here — only plan."* Without
  that line, models routinely answer during planning, and you pay twice.
- `make_plan` uses the tool-as-schema trick with `tool_choice` — exactly Day 4's technique, applied
  to a different object. This is the deliberate repetition the plan's Part 6 is built on.
- `for i, step in enumerate(plan.steps, start=1):` — `start=1` makes the counter human-readable.
- `if step.tool == "answer": break` — the synthesis happens after the loop, with all observations
  available.
- `payload[:600]` — **truncate each observation.** This is Day 4's "trim the tool result" lever
  applied concretely. Without it the synthesis prompt grows unboundedly with the number of steps.
- The synthesis prompt says *"using ONLY the observations below"* and *"If the observations are
  insufficient, say what is missing."* — the second half is what stops the model filling gaps with
  invention. Giving a model an honest way out is how you get honest answers.
- `input("\npress enter to execute this plan...")` — **this line is the point of the whole file.**
  A human sees the plan before anything runs. It is crude, and it is genuinely the same shape as
  OAI-23 approvals (Day 21), CrewAI HITL (Day 33), LangGraph `interrupt()` (Day 50) and MCP
  Elicitation (Day 56). Four sophisticated implementations of `input()`. Recognising that on Day 5
  makes all four land faster.

---

## §5 Make it wander — `days/day-05/lab/wander.py`

You cannot fix what you have not seen. This file's job is to *provoke* the failure.

```python
"""Provoke the three ReAct failure modes on purpose.

Budget: ~20 requests. Groq.

Run:
    uv run python days/day-05/lab/wander.py
"""

from react_agent import run

PROVOCATIONS = [
    # 1. vague scope -> the drift
    "Look into the login problems and also anything about invoices, then tell me what matters most.",
    # 2. non-existent thing -> the loop (it keeps searching for something that isn't there)
    "Find all tickets about the mobile app crash and summarise them.",
    # 3. trivially answerable -> the premature stop
    "Are there any billing tickets?",
]

for i, question in enumerate(PROVOCATIONS, start=1):
    print(f"\n{'=' * 70}\n[{i}] {question}\n{'=' * 70}")
    try:
        answer, trace = run(question, max_turns=6, verbose=True)
        print(f"\nanswer: {answer[:300]}")
    except RuntimeError as exc:
        print(f"\nDID NOT CONVERGE: {exc}")
        continue
    print(f"tools:   {trace.tool_names()}")
    print(f"repeats: {trace.repeated_calls()}")
```

**What to watch for, and what it teaches:**

1. **Provocation 1 (drift).** Two goals in one sentence. Watch the trace: it usually pursues one,
   then the other, then produces an answer about only one of them. *The transcript contains both
   goals — but the model re-derives its intent every turn from a transcript that is now mostly about
   login.* **That is the ceiling of reacting, and you have just watched it.**
2. **Provocation 2 (loop).** There are no mobile-app tickets in the golden set. Watch it search
   "mobile", then "app", then "crash", then "mobile app". `repeats` may stay empty — the arguments
   differ each time — but it is looping in substance. **This is why your loop detector will miss
   real loops, and why `max_turns` is not optional.**
3. **Provocation 3 (premature stop).** Often answers "yes" after one search without reading any
   ticket. Technically correct, practically useless.

Now run the same three through `plan_execute.py` and compare. Provocation 1 usually improves
markedly: the plan names both goals up front and the executor visits both. **Write down what
changed** — that comparison is your interview answer for AG-06.

---

## §6 The eval that must be able to fail

### `tests/test_react_limits.py`

```python
"""Day-5 guardrails: the loop terminates, the trace is honest, plans are valid."""

import pytest

from mandala.trace import Trace


def test_repeated_calls_detects_reordered_args():
    """Key order must not hide a repeat. This is why signature() sorts keys."""
    t = Trace()
    t.record(turn=1, thought="a", tool="search_tickets",
             args={"query": "login", "limit": 3}, result_len=10)
    t.record(turn=2, thought="b", tool="search_tickets",
             args={"limit": 3, "query": "login"}, result_len=10)
    assert len(t.repeated_calls()) == 1


def test_different_args_are_not_repeats():
    t = Trace()
    t.record(turn=1, thought="a", tool="search_tickets", args={"query": "login"}, result_len=10)
    t.record(turn=2, thought="b", tool="search_tickets", args={"query": "invoice"}, result_len=10)
    assert t.repeated_calls() == []


def test_plan_rejects_unknown_tools():
    from plan_execute import Plan
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Plan.model_validate({
            "goal": "x",
            "steps": [{"tool": "delete_everything", "args": {}, "why": "no"}],
        })


def test_plan_rejects_oversized_plans():
    from plan_execute import Plan
    from pydantic import ValidationError

    steps = [{"tool": "get_ticket", "args": {"ticket_id": "T-1001"}, "why": "x"}] * 7
    with pytest.raises(ValidationError):
        Plan.model_validate({"goal": "x", "steps": steps})


@pytest.mark.vcr
def test_react_terminates_on_an_impossible_question():
    """No mobile-app tickets exist. The agent must give up, not spin."""
    from react_agent import run

    try:
        answer, trace = run("Summarise every mobile app crash ticket.", max_turns=4, verbose=False)
    except RuntimeError:
        return                       # hitting the cap is an acceptable outcome
    assert len(trace.steps) <= 4
    assert any(w in answer.lower() for w in ("no ", "none", "not find", "no tickets"))


@pytest.mark.vcr
def test_react_reads_a_ticket_before_answering_about_it():
    """A trajectory assertion: the path matters, not just the destination."""
    from react_agent import run

    _, trace = run("What is the severity of T-1004?", max_turns=4, verbose=False)
    assert "get_ticket" in trace.tool_names(), (
        f"answered without reading the ticket. Tools used: {trace.tool_names()}"
    )
```

**Line by line:**

- `test_repeated_calls_detects_reordered_args` — **the test that justifies `sort_keys=True`.** Delete
  that argument from `signature()` and this test goes red. This is exactly the kind of test that is
  worth writing: it pins a subtle decision that a future you would otherwise "simplify" away.
- `test_different_args_are_not_repeats` — the negative case. A detector that flags everything is as
  useless as one that flags nothing. **Always test both directions of a predicate.**
- `[...] * 7` — list multiplication repeats the element seven times. Fine here because the test only
  cares about the count. (In production code, `[{}] * 7` gives seven references to *the same* dict,
  which is a classic bug — worth knowing.)
- `except RuntimeError: return` — **hitting the cap is a passing outcome.** The test asserts "the
  agent terminates", not "the agent terminates gracefully". Writing the test to accept both honest
  outcomes stops it being flaky for the wrong reason.
- `test_react_reads_a_ticket_before_answering_about_it` — a **trajectory eval**: it asserts on the
  path, not the answer. This is the middle layer of AG-22's three (unit → trajectory → outcome), and
  it is the layer people skip. An agent can produce the right answer by luck; a trajectory assertion
  catches that.

---

## §7 Traps

- **Forgetting `args.pop("thought")`.** Every tool call raises `TypeError`. The most common Day-5 bug.
- **Mutating `TOOL_SCHEMAS` in place** in `_with_thought`. Day 3's tests break mysteriously. Deep-copy.
- **Raising on a repeated call instead of feeding it back.** You lose the agent's chance to recover.
- **Believing the loop detector catches all loops.** It catches *identical* calls. Semantic loops
  (`"mobile"`, `"app"`, `"crash"`) slip straight past it. `max_turns` is the backstop, not the
  detector.
- **Planning everything.** A plan for a single lookup is pure overhead — you paid an extra request to
  be told to make one call.
- **A plan with no cap.** `max_length=6` on the schema is what stops a 40-step plan costing 40
  requests.
- **Letting the synthesis step re-read raw tool output.** Truncate the observations, or you have
  rebuilt the fat-context problem from Day 4.
- **Skipping `wander.py` because the happy path works.** The failures are the lesson. You are
  buying an understanding of Day 43 for the price of twenty requests.

---

## §8 Request budget

| Activity | Requests |
|---|---|
| Getting `react_agent.py` working | ~20 (Groq) |
| `wander.py` — 3 provocations × up to 6 turns | ~18 (Groq) |
| `plan_execute.py` — plan + steps + synthesis, ~4 runs | ~20 (Groq) |
| Cassettes | ~8 |
| **Total** | **≈ 65, all Groq** |

---

## §9 Verify before you code

Written **2026-08-20**.

- `https://platform.openai.com/docs/guides/function-calling` — whether `tool_choice` still takes the
  `{"type": "function", "function": {"name": ...}}` form.
- `https://console.groq.com/docs/tool-use` — Groq's `tool_choice` support and any parallel-tool-call
  behaviour, which affects how many calls arrive per turn.
- `https://docs.pydantic.dev/latest/concepts/fields/` — `min_length` / `max_length` on list fields.

---

## §10 Say it in an interview

> "ReAct's real limitation isn't reasoning quality, it's that the agent re-derives its intent from
> the transcript every turn — so a surprising tool result can quietly change what it thinks it's
> doing. I've watched that happen: give it two goals in one sentence and it finishes one. The cheap
> mitigations are a turn cap and repeat-detection fed back into the loop as an observation rather
> than raised as an error. The real fix is to make it write a plan first, which also happens to be a
> prerequisite for human approval — you can't approve a plan that was never written down. That's the
> line of reasoning that leads directly to explicit graphs."

---

## §11 Done when

```bash
./m check
./m done 5
```

Tomorrow: the system prompt becomes an API, and you build the 429-aware router that every later
phase reuses.
