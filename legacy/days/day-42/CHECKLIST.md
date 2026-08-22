# Day 42 — CHECKLIST 🎯 Phase-6 gate

**IDs covered:** LC-13 🛠️ (the LangChain↔LangGraph seam), LC-14 🛠️ (Phase-6 checkpoint artifact)

## Demo command

```bash
uv run python days/day-42/lab/seam_demo.py T-9002   # <= 6 requests
uv run pytest tests/test_seam.py -v                 # 0 requests
uv run pytest -m live -q                            # 2 requests — the provider swap
```

Expected: a three-node ASCII graph where one node is an entire LangChain agent, a `TriageResult` out
of the seam, and a green provider-swap test on two providers.

## §1 — the plan-internal inconsistency, FIRST

- [ ] Checked whether `langgraph` is installed transitively and **unpinned**
- [ ] Understood why an inherited, unpinned dependency violates Principle 4
- [ ] Live version verified before pinning
- [ ] `uv add "langgraph==..."` run — **or** §1 deliberately overruled
- [ ] `docs/PINS.md` ledger row moved from Day 43 to Day 42
- [ ] Amendment logged in `docs/CHANGELOG_PLAN.md`
- [ ] Can state the habit: reality disagrees → amend in writing → then change code

## Setup

- [ ] `./m start 42` and `./m scaffold 42` run
- [ ] `git status` clean before assembly
- [ ] Files created (`lc/seam.py`, `tests/test_seam.py`, `seam_demo.py`, `ADR-002-*.md`)
- [ ] `seam.py` placed in `src/`, **not** `days/` — and can say why

## LC-13 — the seam

- [ ] Can state the three-step chain: agent → compiled graph → Runnable → node
- [ ] `WorkflowState` is a `TypedDict`, **not** a message list — the day's design decision
- [ ] `keep_first` reducer written, and understood as a **write-once security primitive**
- [ ] Noticed `notes` replaces rather than appends — **left wrong on purpose**, observation recorded
- [ ] Nodes return **partial updates**, not mutated shared state — and can compare with Day 31
- [ ] Agent constructed **inside** the node, and the reason (test surface) written down
- [ ] `route_node` makes no model call — third framework, same rule
- [ ] Turn count captured at the seam and folded into `notes` (Day 76 will want it)
- [ ] `draw_ascii()` output saved **next to Day 38's** — two pictures, one nested in the other

## Gate evidence table (§4.1)

- [ ] Row 1 — middleware-hardened (scrubber first in the stack)
- [ ] Row 2 — secrets never reach a provider
- [ ] Row 3 — **provider-swap test green on two providers**
- [ ] Row 4 — the loop is capped
- [ ] Row 5 — `TriageResult` unmodified since Day 4
- [ ] Row 6 — the model cannot forge a `request_id`
- [ ] Row 7 — progress never leaks model text
- [ ] Row 8 — the agent runs as a node in a bigger graph
- [ ] Row 9 — scope decisions enforced
- [ ] Row 10 — ADR-002 written
- [ ] Row 11 — pins re-verified; drift logged or nil-reported
- [ ] Row 12 — the §1 amendment is written down
- [ ] Every cell carries a **filename or command**

## The provider-swap test (§4.2)

- [ ] Marked `@pytest.mark.live` — the Day-0 marker's first real use
- [ ] Confirmed `./m check` **skips** it
- [ ] Two providers, not three — and can say why the judge is excluded
- [ ] **Assertions are about shape, not content** — and can explain why that matters
- [ ] Agent built inline (the point is swapping the model), with a comment saying so

## ADR-002

- [ ] All three mechanisms compared: SDK guardrails / CrewAI task guardrails / LC middleware
- [ ] "Can it rewrite the payload?" row filled — the row that actually separates them
- [ ] "Cost per agent run" filled with a **number**, not an adjective
- [ ] "Testable without a provider?" answered honestly for all three
- [ ] Decision section justifies a **mix**, not one winner
- [ ] Phase-6 request total recorded and compared against Phase 5 (free-tier friendliness row)
- [ ] Reads like something a hiring panel could be handed (Principle 9)

## Tests that must be able to fail

- [ ] `test_the_router_is_the_same_policy_as_day_31[4 rows]`
- [ ] `test_an_unclassified_ticket_escalates` — third framework, same flip-it test
- [ ] `test_the_router_makes_no_model_call`
- [ ] `test_the_body_is_write_once`
- [ ] `test_the_outer_state_is_not_a_message_list`
- [ ] `test_the_graph_has_the_expected_shape`
- [ ] `test_the_seam_records_what_the_agent_cost`
- [ ] `test_langgraph_is_a_direct_dependency` — **or deleted, with the overrule written down**
- [ ] All non-live tests cost **0 model requests**

## Standing gate freshness check (§6)

- [ ] All six LangChain-family packages re-verified against `docs/PINS.md`
- [ ] MCP spec revision checked — ten seconds, and Day 53 benefits
- [ ] Result written in `docs/CHANGELOG_PLAN.md`, **nil report included if nothing moved**
- [ ] Minor/major drift → addendum **before** any pin changed

## Budget

- [ ] Actual counts logged in `docs/RATE_BUDGET.md` (declared: ~10)
- [ ] Phase-6 seven-day total computed and recorded

## Commit

```bash
./m check
./m done 42
```

- [ ] Phase-6 bake-off row complete: control, durability, HITL, testing, ops, velocity, lock-in,
      free-tier friendliness
- [ ] **Predictions written for Days 43, 47 and 50** — and compared against the ones made on Day 35
- [ ] `./m done 42` succeeded — trackers updated automatically
