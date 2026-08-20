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
> **Today:** two disciplines that make that loop usable by *other code* — forcing the output into a
> shape you can trust, and treating the context window as a budget you spend on purpose.
> **Tomorrow:** ReAct, and the day the loop starts wandering.

```bash
./m start 4
./m scaffold 4
```

---

## §1 The story

Yesterday's agent answered in English. Lovely for a human, useless for a program.

Picture Mandala's real pipeline. Triage decides a ticket is severe; a router reads that decision and
sends it down the fast lane or the deep-research lane. What does the router receive?

> *"This looks fairly serious to me — I'd probably call it high priority, though it could arguably
> be a medium depending on how many users are affected."*

You cannot branch on that. You could try to parse it — search for the word "high" — and you would be
building a system that fails the day the model says "elevated". Prose output means every downstream
consumer becomes a fragile little parser. That is the first half of today: **make the model return a
shape** (AG-03).

The second half is quieter and, long-term, more expensive to get wrong.

Everything the model knows in a given turn goes through one door: the context window. Your system
prompt, the whole conversation so far, every tool result, all the tool schemas — resent on **every
single call**, because the model is stateless. It is not a memory. It is a **desk**. A big desk, but
finite. The discipline of deciding what earns a place on the desk has a name: **context engineering**
(AG-04).

The plan says it best: *200 tickets don't fit; a retrieved top-5 does.* Everything you build on Day 46
(RAG), Day 39 (summarisation middleware) and Day 76 (context pruning) is an answer to that one line.

---

## §2 Setup — run this

```bash
uv add "pydantic==2.13.4"
```

- `uv add "pydantic==2.13.4"` — the data-validation library. It turns a Python class into a JSON
  Schema *and* validates incoming data against it. You need both halves today: the schema goes to
  the model, the validation catches what comes back.
- Pydantic v2 is already an indirect dependency (the `openai` client uses it), but you now depend on
  it **directly**, so it must be declared directly. An undeclared dependency that happens to be
  installed is a bug waiting for the day the other package drops it.

```bash
mkdir -p days/day-04/lab
touch src/mandala/schemas.py
touch src/mandala/budget.py
touch days/day-04/lab/triage_naked.py
touch days/day-04/lab/compare.py
touch days/day-04/lab/fat_context.py
touch tests/test_triage_schema.py
```

---

## §3 AG-03 — Structured output

### The plain idea

You give the model a schema and require its answer to conform. Downstream code then receives an
object with known fields and known types instead of a paragraph it must interpret.

There are three ways to get one, and knowing which you are using matters:

| Technique | How | Reliability |
|---|---|---|
| **Ask nicely in the prompt** | "reply as JSON with keys severity, category…" | Poor. Works until it doesn't, usually mid-demo. |
| **Provider-native structured output** | pass `response_format` with a JSON Schema | Good, *where supported* |
| **Tool-call as the schema** | define one tool whose *arguments* are your schema; the call **is** the answer | Good, and works nearly everywhere |

That third one deserves a moment. You already learned yesterday that tool calls arrive as structured,
schema-validated arguments. So: define a tool called `submit_triage` whose parameters are exactly
`{ticket_id, severity, category, summary, confidence}`, and tell the model that submitting is how it
finishes. Now the model's *answer* arrives through the same validated channel its *tool requests* do.
No new machinery — you are reusing yesterday's.

This matters for a $0 project specifically: **provider support for native structured output varies
across free tiers.** The tool-call route works on anything that supports function calling, so it is
the portable one.

### 3.1 `src/mandala/schemas.py`

Write this once; it lives for 86 more days.

