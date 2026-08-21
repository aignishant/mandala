# Day 82 — CHECKLIST

**IDs covered:** — (capstone assembly: durable approval gate + the first external write; realises
AG-20 and LG-09 in the capstone)

## Demo command

```bash
uv run pytest tests/test_approval.py tests/test_external_write.py -v   # 0 requests
uv run python days/day-79/lab/run_spine.py T-9004        # stops at the gate
# close the terminal completely
uv run python days/day-82/lab/approve_cli.py --list
uv run python days/day-82/lab/approve_cli.py T-9004-<suffix> approve --by "you"
cat outbox/T-9004-*.json && cat .state/approvals/T-9004-*.json
```

Expected: the run suspends at the gate; a **different process** approves it; exactly one file in
`outbox/`; approving twice produces one write, not two.

## Before any code — the drift test

- [ ] `test_the_checked_in_table_is_not_stale` green **before** the change
- [ ] Write tool added to `permissions.py`; test goes **red**
- [ ] Table regenerated; **`git diff docs/PERMISSION_TABLE.md` read properly**
- [ ] New row shows `✍️ yes` with a blast-radius sentence you wrote
- [ ] Trifecta table recomputed — **zero ❌ VIOLATION rows**; if not, stopped and fixed structurally
- [ ] Can say why this failure is the feature working (Day 70 §4.2 predicted it)

## The write tool, declared

- [ ] `sees_untrusted_text=False` on the Resolver — **honestly**, not aspirationally
- [ ] Resolver receives a validated `Resolution` + approval, never the ticket body or findings
- [ ] `reads_untrusted` on the tool decided by thinking about what the channel returns
- [ ] `blast_radius` names what it destroys **and** states the retry policy
- [ ] Channel is a **local `outbox/`** — reason written down (not just budget)
- [ ] `outbox/` gitignore decision made deliberately (it is evidence for Day 83; decide and note)

## The durable gate

- [ ] `Approval` is a frozen record: run, hash, by, at, decision, reason
- [ ] `check()` validates four distinct failure causes with four distinct messages
- [ ] `check()` called **even on a freshly-made approval** — one code path
- [ ] `existing is not None` branch makes resume **idempotent** — no re-asking the human
- [ ] `interrupt()` payload shows the customer-facing text and hash, **nothing internal**
- [ ] `decided_by` required, not defaulted
- [ ] Timestamps timezone-aware
- [ ] CLI lists pending runs **from the checkpointer**, not a parallel list
- [ ] CLI prints the draft in full, untruncated

## The kill-at-the-gate drill (§4.2)

- [ ] Run suspended at the gate; **terminal closed entirely**
- [ ] Approved from a fresh process
- [ ] Verified nothing before the gate re-ran
- [ ] Verified the draft came from the checkpoint, not a fresh model call
- [ ] `.state/approvals/` inspected
- [ ] **Approved twice — exactly one write produced**
- [ ] Whole drill written up in `days/day-82/lab/kill_at_the_gate.md`

## The write

- [ ] Three gates in order: permission → approval → already-sent
- [ ] `AlreadySent` **raises**; the receipt file's existence is the record
- [ ] Span carries `run_id`, `draft_hash` and `approved_by`
- [ ] Can say why those attributes are what makes tomorrow's gate provable
- [ ] Decision recorded on whether `agent=` should be defaulted or required

## Tests that must be able to fail

- [ ] `test_no_approval_means_no_write`
- [ ] `test_an_approval_for_a_different_run_is_refused`
- [ ] `test_a_changed_draft_invalidates_the_approval` — **flip it:** drop the hash check, approve A
      and send B
- [ ] `test_a_rejection_is_not_an_approval`
- [ ] `test_reordering_citations_does_not_invalidate_an_approval`
- [ ] `test_writing_twice_raises_rather_than_duplicating` — asserts the exception **and** the file count
- [ ] `test_an_agent_without_the_grant_cannot_write`
- [ ] `test_the_researcher_still_holds_no_write_tool`
- [ ] `test_no_agent_holds_the_lethal_trifecta_after_adding_a_write_tool` — **green for 74 days,
      teeth today**
- [ ] `test_the_permission_table_was_regenerated`
- [ ] `test_every_write_span_carries_an_approval_attribute`
- [ ] All cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why is `input("approve? y/n")` not an approval system?
- [ ] Why bind an approval to a draft hash rather than to a run?
- [ ] Why must a resumed graph not re-ask the human?
- [ ] Why is a boolean not evidence for the Phase-12 gate?
- [ ] What makes this write idempotent, and what would you do if it weren't?
- [ ] Why is the Resolver's `sees_untrusted_text=False` the whole separation argument?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~12)
- [ ] Noted that the **riskiest code in the system costs 0 requests to test** — and why that's not an
      accident
- [ ] `interrupt()` semantics confirmed: does the node re-execute on resume? — **today's biggest risk**
- [ ] `Command(resume=...)` API confirmed
- [ ] Enumerating interrupted threads from `SqliteSaver` confirmed
- [ ] `asdict()` round-trip through the checkpointer confirmed
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 82
```

- [ ] Regenerated `docs/PERMISSION_TABLE.md` committed **with** the code change
- [ ] `kill_at_the_gate.md` committed
- [ ] `./m done 82` succeeded
