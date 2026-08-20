# Day 28 — CHECKLIST

**IDs covered:** CR-11 🛠️ (testing & training crews), CR-12 🛠️ (crew observability)

## Demo command

```bash
uv run crewai test -n 3 -m openrouter/<free-model>     # judge != judged
uv run python days/day-28/lab/score_report.py --rounds 2
uv run python days/day-28/lab/traced_crew.py T-1004
uv run python days/day-14/lab/span_tree.py             # the Day-14 viewer, unchanged
```

## Setup

- [ ] `./m start 28` and `./m scaffold 28` run
- [ ] No new packages — OTel stays on Day 75
- [ ] **Decided the CLI-layout question today, not on gate day** — option A adapter written
- [ ] `src/mandala/crew/crew_entry.py` `@CrewBase` wrapper builds the **existing** crew objects
- [ ] Confirmed how `crewai test` discovers a crew in 1.15.17
- [ ] Files created (`crew/observability.py`, two lab files, one test file)

## CR-11 — `crewai test`

- [ ] Can state plainly what the command measures: **an LLM scores each task out of ten**
- [ ] `-m` confirmed to select the **scoring** model, and it accepts a LiteLLM provider string
- [ ] Scorer runs on **OpenRouter**, never the crew's provider (RATE_BUDGET rule 1)
- [ ] If `-m` does not work as needed → **logged an amendment** rather than scoring wrongly
- [ ] Can recite the thermometer-vs-tripwire table
- [ ] Ran it **3 times unchanged** and looked at the spread first
- [ ] Scores observed: **___ / ___ / ___** · mean **___** · stdev **___**
- [ ] **Threshold set BEFORE the gate and written here: ___** (with a little room, not much)
- [ ] Threshold sits **below the noise floor** — can show the arithmetic

## CR-11 — `crewai train`

- [ ] Can name all four rows where a trained-agents pickle violates Day 6's prompt rules
- [ ] Understands the serious one: **implicit load = a behaviour change that skipped review**
- [ ] Mandala's position understood: train to **discover**, hand-write the improvement into
      `mandala.prompts`, do not ship the pickle
- [ ] If disagreeing with that position → **wrote the disagreement into the bake-off list**
- [ ] Pickle either gitignored or committed deliberately — **never ambiguous**

## CR-12 — observability

- [ ] Can recite the verbose-vs-callbacks-vs-Day-14 table, especially the **redactable** row
- [ ] `step_callback` / `task_callback` signatures confirmed for 1.15.17
- [ ] Confirmed what object each callback receives; replaced defensive `getattr` with real access
- [ ] Emits **Day 14's JSONL format** — no new format invented
- [ ] `JsonlTraceProcessor` and the shrink helper **reused**, not reimplemented
- [ ] TODO(me): promoted `_shrink` to a public name now that it has two callers
- [ ] `SAFE_STEP_FIELDS` / `SAFE_TASK_FIELDS` allowlists — the fourth time this reflex applies
- [ ] **Thought recorded as `thought_present` boolean**, never as text
- [ ] Task output recorded as `output_len`, never as content
- [ ] `verbose=False` turned off for good
- [ ] Guardrails from Day 27 **still on** while adding observability

## The Principle-8 payoff (§4.3)

- [ ] `traced_crew.py` run, then `span_tree.py` on the result
- [ ] It rendered **without crashing** — the format matched
- [ ] Ran T-9002 and grepped: `grep -ril "PINEAPPLE" .mandala/traces/` finds **nothing**
- [ ] `model_calls` reported: **___** — if **0**, fixed the counter to recognise both frameworks
- [ ] Noted this is the **third time** the Day-14 span-type open item has mattered
- [ ] TODO(me): investigated reconstructing `parent_id` nesting from task boundaries

## Tests that must be able to fail

- [ ] `test_a_thought_is_recorded_as_a_boolean_not_as_text` — **flip it:** record `thought` itself
- [ ] `test_task_output_is_recorded_as_a_length_not_as_content`
- [ ] `test_unknown_fields_never_reach_disk` — the allowlist vs. a field nobody anticipated
- [ ] `test_every_record_is_one_json_line`
- [ ] `test_the_trace_opens_with_a_trace_start_record`
- [ ] `test_day_14s_reader_can_load_a_crew_trace` — **the Principle-8 test**
- [ ] `test_a_broken_callback_does_not_kill_the_run`
- [ ] `test_the_score_threshold_is_recorded_and_below_the_noise_floor` — ships **skipped**
- [ ] Fakes are **hostile** (they contain the canary) — a clean fake proves nothing
- [ ] Every test costs **0 model requests**

## Understanding check — answer out loud

- [ ] What is the difference between a thermometer and a tripwire, and which does Principle 7 want?
- [ ] Why must the scorer run on a different provider than the crew?
- [ ] Why is a threshold chosen after seeing the score worthless?
- [ ] What exactly is wrong with a file that silently improves your prompts?
- [ ] Why record that a thought happened rather than what it said?
- [ ] What would it have cost me later to invent a nicer trace format today?

## Budget & freshness — READ THIS BEFORE RUNNING

- [ ] Actual counts logged in `docs/RATE_BUDGET.md` (declared: ~240 Groq, ~36 OpenRouter)
- [ ] ⚠️ **OpenRouter free tier is ~50 requests/day** — `--rounds 2` used, or variance checked once
- [ ] **Did NOT spend tomorrow's judge budget** — the gate needs scorer calls
- [ ] `crewai train` skipped or run at `-n 3` maximum
- [ ] `finish_reason` located; understood `"length"` masquerades as a model-quality problem
- [ ] Whether an exception inside a callback propagates: confirmed
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 28
```

- [ ] Bake-off list updated: framework eval harness gained; a non-deterministic score is not an eval
- [ ] OpenRouter quota checked and **left with room for tomorrow's gate**
- [ ] `./m done 28` succeeded — trackers updated automatically
