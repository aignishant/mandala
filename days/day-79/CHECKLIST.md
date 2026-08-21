# Day 79 — CHECKLIST

**IDs covered:** — (capstone assembly: the durable triage spine, per ADR-003)

## Demo command

```bash
uv run pytest tests/test_spine.py -v                       # 0 requests
uv run python days/day-79/lab/run_spine.py T-9001          # prints the graph, then runs
# ctrl-c mid-run, then:
uv run python days/day-79/lab/run_spine.py --resume T-9001-<suffix>
sqlite3 .state/mandala.sqlite ".tables"
```

Expected: the four-node graph drawn **before** invoke; the resume picks up without re-running
`classify`, and costs visibly fewer requests than the original run.

## Setup

- [ ] `./m start 79` and `./m scaffold 79` run
- [ ] `langgraph-checkpoint-sqlite` confirmed pinned (Day 47) — **stop and fix if missing**
- [ ] `.state/` gitignored (fourth time this pattern)
- [ ] ADR-003 re-read; today implements it

## State

- [ ] `body` is `Untrusted` **inside graph state** — not unwrapped for the serialiser
- [ ] If the checkpointer fought the type: serialisation solved, type kept
- [ ] `run_id`, `ticket_id`, `body` all `keep_first` (write-once)
- [ ] `severity` uses `take_max_severity` — fail-safe merge
- [ ] `steps` accumulates the trajectory in state — Day-71 rubrics can grade from a checkpoint
- [ ] `total=False` so nodes return partial updates

## Nodes

- [ ] The ticket body reaches a prompt **only** through `render_as_data()`
- [ ] `grep -rn "\.text" src/mandala/` run — every hit justifiable
- [ ] Classifier system prompt frames injected instructions as **part of the complaint**
- [ ] `route()` makes **no model call** — fourth framework, same rule
- [ ] `route()` **overrides** the model for high/critical — policy beats the model
- [ ] `TriageResult.model_validate_json` at the seam (kills RT-06)
- [ ] Each node appends its own `Step`; nodes know nothing about grading

## The spine

- [ ] All four nodes declared today; unbuilt ones raise `NotImplementedError`
- [ ] `thread_id = ticket.run_id`, with a comment saying why
- [ ] Graph printed **before** invoke
- [ ] `SqliteSaver` used per its **verified** current API
- [ ] No `try/except` swallowing `invoke` failures
- [ ] No nodes added beyond ADR-003 without an amendment

## The kill-and-resume drill (§5.1) — the day's deliverable

- [ ] Run killed mid-node, deliberately
- [ ] Resumed with the same `run_id`
- [ ] **`classify` did not re-run** — verified, not assumed
- [ ] Checkpoint DB inspected by hand (`.tables`, one row read)
- [ ] Resumed with a **wrong** thread id; result understood (fresh run, not an error)
- [ ] Whole drill written up verbatim in `days/day-79/lab/kill_and_resume.md`
- [ ] Request counts recorded for original vs resume

## Tests that must be able to fail

- [ ] `test_routing_makes_no_model_call` — **flip it:** route by model, lose determinism
- [ ] `test_critical_tickets_always_get_research_whatever_the_model_said`
- [ ] `test_the_body_is_write_once`
- [ ] `test_the_body_stays_untrusted_inside_graph_state` — **flip it:** unwrap to `str`, every fence
      downstream becomes optional
- [ ] `test_the_graph_declares_every_capstone_node`
- [ ] `test_unimplemented_nodes_raise_rather_than_return_empty`
- [ ] `test_resume_does_not_rerun_a_completed_node` — written yourself, not skipped
- [ ] `test_thread_id_is_the_run_id_not_the_ticket_id`
- [ ] All cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why would a plain pipeline function work today and fail on Day 82?
- [ ] Why is the thread id the run id rather than the ticket id?
- [ ] What does a stub returning `{}` cost you tomorrow?
- [ ] Why does `route()` override the classifier on critical tickets?
- [ ] After an interrupt, what exactly re-runs — the node or the super-step?
- [ ] What did durability cost you in complexity, and what did it buy in requests?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~12)
- [ ] **Original-vs-resume request counts recorded** — the concrete value of durability
- [ ] `SqliteSaver.from_conn_string` API confirmed on 3.1.1 — **today's biggest risk**
- [ ] Frozen-dataclass serialisation confirmed (or the custom hook found)
- [ ] `print_ascii()` / `draw_ascii()` method name confirmed
- [ ] Conditional-edge return semantics confirmed
- [ ] Post-interrupt resume semantics confirmed — Day 82 depends on this
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 79
```

- [ ] `kill_and_resume.md` committed
- [ ] `git status` clean of `.state/`
- [ ] `./m done 79` succeeded
