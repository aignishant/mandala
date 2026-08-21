---
day: 60
phase: 9
phase_name: "The bake-off"
title: "Bake-off II — the slice on CrewAI"
ids: []
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 60 — Bake-off II: the slice, on CrewAI

**Phase 9 · The bake-off 🥇** · IDs: none — the slice is the artifact

> **Yesterday:** the rules, the frozen slice, the acceptance suite, and implementation one.
> **Today:** the identical slice on CrewAI. Same two hours, same tests, same MCP server. The
> interesting question is which of CrewAI's **two** answers you use — Crews or Flows — because it is
> the only framework in the bake-off that offers a choice, and choosing is itself a finding.
> **Tomorrow:** LangChain.

```bash
./m start 60
./m scaffold 60
```

---

## §1 The story

**Nothing about the rules changes today.** `SLICE.md` is frozen, `tests/test_bakeoff.py` is written,
the timer is two hours, and `ticket-db` is the tool layer. If you find yourself wanting to adjust the
specification because CrewAI would do better with a small change — **that impulse is the finding**.
Write it in `surprises.md` and build to the spec.

The genuine decision today is one no other framework poses:

> **Crews or Flows?**

CrewAI is the only framework in this comparison that ships **two** answers to "who owns the loop":
roles own it (Crews, Days 23–29) or you own it in decorators (Flows, Days 30–35). **Pick one, build
it, and write down why** — and then note that "this framework made me choose before I could start" is
itself a row on the scorecard, and not obviously a positive one.

**The recommendation, and you should disagree with it if your reasoning differs:** build it as a
**Flow with a Crew inside the research branch**, because that is what Day 31's CR-17 established as
the production shape and it is what you would actually ship. Building a pure Crew would be building
the framework's weaker half on purpose; building a pure Flow would leave out the thing CrewAI is
famous for.

**But time the decision.** If choosing takes fifteen minutes of your two hours, that is 12.5% of the
timebox spent before the first line — and **the three other frameworks charge you nothing for it.**

---

## §2 The build

### 2.1 What you already have

- `src/mandala/flows/` — state, routing, organs, persistence, approval (Days 30–35)
- `src/mandala/crew/` — roles, tools, tasks, guardrails, `mandala_mini` (Days 23–29)
- The MCP mount via `crewai_tools.MCPServerAdapter` (Day 55)

**Considerable foundation, and that is fair** — the same is true of the other three. What the bake-off
measures is how fast you get from "I know this framework" to "the slice passes".

### 2.2 `src/mandala/bakeoff/crew_slice.py`

```python
"""The slice, on CrewAI. Two hours, hard stop. Same contract as every other day.

Shape: a Flow skeleton with a Crew in the research branch (CR-17, Day 31) -- the
production shape, and what I would actually ship.

Rule 3 (critical -> escalate) is a @router: routing is MY code and costs no model
turn, which is the opposite of yesterday's handoff. That contrast is the single
cleanest data point in the whole bake-off, because it is the same business rule at
two different loci of control, measured the same way.

Rule 6 (the drafter never sees the raw body): flow state is GLOBAL to the run, so
the only mechanism is deletion -- drop_body() before the drafting step (Day 30 §4.4).
Which makes ORDERING a security property. Time how long it takes to be confident
that ordering actually holds; that is the real cost of this approach.
"""

from __future__ import annotations

from tests.test_bakeoff import SliceResult


def run_slice(ticket_id: str) -> SliceResult:
    ...
```

**Line by line — the three design notes are the day's content:**

- **The Flow-with-a-Crew shape**, declared in the docstring with its justification. A reader of your
  bake-off should be able to see *why* this shape and not another.
- **Rule 3 as a `@router` costs zero model turns**, where yesterday's handoff cost one. **Record both
  numbers.** Same rule, two loci, and it is a real per-ticket cost difference rather than a stylistic
  preference. On a 50-request-a-day provider, one turn per ticket is a hard limit on throughput.
- **Rule 6 by deletion**, and the docstring names the consequence honestly: ordering becomes a
  security property. Yesterday the SDK needed a separate context (agents-as-tools); today you need a
  correctly-placed `drop_body()`. **Time how long it takes to be *confident* the ordering holds**, not
  just to write the call — that confidence gap is what a scorecard row should capture, and it is why
  Day 62's subgraph schema will feel different.

### 2.3 Where the timebox will go

Three predictable sinks, so you recognise them rather than being surprised:

1. **The MCP adapter's lifecycle.** Day 55 noted `MCPServerAdapter` is a **context manager**, which
   raises a question no other client raised: who opens it, and does the crew outlive the `with` block?
   **If you spend twenty minutes here, that is a scorecard row**, not a personal failing.
