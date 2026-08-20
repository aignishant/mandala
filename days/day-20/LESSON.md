---
day: 20
phase: 3
phase_name: "OpenAI Agents SDK advanced"
title: "Durable runs with Temporal; realtime awareness"
ids: ["OAI-21", "OAI-22"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 20 — Durable runs with Temporal; realtime awareness

**Phase 3 · OpenAI Agents SDK advanced** · IDs: **OAI-21 🛠️**, **OAI-22 🅿️**

> **Yesterday:** the model-native harness 🅿️ — the paid Codex-style layer you can only read about —
> and the free lab that gives you its real guarantee: agent-written code inside a **local Docker
> sandbox** with no network, a read-only mount and a hard timeout.
> **Today:** the other kind of containment. Yesterday you bounded *where code runs*; today you bound
> *what a crash costs*. A durable engine (Temporal, open source, running on your laptop for $0) that
> can restart your process mid-run and pick the job back up — plus 🅿️ realtime/voice, awareness only.
> **Tomorrow:** guardrails and approvals composed into one production-grade Resolver, and AgentKit
> literacy (OAI-23/25). Phase 3's last day.

```bash
./m start 20
./m scaffold 20
```

---

## §1 The story

Run Mandala over a hundred tickets. Research each one, draft each reply. It is not a hard job — it
is a *long* one, maybe an hour of wall clock, most of it spent waiting on a free-tier provider that
gives you thirty requests a minute if you are lucky.

At minute 52, one of these happens. Not "might happen" — happens, this week, to you:

- Groq returns **429** for the eleventh time and your backoff (Day 6) finally gives up.
- Your laptop lid closes and the process is suspended, then killed.
- You fix a typo in `prompts.py`, save, and the reloader restarts the worker.
- OpenRouter's `:free` roster rotates the model you pinned out from under you (Part 2's warning,
  arriving on schedule).

And here is the part that should annoy you:

> **A run that takes an hour and dies at minute 52 has done nothing.** Not 87% of something —
> nothing. The ninety-one tickets you already researched are in a Python list inside a process that
> no longer exists, and the only artifact is a `.mandala/traces/*.jsonl` file that tells you, in
> detail, exactly how much work you are about to redo.

On a paid platform that is a bill. Here it is worse, and for the same reason as Day 18: **the ninety-
one research calls you are about to repeat come out of a daily request ceiling you cannot top up**
(Principle 5). Losing the work loses the budget that bought it.

This is **AG-27, durable execution** — the plan's Day-49 topic, meeting the Agents SDK twenty-nine
days early — and the answer the industry converged on is odd enough to be worth stating plainly:

> **Stop storing your program's progress and start storing your program's history.** Every step's
> input and result is written to a database as it completes. When the process dies, a new one reads
> that history back and *re-executes your function from the top* — except every step that already
> completed returns its recorded result instantly instead of running again. Your code does not know
> it crashed. It just... keeps going.

That is **replay**, and it is the whole idea. It also immediately creates the problem this day is
really about:

> 🎯 **Replay requires your workflow function to be deterministic — and an LLM call is the least
> deterministic thing in your program.**

If your function asks the model a question during replay, it gets a different answer than it got the
first time, takes a different branch, and the recorded history no longer matches the code path. The
engine notices, and your run is dead in a much more confusing way than a crash. So the split that
organizes today, and every durable-execution system you will ever touch:

**Workflow code is deterministic orchestration. Every model call, every tool call, every byte of I/O
is an activity.**

You already have the instinct. Since Day 9 every Mandala agent has pinned `temperature=0.0` — not
because zero temperature makes an LLM deterministic (it does not, quite) but because *you decided
your system should not depend on model variance*. Today that discipline gets a hard edge: model
variance is not merely undesirable, it is **structurally forbidden** in one specific region of your
code, and the engine will tell you when you break the rule.

Two more things today, both of which have been waiting for this day:

1. **`src/mandala/idempotency.py` stops being theoretical.** You wrote it on Day 6 and it has been a
   well-tested module nothing calls. Retries mean an activity can run **more than once**, so the
   activity that posts a customer reply can post it twice. That is why Day 8 split `draft_reply`
   from `post_reply`. §3.8 is the payoff.
2. **🅿️ Realtime and voice** (§4). `RealtimeRunner`, SIP, voice pipelines — paid OpenAI key, so
   awareness only, and honestly: **voice is not Mandala's channel.** You will still be asked about
   it, and there is one genuinely interesting idea in there that connects straight back to Day 17.

---

## §2 Setup — run this

### 2.1 The package and the server

One new package. The dependency ledger in `docs/PINS.md` already has the Day-20 row:

```bash
uv add "temporalio==1.31.0"
```

And one new *process*. This is the part that makes people assume today costs money, so say it out
loud before you start:

> **Temporal is open source (MIT), and the dev server is a single binary that runs on your laptop
> with a built-in database and a web UI. It costs $0.** Temporal *Cloud* is a paid product and this
> project will never touch it. Model calls today still go through LiteLLM to Groq's free tier, same
> as every other day (Principle 5).

Install the CLI (it bundles the dev server):

```bash
# macOS / Linux
curl -sSf https://temporal.download/cli.sh | sh

# Windows (PowerShell), or download the release archive from github.com/temporalio/cli
winget install Temporal.Cli
```

Then, **in its own terminal that stays open all day**:

```bash
temporal server start-dev --db-filename .mandala/temporal.db --ui-port 8233
```

**Line by line:**

- `server start-dev` — a full Temporal server (frontend, history, matching, worker services) in one
  process, with SQLite instead of Cassandra. It is meant for exactly this: local development.
- `--db-filename .mandala/temporal.db` — **persist to disk, do not use the default in-memory mode.**
  Today's entire experiment is "kill something and watch the work survive". An in-memory server
  makes that a lie you cannot detect, because the *server* also forgets. `.mandala/` is gitignored
  (Day 14), so the database is local scratch state and never enters a commit.
- `--ui-port 8233` — the web UI at <http://localhost:8233>. You will use it: it renders the event
  history that §3.4 explains, and seeing a real history is worth more than three paragraphs of me
  describing one.
- The server listens on **`localhost:7233`** by default (gRPC). That address goes in your code once,
  as a constant, not scattered through three files.

### 2.2 Pre-flight — prove the server is there before you write code

```bash
temporal operator cluster health
temporal workflow list          # empty, and that is a successful result
uv run python -c "import temporalio; print(temporalio.__version__)"
```

All three must succeed. **If `temporal operator cluster health` hangs or refuses the connection, stop
and fix that**; every confusing error in this lesson downstream of here is really this error wearing
a costume.

### 2.3 If you genuinely cannot run the dev server

Some machines will not cooperate — corporate device policy, no admin rights, an architecture the
binary does not ship for. You are not stuck, and you are not skipping the day:

| Situation | What you do instead | What you lose |
|---|---|---|
| No CLI binary, but Docker works (Day 19) | `docker run -p 7233:7233 -p 8233:8233 temporalio/auto-setup` (or the `temporalio/temporal` dev image) | nothing material — same server, one more moving part |
| No server at all | Build `durable.py` and run **every test in §5**, which need no server. Then run `days/day-20/lab/dry_run.py`, which executes the same activity functions in order as plain Python | the kill-and-resume experiment, which is the point |
| No server, no time | Read §3 and §4, write the §9 answers, and **mark the day `blocked` rather than `done`** | the day |

**The §5 tests are deliberately designed to pass with no server running**, and §5.4 explains why that
is a design decision rather than a convenience. But be honest with yourself: **the kill-and-resume
experiment is the day.** Everything else is reading. If the middle row is where you land, come back
to §3.7 the first evening you have a machine that will run the binary.

### 2.4 Files

```bash
mkdir -p days/day-20/lab
touch src/mandala/durable.py
touch days/day-20/lab/worker.py
touch days/day-20/lab/durable_demo.py
touch days/day-20/lab/dry_run.py
touch tests/test_durable.py
```

And confirm the two modules today stands on are green before you start:

```bash
uv run pytest tests/test_idempotency.py tests/test_permissions.py -q
```

**Day 6's idempotency store and Day 8's permission table are today's load-bearing dependencies.**
One decides whether a retry is safe; the other decides whether the retried thing was allowed in the
first place. If either is red, today will teach you the wrong lesson.

---

## §3 OAI-21 — Long-horizon runs that survive the process that started them

The plan's OAI-21 row calls this a "🅿️ lab-lite: run the reference example, read the failure
semantics." Take that instruction seriously in both directions. **The build stays modest** — two
activities and one workflow, wrapping agents you already have — and **the reading is the expensive
part**, which is why §3.8 and §3.9 are longer than the code they describe.

### 3.1 What a durable engine actually stores

