---
day: 34
phase: 5
phase_name: "CrewAI Flows"
title: "The declarative FlowDefinition DSL + the enterprise map"
ids: ["CR-20", "CR-21"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 34 — The declarative DSL, and the map of everything you are not building

**Phase 5 · CrewAI Flows** · IDs: **CR-20 🅿️+lab-lite**, **CR-21 🅿️**

> **Yesterday:** the flow pauses for a human, durably, and the reviewer is a separate process.
> **Today:** the same flow written as **data instead of Python**, so you can feel exactly what a
> declarative DSL buys and what it takes away. Then the enterprise layer — the vocabulary, without
> building any of it.
> **Tomorrow:** the Phase-5 gate. Everything from Days 30–34, running, killed, and resumed.

```bash
./m start 34
./m scaffold 34
```

---

## §1 The story

Today is a **lab-lite** day and the plan says so: CR-20 is marked 🅿️+lab-lite, CR-21 is 🅿️. That is
not a rest day — it is a day where the deliverable is a *judgement* rather than a feature, and the
judgement has to be earned by porting real code.

The question is one you will be asked in interviews for the rest of your career:

> **When should orchestration be code, and when should it be data?**

CrewAI 1.15 gives you both for the same flow. `FlowDefinition` lets you declare steps, conditions and
actions as a structure — validated at load time, with CEL expressions for conditions, `each.do` for
iteration, composite actions, and single-agent actions. You have spent four days writing the Python
version. Today you port one small piece and write down the diff honestly.

**The honest answer is not "code is better".** Declarative orchestration wins real things:

- **Validation before execution.** A typo in a route label (Day 31's whole `routes.py` argument) is a
  load-time error, not a silent no-match at runtime.
- **Tooling.** Data can be diffed, linted, visualised, and generated. A UI can edit it. Python can be
  none of those things without an AST.
- **A blast-radius boundary.** A flow that is data cannot `import os`. For a flow authored by someone
  who is not you — a support lead, or a model — that is not a limitation, it is the point (Principle
  6).

And it loses real things too, which §4 makes you find out by hitting them rather than by reading
about them.

The second half of the day is CR-21: **AMP, Crew Studio, the Agent Control Plane.** The plan is blunt
about this — *"know the vocabulary; build nothing."* §5 explains why that is the correct instruction
and not laziness.

---

## §2 Setup — run this

### 2.1 No new packages

```bash
grep -n 'crewai' pyproject.toml
```

- The DSL ships inside `crewai==1.15.17`. **This is the surface Part 2 of the plan singles out as
  moving fast** — "the DSL/declarative-flow surface is moving fast — pin exact patch version". Expect
  §8's checks to actually find something today. That is a good outcome, not a bad one.

### 2.2 Create today's files

```bash
mkdir -p days/day-34/lab
touch days/day-34/lab/triage_flow.yaml
touch days/day-34/lab/load_dsl.py
touch days/day-34/lab/compare.md
touch tests/test_dsl_port.py
```

- `triage_flow.yaml` is the port. **Only the routing part** — `classify → route → three lanes` — not
  the whole flow. One small port that you finish beats a large one you abandon at 4pm.
- `compare.md` is today's real deliverable. It is a document, and it goes in the repo, because
  Principle 9 says every phase ends with a written decision you could defend to a hiring panel.
- Note there is **no new `src/mandala/` file today.** The Python flow stays the production path. The
  DSL port is an experiment that lives in `days/`, and keeping experiments out of `src/` is how a
  repo stays readable.

---

## §3 CR-20 — the port

### 3.1 What the DSL is made of

Four vocabulary items, and each maps onto something you already wrote:

| DSL concept | Your Python | The difference |
|---|---|---|
| **step** | a `@start` / `@listen` method | declared, not defined |
| **CEL condition** | the `if`s in `route()` (Day 31) | an expression language, not Python |
| **`each.do`** | a `for` loop | iteration without arbitrary control flow |
| **composite / single-agent action** | a call into `organs.py` | the escape hatch back into code |

**CEL** — Common Expression Language — is the piece worth understanding properly. It is a small,
sandboxed, non-Turing-complete expression language: it can evaluate `state.severity == "critical"`
and cannot loop, call out, or import. That property is the whole reason a DSL can be safe to accept
from an untrusted author. **Not-Turing-complete is a feature here**, exactly as it is for a database
query planner, and saying that out loud is a good interview moment.

### 3.2 `days/day-34/lab/triage_flow.yaml`

Port Day 31's router and nothing else. The shape below is *illustrative* — the real key names come
from §8's verification, and where yours differ, fix the file and note the diff in `compare.md`.

```yaml
# Day 31's route() -- as data.
# Every condition here was an `if` in intake.py. Compare them side by side.

name: mandala-triage
state:
  ticket_id: string
  severity: string
  category: string

steps:
  - id: classify
    start: true
    action:
      agent: triage_analyst          # a single-agent action
      inputs: [ticket_id]
      output: severity, category

  - id: route
    router: true
    when:
      - condition: 'state.severity == ""'
        goto: escalate
      - condition: 'state.severity == "critical"'
        goto: escalate
      - condition: 'state.severity == "low" && state.category in ["password_reset", "how_to"]'
        goto: fast
      - default: deep

  - id: fast
    action: { agent: triage_analyst, budget: 1 }
  - id: deep
    action: { crew: mandala_mini, budget: 20 }     # a composite action
  - id: escalate
    action: { none: true, budget: 0 }
```

**Line by line, and what each line costs you:**

- `state:` declaring three fields **as strings** — and there is the first loss. Day 30's
  `MandalaState` is a Pydantic model with `max_length` bounds, a `Literal` for `stage`, a nested
  `TriageResult`, and a `record()` method. A DSL state declaration is a flat bag of primitives. **Ask
  yourself where `max_length` went**, and write the answer in `compare.md`: it did not go anywhere,
  it stopped existing.
- `condition: 'state.severity == ""'` for the None case — notice the port could not express "triage
  is None" and had to become "severity is empty string". That is not a translation, it is a
  **semantic change**, and it is exactly the kind of thing a port surfaces and a rewrite hides.
- `&&` rather than `and` — CEL is not Python and does not pretend to be. Every muscle memory you have
  will produce a load error today. That load error is the feature: it happens at load time.
- `state.category in ["password_reset", "how_to"]` — Day 31's `FAST_LANE_CATEGORIES` frozenset, now
  inline in a condition. **Second loss: the constant is gone**, so the policy is duplicated wherever
  it is used and nothing keeps the copies in sync. Unless the DSL has a variables/constants
  facility — check, and if it does, use it and say so.
- `- default: deep` — every router needs a fallback. Day 31 made the same call in Python with the
  final unconditional `return Route.DEEP`. **Check whether the DSL enforces a default at load time.**
  If it does, that is a genuine win over Python worth writing down: a missing branch becomes
  impossible rather than merely tested-for.
- `budget: 1` / `budget: 20` / `budget: 0` — Day 31's `ROUTE_BUDGET` dict, now attached to the steps
  themselves. **This is a win.** In Python the budget lived in one file and the step in another, and a
  test had to hold them together. Here they cannot drift. Note it: *"data co-locates metadata that
  code separates."*
- `crew: mandala_mini` — the composite action, and the escape hatch. The autonomous organ is a *name*
  here. Everything Day 31 put in `organs.py` — the two precondition raises, the summary-not-body
  choice, the parsing and bounding — **has no expression in this file at all.** It still exists, in
  Python, behind the name. That is the honest picture of declarative orchestration: the declarative
  part is the skeleton, and the interesting decisions live in the code it names.

### 3.3 `days/day-34/lab/load_dsl.py` — 0 model requests

```python
"""Load the YAML flow and print what the framework understood.

Run:
    uv run python days/day-34/lab/load_dsl.py

Budget: 0 requests. Loading is not running -- that is the point of today.
"""

from pathlib import Path

import yaml

SPEC = Path(__file__).parent / "triage_flow.yaml"
raw = yaml.safe_load(SPEC.read_text(encoding="utf-8"))

print(f"name    {raw['name']}")
print(f"steps   {[s['id'] for s in raw['steps']]}")

# TODO(me): construct the 1.15.17 FlowDefinition from `raw` and print its validated form.
# Then BREAK it on purpose -- change 'goto: fast' to 'goto: fastt' -- and record
# whether the failure is at LOAD time or at RUN time. That answer is today's finding.
raise NotImplementedError("wire FlowDefinition, then delete this line")
```

**Line by line:**

- `yaml.safe_load` — **`safe_load`, never `load`.** Plain `yaml.load` can construct arbitrary Python
  objects from a document, which turns a flow definition into remote code execution the moment
  someone else authors one. Given that §1's argument for DSLs is *"a flow that is data cannot import
  os"*, loading it unsafely would undo the entire point in one line. If `pyyaml` is not already a
  transitive dependency, that is a ledger row and a changelog line — check before adding it.
- `Path(__file__).parent / "triage_flow.yaml"` — location-independent, so the script works from any
  working directory. Day 0's `ROOT = Path(__file__).resolve().parent.parent` made this same argument.
- The **deliberate typo experiment** is the assignment. `goto: fastt` in Python's world (Day 31) is a
  silent no-match at runtime — the flow runs and does nothing. If the DSL catches it at load, that is
  a concrete, demonstrable advantage and it belongs at the top of `compare.md`. **Do not take the
  win on faith. Break it and look.**

### 3.4 `days/day-34/lab/compare.md` — the deliverable

Write this yourself. The table below is the skeleton; the right-hand column is the day's work.

```markdown
# Python flow vs. FlowDefinition DSL — Mandala, 2026-08-__

Ported: Day 31's `route()` and its three lanes. Not ported: state model, organs, approval gate.

| Dimension | Python (Days 30–33) | DSL (today) | Verdict |
|---|---|---|---|
| Typo in a route label | silent no-match at runtime | ? (§3.3 experiment) | |
| Typed state with bounds | Pydantic, `max_length`, `Literal` | flat primitives | |
| Policy constants | `FAST_LANE_CATEGORIES` in one place | inline per condition | |
| Budget beside the step | separate dict + a test to bind them | attached to the step | |
| Missing default branch | caught by a test | ? load-time? | |
| Expressing "triage is None" | direct | had to become `== ""` | |
| The autonomous organ | 40 lines with two guards | one name | |
| Who can safely author it | me | ? | |
| Debuggability at 2am | breakpoint anywhere | ? | |

## What I would actually use, and when

<two paragraphs, in your own words>

## The one thing that surprised me

<one paragraph>
```

**Why this file exists in this form:**

- **Every row is a fact you can produce today**, not an opinion you could have written last week. A
  comparison table with no experiments behind it is a blog post.
- The `?` cells are the assignment. Fill them by running things.
- *"Who can safely author it"* is the row that matters most and gets skipped most. The real argument
  for declarative orchestration is almost never developer ergonomics — it is that **someone who is
  not a developer, or something that is not a person, can produce one safely.** Hold that thought
  until Day 84's graduated autonomy, where "the model proposes a flow change" stops being
  hypothetical.
- *"Debuggability at 2am"* is the row that decides most real adoptions. Be honest about it.

---

## §4 What the port cost you — read after you have done it

Do not read this section until §3 is done. It will make you agree with someone else's findings
instead of producing your own.

<details>
<summary>Expand after porting</summary>

Four losses show up reliably. Compare them against what you found:

1. **Validation moved earlier, expression power moved down.** CEL cannot call your functions. Day
   31's `triage.category in FAST_LANE_CATEGORIES` worked because `FAST_LANE_CATEGORIES` was a Python
   object; in CEL you inline the list or you use whatever variables facility the DSL provides. You
   traded *reach* for *safety*, and that trade is the entire design of every expression language ever
   embedded in a config file.
2. **The type system did not survive.** `MandalaState` is where Mandala's security property lives —
   `ticket_body` is `str | None` with a shouting docstring, and Day 30's `drop_body()` is meaningful
   because the field is typed and bounded. A flat string bag cannot express any of that. If the DSL
   supports referencing a Pydantic model for state, use it and note it as a major win; if it does
   not, that alone decides where the boundary between DSL and code has to sit.
3. **Composite actions are a wall, not a window.** `crew: mandala_mini` is readable and tells you
   nothing. Every guard in `organs.py` is invisible from the YAML. A reviewer reading only the DSL
   would conclude the deep lane is a single step with a budget of 20 — which is true and also misses
   both security preconditions. **Declarative files describe structure, never invariants.**
4. **Debugging changes shape.** You cannot set a breakpoint in a condition. Debugging becomes
   "print the evaluated state and stare", which is workable and is not the same as stepping. Weigh
   this honestly against the load-time validation win — for a flow edited weekly by five people, the
   DSL wins; for one edited by you at 2am during an incident, it may not.

And one win that is easy to undersell: **a data flow can be generated.** Everything in Phase 12's
capstone and Phase 13's deployment gets easier if a flow can be produced by a tool, versioned as
data, and diffed in a review. That is not an argument for porting Mandala. It is an argument for
knowing exactly where the seam would go if you ever had to.

</details>

---

## §5 CR-21 — the enterprise map, and why you build none of it

Three names, one paragraph each. **The plan says build nothing, and that instruction is a Principle-5
decision, not a shrug:** every one of these is a paid, hosted layer, and this project has no card on
file. What you owe them is recognition, not implementation.

- **AMP (Agent Management Platform)** — the deployment and operations layer: push a crew or flow,
  get a managed runtime, versioning, and rollbacks. The thing to understand is *what it replaces*:
  Day 85's FastAPI wrapper and Day 86's self-hosted server. When an interviewer asks "how would you
  deploy this", the answer that lands is "locally like this, and here's what the managed option
  buys and what it locks in."
- **Crew Studio** — the visual builder. Drag a crew together, ship it without writing Python. Its
  natural output is **exactly the declarative DSL from §3** — which is why these two IDs share a day.
  A visual builder needs a data representation of a flow, and CR-20 is that representation. Now the
  DSL's design constraints read differently: it is not a config format, it is a *UI's file format*.
- **Agent Control Plane** — policy and governance across many agents: cost-limit rules, registries,
  skills catalogues, who may run what. This is the enterprise version of two things you have already
  built by hand — `docs/RATE_BUDGET.md`'s standing rules and Day 31's `ROUTE_BUDGET`. **You have the
  concepts; they have the console.** Say it that way in an interview and you sound like someone who
  has thought about it rather than someone reciting a product page.

**The one-sentence version to keep:** *the managed layer sells deployment, authoring, and governance
— and the reason I can evaluate it is that I built a small version of all three by hand.*

---

## §6 The eval that must be able to fail

Today's tests are unusual: they test **the port's fidelity**, not the framework. That is the right
target — an inaccurate port produces a comparison you cannot trust, and the comparison is today's
deliverable.

### `tests/test_dsl_port.py`

```python
"""Does the YAML port actually agree with the Python it claims to mirror?"""

from pathlib import Path

import pytest
import yaml

from mandala.flows.intake import IntakeFlow
from mandala.flows.routes import ALL_ROUTES, ROUTE_BUDGET
from mandala.flows.state import MandalaState
from mandala.schemas import TriageResult

SPEC = yaml.safe_load(
    (Path("days/day-34/lab/triage_flow.yaml")).read_text(encoding="utf-8")
)
STEPS = {s["id"]: s for s in SPEC["steps"]}


def test_the_port_declares_every_python_route():
    assert ALL_ROUTES <= set(STEPS), sorted(ALL_ROUTES - set(STEPS))


def test_the_budgets_match_the_python_ones():
    for route, budget in ROUTE_BUDGET.items():
        assert STEPS[route]["action"].get("budget") == budget, route


def test_the_router_has_a_default_branch():
    router = STEPS["route"]
    assert any("default" in clause for clause in router["when"]), router["when"]


def test_exactly_one_step_is_the_start():
    assert sum(1 for s in SPEC["steps"] if s.get("start")) == 1


@pytest.mark.parametrize(
    ("severity", "category", "expected"),
    [
        ("low", "password_reset", "fast"),
        ("low", "billing", "deep"),
        ("critical", "outage", "escalate"),
    ],
)
def test_the_python_router_still_agrees_with_the_yaml_conditions(severity, category, expected):
    """If the port drifts from the code, the comparison in compare.md is a lie."""
    flow = IntakeFlow()
    flow.state = MandalaState(
        ticket_id="T-1004",
        triage=TriageResult(severity=severity, category=category, summary="fixture"),
    )
    assert flow.route() == expected


def test_the_yaml_is_loaded_safely():
    """Grep-as-a-test: no yaml.load anywhere in the repo."""
    offenders = [
        p.name
        for p in Path(".").rglob("*.py")
        if ".venv" not in p.parts
        and "yaml.load(" in p.read_text(encoding="utf-8", errors="ignore")
    ]
    assert offenders == [], offenders
```

**Line by line:**

- `SPEC` loaded at **module import**, so a malformed YAML fails collection loudly rather than one
  test at a time.
- `test_the_port_declares_every_python_route` uses `ALL_ROUTES <= set(STEPS)` — subset, not equality,
  because the YAML also has `classify` and `route` steps that are not routes. The assertion message
  prints the *difference*, so a failure names the missing lane instead of dumping two sets.
- `test_the_budgets_match_the_python_ones` is the one that will actually catch something. Two
  representations of the same policy drift the moment someone edits one. This test is why §3.2's
  "data co-locates metadata" win is safe to claim.
- `test_the_router_has_a_default_branch` encodes the §3.2 question as a test **regardless** of whether
  the framework enforces it. If the DSL does enforce it, this test is redundant and harmless; if it
  does not, this test is the enforcement. Writing it before you know the answer is the right order.
- `test_the_python_router_still_agrees_with_the_yaml_conditions` is the fidelity test, and note what
  it does *not* do: it does not execute the YAML. It asserts the Python behaves as the YAML claims,
  which is the honest thing a port test can assert when only one of the two is your production path.
  **Be clear-eyed that this is a weaker test than executing both** — write that limitation in
  `compare.md` rather than pretending.
- `test_the_yaml_is_loaded_safely` — a repo-wide grep for `yaml.load(`. Third day in a row for the
  grep-as-a-test pattern, and this one guards the property that makes the whole DSL argument work.
- **`.venv` excluded from the walk** — otherwise you are asserting things about your dependencies,
  which is neither your business nor a test you can fix.

---

## §7 Traps

- **Porting the whole flow.** You will not finish, and an abandoned port produces no comparison.
  Route + lanes, nothing else.
- **`yaml.load` instead of `yaml.safe_load`.** Undoes the entire safety argument for declarative
  flows in one function call.
- **Writing `compare.md` from intuition.** Every `?` in the table is an experiment. Run them.
- **Concluding "code is better" because you know Python better.** Familiarity is a real cost and it
  is not the same as a design property. Separate the two in your write-up.
- **Concluding "data is better" because the YAML looks tidy.** It looks tidy because §3.2 pushed all
  the hard parts behind `crew: mandala_mini`.
- **Adding `pyyaml` without a ledger row.** Principle 4. Check whether it is already present
  transitively before you `uv add` it, and if you do add it, `docs/PINS.md` and
  `docs/CHANGELOG_PLAN.md` both get a line.
- **Treating CR-21 as reading.** The output is three sentences you can say out loud, tied to things
  you built. If you cannot connect Agent Control Plane to `ROUTE_BUDGET`, you have not done it.
- **Letting the port drift from the code and leaving the test red.** A red fidelity test means
  `compare.md` is comparing something to a thing that no longer exists.

---

## §8 Verify before you code

Written **2026-08-20** against `crewai==1.15.17`, and **this is the surface the plan explicitly warns
is moving fastest** (Part 2). Every key name in §3.2 is a hypothesis. Expect to find drift; log it
(Principle 14):

- **Does `FlowDefinition` exist in 1.15.17, and where does it import from?** If it has been renamed
  or moved since, that is a changelog line before you write any YAML.
- **Is the on-disk format YAML, JSON, or a Python object you construct?** §3.2 assumes YAML because
  that is the format a visual builder would emit; confirm rather than assume.
- **The actual key names** — `steps`, `when`, `goto`, `default`, `action`, `start`, `router`. Get
  these from the docs, correct §3.2, and note the diff.
- **Is validation really at load time?** This is the §3.3 experiment and the headline claim of the
  whole day. Break something on purpose and find out.
- **Does the DSL support a typed state model** (a reference to a Pydantic class) or only primitives?
  This single answer decides where the DSL/code boundary belongs in any real system.
- **Is there a constants or variables facility**, so `FAST_LANE_CATEGORIES` need not be inlined?
- **Does `each.do` exist and what does it iterate?** You are not using it today; know its shape so
  you recognise a fan-out when you meet `Send` on Day 44.
- `https://docs.crewai.com/concepts/flows` — the declarative/DSL section, read today.

---

## §9 Say it in an interview

> "CrewAI ships the same flow two ways, so I ported the routing layer to the declarative DSL and kept
> a table of what changed. The wins were real: a mistyped branch label failed at load instead of
> silently matching nothing at runtime, and the request budget sits on the step instead of in a
> separate dict that a test has to keep in sync. The losses were also real: my typed state model
> flattened to primitives, so the security property I rely on — raw customer text is a bounded,
> nullable field that gets deleted before the research step — has no expression in the DSL at all.
> And the autonomous crew becomes one word, which means a reviewer reading only the declarative file
> cannot see either of the guards protecting that boundary. My conclusion was that the DSL is the
> right shape for a skeleton authored by someone who isn't a Python developer — which is exactly what
> a visual builder needs — and the wrong place to put invariants. That's the seam I'd cut on."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 34
```
