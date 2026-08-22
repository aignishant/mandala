# Day 13 — CHECKLIST

**IDs covered:** OAI-09 🛠️ (handoffs), OAI-10 🛠️ (agents-as-tools vs. handoffs)

## Demo command

```bash
cd days/day-13/lab
uv run python handoff_demo.py T-1003     # finishes with: Billing
uv run python as_tool_demo.py T-1004     # finishes with: Triage
uv run python leak_check.py              # unfiltered=True, filtered=False
cd ../../..
```

Run the first two **back to back** — the differing `finished with:` line is the whole lesson.

## Setup

- [ ] `./m start 13` and `./m scaffold 13` run
- [ ] No new packages
- [ ] Files created (`src/mandala/handoffs.py`, three lab files, `tests/test_handoffs.py`)
- [ ] `dummy_agent` fixture added to `tests/conftest.py`
- [ ] **`T-9002` added to fixtures** with the canary `PINEAPPLE-7731` in its body, marked as a leak test case

## OAI-09 — handoffs

- [ ] Can state that a handoff is **a tool call in disguise**
- [ ] `HandoffReason` uses a `Literal` reason (countable on Day 71) and a length-capped summary
- [ ] Summary description explicitly forbids quoting the ticket body
- [ ] `on_handoff` audit hook wired; signature verified for the `input_type` case
- [ ] `make_handoff()` is keyword-only after the agent
- [ ] **`filtered=True` is the default** — the safe value
- [ ] `input_filter=handoff_filters.remove_all_tools` applied
- [ ] `assert_filtered()` written — the rule is enforced, not just intended
- [ ] `RECOMMENDED_PROMPT_PREFIX` used on every participating agent
- [ ] **Printed and read `RECOMMENDED_PROMPT_PREFIX`**
- [ ] Every handoff description contains a **"Do NOT transfer here for…"** clause
- [ ] Triage told explicitly not to answer the customer itself
- [ ] `max_turns` raised to account for the chain
- [ ] `result.last_agent.name` observed as the **receiver**

## The leak experiment (§3.5) — do not skip

- [ ] `leak_check.py` run with **both** `filtered=False` and `filtered=True`
- [ ] Unfiltered: canary **visible** to the receiver
- [ ] Filtered: canary **not visible**
- [ ] Receiver prompt was strong enough to enumerate hard (a weak probe proves nothing)
- [ ] Understood that raw ticket bodies arrive as **tool output**, which is what `remove_all_tools` strips

## OAI-10 — agents as tools

- [ ] `researcher.as_tool(...)` with a description saying **when** to use it
- [ ] Sub-agent has `output_type=Brief` — a typed return, not prose
- [ ] Parent instructed that it may call the tool more than once
- [ ] `result.last_agent.name` observed as the **parent**
- [ ] Sub-agent run appears as a tool call/output in the parent's `new_items`
- [ ] Can recite the full comparison table, especially the **context isolation** row
- [ ] Can say the decision flowchart out loud

## Tests that must be able to fail

- [ ] `test_handoff_reason_rejects_free_text`
- [ ] `test_handoff_summary_is_length_capped`
- [ ] `test_filtered_is_the_default` — flip the default and confirm **red**
- [ ] `test_unfiltered_handoff_into_a_writer_is_rejected`
- [ ] `test_filtered_handoff_into_a_writer_is_accepted`
- [ ] `test_every_handoff_description_says_when_not_to_use_it` — a prose lint
- [ ] `test_handoff_transfers_control`
- [ ] `test_as_tool_keeps_control` — the **pair**; either alone would pass a broken implementation
- [ ] `test_filtered_handoff_does_not_leak_the_canary` — the security test
- [ ] Configuration tests cost **0 model requests**
- [ ] Cassettes recorded; suite replays offline

## Understanding check — answer out loud

- [ ] The one question that decides handoff vs. agent-as-tool?
- [ ] Why is a handoff into a write-capable agent dangerous **by default**?
- [ ] Why does `remove_all_tools` specifically fix it? (what shape does the ticket body arrive in?)
- [ ] Why is agent-as-tool isolated "by construction"?
- [ ] What do you *lose* by choosing agent-as-tool over a handoff?
- [ ] Which row of the comparison table does `last_agent` let you observe directly?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~46, Groq)
- [ ] Confirmed `remove_all_tools` strips tool **outputs**, not just tool calls
- [ ] Read what `nest_handoff_history` does and how it interacts with `input_filter`
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 13
```

- [ ] `./m done 13` succeeded — trackers updated automatically
