---
day: 61
phase: 9
phase_name: "The bake-off"
title: "Bake-off III — the slice on LangChain"
ids: []
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 61 — Bake-off III: the slice, on LangChain

**Phase 9 · The bake-off 🥇** · IDs: none — the slice is the artifact

> **Yesterday:** CrewAI, a `@router` that costs nothing, and rule 6 by deletion.
> **Today:** LangChain. The framework whose answer is *"the abstraction owns the loop"* — one
> `create_agent`, one interface, any provider. Two hours, same tests, same server. The question that
> makes today interesting: **where does branching live when the framework has no branching
> primitive?**
> **Tomorrow:** LangGraph, and the last of the four.

```bash
./m start 61
./m scaffold 61
```

---

## §1 The story

Rules unchanged. Third build day, and by now the routine should be quick: server up, counting wired,
timer started, log open.

Today's genuine question is structural. **Rule 3 requires a branch, and LangChain's blessed API is
`create_agent`, which is a loop — not a graph.** So where does the branch go? Three honest options,
and choosing among them *is* today's finding:

| Option | Where the branch lives | What it says about the framework |
|---|---|---|
| **Plain Python** around two agents | your code | the framework is a component, not a controller |
| **Middleware** (`LC-07`) intercepting after the model | inside the loop | branching by interception |
| **`create_agent` returns a graph** → wire it | LangGraph | **the framework's answer is another framework** |

**That third row is the most interesting sentence in Phase 9**, and Day 42 already made you build it
(LC-13, the seam). Taking it today would be legitimate — it is the framework's own documented answer.
**It would also make today's implementation indistinguishable from tomorrow's**, which is exactly what
a comparison must not do.

**So: build it option 1, with plain Python around `create_agent` calls, and record loudly that option
3 exists and that you declined it for methodological reasons.** That note is worth more than the code
— it says something true about LangChain that a feature list will not: *for anything with control
flow, LangChain's answer is LangGraph.*

**Then honour it in the scorecard.** "Needs a second library for branching" is a real property. It is
not a criticism — LangGraph is the same product — but it belongs in the lock-in row, because adopting
LangChain for an agent with any branching means adopting both.

---

## §2 The build

### 2.1 What you already have

- `src/mandala/lc/` — chat factory, schema-first tools, `create_agent`, middleware, streaming
  (Days 36–42)
- The MCP mount via `langchain_mcp_adapters` (Day 55)
- `MIDDLEWARE` with the PII scrubber first (Day 39)

### 2.2 `src/mandala/bakeoff/lc_slice.py`

```python
"""The slice, on LangChain. Two hours, hard stop. Same contract.

METHODOLOGICAL NOTE, and it is the point of today:
    LangChain's own answer to rule 3's branch is "create_agent returns a graph --
    put it in a StateGraph" (LC-13, Day 42). That is legitimate and it is what I
    would ship. It would also make this implementation identical to tomorrow's,
    which would measure nothing.

    So: plain Python around create_agent calls, and the fact that I had to decline
    the framework's own answer is recorded as a FINDING rather than hidden as a
    workaround.

Shape:
    triage_agent  = create_agent(tools=[mcp get_ticket], response_format=TriageResult)
    if critical -> escalate                 <- a plain `if`. Zero model turns.
    research_agent = create_agent(tools=[mcp search_handbook])
    draft_agent    = create_agent(tools=[])  <- NO tools, and a fresh message list

Rule 6 (the drafter never sees the raw body) falls out of the shape here, and that
is genuinely notable: three separate create_agent calls means three separate message
lists, so the drafter's context contains ONLY what I pass it. Not deletion (D30),
not a reducer (D43), not a subgraph schema (D48) -- just a new conversation.
Time it. It may be the fastest of the four.
"""

from __future__ import annotations

from tests.test_bakeoff import SliceResult


def run_slice(ticket_id: str) -> SliceResult:
    ...
```

**Line by line — the two design notes are today's content:**

- **The methodological note is not padding.** A bake-off where one implementation quietly becomes
  another is worthless, and the *reason* you had to decline the framework's own answer is a finding
  about the framework. Write it in the module, not just in your notes.
- **Rule 6 by fresh conversations** is the interesting result. Three `create_agent` calls means three
  message lists; the drafter is constructed with no tools and invoked with only the findings, so the
  raw body was never in its context. **No deletion, no reducer, no schema — an absence by
  construction.**
- **Time it against Days 59 and 60**, because there is a real possibility that the framework with the
  least machinery expresses the security requirement most cheaply. **If that is what you find, say
  so**, even though it complicates the story you expected to tell. That is what §2.4 of Day 59's
  guard was for.
- `draft_agent = create_agent(tools=[])` — **no tools at all.** A drafter with a `get_ticket` tool
  could fetch the body itself, and then the fresh-conversation guarantee is worthless. **The tool list
  is part of the security boundary**, which is Day 8's separation rule and Day 12's `permissions.py`
  arriving in the smallest possible form: an empty list.

### 2.3 Where the timebox will go

