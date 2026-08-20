---
day: 35
phase: 5
phase_name: "CrewAI Flows"
title: "Mandala-flow — the Phase-5 gate"
ids: ["CR-22"]
kind: gate
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 35 — Mandala-flow: the Phase-5 gate

**Phase 5 · CrewAI Flows** · IDs: **CR-22 🛠️** · **🎯 gate day**

> **Yesterday:** the same flow written as data, and an honest table of what that trade costs.
> **Today:** the gate. One artifact: a persisted, HITL-gated flow that embeds the Phase-4 crew — and
> a demo where you **kill the process mid-run and resume it**, on camera.
> **Tomorrow:** Phase 6 opens and the fourth framework arrives. Everything CrewAI has to teach you
> is behind you after today.

```bash
./m start 35
./m scaffold 35
```

---

## §1 What a gate day is for

A gate is not "the day I finish the phase". It is **the day the parts meet**, and the parts always
disagree. Day 29 was the Phase-4 gate and it found three collisions that only existed once assembled.
Expect the same today, and budget your afternoon for it rather than your evening.

The plan's Phase-5 gate sentence is short and every clause is a requirement:

> *"persisted, HITL-gated flow embedding the Phase-4 crew; kill the process mid-run and resume it
> on camera."*

| Clause | Built on | Evidence today |
|---|---|---|
| **persisted** | Day 32 | the store has rows from a run that died |
| **HITL-gated** | Day 33 | a `Decision` record with a reviewer and a reason |
| **flow** | Days 30–31 | routing decisions in `state.steps` |
| **embedding the Phase-4 crew** | Days 23–29, 31 | `organ:` in the trail, guards intact |
| **kill mid-run and resume** | Days 32–33 | one recording, two processes, one ticket |

Plus the standing gate requirement from Part 5, which applies to **every** gate in this plan:

> *"Release notes read for all pins? MCP spec revision changed? → if yes, amend the plan first
> (Principle 14)."*

That is not optional today because it is inconvenient. §7 is where it happens.

---

## §2 Setup — run this

### 2.1 Nothing new

```bash
uv run pytest -q
git status --porcelain
```

- **A gate day adds no dependencies.** If today needs a package, the phase was under-built and you are
  papering over it. Note the urge, do not act on it.
- `git status --porcelain` should be clean or close to it. Assembling on top of four days of
  uncommitted work is how gate days go past midnight.

### 2.2 Create today's files

```bash
mkdir -p days/day-35/lab
touch days/day-35/lab/mandala_flow.py
touch days/day-35/lab/gate_demo.sh
touch tests/test_mandala_flow.py
touch docs/adr/ADR-00X-crewai-flows.md
```

- `mandala_flow.py` is the **runner**, not new logic. Everything it calls already exists in
  `src/mandala/flows/`. Day 29's traps section made this point and it is worth repeating: *writing
  new logic in the gate artifact forks a second implementation under time pressure.*
- `gate_demo.sh` is the script you actually read from while recording. A demo you improvise is a demo
  you re-record four times.
- The ADR number is deliberately `00X`. Check `docs/adr/` for what is taken; the plan's numbered ADRs
  are 001 (Day 16), 002 (Day 42) and 003 (Day 64), so a Phase-5 record needs a number that does not
  collide. **Pick it, write it in the filename, and note the choice in `docs/CHANGELOG_PLAN.md`** —
  an ADR scheme that drifts is an ADR scheme nobody trusts.

### 2.3 Start from a clean store

```bash
rm -rf .mandala/flows .mandala/approvals
uv run python days/day-32/lab/inspect_checkpoints.py 2>/dev/null || echo "store empty - good"
```

- Day 32's §6 trap: **resuming into changed code.** You have edited `intake.py` on Days 31, 33 and
  possibly 34. Every checkpoint written before those edits is stale by the definition in Day 32 §4.3.
- Deleting the store before the gate run is not cheating; it is the staleness policy being applied by
  hand. **Add the sweep as a real function today if you have not** — Day 32's checklist left it open,
  and a gate is where open items get closed or written down.

---

## §3 The artifact

### 3.1 `days/day-35/lab/mandala_flow.py`

