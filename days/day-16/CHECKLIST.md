# Day 16 — CHECKLIST

**IDs covered:** OAI-15 🛠️ (MCP in the Agents SDK — mount, filter, cache, approvals) · **PHASE-2 GATE 🎯**

## Demo command

```bash
uv run python days/day-16/lab/mcp_probe.py                  # 0 model calls
uv run python days/day-16/lab/approval_demo.py              # 0 model calls
uv run python days/day-16/lab/gate_demo.py                  # all three gate cases
uv run python days/day-14/lab/span_tree.py                  # the trace, per case
```

## Setup

- [ ] `./m start 16` and `./m scaffold 16` run
- [ ] `uv add "mcp==2.0.0"` — **pin what actually resolved**
- [ ] Read the Day-16 ledger row in `docs/PINS.md` (added today) and entry 2 of `docs/CHANGELOG_PLAN.md`
- [ ] Confirmed **no `httpx` today** — stdio only; streamable HTTP is Day 53
- [ ] Noted that `docs/01_MASTER_PLAN_ADDENDUM_GAPS.md` is **absent** — verify MCP claims against the live spec
- [ ] Files created: `mcp_servers/ticket_db.py`, `src/mandala/mcp_mount.py`, three lab files, two test files
- [ ] `mcp_servers/` is **top-level**, not under `src/mandala/` — can say why (Day 55)

## The server (§3.3)

- [ ] Two tools, both read-only; **no write tool exists in the file at all**
- [ ] Nothing in it imports from `src/mandala/` — can say why that is the boundary
- [ ] Config arrives by environment (`MANDALA_TICKETS`) — `MandalaContext` does **not** cross a process
- [ ] Body clipped server-side; empty case returns **a sentence**, not `[]`; docstrings written as prompts

## The spec (§3.2) — say which matter today

- [ ] Stateless core, no `initialize` — matters **indirectly**
- [ ] `Mcp-Method` / `Mcp-Name` headers — **not today** (stdio has no headers); Day 53 / Day 85
- [ ] **Cacheable, stably-ordered list results — matters directly**; it is why `cache_tools_list=True` is sound
- [ ] Extensions (Apps/Tasks/EMA) → Day 57; Elicitation → Day 56; deprecations → Day 58
- [ ] Can explain why deprecated Sampling means a server **cannot** call my model

## The mount (§3.4–3.5)

- [ ] `mcp_probe.py` run; **read both tool descriptions out loud** as if a stranger wrote them
- [ ] Tools discovered: **___** · digest: **___**
- [ ] Changed one word in a server docstring, re-ran the probe, **fingerprint moved**: **___**
- [ ] `filtered=True` and `cache=True` are the defaults; `client_session_timeout_seconds` pinned
- [ ] `fingerprint()` written (TODO(me)) — **one sentence in the ADR defending the fields chosen**
- [ ] `assert_declared()` written (TODO(me)) — can say why a check that passes trivially is worth writing
- [ ] Found and noted the **tool-list invalidation** method name: **___**

## The collision and the table (§3.6)

- [ ] Triage agent has `tools=[]` and `mcp_servers=[...]` — can say what breaks if both are passed
- [ ] Day 10's `sdk_tools.py` left **unchanged**
- [ ] `uv run pytest tests/test_permissions.py -q` green; `trifecta_violations()` still `[]`
- [ ] Open question written into the ADR: is declaring a stranger's `fetch_record` policy or rubber stamp?

## Approvals (§3.7) — Principle 12

- [ ] Can state the difference between a **filter** (what it sees, build time) and an **approval** (what it does, run time)
- [ ] `HostedMCPTool` 🅿️ shape understood — and why hosted MCP is HTTP-only by construction
- [ ] `ApprovalGate` a **wrapper**, not a subclass; `__aenter__`/`__aexit__` explicit; `NEEDS_APPROVAL` genuinely **empty**
- [ ] `console_approver()` written (TODO(me)) — **non-tty returns False without blocking**
- [ ] `approval_demo.py` run: gated tool still **visible**: **___** · call **denied**: **___** · ungated tool still works: **___**
- [ ] Checked §8 first: does 0.22.0 have a first-class approval hook for local MCP tools? **___** (if yes, delete `ApprovalGate`)

## The Phase-2 gate (§4)

