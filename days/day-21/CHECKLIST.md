# Day 21 — CHECKLIST

**IDs covered:** OAI-23 🛠️ (guardrails + approvals composed, with the decision trace) ·
OAI-25 🅿️ (AgentKit & the platform layer — literacy only)

## Demo command

```bash
uv run python days/day-21/lab/policy_demo.py     # THE battery — seven actions, one table
uv run pytest tests/test_resolver_policy.py -q   # all of it, 0 model requests
```

## Setup

- [ ] `./m start 21` and `./m scaffold 21` run
- [ ] **No new packages** — `docs/PINS.md` grows no Day-21 ledger row, and can say why
- [ ] `tests/test_permissions.py`, `test_guardrails.py`, `test_context.py`, `test_mcp_mount.py`
      all green **before** starting
- [ ] Day 16's `console_approver` `TODO(me)` is **written** — today it guards something real
- [ ] Files created (`src/mandala/resolver_policy.py`, one lab file, one test file);
      `.mandala/outbox/` is gitignored

## §3.1–3.2 The three kinds of check

- [ ] Can name all three, when each runs, what each costs, and what each *asks*
      (heuristic / structural / authority)
- [ ] Can state the thesis: **cheap checks run first, humans last**
- [ ] Can explain why `permission` precedes `guardrail:input` for a single attempted action
      (cost order) while guardrails precede dispatch in a *run* (information order) — and why
      `guardrail:output` is cheap and still last

## §3.3–3.5 What today adds, and what it does not

- [ ] **No new grant** — `permissions.py` is unedited; `post_reply` has been in the table since Day 8
- [ ] Blast radius named: the write goes to `.mandala/outbox/`, not to a customer (Principle 6)
- [ ] `NEEDS_APPROVAL` **derived** from `TOOLS[...].writes`, never hand-listed
- [ ] Day 16's `ApprovalGate.NEEDS_APPROVAL` re-pointed at the same derivation — one source of truth
- [ ] `MandalaContext.approver` added as a **service**, not a second flag; defaults to `None`
- [ ] Can say the `allowed_callers` line: **"the paid feature is a narrower version of the table you
      already keep"** — and can name the two layers Mandala has that it does not

## §3.6–3.8 `resolver_policy.py` built

- [ ] `LAYERS` is one tuple carrying both the order and the cost words, and the costs are words
      (`free`/`ms`/`human`) not numbers — can say why