```python
"""The contracts between Mandala's agents and ordinary code.

TriageResult is the single most reused object in this curriculum. You will build
it again in the Agents SDK (Day 11), CrewAI (Day 26), LangChain (Day 38) and as
LangGraph state (Day 43). Four frameworks, one contract.

Usage
-----
    >>> from mandala.schemas import TriageResult
    >>> r = TriageResult(ticket_id="T-1001", severity="high", category="auth",
    ...                  summary="SSO login loop affecting ~40 users", confidence=0.82)
    >>> r.needs_human_review()
    False
    >>> TriageResult.model_json_schema()["properties"]["severity"]["enum"]
    ['low', 'medium', 'high', 'critical']
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high", "critical"]
Category = Literal["auth", "billing", "data", "howto", "other"]

CONFIDENCE_FLOOR = 0.5


class TriageResult(BaseModel):
    """What Triage promises to return. Nothing downstream may assume more than this."""

    ticket_id: str = Field(
        description="The id of the ticket being triaged, e.g. 'T-1001'. Copy it exactly.",
    )
    severity: Severity = Field(
        description=(
            "How urgent this is. Use 'critical' only for active data loss, a security "
            "exposure, or a full outage. Use 'low' for cosmetic issues and questions."
        ),
    )
    category: Category = Field(
        description="Best single fit. Prefer 'other' over guessing between two poor fits.",
    )
    summary: str = Field(
        max_length=200,
        description="One sentence an on-call engineer would want to read first. No preamble.",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "How sure you are, 0 to 1. Report below 0.5 when the ticket is ambiguous, "
            "contains too little information, or two categories fit equally well. "
            "Reporting high confidence on a vague ticket is an error."
        ),
    )

    def needs_human_review(self) -> bool:
        """Day-84's graduated-autonomy rule starts here."""
        return self.confidence < CONFIDENCE_FLOOR or self.severity == "critical"
```

**Line by line:**

- `from typing import Literal` — `Literal["a", "b"]` is a type meaning "exactly one of these
  strings". It is the single most useful typing tool in this whole project.
- `from pydantic import BaseModel, Field` — `BaseModel` is the base class that gives you validation
  and JSON-Schema generation; `Field` attaches metadata to individual fields.
- `Severity = Literal[...]` at module level — a **named type alias**. Now `Severity` can be imported
  by other modules, so Day 26's CrewAI version and Day 43's LangGraph state use the *same* four
  strings, not four strings that happen to look alike.
- **`Literal` instead of `str`** — this is the most important design choice in the file. With `str`,
  the model returning `"HIGH"` or `"urgent"` validates fine and breaks a router two weeks later.
  With `Literal`, it fails **at the boundary**, loudly, with a message naming the bad value.
- `CONFIDENCE_FLOOR = 0.5` — a named constant rather than a bare `0.5` scattered through the code.
  On Day 84 you will tune this number, and you want exactly one place to tune.
- `class TriageResult(BaseModel):` — subclassing `BaseModel` is what turns a plain class into a
  validating one.
- `ticket_id: str = Field(description=...)` — **every field has a description, and the descriptions
  are prompts.** They go into the JSON Schema the model sees. An undescribed field is an unprompted
  field, and the model fills it by vibe.
- The `severity` description says *when* to use `critical` — a rule, not a label. Compare
  "how urgent" (useless) with "only for active data loss, security exposure, or full outage"
  (actionable). Schema descriptions are where you put judgement criteria.
- The `category` description says *"prefer 'other' over guessing"* — giving the model an explicit
  escape hatch is how you stop it forcing bad fits.
- `max_length=200` on `summary` — a validation constraint. **Note it is a *check*, not a muzzle:**
  the model can still produce 300 characters, and then Pydantic raises. So the limit is also stated
  in the description, and §6 covers what to do when it is violated anyway.
- `ge=0.0, le=1.0` — greater-or-equal / less-or-equal. Bounds on the float.
- The `confidence` description is three sentences long on purpose. **`confidence` is the field people
  skip, and it is the one that makes graduated autonomy possible on Day 84.** An agent that can say
  "I'm not sure" can be trusted with more, because you can route the unsure cases to a human. Models
  are cheerfully overconfident by default; the only fix is to describe, concretely, what low
  confidence looks like.
