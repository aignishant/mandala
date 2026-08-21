# Day 45 — CHECKLIST

**IDs covered:** LG-05 🛠️ (streaming modes), LG-15 🛠️ (`create_agent` nodes; prebuilt is dead),
AG-28 🅿️ (streaming UX)

## Demo command

```bash
uv run python days/day-45/lab/three_modes.py         # 0 requests — byte counts
uv run python days/day-44/lab/fan_out.py T-9002      # yesterday: 15 SILENT seconds
uv run python days/day-45/lab/watch_fanout.py T-9002 # today: the same 15, narrated
uv run pytest tests/test_graph_streaming.py -v
```

**Run the middle two back to back.** That comparison is AG-28.

## Setup

- [ ] `./m start 45` and `./m scaffold 45` run
- [ ] No new packages
- [ ] `days/day-36/lab/what_survived.py` **re-run** now that `langgraph` is installed
- [ ] Files created (`graph/streaming.py`, tests, three lab files)

## LG-05 — streaming modes

- [ ] Can say the reframing in one sentence: streaming a graph is streaming its state
- [ ] Three modes named, with what each yields
- [ ] `three_modes.py` run; **byte counts compared** — a number, not an impression
- [ ] Understood why `values` is wrong for a fan-out UI
- [ ] Extended it with `messages` mode, and noted it is **orthogonal**, not a third point on a scale
- [ ] Multi-mode return shape confirmed (`(mode, chunk)` tuples?)
- [ ] `graph/streaming.py` written with `updates` as the default

## The renderer

- [ ] `NODE_LABELS` translates node names to human phrases
- [ ] `describe()` uses the **shape** of an update, never its contents
- [ ] Inner loop over `chunk.items()` — fan-out chunks carry several nodes
- [ ] `update or {}` guard for a node returning `None`
- [ ] `MAX_LINES` bound with a truncation notice — third file with this shape
- [ ] `flush=True` in the lab script
- [ ] Noted that this one is **sync** while Day 40's was forced async — a portability finding

## LG-15 — the deprecation

- [ ] `langgraph.prebuilt` behaviour in 1.2.11 recorded (imports? warns? fails?)
- [ ] Deprecation message read and written down
- [ ] Understood the surprising direction: the graph library deprecated **its own** agent
- [ ] Can say what that implies about how the two packages are governed
- [ ] Established whether `add_node` accepts a compiled graph directly
- [ ] **Decided the house style**, and can name the three things Day 42's wrapper does that a bare
      agent does not
- [ ] Wrote down: "what did easy cost me?"

## AG-28 — `ux_note.md`

- [ ] The principle written in **your own words**
- [ ] Two-implementation table filled with real numbers
- [ ] "What was identical" section written — filter and security rule survived a framework change
- [ ] The 15-silent-seconds comparison actually run and described
- [ ] A line drawn for a real product (progress only? tokens for the final answer? nothing?)

## Tests that must be able to fail

- [ ] `test_node_names_become_human_labels`
- [ ] `test_finding_counts_are_reported_not_findings` — **flip it:** interpolate findings, see red
- [ ] `test_raw_state_is_never_echoed` (injection strings in two fields)
- [ ] `test_a_fanout_chunk_yields_one_line_per_node`
- [ ] `test_an_unknown_node_falls_back_to_its_name`
- [ ] `test_a_node_returning_none_does_not_crash`
- [ ] `test_the_stream_is_bounded`
- [ ] `test_updates_is_the_default_mode`
- [ ] `test_every_mandala_node_has_a_label` — a cross-file invariant with Day 44
- [ ] `test_describe_is_a_pure_function`
- [ ] `FakeGraph` used — **no LangGraph, no model, no keys**

## Understanding check — answer out loud

- [ ] Why is `updates` the right default, and what does `values` cost with a fan-out?
- [ ] Why is `messages` mode orthogonal to the other two?
- [ ] What is the security rule, and why is it the same rule as Day 40's?
- [ ] Why did LangGraph deprecate its own agent constructor?
- [ ] What three things does the wrapper do that dropping the agent into `add_node` loses?
- [ ] What survived the framework change unchanged, and why does that matter for Day 89?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~11, Groq)
- [ ] Noted that observability added **no** new spend — a bake-off row
- [ ] Stream mode names confirmed; any `custom`/`debug` modes noted
- [ ] Multi-mode yield shape confirmed
- [ ] Fan-out chunk shape confirmed (one chunk with many keys, or many chunks?)
- [ ] `add_node`-accepts-a-graph question answered
- [ ] `DeltaChannel` confirmed present for Day 47
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 45
```

- [ ] Bake-off rows updated: **streaming granularity**, **sync vs. async imposed by the framework**,
      **does observability cost quota?**
- [ ] `./m done 45` succeeded — trackers updated automatically
