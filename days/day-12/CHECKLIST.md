# Day 12 — CHECKLIST

**IDs covered:** OAI-07 🛠️ (context objects & dependency injection), OAI-08 🛠️ (guardrails: input & output)

## Demo command

```bash
cd days/day-12/lab
uv run python injected_tools.py researcher
uv run python injected_tools.py resolver      # same tool, different identity
uv run python guardrail_demo.py
cd ../../..
```

Expected: `researcher` reads the ticket, `resolver` is refused by `PermissionDenied` — with **no
change to the tool**. `guardrail_demo.py` blocks two of three cases at **0 requests**.

## Setup

- [ ] `./m start 12` and `./m scaffold 12` run
- [ ] No new packages
- [ ] Files created (`src/mandala/context.py`, `guardrails.py`, two lab files, two test files)

## OAI-07 — context injection

- [ ] `MandalaContext` is a **frozen** dataclass
- [ ] Holds `actor`, `request_id`, services — and **no instructions**
- [ ] `memory` uses `field(default_factory=...)`
- [ ] `approvals_required` defaults to **True** (default deny)
- [ ] `may_write` is a **derived property** from `mandala.permissions`, not a stored flag
- [ ] `audit()` produces one greppable line carrying `request_id`
- [ ] Tools declare `ctx: RunContextWrapper[MandalaContext]` as the **first** parameter
- [ ] Printed `params_json_schema` and **confirmed `ctx` is absent** from it
- [ ] `check(context.agent_name, tool)` called inside the tool
- [ ] `source=context.actor` used for memory writes — provenance the agent cannot forge
- [ ] Ran as both actors and observed the same tool behave differently

## OAI-08 — guardrails

- [ ] Can state the rule: **a guardrail must cost less than what it protects**
- [ ] All four guardrails cost **0 model requests**
- [ ] `SECRET_PATTERNS` stores `(name, pattern)` pairs
- [ ] `find_secrets()` returns **names only** — never the secret
- [ ] Patterns compiled at module level
- [ ] Word boundaries (`\b`) and length floors (`{20,}`) used to avoid false positives
- [ ] `no_secrets_in_input` — input guardrail
- [ ] `input_is_within_budget` — Day-4's context budget, enforced for free
- [ ] `no_secrets_in_output` — the mirror; understood why it is **not** redundant
- [ ] `no_other_customers` — the plan's own OAI-08 example
- [ ] **`_as_text()` unwraps `TriageResult`** — the typed-output trap handled
- [ ] Guardrails attached via `input_guardrails=` / `output_guardrails=`
- [ ] Observed the tripwire exceptions and reached `exc.guardrail_result.output.output_info`
- [ ] Confirmed blocked runs cost **0 requests**

## Tests that must be able to fail

- [ ] `test_each_secret_pattern_is_detected` (6 cases)
- [ ] `test_ordinary_text_does_not_false_positive` (4 cases) — the negatives matter more
- [ ] `test_find_secrets_never_returns_the_secret`
- [ ] `test_input_guardrail_trips_on_a_secret`
- [ ] `test_input_guardrail_passes_clean_text`
- [ ] `test_budget_guardrail_trips_above_the_limit`
- [ ] `test_output_guardrail_inspects_typed_output_not_its_repr` — delete `_as_text`'s branch and confirm **red**
- [ ] `test_context_is_immutable`
- [ ] `test_may_write_is_derived_from_the_permission_table`
- [ ] `test_approvals_are_required_by_default`
- [ ] `test_context_parameter_is_not_in_the_tool_schema` — a security property, asserted
- [ ] `test_tool_uses_injected_path_not_a_global` — **`TODO(me)` solved** (learn to construct `RunContextWrapper`)
- [ ] Both test files cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why is putting identity in the context a *security* decision, not just an ergonomic one?
- [ ] Why is `may_write` derived rather than stored?
- [ ] What breaks on Day 44 if the context is mutable?
- [ ] What exactly goes wrong if `_as_text` does not unwrap a typed output?
- [ ] Why are input and output secret guardrails not redundant?
- [ ] When is it correct for a guardrail to call a model, and when is it not?
- [ ] Why must `output_info` never contain the matched secret?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~24, Groq)
- [ ] Verified the guardrail exception attribute chain in 0.22.0
- [ ] Verified that the context parameter is excluded from the schema **by printing it**
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 12
```

- [ ] `./m done 12` succeeded — trackers updated automatically