1. **The provider abstraction is a non-issue and that is a result.** Day 36's factory means
   `fast_loop()` and you are done. **Record zero minutes here** — three days in, this is the first
   framework where model wiring cost nothing, and a zero is a data point.
2. **Middleware ordering.** Your `MIDDLEWARE` list has the scrubber first (Day 39 §3.4). If you attach
   it to all three agents, it runs on all three — which is correct, and worth a line: **the scrubber
   is per-agent, so three agents means remembering three times.** Did you? A framework that makes you
   remember something three times will eventually catch you.
3. **Getting `SliceResult` out.** `create_agent` with `response_format` gives you a real
   `TriageResult` (Day 38), so the triage step needs no parsing. **The draft step will**, unless you
   give it a response format too. **Count the parsing lines and compare with yesterday's crew
   parser** — that is the "typed in, prose out" row, now with three data points.

### 2.4 The counting question

**Model calls are harder to count here than anywhere else**, and that is worth recording.

Yesterday CrewAI had callbacks; Day 38 established that counting `AIMessage`s in the result works for
one agent. **With three separate agents you must sum three results**, and the middleware may add calls
you did not initiate (Day 39 §4.1: summarization middleware makes its own model call).

**Wire the counting before the timer**, and then answer the question that matters: **could you have
been surprised?** A framework where an attached middleware can silently spend a request is a framework
where your ledger can be wrong without you noticing. **That is a free-tier scorecard row and today is
the day you can fill it in.**

---

## §3 What to compare, today

| Question | SDK (59) | CrewAI (60) | LangChain (61) |
|---|---|---|---|
| Model turns for the routing decision | 1 | 0 | **0** (a plain `if`) |
| How rule 6 is expressed | separate context | deletion | **a fresh conversation** |
| Minutes until you trusted rule 6 | | | |
| Lines of output parsing | | | |
| Minutes on model wiring | | | **expect 0** |
| Could a hidden call inflate my count? | | | |
| Escape hatches reached for | | | |
| **Needed a second library for control flow** | no | no | **yes — declined, and recorded** |

**The last row is unique to today** and it is the one to be careful about phrasing. LangChain and
LangGraph are one product; "needed a second library" is accurate and slightly unfair. **Write it
precisely:** *"for a workflow with a branch, LangChain's documented answer is to use LangGraph."*
Precision here is what keeps the scorecard from reading as advocacy.

---

## §4 Traps

- **Taking option 3** and building a graph. Today becomes tomorrow and you have measured nothing.
- **Hiding the declined option as a workaround.** It is the finding.
- **Giving the drafter tools.** The fresh-conversation guarantee dies the moment it can fetch.
- **Forgetting the middleware on one of the three agents.** And not noticing that you had to remember
  three times.
- **Not recording the zero.** Zero minutes on model wiring is a result, not an absence of one.
- **Estimating the model calls** when middleware might be adding them.
- **Phrasing the lock-in row as a criticism.** Write what is true and let Day 63 weigh it.
- **Assuming rule 6 was harder here** because the framework is simpler. It may be the cheapest of the
  four — measure before you conclude.

---

## §5 Request budget

**Declared: ~14 model requests, Groq.**

| What | Requests |
|---|---|
| Acceptance tests against a recorded result | **0** |
| Iterating during the timebox | ~8 |
| Three final runs (normal, critical, unclassifiable) | ~14 |

**Three agents means three loops**, but each is short — the branch costs nothing and there is no crew.
Expect this to land **below** yesterday's CrewAI number and above tomorrow's, and if it does not,
**that is worth investigating rather than accepting**: an unexpected request count usually means
something is running that you did not intend, which is exactly §2.4's question.

---

## §6 Verify before you code

- **`ticket-db` running**, and `langchain_mcp_adapters` still connecting after Phase 8.
- **`langchain==1.3.16` / `langchain-core==1.6.0`** still pinned and installed.
- **Model-call counting across three agents**, wired **before** the timer.
- **Does your `MIDDLEWARE` list add any model calls?** Check before you count.
- **`response_format` on the drafting agent** — available, and does it cost an extra turn (Day 38
  §4.1's open question)? If it does, that is a request-budget fact for the ledger.

---

## §7 Say it in an interview

> "LangChain's blessed API is a single agent loop, so the branching requirement had nowhere natural to
> go — and the framework's own documented answer is 'create_agent returns a graph, put it in a
> StateGraph', which is LangGraph. I declined that deliberately, because taking it would have made
> this implementation identical to the next one and measured nothing, and I recorded the decline as a
> finding rather than hiding it as a workaround: for a workflow with a branch, LangChain's answer is
> another library. The result that surprised me was the security requirement. Three separate
> `create_agent` calls means three separate message lists, so keeping raw customer text away from the
> drafting step wasn't deletion or a reducer or a state schema — it was just a new conversation, plus
> an empty tool list so the drafter couldn't fetch the ticket itself. That may have been the cheapest
> expression of that requirement across all four frameworks, which complicates the story I expected to
> tell, and that's precisely why I wrote my predictions down first."

---

## §8 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 61
```
