# Day 17 — CHECKLIST

**IDs covered:** OAI-16 🛠️ (`run_streamed`, event types, rendering progress), AG-28 🅿️ (streaming UX,
concept + the three tensions)

## Demo command

```bash
cd days/day-17/lab
uv run python naked_stream.py                   # streaming with no framework: stream=True
uv run python stream_demo.py T-1004             # rich Live: tool calls + tokens as they arrive
uv run python first_token.py T-1004             # the number of the day — record it below
cd ../../..
```

## Setup

- [ ] `./m start 17` and `./m scaffold 17` run
- [ ] `uv add "rich==15.0.0"` — **pin what actually resolved** (ledger row for Day 17 already exists)
- [ ] Files created: `src/mandala/streaming.py`, three lab files, `tests/test_streaming.py`,
      `tests/test_stream_guardrails.py` — and **nothing else touched**. Streaming is additive.

## OAI-16 — naked first (§3.1)

- [ ] `naked_stream.py` run — text appeared a chunk at a time
- [ ] Can say what `stream=True` actually changes (one JSON body → server-sent events)
- [ ] Knows why it is `delta.content`, not `message.content`, and why `or ""` is the protocol
- [ ] `first_token_at` set on the first **non-empty** piece (not the role chunk)

## OAI-16 — `run_streamed` and the three families (§3.2–3.4)