- `def needs_human_review(self)` — **behaviour on the schema, not just data.** The rule "escalate if
  unsure or if critical" lives with the contract it depends on, so every framework's version
  inherits the same policy for free.
- `TriageResult.model_json_schema()` (in the docstring) — the Pydantic v2 method that emits JSON
  Schema. That output is literally what you hand the provider.

### 3.2 `days/day-04/lab/triage_naked.py`

```python
"""Triage one ticket into a validated TriageResult, three different ways.

Run:
    uv run python days/day-04/lab/triage_naked.py T-1001 tool
    uv run python days/day-04/lab/triage_naked.py T-1007 native
    uv run python days/day-04/lab/triage_naked.py T-1007 prompt
"""

from __future__ import annotations

import json
import sys

from openai import OpenAI

from mandala.config import load_keys
from mandala.models import PROVIDERS
from mandala.schemas import TriageResult

SYSTEM = (
    "You are Mandala's triage analyst. Given one support ticket, classify it. "
    "Never invent facts not present in the ticket body. "
    "Be honest about uncertainty: a vague ticket deserves a low confidence score."
)

_provider = PROVIDERS["groq"]
_client = OpenAI(api_key=load_keys().groq, base_url=_provider.base_url)

SUBMIT_TOOL = {
    "type": "function",
    "function": {
        "name": "submit_triage",
        "description": "Submit your triage decision. Calling this is how you finish.",
        "parameters": TriageResult.model_json_schema(),
    },
}


def triage_via_tool(ticket: dict) -> TriageResult:
    """Technique 3: the tool-call IS the answer. Portable across providers."""
    response = _client.chat.completions.create(
        model=_provider.default_model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(ticket)},
        ],
        tools=[SUBMIT_TOOL],
        tool_choice={"type": "function", "function": {"name": "submit_triage"}},
    )
    call = response.choices[0].message.tool_calls[0]
    return TriageResult.model_validate_json(call.function.arguments)


def triage_via_native(ticket: dict) -> TriageResult:
    """Technique 2: provider-native structured output. Not supported everywhere."""
    response = _client.chat.completions.create(
        model=_provider.default_model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(ticket)},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "TriageResult",
                "schema": TriageResult.model_json_schema(),
                "strict": True,
            },
        },
    )
    return TriageResult.model_validate_json(response.choices[0].message.content)


def triage_via_prompt(ticket: dict) -> TriageResult:
    """Technique 1: ask nicely. Included so you can measure how badly it does."""
    response = _client.chat.completions.create(
        model=_provider.default_model,
        messages=[
            {"role": "system", "content": SYSTEM + " Reply with ONLY a JSON object, no prose, "
                                                   "with keys: ticket_id, severity, category, "
                                                   "summary, confidence."},
            {"role": "user", "content": json.dumps(ticket)},
        ],
    )
    return TriageResult.model_validate_json(response.choices[0].message.content)


TECHNIQUES = {
    "tool": triage_via_tool,
    "native": triage_via_native,
    "prompt": triage_via_prompt,
}

if __name__ == "__main__":
    from tools import get_ticket  # reuse Day 3's loader

    ticket_id = sys.argv[1] if len(sys.argv) > 1 else "T-1001"
    technique = sys.argv[2] if len(sys.argv) > 2 else "tool"
    result = TECHNIQUES[technique](get_ticket(ticket_id))
    print(result.model_dump_json(indent=2))
    print(f"needs_human_review: {result.needs_human_review()}")
```

**Line by line:**

- `"parameters": TriageResult.model_json_schema()` — **the whole trick.** Your Pydantic class becomes
  the tool's parameter schema directly. One definition, no duplication, no drift between the shape
  you validate and the shape you asked for.
- `tool_choice={"type": "function", "function": {"name": "submit_triage"}}` — **force** the model to
  call this specific tool rather than letting it choose. This is what converts "a tool it might use"
  into "the only way to answer". Without it the model sometimes replies in prose and you get an
  `IndexError` on `tool_calls[0]`.
