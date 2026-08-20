# Day 4 — CHECKLIST

**IDs covered:** AG-03 🛠️ (structured output), AG-04 🛠️ (context window as budget)

## Demo command

```bash
cd days/day-04/lab
uv run python triage_naked.py T-1001 tool
uv run python compare.py
uv run python fat_context.py
cd ../../..
```

Expected: a validated `TriageResult` printed as JSON, the three-technique comparison table, and the
fat-context table showing tokens climbing while quality drops.

## Setup

- [ ] `./m start 4` and `./m scaffold 4` run
- [ ] `uv add "pydantic==2.13.4"` — declared **directly**, not relied on as a transitive dep
- [ ] Today's files created (`src/mandala/schemas.py`, `budget.py`, `lab/triage_naked.py`, `lab/compare.py`, `lab/fat_context.py`, `tests/test_triage_schema.py`)

## AG-03 — structured output

- [ ] `src/mandala/schemas.py` — `TriageResult` written
- [ ] `Severity` and `Category` are **`Literal` aliases at module level**, not `str`
- [ ] **Every** field has a `Field(description=...)`
- [ ] The `severity` description states *when* to use `critical` (a rule, not a label)
- [ ] The `category` description gives an explicit escape hatch (`prefer 'other'`)
- [ ] The `confidence` description says concretely what low confidence looks like
- [ ] `CONFIDENCE_FLOOR` is a named constant
- [ ] `needs_human_review()` implemented on the model
- [ ] All three techniques implemented (`tool`, `native`, `prompt`)
- [ ] `tool_choice` used to **force** `submit_triage`
- [ ] `parameters` come from `TriageResult.model_json_schema()` — schema defined once
- [ ] Noted whether your Groq model supports `response_format` at all

## AG-04 — context as budget

- [ ] `src/mandala/budget.py` — `ContextBudget` with `charge`, `total`, `over_budget`, `report`
- [ ] `spent` uses `field(default_factory=dict)`, **not** `= {}`
- [ ] Report sorted **descending** by tokens
- [ ] `ContextBudget` wired into `src/mandala/loop.py`; report printed on every run
- [ ] Buckets are separated: `system` / `tool_schemas` / `history` / `tool_results`

## Experiments actually run

- [ ] `compare.py` — the table exists, and **you saved it** (it is interview evidence)
- [ ] Counted how many "ask nicely" responses were unparseable
- [ ] `fat_context.py` — observed tokens climb **and** severity/confidence drift at ×20
- [ ] Observed the trimmed projection stay stable at ×20
- [ ] Deleted a `Literal` value the model likes → saw the `ValidationError` fire

## Tests that must be able to fail

- [ ] `test_drifted_severity_labels_are_rejected[URGENT|urgent|High|sev1|]` (5 cases)
- [ ] `test_confidence_is_bounded[-0.1|1.4|2.0]`
- [ ] `test_summary_length_is_enforced`
- [ ] `test_critical_always_needs_human_review`
- [ ] `test_low_confidence_needs_human_review`
- [ ] `test_schema_exposes_descriptions_to_the_model` — remove a description and confirm it goes **red**
- [ ] `test_every_golden_ticket_produces_a_valid_result` — **all 10**, not most
- [ ] `test_ambiguous_ticket_reports_low_confidence` (T-1007) — **was red first**; fixed via the *prompt*
- [ ] `test_empty_ticket_reports_low_confidence` (T-1006)
- [ ] Cassettes recorded, then the suite replays with **0 requests**
- [ ] `grep -ril "gsk_\|sk-\|AIza" tests/fixtures/cassettes/` prints nothing

## Understanding check — answer out loud

- [ ] Why `Literal` instead of `str`, in one sentence, with a concrete failure it prevents?
- [ ] Why is `confidence` the field that makes Day-84 graduated autonomy possible?
- [ ] Why is `estimate()` deliberately approximate, and what would exact counting buy you?
- [ ] Why is `field(default_factory=dict)` required instead of `= {}`?
- [ ] What does `tool_choice` change, and what error do you get without it?
- [ ] Which of the four context levers is cheapest, and why do people skip it?
- [ ] Why did *more* context make the answer *worse*?

## Budget

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~80, Groq)

## Commit

```bash
./m check
./m done 4
```

- [ ] `./m done 4` succeeded — trackers updated automatically
