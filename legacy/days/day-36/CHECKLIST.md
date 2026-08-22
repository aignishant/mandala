# Day 36 — CHECKLIST

**IDs covered:** LC-01 🛠️ (1.x mental model & package layout), LC-02 🛠️ (chat models & the provider
abstraction)

## Demo command

```bash
uv run python days/day-36/lab/what_survived.py     # 0 requests
uv run python days/day-36/lab/provider_swap.py     # 3 requests
uv run pytest tests/test_lc_chat.py -v
```

Expected: a survey showing `create_agent` present and `LLMChain` gone, then three providers
answering through one interface with their latencies side by side.

## The amendment — do this FIRST (§1.1)

- [ ] `docs/03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md` Part 3 read
- [ ] The 1.2 → 1.3 **release notes** read, and anything surprising logged
- [ ] Sign-off box ticked — **your** decision, not the generator's
- [ ] Acceptance logged in `docs/CHANGELOG_PLAN.md`; plan bumped to **v1.1.1**
- [ ] Installed **after** signing, not before

## Setup

- [ ] `./m start 36` and `./m scaffold 36` run
- [ ] §2.1 PyPI loop run for all five packages, compared with `docs/PINS.md`
- [ ] `uv add` used the versions **verified today**, not the addendum's
- [ ] Any drift pinned and logged; a minor bump would have stopped the day
- [ ] `langchain-community` **not** installed — and can say why
- [ ] `src/mandala/lc/` created as a package, mirroring `crew/` and `flows/`
- [ ] Files created (`lc/chat.py`, `tests/test_lc_chat.py`, two lab files)

## LC-01 — the layout

- [ ] Can name what lives in `langchain-core` vs. `langchain` vs. the adapters
- [ ] Can say why the split exists (provider quirks stay in the provider's package)
- [ ] `what_survived.py` run, and its output **saved to notes**
- [ ] Knows the difference between "gone" and "there but deprecated" for `AgentExecutor`
- [ ] `LLMChain` confirmed absent
- [ ] `langgraph.prebuilt` line noted for re-running on Day 45 (LG-15)
- [ ] Understands the convergence: LangGraph's prebuilt agent now points at `create_agent`
- [ ] Alert to the fact that most LangChain material online predates 1.0

## LC-02 — the provider abstraction

- [ ] `chat.py` written — `workhorse()`, `fast_loop()`, `judge()`
- [ ] Model ids imported from `mandala.models` — **none written in the file**
- [ ] `temperature=0.0` default, and can defend it
- [ ] **`max_retries=0`** set, and can explain the two-retry-layer problem
- [ ] `judge()` reaches OpenRouter via the **openai adapter + `base_url`**
- [ ] Three named functions rather than one string-keyed getter — and can say why
- [ ] `provider_swap.py` run once (3 requests)
- [ ] `time.monotonic()` used, not `time.time()` — and can say why

## What to write down (§4.3)

- [ ] Q1 — same reply class across all three providers? **answered from the run**
- [ ] Q2 — `response_metadata` key sets compared; the odd provider named
- [ ] Q3 — provider-specific branches counted; leakage-vs-configuration argued both ways
- [ ] Q4 — **what `router.py` still has to do that LangChain will not** — the important one
- [ ] Latency difference between Groq and Gemini observed, and `RATE_BUDGET.md` rule 4 re-read

## Tests that must be able to fail

- [ ] `test_every_role_maps_to_a_pinned_model`
- [ ] `test_no_model_id_is_written_in_this_file` — **flip it:** paste an id, see red
- [ ] `test_the_judge_is_not_the_workhorse` — a plan rule, made executable
- [ ] `test_framework_retries_are_disabled` — **flip it:** drop `max_retries=0`, see red
- [ ] `test_temperature_defaults_to_zero`
- [ ] `test_every_role_supplies_a_key[workhorse|fast_loop|judge]`
- [ ] `test_agent_executor_is_not_used_anywhere`
- [ ] Every test monkeypatches `init_chat_model` — **0 model requests, no keys needed**

## Understanding check — answer out loud

- [ ] What are the three layers, and what changes on whose schedule?
- [ ] What did 1.0 delete, and why does that matter more than usual for this framework?
- [ ] What does `init_chat_model` abstract, and what does it not touch at all?
- [ ] Why is `max_retries=0` a *budget* decision rather than a reliability one?
- [ ] Why is `langchain-openai` installed on a machine with no OpenAI key?
- [ ] After five weeks, what has role-based model naming actually saved you?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: 3)
- [ ] `init_chat_model` import path confirmed for 1.3.16
- [ ] Provider strings confirmed (`google_genai`, `groq`, `openai`)
- [ ] `base_url` acceptance on the openai provider confirmed — the OpenRouter path depends on it
- [ ] `max_retries` confirmed to exist **and be honoured** on all three adapters
- [ ] Whether any `response_metadata` keys are documented as standard — checked
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 36
```

- [ ] Bake-off row started: **provider abstraction** — hand-rolled (Day 1/6) vs. `init_chat_model`
- [ ] `./m done 36` succeeded — trackers updated automatically
