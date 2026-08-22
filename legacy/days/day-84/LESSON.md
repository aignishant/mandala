---
day: 84
phase: 12
phase_name: "Capstone build"
title: "Graduated autonomy review + Phase-12 gate"
ids: ["AG-21"]
kind: gate
plan_version: "v1.1.0"
generated: "2026-08-21"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 84 — Graduated autonomy review + Phase-12 gate 🎯

**Phase 12 · Capstone build** · IDs: **AG-21 🅿️** · **Phase-12 gate**

> **Yesterday:** twenty unseen tickets, every write approved by hand, thirty-odd minutes of your
> attention, and a list of rejection reasons.
> **Today:** the question the plan has been building toward since Day 1 — **what is Mandala allowed
> to do without you?** AG-21's answer: start at 100% human review, and let autonomy be *earned* with
> eval evidence, per tool, per agent. Then the Phase-12 gate.
> **Tomorrow:** Phase 13 — deployment and interop, local-first and free.

```bash
./m start 84
./m scaffold 84
```

---

## §1 The story

The plan's AG-21 row is precise, and its example is the whole idea:

> *Start at 100% human review; earn autonomy with eval evidence, per tool, per agent. Example:
> auto-close only for `severity=low` after 4 weeks of clean approvals.*

Three constraints hide in that sentence, and each is a design decision:

1. **Per tool, per agent** — not a global "autonomy level". `post_reply` on a low-severity ticket and
   `post_reply` on a critical one are different risks with the same tool name. Autonomy is granted to
   a **(agent, tool, condition)** triple.
2. **Earned with evidence** — not with confidence, not with elapsed time alone. The evidence is
   yesterday's data: N approvals, zero rejections, zero edits, over a defined window. **A promotion
   rule that a script can evaluate**, or it is a vibe.
3. **Four weeks** — a *duration*, not a count. Twenty clean approvals in one afternoon is a smaller
   claim than twenty across a month, because a month contains variety an afternoon does not.

And the constraint the plan does not state but you should add, because Day 69 taught it:
**demotion must be automatic and must be easier than promotion.** A single bad outcome revokes
autonomy immediately; restoring it requires the full window again. Asymmetry is the entire safety
property. A system where autonomy is hard to gain and easy to lose degrades gracefully; the reverse
degrades into an incident.

**Read `days/day-77/lab/debts.md` before you start.** You wrote "golden labels may be stale — bites
on Day 84 (autonomy review needs trustworthy labels)". Today is that day. If the labels are stale,
the evidence you are about to build a promotion rule on is stale too.

---

## §2 Setup — run this

```bash
touch src/mandala/autonomy/__init__.py
touch src/mandala/autonomy/ladder.py
touch src/mandala/autonomy/evidence.py
mkdir -p days/day-84/lab
touch days/day-84/lab/autonomy_review.md
touch docs/adr/gate-phase-12.md
touch tests/test_autonomy.py
```

No new dependencies. **Nine consecutive days** — worth noting in the ADR: the capstone was built
entirely from what the first eleven phases had already pinned.

---

## §3 AG-21 — the ladder, as data

```python
# src/mandala/autonomy/ladder.py
"""Autonomy is granted to (agent, tool, condition) triples, never globally.

Levels:
  0  REVIEW_ALL     every call goes to a human (where everything starts)
  1  REVIEW_SAMPLE  a fraction sampled for review, the rest auto
  2  AUTO_NOTIFY    automatic, human notified after the fact
  3  AUTO           automatic, audited only

Nothing starts above 0. Nothing skips a level. Demotion goes straight to 0.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Literal

Level = Literal[0, 1, 2, 3]
MAX_LEVEL_EVER: Level = 2          # <- your deliberate ceiling; see §3.1


@dataclass(frozen=True)
class Grant:
    agent: str
    tool: str
    condition: str                 # e.g. "severity == 'low' and confident"
    level: Level
    granted_on: str
    evidence: str                  # a pointer, not a claim: "docs/adr/gate-phase-12.md#autonomy"
    review_by: str


@dataclass(frozen=True)
class Rule:
    """The promotion rule. A script evaluates this; a human does not eyeball it."""

    min_window_days: int = 28
    min_decisions: int = 40
    max_rejections: int = 0
    max_edits: int = 0
    max_verification_failures: int = 0     # invented citations, Day 81
    max_redteam_breaches: int = 0


GRANTS: tuple[Grant, ...] = ()     # empty on Day 84. That is the correct answer today.
```

**Line by line:**