```python
"""Mandala-flow: the Phase-5 gate artifact.

Assembly only. Every import below was written on Days 30-33; this file adds no
behaviour, it just runs the thing end to end and prints evidence.

Run:
    uv run python days/day-35/lab/mandala_flow.py T-9002 --attempt a1
    uv run python days/day-35/lab/mandala_flow.py T-9002 --attempt a1 --resume

Budget: ~22 requests for the first attempt, ~0-2 for the resume.
"""

from __future__ import annotations

import argparse
import sys

from mandala.flows.approval import FlowPaused
from mandala.flows.intake import IntakeFlow
from mandala.flows.persistence import CHECKPOINT_DB, ensure_store

parser = argparse.ArgumentParser()
parser.add_argument("ticket_id")
parser.add_argument("--attempt", required=True, help="an ATTEMPT id, not a ticket id (Day 32 §4.2)")
parser.add_argument("--resume", action="store_true", help="explicit opt-in (Day 32 §4.3)")
args = parser.parse_args()

run_id = f"{args.ticket_id}:{args.attempt}"
ensure_store()

flow = IntakeFlow()
try:
    state = flow.kickoff(inputs={
        "ticket_id": args.ticket_id,
        "id": run_id,
        "resume": args.resume,
    })
except FlowPaused as pause:
    print(f"\nPAUSED  {pause}")
    print(f"store   {CHECKPOINT_DB} ({CHECKPOINT_DB.stat().st_size} bytes)")
    sys.exit(0)

print(f"\nticket    {state.ticket_id}")
print(f"attempt   {args.attempt}")
print(f"stage     {state.stage}")
print(f"trail     {' -> '.join(state.steps)}")
print(f"findings  {len(state.findings)}  sources {len(state.sources)}")
print(f"body      {state.ticket_body!r}   <- must be None")
print(f"draft     {(state.draft or '')[:120]}...")
```

**Line by line:**

- `argparse` rather than `sys.argv` slicing, because this script is now a **demo instrument** and it
  needs a `--help`. A gate artifact somebody else can run is worth more than one only you can.
- `--attempt` is `required=True` with the reason in the help text. Day 32 §4.2 established that a run
  id names an attempt, not a subject; making it required means the gate demo cannot accidentally
  demonstrate the bug.
- `run_id = f"{ticket_id}:{attempt}"` — the composite identity, exactly as Day 32 specified.
- `--resume` as an explicit flag threaded into `kickoff` inputs — Day 32 §4.3's gate. The default is
  *not* to resume, so the demo's first command is unambiguous.
- `except FlowPaused as pause:` and `sys.exit(0)` — **a pause is a success, not a failure.** Exit code
  0 matters: `gate_demo.sh` runs with `set -e` (§3.2), and a nonzero exit would abort the demo at the
  exact moment it is proving the point. This is Day 33's trap ("treating a `FlowPaused` as an error")
  becoming concrete.
- The pause branch prints the store size, so the recording shows there is state on disk *at the moment
  of the pause*. Evidence, not narration.
- `state.ticket_body!r` printed with the `<- must be None` marker — Day 30's security property,
  surviving three days, two processes and a serialization round trip. **This is the single line the
  camera needs.**
- `(state.draft or '')[:120]` — truncated, because a full draft on screen adds nothing and a demo that
  scrolls is a demo nobody watches twice.

### 3.2 `days/day-35/lab/gate_demo.sh` — the script you read from

```bash
#!/usr/bin/env bash
# The Phase-5 gate demo. Read from this; do not improvise.
set -euo pipefail

TICKET=T-9002
ATTEMPT=gate-$(date +%H%M%S)

echo "== 1. clean store =================================================="
rm -rf .mandala/flows .mandala/approvals

echo "== 2. start the run; it will pause at the approval gate ============"
uv run python days/day-35/lab/mandala_flow.py "$TICKET" --attempt "$ATTEMPT"

echo "== 3. proof that state is on disk while nothing is running ========="
uv run python days/day-32/lab/inspect_checkpoints.py

echo "== 4. a HUMAN decides, in a different process ======================"
uv run python days/day-33/lab/approve_cli.py "req-$TICKET"

echo "== 5. resume -- note the trail starts before the pause ============="
uv run python days/day-35/lab/mandala_flow.py "$TICKET" --attempt "$ATTEMPT" --resume

echo "== 6. the evidence table ==========================================="
uv run pytest tests/test_mandala_flow.py -v
```

**Line by line:**

