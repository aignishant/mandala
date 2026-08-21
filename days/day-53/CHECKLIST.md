# Day 53 — CHECKLIST

**IDs covered:** MCP-01 🛠️ (the N×M problem), MCP-02 🛠️ (the 2026-07-28 stateless core),
MCP-12 🅿️ (governance & registry)

## Demo command

```bash
uv run python days/day-53/lab/wire_shape.py     # 0 requests
uv run pytest tests/test_tool_parity.py -v
```

## §1 — the missing reference, FIRST

- [ ] Option chosen: **carry over** `01_MASTER_PLAN_ADDENDUM_GAPS.md`, **or** repoint the references
- [ ] `CLAUDE.md` and the plan's Part 2 now name a reference that **actually exists**
- [ ] Decision logged in `docs/CHANGELOG_PLAN.md`
- [ ] **MCP spec revision verified as still 2026-07-28** — the load-bearing check for six days
- [ ] If it moved: **stopped**, and wrote an addendum before teaching anything

## Setup

- [ ] `./m start 53` and `./m scaffold 53` run
- [ ] **Nothing installed** — `mcp==2.0.0` arrived on Day 16
- [ ] Checked whether `httpx` is needed on Day 54 or only Day 55; ledger row moved if wrong
- [ ] Files created (`wire_shape.py`, `tests/test_tool_parity.py`)

## MCP-01 — the N×M problem, with your own evidence

- [ ] All four per-framework tool declarations **read side by side**
- [ ] Q1 — same tool name in all four? **answered**
- [ ] Q2 — does the `T-\d{4}` constraint exist in all four, or only LangChain's? **answered**
- [ ] Q3 — does each bound its result? **answered**
- [ ] Q4 — do the descriptions (which are prompt text) say the same thing? **answered**
- [ ] Divergence recorded as the day's headline finding — correctness cost, not typing cost
- [ ] Can state the 4×K → 4+K argument using **your own numbers**
- [ ] **Prediction written** for what MCP does to `InjectedToolArg` (D37) and `permissions.py` (D12)

## MCP-02 — the stateless core

- [ ] Can fill in the four-row before/after table
- [ ] Can give the **deployment consequence** of each row, not just the protocol change
- [ ] Understands why "no session pinning" means no sticky sessions in the LB (Day 85)
- [ ] Understands why headers let a router work without parsing a body
- [ ] Understands why stable ordering makes change-detection possible (Day 66)
- [ ] `wire_shape.py` run; **headers read separately from the body**
- [ ] Noticed the redundancy between `Mcp-Name` and `params.name`, and asked who is authoritative
- [ ] **All five spec questions answered from the specification** and written into the file
- [ ] Can say the "stateful core, stateless edges" sentence and explain why it is not a contradiction
- [ ] Connected it forward to LG-21 (Day 86)

## MCP-12 — governance

- [ ] Agentic AI Foundation (Linux Foundation, Dec 2025) — noted
- [ ] Official registry — noted, **and understood as a supply chain**
- [ ] Extensions framework on independent timelines — noted for Day 57
- [ ] Can say why vendor-neutrality makes Principle 11 durable rather than a bet
- [ ] Reframed MCP-15 (Day 66) from paranoia to dependency hygiene

## Tests that must be able to fail

- [ ] `test_every_framework_uses_the_same_tool_name[3]`
- [ ] `test_every_framework_constrains_the_ticket_id[3]` — **likely red; fixed or deferred in writing**
- [ ] `test_no_framework_tool_writes[3]`
- [ ] `test_every_framework_bounds_its_result[3]`
- [ ] `test_the_underlying_function_is_shared`
- [ ] `test_the_count_of_declarations_is_recorded` — the test that **fails on progress**
- [ ] Did **not** weaken a red test to make it pass
- [ ] All tests cost **0 model requests**

## Understanding check — answer out loud

- [ ] What did four declarations of one function actually cost you?
- [ ] What does "no initialize" mean for a load balancer?
- [ ] Why did routing information move into headers?
- [ ] What does stable ordering let you detect?
- [ ] Why is your agent stateful while the tool boundary is stateless?
- [ ] Why does foundation governance matter to an engineer, not just to a lawyer?

## Budget & freshness

- [ ] Logged in `docs/RATE_BUDGET.md`: **0 requests**
- [ ] Noticed the pattern: the free days produce the quotable artifacts
- [ ] `Mcp-Method` / `Mcp-Name` required-vs-optional, and per-transport applicability — answered
- [ ] Header-vs-body authority question — answered
- [ ] What replaced `initialize` — answered
- [ ] `tools/list` cacheability mechanism — answered
- [ ] "Stably ordered" scope — answered
- [ ] `mcp==2.0.0` still current and still tracking the 2026-07-28 revision
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 53
```

- [ ] Bake-off note started: **portability of the tool layer** — four declarations today, one server
      from Day 55
- [ ] `./m done 53` succeeded — trackers updated automatically
