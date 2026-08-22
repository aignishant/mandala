# Day 80 — CHECKLIST

**IDs covered:** — (capstone assembly: the research organ, a CrewAI crew as one subgraph node)

## Demo command

```bash
uv run pytest tests/test_research_organ.py -v          # 0 requests — crew monkeypatched
uv run python days/day-80/lab/research_only.py "printer offline after firmware update"
uv run python days/day-80/lab/prune_experiment.py
uv run python days/day-73/lab/compare.py triage-baseline-D73 prune-dedupe-by-url
uv run python days/day-79/lab/run_spine.py T-9003      # research node now real
```

Expected: findings returned as `Untrusted` with source URLs; the organ never exceeds its budget
slice; the spine's `research` node no longer raises.

## Setup

- [ ] `./m start 80` and `./m scaffold 80` run
- [ ] **No new dependencies**
- [ ] Module named `organs/`, **not** `crew/` — and can say why
- [ ] Day 23's crew reused rather than rewritten
- [ ] **`days/day-77/lab/debts.md` opened and read** — today is the pruning debt's due date

## Wall one — read-only toolbelt

- [ ] Tool names derived from / checked against `permissions.TOOLS`
- [ ] **Two import-time assertions**: all declared, none write
- [ ] Verified the assertion fires by temporarily adding a write tool
- [ ] `MAX_RESULTS` bounds each search at the tool
- [ ] Snippet format (`title :: href :: body`) decided here, once, for tomorrow's citation checker
- [ ] Crew's LLM still pinned to the free-tier model (Principle 4) — checked, not assumed

## Wall two — the organ

- [ ] `research()` takes and returns plain types — no framework names in the signature
- [ ] `Finding.claim` is `Untrusted` and `source` records the URL
- [ ] Organ gets a **slice** of the run budget: `min(SHARE, remaining)`
- [ ] Parent budget charged in a **`finally`** — verified with a deliberately crashing crew
- [ ] `BudgetExceeded` → `[]` (degraded, valid) and the truncation recorded in the span
- [ ] `MAX_FINDINGS` bounds at the organ, in addition to the tool bound
- [ ] `_parse` skips malformed lines rather than raising
- [ ] Can explain why parsing is **lenient** here and **strict** on the classifier

## Wall three — pruning (the Day-77 debt)

- [ ] Three strategies implemented and run
- [ ] Compared with `compare.py`, **per example**, not by aggregate
- [ ] Three numbers recorded
- [ ] `shortest_first` checked for rubric-gaming (short findings → short drafts → length check passes)
- [ ] Winner chosen with a written reason; folklore avoided
- [ ] `debts.md` row updated to "cleared, Day 80"

## Tests that must be able to fail

- [ ] `test_the_researcher_holds_no_write_tool` — **flip it:** add `save_note`, watch import fail
- [ ] `test_every_researcher_tool_is_declared_in_the_permission_table`
- [ ] `test_findings_are_untrusted_and_carry_their_source`
- [ ] `test_a_finding_cannot_be_interpolated_into_a_prompt`
- [ ] `test_malformed_lines_are_skipped_not_fatal`
- [ ] `test_findings_are_bounded`
- [ ] `test_the_organ_cannot_spend_the_whole_run_budget` — **flip it:** pass `budget` straight through
- [ ] `test_a_failed_crew_still_charges_the_parent_budget` — costs nothing, prevents an outage
- [ ] `test_no_findings_is_a_valid_outcome_not_an_error`
- [ ] `test_the_organ_signature_mentions_no_framework`
- [ ] All cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why must the Researcher never hold a write tool — in trifecta terms?
- [ ] Why is a search snippet untrusted, and which red-team attack proved it?
- [ ] Why a budget slice rather than the whole run budget?
- [ ] What happens without the `finally` on the budget charge?
- [ ] Why strict parsing in one place and lenient in another?
- [ ] Why `organs/` rather than `crew/`?
- [ ] Why does following a URL a search result suggested reopen RT-05?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~35)
- [ ] **Requests-per-finding recorded** — Day 84 uses it for the autonomy decision
- [ ] Ratio against Day 79's spine (~12) noted for the Day-89 portfolio
- [ ] `@tool` import path and naming confirmed on `crewai==1.15.17`
- [ ] Crew output type confirmed (`CrewOutput` vs string) — `_parse` depends on it
- [ ] Native crew iteration / `max_rpm` caps checked; noted which limit fires first
- [ ] `ddgs` result keys confirmed on 9.15.0
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 80
```

- [ ] `debts.md` updated
- [ ] Pruning decision and its three numbers committed
- [ ] `./m done 80` succeeded
