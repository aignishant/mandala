# Day 10 — CHECKLIST

**IDs covered:** OAI-03 🛠️ (function tools & the `@tool` decorator), OAI-04 🛠️ (Runner deep-dive & the agent loop)

## Demo command

```bash
cd days/day-10/lab
uv run python tool_shapes.py        # 0 requests — the generated schema
uv run python runner_anatomy.py     # take RunResult apart
uv run python failure_modes.py      # the four failure modes
cd ../../..
```

Expected: `failure_modes.py` prints `recovered`, `boundary held`, whatever the SDK default is, and
`cap held`. **If case [2] prints `LEAKED`, stop and fix it before anything else.**

## Setup

- [ ] `./m start 10` and `./m scaffold 10` run
- [ ] No new packages
- [ ] Files created (`src/mandala/sdk_tools.py`, three lab files, two test files)

## OAI-03 — tools

- [ ] `tool_error()` written — **your** error policy, not the inherited default
- [ ] `PermissionDenied` is **re-raised**, not converted to text
- [ ] All other errors return JSON with `error`, `detail` (truncated) and a `hint`
- [ ] `failure_error_function=tool_error` attached to every tool that has a policy
- [ ] Every tool has type hints on every parameter
- [ ] Every docstring is google style with an `Args:` section, written **for the model**
- [ ] `get_ticket`'s description keeps Day 3's **"do NOT use this when…"** line
- [ ] `Annotated[int, Field(ge=1, le=5)]` used for the bounded parameter
- [ ] `name_override="draft_reply"` matches the name in `mandala.permissions`
- [ ] Ran `tool_shapes.py` and **compared the generated schema with Day 3's hand-written one**
- [ ] Checked specifically: docstring → `description`, `Args:` → per-param descriptions, `Field` → `minimum`/`maximum`, and whether `additionalProperties: false` is emitted

## OAI-04 — the Runner

- [ ] Can state the three run methods and when each is right
- [ ] Can state what **one turn** is, and why `max_turns` is a *request* budget
- [ ] Walked `result.new_items` and mapped each item type onto a Day-3 line
- [ ] Found `result.context_wrapper.usage` — and **confirmed whether it is populated on your provider**
- [ ] Used `result.to_input_list()` to continue a conversation manually
- [ ] Noted `result.last_agent` and why it matters on Day 13

## The four failure modes — actually run them

- [ ] **[1] Expected failure** → became text, model recovered with the other tool
- [ ] **[2] Boundary failure** → `PermissionDenied` escaped `Runner.run` and killed the run
- [ ] **[3] No handler** → recorded **exactly** what the SDK's default does, in your notes and for ADR-001
- [ ] **[4] Turn cap** → `MaxTurnsExceeded` raised

## Tests that must be able to fail

- [ ] `test_every_tool_has_a_description` (3 cases)
- [ ] `test_every_parameter_has_a_description` (3 cases) — remove an `Args:` entry and confirm **red**
- [ ] `test_name_override_is_applied`
- [ ] `test_field_constraints_reach_the_schema` — verifies a **framework claim**
- [ ] `test_negative_guidance_is_present_in_the_description`
- [ ] `test_error_policy_converts_expected_failures_to_text`
- [ ] `test_error_policy_reraises_permission_denied` — the security test
- [ ] `test_error_policy_truncates_long_messages`
- [ ] `test_a_turn_is_one_model_call_not_one_tool_call`
- [ ] `test_to_input_list_can_continue_a_conversation`
- [ ] `test_permission_denied_escapes_the_runner` — same property, tested at a **second layer**
- [ ] `tests/test_sdk_tools.py` costs **0 model requests**
- [ ] Cassettes recorded; suite replays offline

## Understanding check — answer out loud

- [ ] Which two sources become a tool's schema, and which becomes each field?
- [ ] Why must `PermissionDenied` re-raise instead of becoming a tool result?
- [ ] What is the SDK's default failure behaviour — exactly, having observed it?
- [ ] Why is `max_turns` a request budget rather than a tool-call budget?
- [ ] What does `to_input_list()` do, and which of your Day-7 methods is it equivalent to?
- [ ] Why test the permission boundary at both the policy-function level and the Runner level?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~29, Groq)
- [ ] Verified `params_json_schema`, `RunResult` attribute names, and the `MaxTurnsExceeded` import path against 0.22.0
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 10
```

- [ ] `./m done 10` succeeded — trackers updated automatically