- [ ] `gate_demo.py` runs all three cases end to end
- [ ] `--case clean` → ran to completion, model requests: **___**
- [ ] `--case secret` → guardrail tripped, model requests: **___** (expected 0)
- [ ] `--case billing` → `last_agent` = **___** (expected `Billing`)
- [ ] `span_tree.py` read for each case — spans: **___** · model calls: **___**
- [ ] **Evidence table filled — all 14 rows, each naming its command**
- [ ] Any failed row **recorded honestly**, not edited into passing: **___**

## ADR-001

- [ ] `docs/adr/ADR-001-what-the-sdk-owns.md` written from `docs/adr/ADR-TEMPLATE.md` **verbatim**
- [ ] Title states a **decision**, not a topic
- [ ] Options table includes **"C — do nothing"**
- [ ] Every option row has something in the **Evidence** column (a trace, a test name, a request count)
- [ ] Fed by Day 13 (handoff vs. `as_tool`), Day 14 ("the SDK has no pipeline" + "where the SDK stops"),
      Day 15 ("what I chose not to rent"), Day 16 (`MCP_ALLOWED`, filter vs. approval)
- [ ] At least one **genuinely worse** accepted cost named
- [ ] "What would make us revisit this" is **observable**, not "if it becomes a problem"
- [ ] The interview answer written — three or four sentences, no notes
- [ ] **Cold-read sign-off scheduled for +24h** — checkbox left unsigned today

## Tests that must be able to fail

- [ ] `test_the_server_never_imports_the_application`
- [ ] `test_every_accepted_tool_is_declared_in_the_permission_table`
- [ ] `test_an_undeclared_tool_is_refused` — **flip it:** delete the `not in TOOLS` branch, watch it go green
- [ ] `test_a_declared_read_only_list_is_accepted` — the other half of the pair
- [ ] `test_a_reworded_description_changes_the_fingerprint` — the day's thesis, asserted
- [ ] `test_the_fingerprint_is_stable_across_calls`
- [ ] `test_the_mount_is_filtered_by_default` + `test_the_child_runs_in_this_project_environment`
- [ ] `test_an_ungated_tool_is_not_blocked_by_the_approval_gate` — ships red on purpose
- [ ] `test_the_server_answers_a_real_tools_list` — one subprocess, **0 model requests**
- [ ] `test_the_triage_agent_pins_its_model`
- [ ] `test_the_triage_agent_has_guardrails_on_both_sides`
- [ ] `test_the_triage_agent_holds_no_local_ticket_tools`
- [ ] `test_the_handoff_is_filtered` + `test_the_billing_handoff_says_what_not_to_send_it`
- [ ] `test_the_trifecta_is_still_empty`
- [ ] `test_the_gate_trace_never_contains_the_canary` — Day 14's canary, now across a pipe
- [ ] Every test but the last costs **0 model requests**

## Understanding check — answer out loud

- [ ] What exactly do you stop controlling when a tool arrives over MCP?
- [ ] Which 2026-07-28 spec property makes `cache_tools_list=True` safe rather than racy?
- [ ] Why do `Mcp-Method` / `Mcp-Name` not apply to today's mount?
- [ ] What is the difference between a tool filter and an approval, in one sentence each?
- [ ] Why is `assert_declared()` worth writing on a day it cannot possibly fire?
- [ ] What breaks if both the Day-10 `get_ticket` and the MCP `get_ticket` are given to one agent?
- [ ] Why does an approval prompt need a non-tty path, and what happens if it doesn't have one?
- [ ] What does mounting this server buy on Day 55 that a function tool would not?

## Budget & freshness

- [ ] Model requests logged in `docs/RATE_BUDGET.md` (declared: **≈ 35, Groq**)
- [ ] Confirmed by observation: **MCP discovery, filtering and fingerprinting cost 0 model requests**
- [ ] `mcp` 2.0.0 API verified in a REPL; `MCPServerStdio` kwargs verified against 0.22.0 docs, not this lesson
- [ ] Live MCP spec page checked — still revision **2026-07-28**? **___** (a newer one = Principle 14, stop)
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 16
git tag phase-2-complete
```

- [ ] `./m done 16` succeeded — trackers updated automatically
- [ ] Repo tagged **`phase-2-complete`** (Day 59's bake-off will want it)
- [ ] **Tomorrow: sign the ADR-001 cold-read** before starting Day 17 (streaming, OAI-16 / AG-28)