- `response.choices[0].message.tool_calls[0]` — the forced call.
- `TriageResult.model_validate_json(call.function.arguments)` — parse **and validate** in one step.
  `arguments` is a JSON string; `model_validate_json` parses it and enforces every `Literal`, bound
  and length. If the model sent `"severity": "urgent"`, this raises here — at the boundary, where you
  want it.
- `response_format={"type": "json_schema", ...}` — the native route. Note `"strict": True`, which
  asks the provider to *guarantee* schema conformance rather than merely encourage it.
- **⚠️ Native structured output has schema restrictions** — commonly: every property must be
  required, `additionalProperties` must be `false`, and some keywords are unsupported. Pydantic's
  generated schema may need adjusting. When `native` fails and `tool` succeeds, that is the lesson,
  not a bug in your code.
- `triage_via_prompt` — deliberately fragile. It is here so you can **measure** how often asking
  nicely produces unparseable output. Measuring beats believing.
- `TECHNIQUES = {...}` — a dispatch dict, so the CLI can select one by name without an `if/elif`
  chain.
- `if __name__ == "__main__":` — only run the CLI part when the file is executed directly, not when
  it is imported by `compare.py`.
- `result.model_dump_json(indent=2)` — serialise the validated object back to pretty JSON for
  printing.

### 3.3 `days/day-04/lab/compare.py` — today's real artifact

```python
"""Run all three techniques over all ten golden tickets and print the evidence.

Budget: 30 requests (10 tickets x 3 techniques). Groq only.

Run:
    uv run python days/day-04/lab/compare.py
"""

from __future__ import annotations

import json
import pathlib

from pydantic import ValidationError

from triage_naked import TECHNIQUES

TICKETS = json.loads(
    (pathlib.Path(__file__).resolve().parents[3] / "tests/fixtures/tickets.json").read_text(
        encoding="utf-8"
    )
)

print(f"{'technique':<10} {'valid':>6} {'invalid':>8}   failures")
print("-" * 60)

for name, fn in TECHNIQUES.items():
    valid = 0
    failures: list[str] = []
    for ticket in TICKETS:
        try:
            fn(ticket)
            valid += 1
        except (ValidationError, ValueError, IndexError, TypeError) as exc:
            failures.append(f"{ticket['id']}:{type(exc).__name__}")
    print(f"{name:<10} {valid:>6} {len(failures):>8}   {', '.join(failures[:4])}")
```

**Line by line:**

- `from triage_naked import TECHNIQUES` — reuse the three functions. Because they were behind
  `if __name__ == "__main__"`, importing this module does not run the CLI.
- `parents[3]` — `lab` → `day-04` → `days` → repo root, same anchoring trick as Day 3.
- `print(f"{'technique':<10} {'valid':>6} ...")` — a header row. `<10` left-aligns in 10 characters,
  `>6` right-aligns in 6. Right-aligning numbers makes columns comparable at a glance.
- `"-" * 60` — string multiplication draws the rule.
- `except (ValidationError, ValueError, IndexError, TypeError)` — the four realistic failures:
  schema violation, unparseable JSON, no tool call returned, wrong type.
- `f"{ticket['id']}:{type(exc).__name__}"` — record **which** ticket failed and **how**. "3 failures"
  is a number; "T-1006:ValidationError, T-1007:ValidationError" is a finding — both of your hard
  tickets, which tells you the problem is ambiguity handling, not the technique.
- `failures[:4]` — show the first four so the row stays on one line.

Run it:

```bash
cd days/day-04/lab
uv run python compare.py
cd ../../..
```

**Save that table.** It is your own measured evidence that schema enforcement beats asking nicely,
and it comes out again in an interview.

---

## §4 AG-04 — The context window as a budget

### The plain idea

Every call resends everything. So the cost *and* the reliability of your agent are both functions of
what you choose to include.

Four things compete for the desk:

1. **System prompt** — small, constant, high value.
2. **Tool schemas** — sent on *every* call. Ten verbose tools can quietly cost more than the
   conversation does.