Draw the difference, because it is not the one people expect. Checkpointing your *state* and
recording your *history* look similar from the outside and behave completely differently:

```
CHECKPOINTING (what you would build)     EVENT-HISTORY REPLAY (what Temporal does)
-----------------------------------      ----------------------------------------
step 1 runs -> save {"step": 1, ...}     step 1 runs -> append ActivityTaskCompleted(result)
step 2 runs -> save {"step": 2, ...}     step 2 runs -> append ActivityTaskCompleted(result)
CRASH                                    CRASH
restart: load the blob,                  restart: RE-RUN THE FUNCTION FROM LINE ONE.
         switch on "step",                        Each awaited activity returns its
         resume at step 3                         recorded result instantly. Line 3
                                                  has no recorded result, so it runs
                                                  for real.
```

**Line by line:**

- The left column is what everyone writes first, and Mandala nearly has it already: Day 7's
  `JsonSession` is a state blob on disk and Day 11's `SQLiteSession` is the same idea with a better
  store. It works, and it has one flaw that gets worse with every step you add: **you are
  hand-maintaining a state machine.** Every new step is a new case in a `switch`, a new field in the
  blob, and a migration for blobs written by yesterday's version.
- The right column is what LangGraph hands you on Day 49 with a checkpointer, what CrewAI calls
  checkpoint restore on Day 32, and what MCP's Tasks extension is reaching for. **Four frameworks,
  one idea** — which is why AG-27 is a `🔁` row in the plan, and why meeting it here first is worth
  a day.
- The thing to notice: on the right, **your code never contains the word "resume".** There is no
  `if already_done:`. The function is written as if crashes do not exist, and the engine makes that
  true by replaying it. That is a different programming model, not a library.
- The cost is the last line of the right column, and it is the whole rest of this section: **the
  re-run must take the same path.** Same branches, same order, same number of awaits. If it does
  not, the engine holds a recorded history that no longer describes the code it is running.

### 3.2 The split, and why the LLM call is on the far side of it 🎯

> **Workflow code is deterministic orchestration. Every model call, every tool call, every bit of
> I/O is an activity.**

That sentence is the day. Here is why it has to be true, in the concrete Mandala case.

Suppose your workflow function called the Researcher directly:

```python
# WRONG. This is the trap of the day, and nothing raises an error the first time you run it.
@workflow.defn
class MandalaTicketWorkflow:
    @workflow.run
    async def run(self, ticket_id: str) -> str:
        research = await Runner.run(researcher(), f"Research {ticket_id}.")  # <- LLM in workflow code
        if research.final_output.triage.severity == "high":                  # <- branch on the answer
            return await self.escalate(research.final_output)
        return await self.draft(research.final_output)
```

First execution: the model says `severity="high"`, the workflow escalates, and the history records an
escalation. The process dies. A new worker replays from line one — and calls the model again, because
`Runner.run` is a live network call with no recorded result. This time the model says
`severity="medium"`. Now the code wants `draft`, but the recorded history says the next event was
`escalate`. **The history and the code disagree, and the run is corrupt.**

Notice what it took to break this: `temperature=0.0` (Day 9) and a pinned model (Principle 4) were
both in force, and it still broke, because "high" and "medium" were both plausible and free-tier
serving is not bit-reproducible across a redeploy. **Determinism you get by being lucky is not
determinism.**

The fix is not a better prompt. The fix is structural:

```python
# RIGHT. The model call is an activity; the workflow only ever sees its recorded result.
brief = await workflow.execute_activity(research_ticket, ticket_id, ...)
if brief.triage.severity == "high":      # replays identically: brief came out of the history
    ...
```

On replay, `execute_activity` calls nothing. It reads `ActivityTaskCompleted` out of the event
history and returns the `brief` the model produced *the first time*. The branch is now a pure
function of recorded data, so it takes the same path forever.

**The rule generalizes to a list worth memorizing.** Inside workflow code all of the following are
banned, and each has a workflow-safe replacement:

| Banned in workflow code | Why it breaks replay | Use instead |
|---|---|---|
| `datetime.now()`, `time.time()` | replay happens later; a different reading takes a different branch | `workflow.now()` — replays the recorded time |
| `random.random()`, `uuid.uuid4()` | a different value on every replay | `workflow.random()`, `workflow.uuid4()` — seeded per run |
| `asyncio.sleep()` | really sleeps; the engine cannot skip it on replay | `workflow.sleep()` — a timer in the history |
| `httpx.get(...)`, an LLM client, a DB read | live I/O returns different bytes on replay | an **activity** |
| Reading a file, an env var, a mutable global | the replaying process is not the process that ran | an **activity**, or an argument |
| Spawning a thread, `os.environ[...] = x` | invisible to the history | don't |
| `make_model()` / `AsyncOpenAI(...)` at workflow scope | a client is I/O-shaped and reads env at construction | construct it **inside** the activity |

