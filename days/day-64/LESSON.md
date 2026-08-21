---
day: 64
phase: 9
phase_name: "The bake-off"
title: "ADR-003 — capstone architecture + approval-gate design"
ids: ["LG-24", "AG-20"]
kind: gate
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 64 — ADR-003: the capstone architecture, and the approval gate

**Phase 9 · The bake-off 🥇** · IDs: **LG-24 🛠️**, **AG-20 🛠️** · **🎯 gate day**

> **Yesterday:** the scorecard, published, with weights declared before scores — and you did not
> re-read it.
> **Today:** the **cold read**, then the decision. ADR-003 commits Mandala's capstone architecture and
> designs the approval gate that Phase 12 will build on. This is the most consequential document in
> the plan: **Days 78–90 execute it.**
> **Tomorrow:** Phase 10 opens and you start attacking what you just designed.

```bash
./m start 64
./m scaffold 64
```

---

## §1 The cold read — do this before anything else

The plan's Phase-9 gate: *"published scorecard; **ADR-003 signed by you-as-reviewer a day later (cold
read)**."*

**That parenthesis is a method, not a formality.** Yesterday you were the author, invested and tired.
Today you are the reviewer, and the point is to catch what the author could not see.

Read `SCORECARD.md` end to end **before writing anything**, with one job: find the weak parts.

```markdown
# days/day-64/lab/cold_read.md — written BEFORE ADR-003

## Three claims I would challenge if someone else wrote this
1.
2.
3.

## The dimension whose scoring I now think is wrong, and why

## Where I slid from measurement into judgement without marking it

## What a reader who disagreed with my weights would conclude instead
<run the arithmetic with a plausible alternative weighting. Does the ranking change?
 If it does not, that is a strong result. If it flips easily, the conclusion is fragile
 and the ADR must say so.>

## Am I still comfortable with the conclusion?
```

**The alternative-weighting arithmetic is the most valuable ten minutes of the day.** Take the weights
a *different* engineer would plausibly choose — someone optimising for team velocity, say, or for a
paid tier with no rate limits — and re-total. **If the ranking survives, your conclusion is robust and
you can say so with evidence. If it flips on a small change, your architecture decision is
finely balanced, and an ADR that admits that is far more useful than one that does not.**

**Do not edit the scorecard today.** If the cold read finds a real error, note it in `cold_read.md`
and reference it from the ADR. **A scorecard amended by its own author after seeing the conclusion is
worth nothing**, and the discipline is the same one that made you declare weights first.

---

## §2 LG-24 — the architecture decision

### 2.1 What the plan expects, and what it explicitly does not presume

Part 5's Phase 9: *"Expected — but not presumed — outcome: LangGraph spine · Agents SDK specialist(s)
where hosted tools/sandbox win · a CrewAI crew as one subgraph organ · LangChain as the model/tool
lingua franca · everything behind MCP."*

**Two obligations follow, and they pull in opposite directions:**

1. **If your evidence agrees, say so — and say what would have changed your mind.** Agreement with a
   prediction is only meaningful if the prediction was falsifiable.
2. **If your evidence disagrees, follow the evidence.** The plan says "not presumed" in writing. **An
   ADR that contradicts the plan's expectation, with measurements attached, is a better artifact than
   one that confirms it** — and it is the strongest possible demonstration that you ran a real
   comparison.

### 2.2 `docs/adr/ADR-003-capstone-architecture.md`

The plan's most important ADR. Use the repo's template and cover these.