3. **Conversation history** — grows every turn. This is the one that explodes.
4. **Tool results** — the sneaky one. A tool returning a 200-line JSON blob just spent your budget on
   a payload the model needed three fields of.

The instinct is "the window is 1M tokens, I'm fine". Two reasons that is wrong even when true.
**First**, free tiers meter tokens per minute, so a fat prompt is a rate-limit event, not merely a
slow one. **Second** — and this surprises people — **more context often makes the answer worse.** A
model handed fifty tickets and asked about one will drift toward the wrong one. Relevance beats
volume. The plan's line again: *200 tickets don't fit; a retrieved top-5 does* — and the top-5
version is not merely cheaper, it is *more accurate*.

### The four levers, in the order you should reach for them

| Lever | What it does | You meet it again on |
|---|---|---|
| **Trim the tool result** | return 3 fields, not 30 | today |
| **Cap the history** | keep the last N turns | Day 7 (sessions) |
| **Summarise the middle** | compress old turns into a paragraph | Day 39 (LangChain summarisation middleware) |
| **Retrieve instead of stuff** | fetch only what is relevant | Day 46 (the honest RAG day) |

Reach for them **in that order**. Most people jump straight to retrieval when a three-field select
would have solved it. The cheapest context engineering is not putting it in.

### 4.1 `src/mandala/budget.py`

```python
"""Measure what you are actually sending, before optimising it.

Everyone guesses wrong about where their tokens go. This prints the truth.

Usage
-----
    >>> b = ContextBudget(limit=8000)
    >>> b.charge("system", "You are a helpful assistant.")
    >>> b.charge("tool_results", "{...200 lines of json...}")
    >>> print(b.report())
    context: 812/8000 tokens (10%)
      tool_results        805   99%
      system                7    1%
"""

from __future__ import annotations

from dataclasses import dataclass, field

CHARS_PER_TOKEN = 4


@dataclass
class ContextBudget:
    """A per-run tally of what filled the context window, by bucket."""

    limit: int
    spent: dict[str, int] = field(default_factory=dict)

    @staticmethod
    def estimate(text: str) -> int:
        """~4 characters per token. Deliberately approximate; exact counting is
        provider-specific and not worth a dependency for a decision this coarse."""
        return len(text) // CHARS_PER_TOKEN

    def charge(self, bucket: str, text: str) -> None:
        self.spent[bucket] = self.spent.get(bucket, 0) + self.estimate(text)

    @property
    def total(self) -> int:
        return sum(self.spent.values())

    def over_budget(self) -> bool:
        return self.total > self.limit

    def report(self) -> str:
        total = max(self.total, 1)
        rows = "\n".join(
            f"  {bucket:<18} {tokens:>6}  {tokens / total:>5.0%}"
            for bucket, tokens in sorted(self.spent.items(), key=lambda kv: -kv[1])
        )
        return f"context: {self.total}/{self.limit} tokens ({self.total / self.limit:.0%})\n{rows}"
```

**Line by line:**

- `CHARS_PER_TOKEN = 4` — the rule of thumb for English text. **Why not count exactly?** Exact
  tokenisation needs a provider-specific tokenizer, differs per model, and would add a dependency —
  all to refine a number you are using to answer "is it the tool results or the history?". A 20%
  error does not change that answer. **Precision you cannot act on is waste.**
- `@dataclass` — generates `__init__` and `__repr__`. Not frozen here, because the whole point is
  that it mutates as you charge it.
- `spent: dict[str, int] = field(default_factory=dict)` — **`default_factory`, not `= {}`.** A
  mutable default argument in Python is shared across all instances, so `= {}` would make every
  budget object share one dict. `default_factory=dict` calls `dict()` fresh per instance. (Ruff's
  bugbear rules, enabled on Day 0, catch this class of bug.)
- `@staticmethod def estimate(text)` — no `self` needed, so it is a static method and can be called
  as `ContextBudget.estimate("...")` without an instance.
