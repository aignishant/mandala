# Day 58 — CHECKLIST 🎯 Phase-8 gate

**IDs covered:** MCP-11 🛠️ (deprecation lifecycle), MCP-13 🛠️ (agent over MCP), MCP-16 🛠️ (freshness
drill)

## Demo command

```bash
bash days/day-58/lab/gate_demo.sh
```

Expected: one server, four clients, a probe, a task seen by a second replica, a refused sampling
request, an agent answering as a tool, and a green suite.

## Setup

- [ ] `./m start 58` and `./m scaffold 58` run
- [ ] **No new dependencies**
- [ ] `git status` clean before assembly
- [ ] ADR number chosen without collision, and logged
- [ ] Files created (shim, agent server, two tests, four lab files, ADR)

## MCP-11 — the deprecation drill

- [ ] Can name all three deprecated features and what replaced each
- [ ] Can say **why** all three were untenable under a stateless core
- [ ] `old_style_server.py` written — **the specimen you need in order to recognise one**
- [ ] All six markers understood, especially `{"error": "not initialized"}` as the external tell
- [ ] Understood old Sampling: **your client, your key, your quota, its prompt**
- [ ] Connected the replacement (`InputRequiredResult` + opaque state) to the revision's thesis
- [ ] **Named the fourth instance** of "push state out of the server"
- [ ] `legacy_shim.py` written: **classify, adapt, refuse**
- [ ] Sampling **refused by default**, not proxied
- [ ] The refusal returns model-readable guidance, not an exception
- [ ] Logs stripped from the payload into your own logger
- [ ] Every extracted string bounded
- [ ] `classify` is honest about false positives — a tell is not a proof

## MCP-13 — agent over MCP

- [ ] The agent exposed as a tool, and called successfully
- [ ] **A separate server** (`mandala-triage`), not registered on `ticket-db`
- [ ] Can defend that: a server is a **blast-radius and cost boundary**
- [ ] Cost declared in the model-facing docstring (`EXPENSIVE`, ~11 calls)
- [ ] Description steers the model toward the cheap alternative
- [ ] Concurrency limit present
- [ ] **Statelessness tension decided**: per-process counter accepted, or moved to the shared store
- [ ] Heavy import kept inside the function
- [ ] Day 54's no-framework-imports test **deliberately scoped** to exclude this server, not weakened
- [ ] "Why is this not a Task?" answered
- [ ] §4.1's agent-as-tool vs. agent-as-peer table started, for Day 87

## MCP-16 — the freshness drill

- [ ] Spec revision checked on the revisions page
- [ ] `mcp` and all client packages checked against `docs/PINS.md`
- [ ] `freshness_2026-08-__.md` written
- [ ] **Verdict box ticked, including "checked, unchanged" if that is the answer**
- [ ] "What I looked at" section written so a future you can repeat it exactly
- [ ] **Time taken recorded** — and if it was over ten minutes, that noted as a process problem
- [ ] One line in `docs/CHANGELOG_PLAN.md`, **nil report included**
- [ ] Can say why an unwritten nil report is indistinguishable from not checking

## Evidence table (§6)

- [ ] Rows 1–15 all green
- [ ] Every cell carries a filename or command
- [ ] Row 14: `pytest -q` over the **whole** suite

## Tests that must be able to fail

- [ ] `test_classify_spots_a_legacy_server`
- [ ] `test_classify_spots_a_sampling_request`
- [ ] `test_classify_accepts_a_modern_response`
- [ ] `test_sampling_is_refused` — **flip it:** proxy it, see red
- [ ] `test_the_refusal_tells_the_model_what_to_do_instead`
- [ ] `test_logs_are_stripped_from_the_payload` (injection string)
- [ ] `test_adapted_text_is_bounded`
- [ ] `test_adapt_never_raises`
- [ ] `test_every_sampling_spelling_is_refused`
- [ ] `test_the_agent_tool_is_a_separate_server` — **both halves asserted**
- [ ] `test_the_agent_tool_declares_its_cost`
- [ ] `test_the_agent_tool_steers_toward_the_cheap_alternative`
- [ ] `test_the_heavy_import_is_inside_the_function`
- [ ] `test_there_is_a_concurrency_limit`
- [ ] `test_failures_return_guidance_not_exceptions`

## The demo

- [ ] Recorded, reading from `gate_demo.sh`
- [ ] Servers backgrounded **and cleaned up** — no orphaned port 8765
- [ ] Step 3 shown: probing your own server as a stranger would (previews Day 66)
- [ ] Step 5 shown: a legacy server recognised and its sampling request refused

## The ADR

- [ ] Q1 — was Principle 11 worth it? **Both sides counted**
- [ ] Q2 — the four instances of one idea, and the thesis in one sentence
- [ ] Q3 — the three authorisation layers, and which one Mandala actually relies on today
- [ ] Q4 — **prediction** for Day 87's agent-as-peer comparison
- [ ] Phase-8 request total recorded and compared with Phases 5 and 7
- [ ] Reads like something a hiring panel could be handed (Principle 9)

## Budget

- [ ] Actual counts logged in `docs/RATE_BUDGET.md` (declared: ~13, Groq)
- [ ] Phase-8 six-day total computed — **the strongest free-tier result in the plan**
- [ ] Noted as a Day-63 scorecard row: a protocol boundary is testable without a provider

## Commit

```bash
./m check
./m done 58
```

- [ ] **All comparison tables from Days 30–58 collected into one place tonight** — the bake-off
      starts tomorrow and hunting for them on Day 63 turns a scorecard into an opinion
- [ ] `./m done 58` succeeded — trackers updated automatically
