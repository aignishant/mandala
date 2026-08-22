---
day: 63
phase: 9
phase_name: "The bake-off"
title: "The scorecard"
ids: []
kind: concept
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 63 — The scorecard

**Phase 9 · The bake-off 🥇** · IDs: none — the scorecard is the artifact

> **Yesterday:** the fourth and final implementation, and a fairness ledger written while the timer
> ran.
> **Today:** turn four days of measurements and thirty days of comparison tables into **one published
> scorecard** — scored on a fixed matrix, with the weights declared before the scores. No code today.
> **Tomorrow:** ADR-003, the capstone architecture decision, signed after a cold read.

```bash
./m start 63
./m scaffold 63
```

---

## §1 The story

**Principle 10: compare, don't crusade.** The plan's Phase-9 gate: *"published scorecard; ADR-003
signed by you-as-reviewer a day later (cold read)."*

Today has one job and one failure mode.

**The job:** produce a scorecard a stranger could disagree with usefully. That means every score
traces to a measurement or a stated judgement, and the difference between the two is visible.

**The failure mode:** *scoring to a conclusion.* You know which framework you expect to win; the
temptation is to pick weights that produce it. The defence is procedural and it is the whole of §2:
**declare the weights before you look at the scores, and do not change them afterwards.** If a weight
turns out to be wrong, you may say so in the write-up — you may not edit it and re-total.

**A second, subtler failure mode:** a scorecard where one framework wins every row. Real tools have
trade-offs, and a clean sweep almost always means the matrix was chosen to suit the winner. **If your
totals come out that way, the honest move is to go looking for the row you forgot to include**, not to
celebrate.

---

## §2 The matrix — weights first

The plan fixes the eight dimensions (Part 5, Phase 9): *"control, durability, HITL, testing, ops,
velocity, lock-in, **free-tier friendliness**"*.

### 2.1 Declare the weights now

`days/day-63/lab/weights.md`, written **before opening any log file**:

```markdown
# Scorecard weights — declared 2026-08-__, BEFORE scoring

Weights are for MANDALA, not in general. A different system would weight differently,
and saying which system you are scoring for is what makes a scorecard useful.

| Dimension | Weight | Why this weight FOR MANDALA |
|---|---|---|
| Control | | |
| Durability | | |
| HITL | | |
| Testing | | |
| Ops | | |
| Velocity | | |
| Lock-in | | |
| Free-tier friendliness | | |
| **Total** | **100** | |

## The system I am weighting for
<one paragraph: Mandala is a support-ops system with human approval before external
 writes, running on free tiers, maintained by one person. Every weight follows from
 that sentence -- or it is arbitrary.>

## What would change these weights
<name a different system and how the weights would move. If you cannot, the weights
 are probably not principled.>
```

**Line by line on why this file exists at all:**

- **Weights are contextual and a scorecard that hides that is propaganda.** "Durability: 20" is
  meaningless without "because Mandala pauses for a human and must survive a laptop sleep".
- **The "what would change these weights" section is the credibility test.** If you cannot describe a
  system where LangGraph's durability stops mattering, you have not understood why it matters here.
  Try it: a stateless classification API with no human in the loop weights durability near zero.
- **Total 100** so the arithmetic is trivial and the trade-offs are forced: raising one lowers another.

### 2.2 What each dimension means — pin it before scoring

Ambiguous dimensions are how a scorecard becomes vibes. **Write one operational sentence each**, and
name the evidence:

| Dimension | Operationally, it means | Evidence from |
|---|---|---|
| **Control** | can I decide what runs next, and see that decision before it runs? | routing rows, `draw_ascii()` |
| **Durability** | does a killed process resume, and at what granularity? | Days 32, 47, 49 |
| **HITL** | can a human pause it durably, and is the decision recorded? | Days 21, 33, 39, 50 |
| **Testing** | can I test the loop **without a provider**? | Days 36–40, 43–51 test files |
| **Ops** | can I see what happened and what it cost? | tracing days, `model_calls` |
| **Velocity** | minutes to first passing test; lines of new code | the four `log.md` files |
| **Lock-in** | what do I have to rewrite to leave? | Day 55's deletions; Day 61's finding |
| **Free-tier friendliness** | requests per slice; can a hidden call inflate it? | four request counts |

**Two of these deserve special care:**

- **Testing** is the dimension the plan cares about disproportionately (Principle 7) and the one most
  people score by feel. **You have the evidence:** every framework day since Day 36 has a test file
  that runs with no keys. **Count them.** A framework that ships a fake model (LangChain's
  `FakeListChatModel`, Day 39) is measurably more testable than one where you had to hit a real
  endpoint.