- [ ] `Runner.run_streamed(...)` is **not awaited** — can say what goes wrong when you do
- [ ] `result.final_output` read only **after** the stream is exhausted
- [ ] Can name the three `event.type` families and **who each one is for**
- [ ] Can recite the rule: **raw deltas are for the eyeball; run-item events are for the program**
- [ ] Can say what `agent_updated_stream_event` is the streaming form of (Day 13's `last_agent`)
- [ ] Can give the three reasons for the seam: testability, version drift, boundedness

## OAI-16 — `src/mandala/streaming.py` (§3.5)

- [ ] Four typed events: `TokenDelta`, `ItemDone`, `AgentSwitched`, `Unclassified` (discriminated union)
- [ ] `classify()` is the **only** function naming SDK event types — counted the string literals: **___**
- [ ] Rule 1: unknown events become `Unclassified` and are **counted**, never dropped, never raised
- [ ] Rule 2: `MAX_DELTA_CHARS`, `MAX_LABEL_CHARS`, `MAX_ANSWER_CHARS` all enforced; `_delta_text()`
      returns `None` (not `""`) for a non-text event — can say why
- [ ] **TODO(me) rep 1:** `_delta_text()` written **after printing real events**, not guessed
- [ ] **TODO(me) rep 2:** `label_for()` written; returns `""` rather than raising; sliced to the cap
- [ ] `ProgressReducer` is synchronous and cannot raise (Day 14's `_write` instinct)
- [ ] `ttft_ms` returns `None` before the first token, not `0.0`
- [ ] `tool_calls` reads `tool_call_item` run items — **never** parsed out of `answer`
- [ ] `truncated` flag set on overflow, and the renderer shows it
- [ ] `may_stream()` / `deliver()` / `STREAM_SINKS` live **in** this module — can say why

## OAI-16 — the surface (§3.6)

- [ ] `stream_demo.py` run at least three times
- [ ] The demo agent has **no `output_type=Brief`** — can say why (§4.2), not "to keep it simple"
- [ ] Tool list unchanged from Day 14 — **streaming changed the view, not the permissions**
- [ ] `frame()` is a **pure function of reducer state**; `refresh_per_second=10`, not one per delta
- [ ] Watched `first progress` land while `first token` was still `--`
- [ ] `unclassified` counter shown **in the live frame**, in yellow
- [ ] `reducer.answer == final_output` printed **True** (if False, `_delta_text` drops something)

## OAI-16 — the number (§3.7–3.8)

- [ ] `first_token.py` run with `REPEATS = 2`, blocking and streamed **interleaved**
- [ ] Blocking `Runner.run` — total: **___ ms**
- [ ] Streamed — **time to first token: ___ ms**
- [ ] Streamed — **total time: ___ ms**
- [ ] Streamed — time to first *progress event*: **___ ms**
- [ ] Confirmed `total` barely moved (streamed may be slightly **worse**) — not an optimisation
- [ ] **TODO(me) rep 3:** decided what "first progress" means for a **blocking** run, and wrote two
      sentences of justification here: **___**

## AG-28 🅿️ — streaming UX and the three tensions (§4)

- [ ] Can state the difference between latency and **perceived latency** in one sentence
- [ ] Can say why a spinner is **worse than a partial answer and better than nothing**, and why named
      steps are the sweet spot **for an agent** specifically (not a chatbot)
- [ ] **Tension 1 (Day 11):** can explain why a partial validated object cannot be rendered, and name
      the three real responses + what each costs
- [ ] **Tension 2 (Day 12):** can say why a tripped output guardrail becomes a **retraction**, and name
      all five mitigations with the trade of each
- [ ] **Tension 3 (Principle 5):** streaming saves no tokens and no requests; usage arrives on the
      **final** chunk; a 429 arrives mid-render and **you cannot un-emit tokens** (Day 6's router)
- [ ] Can state Mandala's rule: **drafts stream to the operator; nothing streams to a customer**
- [ ] Four sentences written into notes — one per tension, one for the rule — for Day 45

## Tests that must be able to fail

`tests/test_streaming.py`

- [ ] `test_an_unknown_event_kind_does_not_crash_and_is_not_dropped` — the **decided** behaviour
- [ ] `test_a_foreign_object_with_no_type_still_classifies`
- [ ] `test_every_progress_family_is_reachable_from_classify` — **flip it:** delete the
      `agent_updated_stream_event` branch and confirm it goes RED
- [ ] `test_progress_events_are_ours_not_the_sdks`
- [ ] `test_the_answer_buffer_is_bounded`
- [ ] `test_ttft_is_none_before_any_token_not_zero`
- [ ] `test_tool_calls_come_from_run_items_never_from_token_text`
- [ ] `test_an_agent_switch_is_recorded_in_order`
- [ ] `test_the_default_answer_cap_is_not_absurd`
- [ ] `test_the_reducer_rebuilds_exactly_what_the_sdk_produced` — cassette-backed equivalence
- [ ] `test_streaming_does_not_change_the_answer` — cassette-backed equivalence; `normalise()` **not widened**

`tests/test_stream_guardrails.py` — **0 model requests, all of it**

- [ ] `test_the_customer_channel_is_never_a_live_stream_sink`
- [ ] `test_an_unknown_channel_is_not_streamable`
- [ ] `test_customer_text_cannot_be_released_before_guardrails_ran`
- [ ] `test_a_tripped_output_guardrail_is_a_block_not_a_retraction` — **flip it:** return the text on
      a trip and watch it go red
- [ ] `test_the_operator_surface_may_see_a_draft_live`
- [ ] `test_a_clean_customer_release_still_works` — the pair, so `deliver()` cannot always raise
- [ ] Everything but the two `@pytest.mark.vcr` tests costs **0 model requests**

## Understanding check — answer out loud

- [ ] Why is `Runner.run_streamed` not awaited, and what breaks if you await it?
- [ ] Which event family drives the display, which drives the program, and what if you swap them?
- [ ] Why does the SDK's event vocabulary appear in exactly one function in this project?
- [ ] Unknown event kind: drop, raise, or count — which did you choose and why do the other two lose?
- [ ] Why can you not stream `output_type=Brief`, and what do you stream instead?
- [ ] Why is a tripped output guardrail on a streamed run a retraction rather than a block?
- [ ] Why can Day 6's router not transparently fall back mid-stream?

## Budget & freshness

- [ ] Model requests logged in `docs/RATE_BUDGET.md` (declared: **≈ 45, Groq**; actual: **___**)
- [ ] Tuned `frame()` against a **hand-populated** `ProgressReducer`, not against real runs
- [ ] ⚠️ **Verified whether streaming through `LitellmModel` on Groq matches OpenAI's Responses API** —
      printed the first ten raw events rather than trusting the docs. Result: **___**
- [ ] Exact event class names, `run_item` sub-type strings, and the `include_usage=True` (Day 9)
      usage event confirmed in 0.22.0
- [ ] `rich` 15.0.0 `Live` API confirmed (`refresh_per_second`, `live.update`, `Group` import path)
- [ ] Drift logged in `docs/CHANGELOG_PLAN.md`; a changed **mechanism** gets an addendum (Principle 14)

## Commit

```bash
./m check
./m done 17
```

- [ ] `./m done 17` succeeded — trackers updated automatically
- [ ] Day 18 previewed: programmatic tool calling 🅿️ and the free coordinator tool