- `set -euo pipefail` — exit on error, on undefined variable, and on a failed pipe stage. A demo
  script that silently continues past a failure will show you a green ending for a broken system.
- `ATTEMPT=gate-$(date +%H%M%S)` — a fresh attempt id every recording, so a re-take cannot resume the
  previous take's checkpoint. Small thing; it will save you a confusing re-record.
- **Step 3 is the whole demo.** Between step 2 and step 4 there is *no process running* and the flow
  still exists. Pause on this in the recording and say it out loud, because it is the difference
  between HITL and a blocking prompt, and it is the thing an interviewer will actually remember.
- Step 4 is interactive and that is correct — the human is a real participant, not a mocked one. If
  you need the recording to be hands-free, pre-write the decision file and say that you did.
- Step 6 runs the tests **inside the demo**. Claims made on camera should be checkable on camera.

### 3.3 The three collisions to expect

Day 29's gate found three; today's will too. The likely candidates, so you recognise them fast:

1. **The `stage` `Literal` is out of date.** Days 33 and 35 both add lifecycle values
   (`awaiting_approval`, `approved`, `rejected`). If Day 33's commit updated it and Day 31's route
   for `escalate` sets `stage = "failed"`, you now have two names for "a human has it". **Pick one
   vocabulary today** and fix the `Literal`; Day 71 counts these.
- 2. **`guard_progress` fires on a resumed run.** The resumed flow re-records steps, so `state.steps`
   grows across attempts and can cross `MAX_STEPS` on a long-running ticket that has been resumed
   three times. Decide: does the step budget apply per *attempt* or per *run*? Day 31 did not say.
   Write the answer into `routes.py` as a comment, not just into your head.
3. **The approval is keyed on `request_id`, and the attempt id is not in it.** Day 33 used
   `req-{ticket_id}`; today's identity is `{ticket_id}:{attempt}`. Two attempts on the same ticket
   share an approval file, so attempt 2 resumes with attempt 1's decision — Day 33's own §6 trap
   ("letting a stale decision authorise a new draft") arriving on schedule. **Fix it by keying the
   decision on the run id**, and note that you found it by assembling, which is what gates are for.

---

## §4 The evidence table

A gate passes when every row is green **and you can point at the artifact that proves it.** Fill the
last column with a filename, not a feeling.

| # | Claim | Proved by | ✓ |
|---|---|---|---|
| 1 | The flow routes without a model | `tests/test_routes.py::test_the_router_makes_no_model_call` | ⬜ |
| 2 | Every route has a declared budget | `tests/test_routes.py::test_every_route_has_a_budget` | ⬜ |
| 3 | The deep lane runs the Phase-4 crew | `organ:` appears in `state.steps` | ⬜ |
| 4 | The crew is constructed in exactly one place | `tests/test_organs.py` architecture test | ⬜ |
| 5 | Raw customer text never reaches the research step | `tests/test_organs.py` security test | ⬜ |
| 6 | Raw customer text never reaches disk | `tests/test_persistence.py::test_scrub_removes_the_body` | ⬜ |
| 7 | State survives process death | store has rows while no process runs (demo step 3) | ⬜ |
| 8 | Resume continues rather than restarts | trail contains pre-pause steps (demo step 5) | ⬜ |
| 9 | Resume is explicit, not automatic | `test_resume_requires_an_explicit_request` | ⬜ |
| 10 | Nothing may be sent without a human decision | `test_reject_does_not_authorise_send` | ⬜ |
| 11 | One function decides authorisation | `test_authorises_send_is_the_only_gate` | ⬜ |
| 12 | The reviewer's edit is what gets sent | `test_edit_authorises_send_of_the_edited_text` | ⬜ |
| 13 | The decision record is immutable and attributed | `test_a_decision_cannot_be_altered` | ⬜ |
| 14 | The resume run costs far less than the first | both numbers in `RATE_BUDGET.md` ledger | ⬜ |
| 15 | Pins re-verified; drift logged or nil-reported | `docs/CHANGELOG_PLAN.md` entry, today's date | ⬜ |

**Rows 5 and 6 are the pair to look at twice.** They are the same property at two layers — in memory
and on disk — and Phase 5 is the first phase where the second layer existed at all. A system that
protects data in memory and writes it to a file is not protecting data.