- **Free-tier friendliness** is the dimension nobody else's bake-off has, and it is the one where you
  have hard numbers: requests per slice from four days, phase totals from five phases, and the
  hidden-call question from Day 61 §2.4. **Score it from the ledger, not from impressions.**

---

## §3 Scoring

### 3.1 The rule

Score each framework 1–5 per dimension. **Every score gets a one-line justification naming its
evidence**, and the justification must say whether it is a *measurement* or a *judgement*.

```markdown
| Framework | Score | Evidence | M/J |
|---|---|---|---|
| Agents SDK | 3 | routing costs 1 model turn/ticket (Day 59 log) | **M** |
| CrewAI | 4 | @router, 0 turns (Day 60 log) | **M** |
| LangChain | 4 | plain if, 0 turns (Day 61 log) | **M** |
| LangGraph | 5 | conditional edge, 0 turns, and drawn before running | M + **J** |
```

**The M/J column is the most valuable thing on the page.** It shows a reader exactly where you are
reporting and where you are judging — and it stops *you* from sliding between the two. **If a whole
dimension is J, that is worth noticing**: it means you never measured it, and you should say so rather
than scoring confidently.

### 3.2 The rows you already have as numbers

Do not re-derive these; they are in the logs:

- **routing cost** — 1 turn (SDK) vs. 0 (the other three)
- **minutes to first passing test** — four numbers
- **lines of new code, excluding reuse** — four numbers, and the one that flatters LangGraph least
- **confidence-time for rule 6** — four numbers, and the most interesting of the set
- **escape hatches reached for** — four counts
- **requirements passing at the buzzer** — four counts
- **model calls per slice** — four numbers
- **tool declarations deleted by MCP** — 3 → 1 (Day 55)
- **phase request totals** — Phase 5 ~110/6d, Phase 6 ~60/7d, Phase 7 ~100/10d, Phase 8 ~25/6d,
  Phase 9 ~60/4d

**That last line is worth staring at.** Phase 8 — the protocol phase — cost a quarter of what the
framework phases cost, because a boundary is testable without a provider. **On a $0 budget that is
architectural advice, not trivia**, and it belongs in the write-up's conclusions.

### 3.3 The scorecard file

`days/day-63/lab/SCORECARD.md` — this is the published artifact.

```markdown
# Framework scorecard — Mandala, 2026-08-__

**Scored for:** a support-operations system with human approval before external writes,
running on free tiers, maintained by one person.
**Method:** one frozen slice spec, one shared MCP tool layer, one framework-agnostic
acceptance suite, two hours per framework, weights declared before scores.
**Weights:** `weights.md` (unchanged since declaration).

## Totals
| Framework | Weighted total | Rank |
|---|---|---|

## By dimension
<eight tables, each with four rows: score, evidence, M/J>

## Where each framework wins outright
<one line each. If a framework has none, say so plainly -- and check the matrix.>

## Predictions vs. results
| Prediction (Day 59) | Result | Wrong? |
|---|---|---|
**Predictions wrong: _ of _.** <If zero, why should anyone trust this?>

## The five surprises
<from surprises.md, in the words you wrote at the time>

## What this scorecard does NOT measure
<be specific: production scale, team collaboration, non-support domains, paid tiers,
 anything on the out-of-scope list, and the framework versions you did not test>

## What I would choose, and for what
<not "the winner" -- a sentence per framework naming the system it suits>
```

**The last two sections are what make it credible.**

- **"What this does not measure" is the section a reviewer reads first.** Your bake-off used a
  120-word draft on an eleven-ticket fixture, on free models, by one person who already knew the
  domain. **Naming the limits is not modesty, it is the thing that makes the measured parts
  trustworthy.**
- **"What I would choose, and for what"** — the plan's Principle 10 in one section. Four sentences,
  each naming a system rather than declaring a winner. That is the answer an interviewer is actually
  probing for.

---

## §4 AG-29 — the final draft

You have four drafts of `who_owns_the_loop.md`. **Write the fifth today, then diff it against the
first.**