- `len(text) // CHARS_PER_TOKEN` — `//` is integer division, discarding the remainder.
- `self.spent.get(bucket, 0) + ...` — accumulate, defaulting to 0 for a new bucket.
- `@property def total` — computed on access, so it can never go stale. Called as `b.total`, no
  parentheses.
- `sorted(self.spent.items(), key=lambda kv: -kv[1])` — sort by value, **descending** via the minus
  sign. `kv` is a `(bucket, tokens)` tuple, so `kv[1]` is the count. Descending matters: the biggest
  offender must be the first line you read.
- `max(self.total, 1)` — avoid dividing by zero on an empty budget.
- `{tokens / total:>5.0%}` — format as a percentage, no decimals, right-aligned in 5 characters.

Now wire it into the Day-3 loop: charge `"system"`, `"tool_schemas"`, `"history"` and
`"tool_results"` before each call, and print `report()` at the end of every run. The moment you
**see** that tool results are 70% of your prompt, the fix becomes obvious — and you will never again
guess at where the budget went.

### 4.2 `days/day-04/lab/fat_context.py` — watch it break

```python
"""Prove that more context is not free, and often not better.

Takes T-1009 (the long rambling ticket), inflates it, and shows both the token
count climbing and the answer quality falling. Then trims the tool result and
shows both recover.

Budget: ~6 requests. Groq.

Run:
    uv run python days/day-04/lab/fat_context.py
"""

from __future__ import annotations

import json

from mandala.budget import ContextBudget
from mandala.schemas import TriageResult
from triage_naked import triage_via_tool
from tools import get_ticket

FULL_FIELDS = ("id", "severity", "category", "body")
TRIMMED_FIELDS = ("id", "body")


def inflate(ticket: dict, times: int) -> dict:
    """Make one ticket long by repeating its body. Simulates a real 40-message thread."""
    return {**ticket, "body": (ticket["body"] + " ") * times}


def project(ticket: dict, fields: tuple[str, ...]) -> dict:
    """Return only the fields we choose to spend context on."""
    return {k: v for k, v in ticket.items() if k in fields}


base = get_ticket("T-1009")

for times in (1, 5, 20):
    for label, fields in (("full", FULL_FIELDS), ("trimmed", TRIMMED_FIELDS)):
        payload = project(inflate(base, times), fields)
        budget = ContextBudget(limit=8000)
        budget.charge("tool_results", json.dumps(payload))

        result: TriageResult = triage_via_tool(payload)
        print(
            f"x{times:<3} {label:<8} tokens={budget.total:>5} "
            f"severity={result.severity:<8} confidence={result.confidence:.2f}"
        )
```

**Line by line:**

- `{**ticket, "body": ...}` — dictionary unpacking: copy every key from `ticket`, then override
  `body`. This produces a **new** dict rather than mutating the original, so the loop's later
  iterations are not corrupted by earlier ones.
- `(ticket["body"] + " ") * times` — repeat the body. Crude, and exactly right: you are testing the
  effect of *volume*, holding *content* constant.
- `{k: v for k, v in ticket.items() if k in fields}` — a **dict comprehension** implementing a
  projection, i.e. a `SELECT` of specific columns. This one line is the "trim the tool result" lever.
- `for times in (1, 5, 20)` and the nested loop — six runs: three sizes × two projections.
- `f"{result.confidence:.2f}"` — two decimal places.

**What to look for.** Two things, and the second is the surprise:

1. Token count climbs roughly linearly with `times`. Expected.
2. **`severity` and `confidence` start drifting at ×20 in the `full` runs** — and the `trimmed` runs
   stay stable. More context did not just cost more; it made the answer worse.

That single experiment is the entire argument for context engineering, and you will be able to
describe it from memory in an interview because you ran it yourself.

---

## §5 The eval that must be able to fail

### `tests/test_triage_schema.py`

