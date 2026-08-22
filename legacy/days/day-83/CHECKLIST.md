# Day 83 — CHECKLIST

**IDs covered:** — (capstone assembly: report organ, write audit, end-to-end run on 20 unseen tickets)

## Demo command

```bash
uv run python scripts/daily_report.py                      # check headroom BEFORE starting
uv run pytest tests/test_report.py tests/test_write_audit.py -v
uv run python days/day-83/lab/run_end_to_end.py tests/fixtures/unseen/
uv run python days/day-82/lab/approve_cli.py --list         # then approve each by hand
uv run python scripts/audit_writes.py                       # must exit 0
```

Expected: twenty runs; every write traceable to an approval with a matching hash; audit exits 0;
report generated from spans alone.

## The unseen set — write it FIRST

- [ ] Twenty tickets written **without opening `golden_tickets.jsonl`**
- [ ] Coverage: ≥3 no-research, ≥3 research, 2 ambiguous severity, 2 non-English, 1 very long,
      1 nearly empty, **2 hostile**
- [ ] Expected severity + escalation labelled **before** any run
- [ ] Intent recorded in `days/day-83/lab/write_unseen_set.md`
- [ ] Can say why the golden set cannot serve as gate evidence

## Setup

- [ ] `./m start 83` and `./m scaffold 83` run
- [ ] **No new dependencies**
- [ ] One ticket run first and the JSONL grepped to confirm `run_id` is on every needed span
- [ ] Approval-decision span exists (added to Day 82's node if missing) — **before** the batch
- [ ] Headroom checked; batch split across two days if any provider is above ~60%

## The report organ

- [ ] Generated **from spans**; no `report.append()` inside nodes
- [ ] Spans sorted by `start_ns` — and can say which rubrics break without it
- [ ] Only this run's spans included
- [ ] `approved` has **four** states including `pending`
- [ ] Failures computed by re-running **the Day-71 rubrics** — one definition of "wrong"
- [ ] Fourth trajectory adapter written; **no rubric changed** — noted for the Day-89 write-up

## The write audit

- [ ] Crosses **three** independent records: spans, approval files, receipts
- [ ] Flags: no approval record, hash mismatch, write after rejection, missing identifiers
- [ ] Receipt count vs write-span count compared
- [ ] Exits non-zero on any problem
- [ ] **Added to `.github/workflows/evals.yml`** today

## The end-to-end run

- [ ] All twenty dropped through intake and run
- [ ] Every gate approved or rejected **by hand** through the Day-82 CLI
- [ ] **Total human review time recorded**
- [ ] Time broken down by severity where possible
- [ ] Per-ticket outcome recorded: approved / rejected / edited-then-approved
- [ ] **Every rejection reason written down** — these are tomorrow's autonomy criteria
- [ ] Nothing fixed mid-run; fixes logged in `days/day-83/lab/findings.md` and applied after
- [ ] If fixes were substantial: re-ran cleanly, or noted in the ADR that evidence is pre-fix
- [ ] Both hostile tickets: outcome recorded verbatim

## Tests that must be able to fail

- [ ] `test_spans_are_ordered_by_start_time_not_export_order` — **flip it:** drop the sort, ordering
      rubrics go random
- [ ] `test_only_this_runs_spans_are_included`
- [ ] `test_pending_is_a_distinct_outcome_from_rejected`
- [ ] `test_the_audit_flags_a_write_with_no_approval_record`
- [ ] `test_the_audit_flags_a_hash_mismatch`
- [ ] `test_the_audit_flags_a_write_span_with_no_identifiers`
- [ ] `test_receipt_count_must_match_write_span_count`
- [ ] `test_the_unseen_set_is_disjoint_from_the_golden_set` — **mechanises the gate's meaning**
- [ ] `test_the_unseen_set_includes_hostile_tickets`
- [ ] All cost **0 model requests**

## Understanding check — answer out loud

- [ ] What is the difference between regression and capability, in terms of these two datasets?
- [ ] Why does editing a prompt mid-run invalidate the gate evidence?
- [ ] Why cross three records in the audit rather than reading one?
- [ ] Why is `pending` not `rejected`?
- [ ] Why did the cache not help today, and what does that tell you about what caching is for?
- [ ] What did the hostile tickets do, and which control caught them?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~120 — the largest day)
- [ ] Provider rotation / 429 behaviour observed under sustained load; **which provider answered**
      visible in the report
- [ ] `load_spans()` across multiple day-files confirmed (the run may straddle midnight)
- [ ] `start_ns` monotonicity across the batch processor confirmed
- [ ] `outbox/` git decision made and recorded
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 83
```

- [ ] Unseen set, report, audit script and findings committed
- [ ] Human-review timing and rejection reasons committed — **tomorrow depends on them**
- [ ] `./m done 83` succeeded
