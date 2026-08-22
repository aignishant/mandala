# Day 14 — CHECKLIST

**IDs covered:** OAI-11 🛠️ (multi-agent patterns), OAI-12 🛠️ (tracing)

## Demo command

```bash
cd days/day-14/lab
uv run python pipeline_demo.py T-1004        # two roots in the tree
uv run python supervisor_demo.py T-1004      # one root, everything nested
uv run python span_tree.py                   # the artifact of the day
cd ../../..
```

Run the first two **back to back**, then read both trees. The shape difference is the lesson.

## Setup

- [ ] `./m start 14` and `./m scaffold 14` run
- [ ] No new packages (OTel is Day 75 — do not add it early)
- [ ] **`.mandala/` added to `.gitignore` BEFORE the first traced run**
- [ ] Files created (`src/mandala/tracing.py`, `src/mandala/topologies.py`, three lab files,
      `tests/test_tracing.py`, `tests/test_topologies.py`)
- [ ] `quoting_brief`, `honest_brief`, `mandala_context` fixtures added to `tests/conftest.py`

## OAI-11 — topologies

- [ ] Can say which SDK primitive builds each of Day 8's four topologies
- [ ] Can state why **the SDK has no pipeline construct** — and why that is the thesis, not a gap
- [ ] `researcher()` / `resolver()` are **factories**, not module-level agents
- [ ] `resolver()` holds **no** `get_ticket` — the separation is an omission, not a request
- [ ] The pipeline seam is a `Brief`, serialised with `model_dump_json()`
- [ ] `assert_no_raw_ticket()` written (the TODO(me)) — window size chosen **and justified**
- [ ] Both `Runner.run` calls are inside **one** `with trace(...)`
- [ ] `custom_span("step.research")` / `("step.resolve")` — your vocabulary in the trace
- [ ] `group_id=context.request_id` — Day 12's field finally earns its docstring
- [ ] Supervisor built from `as_tool()`, with a **"Do NOT"** clause on `draft_resolution`
- [ ] Noticed that the pipeline's ordering is a *line of Python* and the supervisor's is a *sentence*
- [ ] `result.last_agent.name` is `Supervisor` — control never left
- [ ] Can recite the §3.5 comparison table, especially the last row (**test vs. trace**)
- [ ] §3.6 "where the SDK stops" table copied into the **ADR-001 draft** for Day 16

## The ordering experiment (§4.5) — do not skip

- [ ] Supervisor run **5 times** on the same ticket
- [ ] Counted how often the tool order matched the instruction: **___ / 5**
- [ ] That number written here, not remembered
- [ ] Understood why the pipeline cannot produce that number at all

## OAI-12 — tracing

- [ ] Day 9's `set_tracing_disabled(True)` **removed** from `src/mandala/sdk.py`
- [ ] Day 9's `test_tracing_is_disabled_on_import` **replaced**, not deleted
- [ ] Used `set_trace_processors([...])`, **not** `add_trace_processor` — can say why
- [ ] `install_local_tracing()` called from the **entry point**, never at library import
- [ ] `JsonlTraceProcessor` implements all four hooks (+ `force_flush` / `shutdown`)
- [ ] `_write` **swallows every exception** — can defend that choice out loud
- [ ] `threading.Lock` around the append
- [ ] `SAFE_SPAN_FIELDS` is an **allowlist**; can say why a denylist fails
- [ ] `MAX_VALUE_CHARS` cap applied to every string, list capped too
- [ ] `span.error` recorded — failures are the traces you actually read
- [ ] **Printed `vars(span)` and `vars(span.span_data)`** and fixed the field names from reality
- [ ] `duration_ms()` written (the TODO(me)) — found out what `started_at` actually is
- [ ] `span_tree.py` prints a tree, a model-call count, and errors
- [ ] Pipeline tree has **two roots**; supervisor tree has **one**
- [ ] Model-call counts recorded: pipeline **___**, supervisor **___**
- [ ] Read §4.6 and can name the three destinations (today / Day 73 / Day 75)

## Tests that must be able to fail

- [ ] `test_resolver_cannot_read_tickets`
- [ ] `test_researcher_holds_no_write_tool`
- [ ] `test_agent_tools_match_the_permission_table`
- [ ] `test_supervisor_exposes_both_agents_as_tools`
- [ ] `test_supervisor_warns_against_passing_raw_tickets` — the prose lint
- [ ] `test_both_topologies_are_registered`
- [ ] `test_assert_no_raw_ticket_catches_a_quoting_brief` **and** `..._accepts_an_honest_brief` — the pair
- [ ] `test_a_broken_record_does_not_kill_the_run` — **flip it:** delete the `try`, confirm red
- [ ] `test_every_record_is_one_json_line`
- [ ] `test_summarise_drops_unknown_fields` — the canary, in a pure function
- [ ] `test_long_values_are_capped`
- [ ] `test_no_processor_points_at_openai` — ships failing; make it pass properly
- [ ] `test_a_pipeline_is_one_trace_not_two` — **flip it:** remove `with trace(...)`, confirm 2 files
- [ ] `test_the_trace_file_never_contains_the_canary` — the security test
- [ ] Configuration + redaction tests cost **0 model requests**
- [ ] Cassettes recorded; suite replays offline

## Understanding check — answer out loud

- [ ] Why does the SDK give you a supervisor but not a pipeline?
- [ ] Where does the ordering constraint live in each topology, and what does that buy you?
- [ ] Why is `add_trace_processor` the wrong call on **this** project specifically?
- [ ] What does `with trace(...)` change about two `Runner.run` calls?
- [ ] Why an allowlist rather than a denylist in `summarise()`?
- [ ] Why must a trace processor never raise?
- [ ] Which two rows of the §3.6 table would push you to LangGraph first, and why?
- [ ] What does a span tree tell you that `include_usage=True` does not — and vice versa?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~66, Groq)
- [ ] **Confirmed whether LiteLLM produces generation or response spans** — `model_calls()` depends on it
- [ ] Confirmed the `TracingProcessor` method names in 0.22.0
- [ ] Found the accessor for the installed processor list (Day 9's open question, closed)
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 14
```

- [ ] `./m done 14` succeeded — trackers updated automatically
