# Day 34 — CHECKLIST

**IDs covered:** CR-20 🅿️+lab-lite (declarative `FlowDefinition` DSL), CR-21 🅿️ (enterprise map)

## Demo command

```bash
uv run python days/day-34/lab/load_dsl.py       # 0 requests — loading is not running
uv run pytest tests/test_dsl_port.py -v
cat days/day-34/lab/compare.md                  # today's actual deliverable
```

## Setup

- [ ] `./m start 34` and `./m scaffold 34` run
- [ ] No new `src/mandala/` file — the experiment lives in `days/`, and can say why
- [ ] `pyyaml` availability checked; **if added**, ledger row + changelog line written
- [ ] Files created (`triage_flow.yaml`, `load_dsl.py`, `compare.md`, `tests/test_dsl_port.py`)

## CR-20 — the port

- [ ] Only the **router + three lanes** ported — not the whole flow
- [ ] Can map all four DSL concepts onto the Python you already wrote
- [ ] Can explain why CEL being **not Turing-complete** is a feature
- [ ] `yaml.safe_load` used — never `yaml.load`
- [ ] Noticed "triage is None" could not be expressed and became `== ""` — a *semantic* change
- [ ] `FAST_LANE_CATEGORIES` inlining noted as a loss (or a variables facility found and used)
- [ ] `budget:` attached to steps, and the co-location win recorded
- [ ] Noticed `crew: mandala_mini` hides both guards from `organs.py`

## The load-time experiment (§3.3)

- [ ] `goto: fastt` typo introduced **on purpose**
- [ ] Recorded whether the failure is at **load** time or **run** time
- [ ] Compared against Day 31's behaviour (silent no-match at runtime)
- [ ] Result written at the top of `compare.md` — not taken on faith

## `compare.md` — the deliverable

- [ ] Every `?` cell filled by an actual experiment
- [ ] "Who can safely author it" row answered — the row that matters most
- [ ] "Debuggability at 2am" row answered honestly
- [ ] Two paragraphs: what I would actually use, and when
- [ ] One paragraph: the thing that surprised me
- [ ] §4 read **only after** the port was done
- [ ] Own findings compared against §4's four losses — agreements *and* disagreements noted
- [ ] Weakness of the fidelity test (it does not execute the YAML) stated in `compare.md`

## CR-21 — the enterprise map

- [ ] **AMP** connected to what it replaces (Day 85 FastAPI, Day 86 self-hosted server)
- [ ] **Crew Studio** connected to CR-20 — a visual builder needs a data format
- [ ] **Agent Control Plane** connected to `RATE_BUDGET.md` rules and `ROUTE_BUDGET`
- [ ] Can say the one-sentence version out loud, tied to things you built
- [ ] Built **nothing** — and can say why that is a Principle-5 decision, not a shrug

## Tests that must be able to fail

- [ ] `test_the_port_declares_every_python_route`
- [ ] `test_the_budgets_match_the_python_ones` — the one that will actually catch drift
- [ ] `test_the_router_has_a_default_branch` — written *before* knowing if the DSL enforces it
- [ ] `test_exactly_one_step_is_the_start`
- [ ] `test_the_python_router_still_agrees_with_the_yaml_conditions[3 rows]`
- [ ] `test_the_yaml_is_loaded_safely` — repo-wide grep, `.venv` excluded
- [ ] All tests cost **0 model requests**

## Understanding check — answer out loud

- [ ] When should orchestration be code, and when should it be data?
- [ ] What exactly did the type system lose in the port, and why does that matter for Mandala?
- [ ] Why is "a flow that is data cannot import os" the strongest argument for a DSL?
- [ ] Why do CR-20 and CR-21 share a day?
- [ ] What can a declarative file describe, and what can it never describe?
- [ ] Which of your findings is about design, and which is just familiarity with Python?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: **0**)
- [ ] `FlowDefinition` existence and import path confirmed for 1.15.17
- [ ] On-disk format confirmed (YAML / JSON / constructed object)
- [ ] Real key names confirmed, and §3.2 corrected to match
- [ ] **Load-time validation claim verified by experiment**, not by docs alone
- [ ] Typed-state support in the DSL — answered
- [ ] Constants/variables facility — answered
- [ ] `each.do` shape noted for Day 44's `Send` comparison
- [ ] All drift logged in `docs/CHANGELOG_PLAN.md` (expect some — Part 2 warns about this surface)

## Commit

```bash
./m check
./m done 34
```

- [ ] Bake-off row added: **authoring model** — Python only vs. Python + data
- [ ] `./m done 34` succeeded — trackers updated automatically
