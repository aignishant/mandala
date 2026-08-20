# Day 5 — CHECKLIST

**IDs covered:** AG-05 🛠️ (ReAct and its limits), AG-06 🛠️ (planning vs. reacting)

## Demo command

```bash
cd days/day-05/lab
uv run python wander.py                         # watch it fail, three ways
uv run python plan_execute.py "Which open tickets share an underlying problem?"
cd ../../..
```

Expected: `wander.py` shows drift / looping / premature-stop with a readable trace;
`plan_execute.py` prints a plan, **pauses for your approval**, then executes it.

## Setup

- [ ] `./m start 5` and `./m scaffold 5` run
- [ ] No new packages (correct — today is technique, not tooling)
- [ ] Files created (`src/mandala/trace.py`, `lab/react_agent.py`, `lab/plan_execute.py`, `lab/wander.py`, `tests/test_react_limits.py`)

## AG-05 — ReAct

- [ ] `src/mandala/trace.py` — `Step`, `Trace`, `signature()`, `repeated_calls()`, `render()`
- [ ] `signature()` uses `json.dumps(args, sort_keys=True)`
- [ ] `Trace` stores `result_len`, **not** the whole result
- [ ] `_with_thought()` **deep-copies** the schema (Day-3 tests still pass)
- [ ] `thought` is `pop`-ed out of `args` before the tool is called
- [ ] Repeated calls are **fed back to the model as an observation**, not raised
- [ ] The system prompt also forbids repeats in words (prompt + code, both)
- [ ] `run()` returns `(answer, trace)`

## Watch it wander — actually run these

- [ ] **Drift** — provocation 1: two goals, one answered. Trace saved/noted.
- [ ] **Loop** — provocation 2: repeated searching for something that does not exist
- [ ] **Premature stop** — provocation 3: answered without reading a ticket
- [ ] Confirmed the loop detector **missed** the semantic loop in provocation 2 (different args)
- [ ] Understood why `max_turns` is the real backstop

## AG-06 — planning

- [ ] `Plan` / `PlanStep` are Pydantic models with `Literal` tool names
- [ ] `steps` capped by the **schema** (`max_length=6`), not by a counter
- [ ] Planner prompt explicitly forbids answering during planning
- [ ] Plan produced via tool-as-schema + `tool_choice` (Day-4 technique reused)
- [ ] Executor truncates each observation before synthesis (Day-4 lever reused)
- [ ] Synthesis prompt says "using ONLY the observations" **and** gives an honest way out
- [ ] `input()` approval gate present before execution
- [ ] Ran all three provocations through the planner and **wrote down what changed**

## Tests that must be able to fail

- [ ] `test_repeated_calls_detects_reordered_args` — remove `sort_keys=True` and confirm it goes **red**
- [ ] `test_different_args_are_not_repeats` (the negative case)
- [ ] `test_plan_rejects_unknown_tools`
- [ ] `test_plan_rejects_oversized_plans`
- [ ] `test_react_terminates_on_an_impossible_question`
- [ ] `test_react_reads_a_ticket_before_answering_about_it` — a **trajectory** assertion
- [ ] Cassettes recorded; suite replays offline

## ID coverage

- [ ] **AG-05** — ReAct built with explicit reasoning; all three failure modes observed first-hand
- [ ] **AG-06** — plan-then-execute built and compared against reacting on the same three questions

## Understanding check — answer out loud

- [ ] In one sentence: what is ReAct's ceiling, and why does a plan raise it?
- [ ] Why does `signature()` sort the JSON keys?
- [ ] Why feed a repeated call back as an observation instead of raising?
- [ ] Why will your loop detector miss the "mobile / app / crash" loop?
- [ ] Why is planning a **prerequisite for human approval**, not just an accuracy trick?
- [ ] Which four later days re-implement that `input()` line, and in which frameworks?

## Budget

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~65, Groq)

## Commit

```bash
./m check
./m done 5
```

- [ ] `./m done 5` succeeded — trackers updated automatically
