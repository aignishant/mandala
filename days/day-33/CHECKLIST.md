# Day 33 — CHECKLIST

**IDs covered:** CR-19 🛠️ (HITL in flows + conversational flows) · **AG-20 · Principle 12**

## Demo command

```bash
uv run python days/day-31/lab/run_branch.py T-1001        # runs, then PAUSES at the gate
uv run python days/day-33/lab/approve_cli.py req-T-1001   # 0 requests — decide
uv run python days/day-31/lab/run_branch.py T-1001        # resumes past the gate
uv run pytest tests/test_approval.py -v
```

Expected: the first run raises `FlowPaused` **with the approve command in the message**; the third
run's trail contains `decision:approve:me` and reaches `stage=approved`.

## Setup

- [ ] `./m start 33` and `./m scaffold 33` run
- [ ] No new packages
- [ ] Day 32's store confirmed working **before** starting (`inspect_checkpoints.py` prints tables)
- [ ] Files created (`flows/approval.py`, `tests/test_approval.py`, two lab files)
- [ ] `.mandala/approvals/` covered by `.gitignore` — drafts derive from customer tickets

## CR-19 — the gate

- [ ] Can list the **five** things a gate records, and say why each is there
- [ ] `Decision` is `frozen=True` — a changed mind is a *second* decision
- [ ] Three outcomes, not two — and can say what `edit` is worth on Days 28 and 71
- [ ] `@model_validator(mode="after")` used, and can say why a field validator could not do it
- [ ] Reason required on reject/edit, **not** on plain approval — and can defend that asymmetry
- [ ] `authorises_send()` exists as **the one** authorisation question in the codebase
- [ ] `final_text()` used, so an approved edit sends the edit
- [ ] `decided_at` is timezone-aware and uses `default_factory`

## The pause

- [ ] `await_approval` listens to the draft-producing lanes, **not** `escalate` — and can say why
- [ ] `"awaiting_approval"` added to the `stage` `Literal` in the same commit
- [ ] `FlowPaused` subclasses `Exception`, not `RuntimeError` — it is not an error
- [ ] The pause message contains the **exact command** to unpause it
- [ ] Second run resumes past the gate — idempotency confirmed
- [ ] Can fill in the six-row blocking-vs-pausing table from §3.4
- [ ] Understood this is hand-building what LangGraph's `interrupt()` gives free on Day 50

## Conversational flows

- [ ] Can state the difference from the gate: **who holds the initiative**
- [ ] `MAX_TURNS` enforced **in code**, not by discipline
- [ ] History bounded — the conversation is the prompt (AG-04, fifth costume)
- [ ] `/quit` and empty-input exits both work
- [ ] Chat API surface for 1.15.17 established and written into §4.2
- [ ] "Conversational persistence — decide on Day 47" written in the bake-off notes

## Tests that must be able to fail

- [ ] `test_approve_needs_no_reason`
- [ ] `test_reject_without_a_reason_is_refused`
- [ ] `test_edit_without_edited_text_is_refused`
- [ ] `test_an_anonymous_decision_is_refused`
- [ ] `test_reject_does_not_authorise_send` — **flip it:** add `reject` to `authorises_send`, see red
- [ ] `test_edit_authorises_send_of_the_edited_text` — **both** halves asserted
- [ ] `test_approve_sends_the_original_text`
- [ ] `test_a_decision_cannot_be_altered`
- [ ] `test_decided_at_is_timezone_aware`
- [ ] `test_two_decisions_have_different_timestamps` — and its limitation understood
- [ ] `test_authorises_send_is_the_only_gate` — the architecture test, second day running
- [ ] All tests cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why does the approval gate depend on yesterday's persistence?
- [ ] Why is a separate reviewer process better than `input()`, in five different ways?
- [ ] Why three outcomes, and what is lost with two?
- [ ] Why is `authorises_send()` a method rather than an `if` at each call site?
- [ ] Why is `FlowPaused` not an error, and what breaks in CI if you treat it as one?
- [ ] Why was today so cheap, and what does that say about where Phase 5's cost lives?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~8, Groq)
- [ ] Whether 1.15.17 has a **built-in** human-feedback step — established
- [ ] Chat API entry point confirmed (module, class, call shape)
- [ ] Whether the chat API auto-persists turns — checked
- [ ] **Confirmed a raise mid-step does not roll back the last checkpoint** — the gate rests on it
- [ ] `kickoff` twice on the same id confirmed to continue past a previously-raising step
- [ ] Stale-decision risk (draft changed, approval did not) written down for Day 82
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 33
```

- [ ] Bake-off row updated: **HITL mechanism** — SDK approvals (21) vs. CrewAI pause (today) vs.
      LangChain middleware (39) vs. LangGraph `interrupt()` (50)
- [ ] `./m done 33` succeeded — trackers updated automatically
