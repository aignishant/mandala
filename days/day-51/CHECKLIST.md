# Day 51 — CHECKLIST

**IDs covered:** LG-10 🛠️ (time travel & forking), LG-16 🅿️+lab-lite (the Functional API)

## Demo command

```bash
uv run python days/day-51/lab/history.py T-9002 a1           # 0 requests
uv run python days/day-51/lab/fork_and_compare.py T-9002 a1  # ~4 requests
uv run python days/day-51/lab/functional_port.py T-9002      # <= 6 requests
uv run pytest tests/test_timetravel.py -v
```

Expected: a checkpoint table, a forked branch that escalates, and the original history still intact.

## Setup

- [ ] `./m start 51` and `./m scaffold 51` run
- [ ] No new packages
- [ ] A **completed run exists** in `.mandala/graph/` (re-run Day 50's lab if not)
- [ ] Files created (`graph/timetravel.py`, tests, four lab files)

## LG-10 — time travel

- [ ] Can state the three operations, and the fork-vs-rewind difference
- [ ] `history.py` run; **checkpoint ids and `next` lists read**
- [ ] Snapshot count checked against your model of super-steps — and the model corrected if wrong
- [ ] Watched `ticket_body` disappear down the history — Day 47's scrub node, visible
- [ ] `checkpoint_before(node=...)` located by **`next`, not by index** — and can say why
- [ ] Newest-match tie-break rule chosen **and pinned by a test**
- [ ] `fork()` spreads the existing `configurable` — `thread_id` preserved
- [ ] `as_node` passed, and its reducer-attribution meaning understood
- [ ] **Downgrade experiment run:** forked `severity="low"`, watched `take_max_severity` refuse it
- [ ] Original history confirmed intact by snapshot count
- [ ] Fork cost (~4) recorded against full-run cost (~11)

## LG-16 — the Functional API

- [ ] Ported a **slice** only: triage → route → lane
- [ ] `choose_lane` **imported unchanged** — policy is API-agnostic
- [ ] The same triage agent reused, **not rewritten** — or the comparison is void
- [ ] Checked that functional runs checkpoint into the **same store**
- [ ] Noticed what is absent: no `StateGraph`, no `TypedDict`, no reducers, no edges
- [ ] `functional_compare.md` table completed
- [ ] **"Can I draw it?" row filled** — and noticed it also appeared in Day 34's DSL comparison
- [ ] Answered: what was the graph actually buying me?
- [ ] Answered: where would I use the Functional API — **by workflow shape, not size**
- [ ] Did **not** conclude "the graph is better"

## Tests that must be able to fail

- [ ] `test_finds_the_checkpoint_where_a_node_was_next`
- [ ] `test_the_newest_match_wins` — a docstring rule, pinned
- [ ] `test_a_missing_node_raises_with_its_name`
- [ ] `test_forking_preserves_the_thread_id` — **flip it:** rebuild the config, see red
- [ ] `test_forking_passes_as_node_through`
- [ ] `test_forking_without_values_is_a_pure_rerun`
- [ ] `test_resume_passes_none_as_input`
- [ ] `test_the_severity_reducer_still_protects_a_fork` — Day 43 defending Day 51
- [ ] `FakeGraph` records its calls — the technique for testing a function that calls something
- [ ] All tests cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why does time travel exist only because of Day 47?
- [ ] Why fork rather than rewind?
- [ ] Why locate a checkpoint by `next` rather than by index?
- [ ] What does `as_node` change, and what breaks if it is wrong?
- [ ] What does a forked comparison prove, and what does it **not** prove?
- [ ] When is a graph worse than four lines of Python?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~10, Groq)
- [ ] **Fork-vs-full-run ratio recorded** — the budget argument for time travel
- [ ] `get_state_history` ordering confirmed
- [ ] Snapshot attributes confirmed (`.next`, `.values`, `.config`)
- [ ] `update_state` return value confirmed
- [ ] **`as_node` reducer semantics proved by experiment**, not assumed
- [ ] Fork-creates-a-branch confirmed by snapshot count
- [ ] `langgraph.func` import path and decorator signatures confirmed
- [ ] Whether interrupts work in the Functional API — answered
- [ ] Whether both APIs share the checkpoint store cleanly — answered
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 51
```

- [ ] Bake-off rows updated: **replayability**, **cost of a controlled comparison**, **two APIs, one
      runtime**
- [ ] `./m done 51` succeeded — trackers updated automatically