**Row 14 is the one people skip and the one a hiring panel finds interesting**, because it is the row
that turns an architecture claim into a number.

---

## §5 `tests/test_mandala_flow.py`

The gate's own test file. It asserts the **assembly**, not the parts — the parts have their own tests
and re-testing them here just makes failures harder to localise.

```python
"""Gate-level assertions: do the four days actually compose? 0 model requests."""

from pathlib import Path

import pytest

from mandala.flows.approval import Decision
from mandala.flows.persistence import NEVER_PERSIST
from mandala.flows.routes import ALL_ROUTES, ROUTE_BUDGET
from mandala.flows.state import MandalaState


def test_every_stage_value_is_reachable():
    """A Literal value nothing ever sets is a lie in the schema."""
    stages = set(MandalaState.model_fields["stage"].annotation.__args__)
    sources = "\n".join(
        p.read_text(encoding="utf-8") for p in Path("src/mandala").rglob("*.py")
    )
    unset = {s for s in stages if f'"{s}"' not in sources}
    assert unset == set(), unset


def test_the_lifecycle_vocabulary_has_no_synonyms():
    """Collision 1 from §3.3. Two names for one state is a counting bug on Day 71."""
    stages = set(MandalaState.model_fields["stage"].annotation.__args__)
    assert not ({"failed", "escalated"} <= stages), "pick one name for 'a human has it'"


def test_the_step_budget_scope_is_documented():
    """Collision 2 from §3.3: per attempt, or per run? Say it in the source."""
    text = Path("src/mandala/flows/routes.py").read_text(encoding="utf-8")
    assert "per attempt" in text or "per run" in text, "MAX_STEPS scope is undocumented"


def test_an_approval_is_bound_to_an_attempt():
    """Collision 3 from §3.3. Flip it: key on ticket_id and this goes red."""
    from mandala.flows.approval import decision_key

    assert decision_key("T-9002", "a1") != decision_key("T-9002", "a2")


def test_the_gate_artifact_adds_no_logic():
    """A gate assembles; it does not implement. Keep the runner thin."""
    runner = Path("days/day-35/lab/mandala_flow.py").read_text(encoding="utf-8")
    assert "def " not in runner, "the gate runner defined a function - move it to src/"


@pytest.mark.parametrize("route", sorted(ALL_ROUTES))
def test_every_route_survived_the_phase(route):
    assert route in ROUTE_BUDGET


def test_the_never_persist_set_is_not_empty():
    """A guard that guards nothing passes silently forever."""
    assert NEVER_PERSIST


def test_a_decision_still_requires_a_reviewer():
    with pytest.raises(Exception):
        Decision(outcome="approve", reviewer="")
```

**Line by line:**

- `test_every_stage_value_is_reachable` reads the `Literal`'s `__args__` and greps `src/` for each
  value. **A dead enum value is worse than a missing one**: it looks like a supported state, tests
  can be written against it, and nothing ever produces it. Cheap to check, and it will catch
  yesterday's leftovers.
- `test_the_lifecycle_vocabulary_has_no_synonyms` encodes collision 1 as an assertion with the
  instruction in the message. Note it does not tell you *which* name to keep — that is a judgement,
  and the test's job is to force you to make it once.
- `test_the_step_budget_scope_is_documented` is a **documentation test** and slightly unusual. It
  passes when the source contains a phrase, which sounds weak until you consider the alternative:
  collision 2 is a decision, not a behaviour, and the only durable artifact of a decision is a
  sentence somebody wrote. Forcing the sentence to exist is the strongest thing a test can do here,
  and being clear about that limitation is part of the lesson.
- `test_an_approval_is_bound_to_an_attempt` — collision 3, with the mutation to try in the docstring.
  This requires you to add a `decision_key(ticket_id, attempt)` helper to `approval.py`, which is the
  fix for the collision rather than a workaround around it.
- `test_the_gate_artifact_adds_no_logic` asserts `"def "` does not appear in the runner. **Crude on
  purpose**, and it will annoy you the first time you want a tiny helper — which is exactly when the
  rule is earning its keep. If you genuinely need a helper, it belongs in `src/mandala/flows/`, where
  Day 78's capstone can reuse it.
- `test_the_never_persist_set_is_not_empty` — one line against a whole failure mode: someone empties
  the set while debugging, every test still passes, and raw text starts flowing to disk.
