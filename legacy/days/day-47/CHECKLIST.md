# Day 47 — CHECKLIST

**IDs covered:** LG-06 🛠️ (checkpointers), LG-07 🛠️ (the Store), AG-12 🛠️ (memory taxonomy,
completed)

## Demo command

```bash
uv run python days/day-47/lab/two_threads.py                      # 0 requests
uv run python days/day-47/lab/kill_and_resume.py T-9002 a1 crash  # ~11 requests
uv run python days/day-47/lab/kill_and_resume.py T-9002 a1 resume # 0-5 requests
uv run pytest tests/test_graph_persistence.py tests/test_store.py -v
diff days/day-32/lab/kill_and_resume.py days/day-47/lab/kill_and_resume.py
```

## Setup

- [ ] `./m start 47` and `./m scaffold 47` run
- [ ] **Day 40's and Day 42's predictions for this day re-read first**
- [ ] `langgraph-checkpoint-sqlite` version verified live, pinned, ledger + changelog
- [ ] Noticed the backend is a **separate package** — and can say what that implies about the swap
- [ ] `.mandala/` confirmed git-ignored **before** the first checkpointed run
- [ ] Files created (`graph/persistence.py`, `graph/memory.py`, two tests, three lab files)

## LG-06 — checkpointers

- [ ] Can define a **super-step**, and say why a five-way fan-out is one
- [ ] Can say why the unit of durability being the unit of concurrency is not a coincidence
- [ ] `checkpointer()` is a **context manager** — connection closed
- [ ] `thread_id()` **raises** on an empty attempt (Day 32's trap, carried as a constraint)
- [ ] `.compile(checkpointer=saver)` used — durability is compile-time
- [ ] `{"configurable": {"thread_id": ...}}` nesting correct
- [ ] `graph.get_state(config).next` printed **before** resuming — Day 32 had no equivalent
- [ ] `invoke(None, config=...)` used to resume — and knows why `{}` is different
- [ ] Crash run and resume run both performed; **ratio recorded**
- [ ] `body None` confirmed after a round trip through disk

## What reaches disk

- [ ] `NEVER_PERSIST` **identical** to Day 32's set
- [ ] Established whether LangGraph has a field-exclusion hook (§8)
- [ ] If not: `scrub_node` written **and scheduled** before anything expensive
- [ ] Can state the uncomfortable conclusion: **ordering is a security property again**
- [ ] Noticed this is the third framework where the same constraint reappeared

## LG-07 — the Store

- [ ] Can fill in the five-row checkpointer-vs-Store table
- [ ] Can say why the **"written by"** row is the one that matters
- [ ] `WRITABLE_FACTS` is an **allowlist**, and can say why a denylist fails open
- [ ] `remember()` **raises** on a non-allowlisted key — no silent no-op
- [ ] Values bounded — a recalled fact is prompt material
- [ ] Can recite the three-part rule: **stable, customer-stated, showable**
- [ ] Can explain the **persistent prompt injection** risk in one sentence (AG-15, Day 65)
- [ ] `two_threads.py` run — including the **refusal loop**
- [ ] Refusal loop kept for the Day-65 and Day-70 demos
- [ ] Persistent Store backend identified (not `InMemoryStore`) for real runs
- [ ] Store retention/TTL question answered — or logged as a Day-84 task

## Tests that must be able to fail

- [ ] `test_the_two_frameworks_scrub_the_same_fields` — **flip it:** diverge one set, see red
- [ ] `test_scrub_node_clears_every_never_persist_field`
- [ ] `test_scrub_node_only_touches_never_persist_fields` — the negative-space sibling
- [ ] `test_a_thread_id_requires_an_attempt`
- [ ] `test_two_attempts_on_one_ticket_differ`
- [ ] `test_the_checkpoint_dir_is_git_ignored`
- [ ] `test_staleness_policy_matches_the_other_framework`
- [ ] `test_the_scrub_node_is_scheduled_before_expensive_nodes` — **weakness stated**, and the
      stronger edge-walking version attempted
- [ ] `test_an_allowlisted_fact_round_trips`
- [ ] `test_a_non_allowlisted_fact_is_refused[refund_authorised|…]` — **flip it:** denylist, see red
- [ ] `test_the_allowlist_is_small`
- [ ] `test_values_are_bounded`
- [ ] `test_recall_of_an_unknown_customer_is_empty_not_an_error`
- [ ] `test_facts_do_not_leak_between_customers`
- [ ] `test_no_free_text_fact_is_writable`
- [ ] All tests cost **0 model requests**

## AG-12 — `memory_taxonomy.md`

- [ ] Four-row table completed (D7, D32/47, D46, D47 Store)
- [ ] Answered: was Day 7 right that write policies matter more than storage?
- [ ] **Day 32's three questions asked of LangGraph** — and counted how many it answered
- [ ] Stated precisely what checkpointing gave you, without inflating it
- [ ] Day-40 and Day-42 predictions compared against reality

## Understanding check — answer out loud

- [ ] What is a super-step, and why does it matter for a fan-out?
- [ ] Which of Day 32's three hard questions did the framework answer for you?
- [ ] Why is there no way to keep a field out of a checkpoint except by scheduling?
- [ ] What is the difference between the checkpointer and the Store, in one sentence?
- [ ] Why is an allowlist the only defensible default for a permanent store?
- [ ] What is a persistent prompt injection, and what stops one here?

## Budget & freshness

- [ ] Both counts logged in `docs/RATE_BUDGET.md` (declared: ~16, Groq), with the ratio
- [ ] **Ratio compared against Day 32's ratio** — a bake-off row nobody else will have
- [ ] `SqliteSaver` import path and context-manager behaviour confirmed
- [ ] `invoke(None)` resume semantics confirmed
- [ ] `get_state().next` contents confirmed
- [ ] **Serialization/exclusion hook question answered** — §3.2 rewritten if one exists
- [ ] `DeltaChannel` behaviour established (automatic or opt-in; effect on resume)
- [ ] Store item shape (`item.key`, `item.value`) confirmed
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 47
```

- [ ] Bake-off rows updated: **durability granularity**, **how much of a failed run is saved**,
      **cross-thread memory**
- [ ] `./m done 47` succeeded — trackers updated automatically
