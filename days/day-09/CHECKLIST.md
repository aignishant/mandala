# Day 9 — CHECKLIST

**IDs covered:** OAI-01 🛠️ (install, project shape, first `Agent`), OAI-02 🅿️ (the Responses API underneath)

## Demo command

```bash
cd days/day-09/lab
uv run python first_agent.py "What severity is ticket T-1001?"
uv run python wire_shapes.py
cd ../../..
```

Expected: the same answer Day 3 gave, from ~10 lines, on Groq, with no OpenAI key — and
`wire_shapes.py` shows a **Chat Completions**-shaped request on the wire.

## Setup

- [ ] `./m start 9` and `./m scaffold 9` run
- [ ] `uv add "openai-agents[litellm]==0.22.0"` — version re-verified against PyPI first
- [ ] `uv add --dev "pytest-asyncio==1.4.0"` (needed for the async tests)
- [ ] `asyncio_mode = "auto"` added under `[tool.pytest.ini_options]` (or `@pytest.mark.asyncio` used everywhere)
- [ ] Files created (`src/mandala/sdk.py`, `lab/first_agent.py`, `lab/wire_shapes.py`, `tests/test_sdk_agent.py`)
- [ ] Noted that the import is **`agents`**, not `openai_agents`

## OAI-01 — the three $0 requirements

- [ ] `set_tracing_disabled(True)` at module level in `src/mandala/sdk.py`
- [ ] Model is an **explicitly constructed `LitellmModel`** with an explicitly passed key
- [ ] `ModelSettings(include_usage=True)` — usage reporting requested
- [ ] `temperature=0.0` pinned (Principle 4)
- [ ] `_LITELLM_PREFIX` maps your provider names to LiteLLM's (note `ollama` → `ollama_chat`)
- [ ] `make_model()` raises `ValueError` on an unknown provider
- [ ] **No model id string appears in `sdk.py`** — it comes from `mandala.models`

## OAI-01 — the first agent

- [ ] `@function_tool` used on both tools
- [ ] Type hints present on every parameter
- [ ] Docstrings written **for the model**, with an `Args:` section
- [ ] Tool bodies reuse Day 3's `RAW_TOOLS` — the logic did not change
- [ ] `instructions=TRIAGE.render()` — Day 6's prompt object, unchanged
- [ ] `max_turns=6` passed explicitly
- [ ] Printed and inspected `result.new_items`
- [ ] Ran it and got the same answer as Day 3

## The comparison table — actually fill it in

- [ ] Opened `naked_agent.py` and `first_agent.py` side by side
- [ ] Filled all nine rows of the §3.4 table
- [ ] **Identified the ❌ row**: provider fallback is lost — the SDK owns the loop
- [ ] Noted it for ADR-001 (Day 16)

## OAI-02 🅿️ — Responses vs Chat Completions

- [ ] Can state the four structural differences from the table
- [ ] Can explain **why** OpenAI built a second API (server-side state enables server-side tools)
- [ ] Can state the free/paid boundary in one sentence, with the reason, not just the list
- [ ] Ran `wire_shapes.py` and **saw** a `messages` + `tools` array on the wire
- [ ] Found your own tool docstring text inside the generated JSON schema
- [ ] Found where usage actually lives on the result object in 0.22.0, and wrote it down

## Tests that must be able to fail

- [ ] `test_tracing_is_disabled_on_import` — **you solved the `TODO(me)`**, reading the SDK source if needed
- [ ] `test_model_string_is_a_pinned_litellm_provider_string`
- [ ] `test_unknown_provider_fails_loudly`
- [ ] `test_usage_reporting_is_requested`
- [ ] `test_temperature_is_pinned`
- [ ] `test_sdk_agent_matches_the_naked_agent_on_T_1001` — the **equivalence** test
- [ ] `test_sdk_agent_actually_calls_the_tool` — a **trajectory** assertion
- [ ] `test_max_turns_is_enforced` — `MaxTurnsExceeded` import path verified in 0.22.0
- [ ] Cassettes recorded; suite replays offline

## Understanding check — answer out loud

- [ ] Name the six SDK primitives and which day you built each by hand
- [ ] What three things must be true for the SDK to run on $0, and what breaks without each?
- [ ] Where does a tool's parameter description come from now?
- [ ] What did you *lose* by adopting the framework?
- [ ] Why is the free/paid boundary structural rather than arbitrary?
- [ ] What is `result.new_items`, and what was its Day-3 equivalent?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~33, Groq)
- [ ] Verified the `LitellmModel` import path and constructor against the live docs
- [ ] Noted the docs' own warning that the LiteLLM adapter is **best-effort/beta** — validate structured output and tool calling on Day 11
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 9
```

- [ ] `./m done 9` succeeded — trackers updated automatically