```markdown
# ADR-003 — Mandala's capstone architecture

Status: accepted · Date: 2026-08-__ · Reviewer: me, cold-read on 2026-08-__
Supersedes: nothing · Informs: Days 78-90

## Context
<the bake-off in three sentences: what was measured, how, and where SCORECARD.md is>

## Decision
| Component | Framework | Why (cite a scorecard row) |
|---|---|---|
| The spine | | |
| Research organ | | |
| Model/tool layer | | |
| Data boundary | | |
| Specialist agents | | |

## The evidence that decided it
<three rows from the scorecard, with numbers. Not eight -- three. If you cannot get
 to three decisive rows, the decision is weaker than it looks and you should say so.>

## What would have changed this decision
<be specific and falsifiable: "if durability had not mattered", "if the slice had had
 no branch", "if I had a team of five". At least one must be a condition that is
 plausibly true for someone else.>

## The counter-case, stated at its strongest
<Day 62's finding: on a small slice, the winner needed the MOST new code for the same
 result. State it in the form its strongest advocate would use, then answer it.>

## Consequences
- For Phase 10 (safety):
- For Phase 11 (evals):
- For Phase 12 (capstone):
- For Phase 13 (deployment):
- What I now cannot easily change:

## Risks I am accepting
| Risk | Likelihood | What I would do about it |
|---|---|---|

## Review trigger
<what event would make me reopen this? name one, with a date or a condition.>
```

**Line by line on the sections that carry the weight:**

- **"The evidence that decided it" is capped at three rows on purpose.** Eight rows of supporting
  evidence usually means none of them was decisive and the decision was made another way. **Three
  forces you to identify what actually moved you** — and if you cannot, that is a finding about your
  own reasoning worth writing down.
- **"What would have changed this decision" must be falsifiable and at least one condition must be
  plausibly true for someone else.** "If LangGraph had been bad" is not a condition. "If the workflow
  had no branch, three fresh `create_agent` calls would have been enough" is — and it is true for
  plenty of real systems.
- **"The counter-case, stated at its strongest"** is the section that separates an ADR from an
  advertisement. Day 62 measured that the expected winner needed the most new code for the same
  result on this slice. **Steelman it: *"you have written a state schema, reducers, nodes and edges to
  do what three fresh conversations did for free, and you are justifying it with capabilities you
  deliberately excluded from the test."*** Then answer it — the honest answer is about the *next*
  thirty days, not this slice, and saying that plainly is stronger than pretending the counter-case is
  weak.
- **"What I now cannot easily change"** is the section future-you will actually read. Name the things
  that get expensive: the state schema shape, the MCP boundary, the approval record format.
- **"Review trigger"** — an ADR with no reopening condition is a decision that will silently expire.
  *"Reopen if the capstone exceeds N nodes"* or *"reopen at the Day-90 retrospective"* both work.

---

## §3 AG-20 — the approval-gate design

The gate's second half, and it is a **design**, not an implementation. Phase 12 builds it; today
specifies it.

### 3.1 Everything you already know

Four implementations (Days 21, 33, 39, 50) and one record (Day 33's `Decision`, imported unchanged by
Day 50 across a framework boundary). **The mechanism question is settled — `interrupt()` — and the
interesting questions are the ones no framework answers.**

### 3.2 `docs/adr/ADR-003a-approval-gate.md`

```markdown
# ADR-003a — the approval gate

## The rule (Principle 12)
No external side effect without a human decision, until Day 84's graduated-autonomy review.

## What is gated
| Action | Gated? | Why |
|---|---|---|
| post a reply to a customer | **yes** | external, irreversible |
| close a ticket | | |
| internal note | | |
| escalate to a human | **no** | a human already has it (Day 33 §3.3) |
| any read | **no** | Principle 6: read-only by default |

## The record
`Decision` (Day 33), unchanged: outcome (approve/reject/edit), reviewer, reason,
edited_text, decided_at. Bound to a run id AND a proposal fingerprint (Day 50).

## The mechanism
`interrupt()` + `Command(resume=...)`, checkpointed. Resume costs 0 model requests.

## The questions no framework answers -- decide them HERE
1. **Timeout.** What happens to a proposal nobody reviews for 24h? (Day 32's staleness
   bound says the checkpoint expires. Then what -- auto-escalate? drop? re-notify?)
2. **Who may approve?** Today `reviewer="me"`. What is the check when there are two
   people, and where does it live -- the token's scopes (Day 56)?
3. **Batch approval.** 20 tickets, one reviewer. One decision for all, or 20?
   What does that do to the fingerprint binding?
4. **Revocation.** Approved, not yet sent, reviewer changes their mind. Is there a
   window, and how long?
5. **What if the reviewer never comes back?** The failure mode nobody designs for.

## The audit trail
<what a compliance reader needs: who, what, when, why, and what was actually sent --
 and note that `final_text()` (Day 33) is why "what was approved" and "what was sent"
 can be proven identical.>

## What is deliberately NOT designed today
<graduated autonomy is Day 84 (AG-21). Say so, so nobody builds it early.>
```

