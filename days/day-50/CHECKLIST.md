# Day 50 — CHECKLIST

**IDs covered:** LG-09 🛠️ (interrupts), AG-20 🛠️ (human-in-the-loop patterns, **completed**)

## Demo command

```bash
uv run python days/day-50/lab/pause_resume.py T-9002 a1 start    # ~8 requests, then PAUSES
# ... the process has exited. nothing is running. ...
uv run python days/day-50/lab/pause_resume.py T-9002 a1 approve  # 0 requests
uv run pytest tests/test_graph_approval.py -v
```

**Two separate process invocations.** That is the demo; say it out loud while recording.

## Setup

- [ ] `./m start 50` and `./m scaffold 50` run
- [ ] No new packages
- [ ] `langgraph-checkpoint-sqlite` confirmed present — **an interrupt without a checkpointer is not
      durable**
- [ ] Files created (`graph/approval.py`, `tests/test_graph_approval.py`, two lab files)

## LG-09 — `interrupt()`

- [ ] Can state the three things that happen, and why the third is surprising
- [ ] **Proved the re-run by experiment** — a `print` at the top of the node, counted across both
      processes
- [ ] Nothing expensive above `interrupt()`
- [ ] Nothing with side effects above `interrupt()`
- [ ] Node kept tiny: gather payload, interrupt, record answer
- [ ] Connected it to yesterday's idempotence rule — retry and resume, one property
- [ ] Pending interrupt surfaced and read **from a second process**
- [ ] `snapshot.next` printed before resuming
- [ ] `Command(resume=...)` used — not `invoke(None)`, and knows the difference

## Mechanism vs. record

- [ ] `Decision` **imported from `mandala.flows.approval` unchanged** — across namespaces
- [ ] Can say precisely what the framework supplied and what it did not
- [ ] Resume value **validated through `Decision`** — it is untrusted input
- [ ] `authorises_send()` still the only authorisation function, now across two frameworks

## The fingerprint — closing a Day-33 deferred item

- [ ] `proposal_fingerprint()` written
- [ ] Payload carries it; the resume echoes it back
- [ ] Mismatch **escalates**, does not raise
- [ ] **Tampered-fingerprint experiment run by hand** — one character changed, escalation observed
- [ ] Noted in the changelog that Day 33's deferred trap is now closed
- [ ] Understood it is change detection, not adversarial security — and said so rather than implying
      more

## AG-20 — `hitl_compare.md`

- [ ] Nine-row four-framework table filled with real numbers
- [ ] "What the framework gave me and what it did not" written precisely
- [ ] The re-entry constraint explained, and linked to Day 49
- [ ] **"What Day 33 was worth" answered honestly** — and the surviving half identified
- [ ] Which one you would ship, and under what constraints
- [ ] Recorded as the strongest Principle-2 evidence in the plan; flagged for Day 89

## Tests that must be able to fail

- [ ] `test_an_approval_lets_the_draft_through`
- [ ] `test_a_rejection_escalates`
- [ ] `test_an_edit_sends_the_edited_text`
- [ ] `test_a_stale_decision_does_not_authorise_a_changed_draft` — **flip it:** drop the check, red
- [ ] `test_an_anonymous_resume_value_is_refused`
- [ ] `test_a_reject_without_a_reason_is_refused`
- [ ] `test_the_decision_is_recorded_in_the_notes`
- [ ] `test_nothing_expensive_happens_above_the_interrupt` — **flip it:** add a model call, red
- [ ] `test_the_decision_model_is_day_33s` — **flip it:** define a second `Decision`, red
- [ ] `test_authorises_send_is_still_the_only_gate` — now spanning two frameworks
- [ ] Learned the trick: **monkeypatch `interrupt` to return the answer** — no graph, no runtime
- [ ] All tests cost **0 model requests**

## Understanding check — answer out loud

- [ ] What exactly happens on `interrupt()`, in three steps?
- [ ] Why does the node re-run, and what does that forbid?
- [ ] Why is a resume value untrusted input?
- [ ] What does the fingerprint prevent, and what does it not protect against?
- [ ] Which half of Day 33 survived, and why was it never going to come from a framework?
- [ ] Across four implementations, what does a human decision cost you?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~8, Groq)
- [ ] **Resume logged as 0** — and the point made in the bake-off
- [ ] `interrupt` import path confirmed
- [ ] Node re-run behaviour **proved**, not assumed
- [ ] How a pending interrupt is surfaced — confirmed
- [ ] `Interrupt` object attributes confirmed (`.value`)
- [ ] Multiple-interrupt resume matching — answered, noted for Day 82
- [ ] `interrupt()` inside a subgraph — answered, noted for Day 83
- [ ] `interrupt()` inside a `Send` branch — answered
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 50
```

- [ ] Bake-off rows updated: **HITL durability**, **cost to wait**, **what the framework does not
      supply**
- [ ] AG-20 marked complete across all four implementations
- [ ] `./m done 50` succeeded — trackers updated automatically