2. **Getting `SliceResult` out of a crew.** Crews return text (Day 31 §4.3's asymmetry: typed going
   in, prose coming out). You will write a parser. **Count its lines** — that is the "how much parsing
   did this framework make me write" row from Day 38's `four_ways.md`, now with a number.
3. **Counting model calls.** A crew with three agents at `max_iter` 5/8/4 does not tell you its
   request count directly. Day 28's callbacks (CR-12) are the mechanism. **Find it before the timer
   starts**, per yesterday's rule.

### 2.4 The log

Same template as yesterday — `days/day-60/lab/log.md` — and **fill it while the timer runs.**

Two extra lines for today only:

```markdown
Framework offered a choice (Crews / Flows): which, and why
Minutes spent deciding before the first line: __
```

**That second number is the honest cost of optionality**, and it is a number the other three days
cannot produce. Whether you write it up as a strength ("it fits more shapes") or a weakness ("it made
me choose before I could start") is your judgement — **but you cannot write it up at all if you did
not time it.**

---

## §3 What to compare, today

Fill these into `surprises.md` **as they happen**:

| Question | Yesterday (SDK) | Today (CrewAI) |
|---|---|---|
| Model turns to make the routing decision | 1 (a handoff) | 0 (a `@router`) |
| Lines to express rule 6 | | |
| Minutes until you *trusted* rule 6 | | |
| Lines of output parsing | | |
| Escape hatches reached for | | |
| Requirements passing at the buzzer | | |

**The "minutes until you trusted rule 6" row is the one to be careful with.** Writing `drop_body()`
takes thirty seconds. Being confident that no future step can read the body — when state is global
and the guarantee is positional — takes longer, and it is what Day 30 made you uncomfortable about at
the time. **Record the second number, not the first.**

---

## §4 Traps

- **Adjusting the slice because CrewAI would prefer it.** Note the impulse; build to spec.
- **Building a pure Crew** because it is CrewAI's famous half. It is not the production shape and you
  established that on Day 31.
- **Not timing the Crews-vs-Flows decision.** It is the only cost of optionality you can measure.
- **Letting the adapter's context manager eat the timebox silently.** Twenty minutes there is a
  finding — write it down at minute twenty, not at the buzzer.
- **Estimating the model-call count.** Wire the callback; an estimated number is not a data point.
- **Not counting the parser.** "Typed in, prose out" is the seam asymmetry and today gives it a
  number.
- **Recording "wrote drop_body()" as the cost of rule 6.** The cost is the confidence, not the call.
- **Rebuilding `mandala_mini`** because it is faster than reading it. Reuse is the realistic
  condition.
- **Skipping the log until afterwards.** Second day running; it does not get less true.

---

## §5 Request budget

**Declared: ~18 model requests, Groq.**

| What | Requests |
|---|---|
| Acceptance tests against a recorded result | **0** |
| Iterating during the timebox | ~12 |
| Three final runs (normal, critical, unclassifiable) | ~18 |

**Today is the most expensive of the four build days**, because a crew is three agents with
`max_iter` 5/8/4 and the research branch actually runs one. **That fact is itself a scorecard row** —
*"what does one slice cost in this framework?"* — and it is why the fan-out and the crew both live
behind one branch rather than in the default path.

Log the number honestly, including the iterations. If the timebox ran long on requests rather than on
minutes, **say so**: on a free tier, "I ran out of quota before I ran out of time" is a real
constraint and the other three days may not hit it.

---

## §6 Verify before you code

- **`ticket-db` running**, and `MCPServerAdapter` still connecting after Phase 8's changes.
- **`crewai==1.15.17` and `crewai-tools==1.15.17`** still pinned and installed.
- **The model-call counting mechanism** (Day 28's callbacks) — wired **before** the timer.
- **`@router` return-value matching** — Day 31's `routes.py` constants, still correct in 1.15.17.
- **Does the adapter's context manager tolerate the crew running inside a flow step?** This is Day 55's
  open lifecycle question and today is when it bites.

---

## §7 Say it in an interview

> "CrewAI was the only framework in my comparison that made me choose before I could start — Crews or
> Flows — and I timed that decision, because optionality has a cost the other three don't charge. I
> built the production shape: a deterministic flow skeleton with a crew in the research branch. The
> cleanest data point of the whole bake-off came out of the routing rule: on the Agents SDK the
> critical-ticket branch is a handoff the model decides to take, which costs a model turn per ticket;
> in a flow it's a `@router` — my code, zero turns. Same business rule, two loci of control, and on a
> free tier that difference is a throughput limit rather than a style preference. The other thing I
> measured was how long it took to *trust* the security requirement rather than to satisfy it: flow
> state is global to the run, so the only way to keep raw customer text from the drafting step is to
> delete it first — which makes ordering a security property, and being confident about ordering takes
> considerably longer than writing the delete."

---

## §8 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 60
```