- [ ] `evaluate()` never raises and never acts; `enforce()` raises — can say why they are separate
- [ ] `PolicyRefused` subclasses `PermissionDenied` — can say what that buys from Day 10
- [ ] `approval_required` uses `or`, not `and` — the switch tightens, never loosens
- [ ] `worst_cost()` written (TODO(me)) — can say what I decided a decision "costs", and why
- [ ] `group_for_approval()` written (TODO(me)) — can name my batching key and defend it
- [ ] `post_reply_gated` calls `enforce` **before** the idempotency check (Day 7 key, Day 20 retries),
      and `name_override="post_reply"` matches `permissions.TOOLS` exactly (Day 15's rule)
- [ ] Audit lines emitted per layer via `context.audit()` (Day 12's format)

## §3.9–3.10 The battery — record every row

Which layer stopped it, and at what cost?

- [ ] 1 clean draft → refused by **___** · cost **___**
- [ ] 2 draft, secret in input → refused by **___** · cost **___**
- [ ] 3 write by an agent that lacks the permission → refused by **___** · cost **___**
- [ ] 4 write, approvals on, human declines → refused by **___** · cost **___**
- [ ] 5 same write, human approves → refused by **___** · cost **___**
- [ ] 6 refused by TWO layers (audit mode) → `refused_by` = **___** · also objected: **___**
- [ ] 7 approved, then output guardrail refuses → refused by **___** · cost **___**
- [ ] **Actions evaluated: ___   Humans asked: ___**
- [ ] The cheapest layer caught the most dangerous case (row 3) — can explain why that is not luck
- [ ] Ran the demo once with the real `console_approver` and was personally stopped by the gate

## §3.11 Approval fatigue — the trap of the day

- [ ] Can say why a clicked-through gate is **worse** than no gate (two reasons: false record,
      laundered responsibility)
- [ ] Can name the four fixes in order: consequence not count · batch · readable diff · measure
- [ ] Can say what you do *not* do, and how it connects to Phase 13's graduated-autonomy review
- [ ] Can say why a gate that has never been declined is not evidence of safety

## §4 OAI-25 🅿️ — AgentKit (read, not run)

- [ ] Can name Agent Builder / ChatKit / connector registry and which SDK concept each wraps
- [ ] Can give **one genuine buy and one genuine lock** without flinching at either, and state the
      locks precisely: definitions out of git, review out of PRs, evals out of CI, migration unpriced
- [ ] Can place it as the **third column** on ADR-001's axis: *what someone else runs*
- [ ] Can say when a team **should** genuinely adopt it — and the "price the exit" rule
- [ ] Knows why the plan treats it as literacy only (zero-budget addendum Part 5, code-first)

## Tests that must be able to fail

- [ ] `test_the_permission_layer_refuses_what_the_table_never_granted`
- [ ] `test_the_input_guardrail_layer_refuses_a_secret`
- [ ] `test_the_approval_layer_refuses_when_the_human_says_no`
- [ ] `test_the_output_guardrail_layer_refuses_another_customers_name`
- [ ] `test_the_layers_are_declared_in_cost_order` — deliberate change-detector
- [ ] `test_a_clean_action_runs_every_layer_in_that_exact_order` — behaviour, not just declaration
- [ ] `test_no_human_is_asked_after_a_cheaper_layer_refuses` — **the thesis, asserted**
- [ ] `test_audit_mode_reports_every_layer_and_still_never_asks_a_human`
- [ ] `test_a_human_is_never_asked_before_the_permission_check` — **flip it:** swap `permission`
      and `approval` in `LAYERS`, confirm red, put it back
- [ ] `test_a_write_with_approvals_required_and_no_approver_raises` — the safe value is the default,
      fourth time (Days 12, 13, 15, 21)
- [ ] `test_an_approved_write_proceeds`
- [ ] `test_the_context_switch_can_tighten_approval_but_never_loosen_it` — the one-character bug
- [ ] `test_reads_are_never_gated`
- [ ] `test_needs_approval_is_derived_from_the_permission_table`
- [ ] `test_the_decision_trace_records_which_layer_fired_and_why`
- [ ] `test_the_trace_produces_greppable_audit_lines`
- [ ] `test_a_refusal_carries_its_own_trace`
- [ ] `test_policy_refused_is_a_permission_denied`
- [ ] `test_trifecta_violations_is_still_empty` — twenty-one days running
- [ ] `test_two_writes_to_one_ticket_are_one_approval` — red until `group_for_approval`
- [ ] `test_the_policy_layer_and_the_attached_guardrail_agree` — TODO(me), currently a placeholder
- [ ] **Every test costs 0 model requests**

## Understanding check — answer out loud

- [ ] Why is a permission structural and a guardrail heuristic, and why must neither do the other's job?
- [ ] Why is asking a human before a `frozenset` lookup indefensible, in one sentence?
- [ ] Why is a clicked-through approval gate worse than having none?
- [ ] Why does `approval_required` use `or` rather than `and`?
- [ ] Why does `PolicyRefused` inherit from `PermissionDenied` rather than `RuntimeError`?
- [ ] Why are `evaluate` and `enforce` two functions instead of one with a flag, and why does
      `resolver_policy.py` deliberately not build an `Agent`?
- [ ] Why can a human approve a write and the output guardrail still refuse it?
- [ ] What does `allowed_callers` buy that Day 8's table does not — and vice versa?
- [ ] What does the managed platform layer lock that you cannot take with you?

## Budget & freshness

- [ ] Model requests logged in `docs/RATE_BUDGET.md` (declared: ~9, Groq)
- [ ] Confirmed a tripped **input** guardrail costs 0 requests (fires before the first model call)
- [ ] Confirmed in **0.22.0**: `function_tool(name_override=..., failure_error_function=...)`,
      the guardrail decorator / exception names, and `RunContextWrapper.context`
- [ ] **Checked whether 0.22.0 has a native tool-approval / run-interruption hook** — if it does,
      logged it; today's `enforce()` is the free stand-in and the plan needs an amendment before
      AG-20 (Day 50). Do not silently adapt (Principle 14).
- [ ] `allowed_callers` shape + what omitting it means, read from the live Responses docs
- [ ] AgentKit component names confirmed current (products get renamed)
- [ ] Plan inconsistency noted: OAI-23 is marked 🛠️ but names `allowed_callers`, which is 🅿️ per
      OAI-17 — logged in `docs/CHANGELOG_PLAN.md`

## Phase-3 gate readiness (tomorrow)

- [ ] Docker Desktop installed **and running**; Day 19's sandbox tests pass
- [ ] `docs/explainers/paid-harness-and-sandbox.md` (drafted Day 19) is finished and read aloud —
      **the gate requires it**
- [ ] Can state the gate in one line: a long-horizon file-touching agent on free models, inside the
      local Docker sandbox, plus the written explainer — and the keys have headroom for it

## Commit

```bash
./m check
./m done 21
```

- [ ] `./m done 21` succeeded — trackers updated automatically
- [ ] Tomorrow is the **Phase-3 gate** (Day 22) — clear the evening for it