- **`GRANTS` is empty and that is the deliverable.** You have twenty decisions from one afternoon.
  The rule requires forty over twenty-eight days. **You do not qualify, and writing the rule that
  disqualifies you is the entire exercise.** The temptation to grant yourself level 1 "since it's a
  demo" is exactly the failure AG-21 exists to prevent, and a reviewer on Day 89 will notice
  immediately if you did.
- `MAX_LEVEL_EVER = 2` — a ceiling you set now, in code, while you are thinking clearly rather than
  in six months while you are tired of approving things. Level 3 (fully automatic, audited only) for
  a customer-facing irreversible write is a decision that needs more than a passing eval rate.
  **Write your reasoning in the docstring.**
- `evidence` is a **pointer to a document**, not a number copied into the grant. Numbers copied into
  a config drift from the runs that produced them; a pointer stays honest.
- `review_by` — every grant expires. An autonomy grant with no expiry is a permanent decision made
  with temporary evidence.
- `condition` as a string is a deliberate simplification with a real risk: it must be evaluated
  somewhere, and `eval()` on it would be absurd. §3.2 handles this with a small registry.
- `min_decisions=40` and `max_rejections=0`: **zero, not "few".** At level 0 with twenty samples you
  cannot distinguish a 2% failure rate from a 10% one, so demanding perfection over a larger sample
  is the only statistically honest bar you can set. Say that out loud in the review doc — it is a
  better answer than a made-up threshold.

### 3.1 The condition registry

```python
CONDITIONS: dict[str, callable] = {
    "severity == 'low' and confident": lambda s: s["severity"] == "low" and s["draft"]["confident"],
    "severity == 'low'": lambda s: s["severity"] == "low",
}


def resolve(condition: str):
    if condition not in CONDITIONS:
        raise KeyError(f"unknown autonomy condition {condition!r} — add it deliberately")
    return CONDITIONS[condition]
```

**Line by line:**

- A **closed registry**, and an unknown condition raises. The alternative — parsing or `eval`-ing the
  string — means an autonomy condition could be introduced by anything that can write a config, and
  that is a privilege-escalation channel in the one subsystem where you least want one.
- Note that `"severity == 'low' and confident"` is strictly narrower than `"severity == 'low'"`. Start
  with the narrower one. **Widening later is a decision; starting wide is a habit.**

### 3.2 The gate, wired

```python
# in approve_node, before interrupt():
grant = active_grant(agent="resolver", tool="post_reply", state=state)
if grant and grant.level >= 2:
    a = Approval(run_id=state["run_id"], draft_hash=resolution.content_hash,
                 decided_by=f"auto:{grant.condition}", decided_at=now(),
                 decision="approve", reason=f"autonomy level {grant.level}")
    record(a)
    return {"approval": asdict(a), "notes": [f"auto-approved under {grant.condition}"]}
```

**Line by line:**

- **The auto-approval still writes an `Approval` record**, with `decided_by="auto:<condition>"`. Day
  83's audit therefore keeps working unchanged, and every automatic write is as traceable as a manual
  one. **If autonomy bypassed the record, you would have destroyed your own audit trail on the day
  you granted it** — which is how this goes wrong in real systems.
- `grant.level >= 2` — level 1 (sample) needs sampling logic; write it when you have a level-1 grant,
  not before. Do not build the ladder you have no evidence to climb.
- The code path is **the same** for auto and human approval: same record, same `check()`, same write.
  Sixth application of the chokepoint pattern, and the reason it is safe to add autonomy at all.

---

## §4 The review — evidence, not feelings

Write `days/day-84/lab/autonomy_review.md` with **four sections**, using yesterday's data:

**1. What actually happened.** From Day 83: 20 tickets, N approved unchanged, M edited, K rejected,
total human minutes, minutes by severity band. **Numbers only.**