**Line by line:**

- **The gated/not-gated table is the whole spec**, and the two `no` rows matter as much as the `yes`
  rows. Day 33 established that gating an escalation teaches people to click through gates; **a gate
  that fires when there is no decision to make destroys the gate that matters.**
- **The five questions are the day's real work**, and the reason is that **no framework answers any of
  them.** `interrupt()` gives you a durable pause. It has no opinion about timeouts, authorisation,
  batching, revocation, or an absent reviewer. **That gap is where production systems fail**, and
  designing it now — on a quiet gate day — is enormously cheaper than discovering it in Phase 12.
- **Question 1 is the one to answer most carefully**, because it interacts with a decision you already
  made: Day 32's `MAX_CHECKPOINT_AGE_HOURS = 24`. A proposal older than that has a stale checkpoint.
  **So "nobody reviewed it for 24h" is not a hypothetical — it is a guaranteed event** and your system
  currently has no defined behaviour for it.
- **Question 3 is the one with a hidden trap.** Day 50 bound each decision to a fingerprint of *its*
  draft. A single decision covering twenty drafts cannot carry twenty fingerprints. **Either batch
  approval means twenty `Decision` records with one UI action, or the binding weakens.** Pick, and say
  which.
- **Question 5 is the one nobody designs.** The answer can be "the ticket escalates to a second
  reviewer after N hours" or "it expires and re-enters the queue" — but *"the flow waits forever"* is
  a decision too, and an undocumented one is a bug waiting to be discovered by a customer.

---

## §4 The evidence table

| # | Claim | Proved by | ✓ |
|---|---|---|---|
| 1 | The scorecard is published | `days/day-63/lab/SCORECARD.md` | ⬜ |
| 2 | Weights were declared before scores | `weights.md` + `git log` | ⬜ |
| 3 | **A cold read happened, a day later** | `cold_read.md`, dated | ⬜ |
| 4 | The conclusion survives an alternative weighting — or is stated as fragile | `cold_read.md` | ⬜ |
| 5 | ADR-003 names a framework per component, each citing a scorecard row | ADR-003 | ⬜ |
| 6 | **The decision cites exactly three decisive rows** | ADR-003 | ⬜ |
| 7 | Falsifiable change-my-mind conditions, one plausible for someone else | ADR-003 | ⬜ |
| 8 | **The counter-case is stated at its strongest, then answered** | ADR-003 | ⬜ |
| 9 | A review trigger exists | ADR-003 | ⬜ |
| 10 | The gated/not-gated table is complete, including the `no` rows | ADR-003a | ⬜ |
| 11 | **All five unanswered questions are decided** | ADR-003a | ⬜ |
| 12 | Graduated autonomy is explicitly deferred to Day 84 | ADR-003a | ⬜ |
| 13 | All four bake-off implementations still green | `pytest tests/test_bakeoff.py` | ⬜ |
| 14 | Pins re-verified; drift logged or nil-reported | `docs/CHANGELOG_PLAN.md` | ⬜ |

**Row 6 is the one to be strict about.** If you cannot name three decisive rows, do not pad it — write
*"the decision rested on two rows plus a judgement about the next thirty days"* and say which. That
sentence is more useful than a list.

---

## §5 The standing gate freshness check