```python
"""Day-4 guardrails: the contract holds, and the agent is honest about uncertainty."""

import pytest
from pydantic import ValidationError

from mandala.schemas import TriageResult


def _valid(**overrides) -> dict:
    base = {
        "ticket_id": "T-1001",
        "severity": "high",
        "category": "auth",
        "summary": "SSO login loop",
        "confidence": 0.8,
    }
    return {**base, **overrides}


@pytest.mark.parametrize("bad", ["URGENT", "urgent", "High", "sev1", ""])
def test_drifted_severity_labels_are_rejected(bad):
    """A drifted label must fail at the boundary, not flow downstream."""
    with pytest.raises(ValidationError):
        TriageResult(**_valid(severity=bad))


@pytest.mark.parametrize("bad", [-0.1, 1.4, 2.0])
def test_confidence_is_bounded(bad):
    with pytest.raises(ValidationError):
        TriageResult(**_valid(confidence=bad))


def test_summary_length_is_enforced():
    with pytest.raises(ValidationError):
        TriageResult(**_valid(summary="x" * 201))


def test_critical_always_needs_human_review():
    """Even a confident critical must not be auto-resolved. Day-84 depends on this."""
    assert TriageResult(**_valid(severity="critical", confidence=0.99)).needs_human_review()


def test_low_confidence_needs_human_review():
    assert TriageResult(**_valid(confidence=0.3)).needs_human_review()


def test_schema_exposes_descriptions_to_the_model():
    """Descriptions are prompts. A field without one is a field filled by vibe."""
    schema = TriageResult.model_json_schema()
    for name, prop in schema["properties"].items():
        assert prop.get("description"), f"{name} has no description"


@pytest.mark.vcr
def test_every_golden_ticket_produces_a_valid_result(golden_tickets):
    """All 10. Not 'usually'. The point of a schema is that it always holds."""
    from triage_naked import triage_via_tool

    for ticket in golden_tickets:
        assert isinstance(triage_via_tool(ticket), TriageResult)


@pytest.mark.vcr
def test_ambiguous_ticket_reports_low_confidence(golden_tickets):
    """T-1007 is genuinely ambiguous (billing or data?). An honest agent says so."""
    from triage_naked import triage_via_tool

    ticket = next(t for t in golden_tickets if t["id"] == "T-1007")
    result = triage_via_tool(ticket)
    assert result.confidence < 0.7, (
        f"model reported {result.confidence} on a ticket careful humans disagree about"
    )


@pytest.mark.vcr
def test_empty_ticket_reports_low_confidence(golden_tickets):
    """T-1006 is 'it's broken'. There is nothing to be confident about."""
    from triage_naked import triage_via_tool

    ticket = next(t for t in golden_tickets if t["id"] == "T-1006")
    assert triage_via_tool(ticket).confidence < 0.5
```

**Line by line:**

- `def _valid(**overrides) -> dict:` — a **test-data builder**. `**overrides` collects any keyword
  arguments into a dict, and `{**base, **overrides}` merges them with the later one winning. So
  `_valid(severity="URGENT")` is a fully-valid object with one field deliberately broken. This keeps
  every test focused on the *one* thing it is testing, and means adding a required field later is a
  one-line change instead of an edit to twelve tests.
- `@pytest.mark.parametrize("bad", ["URGENT", "urgent", "High", "sev1", ""])` — five separate test
  results. Note `"High"` and `"urgent"` specifically: **case and synonym drift are the realistic
  failures**, not obvious nonsense.
- `test_critical_always_needs_human_review` — asserts the *policy*, not the data. This is the test
  that will stop a future you from auto-resolving T-1008.
- `test_schema_exposes_descriptions_to_the_model` — a test **about your prompt engineering**. Add a
  field without a description on Day 30 and this goes red. It is one of the highest-value tests in
  this file precisely because it guards something you would otherwise forget.
- `next(t for t in golden_tickets if t["id"] == "T-1007")` — find the first match from a generator.
  Raises `StopIteration` if the ticket is gone, which is the correct loud failure.
