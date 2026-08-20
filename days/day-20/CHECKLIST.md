# Day 20 — CHECKLIST

**IDs covered:** OAI-21 🛠️ (long-horizon & durable runs with Temporal — AG-27 applied) ·
OAI-22 🅿️ (realtime & voice, awareness only, no lab)

## Demo command

```bash
temporal server start-dev --db-filename .mandala/temporal.db --ui-port 8233   # terminal 1
uv run python days/day-20/lab/worker.py                                       # terminal 2
uv run python days/day-20/lab/durable_demo.py T-1001                          # terminal 3
# then: Ctrl-C the worker mid-run, restart it, watch the run resume
```

## Setup

- [ ] `./m start 20` and `./m scaffold 20` run
- [ ] `uv add "temporalio==1.31.0"` — the Day-20 ledger row in `docs/PINS.md` already exists
- [ ] Temporal CLI installed; `temporal operator cluster health` succeeds
- [ ] Dev server started **with `--db-filename`** (an in-memory server fakes the whole experiment)
- [ ] `tests/test_idempotency.py` and `tests/test_permissions.py` green **before** starting
- [ ] Files created (`src/mandala/durable.py`, three lab files, one test file)
- [ ] Can say why this still costs **$0**: Temporal is open source and self-hosted; model calls go
      through LiteLLM to Groq's free tier (Principle 5)

## OAI-21 — the determinism split (§3.2)

- [ ] Can state it in one sentence: **workflow code is deterministic orchestration; every model call,
      tool call and byte of I/O is an activity**
- [ ] Can explain *why* — replay re-runs the function and a different model answer takes a different
      branch than the recorded history
- [ ] Can name what is banned in workflow code: `datetime.now`, `random`, `uuid4`, `asyncio.sleep`,
      file/env reads, HTTP, and constructing a model client
- [ ] Can say why `make_model()` specifically must live inside the activity (it reads env via
      `load_keys()`, Day 1/9)
- [ ] Can explain why `uuid.uuid4()` in `durable_demo.py` is fine — the ban is on a *region of code*
- [ ] Can distinguish event-history replay from state checkpointing (§3.1) and name three other
      places the same idea appears (CrewAI Day 32, LangGraph Day 49, MCP Tasks)

## 🛠️ Built — `src/mandala/durable.py`

- [ ] `TASK_QUEUE` / `TEMPORAL_TARGET` defined **once**
- [ ] `imports_passed_through()` used for the Agents SDK imports, and I can say why
- [ ] `research_ticket` and `resolve_ticket` activities wrap Day 14's `researcher()` / `resolver()`
- [ ] `assert_no_raw_ticket` (Day 14) still runs — the Day-8 seam survived the port
- [ ] `MandalaTicketWorkflow` contains **no** `Runner.run`, no client, no clock, no randomness
- [ ] `@workflow.query progress` implemented — free progress on a long run
- [ ] Both retry policies are module constants with **every field explicit** (Principle 4)
- [ ] `NON_RETRYABLE` includes `PermissionDenied`; can say why (Day 8/10)
- [ ] Every `execute_activity` names a timeout **and** a retry policy
- [ ] `post_reply_activity` checks `approvals_required` **before** computing the key (Principle 12)

## 🎯 The experiment — kill the worker mid-run (§3.9)

- [ ] Ran `durable_demo.py`, then Ctrl-C'd the worker during **resolve**, then restarted it
- [ ] **Workflow id: ______________________**
- [ ] **Step it resumed from: ______________**
- [ ] **What re-ran (activity names + `attempt=` values): ______________________**
- [ ] **Model calls repeated by the resume: ______** (counted with Day 14's `model_calls()`, not
      estimated)
- [ ] **Research was NOT repeated — confirmed in the new worker's log: [ ] yes / [ ] no**
- [ ] Second run: killed during **research** instead. What re-ran: **______________________**
      Model calls lost: **______**
- [ ] Read a real event history: `temporal workflow show -w <id>` or the web UI
- [ ] Can name the rhyme: the same kill-and-resume demo is the Phase-5 gate for CrewAI Flows on
      **Day 35** and LangGraph's checkpointer lab on **Day 49**

## Failure semantics (§3.10) — the reading the plan asked for

