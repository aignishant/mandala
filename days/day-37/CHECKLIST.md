# Day 37 — CHECKLIST

**IDs covered:** LC-03 🛠️ (messages & standard content blocks), LC-04 🛠️ (`@tool` & runtime
injection)

## Demo command

```bash
uv run python days/day-37/lab/injection_demo.py    # 0 requests
uv run python days/day-37/lab/block_survey.py      # 3 requests
uv run pytest tests/test_lc_tools.py -v
```

Expected: two schemas printed where `request_id` appears in the **runtime** view and never in the
**model** view, then a per-provider report of block types, `finish_reason` and `usage_metadata`.

## Setup

- [ ] `./m start 37` and `./m scaffold 37` run
- [ ] No new packages
- [ ] Files created (`lc/tools.py`, `tests/test_lc_tools.py`, two lab files)

## LC-03 — messages and blocks

- [ ] Can name the four message types and who authors each
- [ ] Noticed `HumanMessage` is usually **untrusted** text in Mandala, and the name misleads
- [ ] Knows `tool_call_id` links a `ToolMessage` to its `AIMessage`
- [ ] Can say why a `str` cannot represent a reply that contains reasoning and citations
- [ ] Knows tool calls live on `message.tool_calls`, **not** in `content`
- [ ] `block_survey.py` run once (3 requests)
- [ ] Both branches exercised — handled `content` as `str` **and** as a list

## What to write down (§3.4)

- [ ] Q1 — which providers returned a list, which a string
- [ ] Q2 — any `reasoning` block? any `citation` block?
- [ ] Q3 — is `usage_metadata` the same shape across all three?
- [ ] Q4 — if no citation blocks on free models, **Day 29's regex guardrail stays** — recorded as a
      finding, with the distinction between "abstraction is real" and "my models don't exercise it"
- [ ] `finish_reason` connected back to Day 1's empty-reply mystery

## LC-04 — schema-first tools

- [ ] `lc/tools.py` written, wrapping the **same** functions from Days 10 and 27
- [ ] Tool names explicit, not inferred from the Python function name
- [ ] `args_schema=` used — and can say what inference would have cost
- [ ] `pattern=r"^T-\d{4}$"` on `ticket_id` — prose became a wall
- [ ] Every field has a `description` — and knows that text goes into the prompt
- [ ] `k` bounded with `ge`/`le` — an unbounded numeric arg is an AG-04 vulnerability
- [ ] Every tool documented **and intended** as read-only (Principle 6)
- [ ] `READ_TOOLS` exported as one importable list

## Runtime injection

- [ ] `request_id: Annotated[str, InjectedToolArg]` in the signature
- [ ] `request_id` **absent** from the args schema — verified by `injection_demo.py`
- [ ] Can fill in the four-row table: prompt / closure / shared state / injection
- [ ] Can say why injection is a *security boundary* and the other three are not
- [ ] Recorded in the bake-off that LangChain beats Day 31's approach here

## Tests that must be able to fail

- [ ] `test_the_model_cannot_see_the_request_id` — **flip it:** drop `InjectedToolArg`, see red
- [ ] `test_the_runtime_still_receives_the_request_id` — the negative-space sibling
- [ ] `test_a_hallucinated_ticket_id_is_refused`
- [ ] `test_a_prose_ticket_id_is_refused`
- [ ] `test_k_is_bounded`
- [ ] `test_every_tool_field_has_a_description`
- [ ] `test_tool_names_are_explicit_not_inferred`
- [ ] `test_the_read_set_is_read_only` — **and its weakness stated out loud**
- [ ] `test_no_tool_takes_a_free_text_identifier`
- [ ] Whole file runs **offline, with no keys** — the property Day 74 needs

## Understanding check — answer out loud

- [ ] What can a block list express that a string cannot, and when did that first cost you?
- [ ] Why is `finish_reason` worth printing next to every `content`?
- [ ] What exactly does `args_schema` buy over an inferred schema — three things?
- [ ] Why is a `pattern` better than "never invent a ticket id" in a prompt?
- [ ] Why can the model not forge the `request_id`?
- [ ] What does `"Read-only"` in a docstring actually guarantee?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: 3)
- [ ] `InjectedToolArg` import path confirmed for `langchain-core==1.6.0`
- [ ] **`args_schema` + injected-arg-not-in-schema combination confirmed to work** — §4.1 rests on it
- [ ] Blocks confirmed as dicts or typed objects — Day 40 will care
- [ ] `usage_metadata` population checked per adapter; gaps noted in `RATE_BUDGET.md`
- [ ] Whether `reasoning` is a **standard** block type — checked in docs, not inferred
- [ ] `@tool` vs. `@tool(...)` form confirmed
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 37
```

- [ ] Bake-off rows updated: **tool declaration ergonomics** (SDK Day 10 / CrewAI Day 25 / today) and
      **hidden-argument support**
- [ ] `./m done 37` succeeded — trackers updated automatically
