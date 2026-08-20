# Day 40 — CHECKLIST

**IDs covered:** LC-09 🛠️ (`stream_events` v3), LC-10 🛠️ (short-term memory & threads)

## Demo command

```bash
uv run python days/day-40/lab/memory_edges.py    # 0 requests — fake model
uv run python days/day-40/lab/event_zoo.py       # <= 6 requests — run ONCE, save output
uv run python days/day-40/lab/render.py T-9002   # <= 6 requests
uv run pytest tests/test_lc_streaming.py -v
```

Expected: ~100 events from `event_zoo.py`, ~5 lines from `render.py`, and that ratio understood.

## Setup

- [ ] `./m start 40` and `./m scaffold 40` run
- [ ] No new packages — **`langgraph` deliberately not installed** (Day 43 owns it)
- [ ] `pytest-asyncio` decision made deliberately; if added, ledger row + changelog line
- [ ] Files created (`lc/streaming.py`, `tests/test_lc_streaming.py`, three lab files)

## LC-09 — streaming

- [ ] Can state the difference between a **token** stream and an **event** stream
- [ ] Can say why events matter more for an agent
- [ ] `event_zoo.py` run **once**, output **saved to notes** for Days 45 and 75
- [ ] `version="v3"` passed explicitly — and can say why pinning a wire format is Principle 4
- [ ] Real event-type names recorded; `INTERESTING` corrected to match
- [ ] Event envelope keys learned (`event`, `name`, `data`, `tags`, `run_id`)
- [ ] Noted how tags would identify a *second* model (e.g. a summarizer)
- [ ] Approximate event count for a six-turn run written down

## The renderer

- [ ] `streaming.py` written in `src/` — Day 78 reuses it
- [ ] `INTERESTING` is a small module-level constant, not an inline condition
- [ ] **Never yields model output verbatim** — and can say why that is security, not style
- [ ] Tool results reported as a **length**, never content
- [ ] `MAX_LINES` bound with a truncation notice
- [ ] `yield`, not `print` — I/O decisions belong to `render.py`
- [ ] `flush=True` in `render.py`, and can say what breaks without it
- [ ] Output volumes compared: `event_zoo.py` vs. `render.py`

## LC-10 — memory and the boundary

- [ ] `memory_edges.py` run in-process — history behaviour observed
- [ ] Same `thread_id` tried in a **new process** — the gap found by experiment
- [ ] Result compared side by side with Day 32's `kill_and_resume.py`
- [ ] `configurable` nesting understood — top-level `thread_id` is a silent no-op
- [ ] Three-row memory table filled in (Days 7, 32, and a **prediction** for Day 47)
- [ ] Can state the boundary generously: LangChain owns the message list, not the durability policy
- [ ] Can name the three hard questions a default memory backend would hide
- [ ] Written into `four_ways.md`

## Tests that must be able to fail

- [ ] `test_only_interesting_events_are_rendered`
- [ ] `test_tool_names_are_rendered`
- [ ] `test_tool_output_is_reported_as_a_length_not_content` — **flip it:** yield the output, see red
- [ ] `test_model_text_is_never_yielded_verbatim` (injection string)
- [ ] `test_the_stream_is_bounded` — asserts `MAX_LINES + 1`, off-by-one deliberate
- [ ] `test_an_empty_run_yields_nothing`
- [ ] `test_the_event_version_is_pinned`
- [ ] `test_the_interesting_set_is_small` — pins the design, not the behaviour
- [ ] `FakeAgent` used — **no LangChain, no keys, no network** in the test file

## Understanding check — answer out loud

- [ ] Why is the reduction the real work, not the stream?
- [ ] Why is an unpinned event-schema version a dependency problem?
- [ ] What can go wrong if you stream model text straight to an operator console?
- [ ] Why does every stream in this project have a ceiling?
- [ ] Where exactly does LangChain's memory stop, and why is stopping defensible?
- [ ] What did persistence actually cost you on Days 7 and 32, and what will it cost on Day 47?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~12, Groq)
- [ ] `astream_events` + `version="v3"` confirmed current
- [ ] Event-type names confirmed against a real run
- [ ] Tool result location (`data.output`) confirmed
- [ ] Whether a **sync** event stream exists — noted for Day 78
- [ ] `thread_id` under `configurable` confirmed; cross-process behaviour recorded
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 40
```

- [ ] Bake-off rows updated: **streaming granularity** and **memory: what the framework owns**
- [ ] `./m done 40` succeeded — trackers updated automatically