- [ ] Can say **at-least-once, never exactly-once**, and what that implies for `post_reply`
- [ ] Can classify five errors as retryable or not, with a reason for each
- [ ] Knows what a timeout actually cancels (my waiting; not the request in flight)
- [ ] Knows what heartbeats are for, and that a declared `heartbeat_timeout` nothing satisfies is
      worse than none (the §3.7 `TODO(me)`)
- [ ] Can describe the two stacked backoffs (Day 6's router inside Temporal's retry) and the risk
      of the inner one flattening a permanent error

## Idempotency — Day 6 stops being theoretical (§3.6)

- [ ] `idempotency_key` derived from **stable inputs** (`request_id` + text), never the attempt
- [ ] Can say why Day 8 split `draft_reply` from `post_reply`, in terms of retries
- [ ] `.mandala/sent.jsonl` has **one** line after the kill-and-resume run — count: **______**
- [ ] The store-survives-restart `TODO(me)` is either done or written down as owed

## OAI-22 🅿️ — realtime & voice (§4)

- [ ] Can name the two architectures (speech-to-speech vs. chained STT → agent → TTS) and which
      Mandala would pick, and why
- [ ] Can name three things that are new: turn detection, barge-in, a latency budget in tens of ms
- [ ] Can explain the Day-17 connection: a voice guardrail's deadline moves from "before delivery"
      to "before the next 300 ms of delivery"
- [ ] Can say why `find_secrets`-style cheap deterministic checks survive the move to voice
- [ ] Can give the honest three-part reason for **not** rebuilding it free: Principle 3, the hard
      parts do not survive the rebuild, and Mandala is a text channel (plan Part 8)
- [ ] Can name two situations where voice genuinely is the right channel

## Tests that must be able to fail

- [ ] `test_workflow_code_contains_no_banned_nondeterminism` — the §3.2 table as a lint
- [ ] `test_the_workflow_never_calls_a_model_or_builds_a_client` — the trap of the day, statically
- [ ] `test_the_workflow_only_reaches_the_outside_through_execute_activity` — AST whitelist
- [ ] `test_every_retry_policy_spells_out_every_field` — Principle 4 mechanized
- [ ] `test_a_permission_denial_is_never_retried` — the security test
- [ ] `test_the_non_retryable_list_is_exactly_what_we_reviewed` — deliberate change-detector
- [ ] `test_every_activity_call_names_a_timeout_and_a_policy`
- [ ] `test_the_idempotency_key_is_stable_across_attempts`
- [ ] `test_an_activity_run_twice_produces_exactly_one_effect` — **flip it:** delete the
      `_EFFECTS.run` wrapper and watch it go red
- [ ] `test_a_write_activity_still_requires_approval` — Principle 12 survives durability
- [ ] `test_the_workflow_replays_deterministically` — `@pytest.mark.temporal`, skipped, owed
- [ ] Suite green with **no server running**; can say why that is a design decision (§5.2)
- [ ] Every unskipped test costs **0 model requests**

## Understanding check — answer out loud

- [ ] Why is an LLM call in workflow code a correctness bug rather than a style issue?
- [ ] Why did `temperature=0.0` and a pinned model not make it safe?
- [ ] What exactly does the engine store, and how does that differ from a checkpoint file?
- [ ] Why is at-least-once unavoidable, and what *can* be made exactly-once?
- [ ] Why is retry policy a permission question as well as a reliability one?
- [ ] What does durability cost me? (name three, from the §3.11 table)
- [ ] When would I say "don't use this"?

## Budget & freshness

- [ ] Model requests logged in `docs/RATE_BUDGET.md` (declared: ~31, Groq)
- [ ] `temporalio` 1.31.0 API confirmed: `execute_activity` kwargs, `RetryPolicy` import path,
      `ApplicationError(non_retryable=...)`, `imports_passed_through()`
- [ ] The Agents SDK + Temporal integration module's import path confirmed for 0.22.0
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md` — **do not silently adapt** (Principle 14)

## Commit

```bash
./m check
./m done 20
```

- [ ] `./m done 20` succeeded — trackers updated automatically
- [ ] Tomorrow closes Phase 3: guardrails + approvals composed (OAI-23) and AgentKit literacy
      (OAI-25). No new package — but re-read Day 12's approval gate tonight, because tomorrow
      `post_reply` finally stops raising.
