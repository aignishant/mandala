# Day 23 — CHECKLIST

**IDs covered:** CR-01 🛠️ (install, scaffold, YAML vs. code), CR-02 🛠️ (role, goal, backstory)

## Demo command

```bash
uv run python days/day-23/lab/scaffold_tour.py            # 0 model calls
uv run python days/day-23/lab/scaffold_tour.py --write    # generate agents.yaml
uv run python days/day-23/lab/first_crew.py T-1004
```

## Setup

- [ ] `./m start 23` and `./m scaffold 23` run
- [ ] `uv add "crewai==1.15.17" "crewai-tools==1.15.17"` — **exact patch pinned**
- [ ] Pinned what actually resolved; PINS ledger row for Day 23 checked
- [ ] `CREWAI_TELEMETRY_OPT_OUT=true` in `.env`, **variable name verified for 1.15.17**
- [ ] Files created (`crew/llms.py`, `crew/roles.py`, `crew/config/`, two lab files, one test file)
- [ ] Toured `crewai create crew` output **in a temp dir**, not at the repo root

## CR-01 — the scaffold and the YAML question

- [ ] Can name the four things in the generated tree and what each is for
- [ ] Spotted the `.env` expecting `OPENAI_API_KEY` — the first paid assumption
- [ ] Can argue **YAML vs. Python** from the comparison table, both directions
- [ ] Understood Mandala's decision: **YAML holds text, Python owns wiring, both generated from
      `mandala.prompts`**
- [ ] `agents.yaml` carries the **GENERATED FILE** header and the regeneration command
- [ ] YAML uses folded blocks so the diff is readable — the whole reason to want YAML

## `llms.py` — the file that keeps this project free

- [ ] **No model id written in the module** — ids come from `mandala.models.PROVIDERS`
- [ ] `api_key=` passed explicitly, never left to ambient discovery
- [ ] `temperature=0.0` and `max_tokens` pinned (Principle 4)
- [ ] Named by **role** (`worker`/`manager`/`judge`), not by provider
- [ ] `judge_llm()` exists now, though nothing judges until Phase 11 — can say why

## CR-02 — the triad

- [ ] `triad()` written (the TODO(me))
- [ ] **Decided where `prompt.version` goes, and wrote the justification in a comment**
- [ ] Can recite the mapping table and name **the two losses** (refusal identity, version)
- [ ] `role` is a job title, not a personality
- [ ] Refusals kept structurally separate **upstream**, in the `Prompt` object
- [ ] Can give the three reasons the triad works, **in descending order of importance**
- [ ] Noticed the failure mode: over-investing in register, under-investing in identity/objective

## The first crew

- [ ] **`llm=` on every `Agent`** — no exceptions
- [ ] `tools=[]` stated explicitly, not omitted
- [ ] `allow_delegation=False` stated explicitly
- [ ] `max_iter` set — and **verified it counts what `max_turns` counted**
- [ ] `memory=False` and telemetry off, both stated
- [ ] `verbose=False` while working with ticket text
- [ ] Noticed the ticket body is interpolated into the prompt with **no untrusted envelope**
- [ ] `token_usage` read and recorded: **___** tokens for one agent, one task

## Tests that must be able to fail

- [ ] `test_every_llm_is_a_free_provider` — **flip it:** point one at a paid model
- [ ] `test_every_llm_pins_temperature`
- [ ] `test_no_agent_is_constructed_without_an_llm` — the source lint
- [ ] Understood the lint's weakness (400-char window) and accepted or replaced it
- [ ] `test_the_judge_is_not_the_worker`
- [ ] `test_every_refusal_survives_the_translation`
- [ ] `test_role_is_a_job_title_not_a_personality`
- [ ] `test_the_generated_yaml_matches_the_prompt_objects`
- [ ] `test_telemetry_is_opted_out` — ships **failing**; assert from the runtime, not from `.env`
- [ ] Every test costs **0 model requests**

## The trap, reproduced deliberately

- [ ] Constructed an `Agent` with no `llm=`, offline, once
- [ ] **Read the error CrewAI actually produces** — so it is recognisable in six weeks
- [ ] Confirmed whether 1.15.17 defaults or raises; if it raises, logged a plan amendment

## Understanding check — answer out loud

- [ ] What is CrewAI's answer to "who owns the loop", and how does it differ from the SDK's?
- [ ] What does the triad give you for free, and what does it take away?
- [ ] Why is `expected_output` not in the agent?
- [ ] Why generate the YAML instead of writing it?
- [ ] Why is `memory=True` a zero-budget hazard?
- [ ] Which Phase-1 things did the framework hand me today — first entries for the Day-59 bake-off list

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~29, Groq)
- [ ] `crewai.LLM` signature verified against live docs
- [ ] `max_iter` / `allow_delegation` / `telemetry` / `memory` kwargs verified for 1.15.17
- [ ] `RAW_TICKETS` import checked against what Day 10 actually exported
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 23
```

- [ ] Started the **Day-59 bake-off list**: what CrewAI gave me, what it took
- [ ] `./m done 23` succeeded — trackers updated automatically