- **No test here runs a flow or calls a model.** The gate's *behaviour* is demonstrated by the
  recording; the gate's *invariants* are tested here. Knowing which claims a test can carry and which
  need a demo is a real engineering judgement, and gate days are where you practise it.

---

## §6 The ADR

Write `docs/adr/ADR-00X-crewai-flows.md` today, while the collisions are fresh. Use the repo's
template (`docs/adr/ADR-TEMPLATE.md`) and answer these four questions in your own words:

1. **When would I choose CrewAI Flows for a real system?** Be specific, and name a case where you
   would not.
2. **What did Flows give me that Crews could not?** Determinism, a typed seam, routing you can test
   for free, durable pauses. Which mattered most, and why?
3. **Where does the DSL boundary belong?** Yesterday's `compare.md` answers this; carry the
   conclusion here in two sentences.
4. **What am I carrying into Phase 7?** LangGraph's Day 43 state model, Day 47 checkpointers and Day
   50 interrupts are the same three ideas you just built. Write down what you expect *before* you see
   them — a prediction you recorded is worth ten times an observation you rationalised.

Principle 9: this is an interview artifact. Write it as though a hiring panel will read it, because
that is precisely what it is for.

---

## §7 The standing gate freshness check

Every gate in this plan carries it. Do it now, not "later":

```bash
for p in crewai crewai-tools; do
  printf "%-16s " "$p"
  curl -s --max-time 30 "https://pypi.org/pypi/$p/json" \
    | python -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
done
```

- Compare against `docs/PINS.md` (`crewai` / `crewai-tools` **1.15.17**, verified 2026-08-20).
- **Patch bump** → pin the new patch, one line in `docs/CHANGELOG_PLAN.md`.
- **Minor or major** → stop, read the release notes, write an addendum, *then* pin (Principle 14).
  Pay particular attention to the declarative-flow surface; Part 2 warns it moves, and yesterday you
  were reading it closely enough to notice a change.
- **Nothing changed?** That is still a result. *"Checked, unchanged"* goes in the changelog. The
  habit is the deliverable (Principle 13), and a nil report you skipped is a habit you do not have.
- The MCP spec revision is also on the standing list. It does not affect Phase 5, and checking it
  takes ten seconds — do it anyway, because Day 53 will thank you and because a check you only run
  when you expect a result is not a check.

---

## §8 Traps

- **Writing new logic in `mandala_flow.py`.** Day 29's trap, repeated because it is the one that
  recurs. Test 5 in §5 enforces it.
- **Resuming into a stale store.** §2.3. You edited the flow three times this week.
- **Recording the demo before the tests are green.** You will re-record.
- **Improvising the demo.** Read from `gate_demo.sh`.
- **Skipping demo step 3.** "Nothing is running and the state still exists" *is* the phase.
- **Treating `FlowPaused` as a failure**, so the demo script aborts at its best moment.
- **Filling the evidence table with feelings.** Every row needs a filename or a command.
- **Skipping the freshness check because the gate went long.** The check is the smallest item on the
  page and the only one that compounds.
- **Fixing the three collisions silently.** Each one is a finding. They go in the ADR — a gate that
  reports "everything composed perfectly" is a gate that was not actually assembled.

---

## §9 Request budget

**Declared: ~25 model requests, Groq.**

| What | Requests |
|---|---|
| `tests/test_mandala_flow.py` and all Phase-5 tests | **0** |
| One full gate demo run (deep lane + crew) | ~22 |
| Resume after approval | 0–2 |
| One re-record allowance | ~22 |

**Do the first take with the tests already green.** The re-record allowance exists because you will
want one, not because you should plan on two — and against OpenRouter's 50 RPD (`RATE_BUDGET.md` §1)
a third full take would be most of a day's quota on that provider.

Log both attempt costs, and log the **ratio** for row 14 of the evidence table.

---

## §10 Done when

Phase 5 is complete when every row in §4 is green, the ADR exists, and the recording shows a process
that died and a flow that did not.

```bash
./m check
./m done 35
```

Then read Day 36's first section before you close the laptop. Phase 6 starts with LangChain 1.x, and
`docs/03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md` has an **unsigned** amendment about the
LangChain pin waiting for you. Handling it before Day 36 rather than during it is the difference
between a clean start and an hour of yak-shaving.
