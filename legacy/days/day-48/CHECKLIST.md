# Day 48 — CHECKLIST

**IDs covered:** LG-11 🛠️ (subgraphs), LG-12 🛠️ (supervisor pattern), LG-13 🅿️ (swarm/peer) ·
**AG-11 completed**

## Demo command

```bash
uv run python days/day-48/lab/nested_draw.py    # 0 requests — three drawings
uv run pytest tests/test_subgraph.py tests/test_supervisor.py -v
```

Expected: the Research subgraph alone, the parent with Research as **one box**, and the same parent
expanded with `xray=True`.

## Setup

- [ ] `./m start 48` and `./m scaffold 48` run
- [ ] No new packages
- [ ] Files created (`graph/research.py`, `graph/supervisor.py`, two tests, two lab files)

## LG-11 — subgraphs

- [ ] Can fill in the five-row shared-state vs. own-state table
- [ ] Chose **own state + mapping**, and can say why shared state recreates Day 30's problem
- [ ] `ResearchState` has ≤5 fields, and its docstring **names what is absent**
- [ ] `to_research` is an **allowlist**, not a filter
- [ ] Research receives `triage.summary`, never `ticket_body` — and the residual risk noted for Day 65
- [ ] `from_research` bounds both lists on the way out
- [ ] `notes` carries a **count**, not the findings — Day 45's rule, now in state
- [ ] `research_node` is three lines: map in, invoke, map out
- [ ] `kb.search()` still called with the **Day-15 signature** — 33 days, four frameworks
- [ ] **Day 44's fan-out moved INSIDE the subgraph** — the parent does not know Research is parallel
- [ ] Can recite the four-step progression: delete → write-once → private payload → separate schema

## `nested_draw.py`

- [ ] All three drawings printed and **saved** for Day 52's gate and Day 89's portfolio
- [ ] `xray=True` parameter confirmed for 1.2.11
- [ ] Can state the pair: it hides complexity, **and** you can still see all of it

## LG-12 — the supervisor

- [ ] `pick_worker` is a **pure function** — no model
- [ ] `MAX_DELEGATIONS` checked **first**, and can say why last is the bug
- [ ] `supervisor_node` returns a `Command` — record and jump, atomically
- [ ] Can say why two nodes would be wrong here (a crash between them leaves a lie)
- [ ] Every delegation recorded in `notes` — countable on Day 71
- [ ] `delegations` arithmetic decided (reducer vs. computed at the site) and written down
- [ ] Four-framework supervisor table completed (Days 14, 25, —, 48)
- [ ] Can name what a routing function **loses** vs. a manager LLM

## LG-13 — `topologies.md`

- [ ] Four-topology table filled, each anchored to a day you built it
- [ ] **Turn arithmetic actually done** for a 3-worker supervisor
- [ ] Converted to a free-tier number (requests/day spent on routing)
- [ ] Peer handoff's gain and loss both stated
- [ ] Manager-LLM vs. routing-function table filled, with the switching condition
- [ ] Coordination-overhead measurement recorded for **two** frameworks (Days 25 and 48)

## Tests that must be able to fail

- [ ] `test_the_subgraph_cannot_see_the_raw_body` — **flip it:** pass parent state through, see red
- [ ] `test_the_subgraph_cannot_see_the_draft_or_the_conversation`
- [ ] `test_the_mapping_is_an_allowlist_not_a_filter` — **the test for six months from now**
- [ ] `test_research_receives_the_summary_not_the_body`
- [ ] `test_an_unclassified_ticket_maps_to_an_empty_question`
- [ ] `test_only_declared_keys_cross_back`
- [ ] `test_the_return_is_bounded`
- [ ] `test_notes_report_a_count_not_the_findings`
- [ ] `test_the_subgraph_schema_is_small`
- [ ] `test_no_triage_escalates` / `test_critical_escalates`
- [ ] `test_research_comes_before_draft` / `test_draft_comes_after_findings` / `test_done_when_a_draft_exists`
- [ ] `test_the_delegation_cap_wins_over_everything` — **flip it:** check the cap last, see a spin
- [ ] `test_the_cap_is_small`
- [ ] `test_the_supervisor_costs_no_model_call` — **the LG-12 vs. CR-05 difference, asserted**
- [ ] `test_the_command_records_the_choice_and_the_jump_together`
- [ ] All tests cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why is a subgraph's state schema a capability declaration?
- [ ] Why does an allowlist beat a filter at a subsystem boundary?
- [ ] What are the four answers to "stop this component seeing that field", in order?
- [ ] Why does the fan-out belong inside Research rather than in the parent?
- [ ] Why must the delegation cap be checked first?
- [ ] How many requests does a model supervisor spend on pure coordination, for three workers?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~12, Groq)
- [ ] Compared against Day 25's hierarchical crew — coordination overhead as a fraction
- [ ] `xray` parameter form confirmed
- [ ] Shared-state subgraph path confirmed, so you know what you are declining
- [ ] **Whether a nested subgraph gets its own checkpoints** — Day 51 depends on the answer
- [ ] `Command` targeting a parent node — question from Day 44 answered
- [ ] `Send` inside a subgraph confirmed to work
- [ ] `Command.goto` to `END` confirmed
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 48
```

- [ ] Bake-off rows updated: **composition**, **supervisor cost**, **coordination overhead**
- [ ] `./m done 48` succeeded — trackers updated automatically
