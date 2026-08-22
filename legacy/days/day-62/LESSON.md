---
day: 62
phase: 9
phase_name: "The bake-off"
title: "Bake-off IV — the slice on LangGraph"
ids: []
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 62 — Bake-off IV: the slice, on LangGraph

**Phase 9 · The bake-off 🥇** · IDs: none — the slice is the artifact

> **Yesterday:** LangChain, three fresh conversations, and a declined answer recorded as a finding.
> **Today:** the last implementation, and the one you expect to win — which is precisely why today
> needs the most discipline. Same two hours, same tests, same server, and **the out-of-scope list
> matters more today than on any other day**, because this is the framework that makes the excluded
> capabilities free.
> **Tomorrow:** the scorecard.

```bash
./m start 62
./m scaffold 62
```

---

## §1 The story

**The plan told you the expected outcome on Day 1** and flagged it as *"expected — but not
presumed"*. Today is the day that flag earns its keep, because three things are all true at once:

1. LangGraph is genuinely well suited to a workflow with a branch.
2. You have spent ten days on it, more recently than on any other framework except MCP.
3. You want it to win.

**Only the first is evidence.** The other two are the confounds Day 59 §2.4 set up defences against,
and today is when they bite hardest. Three specific disciplines:

- **The out-of-scope list is binding.** Persistence, approvals, streaming and retries are all *one
  line each* in LangGraph — Days 47, 50, 45 and 49. **Building any of them today would mean scoring
  a capability three implementations do not have.** The temptation is real and it is the single most
  likely way to corrupt the bake-off.
- **The timebox is binding.** Finishing early is a result; using the spare time to polish is not.
- **The comparison is like-for-like.** If LangGraph passes 8/8 while the SDK passed 6/8, **the
  interesting question is which two and why**, not the totals.

**And there is a real counter-case to hold open.** The slice is small. Yesterday LangChain expressed
the security requirement with three fresh conversations and no machinery at all. Today you will write
a state schema, reducers, node functions and edges to do the same thing. **On a slice this size, that
may be more code for the same result** — and Day 51 §4.3 already made you write that conclusion once,
about the Functional API. If today reproduces it, **say so.**

---

## §2 The build

### 2.1 What you already have

- `src/mandala/graph/` — state and reducers, routing, fan-out, subgraphs, supervisor, policy,
  approval, timetravel, and `core.py`'s `build_core()` (Days 43–52)
- The MCP mount via `langchain_mcp_adapters` (Day 55)

**You have more foundation here than anywhere else**, and that is itself a confound worth naming in
the log: *"I had a `build_core()` to start from and no equivalent for the SDK."* **A fair scorecard
mentions it.**

### 2.2 `src/mandala/bakeoff/graph_slice.py`

```python
"""The slice, on LangGraph. Two hours, hard stop. Same contract.

DISCIPLINE NOTE -- read before starting:
    Persistence, approvals, streaming and retries are ONE LINE EACH here. They are
    out of scope in all four implementations. Building them today would score a
    capability three other implementations do not have, which is the fastest way to
    make this whole phase worthless.

    If the timer rings early, STOP. Finishing early is a result.

Shape:
    StateGraph(SliceState)
      fetch -> triage -> scrub -> [conditional edge] -> escalate | research -> draft
    research is a SUBGRAPH with its own schema (Day 48).

Rule 3: a conditional edge. My code, zero model turns -- same as CrewAI's @router
and LangChain's plain `if`. Three of the four cost nothing; only the SDK's handoff
costs a turn. That is the cleanest single row in the scorecard.

Rule 6: the drafting node is not given the field. Two mechanisms, and note that
today is the only day I get to choose:
    - scrub node before the lanes (Day 52's core.py placement), OR
    - a subgraph state schema that simply lacks ticket_body (Day 48)
The second is stronger: it is an absence, not a deletion, so ordering stops
mattering. Time BOTH understandings, not just the typing.
"""

from __future__ import annotations

from tests.test_bakeoff import SliceResult


def run_slice(ticket_id: str) -> SliceResult:
    ...
```

**Line by line:**

- **The discipline note goes at the top of the file, not in your head.** You will read it when you are
  two-thirds through with spare time and an idea about checkpointers.
- **Rule 3 as a conditional edge**, and the docstring already does the cross-day arithmetic: three of
  four cost zero turns, one costs one. **That row is finished today** and it is the cleanest thing in
  the scorecard because it is a per-ticket number rather than a judgement.
