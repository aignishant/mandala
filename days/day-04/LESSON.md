---
day: 4
phase: 1
phase_name: "Agents from first principles"
title: "Shapes and budgets — structured output and the context window"
ids: ["AG-03", "AG-04"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 4 — Shapes and budgets

**Phase 1 · Agents from first principles** · IDs: **AG-03 🛠️**, **AG-04 🛠️**

> **Yesterday:** a working loop — the model asks, your code answers.
> **Today:** two disciplines that make that loop usable by *other code*: forcing the output into a
> shape you can trust, and treating the context window as a budget you spend deliberately.
> **Tomorrow:** ReAct, and the day the loop starts wandering.

---

## §1 The story

Yesterday's agent answered in English. That is lovely for a human and useless for a program.

Picture Mandala's real pipeline. Triage decides a ticket is severe; the router reads that decision
and sends it down the fast lane or the deep-research lane. What does the router receive?

> *"This looks fairly serious to me — I'd probably call it high priority, though it could arguably be
> a medium depending on how many users are affected."*

You cannot branch on that. You could try to parse it — search for the word "high" — and you would
be building a system that fails the day the model says "elevated" instead. Prose output means every
downstream consumer becomes a fragile little parser. That is the first half of today: **make the
model return a shape** (AG-03).

The second half is quieter and, in the long run, more expensive to get wrong.

Everything the model knows in a given turn has to fit through one door: the context window. Your
system prompt, the whole conversation so far, every tool result, the tool schemas — all of it, resent
on every single call, because the model is stateless. It is not a memory. It is a **desk**. A big
desk, but finite. And the discipline of deciding *what earns a place on the desk* has a name:
**context engineering** (AG-04).

Here is the sentence from the plan that says it best: *200 tickets don't fit; a retrieved top-5
does.* Everything you will build on Day 46 (RAG), Day 39 (summarisation middleware) and Day 76
(context pruning) is an answer to that one line.

---

## §2 AG-03 — Structured output

### The plain idea

You give the model a schema — a JSON Schema, or a Pydantic model that generates one — and require
that its answer conform. Downstream code then gets an object with known fields and known types,
instead of a paragraph it has to interpret.

There are three ways to get one, and knowing which you're using matters:

| Technique | How | Reliability |
|---|---|---|
| **Ask nicely in the prompt** | "reply as JSON with keys severity, category…" | Poor. Works until it doesn't, usually mid-demo. |
| **Provider-native structured output** | pass `response_format` with a JSON Schema | Good, where supported |
| **Tool-call as the schema** | define one tool whose *arguments* are your schema; the call is the answer | Good, and works nearly everywhere |

That third one is a genuinely useful trick and it deserves a moment. You already learned yesterday
that tool calls arrive as structured, schema-validated arguments. So: define a tool called
`submit_triage` whose parameters are exactly `{severity, category, summary}`. Tell the model that
submitting is how it finishes. Now the model's *answer* arrives through the same validated channel
its *tool requests* do. No new machinery — you're reusing yesterday's.

This matters for a $0 project specifically: **provider support for native structured output varies
across free tiers.** The tool-call route works on essentially anything that supports function
calling, so it is the portable one.

### Why Mandala needs it

`TriageResult` is the single most reused object in these 90 days. Look at the plan's repetition map:
you will build this exact schema in the Agents SDK (Day 11), CrewAI (Day 26), LangChain (Day 38), and
as LangGraph state (Day 43). Four frameworks, one contract. Defining it well today pays four times.

```python
# src/mandala/schemas.py — write this once; it lives for 87 more days.
from typing import Literal
from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high", "critical"]
Category = Literal["auth", "billing", "data", "howto", "other"]

class TriageResult(BaseModel):
    ticket_id: str = Field(description="The id of the ticket triaged, e.g. 'T-1001'.")
    severity: Severity = Field(description="How urgent. 'critical' means active data loss or outage.")
    category: Category = Field(description="Best single fit. Use 'other' rather than guessing.")
    summary: str = Field(max_length=200, description="One sentence a human on-call would want.")
    confidence: float = Field(ge=0.0, le=1.0, description="0-1. Below 0.5 means escalate to a human.")
```

Three deliberate design choices in there, each worth stealing:

- **`Literal` instead of `str`** for severity and category. This turns "the model said `HIGH`" and
  "the model said `urgent`" from silent downstream bugs into a loud validation error at the boundary.
- **Every field has a `description`.** Those descriptions go into the schema the model sees. They are
  prompt, exactly like tool descriptions were yesterday. An undescribed field is a field the model
  will fill in by vibe.
- **`confidence`.** This is the field people skip, and it is the one that makes graduated autonomy
  possible on Day 84. An agent that can say "I'm not sure" can be trusted with more, because you can
  route the unsure cases to a human. Build the affordance now, use it in twelve weeks.

### Watch it break

1. **Send a ticket that is genuinely ambiguous** (you put one in the golden set on Day 2, on purpose).
   Watch the `confidence` value. If your prompt never mentions confidence, the model will report 0.9
   for everything — models are, by default, cheerfully overconfident. Fixing that is a prompt problem.
2. **Add a category to the `Literal` and don't tell the prompt.** It still works — the schema is
   enough. Now *remove* one the model likes using. Watch the validation error. That error is your
   friend: it is the boundary doing its job.
3. **Ask for JSON in the prompt only** (no schema enforcement) and run it twenty times. Count how
   many are malformed. This is the number that convinces people to stop asking nicely.

### Say it in an interview

> "Anywhere an agent's output crosses into ordinary code, I put a schema on the boundary — usually
> Pydantic with `Literal` types for the enumerated fields, so a drifted label fails loudly instead of
> flowing downstream. And I always include a confidence field, because that's what lets you route
> low-confidence cases to a human instead of trusting everything equally."

---

## §3 AG-04 — The context window as a budget

### The plain idea

Every call resends everything. So the cost and the reliability of your agent are both functions of
what you choose to include.

Four things compete for the desk:

1. **System prompt** — small, constant, high value.
2. **Tool schemas** — sent on *every* call. Ten verbose tools can quietly cost more than the
   conversation.
3. **Conversation history** — grows with every turn. This is the one that explodes.
4. **Tool results** — the sneaky one. A tool that returns a 200-line JSON blob has just spent your
   budget on a payload the model needed three fields of.

The instinct is "the window is 1M tokens, I'm fine". Two reasons that's wrong even when true.
**First**, free tiers meter tokens per minute, so a fat prompt is a rate-limit event, not just a
slow one. **Second** — and this is the part that surprises people — **more context often makes the
answer worse.** A model given fifty tickets and asked about one will drift toward the wrong one.
Relevance beats volume. The plan's line again: *200 tickets don't fit; a retrieved top-5 does* — and
the top-5 version is not merely cheaper, it is *more accurate*.

### The four levers, in the order you should reach for them

| Lever | What it does | You'll meet it again on |
|---|---|---|
| **Trim the tool result** | return 3 fields, not 30 | today |
| **Cap the history** | keep the last N turns | Day 7 (sessions) |
| **Summarise the middle** | compress old turns into a paragraph | Day 39 (LangChain summarisation middleware) |
| **Retrieve instead of stuff** | fetch only what's relevant | Day 46 (the honest RAG day) |

Reach for them in that order. Most people jump straight to retrieval when a `select` of three fields
would have solved it. The cheapest context engineering is *not putting it in*.

### Why Mandala needs it

Because a real ticket thread has forty messages and the golden-set ones have one. Every agent you
build in these 90 days will look fine on the fixtures and fall over on realistic volume unless you
build the measuring habit today.

### The smallest thing that works — measure before you optimise

```python
# src/mandala/budget.py
from dataclasses import dataclass, field

@dataclass
class ContextBudget:
    """Counts what you're actually sending. Wire it into the Day-3 loop."""
    limit: int
    spent: dict[str, int] = field(default_factory=dict)

    def charge(self, bucket: str, text: str) -> None:
        self.spent[bucket] = self.spent.get(bucket, 0) + self.estimate(text)

    @staticmethod
    def estimate(text: str) -> int:
        # Deliberately approximate: ~4 chars per token. Good enough to make decisions.
        # Exact counting is provider-specific and not worth a dependency today.
        return len(text) // 4

    def report(self) -> str:
        total = sum(self.spent.values())
        rows = "\n".join(f"  {k:<18} {v:>6}  {v/max(total,1):>5.0%}"
                         for k, v in sorted(self.spent.items(), key=lambda kv: -kv[1]))
        return f"context: {total}/{self.limit} tokens ({total/self.limit:.0%})\n{rows}"
```

Print that report after every run today. The moment you *see* that tool results are 70% of your
prompt, the fix becomes obvious, and you will never again guess at where the budget went.

### Watch it break

Take a golden-set ticket and duplicate its body twenty times to make a long one. Run yesterday's
loop. Watch two things: the token report climb, and — more interestingly — the answer quality drop.
Then trim the tool result to only `{id, severity, category}` and watch both recover.

That single experiment is the entire argument for context engineering, and you will be able to
describe it from memory in an interview because you did it.

### Say it in an interview

> "I treat the context window as a budget with four line items: system prompt, tool schemas, history,
> and tool results. Tool results are usually the surprise — people return whole rows when the model
> needs three fields. I instrument it first, because everyone guesses wrong about where their tokens
> are going. And I've measured that trimming context often *improves* accuracy, not just cost."

---

## §4 Build brief

```
src/mandala/
  schemas.py     # TODO(me): TriageResult with Literal types, descriptions, confidence
  budget.py      # TODO(me): ContextBudget — charge() + report()
  loop.py        # TODO(me): extend Day 3's loop with an optional `output_schema=`
                 #           and wire ContextBudget into every call

days/day-04/lab/
  triage_naked.py  # TODO(me): triage one ticket, return a validated TriageResult
  compare.py       # runs all three techniques from §2's table on the same 10 tickets
                   # and prints a table: technique | valid | invalid | mean tokens
  fat_context.py   # the "watch it break" experiment from §3
```

`compare.py` is the day's real artifact. Ten tickets × three techniques = thirty calls, and at the
end you have **your own measured evidence** for why schema enforcement beats asking nicely. That
table goes in your notes and comes out again in an interview.

---

## §5 The eval that must be able to fail

```python
# tests/test_triage_schema.py
import pytest
from pydantic import ValidationError
from mandala.schemas import TriageResult

def test_bad_severity_is_rejected():
    """A drifted label must fail at the boundary, not flow downstream."""
    with pytest.raises(ValidationError):
        TriageResult(ticket_id="T-1", severity="URGENT", category="auth",
                     summary="x", confidence=0.9)

def test_confidence_is_bounded():
    with pytest.raises(ValidationError):
        TriageResult(ticket_id="T-1", severity="high", category="auth",
                     summary="x", confidence=1.4)

@pytest.mark.cassette
def test_triage_returns_valid_object_for_every_golden_ticket(golden_tickets, cassette):
    """All 10. Not 'usually'. The point of a schema is that it always holds."""
    for ticket in golden_tickets:
        result = triage(ticket)                 # must not raise
        assert isinstance(result, TriageResult)

@pytest.mark.cassette
def test_ambiguous_ticket_reports_low_confidence(cassette):
    """T-100X is genuinely ambiguous. An honest agent says so."""
    result = triage(AMBIGUOUS_TICKET)
    assert result.confidence < 0.7, "model is overconfident on a case humans disagree about"
```

That last test is the one that will be **red for a while**, and it should be. Making a model
appropriately unsure is a prompt-engineering problem: you have to describe what low confidence
*means* and give an example. This is the honest introduction to calibration, which returns in force
on Day 72 (LLM-as-judge).

---

## §6 Request budget

| Activity | Requests |
|---|---|
| `compare.py`: 10 tickets × 3 techniques | 30 (Groq) |
| Getting `triage_naked.py` right | ~15 (Groq) |
| The fat-context experiment | ~6 (Groq) |
| Confidence-calibration prompt iterations | ~15 (Groq) |
| Cassettes | ~12 |
| **Total** | **≈ 80, all Groq** |

Eighty is a big day by this plan's standards. Groq's request-per-day allowance handles it; Gemini's
would not comfortably. **This is why you have three providers.** Log actual usage in
`docs/RATE_BUDGET.md`.

---

## §7 Traps

- **`str` where you meant `Literal`.** The most common structured-output bug: everything validates,
  nothing is checked, and "High" vs "high" breaks a router two weeks later.
- **Fields with no description.** The model sees the schema. An undescribed field is an unprompted
  field.
- **Validating and then ignoring.** If `ValidationError` is caught and logged, you have a schema
  that documents rather than enforces. Let it raise, or retry — one or the other, deliberately.
- **`max_length` on `summary` that the model keeps violating.** Two fixes: say the limit in the
  description too, and truncate-with-retry rather than crash. Schema constraints are not
  self-enforcing on the model side — they are *checks*, and checks need a response plan.
- **Optimising context before measuring it.** Build `ContextBudget` first. Every time.
- **Assuming your free-tier model supports `response_format`.** Check. If it doesn't, use the
  tool-call technique — that's why it's in the table.

---

## §8 Verify before you code

Written **2026-08-20** against `openai` **3.3.1** and Pydantic v2.

- `https://platform.openai.com/docs/guides/structured-outputs` — the `response_format` shape and its
  schema restrictions (no `anyOf` at root, all fields required, etc. — these bite).
- `https://console.groq.com/docs/structured-outputs` — **which** Groq models support it. Not all do.
- `https://ai.google.dev/gemini-api/docs/structured-output` — Gemini's response-schema form differs
  from OpenAI's; if you use Gemini today, read this.
- `https://docs.pydantic.dev/latest/concepts/json_schema/` — `model_json_schema()` output, which is
  what you hand to the provider.

---

## §9 Done when

See `CHECKLIST.md`. Tomorrow: the loop gets ambitious, starts wandering, and you learn why every
serious agent framework eventually reinvents the graph.