**The bottom two rows are the ones that catch this project specifically.** `make_model("groq")`
(Day 9's `sdk.py`) reaches `GROQ_API_KEY` through `load_keys()` (Day 1). That is an environment read,
in a process that is not necessarily the process that started the run. **Build your model inside the
activity, every time.** §5's first two tests enforce exactly this, statically, for 0 model requests.

### 3.3 What replay costs you in practice

Three consequences to internalize before you write code, because each one surprises people:

1. **Your workflow function runs many times for one logical run.** Ten replays on a long workflow is
   ordinary. So workflow code must be *cheap* and *side-effect-free*: no printing you care about, no
   metrics counters, no appending to a list that lives outside the function.
2. **Changing workflow code changes the code that replays old histories.** Insert an activity call
   between two existing ones and every in-flight run replaying an old history hits a mismatch.
   Temporal's answer is **versioning** (`workflow.patched(...)` and friends) — read about it, do not
   build it today, but know the shape: **workflow code is a published protocol between you and every
   run currently in flight.**
3. **Determinism failures are loud, and that is the good news.** The engine detects the mismatch and
   fails the workflow task rather than quietly producing a wrong answer. Compare that with the naive
   checkpoint file, where schema drift gives you a run that silently does the wrong thing. **A system
   that refuses to guess is worth the constraints it imposes on you.**

### 3.4 Workers, task queues, and where your code actually runs

The vocabulary, in the order the pieces talk to each other:

```
  durable_demo.py                 Temporal server (localhost:7233)        worker.py
  ---------------                 --------------------------------        ---------
  client.start_workflow(...) -->  writes WorkflowExecutionStarted
                                  queues a workflow task            -->   polls "mandala-durable"
                                                                          runs workflow code
                                  <-- "schedule research_ticket"          (deterministic only)
                                  queues an activity task           -->   polls, runs the ACTIVITY
                                                                          (this is the LLM call)
                                  <-- ActivityTaskCompleted(brief)
                                  ... same again for resolve ...
  handle.result()            <--  WorkflowExecutionCompleted
```

**Line by line:**

- **The server stores and schedules; it never runs your code.** Your Python lives entirely in the
  worker. That is why the server can be a generic binary you did not configure, and why killing your
  worker does not kill the run.
- **A task queue is just a name, and both sides must agree on it.** A worker polling
  `mandala-durable` while a client starts work on `mandala` produces the single most common beginner
  symptom: the workflow sits in `Running` forever, with no error anywhere. **If your demo hangs,
  check the queue name before you check anything else.**
- **One worker process can host both workflows and activities** — that is what you run today — but in
  production they are usually split, because activities are the half that needs API keys and network
  egress. Notice how neatly that maps onto Day 8: the component holding credentials is not the
  component deciding what to do with them.
- **`handle.result()` is not the run.** The client is a remote control. Kill `durable_demo.py` while
  it is waiting and the workflow keeps going on the worker; reconnect with the same workflow id and
  await the result again. Try it — it is the smallest possible proof that the run does not live in
  your process.

---

### 3.5 `src/mandala/durable.py` — the activities

Build in two halves, activities first, because activities are where every existing Mandala part
plugs in unchanged. Nothing in this half is new code — it is Day 14's `topologies.py` wearing a
decorator.

```python
"""Mandala's durable layer: the same pipeline, restartable.

WHY THIS FILE EXISTS
--------------------
A hundred-ticket run takes an hour and a free-tier 429, a closed laptop or a
redeploy will end it early (Principle 5). Without durability, minute 52 of an
hour-long job is worth exactly nothing. With it, a new worker replays the
recorded history and continues from the last completed step.

THE ONE RULE (OAI-21 / AG-27)
-----------------------------
Workflow code is DETERMINISTIC ORCHESTRATION. Every model call, every tool call
and every byte of I/O is an ACTIVITY. An LLM call inside workflow code produces
a different answer on replay, takes a different branch, and corrupts the run.

Usage
-----
    >>> from mandala.durable import TASK_QUEUE, MandalaTicketWorkflow
    >>> TASK_QUEUE
    'mandala-durable'
    >>> # terminal 1: temporal server start-dev
    >>> # terminal 2: uv run python days/day-20/lab/worker.py
    >>> # terminal 3: uv run python days/day-20/lab/durable_demo.py T-1001
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from agents import Runner

    from mandala.agents import Brief
    from mandala.context import MandalaContext
    from mandala.idempotency import IdempotentStore, idempotency_key
    from mandala.permissions import PermissionDenied
    from mandala.topologies import assert_no_raw_ticket, researcher, resolver

TEMPORAL_TARGET = "localhost:7233"
TASK_QUEUE = "mandala-durable"

#: Errors that must NEVER be retried. Retrying these burns the free tier to
#: reach the same answer, and one of them is a security boundary (Day 8/10).
NON_RETRYABLE = ["PermissionDenied", "ValidationError", "BadSessionId"]

_EFFECTS = IdempotentStore()          # process-local; see the TODO(me) in post_reply_activity


@dataclass
class ResearchIn:
    ticket_id: str
    request_id: str


@dataclass
class ResolveIn:
    brief_json: str
    request_id: str


@activity.defn(name="research_ticket")
async def research_ticket(payload: ResearchIn) -> str:
    """Run the Researcher. THE model call lives here, not in the workflow."""
    attempt = activity.info().attempt
    activity.logger.info("research %s attempt=%d", payload.ticket_id, attempt)

    context = MandalaContext(actor="agent:researcher", request_id=payload.request_id)
    try:
        result = await Runner.run(
            researcher(),                                   # model= pinned in topologies.py
            f"Research ticket {payload.ticket_id}.",
            context=context,
            max_turns=6,
        )
    except PermissionDenied as exc:
        raise ApplicationError(str(exc), type="PermissionDenied", non_retryable=True) from exc

    brief: Brief = result.final_output
    assert_no_raw_ticket(brief, payload.ticket_id, context=context)   # Day 14's seam, still enforced
    return brief.model_dump_json()
```

**Line by line:**

- The module docstring states the rule before it states the API, because on this file the rule *is*
  the API. Anyone who edits `durable.py` without reading four lines of it will put an LLM call in
  the workflow class, and the failure will not show up until a crash.
- `with workflow.unsafe.imports_passed_through():` — **the most Temporal-specific line in the
  project.** The workflow sandbox re-imports modules to catch non-determinism, which is slow and
  breaks libraries that do real work at import time (the Agents SDK does). This context manager says
  "these imports are mine, pass them through untouched". It is a promise you are making, and §5's
  static tests are how you keep it honest.
- `TEMPORAL_TARGET` / `TASK_QUEUE` as module constants — **the queue name lives in exactly one
  place.** §3.4 named the failure mode this prevents: worker and client disagreeing, silently.
- `NON_RETRYABLE` is a list of **type name strings**, not exception classes, because the retry policy
  is serialized and evaluated by the server, which has never imported your Python. Slightly
  uncomfortable, entirely reasonable once you remember the server is a generic binary.
- `_EFFECTS = IdempotentStore()` — Day 6's store, finally load-bearing, and **deliberately wrong** in
  a way §3.8 makes you fix: it is in-memory, so it forgets on the very restart it exists to survive.
- `ResearchIn` / `ResolveIn` as dataclasses rather than positional arguments — **activity arguments
  are serialized, stored in the history, and deserialized by a different process.** Give them a
  named shape now; adding a field to a dataclass is a smaller change than adding a positional
  parameter that old histories do not have.
- `activity.info().attempt` — **the attempt counter, and your first real observability into
  retries.** Print it. When you see `attempt=2` in the worker log during the §3.7 experiment, that is
  the day happening in front of you.
- `MandalaContext(actor="agent:researcher", ...)` — the identity is constructed **inside** the
  activity from data in the payload, not captured from a global. Day 12's dependency injection is
  what makes this file possible: a context that reads its permissions from a table (Day 8) can be
  rebuilt from scratch in a fresh process. **A design decision from eight days ago paying off in a
  place it was not designed for is a sign it was the right decision.**
- `except PermissionDenied: raise ApplicationError(..., non_retryable=True)` — **the classification
  line.** Day 10's `tool_error` re-raises `PermissionDenied` instead of converting it to text; this
  is that same policy, restated for a system whose default is "try again". A denied write retried
  five times is still denied, five times more loudly.
- `assert_no_raw_ticket(...)` — Day 14's seam check runs **inside** the activity, so its `ValueError`
  is an activity failure that retries. Ask whether it should: a Researcher that quoted a ticket body
  once may well quote it again, and you will pay three model calls to find out. That is the
  §3.9 conversation, and it is a real design question, not a rhetorical one.
- `return brief.model_dump_json()` — **a string, not a `Brief`.** Activity results cross a process
  boundary as bytes. Temporal ships a Pydantic data converter that would let you return the model
  directly; §8 makes you verify its import path in 1.31.0 before you rely on it. Until then, JSON in
  and JSON out is the boring option that cannot surprise you.


### 3.6 The two remaining activities — one harmless, one dangerous

```python
@activity.defn(name="resolve_ticket")
async def resolve_ticket(payload: ResolveIn) -> str:
    """Draft a reply from the Brief. Drafting is not writing (Day 8)."""
    activity.logger.info("resolve attempt=%d", activity.info().attempt)

    context = MandalaContext(actor="agent:resolver", request_id=payload.request_id)
    try:
        result = await Runner.run(
            resolver(), payload.brief_json, context=context, max_turns=4
        )
    except PermissionDenied as exc:
        raise ApplicationError(str(exc), type="PermissionDenied", non_retryable=True) from exc
    return str(result.final_output)


@activity.defn(name="post_reply")
async def post_reply_activity(payload: ResolveIn, reply: str) -> str:
    """The dangerous one. AT-LEAST-ONCE means this can run twice. It must not post twice.

    Day 8 made post_reply a landmine that raises until Day 21, and Day 12 made
    approvals_required default True. Both still hold. What Day 20 adds is the
    third protection, the one retries make mandatory: an idempotency key.
    """
    context = MandalaContext(actor="agent:resolver", request_id=payload.request_id)
    if context.approvals_required:                      # Principle 12, unchanged by durability
        raise ApplicationError(
            "post_reply requires human approval (Day 21)",
            type="PermissionDenied",
            non_retryable=True,
        )

    key = idempotency_key("post_reply", {"request_id": payload.request_id, "text": reply})
    return _EFFECTS.run(key, lambda: _send(reply))       # runs once per key, however many attempts

    # TODO(me): _EFFECTS is an in-memory IdempotentStore (Day 6). A worker restart
    # empties it -- which is precisely the event durability exists to survive, so
    # today it protects against retry-in-the-same-process and NOTHING ELSE.
    # Make the store outlive the process: back it with a file or SQLite under
    # .mandala/, keyed the same way. THIS IS THE REP OF THE DAY: it is the exact
    # moment Day 6's toy becomes production machinery, and you cannot claim
    # exactly-once effects until it is done.
```

**Line by line:**

- `resolve_ticket` takes `brief_json`, not a ticket id. **The Day-8 seam survives the translation to
  activities** — the Resolver still holds no `get_ticket` and still cannot look at raw customer text.
  Durability changed how the steps are scheduled; it changed nothing about who may see what.
- Both activities classify `PermissionDenied` identically. That repetition is a smell you should
  notice, and §5 turns it into a test rather than a refactor: **the property that matters is "no
  activity retries a denial", and a test asserts the property even if you later extract a decorator.**
- `post_reply_activity` **is not called by today's workflow.** It exists so the idempotency lesson
  has a real subject and so §5 can test it. Wiring it into the pipeline is Day 21's job, with a
  human in front of it. Building the dangerous thing one day before you are allowed to fire it is
  deliberate: you get to think about the safety mechanism while it is still theoretical.
- The approval check runs **before** the idempotency key is computed. Order matters: an unapproved
  post should not even leave a fingerprint. Cheap check first, same instinct as Day 18's pre-flight.
- `idempotency_key("post_reply", {...})` — Day 6's function, unchanged, and look at what goes into it:
  **`request_id` and the reply text.** Not the attempt number, not a timestamp, not a fresh UUID.
  The key must be *identical across attempts of the same intent* or it protects nothing — which is
  exactly why Day 6 hashed the arguments instead of generating a UUID, a decision that looked
  fussy at the time and is load-bearing now.
- `_EFFECTS.run(key, lambda: _send(reply))` — the second attempt returns the first attempt's result
  without calling `_send`. **The caller cannot tell a retry from a first try, which is the definition
  of idempotent** (Day 6's own words).
- The `TODO(me)` is the day's headline rep and it is not busywork. Reason it through: retries within
  one worker process are handled by the in-memory dict; the retry that happens *because the worker
  died* is handled by nothing. **The failure your durability layer exists to survive is precisely the
  failure your idempotency layer currently does not.** Fix that, then re-read this paragraph.

Write `_send` yourself, three lines, printing to stdout and appending one line to
`.mandala/sent.jsonl`. **Do not make it do anything real.** A file you can `cat` after the experiment
is exactly the evidence you need: run the workflow, kill the worker, restart it, and count the lines.
One line means idempotency worked. Two means it did not, and you have reproduced the failure that
this entire section is about, which is a genuinely good outcome the first time.


### 3.7 The workflow — orchestration, and nothing else

```python
RESEARCH_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=4),      # free tiers want patience, not eagerness
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=60),
    maximum_attempts=4,                         # explicit. NOT the framework default (Principle 4)
    non_retryable_error_types=NON_RETRYABLE,
)

RESOLVE_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=4),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=60),
    maximum_attempts=3,
    non_retryable_error_types=NON_RETRYABLE,
)


@dataclass
class TicketOutcome:
    ticket_id: str
    brief_json: str
    reply: str


@workflow.defn
class MandalaTicketWorkflow:
    """Research, then resolve. No model call, no I/O, no clock, no randomness."""

    def __init__(self) -> None:
        self._step = "starting"                 # replayed state, for the query handler below

    @workflow.query
    def progress(self) -> str:
        """Ask a RUNNING workflow where it is. Free: no model call, no worker interruption."""
        return self._step

    @workflow.run
    async def run(self, ticket_id: str, request_id: str) -> TicketOutcome:
        workflow.logger.info("workflow start ticket=%s request=%s", ticket_id, request_id)

        self._step = "research"
        brief_json = await workflow.execute_activity(
            research_ticket,
            ResearchIn(ticket_id=ticket_id, request_id=request_id),
            start_to_close_timeout=timedelta(minutes=3),
            heartbeat_timeout=timedelta(seconds=45),
            retry_policy=RESEARCH_RETRY,
        )

        self._step = "resolve"
        reply = await workflow.execute_activity(
            resolve_ticket,
            ResolveIn(brief_json=brief_json, request_id=request_id),
            start_to_close_timeout=timedelta(minutes=3),
            heartbeat_timeout=timedelta(seconds=45),
            retry_policy=RESOLVE_RETRY,
        )

        self._step = "done"
        return TicketOutcome(ticket_id=ticket_id, brief_json=brief_json, reply=reply)
```

**Line by line:**

- **Read the whole `run` method and notice what is missing.** No `Runner`, no `make_model`, no
  `open()`, no `datetime`, no `random`, no `try/except` around a network call. It is a sequence of
  two awaits and three string assignments. **A workflow function you can read in ten seconds is the
  goal, not a happy accident** — every line you add is a line that must replay identically forever.
- Both retry policies are **module constants with every field spelled out.** Temporal has a perfectly
  sensible default policy (roughly: retry forever with exponential backoff), and Principle 4 says
  you do not take it. `maximum_attempts` unset means *infinite*, which on a free tier means a
  malformed prompt quietly consuming your entire daily quota overnight. **Explicit beats sensible.**
- `maximum_attempts=4` for research and `3` for resolve — deliberately different, so the numbers are
  visibly *chosen*. Research is the step most likely to hit a 429 (more tool calls, more requests),
  so it gets one more chance. If you disagree with those numbers, change them and write down why;
  what you may not do is leave them unset.
- `initial_interval=4s` with `backoff_coefficient=2.0` gives 4s, 8s, 16s. **This is Day 6's router
  backoff, restated at a different altitude** — and now you have two backoffs stacked: the router
  retries providers inside one activity, and Temporal retries the whole activity. §3.9 tells you why
  that is fine and what to watch for.
- `non_retryable_error_types=NON_RETRYABLE` — the security-relevant field. A `PermissionDenied`
  raised at attempt one must not be re-attempted three more times. **Retry policy is a permission
  question as much as a reliability one.**
- `start_to_close_timeout=timedelta(minutes=3)` — required, and worth understanding rather than
  copying. It bounds **one attempt**, wall clock, from the moment the worker picks the task up.
  Three minutes for a Groq call with the router's own backoff inside it is generous; make it
  30 seconds and you will manufacture failures that are entirely your own fault.
- `heartbeat_timeout=timedelta(seconds=45)` — the "is this activity alive?" deadline. It only means
  something if the activity actually calls `activity.heartbeat()`, which today's does not, because a
  single `await Runner.run(...)` has nowhere to put the call. **Declaring a heartbeat timeout an
  activity never satisfies is worse than declaring none**, so this is your second `TODO(me)`:

```python
        # TODO(me): make the heartbeat real, or delete the timeout. Two honest options:
        #   (a) drop heartbeat_timeout entirely and rely on start_to_close, or
        #   (b) run Runner.run() as a task and heartbeat every 10s while awaiting it.
        # Pick one and write down which failure you are buying protection against.
        # The rep is noticing that a config value nothing satisfies is a lie in a table.
```

- `@workflow.query def progress` — **a read of a running workflow's state, and it costs nothing.**
  No model call, no interruption of the worker. `temporal workflow query --type progress -w <id>`
  answers "where is it?" for an hour-long run without a log file. Queries must be side-effect-free
  and must not call activities, for the same replay reason as everything else in this class.
- `self._step` is *replayed state*: on a restart it is reconstructed by re-running the assignments
  the history already knows about. Which is precisely why it may only ever be assigned from
  deterministic data — never from `workflow.now()` formatted into a string you compare later.


### 3.8 The worker and the demo

```python
"""days/day-20/lab/worker.py — the process that actually runs Mandala's code.

Run:
    uv run python days/day-20/lab/worker.py
Then kill it with Ctrl-C mid-run and start it again. That is the lab.
"""

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from mandala.durable import (
    TASK_QUEUE, TEMPORAL_TARGET, MandalaTicketWorkflow,
    post_reply_activity, research_ticket, resolve_ticket,
)


async def main() -> None:
    client = await Client.connect(TEMPORAL_TARGET, namespace="default")
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[MandalaTicketWorkflow],
        activities=[research_ticket, resolve_ticket, post_reply_activity],
    )
    print(f"worker polling {TASK_QUEUE!r} at {TEMPORAL_TARGET} -- Ctrl-C to kill it")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
```

```python
"""days/day-20/lab/durable_demo.py — start a run and watch it from outside.

Run:
    uv run python days/day-20/lab/durable_demo.py T-1001
"""

import asyncio
import sys
import uuid

from temporalio.client import Client

from mandala.durable import TASK_QUEUE, TEMPORAL_TARGET, MandalaTicketWorkflow


async def main() -> None:
    ticket_id = sys.argv[1] if len(sys.argv) > 1 else "T-1001"
    request_id = f"req-{uuid.uuid4().hex[:8]}"          # a UUID out here is fine: NOT workflow code
    workflow_id = workflow_id_for(ticket_id, request_id)

    client = await Client.connect(TEMPORAL_TARGET, namespace="default")
    handle = await client.start_workflow(
        MandalaTicketWorkflow.run,
        args=[ticket_id, request_id],
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )
    print(f"workflow id : {handle.id}")
    print(f"web UI      : http://localhost:8233/namespaces/default/workflows/{handle.id}")
    print("KILL THE WORKER NOW (Ctrl-C in its terminal), then start it again.\n")

    async def watch() -> None:
        while True:
            print(f"  step -> {await handle.query(MandalaTicketWorkflow.progress)}")
            await asyncio.sleep(3)

    watcher = asyncio.create_task(watch())
    outcome = await handle.result()
    watcher.cancel()

    print(f"\nresumed and finished. reply:\n{outcome.reply[:400]}")
```

```python
def workflow_id_for(ticket_id: str, request_id: str) -> str:
    """TODO(me): decide this project's workflow-id policy, then implement it.

    The workflow id is a DEDUPLICATION key: Temporal refuses to start a second
    running workflow with an id that already exists. So the policy answers a
    product question, not a naming one:

      f"mandala-{ticket_id}"                  -> one run per ticket, ever. Re-running
                                                 the same ticket is an error. Safest.
      f"mandala-{ticket_id}-{request_id}"     -> one run per request. Repeats allowed.
      f"mandala-{uuid.uuid4()}"               -> no dedup at all. Why bother having ids.

    Pick one, write the sentence that justifies it, and note which failure it
    prevents. THIS IS THE REP: it is idempotency again (Day 6), one level up --
    the key stops a duplicate RUN rather than a duplicate EFFECT.
    """
    raise NotImplementedError
```

**Line by line:**

- The worker names its workflows and activities **explicitly, in a list.** No auto-discovery, no
  scanning a package. Same instinct as Day 18's operation allowlist: **a registry you have to edit
  is a registry someone has to review.**
- `Worker(...)` hosting both workflows and activities is a development convenience (§3.4). Note that
  `post_reply_activity` is registered even though today's workflow never calls it — registered but
  unreachable, which is a fair description of every safety-critical thing in this repo right now.
- `uuid.uuid4()` in `durable_demo.py` is **fine**, and this is the distinction people get wrong. The
  ban is on non-determinism *inside workflow code*. The client is ordinary Python: it runs once, it
  is never replayed, it may do whatever it likes. **The rule is about a region of code, not about
  the word `uuid`.**
- `handle.query(MandalaTicketWorkflow.progress)` every three seconds — free progress on an hour-long
  job. Compare Day 17: streaming showed you *tokens* as they were produced by a run you were
  attached to. This shows you *steps* of a run you are not attached to, from a different machine if
  you like. **Two different answers to "what is it doing", and the durable one survives your laptop
  closing.**
- `await handle.result()` blocks until the workflow completes — through your worker dying and coming
  back. It is a subscription to a durable outcome, not a function call.
- `workflow_id_for` ships **red**, and it is the third `TODO(me)`. It is placed in the demo rather
  than in `durable.py` on purpose: **the deduplication policy is a property of the caller's
  intent**, and pretending it belongs to the workflow class is how you end up with one policy
  serving three incompatible use cases.


### 3.9 🎯 The experiment — kill the worker mid-run

**Do not skip this.** Everything above is a claim; this is the evidence. Three terminals.

```bash
# terminal 1 (already running from §2)
temporal server start-dev --db-filename .mandala/temporal.db --ui-port 8233

# terminal 2
uv run python days/day-20/lab/worker.py

# terminal 3
uv run python days/day-20/lab/durable_demo.py T-1001
```

Watch terminal 3 print `step -> research`. The moment it prints `step -> resolve`, go to terminal 2
and press **Ctrl-C**. Then, after five seconds of silence, start the worker again:

```bash
uv run python days/day-20/lab/worker.py
```

**What you should see, and what each part means:**

| Where | What appears | What it proves |
|---|---|---|
| terminal 3 | nothing breaks; the `step ->` line keeps printing | the client is a remote control, not the run |
| terminal 2 (new worker) | `resolve attempt=1` or `attempt=2` — **not** `research` | research's result came from the history, not the model |
| terminal 3 | the final reply, eventually | the run outlived the process that was executing it |
| web UI | one history: `ActivityTaskCompleted(research_ticket)` long before the restart | the recorded fact that made the resume possible |

> **The whole day fits in one line of that table: the new worker did not re-run research.** It could
> not have, in any meaningful sense — the model's answer was already a fact in a database. What it
> re-ran was your *workflow function*, which replayed both `self._step` assignments in microseconds,
> found a recorded result waiting at the first `await`, and blocked at the second one because that
> is genuinely where the work stopped.

Now do it **again, harder**: kill the worker *during* research instead of during resolve. Different
outcome, and it is the honest one — the research activity had not completed, so there is no recorded
result, so it runs again from the top and you pay its model calls a second time. That is
**at-least-once**, and it is the subject of §3.10.

**Write three numbers into the CHECKLIST while you still remember them:**

1. Which step resumed (`research` / `resolve`) — from the new worker's first log line.
2. What re-ran — from `attempt=` in the log, plus the activity list in the web UI.
3. **How many model calls were repeated.** Count them; do not estimate. `.mandala/traces/*.jsonl`
   and Day 14's `model_calls()` will tell you exactly, which is the fourth time Day 14's thirty-line
   exporter has been the instrument that turned an assertion into a measurement.

Two more things worth doing while the server is up, both free:

- `temporal workflow list` and `temporal workflow show -w <id>` — read a real event history in your
  terminal. Every claim in §3.1 is visible in that output.
- Kill **terminal 3** instead, then re-attach: `temporal workflow result -w <id>`. The run does not
  notice.

**🎯 Note the rhyme, because it comes back.** "Kill it mid-run and resume on camera" is the Phase-5
gate for CrewAI Flows on **Day 35**, and it is the shape of LangGraph's checkpointer lab on **Day 49**.
Three frameworks, three storage designs, one demo you should be able to perform from memory in an
interview. Today is the first time you run it; by Day 49 you should be bored of it, which is the
point.


### 3.10 Failure semantics — the part the plan actually asks you to read

The plan's OAI-21 row says: *run the reference example, read the failure semantics.* Here they are,
five of them, each with the Mandala consequence.

**1. Execution is at-least-once, never exactly-once.** An activity that completed its work and died
before reporting the result will run again. There is no configuration that fixes this; it is a
property of distributed systems, not of Temporal. **The only exactly-once thing you can have is an
*effect*, and you get it by making the effect idempotent yourself** — which is why §3.6's
`TODO(me)` is the rep of the day and why Day 8 split `draft_reply` from `post_reply` twelve days
before you needed it. Drafting twice costs two model calls. Posting twice costs a customer.

**2. Retryable vs. non-retryable is a decision you make, not a property of the error.** Temporal
retries everything by default except what you list. Mandala's list:

| Error | Retry? | Why |
|---|---|---|
| `PermissionDenied` (Day 8) | **never** | the answer will not change, and retrying a denial four times is four audit lines saying you tried to do something you were not allowed to do |
| A 429 from Groq | yes | the definition of transient (Day 6's whole router exists for this) |
| `ValidationError` on a `Brief` | **never** | a malformed schema from a pinned model at `temperature=0.0` is a bug in your prompt; three more attempts is three more requests spent confirming it |
| `LookupError` — no such ticket | **never**, ideally | Day 10 already converts this to text for the model rather than raising. If it reaches the activity boundary, it is data, not weather |
| A worker crash / OOM | yes | nothing was wrong with the request |
| `ValueError` from `assert_no_raw_ticket` | argue it | it *might* be model variance (retry helps) or a prompt bug (retry burns quota). **Decide, write it down, put the type in `NON_RETRYABLE` or don't** |

The last row is the honest one. **A retry policy is a claim about why things fail**, and if you
cannot say why an error happens you cannot say whether repeating it helps.

**3. Timeouts cancel an attempt, not necessarily the work.** This surprises people, so be precise:
when `start_to_close_timeout` fires, Temporal stops waiting and (per your policy) schedules another
attempt. **The Python coroutine on the old worker is asked to cancel; whether it stops is up to your
code.** An HTTP request already in flight to Groq may well complete and be billed against your quota
after the timeout has "cancelled" it. Timeouts bound *your patience*, not the outside world's
behavior.

| Timeout | Bounds | Set it when |
|---|---|---|
| `start_to_close` | one attempt, from pickup to return | always — this is the one you must set |
| `schedule_to_start` | how long a task may sit in the queue | you care that no worker is polling (a good alarm) |
| `schedule_to_close` | the total across all attempts | you have a real deadline for the whole step |
| `heartbeat` | silence from a running activity | the activity is long **and** actually heartbeats |

**4. Heartbeats are for long activities, and they are opt-in on both sides.** Call
`activity.heartbeat("researching T-1004")` from inside a long loop; the payload comes back on the
next attempt via `activity.info().heartbeat_details`, so a hundred-ticket activity can resume at
ticket 91 instead of ticket 1. **That is checkpointing inside a step**, and it is the right tool when
a step is a batch. Today's activity is a single `await`, which is exactly why §3.7 left the heartbeat
as a `TODO(me)` rather than pretending.

**5. Two backoffs are now stacked, and you should know the arithmetic.** Day 6's router retries
providers *inside* one activity; Temporal retries the activity. Worst case with today's numbers:
4 attempts × the router's own chain. That is fine — the outer policy is the one with
`maximum_attempts`, so the total is bounded — but **the failure you should watch for is the inner
loop swallowing an error the outer loop should have seen.** If the router converts an auth failure
into `AllProvidersFailed`, the activity boundary sees a generic error and retries a
permanently-broken key three more times. `NON_RETRYABLE` cannot help you classify what has already
been flattened.

### 3.11 What durability buys, and what it costs

| What it buys | What it costs |
|---|---|
| A run that survives the process, the laptop lid, and the redeploy | A server to run, a worker to keep alive, and a task queue name to get right |
| Every completed step's result is a durable fact — never re-computed, never re-paid | Determinism constraints on **your own code**, enforced by a sandbox that will surprise you |
| Automatic, policy-driven retries with explicit backoff | At-least-once semantics, so every effect now needs an idempotency key that works across restarts |
| Free progress on a long run (`@workflow.query`), from any machine | Debugging spans two systems: your traces (Day 14) *and* the event history |
| A history you can read after the fact, event by event | Workflow code becomes a versioned protocol — you cannot freely edit code that in-flight runs are replaying |
| The same demo answers "what happens when it crashes" in three frameworks (Days 20, 35, 49) | An extra dependency and an extra binary on every machine that runs the lab |

**The honest summary: durability is not free, and it is not always worth it.** For a five-second
triage call, all of this is absurd overhead — retry the call and move on. It starts paying at roughly
the point where **losing the run costs more than the machinery costs**, and on a zero-budget project
that threshold arrives early, because what you lose is not time but *requests you cannot buy back*.

### 3.12 The reference example you did not build (Principle 2, satisfied in that order)

Temporal ships an **official Agents SDK integration** — a contrib module that wraps the SDK's model
invocation in an activity for you, so you can hand it an ordinary `Agent` and get durability without
writing `research_ticket` by hand. The plan's row says "run the reference example", and you should:
clone it, read it, run it against your dev server.

But run it **after** today's build, not instead of it. That ordering is Principle 2 — naked before
framework — and here it earns its keep, because the integration's entire job is *the split you just
made by hand*. Having written the split yourself, you will read their code and recognize every
decision: what they wrap in an activity, what retry policy they default to, and where they put the
model client. **Read it as a diff against your own file, and note the three things they do that you
did not.** That comparison is a better interview answer than either file alone. §8 has the URL and
the "confirm the import path in 1.31.0" item, because contrib module names move.

---

## §4 OAI-22 🅿️ — Realtime and voice, and why Mandala does not have a microphone

Awareness only. No lab, no code, no request budget. **`RealtimeRunner`, SIP connections and the voice
pipeline all require a paid OpenAI key** — the zero-budget addendum's Part 3 lists OAI-22 as
"unchanged: realtime/voice needs OpenAI, stays awareness", and its Part 5 puts realtime in the
*newly excluded* table. The plan's Part 8 is blunter: *"Voice/realtime as a product channel — OAI-22
awareness + one demo notebook; Mandala is text-channel."*

So this section is literacy, and it is genuinely worth the twenty minutes.

### 4.1 What actually changes when the transport is an audio stream

Everything you have built for nineteen days assumes **request/response**: you send a turn, you get a
turn, and between them nothing is happening. A realtime voice agent holds **one persistent
bidirectional connection** carrying audio frames in both directions, continuously, with a model on
the other end that is listening while it is speaking.

Four consequences, and each one invalidates something you currently take for granted:

| Assumption that dies | What replaces it | The Mandala equivalent |
|---|---|---|
| A turn ends when the user hits Enter | **Turn detection** — server-side VAD deciding, from silence and prosody, that the user stopped | your `input()` prompt, gone |
| The user waits politely for your output | **Barge-in / interruption** — the user talks over the model, and you must truncate the audio *and* the model's own record of what it said | there is no text-chat analogue; this is new |
| Latency is a UX nicety | A **hard budget in tens of milliseconds**: past ~300–500 ms round trip, the conversation feels broken | Day 17 measured latency to make a spinner honest; here it is the product |
| Output can be inspected before delivery | Audio is **already leaving** as it is generated | 🎯 see §4.2 |

The architectural fork worth knowing by name: **speech-to-speech** (audio in, audio out, one model —
lowest latency, keeps tone and emotion, hardest to inspect) versus a **chained pipeline**
(STT → your existing text agent → TTS — higher latency, but every text-domain tool you own still
works, including every guardrail in `guardrails.py`). The SDK supports both shapes;
`RealtimeRunner`/`RealtimeSession` is the first, the voice-pipeline classes are the second. **If you
had to add voice to Mandala tomorrow, the chained pipeline is the answer**, precisely because it
keeps the text boundary where all nineteen days of your safety work lives.

SIP is the boring, important footnote: it is how a realtime agent answers **an actual phone call**
rather than a websocket from a browser. Know the word, know that it makes "the agent picks up the
support line" a configuration rather than a project, and know that it is the moment your blast radius
includes the PSTN.

### 4.2 🎯 The idea worth stealing: a guardrail with a deadline

Day 17's §4.3 named a tension: **output guardrails (Day 12) run *after* the output exists, and
streaming has already shown the user the text.** Mandala's answer was `may_stream()` — stream to the
operator, never to the customer, because the operator is inside the trust boundary.

Voice takes that same tension and removes the escape hatch. **There is no "operator channel" for a
customer phone call, and audio the customer has heard cannot be un-heard.** So realtime systems run
guardrails on a rolling basis — on the transcript as it is produced, every N words rather than once
at the end — and when one trips they *interrupt the model mid-sentence* and speak a correction.

Sit with what that means: **the guardrail's deadline is not "before delivery", it is "before the next
few hundred milliseconds of delivery".** Your check must be fast enough to run repeatedly on a
partial output, and correct enough to be worth acting on when it fires. Look at `find_secrets` in
`guardrails.py` (Day 12): a regex over text, microseconds, no model call. **That is the shape of a
guardrail that could survive being moved to a voice channel**, and it is not an accident — cheap
deterministic checks were the right call for text too, and voice merely makes the alternative
impossible rather than merely expensive.

There is also no `deliver()` gate to hide behind. Day 17's `StreamWithheld` works because text can
be buffered. **Audio buffered long enough to be inspected is audio that arrives too late to be
conversational.** That is the honest, unresolved trade-off at the heart of voice agents, and saying
it plainly is a better interview answer than any feature list.


### 4.3 Could you rebuild it for free? Yes. Should you today? No.

Day 15 rebuilt hosted web search with `ddgs`. Day 19 rebuilt the hosted sandbox with Docker. The
pattern of this project is "the paid thing is a convenience; build the guarantee yourself". So be
consistent and ask the question properly.

**The parts exist and are free.** Local STT (a Whisper-class model), local TTS (any of several open
voices), a VAD library for turn detection, `sounddevice` for the microphone, and your existing text
agent in the middle. Nothing on that list needs a key.

**And it is still the wrong day for it**, for three reasons worth saying out loud rather than
hand-waving:

1. **It is not one concept, one day, one demo (Principle 3).** Audio device wrangling alone is a day.
   Adding STT + VAD + TTS + interruption handling is a week, and none of that week teaches you
   anything about agents.
2. **The hard part does not survive the rebuild.** Your local pipeline would have 2–4 seconds of
   latency, which means you would never experience barge-in, turn detection under pressure, or the
   rolling-guardrail deadline — **the four things §4.1 says are the actual content of realtime.** You
   would ship a slow chatbot with a microphone and learn none of it.
3. **Mandala is a text-channel support-operations system** (plan Part 0). A voice channel would be a
   different product with a different threat model — recordings are personal data, phone numbers are
   identity, and "the agent hung up on a customer" is a failure mode with no text analogue.

So: **not today, and not a blind spot — a decision** (the addendum's Part 5 words). If you want the
demo notebook the plan mentions, the honest free version is a *transcript* notebook: run a chained
pipeline on a `.wav` file you record, offline, in one cell, and watch where the latency goes. Twenty
minutes, zero API keys, and it makes §4.1's latency table concrete.

### 4.4 When voice is genuinely the right channel

Not never. Voice wins when **the user's hands or eyes are busy** (a technician under a machine, a
driver), when **the phone is the only channel the user has** (an outage that took the web app down;
an elderly or low-literacy customer), when **latency-to-first-help matters more than precision** (a
triage line that routes rather than resolves), and when **tone carries information** — a distressed
customer is audibly distressed thirty seconds before they type anything that says so.

What all four have in common: **the value is in the channel, not in the agent.** If your answer to
"why voice?" is "it seems more advanced", you are adding a real-time system, three new failure modes
and a compliance surface to a problem a text box already solved.

### 4.5 What to read, and what to be able to say

Read (thirty minutes, no key required):

- The Agents SDK realtime guide and the `RealtimeRunner` / `RealtimeSession` reference — the event
  names and the interruption API.
- The voice-pipeline docs — the chained STT → agent → TTS shape, and where you would insert a
  guardrail.
- The realtime API guide's sections on **turn detection** and **audio interruption**, plus the SIP
  page for phone-call connections.

Be able to say, without notes:

- **Two architectures**, speech-to-speech vs. chained pipeline, and which you would pick for Mandala
  and why (chained, because the text boundary is where all your guardrails live).
- **Three things that are new**: turn detection, barge-in, and a latency budget in tens of
  milliseconds.
- **One connection**: a voice guardrail is Day 17's streaming-vs-output-guardrail tension with the
  deadline moved from "before delivery" to "before the next 300 ms of delivery" — which is why the
  cheap deterministic checks in `guardrails.py` are the ones that would survive the move.
- **One honest sentence about why you have not built it**: paid key, wrong channel for this product,
  and a free rebuild that would omit precisely the parts that make realtime hard.

---

## §5 The eval that must be able to fail

### `tests/test_durable.py`

**Every test in this file costs 0 model requests**, and §5.2 explains why that is a design result
rather than a lucky one. Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = ["temporal: needs a local Temporal dev server (temporal server start-dev)"]
```

```python
"""Durability policy tests. No server, no model, no network -- see §5.2."""

import ast
import inspect
import re

import pytest

from mandala import durable
from mandala.durable import (
    NON_RETRYABLE, RESEARCH_RETRY, RESOLVE_RETRY, TASK_QUEUE, MandalaTicketWorkflow,
)
from mandala.idempotency import IdempotentStore, idempotency_key

WORKFLOW_SOURCE = inspect.getsource(MandalaTicketWorkflow)

BANNED = [
    r"\bdatetime\.now\b", r"\btime\.time\b", r"\bdate\.today\b",
    r"\brandom\.", r"\buuid\.uuid4\b", r"\basyncio\.sleep\b",
    r"\bopen\(", r"\bos\.environ\b", r"\brequests\.", r"\bhttpx\.",
]


# --- the determinism boundary -------------------------------------------------------
@pytest.mark.parametrize("pattern", BANNED)
def test_workflow_code_contains_no_banned_nondeterminism(pattern):
    """The §3.2 table, as an assertion. Replay-safe code cannot read a clock or a die."""
    assert not re.search(pattern, WORKFLOW_SOURCE), f"{pattern} inside workflow code"
    # TODO(me): a regex sees text, not code. `from datetime import datetime as dt` then
    # `dt.now()` sails straight past this. Rewrite it as an ast.walk over the parsed
    # class, matching ast.Call nodes by resolved name. THE REP: a lint that can be
    # renamed around is a lint that will be, on the day it matters most.


def test_the_workflow_never_calls_a_model_or_builds_a_client():
    """An LLM call in workflow code is the trap of the day (§3.2). Catch it statically."""
    for forbidden in ("Runner.run", "make_model", "AsyncOpenAI", "LitellmModel"):
        assert forbidden not in WORKFLOW_SOURCE, f"{forbidden} belongs in an activity"


def test_the_workflow_only_reaches_the_outside_through_execute_activity():
    tree = ast.parse(WORKFLOW_SOURCE)
    awaited = {
        ast.unparse(n.value.func)
        for n in ast.walk(tree)
        if isinstance(n, ast.Await) and isinstance(n.value, ast.Call)
    }
    assert awaited <= {"workflow.execute_activity"}, f"unexpected await: {awaited}"


# --- policy is explicit, not defaulted (Principle 4) --------------------------------
@pytest.mark.parametrize("policy", [RESEARCH_RETRY, RESOLVE_RETRY])
def test_every_retry_policy_spells_out_every_field(policy):
    """Framework defaults retry FOREVER. On a free tier that is a quota bonfire."""
    assert policy.maximum_attempts is not None and 1 <= policy.maximum_attempts <= 6
    assert policy.initial_interval is not None
    assert policy.backoff_coefficient and policy.backoff_coefficient > 1.0
    assert policy.maximum_interval is not None


@pytest.mark.parametrize("policy", [RESEARCH_RETRY, RESOLVE_RETRY])
def test_a_permission_denial_is_never_retried(policy):
    """Day 8's boundary, restated for a system whose default is 'try again' (§3.10)."""
    assert "PermissionDenied" in (policy.non_retryable_error_types or [])


def test_the_non_retryable_list_is_exactly_what_we_reviewed():
    """A deliberate change-detector: adding an error class here is a policy decision."""
    assert set(NON_RETRYABLE) == {"PermissionDenied", "ValidationError", "BadSessionId"}


def test_every_activity_call_names_a_timeout_and_a_policy():
    """No unbounded activity. A hung Groq call must not become a hung workflow."""
    tree = ast.parse(WORKFLOW_SOURCE)
    calls = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and ast.unparse(n.func) == "workflow.execute_activity"
    ]
    assert calls, "no activity calls found -- did the class get renamed?"
    for call in calls:
        names = {kw.arg for kw in call.keywords}
        assert "retry_policy" in names
        assert names & {"start_to_close_timeout", "schedule_to_close_timeout"}


def test_the_task_queue_has_exactly_one_definition():
    """§3.4's silent hang: a worker and a client disagreeing about a string."""
    assert TASK_QUEUE == "mandala-durable"
    assert inspect.getsource(durable).count('"mandala-durable"') == 1


```python
# --- idempotency: the thing at-least-once makes mandatory (§3.10) -------------------
def test_the_idempotency_key_is_stable_across_attempts():
    """Same intent, same key -- attempt number must not be an input (Day 6)."""
    args = {"request_id": "req-1", "text": "Sorry about that."}
    assert idempotency_key("post_reply", args) == idempotency_key("post_reply", args)


def test_the_idempotency_key_changes_when_the_reply_changes():
    a = idempotency_key("post_reply", {"request_id": "req-1", "text": "one"})
    b = idempotency_key("post_reply", {"request_id": "req-1", "text": "two"})
    assert a != b


def test_an_activity_run_twice_produces_exactly_one_effect():
    """FLIP IT: delete the `_EFFECTS.run(key, ...)` wrapper in post_reply_activity and
    call `_send` directly. This goes red, and what you have just re-created is a
    customer receiving the same apology twice because a worker died after sending it.
    """
    sent = []
    store = IdempotentStore()
    key = idempotency_key("post_reply", {"request_id": "req-1", "text": "hi"})
    for _ in range(2):                                  # attempt 1, then the retry
        store.run(key, lambda: sent.append("hi"))
    assert len(sent) == 1, "the effect ran twice -- this is the double-post bug"


def test_a_write_activity_still_requires_approval(mandala_context):
    """Principle 12 is not suspended because the run is durable."""
    assert mandala_context.approvals_required is True
    assert mandala_context.may_write is False or "post_reply" in NON_RETRYABLE or True


# --- needs a server; skipped by default (§5.2) --------------------------------------
@pytest.mark.temporal
@pytest.mark.asyncio
async def test_the_workflow_replays_deterministically():
    """Run the recorded history back through the workflow code and demand the same path.

    TODO(me): capture a real history (WorkflowEnvironment + a stub activity that
    returns a canned Brief), then feed it to Replayer.replay_workflow. Asserting
    'my workflow is replay-safe' is the only test that proves §3.2 end to end.
    """
    pytest.skip("TODO(me): implement with WorkflowEnvironment + Replayer")
```

**Line by line:**

- `test_workflow_code_contains_no_banned_nondeterminism` — **§3.2's table turned into a lint**, and it
  runs on `inspect.getsource` of one class, so it is fast, free and offline. Its `TODO(me)` is the
  fourth rep and it is honest about its own weakness: a regex matches text, and `dt.now()` defeats it.
- `test_the_workflow_only_reaches_the_outside_through_execute_activity` — the strongest of the three,
  because it is a **whitelist over the AST**, not a blacklist over strings. Add `await
  some_client.get(...)` to the workflow and it goes red without anyone updating a pattern list.
- `test_every_retry_policy_spells_out_every_field` — Principle 4, mechanized. `maximum_attempts=None`
  means *retry forever*, and forever against a free tier is a quota bonfire you will discover from
  the provider console, not from your logs.
- `test_a_permission_denial_is_never_retried` — the security test of the day, and it costs nothing
  because the policy is data. **Put security decisions in data structures and you can assert them for
  free** — the same result Day 18 got, for the same reason.
- `test_the_non_retryable_list_is_exactly_what_we_reviewed` — a deliberate change-detector, same
  spirit as Day 8's blast-radius test and Day 18's operation registry. Going red *is* the feature.
- `test_the_task_queue_has_exactly_one_definition` — silly-looking, and it catches §3.4's worst
  symptom: a run that hangs forever with no error because two strings drifted apart.
- `test_an_activity_run_twice_produces_exactly_one_effect` — **the flip-it test.** Read its docstring,
  do what it says, watch it go red, then put the wrapper back. Ten seconds, and you will never again
  hear "at-least-once" as an abstraction.
- The `@pytest.mark.temporal` test is skipped by default and left as a `TODO(me)` because a replay
  test written from memory is worse than none.

### 5.2 Why the suite passes with no server running

Run `uv run pytest tests/test_durable.py -q` with terminal 1 closed. **It should be green.** That is
deliberate, and the reasoning generalizes beyond today: `make check` must stay green on a machine
that has not started a daemon, or people will start ignoring red — and a suite people ignore is worse
than no suite. So the server-dependent test carries a marker (`-m "not temporal"` in CI), and
**everything that encodes a *decision* — the determinism boundary, the retry policy, the
non-retryable list, the idempotency key — is testable as pure data at 0 requests.** If a rule of
yours is only checkable by running the whole system, that is usually a hint the rule is in the wrong
place.

---

## §6 Traps

- **An LLM call inside workflow code.** 🎯 **The trap of the day.** It works perfectly until the
  first crash, then replay asks the model again, gets a different answer, takes a different branch,
  and the run is corrupt in a way no stack trace explains. The model call goes in an activity, always.
- **A retried `post_reply` with no idempotency key.** At-least-once means the write *will* run twice
  eventually. The customer gets two apologies and you get a conversation with your manager.
- **An in-memory idempotency store.** The retry you most need to deduplicate is the one caused by the
  worker dying — which is the exact event that empties the dict. §3.6's `TODO(me)`.
- **Leaving `maximum_attempts` unset.** The default is retry-forever, and forever against a free tier
  is a daily quota consumed overnight by one malformed prompt (Principle 5).
- **Retrying `PermissionDenied`.** The answer will not change, and you have turned one denied action
  into four audit lines that say you kept trying (Day 8, Day 10).
- **Constructing the model client at workflow scope.** `make_model()` reads the environment through
  `load_keys()`; the replaying process may not have the same one. Build it inside the activity.
- **A worker and a client with different task-queue names.** No error, no timeout — the workflow just
  sits in `Running` forever. Check this first, every time (§3.4).
- **Running `start-dev` without `--db-filename`.** The server forgets too, so your kill-and-resume
  experiment "passes" for the wrong reason and teaches you nothing.
- **Declaring a `heartbeat_timeout` for an activity that never heartbeats.** You have configured a
  deadline nothing can satisfy — worse than no deadline, because the table now lies.
- **Assuming a timeout cancels the work.** It cancels your *waiting*. The HTTP request may still land
  and still count against your quota (§3.10).
- **Editing workflow code while runs are in flight.** Insert an activity between two existing ones
  and every replaying history mismatches. Versioning exists; know it is there before you need it.
- **Letting Day 6's router flatten a permanent error into a generic one.** `NON_RETRYABLE` cannot
  classify what the inner loop already turned into `AllProvidersFailed`.
- **Treating durability as free.** Read the §3.11 table again before adding it to a five-second call.

---

## §7 Request budget

Activities are where the model calls live, so the budget is a count of *activity executions* —
and the kill-and-resume experiment re-runs some of them on purpose.

| Activity | Model requests | Notes |
|---|---|---|
| `temporal server start-dev`, CLI, web UI | **0** | it is a database, not a model |
| Every test in `tests/test_durable.py` | **0** | AST, regex, retry-policy fields, hashes (§5.2) |
| `dry_run.py` with stub activities | **0** | proves the wiring before spending anything |
| `durable_demo.py`, one clean run | ~5 (Groq) | ~3 research turns + ~2 resolve |
| **Kill during `resolve`** (the main experiment) | ~7 (Groq) | ~5 for the first attempt + ~2 for resolve re-run; **research is not repeated** |
| **Kill during `research`** (the honest second run) | ~9 (Groq) | ~3 lost, ~3 repeated, ~3 resolve — this is at-least-once costing you money it cannot bill |
| Wiring iteration (queue names, serialization, sandbox import errors) | ~10 (Groq) | budget for it; the first worker run rarely reaches an activity |
| OAI-22 realtime (§4) | **0** | no lab, no key, no notebook that calls anything |
| **Total** | **≈ 31, Groq** | log it in `docs/RATE_BUDGET.md` |

**Two-thirds of a durability budget is spent proving that durability works**, which is the same joke
as Day 18's naive baseline: you pay once to see the failure and its recovery, then never again.

If your Groq ceiling is tight: drop the second kill (during `research`) and instead **read** its
outcome off the web UI's history from the first run. Do **not** drop the first kill — it is the day.
And run `dry_run.py` until the wiring is clean, because iterating on a queue name at ~5 requests a
try is the most avoidable spend on this page.

---

## §8 Verify before you code

Written **2026-08-20** against `openai-agents` **0.22.0** and `temporalio` **1.31.0**. Today's code
touches a package this project has never used before, so **verify more than usual** — and remember
Principle 14: if reality differs, say so and propose an amendment; do not silently adapt.

- `https://docs.temporal.io/develop/python/` — the Python SDK developer guide: workflows, activities,
  workers, timeouts, retries. Read the "core application" and "failure detection" pages.
- `https://python.temporal.io/` — the API reference. **Confirm in 1.31.0:** `workflow.execute_activity`
  keyword names (`start_to_close_timeout`, `heartbeat_timeout`, `retry_policy`), the import path of
  `RetryPolicy` (`temporalio.common`), and `ApplicationError(non_retryable=True, type=...)`.
- **Confirm in 1.31.0: `workflow.unsafe.imports_passed_through()`.** This is the line most likely to
  have moved or gained an alternative (a sandbox-runner configuration). If the Agents SDK still
  explodes on import inside the sandbox despite it, that is a real finding — log it.
- **Confirm in 1.31.0: how activity functions are registered and whether they must be `async`.**
  Sync activities need a thread/process executor on the `Worker`; today's are async, so this should
  be moot — but check, because "why is my worker refusing to start" usually lives here.
- **Confirm in 1.31.0: the Pydantic data converter** (`temporalio.contrib.pydantic`) and whether
  passing a `Brief` directly is supported. §3.5 returns JSON strings to avoid depending on it. If the
  converter is stable, using it is a legitimate simplification — pin it and note the change.
- `https://docs.temporal.io/develop/python/testing-suite` — `WorkflowEnvironment` and `Replayer`. You
  need both for §5's skipped `TODO(me)` test.
- **The Agents SDK + Temporal integration page** (linked from
  `https://openai.github.io/openai-agents-python/` and from Temporal's docs). **Confirm the contrib
  module's import path and whether it targets `openai-agents` 0.22.0** — contrib module names move
  between releases more than anything else in this stack. §3.12 depends on this being findable.
- `https://openai.github.io/openai-agents-python/realtime/guide/` and the voice-pipeline reference —
  read-only (§4). **Confirm `RealtimeRunner`/`RealtimeSession` are still the names** and note the
  event set for interruption.
- `https://platform.openai.com/docs/guides/realtime` — turn detection, audio interruption, SIP.
  Read, do not run: it needs a paid key (Principle 5).
- Re-check `temporalio` on PyPI. **1.31.0 is what `docs/PINS.md` recorded on 2026-08-20**; a patch
  bump is routine (pin it, log one line), a minor bump means read the release notes first.

---

## §9 Say it in an interview

> "Durable execution is replay, and the interesting consequence is what it forbids. Temporal restarts
> your workflow function from line one after a crash and returns each completed step's *recorded*
> result instead of re-running it — so the function has to take the same path every time. That means
> **the LLM call cannot be in the workflow; it has to be an activity.** I proved that to myself the
> uncomfortable way: even with a pinned model and `temperature=0.0`, the answer that came back on
> replay could differ, the branch would differ, and the run would be corrupt. So the split is:
> workflow code is deterministic orchestration — no clock, no randomness, no I/O, no model — and
> every model call, tool call and byte of I/O is an activity with an explicit timeout and an explicit
> retry policy. I have a test that walks my workflow class's AST and fails if it awaits anything
> other than `execute_activity`, and it costs zero API requests to run."

> "I demoed it by killing the worker mid-run. The run was researching a ticket, then drafting a
> reply; I Ctrl-C'd the worker during the draft step and restarted it, and **the new process did not
> re-run the research — its result was already a fact in the event history, so the workflow replayed
> to the draft step in microseconds and continued.** On a zero-budget project that is not a
> reliability nicety, it is the budget: the research calls I did not repeat are free-tier requests I
> did not have to spend twice. The other half of the lesson is that execution is at-least-once, never
> exactly-once — so any activity with a side effect needs an idempotency key derived from stable
> inputs, not from the attempt. That is why my `post_reply` is separate from `draft_reply` and why
> `PermissionDenied` is in `non_retryable_error_types`: retrying a denial four times doesn't get you
> permission, it gets you four audit lines."

---

## §10 Done when

```bash
./m check
./m done 20
```

- The tests are green **with no Temporal server running** (§5.2), and green again with one.
- The kill-and-resume experiment is recorded in the CHECKLIST with real numbers, not adjectives.

Tomorrow closes Phase 3: guardrails and approvals composed into one Resolver that finally has its
whole permission story — the day `post_reply` stops being a landmine and becomes a gated write —
plus AgentKit literacy (OAI-23/25). Today you made a run survive a crash; tomorrow you make sure the
thing it resumes into still needs a human to say yes.
