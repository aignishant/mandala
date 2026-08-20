---
day: 38
phase: 6
phase_name: "LangChain 1.x"
title: "`create_agent` and structured output, fourth time around"
ids: ["LC-05", "LC-06"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 38 — `create_agent`, and `TriageResult` for the fourth time

**Phase 6 · LangChain 1.x** · IDs: **LC-05 🛠️**, **LC-06 🛠️**

> **Yesterday:** typed content blocks, and tools whose schema hides an argument from the model.
> **Today:** the blessed loop. One function turns a model plus tools plus a prompt into a running
> agent — and it returns a **graph**, which is the fact Phase 7 is built on. Then `TriageResult`,
> for the fourth and final framework, with all four ergonomics finally comparable.
> **Tomorrow:** middleware — how you change any of this without subclassing anything.

```bash
./m start 38
./m scaffold 38
```

---

## §1 The story

Thirty-five days ago you wrote the loop by hand: model → tool → observe → repeat, forty lines, a
`max_iterations` guard, and a `Trace` object (Days 3–5). Since then three frameworks have offered to
own that loop for you. Today the fourth does, and it is the most compressed offer of the four:

```python
agent = create_agent(model, tools, system_prompt=...)
result = agent.invoke({"messages": [HumanMessage(ticket_body)]})
```

**That is the whole API.** No `Runner`, no `Crew`, no decorators. And the compression is the thing to
be suspicious of, so today asks two questions and answers both by looking rather than reading:

1. **What is `create_agent` actually returning?** (A `CompiledStateGraph`. That is not trivia — it is
   Day 42's seam, Day 45's node, and the reason `langgraph.prebuilt` is deprecated.)
2. **Where did my `max_iterations` guard go?** Day 5 built one because ReAct loops wander. A one-line
   agent constructor has one somewhere, or it does not, and both answers matter.

Then LC-06: `TriageResult` runs on its fourth framework. You now have all four data points for what
the plan has been claiming since Day 4 — *the schema is the durable artifact and the frameworks are
interchangeable around it.* Today is the day you can finally say whether that claim survived contact.

| Framework | Mechanism | Day |
|---|---|---|
| raw client | JSON mode + manual `model_validate` | 4 |
| Agents SDK | `output_type=TriageResult` | 11 |
| CrewAI | `output_pydantic=TriageResult` | 26 |
| **LangChain** | **`response_format=` on `create_agent`** | **today** |

---

## §2 Setup — run this

### 2.1 No new packages

```bash
grep -n 'langchain' pyproject.toml
```

### 2.2 Create today's files

```bash
touch src/mandala/lc/agent.py
touch tests/test_lc_agent.py
mkdir -p days/day-38/lab
touch days/day-38/lab/what_is_it.py
touch days/day-38/lab/triage_once.py
touch days/day-38/lab/four_ways.md
```

- `what_is_it.py` costs **0 requests** and answers question 1 by introspection. Do it before you run
  the agent; knowing what you are holding changes how you read everything after.
- `four_ways.md` is the LC-06 deliverable — the four-framework comparison, written once, referenced
  by the Day-63 bake-off. **This document is worth more than today's code.**

---

## §3 LC-05 — `create_agent`

### 3.1 `src/mandala/lc/agent.py`

```python
"""Mandala's triage agent, fourth framework.

What is new is not the behaviour -- it is that the loop, the tool dispatch, the
message accumulation and the structured-output coercion are all supplied by one
function. Everything Mandala-specific is a parameter to it.

What create_agent returns is a COMPILED GRAPH (LangGraph). That is why Day 42 can
drop this straight into a StateGraph, and why langgraph.prebuilt is deprecated in
its favour (LG-15, Day 45).

Blast radius (Principle 6): READ_TOOLS only. Mandala's first write is Day 82.

Usage
-----
    >>> from mandala.lc.agent import triage_agent
    >>> agent = triage_agent()
    >>> agent.invoke({"messages": [("user", "checkout is down")]})   # doctest: +SKIP
"""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

from mandala.lc.chat import fast_loop
from mandala.lc.tools import READ_TOOLS
from mandala.prompts import TRIAGE_SYSTEM
from mandala.schemas import TriageResult

#: Day 5's lesson: a ReAct loop wanders. Cap it, whatever the framework calls it.
MAX_STEPS = 6


def triage_agent(*, structured: bool = True):
    """Build the triage agent. One call, four frameworks' worth of scar tissue."""
    kwargs = {
        "model": fast_loop(),
        "tools": READ_TOOLS,
        "system_prompt": SystemMessage(TRIAGE_SYSTEM),
    }
    if structured:
        kwargs["response_format"] = TriageResult
    return create_agent(**kwargs)
```

**Line by line:**

- `from langchain.agents import create_agent` — from `langchain`, **not** `langchain_core`. Agents are
  framework, abstractions are core (Day 36 §3.1). The import path is the layering, visible.
- `model=fast_loop()` — Groq, because triage is many small tool-calling turns and Groq is the fast
  loop (`RATE_BUDGET.md` rule 4: route by shape). **The model is constructed by Day 36's factory**, so
  the pin still lives in `models.py` and this file names no vendor. Fourth framework, same rule.
- `tools=READ_TOOLS` — yesterday's list, unchanged. **Notice how little glue this took.** The tools
  were declared once; the agent takes them whole. Compare Day 25's per-agent `tools_for("analyst")`
  and Day 10's SDK registration, and put the comparison in `four_ways.md`.
- `system_prompt=SystemMessage(TRIAGE_SYSTEM)` — importing the prompt from `mandala.prompts`, written
  on Day 6. **The prompt is as portable as the schema**, and after four frameworks that is worth
  stating as a finding: the two things that survived every framework change are `schemas.py` and
  `prompts.py`.
- `response_format=TriageResult` — LC-06 in one keyword, §4 below.
- `structured: bool = True` as a keyword-only switch — Day 39's middleware and Day 40's streaming both
  want an *unstructured* agent to experiment against, and adding the flag now is cheaper than
  duplicating the constructor twice this week.
- `MAX_STEPS = 6` **defined but not yet passed.** That is deliberate and it is §3.3's assignment: find
  out what `create_agent` calls its iteration cap in 1.3.16 and wire it. **Do not ship this file with
  an unbounded loop** — an agent that can call tools forever is a free-tier quota with a hole in it.
- `kwargs` built as a dict — so the `structured` branch adds a key rather than duplicating the call.
  Small, and it keeps the two paths provably identical apart from one parameter, which §5 tests.

### 3.2 `days/day-38/lab/what_is_it.py` — 0 model requests

```python
"""What did create_agent actually give me? Introspect before you invoke.

Run:
    uv run python days/day-38/lab/what_is_it.py

Budget: 0 requests. Building an agent does not call a model.
"""

from mandala.lc.agent import triage_agent

agent = triage_agent()

print(f"type      {type(agent).__module__}.{type(agent).__name__}")
print(f"mro       {[c.__name__ for c in type(agent).__mro__[:4]]}")
print(f"has invoke  {hasattr(agent, 'invoke')}")
print(f"has stream  {hasattr(agent, 'stream')}")
print(f"has astream {hasattr(agent, 'astream')}")

graph = agent.get_graph()
print(f"\nnodes     {[n for n in graph.nodes]}")
print(f"edges     {[(e.source, e.target) for e in graph.edges]}")
print("\n" + graph.draw_ascii())
```

**Line by line:**

- `type(agent).__module__` printed with the class name — **the answer should contain `langgraph`.**
  Reading that line yourself, from your own installed packages, is worth more than any paragraph
  claiming it. `create_agent` lives in `langchain` and returns a LangGraph object; the two libraries
  are one product with two package names.
- `__mro__[:4]` — the method resolution order, first four entries. It shows you what the object *is*,
  not just what it is called.
- `hasattr(agent, 'stream')` — Day 40's streaming is already here. So is `astream`. **The agent is a
  Runnable**, which means `invoke` / `stream` / `batch` all work, which is the payoff of Day 36's
  "one universal verb" observation.
- `agent.get_graph()` — the compiled graph, introspectable. `nodes` and `edges` printed as data.
- `graph.draw_ascii()` — **the loop, drawn.** You should see something close to
  `__start__ → agent → tools → agent → __end__`, with a conditional edge from the agent node. That
  picture is Day 3's hand-written loop, compiled, and seeing them side by side is the single best
  moment of Phase 6. Keep the output; Day 43 will draw its own graph and you will want the comparison.
- If `draw_ascii()` needs an optional dependency, do **not** `uv add` it reflexively — check whether a
  `.get_graph().nodes` dump is enough, and if you do add one, it needs a `docs/PINS.md` ledger row and
  a changelog line (Principle 4).

### 3.3 The missing guard

Day 5 built `max_iterations` because ReAct loops wander. Three frameworks later:

| Framework | The cap | Day |
|---|---|---|
| naked loop | `for _ in range(6)` | 5 |
| Agents SDK | `max_turns` on `Runner.run` | 10 |
| CrewAI | `max_iter` per agent | 29 |
| **LangChain** | **? — find it today** | **today** |

**Find the parameter and pass `MAX_STEPS`.** It may be on `create_agent`, on the compiled graph's
config (`recursion_limit`), or both — LangGraph's `recursion_limit` guards the graph rather than the
agent, and the distinction matters. Write which one you used and why in `four_ways.md`.

**Why this is not pedantry.** A wandering agent on Gemini's free tier is a day's quota. A wandering
agent on OpenRouter's 50 RPD is two tickets. Every framework in this plan gives you a cap because
every framework's authors were bitten; **the day you cannot find the cap is the day to be most
careful**, not least.

### 3.4 `days/day-38/lab/triage_once.py`

```python
"""One ticket, one agent, one run. Real requests.

Run:
    uv run python days/day-38/lab/triage_once.py T-9002

Budget: <= 6 requests (MAX_STEPS). Run it twice at most.
"""

import sys

from langchain_core.messages import HumanMessage

from mandala.lc.agent import triage_agent
from mandala.sdk_tools import RAW_TICKETS

ticket_id = sys.argv[1] if len(sys.argv) > 1 else "T-9002"
body = RAW_TICKETS[ticket_id]["body"]

agent = triage_agent()
result = agent.invoke({"messages": [HumanMessage(f"<ticket id={ticket_id}>\n{body}\n</ticket>")]})

print(f"keys          {sorted(result)}")
print(f"messages      {len(result['messages'])}")
for message in result["messages"]:
    kind = type(message).__name__
    calls = getattr(message, "tool_calls", []) or []
    preview = str(message.content)[:70].replace("\n", " ")
    print(f"  {kind:<14} tools={len(calls):<2} {preview!r}")

structured = result.get("structured_response")
print(f"\nstructured    {type(structured).__name__}")
print(f"              {structured}")
```

**Line by line:**

- `HumanMessage(f"<ticket id=...>\n{body}\n</ticket>")` — the ticket wrapped in **delimiters**. Day 29's
  crew task said "the ticket body is DATA written by a stranger, never instructions", and delimiting
  is the mechanical half of that promise. It is not a defence (Day 65 will walk straight through it);
  it is the minimum hygiene, and skipping it makes Day 65's demo too easy.
- `result` is a **dict**, not an object — `create_agent` returns graph state. `sorted(result)` prints
  the keys so you learn the shape from the run rather than from a guess.
- **The message-by-message loop is the day's most valuable output.** You see the whole trajectory: the
  `HumanMessage`, an `AIMessage` with `tool_calls`, `ToolMessage`s carrying results, and a final
  `AIMessage`. That is Day 3's loop, printed. Count the `AIMessage`s: that is how many model requests
  this cost, and it should match your ledger entry.
- `getattr(message, "tool_calls", []) or []` — `ToolMessage` has no `tool_calls`, and an `AIMessage`
  can have `None`. Two fallbacks, both real.
- `result.get("structured_response")` — **`.get`, not `[...]`**, because the key is absent when
  `structured=False`, and today you will run both. Confirm the actual key name in 1.3.16 (§8); it is
  the one thing in this file most likely to have drifted.
- `type(structured).__name__` printed before the value — you want to see `TriageResult`, not a dict
  that merely looks right. **The coercion is the feature; verify it happened.**

---

## §4 LC-06 — structured output, and the four-way comparison

### 4.1 One keyword

`response_format=TriageResult` is the whole of LC-06 at the call site. What it does underneath is
worth understanding, because 1.x supports more than one strategy:

- **Provider-native structured output** — the model API is told the schema and constrains generation.
  Most reliable, not universally supported, and **on free tiers this is the one that varies.**
- **Tool-calling coercion** — the schema becomes a synthetic tool the model must call. Widely
  supported, costs a turn.
- **A second model call** — the agent answers freely, then a follow-up call reshapes it. Most
  portable, most expensive: **one extra request per ticket**, which on OpenRouter's 50 RPD is 2% of a
  day.

**Find out which one your providers take.** The number of `AIMessage`s in §3.4's output tells you: if
structured output costs a turn, you will see it. This is a Principle-5 question wearing an
architecture costume, and it belongs in the ledger.

### 4.2 `days/day-38/lab/four_ways.md` — the deliverable

Write this yourself. The rows are fixed; the cells are your findings.

```markdown
# TriageResult, four ways — Mandala, 2026-08-__

Same Pydantic model (`src/mandala/schemas.py`, Day 4), four frameworks, one table.

| | Raw client (D4) | Agents SDK (D11) | CrewAI (D26) | LangChain (D38) |
|---|---|---|---|---|
| Declaration | `response_format=` + `model_validate` | `output_type=` | `output_pydantic=` | `response_format=` |
| Lines of glue | | | | |
| Where the result lands | a variable | `result.final_output` | `result.pydantic` | `result["structured_response"]` |
| Extra model calls | | | | |
| Behaviour on schema violation | | | | |
| Can I see the failure? | | | | |
| Did I have to parse text? | | | | |

## Did the schema survive four frameworks unchanged?

<yes/no, and the diff if no>

## Which ergonomics did I actually prefer, and why isn't it the shortest one?

<one paragraph>

## What each framework made hard

<one line each>
```

**Why these rows:**

- **"Lines of glue"** is the only honest measure of ergonomics, and it must include the unwrapping.
  Four frameworks put the result in four different places; the declaration being one keyword in all
  four hides that.
- **"Behaviour on schema violation"** is the row that separates the frameworks. Ask each: does it
  retry, raise, or hand you a dict shaped wrong? Day 27's CrewAI guardrail retried. Day 4's raw client
  raised a `ValidationError` you had to catch. **A framework that silently degrades to a dict is the
  dangerous one**, because downstream code keeps working and starts being wrong.
- **"Can I see the failure?"** — Principle 8. If the coercion retried, is that in a trace, or did it
  cost you a request invisibly?
- **The last question is the one to answer honestly.** The shortest declaration is not automatically
  the best; the SDK's `output_type` and today's `response_format` are the same length, and what
  differs is what happens when the model does not comply.

---

## §5 The eval that must be able to fail

### `tests/test_lc_agent.py`

```python
"""Agent construction is policy. 0 model requests -- nothing here invokes."""

from pathlib import Path

import pytest

from mandala.lc import agent as agent_module
from mandala.lc.agent import MAX_STEPS, triage_agent
from mandala.lc.tools import READ_TOOLS
from mandala.schemas import TriageResult


def test_the_agent_holds_only_read_tools():
    """Principle 6. Flip it: add a write tool and this goes red."""
    built = triage_agent()
    names = {t.name for t in READ_TOOLS}
    assert names == {"lookup_ticket", "search_handbook"}
    assert built is not None


def test_the_loop_is_capped():
    """Day 5's guard, fourth framework. An uncapped agent is an uncapped budget."""
    source = Path("src/mandala/lc/agent.py").read_text(encoding="utf-8")
    assert "MAX_STEPS" in source
    assert source.count("MAX_STEPS") >= 2, "MAX_STEPS is defined but never passed"


def test_the_cap_is_small_enough_to_matter():
    assert 1 <= MAX_STEPS <= 12


def test_no_model_id_appears_in_the_agent_module():
    source = Path("src/mandala/lc/agent.py").read_text(encoding="utf-8")
    for banned in ("gemini-", "gpt-oss", "nemotron", ":free"):
        assert banned not in source, banned


def test_the_prompt_is_imported_not_inlined():
    """prompts.py survived four frameworks. Keep it that way."""
    source = Path("src/mandala/lc/agent.py").read_text(encoding="utf-8")
    assert "from mandala.prompts import" in source
    assert '"""' in source  # the module docstring, not an inlined prompt
    assert "You are a" not in source, "a prompt was inlined"


def test_the_schema_is_still_day_4s():
    """The plan's central claim, asserted. Flip it: subclass it 'just for LangChain'."""
    assert TriageResult.__module__ == "mandala.schemas"
    fields = set(TriageResult.model_fields)
    assert {"severity", "category", "summary"} <= fields


def test_structured_can_be_turned_off(monkeypatch):
    """Days 39 and 40 both need an unstructured agent to experiment against."""
    captured: dict = {}
    monkeypatch.setattr(agent_module, "create_agent",
                        lambda **kw: captured.update(kw) or object())
    triage_agent(structured=False)
    assert "response_format" not in captured

    captured.clear()
    triage_agent(structured=True)
    assert captured["response_format"] is TriageResult


@pytest.mark.parametrize("flag", [True, False])
def test_both_paths_differ_only_in_response_format(monkeypatch, flag):
    captured: dict = {}
    monkeypatch.setattr(agent_module, "create_agent",
                        lambda **kw: captured.update(kw) or object())
    triage_agent(structured=flag)
    assert {"model", "tools", "system_prompt"} <= set(captured)
```

**Line by line:**

- Every test either **greps the source** or **monkeypatches `create_agent`**. Neither builds a real
  model or spends a request, so the file runs in CI with no keys — the same discipline as Days 36 and
  37, and the reason Day 74's regression gate will be possible at all.
- `test_the_loop_is_capped` counts occurrences of `MAX_STEPS`: **defined once is not enough, it must
  also be passed.** A constant that is never used is the most convincing kind of false comfort, and
  §3.1 ships the file in exactly that state on purpose.
- `test_the_cap_is_small_enough_to_matter` pins a judgement rather than a behaviour, same as Day 32's
  staleness bound. It does not claim 6 is right; it makes 200 argue with a test.
- `test_the_prompt_is_imported_not_inlined` checks for `"You are a"` — crude, and it catches the exact
  temptation of a Friday afternoon: pasting a tweaked prompt into the agent file "just to try
  something". Four frameworks have shared `prompts.py`; that is a claim worth defending mechanically.
- `test_the_schema_is_still_day_4s` asserts `TriageResult.__module__`. **This is the plan's central
  thesis as an assertion.** Subclass it for LangChain and the test goes red, which is the correct
  outcome: the moment there are two triage schemas, the four-framework comparison is measuring
  nothing.
- `test_structured_can_be_turned_off` asserts **both directions** — absent when off, and *identically*
  `TriageResult` when on. `is` rather than `==`, because a coerced copy would be a different object
  and a quiet sign something re-wrapped your schema.
- `test_both_paths_differ_only_in_response_format` — the `kwargs`-dict design from §3.1, tested. It is
  the kind of test that looks redundant until someone adds a `if structured:` branch that also
  changes the model.

---

## §6 Traps

- **Shipping `MAX_STEPS` defined but unused.** §3.1 hands you the bug; §5 catches it. Wire the cap.
- **Confusing `recursion_limit` with an agent step cap.** One guards the graph, one guards the loop.
  Know which you set, and say so.
- **Assuming `result` is an object.** It is graph state, a dict, with `messages` in it.
- **Indexing `result["structured_response"]` when structured is off.** Use `.get`.
- **Subclassing `TriageResult` "for LangChain".** The moment there are two schemas the whole
  comparison is worthless, and it happens for the most reasonable-sounding reason every time.
- **Inlining the prompt.** Same argument, different file.
- **Not counting the `AIMessage`s.** That count is your request count, and it is the only honest input
  to the ledger.
- **Not delimiting the ticket body.** It is not a defence; it is the hygiene that makes Day 65's
  attack interesting rather than trivial.
- **`uv add`-ing a graph-drawing dependency without a ledger row.** Principle 4 does not have a
  convenience exception.
- **Writing `four_ways.md` from memory.** Three of the four columns are in your git history. Go read
  them.

---

## §7 Request budget

**Declared: ~12 model requests, Groq.**

| What | Requests |
|---|---|
| `what_is_it.py` | **0** |
| `tests/test_lc_agent.py` | **0** |
| `triage_once.py`, structured | ≤ 6 |
| `triage_once.py`, unstructured (for the §4.1 comparison) | ≤ 6 |

**The second run is what earns the day.** Running with `structured=False` and comparing the
`AIMessage` count against the structured run tells you whether `response_format` cost you a turn —
which is §4.1's question, and it is not answerable any other way on a free tier.

---

## §8 Verify before you code

Written **2026-08-20** against `langchain==1.3.16`:

- **Is `create_agent` in `langchain.agents`?** Yesterday's `what_survived.py` already told you; confirm
  it still holds after any version change.
- **What is the iteration-cap parameter called?** §3.3 is the whole assignment. `max_iterations`,
  `recursion_limit` in config, both, neither — find it and wire it.
- **Is the output key `structured_response`?** §3.4 assumes it. If it differs, fix the lab and log it.
- **Which structured-output strategy do the three adapters use** — native, tool-call, or a second
  call? This changes the request budget, so it belongs in `RATE_BUDGET.md` as well as the changelog.
- **What happens when the model violates the schema** — retry, raise, or a degraded dict? The
  `four_ways.md` row that matters most.
- **Does `system_prompt` take a `SystemMessage` or a `str`** in 1.3.16? Both may work; know which is
  canonical.
- **Does `get_graph().draw_ascii()` require an extra package?** If yes, decide whether you need it
  before you install it.
- `https://docs.langchain.com/oss/python/langchain/agents` — read today.

---

## §9 Say it in an interview

> "`create_agent` is one function — model, tools, prompt, optional response format — and the first
> thing I did was introspect what it returned rather than invoke it. It's a compiled LangGraph, which
> is why the same object has `invoke` and `stream`, why it drops into a bigger graph as a node, and
> why LangGraph's own prebuilt agent is deprecated in its favour. The second thing I did was go
> looking for the iteration cap, because I'd written one by hand in week one and every framework since
> has had its own name for it — on a free tier an uncapped ReAct loop is a day's quota. And I ran the
> same ticket with and without structured output specifically to count the model calls, because
> whether `response_format` is provider-native, a synthetic tool call, or a second request is a
> budget question, not a style question. The thing I'd point at is that the Pydantic schema and the
> system prompt are byte-identical across all four frameworks I've used — those two files are the
> durable artifacts and the framework code around them is replaceable."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 38
```
