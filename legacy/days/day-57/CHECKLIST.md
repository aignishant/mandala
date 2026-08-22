# Day 57 — CHECKLIST

**IDs covered:** MCP-08 🛠️ (Tasks extension), MCP-09 🅿️ (MCP Apps), MCP-10 🅿️ (extensions framework
+ EMA) · **AG-27's fourth implementation**

## Demo command

```bash
uv run python days/day-57/lab/task_lifecycle.py      # 0 requests
uv run python days/day-57/lab/capability_probe.py    # 0 requests
uv run pytest tests/test_mcp_tasks.py -v
```

Expected: replica 2 seeing and cancelling a task replica 1 started.

## Setup

- [ ] `./m start 57` and `./m scaffold 57` run
- [ ] No new packages
- [ ] **Established which extensions `mcp==2.0.0` actually implements** — and said so honestly if
      Tasks is modelled rather than used
- [ ] Files created (`tasks.py`, tests, three lab files)
- [ ] `capability_probe.py` written as a **reusable tool**, not a demo (Day 66 needs it)

## MCP-08 — Tasks

- [ ] Can fill the five-row ordinary-call vs. task table
- [ ] **Can explain how a stateless server holds a task record** — the store is external
- [ ] `TaskStore` as a `Protocol`; SQLite for real, in-memory for tests
- [ ] A new connection per operation, and can say why
- [ ] Task ids **unguessable**, and can say why that is the authorisation control
- [ ] `Status` is a `Literal`; `TERMINAL` is a frozenset
- [ ] `request_cancel` sets a **flag** and no-ops on a finished task
- [ ] Cancellation is **cooperative** — nothing is killed, and the worker checks the flag
- [ ] `MAX_RESULT_CHARS` and `TASK_TTL_S` set
- [ ] Tool docstring tells the **model** it gets a handle and must poll
- [ ] Checked whether a proper task-handle response type exists, rather than a string

## The two-replica proof

- [ ] `task_lifecycle.py` run
- [ ] **A second store object saw a task the first created**
- [ ] A cancel requested by replica 2 observed by replica 1
- [ ] **Extended it:** killed the process mid-task and restarted
- [ ] Decided what happens to a task whose worker died (heartbeat / TTL sweep / accept) — **and
      wrote the decision down**

## MCP-09 — Apps (🅿️)

- [ ] Understood what an App is: a tool that ships a sandboxed-iframe UI
- [ ] Connected it to Day 50: the server ships the approval panel
- [ ] Can say why it is a **bigger** surface than Day 56's elicitation
- [ ] Four questions written for `extensions_notes.md`, including the sandbox policy
- [ ] Built nothing — Mandala is a text channel (Part 8)

## MCP-10 — extensions framework + EMA (🅿️)

- [ ] Can say why extensions exist, in governance terms and in engineering terms
- [ ] **Named the cost: discovery** — and answered the §4.3 TODO
- [ ] **Three-layer authorisation table filled** (client allowlist / scopes / EMA)
- [ ] Can say what question each layer answers that the one below cannot
- [ ] Connected EMA to the registry (MCP-12) and to Day 66
- [ ] **Wrote the solo-project EMA policy down** — "I am the allowlist" as one explicit line

## `capability_probe.py`

- [ ] Runs against `ticket-db`, and takes a URL argument
- [ ] Prints every tool's `inputSchema` — third time this habit appears
- [ ] **Prints every server-supplied prompt in full**, and you read them
- [ ] Extension-discovery mechanism found and wired in

## Tests that must be able to fail

- [ ] `test_a_task_starts_working`
- [ ] `test_task_ids_are_unguessable` — **flip it:** use a counter, see red
- [ ] `test_a_second_replica_sees_the_task` — **the headline test**
- [ ] `test_a_second_replica_can_cancel`
- [ ] `test_cancelling_a_finished_task_is_a_no_op`
- [ ] `test_cancellation_is_cooperative_not_a_kill` — **and its limitation noted** (one file only)
- [ ] `test_the_terminal_set_covers_every_non_working_status`
- [ ] `test_results_are_bounded`
- [ ] `test_tasks_have_a_ttl`
- [ ] `test_no_module_level_mutable_state` — Day 54's AST check, reused
- [ ] Considered extracting the AST check to `conftest.py` since it is now used twice
- [ ] `test_the_tool_docstring_tells_the_model_it_gets_a_handle`
- [ ] All tests cost **0 model requests**

## `extensions_notes.md`

- [ ] Extension support table filled (spec / SDK / Mandala)
- [ ] Discovery-without-initialize answered
- [ ] Three-layer table copied in
- [ ] EMA policy written as an explicit sentence
- [ ] Apps questions listed
- [ ] Task-worker-death failure mode and decision recorded

## Understanding check — answer out loud

- [ ] How does a stateless server offer a stateful extension?
- [ ] Why cooperative cancellation rather than a kill?
- [ ] Why must a task id be unguessable?
- [ ] What did the extensions framework make harder, and what did it make possible?
- [ ] Name the three authorisation layers and what each one alone cannot do.
- [ ] Why is an App a bigger surface than an elicitation prompt?

## Budget & freshness

- [ ] Logged in `docs/RATE_BUDGET.md`: **0 requests**
- [ ] Phase-8 running total noted for Day 58's gate write-up
- [ ] Tasks method names confirmed (`tasks/get`, `tasks/cancel`, `tasks/list`?)
- [ ] Task-handle response type — confirmed or absent
- [ ] **Extension discovery mechanism** — confirmed
- [ ] Whether the spec addresses task-id unguessability / polling authorisation — answered
- [ ] Apps iframe sandbox policy — read
- [ ] EMA allowlist location and client discovery — read
- [ ] Extension versioning and mismatch behaviour — answered
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 57
```

- [ ] AG-27's fourth implementation recorded (Days 20, 32, 47/49, **57**)
- [ ] `./m done 57` succeeded — trackers updated automatically
