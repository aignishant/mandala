# Day 88 — CHECKLIST 🎯 Phase-13 gate

**IDs covered:** INT-04 🅿️ (AP2 mandates), INT-05 🅿️ (x402 / TAP awareness),
INT-06 🛠️ (interop capstone) · gate day

## Demo command

```bash
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.workers.yml up -d
uv run python days/day-85/lab/any_replica_test.py
uv run python days/day-86/lab/two_workers_one_thread.py T-9301
uv run python days/day-88/lab/partner_sim_both_paths.py     # run the ABUSE case first
uv run python scripts/audit_writes.py
uv run pytest -m "eval_unit or eval_trajectory" -q
```

Expected: 1 answer / 3 replicas; no node run twice; equivalent findings over MCP and A2A; three
abuses refused; audit still exit 0.

## Setup

- [ ] `./m start 88` and `./m scaffold 88` run
- [ ] **No new dependencies**
- [ ] Day 84's `Grant` re-read before writing the mandate model

## INT-04 — the mandate (concept + model)

- [ ] `Mandate` mirrors `Grant` deliberately — correspondence written in the ADR
- [ ] **Money is integers (minor units)**, never float
- [ ] `granted_by` is a human; noted that no type can enforce that
- [ ] `permits()` returns `(bool, reason)` — house style, fifth time
- [ ] Checks ordered: revoked → expired → agent → scope → cap
- [ ] Docstring says plainly that **local `revoked` is the wrong design** for real revocation, and why
- [ ] No open-ended mandates (expiry is a required field)
- [ ] `ap2_threat_model.md` written — four paragraphs:
  - [ ] what a mandate prevents that a prompt does not
  - [ ] **what happens under prompt injection while holding one** (bounds blast radius, not misuse)
  - [ ] where it must be checked (counterparty, not self) — mapped onto Day 82's write-tool check
  - [ ] what you would require before granting one (Day 84's rule)

## INT-05 — awareness only

- [ ] x402 described in one sentence (machine-payable 402 challenge)
- [ ] TAP-style identity attestation described in one sentence
- [ ] **Nothing implemented**; no opinions on settlement internals
- [ ] Both cited with today's date and the version read

## INT-06 — one organ, two contracts

- [ ] `expose_mcp.py` and `expose_a2a.py` are **thin adapters** over the same `research()`
- [ ] No research logic duplicated
- [ ] **Inbound questions wrapped as `Untrusted`** — and can say why this direction is new
- [ ] **Inbound calls budgeted** — a stranger cannot spend your free tier
- [ ] New attack added to the corpus as **RT-20** (inbound quota exhaustion)
- [ ] MCP path returns a value; A2A path manages a task with states — difference understood, not just
      implemented
- [ ] **Nothing but research exposed** — no drafter, no approval, no `post_reply`
- [ ] Mandala's own Agent Card published and signed (the other half of yesterday)

## The partner-sim, both paths (§4.1)

- [ ] Discovers and **verifies** Mandala's card
- [ ] Completes an A2A research task
- [ ] Calls the same capability over MCP (through the LB, or decision recorded)
- [ ] **Asserts findings are equivalent across both paths** — the INT-06 gate artifact
- [ ] Abuse 1: over-budget flood — refused (**run this first**)
- [ ] Abuse 2: request for an unexposed skill — refused
- [ ] Abuse 3: injected instruction in the question — fence held

## The Phase-13 gate

- [ ] Stateless API criterion evidenced
- [ ] Checkpointer-backed workers criterion evidenced (no double execution)
- [ ] 3-replica MCP criterion evidenced (including the replica-stop run)
- [ ] Partner-sim criterion evidenced on **both** paths, abuses included
- [ ] **Zero-unapproved-writes re-proved after distribution** — and can say why re-proving matters
- [ ] `docs/adr/gate-phase-13.md` written with a specific evidence column
- [ ] **"What is local-only and would change in a funded deployment"** written
- [ ] **"DEV ONLY items to remove" listed** (localhost card exemption, `x-replica` header, SQLite
      checkpointer, `replica` in responses, simulator keys…)
- [ ] Debts carried into Phase 14
- [ ] `/freshness` run; nil reports logged
- [ ] `git tag -a phase-13-complete`
- [ ] **ADR not signed today** — cold read tomorrow

## Tests that must be able to fail

- [ ] `test_money_is_integers_not_floats`
- [ ] `test_a_revoked_mandate_permits_nothing`
- [ ] `test_an_expired_mandate_permits_nothing`
- [ ] `test_scope_and_agent_are_both_checked`
- [ ] `test_the_cap_is_inclusive_and_enforced`
- [ ] `test_there_are_no_open_ended_mandates`
- [ ] `test_only_research_is_exposed_over_either_protocol` — **flip it:** expose the drafter
- [ ] `test_inbound_questions_are_untrusted`
- [ ] `test_inbound_calls_are_budgeted`
- [ ] `test_both_paths_call_the_same_organ`
- [ ] `test_the_exposed_agent_holds_no_write_tool`
- [ ] All cost **0 model requests**

## Understanding check — answer out loud

- [ ] How is an AP2 mandate the same object as your autonomy grant?
- [ ] What does a mandate NOT protect you from?
- [ ] Why is a self-checked mandate only a suggestion?
- [ ] What is genuinely different about serving MCP vs serving A2A?
- [ ] Why is inbound text untrusted, and why is that direction new for you?
- [ ] Why was exposing the Researcher safe, and which day made it so?

## Budget & freshness

- [ ] Request count logged in `docs/RATE_BUDGET.md` (declared: ~20)
- [ ] Abuse-flood cost recorded — **the cheap way to discover a missing inbound budget**
- [ ] A2A skill/task-handler schema verified on `a2a-sdk==1.1.2`
- [ ] Agent Card publication + signing verified
- [ ] `FastMCP` return-type and error-on-the-wire behaviour verified on `mcp==2.0.0`
- [ ] AP2 status read today and cited with the date
- [ ] Full `/freshness` sweep logged

## Commit

```bash
./m check
./m done 88
```

- [ ] Threat model, both adapters, partner-sim and gate ADR committed
- [ ] `./m done 88` succeeded
- [ ] **Day 89 not started until the cold read is done**
