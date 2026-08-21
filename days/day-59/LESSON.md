---
day: 59
phase: 9
phase_name: "The bake-off"
title: "Bake-off I — the slice on the Agents SDK"
ids: ["AG-29"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 59 — Bake-off I: the slice, on the Agents SDK

**Phase 9 · The bake-off 🥇** · IDs: **AG-29 🅿️**

> **Yesterday:** the Phase-8 gate — one server, four clients, a legacy shim, and a nil report written
> down properly.
> **Today:** the bake-off opens. **The same Mandala slice, built four times, one framework per day,
> timeboxed.** Today is the Agents SDK. The rules are set today and they bind all four days, because
> a comparison whose conditions change halfway is not a comparison.
> **Tomorrow:** the identical slice on CrewAI.

```bash
./m start 59
./m scaffold 59
```

---

## §1 The story

Fifty-eight days of building, and every framework has looked good on its own day. **That is exactly
the problem.** You learned each one while excited about it, on a task shaped to suit it, with more
practice each time. Three confounds, all pointing the same way.

**The bake-off's job is to remove them:**

| Confound | How Days 59–62 remove it |
|---|---|
| Different tasks | **one slice specification**, identical in all four |
| Different amounts of practice | you have now used all four for weeks |
| Unbounded effort | **a fixed timebox**, same for all four |
| Different tools | **the same MCP server** (Day 55) in all four |
| Different judgement of "done" | **the same acceptance tests**, written today |

That last row is the one people skip and it is what makes today matter more than the other three
build days. **You write the acceptance tests before you write any of the four implementations**, and
they are framework-agnostic by construction. Then "done" is not a feeling.

**AG-29 is today's ID and it is 🅿️**: *"the 'who owns the loop?' axis as a reusable interview answer;
filled in for real during the Phase 9 bake-off."* You have been able to recite that axis since Day 1.
Today you start replacing the recitation with evidence, and by Day 63 you will have four data points
where you used to have a slogan.

**One warning worth taking seriously.** You know the expected outcome — the plan states it in Part 5
and even flags it: *"expected — but not presumed."* Knowing the answer in advance is how a bake-off
becomes a formality. §2.4 is the specific defence against that, and it is the difference between an
evaluation and a rationalisation.

---

## §2 The rules — set today, binding for four days

### 2.1 The slice

**One specification, four implementations.** Write it once, in `days/day-59/lab/SLICE.md`, and do not
edit it after tomorrow begins.

```markdown
# The bake-off slice — frozen 2026-08-__

Input:  a ticket id
Output: a TriageResult, plus a drafted reply, plus an audit trail

Required behaviour:
1. Fetch the ticket via the ticket-db MCP server (Day 55). No local fixtures.
2. Classify it into TriageResult (Day 4's schema, unchanged).
3. If severity == "critical": stop and escalate. No draft.
4. Otherwise: search the handbook via MCP, gather 2-4 cited findings.
5. Draft a reply of <= 120 words that cites at least one source.
6. The drafting step must NOT see the raw ticket body (Day 8's rule).
7. Produce an audit trail naming every step that ran, in order.
8. Fail closed: if classification produces nothing, escalate.

Out of scope (do NOT build): persistence, human approval, streaming, retries.
```

**Line by line on why each rule is there:**

- **Rule 1 forces MCP**, so the tool layer is genuinely identical rather than "the same idea, four
  ways". That was the whole point of Phase 8 and it makes the comparison honest.
- **Rule 3 is a branch.** Without one, three of the four frameworks look identical, because every
  framework can do a pipeline. **The differences only appear where control flow does.**
- **Rule 6 is the security constraint** and it is deliberately the hardest to satisfy. You solved it
  four different ways already — deletion (Day 30), a write-once reducer (Day 43), a private `Send`
  payload (Day 44), a subgraph schema (Day 48). **How gracefully each framework expresses it is a
  scorecard row**, and it is the row that will surprise you.
- **Rule 7 forces observability** into each implementation rather than leaving it as a framework
  feature you might or might not use.
- **Rule 8 is the `None` branch**, fourth appearance. Every framework needs it and they differ in how
  natural it is.
- **The out-of-scope list is as important as the requirements.** Without it you will build durability
  in LangGraph (where it is free) and not in the SDK (where it is not), and then compare them. **Any
  capability not in all four is not in the bake-off.**

### 2.2 The timebox

**Two hours per framework, wall clock, hard stop.**

- Start a timer. When it rings, **stop, even mid-function**, and record what state the implementation
  is in.
- **An unfinished implementation is data, not failure.** "Ran out of time at step 5" is one of the
  most informative outcomes available and it is exactly what an unbounded bake-off hides.
- Record the timer's reading against each acceptance test as you pass it (§2.3). **Time-to-first-pass
  per requirement is a better velocity metric than total time**, because it shows *where* each
  framework front-loads its cost.

**Two hours is deliberately tight.** You are not building a product; you are measuring how quickly
each framework gets you to a working slice of a system you already understand completely.

### 2.3 The acceptance tests — written today, before any implementation

```python
# tests/test_bakeoff.py
"""ONE test suite, four implementations. Framework-agnostic by construction.

Every implementation exposes exactly one function:

    run_slice(ticket_id: str) -> SliceResult

so the tests import a different module per framework and assert identically. The
moment a test needs to know which framework is under it, the comparison is broken.

0 model requests: the suite runs against a RECORDED result (see conftest), and the
four live runs happen once each in the lab script.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SliceResult:
    """The only contract. All four implementations return this."""

    triage: object | None          # a TriageResult, or None if classification failed
    draft: str | None
    findings: list[str]
    sources: list[str]
    trail: list[str]               # every step that ran, in order
    saw_raw_body: set[str]         # which steps were exposed to the raw ticket text
    model_calls: int               # the honest request count


def test_it_classifies(result):
    assert result.triage is not None
    assert result.triage.severity in {"low", "normal", "high", "critical"}


def test_a_critical_ticket_escalates_without_a_draft(critical_result):
    assert critical_result.draft is None
    assert "escalate" in critical_result.trail


def test_an_unclassifiable_ticket_escalates(unclassifiable_result):
    """Rule 8, fail closed. Fourth framework, fourth time this test appears."""
    assert "escalate" in unclassifiable_result.trail


def test_the_draft_cites_a_source(result):
    assert result.draft is not None
    assert result.sources, "a draft with no sources"
    assert any(s.split(":")[0] in result.draft for s in result.sources)


def test_the_draft_is_short(result):
    assert len(result.draft.split()) <= 120


def test_findings_are_bounded(result):
    assert 2 <= len(result.findings) <= 4


def test_the_drafting_step_never_saw_the_raw_body(result):
    """THE test. Rule 6, and the one the frameworks differ most on."""
    assert "draft" not in result.saw_raw_body, result.saw_raw_body


def test_the_trail_names_every_step_in_order(result):
    assert result.trail == sorted(result.trail, key=result.trail.index)
    assert result.trail[0] == "fetch"
    assert len(result.trail) >= 4


def test_the_tools_came_from_mcp(result):
    """Rule 1. Flip it: use a local fixture and this goes red."""
    assert any("mcp" in step or "ticket-db" in step for step in result.trail)
```

**Line by line:**

- **`SliceResult` is the entire contract**, and freezing it today is what makes the four
  implementations comparable. Note `saw_raw_body` and `model_calls`: **the two things you most want to
  compare are not outputs, they are properties of the run**, so they have to be in the contract or
  they cannot be measured.
- `saw_raw_body: set[str]` — each implementation records which of its own steps were handed the raw
  ticket text. **That is self-reported and therefore only as honest as you are**, which is worth
  stating: a framework where you *cannot easily tell* is itself a finding, and you should record
  "unclear" rather than guessing.
- `model_calls: int` — **the honest request count.** Day 38 established that counting `AIMessage`s is
  how you get it; each framework needs its own equivalent and finding it is part of the exercise.
- **Every test is written against `SliceResult`, never against a framework object.** The docstring
  says why: the moment a test knows which framework it is testing, the comparison is broken.
- `test_the_drafting_step_never_saw_the_raw_body` is the headline. **You have solved this four ways
  already and today you find out which framework makes it natural** rather than possible.
- The four tests that mirror earlier days (`test_an_unclassifiable_ticket_escalates` especially) are
  **deliberately the same tests you have already written three or four times.** By now that
  repetition is itself evidence: a policy test you can port unchanged across four frameworks is proof
  the policy is framework-independent, which is the plan's thesis.

### 2.4 Guarding against the expected outcome

The plan states the expected result and then says *"not presumed"*. Three defences, and use all three:

1. **Write your prediction down now**, before building, in `days/day-59/lab/prediction.md`: which
   framework wins each scorecard row, and by how much. **A prediction you recorded is falsifiable; a
   memory is not.**
2. **Build in the order the plan gives** — SDK, CrewAI, LangChain, LangGraph — which puts your
   expected winner *last*, when you are most tired and most practised. Those two effects push in
   opposite directions, which is the best you can do without randomising.
3. **Record the surprises immediately**, in a running `surprises.md`. On Day 63 you will remember the
   conclusions and forget the moments that produced them.

**And on Day 63, count how many of your predictions were wrong.** If the answer is zero, be suspicious
of the experiment rather than pleased with yourself.

---

## §3 Today's build — the Agents SDK

### 3.1 What you already have

- `src/mandala/sdk.py` — agents, `Runner`, handoffs (Days 9–14)
- The MCP mount with `require_approval` (Day 55) — **the SDK's distinguishing feature**
- `mandala.schemas.TriageResult` and `mandala.prompts` — unchanged since Days 4 and 6

**You are not starting from zero, and neither will the other three days.** That is fair: the bake-off
measures *"how quickly does this framework get me to a working slice"*, and having a foundation is the
realistic condition.

### 3.2 `src/mandala/bakeoff/sdk_slice.py`

```python
"""The slice, on the OpenAI Agents SDK. Two hours, hard stop.

One exported function: run_slice(ticket_id) -> SliceResult.

The SDK's answer to "who owns the loop?" is: the MODEL owns it. So rule 3's branch
(critical -> escalate) is expressed as a HANDOFF and the model decides to take it,
which is the honest way to build this in this framework -- forcing an if-statement
around the runner would be building LangGraph badly and would make the comparison
meaningless.

Rule 6 (the drafter must not see the raw body) is the interesting one here: with the
model owning the loop, the raw body is in the conversation, and everything downstream
sees the conversation. See §3.3.
"""

from __future__ import annotations

from tests.test_bakeoff import SliceResult

STEPS: list[str] = []
SAW_BODY: set[str] = set()


def run_slice(ticket_id: str) -> SliceResult:
    ...
```

**Line by line — and the design notes matter more than the code today:**

- **`run_slice` is the only export.** One function, one contract, four implementations.
- **The docstring commits to building it the framework's way**, and that commitment is the most
  important methodological decision in the bake-off. Every framework has an escape hatch that lets
  you write imperative Python around it. Using it would make all four implementations converge and
  measure nothing. **Build it the way the framework wants, and record where that hurts.**
- `STEPS` and `SAW_BODY` as module globals — ugly, and correct for a timeboxed comparison harness.
  **Do not spend timebox minutes on elegance in a measurement rig**, and note that you did not.
- **Rule 3 as a handoff** is the SDK's idiom: an `EscalationAgent` the triage agent hands off to when
  severity is critical. **Compare with Day 31's `@router`, Day 42's node, Day 44's conditional edge.**
  The same business rule, fourth locus of control, and this one costs a model turn to decide.

### 3.3 The hard part, and where to spend the timebox

**Rule 6 is the requirement the SDK makes hardest, and finding out why is worth more than finishing.**

The SDK's model owns the loop, which means the ticket body enters the conversation and the
conversation is what every subsequent turn sees. Your options:

- **Agents-as-tools** (OAI-10, Day 13): the drafter becomes a *tool* called with only the findings, so
  it has its own context. **This is the SDK's real answer** and it is a good one.
- **A second `Runner.run`** with a fresh conversation seeded only with findings. Cruder, obvious,
  works.
- **An output guardrail** that checks the draft does not quote the body. **This is detection, not
  prevention** — Day 29 already found that guardrails protect the output path, not the input path.
  Record it as such if you use it.

**Whichever you pick, record it against the "expressing rule 6" scorecard row**, and record how many
minutes it took. On Day 62, LangGraph will express the same rule as a subgraph state schema — one
declaration — and **the minutes are the comparison.**

### 3.4 What to measure, as you go

Keep `days/day-59/lab/log.md` open and write while the timer runs:

```markdown
# Bake-off I — Agents SDK — 2026-08-__

Timer started: __:__

| Requirement | Passed at | Notes |
|---|---|---|
| 1. MCP fetch | | |
| 2. classify | | |
| 3. critical -> escalate | | |
| 4. handbook findings | | |
| 5. draft <= 120 words | | |
| 6. drafter never sees body | | **how did I do it? how long?** |
| 7. audit trail | | |
| 8. fail closed | | |

Timer stopped: __:__   Requirements passing: _/8
Model calls for one run: __
Lines of code: __
Times I reached for an escape hatch: __
The moment I got stuck: 
The thing that was easier than expected:
```

- **"Times I reached for an escape hatch"** is the most revealing line on the page. It counts how often
  the framework's idiom did not fit and you wanted plain Python.
- **"Passed at" times, not durations** — you want to see where the cost front-loads.
- **Write while the timer runs**, not afterwards. Reconstructed notes are conclusions, not
  observations.

---

## §4 AG-29 — the interview answer, first draft

🅿️. Half a page, and you will revise it three more times this week.

`days/day-59/lab/who_owns_the_loop.md`:

```markdown
# Who owns the loop? — draft 1 of 4, after building the slice on the Agents SDK

| Framework | Who owns the loop | What that makes easy | What that makes hard |
|---|---|---|---|
| OpenAI Agents SDK | the model | | |
| CrewAI | roles / the process | | |
| LangChain | the abstraction | | |
| LangGraph | you | | |

## Today's evidence (SDK)
<what did "the model owns the loop" actually cost or save, in minutes and in lines?>

## The sentence I would say in an interview, today
<one paragraph. You will rewrite it on Days 60, 61, 62 and 63 -- keep all four drafts.>
```

**Keep all four drafts.** Watching your own answer change as evidence arrives is the most honest thing
in this phase, and on Day 89 the diff between draft 1 and draft 5 is a portfolio artifact in its own
right.

---

## §5 Traps

- **Editing `SLICE.md` after tomorrow starts.** The specification is frozen; if it is wrong, note the
  flaw and keep it — a flawed constant beats a moving target.
- **Skipping the acceptance tests** and judging "done" by eye. Then Day 63 compares four different
  ideas of done.
- **Letting the timebox slip "just to finish".** The unfinished state is the measurement.
- **Building the SDK version like a graph** because you know graphs now. Build it the SDK's way.
- **Adding persistence or approval** because the framework makes it easy. Out of scope in all four.
- **Using local fixtures instead of the MCP server.** Rule 1 exists so the tool layer is identical.
- **Not writing the prediction down.** Then every result confirms what you already thought.
- **Reconstructing the log afterwards.** Write while the timer runs.
- **Treating an escape hatch as free.** Count them; that count is a scorecard row.
- **Being pleased that your prediction was right.** On Day 63, zero wrong predictions is a smell.

---

## §6 Request budget

**Declared: ~15 model requests, Groq.**

| What | Requests |
|---|---|
| `tests/test_bakeoff.py` against a recorded result | **0** |
| Iterating during the timebox | ~10 |
| Three final runs (normal, critical, unclassifiable) | ~15 |

**Budget carefully: this is four days of the same spend.** Phase 9's build days will cost roughly 60
requests between them, which is 5% of a Groq week but **more than a full day of OpenRouter**. Use
Groq for all four, and record `model_calls` per implementation — **that number is a scorecard row and
it is the one nobody else measures.**

---

## §7 Verify before you code

- **Is the `ticket-db` MCP server running?** All four implementations depend on it (rule 1). Start it
  before the timer.
- **Does the SDK's MCP mount still work** after Phase 8's changes? Day 55's code, re-run.
- **`openai-agents==0.22.0` still pinned and installed?** Six phases since Day 9.
- **How do you count model calls in the SDK?** Day 14's tracing, or the run result. **Find it before
  the timer starts** — hunting for it inside the timebox is measuring the wrong thing.
- **Does `require_approval` interfere** with an unattended run? You want no approvals today; approval
  is out of scope (rule list).

---

## §8 Say it in an interview

> "I built the same slice four times, one framework per day, two hours each, against one frozen
> specification, one shared MCP tool server, and one framework-agnostic acceptance suite written
> before any of the implementations. Everything else in a framework comparison is confounded —
> different tasks, different amounts of practice, unbounded effort — and freezing those is most of the
> work. The requirement that separated them was that the drafting step must never see the raw customer
> text: I'd solved that four different ways across the project, and what I measured was how many
> minutes and how many escape hatches each framework needed to express it. I also wrote my predictions
> down before starting, and counted how many were wrong at the end — if none of them had been, I'd
> have trusted the experiment less, not more."

---

## §9 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 59
```