**2. Rejection analysis.** Every rejection reason, grouped. This is the highest-value part. Typical
groupings: *tone wrong*, *missed the real question*, *citation technically valid but irrelevant*
(Day 81's known limit, appearing in the wild), *escalation needed and not flagged*. **Each group is a
candidate autonomy blocker or a candidate new eval.** Convert at least one into a rubric line today.

**3. The rule, and whether you meet it.** State `Rule` in prose, then the honest answer: **no**.
20 decisions, one day, not 40 over 28. Write the sentence "Mandala remains at level 0 for every tool"
and mean it.

**4. What would change the answer.** Concretely: run the pipeline on real-ish traffic for four weeks;
require zero rejections *and* zero verification failures; re-check kappa (Day 72) since the judge is
part of the evidence chain; re-pin the golden baseline. **Give it a date.**

**Line by line on why this document matters:** it is the artifact that most distinguishes a portfolio
from a demo. Anyone can show an agent that works. Showing a written, evidence-based argument for why
you have *not* let it act alone yet — with the rule that would change your mind — is a much rarer
thing, and it is the honest state of essentially every agent system in production today.

---

## §5 The Phase-12 gate

```bash
uv run pytest -m "eval_unit or eval_trajectory" -q     # everything offline
uv run python scripts/audit_writes.py                  # exit 0
uv run python scripts/eval_gate.py                     # exit 0
uv run python scripts/daily_report.py
uv run python scripts/gen_permission_table.py --check
```

`docs/adr/gate-phase-12.md`:

```markdown
# Gate — Phase 12 (Capstone build)

Date: 2026-__-__ · Days 78–84 · Reviewer: me (cold read: +1 day)

| Criterion (plan Part 5) | Evidence | Verdict |
|---|---|---|
| End-to-end demo on 20 unseen tickets | `tests/fixtures/unseen/`, disjoint-set test green, run log | |
| Eval suite green | `pytest -m "eval_unit or eval_trajectory"`, `eval_gate.py` exit 0 | |
| Zero unapproved external writes in the trace log | `audit_writes.py` exit 0, N writes, 3 records crossed | |

## Autonomy decision
Level 0 for every (agent, tool) pair. Rule: `days/day-84/lab/autonomy_review.md`. Next review: ____

## What broke during the unseen run, and what I changed
…
## What I would still not deploy, and why
…
## Debts carried into Phase 13
(from days/day-77/lab/debts.md, updated)
```

**Line by line:**

- The middle criterion's evidence names **three crossed records**, not "the audit passed". Evidence
  is specific or it is decoration.
- "What broke during the unseen run" is mandatory and is the section a reviewer reads first. A
  capstone where nothing broke on twenty unseen tickets means the tickets were too easy.
- **Third gate ADR with a "what I would still not deploy" section** (Days 70, 77, 84). That
  consistency is itself a portfolio signal.
- Freshness sweep, `git tag -a phase-12-complete`, and **cold read tomorrow**. Same discipline as
  every gate.

---

## §6 The eval that must be able to fail

```python
# tests/test_autonomy.py
import pytest

from mandala.autonomy.ladder import GRANTS, MAX_LEVEL_EVER, Grant, Rule, resolve

pytestmark = pytest.mark.eval_unit


def test_everything_starts_at_level_zero():
    """The day's headline. Flip it: grant yourself level 1 'for the demo'."""
    assert GRANTS == ()


def test_no_grant_may_exceed_the_ceiling():
    for g in GRANTS:
        assert g.level <= MAX_LEVEL_EVER


def test_every_grant_has_an_expiry_and_an_evidence_pointer():
    for g in GRANTS:
        assert g.review_by and g.evidence.startswith(("docs/", "days/"))


def test_the_promotion_rule_demands_zero_rejections():
    r = Rule()
    assert r.max_rejections == 0 and r.max_edits == 0 and r.max_verification_failures == 0


def test_the_rule_requires_a_window_not_just_a_count():
    assert Rule().min_window_days >= 28


def test_yesterdays_evidence_does_not_meet_the_rule():
    """20 decisions in one day. Encodes the honest answer so nobody quietly softens it."""
    r = Rule()
    assert not (20 >= r.min_decisions and 1 >= r.min_window_days)


def test_an_unknown_condition_raises():
    with pytest.raises(KeyError):
        resolve("severity != 'critical'")


def test_conditions_are_a_closed_registry_not_evaluated_strings():
    import inspect

    from mandala.autonomy import ladder

    assert "eval(" not in inspect.getsource(ladder)


def test_auto_approval_still_writes_an_approval_record():
    """Flip it: let autonomy skip the record and the Day-83 audit silently stops working."""
    import inspect

    from mandala.organs import approval

    src = inspect.getsource(approval.approve_node)
    assert "auto:" in src and "record(" in src


def test_demotion_goes_straight_to_zero():
    from mandala.autonomy.ladder import demote

    g = Grant("resolver", "post_reply", "severity == 'low'", 2, "2026-01-01", "docs/x", "2026-02-01")
    assert demote(g).level == 0


def test_the_golden_labels_were_rechecked_today():
    """The Day-77 debt. Flip it: skip it and today's evidence rests on stale ground truth."""
    import pathlib

    review = pathlib.Path("days/day-84/lab/autonomy_review.md").read_text(encoding="utf-8")
    assert "label" in review.lower()
```

**Line by line:**

- `test_everything_starts_at_level_zero` is the day's headline, and its flip-it is the exact
  self-deception AG-21 exists to prevent.
- `test_yesterdays_evidence_does_not_meet_the_rule` **encodes the honest answer as a test.** If a
  future you softens the rule to qualify, this goes red and forces the softening to be deliberate.
- `test_conditions_are_a_closed_registry_not_evaluated_strings` greps for `eval(` — crude, correct,
  and guarding a genuine privilege-escalation channel.
- `test_auto_approval_still_writes_an_approval_record` protects the audit trail on the exact day it
  is most at risk.
- `test_demotion_goes_straight_to_zero` encodes the asymmetry that is the whole safety property.

---

## §7 Traps

- **A global autonomy level.** Same tool, different risk, per condition.
- **Granting yourself level 1 "for the demo".** The reviewer will notice; so will you, later.
- **Elapsed time or count alone.** You need both, and a window contains variety a day does not.
- **"Few" rejections instead of zero.** With 20 samples you cannot tell 2% from 10%.
- **Symmetric promotion and demotion.** Easy to lose, hard to gain — never the reverse.
- **Autonomy that skips the approval record.** You destroyed your audit trail.
- **Evaluated condition strings.** A config that can grant privileges.
- **A grant with no expiry.** Permanent decision, temporary evidence.
- **Numbers copied into the grant** instead of a pointer to the run that produced them.
- **Building level-1 sampling before you have a level-1 grant.**
- **Skipping the Day-77 label debt.** Your evidence rests on it.
- **A gate ADR where nothing broke.** The tickets were too easy.

---

## §8 Request budget

**Declared: ~10 model requests — a review day, not a build day.**

| What | Requests |
|---|---|
| All tests, the review doc, the audit, the report | **0** |
| Re-running any ticket whose rejection you want to re-examine | ≤ 10 |

**The whole Phase-12 gate is verifiable for roughly nothing.** Every criterion — the disjoint-set
test, the eval suite, the write audit, the permission-table drift check — is deterministic. Note it
in the ADR beside the Phase-10 and Phase-11 observations: **three consecutive gates passed on
deterministic evidence.** That is the strongest single claim this repo makes.

---

## §9 Verify before you code

Written **2026-08-21**:

- **Re-check the judge's kappa** (Day 72) — it is part of the evidence chain for any future autonomy
  grant, and if it drifted, so did every outcome score.
- **Golden labels**: sample five and ask whether you would still label them that way. The Day-77 debt.
- **Re-pin the baseline** if labels changed — in its own commit (Day 73's rule).
- **Does your approval CLI record *edits*** as distinct from approvals? The rule needs `max_edits`,
  and if the CLI only offers approve/reject you cannot measure it. **Add it today** or drop the field
  honestly.
- **`Literal` with int members** (`Level`) — confirm it behaves as expected in your type checker.
- **Full `/freshness` sweep** for the gate.

---

## §10 Say it in an interview

> "The last day of the capstone was deciding what the system is allowed to do without me, and the
> answer was: nothing, yet — and writing the rule that produced that answer was the point. Autonomy
> is granted to an agent-tool-condition triple rather than as a global level, because posting a reply
> on a low-severity ticket and on a critical one are different risks with the same tool name. The
> promotion rule is machine-evaluable: forty decisions over twenty-eight days with zero rejections,
> zero edits and zero citation-verification failures. I had twenty decisions in one afternoon, so I
> don't qualify, and I have a test that encodes that — if a future version of me softens the rule to
> qualify, it goes red and the softening has to be deliberate. Demotion is asymmetric: one bad
> outcome drops straight to zero and you re-earn the whole window, because a system where autonomy is
> hard to gain and easy to lose degrades gracefully and the reverse degrades into an incident. The
> implementation detail I'd defend most: an auto-approval still writes the same approval record a
> human would, with `decided_by` set to `auto:<condition>`, so the write audit keeps working
> unchanged — if autonomy had bypassed the record, I'd have destroyed my own audit trail on the day
> I granted it. And the most useful artifact isn't the ladder, it's the rejection analysis: the
> reasons I rejected drafts became rubric lines, so the thing that blocked autonomy also became the
> evidence that could eventually unblock it."

---

## §11 Done when

```bash
./m check
./m done 84
```

Phase 12 closes here. **Cold-read `docs/adr/gate-phase-12.md` tomorrow before Day 85.**
