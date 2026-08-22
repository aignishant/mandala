# Day 43 — CHECKLIST

**IDs covered:** LG-01 🛠️ (graph thinking: state, nodes, edges), LG-02 🛠️ (state schemas & reducers)

## Demo command

```bash
uv run python days/day-43/lab/reducer_trap.py     # 0 requests — the whole lesson in two lines
uv run python days/day-43/lab/first_graph.py T-9002
uv run pytest tests/test_graph_state.py -v
```

Expected: `{'notes': ['beta ran']}` vs. `{'notes': ['alpha ran', 'beta ran']}`, then a four-node
graph drawn before it runs and one note per node in the final state.

## Setup

- [ ] `./m start 43` and `./m scaffold 43` run
- [ ] `langgraph` confirmed **pinned in `pyproject.toml`** (Day 42 §1) — not inherited
- [ ] Installed version matches the pin
- [ ] `src/mandala/graph/` created as the fourth framework namespace
- [ ] Files created (`graph/state.py`, `graph/nodes.py`, tests, three lab files)
- [ ] **Day 30's half-filled comparison table found and reopened before reading §3**

## LG-01 — nodes and edges

- [ ] Can state the two properties: nodes return updates; the loop is data
- [ ] Can say **why** returning updates enables checkpointing, replay and parallelism
- [ ] `nodes.py` written with thin bodies; the unfinished ones raise `NotImplementedError`
- [ ] `route_node` makes no model call — third framework, same rule
- [ ] `draw_ascii()` printed **before** `invoke()` — the habit for the whole phase
- [ ] Felt the cost of `TypedDict` having no defaults at the entry point

## LG-02 — reducers

- [ ] `reducer_trap.py` run — the one-annotation difference **observed, not read**
- [ ] **Extended it:** two nodes from `START` in the same super-step, no reducer
- [ ] Recorded what LangGraph does on an unreduced concurrent write (raise? clobber?)
- [ ] `append` written with a bound, and the **recent** end kept
- [ ] `keep_first` written — write-once
- [ ] `take_max_severity` written — a **domain** reducer, fail-safe
- [ ] `add_messages` used for `messages` rather than hand-rolled
- [ ] Noticed `findings` is bounded at the writer, not in the reducer — decision made and recorded
- [ ] Can say why the reducer is attached to the **field** rather than the node

## The comparison (§4) — the promise from Day 30

- [ ] `state_compare.md` table completed, both columns
- [ ] Concurrent-write row filled from **your own experiment**
- [ ] Day-30 prediction compared against what is actually here
- [ ] Answered: deletion (D30) vs. write-once (D43) — **and named the failure mode each still has**
- [ ] Noted that Day 48's subgraphs give the third option

## Tests that must be able to fail

- [ ] `test_append_concatenates`
- [ ] `test_append_is_bounded`
- [ ] `test_append_keeps_the_recent_end` — **flip it:** slice `[:N]`, see red
- [ ] `test_keep_first_refuses_to_overwrite`
- [ ] `test_keep_first_accepts_the_first_write`
- [ ] `test_severity_merges_fail_safe[4 rows]` — **flip it:** use `min()`, downgrade a critical
- [ ] `test_severity_merge_is_order_independent` — **commutativity**, all 16 pairs
- [ ] `test_unknown_severity_does_not_crash_the_graph`
- [ ] `test_every_collection_field_declares_a_reducer` — with `include_extras=True`
- [ ] `test_the_body_is_write_once`
- [ ] `test_the_schema_is_still_day_4s` — fifth framework
- [ ] All tests cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why can't you checkpoint, replay or parallelise over a shared mutable object?
- [ ] What is a reducer, in one sentence, and why does it live on the field?
- [ ] Why must a reducer be commutative, and what breaks if it isn't?
- [ ] What does `TypedDict` cost you compared with Day 30's Pydantic state?
- [ ] Which end of a bounded list should survive, and why?
- [ ] Deletion or write-once — which protects what?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~6, Groq)
- [ ] Compared against Days 23 and 30 — "cost to learn this framework" recorded for the bake-off
- [ ] `StateGraph` / `START` / `END` import paths confirmed
- [ ] `add_messages` import path confirmed
- [ ] **Pydantic-state-with-reducers question answered** and written into `state_compare.md`
- [ ] Unreduced concurrent-write behaviour recorded
- [ ] `DeltaChannel` name noted for Day 47
- [ ] Node timeouts / error recovery / graceful shutdown confirmed present for Day 49
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 43
```

- [ ] Bake-off rows updated: **state model**, **concurrency semantics**, **cost to learn**
- [ ] `./m done 43` succeeded — trackers updated automatically
