# Day 49 — CHECKLIST

**IDs covered:** LG-08 🛠️ (durable execution semantics), LG-14 🛠️ (tool-error & retry policy
in-graph), AG-27 🛠️ (durable execution, completed)

## Demo command

```bash
uv run python days/day-49/lab/failure_zoo.py    # 0 requests — the day's key file
uv run pytest tests/test_graph_policy.py -v
```

Expected: a graph that fails, a state snapshot showing exactly what survived, and a `next` list you
can reason about.

## Setup

- [ ] `./m start 49` and `./m scaffold 49` run
- [ ] No new packages
- [ ] Files created (`graph/policy.py`, `tests/test_graph_policy.py`, two lab files)
- [ ] `router.MAX_ATTEMPTS` exported from Day 6's router (needed by a test)

## LG-08 — failure semantics (answer by RUNNING, not reading)

- [ ] **Q1** — a node raises: do siblings' updates in the same super-step survive? **Answer written**
- [ ] **Q2** — is the previous super-step's checkpoint intact? **Answer written**
- [ ] **Q3** — does a hanging node time out? At what level? Parameter name recorded
- [ ] **Q4** — SIGINT mid-super-step: what is written? **Answer written**
- [ ] **Q5** — on resume, does the failed node re-run alone or does the whole super-step? **Answer
      written, and converted into a request-count fact**
- [ ] Q5's answer used to decide **how wide you are willing to fan out**
- [ ] Both `failure_zoo.py` TODOs completed

## Policy

- [ ] `NodePolicy` has `timeout_s`, `max_attempts`, **and `idempotent`**
- [ ] `retries_for()` returns 0 for non-idempotent nodes **regardless of `max_attempts`**
- [ ] `post_reply` in the table **before it exists** (Day 82), marked non-idempotent
- [ ] `await_approval` non-retryable — asking a human twice
- [ ] Pure nodes (`route`, `supervisor`) have **tight** timeouts
- [ ] `FANOUT_TIMEOUT_S < DEFAULT_TIMEOUT_S`, and can say why (Day 44's consequence)
- [ ] `max_attempts` defaults to 1 — **retry is opt-in**
- [ ] Real LangGraph retry/timeout API found, and `NODE_POLICY` **wired into it** — not
      reimplemented by hand

## The three-layer decision (§4.1)

- [ ] `retry_layers.md` written
- [ ] Can say what a **node** retry does that a **call** retry cannot
- [ ] Can say why node bodies own nothing
- [ ] **Multiplication check done with real numbers** (router attempts × graph attempts)
- [ ] Converted to a free-tier percentage, and a number lowered if it was uncomfortable
- [ ] Day 36's `max_retries=0` **kept**, and the reason restated
- [ ] Idempotence rule written down with the interlock explained

## Poison-input quarantine (§4.2)

- [ ] `after_triage` fallback edge written
- [ ] Failure counter kept **in state**, not in a local variable — and can say why
- [ ] Quarantine routes to a human rather than raising
- [ ] Connected back to Day 31's `guard_progress` — a loop bound should *route*, not just raise

## Tests that must be able to fail

- [ ] `test_non_idempotent_nodes_are_never_retried` — **flip it:** drop the interlock, see red
- [ ] `test_a_side_effecting_node_stays_non_idempotent`
- [ ] `test_the_approval_node_is_not_retryable`
- [ ] `test_an_unknown_node_gets_the_safe_default` — fail closed
- [ ] `test_retry_is_opt_in`
- [ ] `test_every_node_has_a_timeout`
- [ ] `test_pure_nodes_time_out_fast`
- [ ] `test_fanout_nodes_time_out_sooner_than_serial_ones`
- [ ] `test_the_worst_case_multiplication_is_bounded` — **the arithmetic, as a test**
- [ ] `test_the_policy_covers_every_node_in_the_graph` — walks the real compiled graph
- [ ] `test_no_node_body_retries_by_hand`
- [ ] All tests cost **0 model requests**

## The one real run

- [ ] A transient failure forced deliberately (a bad model id for one attempt)
- [ ] **Watched a retry actually fire** — a policy never observed is a policy you do not have
- [ ] Requests counted in the trace and checked against §4.1's multiplication

## Understanding check — answer out loud

- [ ] What survives when one branch of a fan-out raises?
- [ ] Does resume re-run the failed node or the whole super-step, and what does that cost?
- [ ] Which layer owns which kind of retry, and why?
- [ ] What is the worst-case request cost of one stuck node in your system?
- [ ] Why must a retry counter live in state?
- [ ] Why is quarantine better than either retrying or crashing?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~8, Groq)
- [ ] Retry API name and `RetryPolicy` fields confirmed — **including which exceptions are retried**
- [ ] Timeout API confirmed (per node? per graph? wall-clock or per-attempt?)
- [ ] Graceful-shutdown behaviour on SIGINT established
- [ ] `DeltaChannel` — automatic or opt-in — answered
- [ ] `MemorySaver` import path confirmed
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 49
```

- [ ] Bake-off rows updated: **failure semantics**, **retry ownership**, **cost of a stuck node**
- [ ] AG-27 marked complete across all four implementations (Days 20, 32, 47/49, 57 ahead)
- [ ] `./m done 49` succeeded — trackers updated automatically