- The multi-line `assert ... , (f"...")` form — parentheses let the failure message wrap. **Always
  include the actual value in the message**; "assert 0.9 < 0.7" tells you nothing about which model
  or which ticket.

**`test_ambiguous_ticket_reports_low_confidence` will be red for a while, and it should be.** Making
a model appropriately unsure is prompt work: you must describe what low confidence *means* and give
it permission to be unsure. This is your honest introduction to calibration, which returns in force
on Day 72 (LLM-as-judge).

```bash
uv run pytest tests/test_triage_schema.py -m live     # record cassettes: ~30 requests
uv run pytest tests/test_triage_schema.py            # replays: 0 requests
```

---

## §6 Traps

- **`str` where you meant `Literal`.** The most common structured-output bug: everything validates,
  nothing is checked, and `"High"` vs `"high"` breaks a router two weeks later.
- **Fields with no description.** The model sees the schema. Undescribed field, unprompted field.
- **Validating and then catching the error and logging it.** Now you have a schema that documents
  rather than enforces. Let it raise, or retry — one or the other, **deliberately.**
- **`max_length` the model keeps violating.** Two fixes together: state the limit in the description
  *as well*, and on `ValidationError` retry once with the error message fed back as a user turn.
  Schema constraints are checks, and checks need a response plan.
- **Assuming your free-tier model supports `response_format`.** Check. When it does not, use the
  tool-call technique — that is why it is in the table.
- **Forgetting `tool_choice`** when using the tool-as-schema trick. Without it the model sometimes
  answers in prose and you get `IndexError: list index out of range`.
- **Optimising context before measuring it.** Build `ContextBudget` first. Every time.
- **Believing `estimate()` is accurate.** It is a ratio, not a tokenizer. Use it to compare buckets,
  never to decide whether you fit in the window.

---

## §7 Request budget

| Activity | Requests |
|---|---|
| `compare.py`: 10 tickets × 3 techniques | 30 (Groq) |
| Getting `triage_naked.py` right | ~15 (Groq) |
| `fat_context.py`: 3 sizes × 2 projections | 6 (Groq) |
| Confidence-calibration prompt iterations | ~15 (Groq) |
| Recording cassettes | ~12 (Groq) |
| **Total** | **≈ 80, all Groq** |

Eighty is a big day by this plan's standards. Groq's requests-per-day allowance handles it; Gemini's
would not comfortably. **This is why you have three providers.** Log the real number in
`docs/RATE_BUDGET.md`.

---

## §8 Verify before you code

Written **2026-08-20** against `openai` **3.3.1**, `pydantic` **2.13.4**.

- `https://platform.openai.com/docs/guides/structured-outputs` — the `response_format` shape and its
  schema restrictions (all fields required, `additionalProperties: false`, unsupported keywords).
  These restrictions bite, and they are why `triage_via_native` may need schema massaging.
- `https://console.groq.com/docs/structured-outputs` — **which** Groq models support it. Not all do.
- `https://ai.google.dev/gemini-api/docs/structured-output` — Gemini's response-schema form differs
  from OpenAI's. Read it before using Gemini for this.
- `https://docs.pydantic.dev/latest/concepts/json_schema/` — what `model_json_schema()` emits, and
  the `mode="serialization"` option.

---

## §9 Say it in an interview

> "Anywhere an agent's output crosses into ordinary code I put a schema on the boundary — Pydantic
> with `Literal` types for the enumerated fields, so a drifted label fails loudly instead of flowing
> downstream. I always include a confidence field, because that's what lets you route low-confidence
> cases to a human instead of trusting everything equally. And on context: I treat the window as a
> budget with four line items — system prompt, tool schemas, history, tool results. Tool results are
> usually the surprise; people return whole rows when the model needed three fields. I instrument it
> before optimising, because everyone guesses wrong, and I've measured that trimming context often
> *improves* accuracy rather than just cost."

---

## §10 Done when

```bash
./m check
./m done 4
```

Tomorrow: the loop gets ambitious, starts wandering, and you learn why every serious agent framework
eventually reinvents the graph.