```markdown
# Who owns the loop? — final, with evidence

| Framework | Who owns the loop | Costs | Buys | Best for |
|---|---|---|---|---|
| Agents SDK | the model | 1 turn per decision | adapts to the unanticipated case | |
| CrewAI | roles, or you (Flows) | a choice before you start | two shapes in one library | |
| LangChain | the abstraction | a second library for branching | provider neutrality, testability | |
| LangGraph | you | machinery on small slices | durability, HITL, replay as runtime properties | |

## The interview answer, final
<one paragraph. Then read draft 1 and note what changed.>

## What changed between draft 1 and draft 5, and why
<this is the portfolio artifact. It shows evidence changing a view.>
```

**The diff is the artifact.** Anyone can state the axis after reading the plan's Part 0 — you could on
Day 1. **Being able to show how your own answer moved as measurements arrived is what separates
someone who has used four frameworks from someone who has read about them**, and it is worth a
prominent place on Day 89.

---

## §5 The self-check before publishing

Run through these honestly. **Each one has a specific remedy, not just a warning:**

| Check | If it fails |
|---|---|
| Did one framework win every row? | Find the row you left out. Real tools have trade-offs. |
| Did the weights change after scoring? | Revert them. Note the temptation in the write-up. |
| Is any dimension scored entirely on judgement? | Say so in that dimension's header. |
| Were zero predictions wrong? | Say so, and explain why the reader should still trust it. |
| Does the totals table drive the conclusion? | Rewrite the conclusion from the per-dimension tables. |
| Could a stranger reproduce a single score? | Add the evidence pointer that is missing. |
| Is the "does not measure" section shorter than the totals? | It is too short. |

**The last one is a decent heuristic in general:** a comparison whose limitations section is shorter
than its results section is usually selling something.

---

## §6 Traps

- **Opening the logs before declaring the weights.** Then the weights are a conclusion.
- **Editing weights after seeing totals.** You may criticise a weight in the write-up; you may not
  change it and re-total.
- **A clean sweep.** Go looking for the missing row.
- **Scoring "testing" by feel** when you have four test suites that run without keys. Count them.
- **Scoring free-tier friendliness by impression** when you have nine request numbers.
- **Omitting the M/J column.** It is what stops you sliding from reporting into judging.
- **Skipping "what this does not measure".** It is the section that makes the rest credible.
- **Declaring a winner instead of matching frameworks to systems.** Principle 10.
- **Throwing away the earlier drafts of the interview answer.** The diff is the artifact.
- **Zero wrong predictions, unremarked.** Either the experiment was weak or you are not looking hard
  enough; say which.

---

## §7 Request budget

**Declared: 0 model requests.**

| What | Requests |
|---|---|
| Everything today | **0** |

**Sixth free day**, and the pattern is now unmistakable: **Days 46, 53, 54, 56, 57 and 63 cost nothing
and produced the artifacts you would actually show someone.** Write that observation into
`RATE_BUDGET.md` §2 as a standing note — on a constrained budget, *the days that produce decisions
are free and the days that produce behaviour are expensive*, and knowing which is which is how you
schedule a week.

---

## §8 Verify before you write

Not a code day, but there is still a freshness obligation and one honest check:

- **Are all four implementations still green?** `uv run pytest tests/test_bakeoff.py -v` against each.
  Scoring an implementation that no longer passes is scoring a memory.
- **Are the four `log.md` files complete?** Any blank cell becomes a guess today.
- **Is `prediction.md` untouched since Day 59?** Check `git log` on it. If it was edited, say so.
- **Are the framework versions in `docs/PINS.md` the ones you actually tested?** The scorecard must
  state the versions — a comparison of unnamed versions is undatable and therefore unusable.

---

## §9 Say it in an interview

> "I published a scorecard across eight dimensions, and the two things that make it worth reading are
> procedural. First, I declared the weights before I looked at any score, and the weights are stated
> as being for *my* system — a support-ops tool with a human approval gate, on free tiers, maintained
> by one person — with a section describing what would change them. A scorecard that hides its context
> is propaganda. Second, every score carries its evidence and a marker saying whether it's a
> measurement or a judgement, so a reader can see exactly where I'm reporting and where I'm opining.
> The rows I'd defend hardest are the measured ones: the same routing decision costs one model turn on
> one framework and zero on the other three; the security requirement's *confidence* time varied by
> more than its implementation time; and the protocol phase cost a quarter of what the framework
> phases cost, because a boundary is testable without a provider. I also tracked how many of my
> Day-one predictions were wrong — if the answer had been none, I'd have trusted the experiment less."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 63
```

**Do not read the scorecard again today.** Tomorrow's ADR-003 requires a *cold read* — the plan's
Phase-9 gate says signed "a day later" for exactly this reason. Sleep on it, then review it as a
stranger would.
