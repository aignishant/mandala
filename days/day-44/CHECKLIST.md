# Day 44 — CHECKLIST

**IDs covered:** LG-03 🛠️ (conditional edges & `Command`), LG-04 🛠️ (the Send API & map-reduce)

## Demo command

```bash
uv run python days/day-44/lab/two_routers.py     # 0 requests — two pictures, one behaviour
uv run python days/day-44/lab/fan_out.py T-9002  # 5 parallel requests
uv run pytest tests/test_graph_routing.py tests/test_fanout.py -v
```

Expected: a diamond in the graph drawing, five findings back from five branches, and interleaved
notes in nondeterministic order.

## Setup

- [ ] `./m start 44` and `./m scaffold 44` run
- [ ] No new packages
- [ ] Files created (`graph/routing.py`, `graph/fanout.py`, two tests, two lab files)

## LG-03 — routing

- [ ] Can fill in the **completed** four-framework router table (Days 13, 31, 39/42, 44)
- [ ] Can state the five-row difference between a conditional edge and a `Command`
- [ ] Chose the conditional edge for the severity router — **and can defend it with the picture
      argument from Day 34**
- [ ] Can name the case where `Command` is right (atomic update + jump; Day 48's supervisor)
- [ ] `LANE_TARGETS` passed explicitly to `add_conditional_edges` — node names decoupled from labels
- [ ] `.get("triage")`, not `["triage"]` — `total=False` means absent keys
- [ ] **`None` branch first**, fourth framework running
- [ ] Rejoin edges added by iterating `LANE_TARGETS.values()` — Day 31's `or_`, spelled out
- [ ] `two_routers.py` run; the **two ASCII drawings compared side by side**
- [ ] Judgement written in the bake-off notes: which picture would you hand a reviewer?

## LG-04 — fan-out

- [ ] Can say what `Send` does that a for-loop in one node does not (parallel, checkpointed,
      retryable)
- [ ] Can say why Days 30–35 could not express this at all
- [ ] `MAX_BRANCHES` capped, and the slice applied **before** building the `Send` list
- [ ] Can state that fan-out width is a **rate-limit** decision first
- [ ] Each `Send` carries a **private payload**, not whole state
- [ ] Recognised this as the **third and best** answer to Day 43 §4's security question
- [ ] No merge logic written anywhere — the reducer does it
- [ ] `fan_out.py` run; `findings` count compared against branch count
- [ ] Notes observed arriving in **nondeterministic order**, and connected to yesterday's
      commutativity test

## Tests that must be able to fail

- [ ] `test_the_routing_table[5 rows]`
- [ ] `test_an_unclassified_ticket_escalates` — **the fourth identical copy**; noted as evidence
- [ ] `test_every_lane_has_a_target_and_a_budget`
- [ ] `test_the_four_frameworks_agree_on_the_budget` — **flip it:** change one copy, see red
- [ ] `test_the_four_frameworks_agree_on_the_fast_lane`
- [ ] `test_the_router_makes_no_model_call`
- [ ] `test_one_send_per_similar_ticket`
- [ ] `test_fanout_is_capped` — **flip it:** drop the slice, 50 branches fire
- [ ] `test_a_branch_sees_only_its_own_ticket` — **the day's most important test**
- [ ] `test_no_similar_tickets_means_no_branches`
- [ ] `test_the_cap_is_below_the_notes_bound` — a cross-constant invariant
- [ ] All tests cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why does Mandala route on the edge rather than with `Command`?
- [ ] When is `Command` the right choice, and what does "atomic" buy there?
- [ ] Why pass an explicit label→node mapping instead of letting labels be node names?
- [ ] Why is `Send`'s private payload a security mechanism and not just an ergonomic one?
- [ ] Why is fan-out width a budget decision before it is a performance decision?
- [ ] What exactly did yesterday's commutativity test protect you from today?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~11, Groq)
- [ ] **429s-hit column filled** — parallel branches are the likeliest source so far
- [ ] `Command` and `Send` import paths confirmed
- [ ] `Send` attribute names (`.node`, `.arg`) confirmed; tests fixed if they differ
- [ ] `add_conditional_edges` accepting `list[Send]` confirmed
- [ ] Any framework-level concurrency limit found and noted in `RATE_BUDGET.md`
- [ ] **Failing-branch semantics established** (abort the super-step, or survivors still apply?)
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 44
```

- [ ] Bake-off rows updated: **routing locus** (now complete for all four) and **dynamic parallelism**
- [ ] `./m done 44` succeeded — trackers updated automatically