```bash
for p in openai-agents crewai langchain langgraph mcp; do
  printf "%-18s " "$p"
  curl -s --max-time 30 "https://pypi.org/pypi/$p/json" \
    | python -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
done
```

- Compare against `docs/PINS.md`. Patch → pin and log. Minor/major → **addendum first**.
- **Today's check has a twist worth noticing.** The scorecard names versions, and a scorecard is only
  valid for the versions tested. **If a framework moved a minor version today, your scorecard's
  conclusion has a stated expiry** — and that belongs in ADR-003's review trigger. *"Reopen if any
  framework in the comparison moves a minor version"* is a defensible trigger and it makes the ADR
  self-maintaining.
- MCP spec revision: check.
- Nil report: **write it down.** Day 58 graded this; every gate from here does too.

---

## §6 Traps

- **Writing the ADR before the cold read.** The parenthesis in the gate sentence is the method.
- **Editing the scorecard after seeing the conclusion.** Note errors in `cold_read.md` instead.
- **Skipping the alternative-weighting arithmetic.** It is ten minutes and it tells you whether your
  decision is robust or finely balanced.
- **Confirming the plan's expectation without saying what would have changed your mind.**
- **Padding "the evidence that decided it" to eight rows.** Three, or an honest admission.
- **A weak counter-case.** Steelman it or leave it out; a strawman is worse than nothing.
- **No review trigger.** The decision expires silently.
- **Gating the escalation path.** Teaches people to click through gates.
- **Leaving the five approval questions to Phase 12.** They are cheap today and expensive later.
- **Answering question 1 without checking Day 32's 24-hour bound.** They interact, and the interaction
  is a guaranteed event.
- **Designing graduated autonomy.** Day 84. Say so, so nobody builds it early.

---

## §7 Request budget

**Declared: ~4 model requests, Groq.**

| What | Requests |
|---|---|
| Cold read, ADRs, freshness check | **0** |
| Re-running the four bake-off implementations for row 13 | ~4 (one each, smoke only) |

**Phase 9 total: roughly 65 requests across six days** — four expensive build days and two free
decision days. **Put the phase total in ADR-003 alongside Phases 5–8.** The pattern across five
phases is now a documented property of this project and it is the empirical backing for the free-tier
scorecard row.

---

## §8 Say it in an interview

> "The bake-off ended with an architecture decision record, and the process mattered as much as the
> conclusion. I published the scorecard one day and signed the ADR the next, deliberately cold, and the
> first thing I did as reviewer was re-run the totals with a *different* engineer's plausible weights
> — someone optimising for team velocity rather than free-tier limits — to see whether my ranking
> survived. If a conclusion flips on a small change in weighting, the ADR needs to say it's finely
> balanced. I capped 'the evidence that decided it' at three rows, because eight rows of support
> usually means none of them was decisive. And I wrote the counter-case at its strongest: on the slice
> I actually measured, my chosen spine needed the most new code for the same result, and I was
> justifying it with durability and human-pause capabilities I'd deliberately excluded from the test.
> The honest answer is that the decision is about the next thirty days rather than this slice — and
> saying that plainly is stronger than pretending the objection is weak. The second half was the
> approval gate, and the design work there was entirely in the questions no framework answers: what
> happens to a proposal nobody reviews before its checkpoint goes stale, who may approve when there
> are two people, whether a batch decision is one record or twenty given that each decision is bound
> to a hash of its own draft, and what happens if the reviewer never comes back. A durable pause is a
> mechanism; those five answers are the actual policy."

---

## §9 Done when

Phase 9 is complete when every row in §4 is green and both ADRs are signed.

```bash
./m check
./m done 64
```

Then read Day 65's §1. **Phase 10 opens by attacking what you just designed** — prompt injection and
the lethal trifecta — and the first thing it will test is the seam you have carried since Day 31: the
research organ receives a *model-written summary* of untrusted text, and you have flagged it as "still
Day 65's problem" three separate times. **Tomorrow it stops being deferred.**