- **Rule 6 has two mechanisms here and only here.** Note the difference precisely: the scrub node is
  *deletion at the right moment* (CrewAI's answer with better placement); the subgraph schema is
  *absence by construction* (LangChain's fresh-conversation answer with a type behind it). **Use the
  subgraph.** Then record that this framework was the only one that offered a choice of security
  mechanism — which is either expressive power or unnecessary optionality, and Day 63 has to decide
  which.
- **"Time BOTH understandings"** — writing the schema is fast; being confident that nothing else can
  reach the field required a `test_the_mapping_is_an_allowlist_not_a_filter` on Day 48. **Confidence
  time, third day running**, and today it should be the lowest of the four. If it is, that is your
  strongest single result.

### 2.3 Where the timebox will go

1. **State schema and reducers.** Real cost, and it is front-loaded: you write `SliceState`,
   `Annotated` reducers, and the subgraph's schema before anything runs. **Record the minutes before
   the first passing test** — that is the "time to first green" metric and LangGraph will lose it.
2. **The subgraph mapping.** `to_research` / `from_research` (Day 48). Small, and it is the security
   boundary.
3. **Counting model calls.** Easiest of the four: nodes are explicit, so `notes` already carries the
   turn count if you kept Day 42's seam habit. **Record that it was easy** — observability being cheap
   is a real property.

### 2.4 The thing to be honest about

**Write this into `log.md` while the timer runs, not afterwards:**

```markdown
## The fairness ledger for today
- Foundation I started from: __ (build_core, state, reducers, subgraph, routing)
- Foundation the SDK day started from: __
- Days since I last used this framework: __ (vs. __ for the SDK)
- Out-of-scope capabilities I was tempted to build: __
- Did I stop when the timer rang?
- Lines of code, excluding what I reused: __
```

**"Lines of code, excluding what I reused" is the number that matters** and it is the one that will
flatter LangGraph least. Compute it honestly for all four on Day 63.

---

## §3 What to compare, today — the completed table

| Question | SDK (59) | CrewAI (60) | LangChain (61) | LangGraph (62) |
|---|---|---|---|---|
| Model turns for the routing decision | 1 | 0 | 0 | **0** |
| How rule 6 is expressed | separate context | deletion | fresh conversation | **absence in a schema** |
| Minutes until you trusted rule 6 | | | | |
| Minutes to first passing test | | | | |
| Lines of new code | | | | |
| Lines of output parsing | | | | |
| Escape hatches reached for | | | | |
| Requirements passing at the buzzer | | | | |
| Model calls for one run | | | | |
| Could a hidden call inflate the count? | | | | |
| Needed a second library for control flow | no | no | **yes** | no |
| Offered a choice before I could start | no | **yes** | no | **yes (rule 6)** |
| Observability of my own request count | | | | |

**Fill every cell today.** Tomorrow's scorecard turns this into weighted judgements, and a cell you
leave blank tonight becomes a guess tomorrow.

---

## §4 Traps

- **Building persistence, approvals, streaming or retries.** One line each, and out of scope in all
  four. **This is the trap of the day.**
- **Polishing with spare time.** Finishing early is the result; polishing destroys it.
- **Not recording the foundation you started from.** You had `build_core()`; the SDK day had less.
- **Comparing totals instead of asking which requirements failed and why.**
- **Using the scrub node** when the subgraph schema is available and stronger. Then recording it as if
  you had no choice.
- **Not noticing that having a choice of security mechanism is itself a scorecard row.**
- **Recording write-time instead of confidence-time for rule 6.** Third day; still true.
- **Leaving cells blank in §3.** Tomorrow they become guesses.
- **Concluding LangGraph won before counting lines of new code.** That number is the counter-case.

---

## §5 Request budget

**Declared: ~12 model requests, Groq.**

| What | Requests |
|---|---|
| Acceptance tests against a recorded result | **0** |
| Iterating during the timebox | ~7 |
| Three final runs (normal, critical, unclassifiable) | ~12 |

**Expect the lowest of the four.** Zero-turn routing, no crew, no middleware surprises, and explicit
nodes mean nothing runs that you did not draw. **If it is not the lowest, find out why before
tomorrow** — an unexplained request count in the framework with the most explicit control flow would
be a genuinely interesting finding.

**Phase 9's four build days total should land near 60 requests.** Log it; Day 63 wants the phase total
alongside Phases 5, 6, 7 and 8.

---

## §6 Verify before you code

- **`ticket-db` running**; the LangGraph mount re-verified.
- **`langgraph==1.2.11`** still pinned and installed.
- **Model-call counting** — the `notes` turn-count habit from Day 42, still in place.
- **`build_core()` still green** after Phase 8 — you are reusing pieces of it, and starting the timer
  on a broken foundation would measure your debugging rather than the framework.

---

## §7 Say it in an interview

> "The framework I expected to win was the one I built last and had used most recently, which is two
> confounds pointing the same way — so the discipline that mattered on the final day was the
> out-of-scope list. Persistence, human approval, streaming and retries are one line each in
> LangGraph, and building any of them would have scored a capability the other three implementations
> didn't have. The result I'd actually lead with is the routing row: the same critical-ticket branch
> costs one model turn on the Agents SDK, where the model decides to hand off, and zero in the other
> three, where it's my code — that's a per-ticket cost rather than an opinion. And the honest
> counterweight is lines of new code: on a slice this small, writing a state schema, reducers, nodes
> and edges to express what three fresh conversations expressed for free is more machinery for the
> same result. The graph earns that machinery the moment you want durability or a human pause — but
> those were out of scope, so on this slice it doesn't get credit for them."

---

## §8 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 62
```

Tonight, before Day 63: **collect all four `log.md` files, `surprises.md`, `prediction.md`, the four
drafts of `who_owns_the_loop.md`, and §3's completed table into one folder.** The scorecard is
tomorrow's only job and it should be synthesis, not archaeology.
