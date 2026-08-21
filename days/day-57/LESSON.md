---
day: 57
phase: 8
phase_name: "MCP (2026-07-28 spec)"
title: "Tasks, Apps, and the extensions framework"
ids: ["MCP-08", "MCP-09", "MCP-10"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 57 — Tasks, Apps, and the extensions framework

**Phase 8 · MCP 2026-07-28** · IDs: **MCP-08 🛠️**, **MCP-09 🅿️**, **MCP-10 🅿️**

> **Yesterday:** four token checks, a scope-escalation bug your own lab caught, and a closed
> elicitation schema.
> **Today:** the extensions. **Tasks** (MCP-08) is the buildable one and it completes AG-27's fourth
> durable-execution implementation — a tool call that returns a *handle* instead of an answer. Then
> two 🅿️ reads that matter more than they look: **Apps** (tools shipping their own UI) and **EMA**
> (enterprise-governed allowlists), plus the framework that lets all three ship on independent
> schedules.
> **Tomorrow:** the deprecation drill, agent-over-MCP, and the Phase-8 gate.

```bash
./m start 57
./m scaffold 57
```

---

## §1 The story

The 2026-07-28 revision did something structural that is easy to miss: **it stopped putting every
capability in the core.** Apps, Tasks and EMA are *extensions* — versioned separately, adopted
separately, and negotiable per server.

**That is a governance decision with engineering consequences**, and it is worth reading against Day
53's MCP-12. A single monolithic spec means every client must implement everything before anyone can
use anything, and every capability moves at the speed of the slowest reviewer. Extensions mean a
server can offer Tasks without offering Apps, and a client can support neither and still work.

**The cost is discovery.** With one spec, "what can this server do?" had one answer. With extensions,
it is a negotiation — and §4.2 makes you find out how it works, because **you cannot review a
third-party server (Day 66) without knowing how to enumerate what it has turned on.**

**MCP-08 is the one you build**, and it is genuinely useful for Mandala. Every tool call so far has
been request/response: the client waits, the server answers. That model breaks for
*"re-index the archive"* — work measured in minutes. **Tasks return a handle immediately, and the
client polls.** That is AG-27's fourth implementation, and the plan named it as such on Day 49.

---

## §2 Setup — run this

### 2.1 No new packages

```bash
grep -n 'mcp' pyproject.toml
```

- Extensions ship inside `mcp==2.0.0` — or they do not, and **finding out which is §5's first
  question.** An extension the SDK does not implement is a read-only day for that ID, and the plan
  marks two of three 🅿️ already.

### 2.2 Create today's files

```bash
touch src/mandala_mcp/tasks.py
touch tests/test_mcp_tasks.py
mkdir -p days/day-57/lab
touch days/day-57/lab/task_lifecycle.py
touch days/day-57/lab/capability_probe.py
touch days/day-57/lab/extensions_notes.md
```

- `capability_probe.py` costs **0 requests** and is the file you will reuse on Day 66 against a
  stranger's server. **Write it as a tool, not as a demo.**

---

## §3 MCP-08 — the Tasks extension

### 3.1 The shape

| | Ordinary tool call | Task |
|---|---|---|
| Returns | the answer | **a task handle** |
| Client behaviour | waits | polls `tasks/get` |
| Timeout risk | the whole call | none — each poll is short |
| Cancellation | kill the connection | **`tasks/cancel`, cooperatively** |
| Server-side state | none | **the task record** |

**That last row is the interesting one and you should stop on it.** Day 53 established that the
2026-07-28 core is stateless, and Day 54 made you assert no module-level mutable state. **A task
record is state.** So how does a stateless server hold one?

The answer is that it does not hold it *in the process*. **The task store is external** — a database,
a queue, a shared cache — exactly as Day 47's checkpointer is external to your graph. Any replica can
answer `tasks/get` for a task another replica started, which is precisely what Day 85's three-replica
proof requires.

**Getting this right is the whole design of §3.2**, and getting it wrong is the easiest way to break
the stateless promise while thinking you are following the spec.

### 3.2 `src/mandala_mcp/tasks.py`

```python
"""Long work returns a handle. The task record lives OUTSIDE the process.

The stateless trap
------------------
A task has state, and a stateless server cannot hold it. Putting `_TASKS = {}` at
module level would make this work perfectly on one replica and fail the moment Day 85
runs three -- a client would poll a replica that never heard of its task.

So the store is an interface with a SQLite implementation (fine for one machine and
for Day 85's compose file, since all three replicas mount the same volume) and an
in-memory implementation for tests only. The rule:

    a task started by any replica must be readable by every replica.

Cooperative cancellation: nothing is killed. A cancel sets a flag; the worker checks
it between units of work and stops. Kill-based cancellation cannot clean up.

Usage
-----
    >>> store = InMemoryTaskStore()
    >>> handle = store.create("reindex", {"scope": "handbook"})
    >>> store.get(handle.task_id).status
    'working'
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, Protocol

Status = Literal["working", "completed", "failed", "cancelled"]

TERMINAL: Final[frozenset[str]] = frozenset({"completed", "failed", "cancelled"})
MAX_RESULT_CHARS: Final = 4_000
TASK_TTL_S: Final = 24 * 3600


@dataclass(frozen=True)
class Task:
    task_id: str
    kind: str
    status: Status
    progress: int = 0
    result: str | None = None
    error: str | None = None


class TaskStore(Protocol):
    def create(self, kind: str, params: dict) -> Task: ...
    def get(self, task_id: str) -> Task | None: ...
    def update(self, task_id: str, **fields) -> Task: ...
    def request_cancel(self, task_id: str) -> bool: ...
    def cancel_requested(self, task_id: str) -> bool: ...


class SqliteTaskStore:
    """Shared by every replica. The reason a stateless server can offer Tasks."""

    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as con:
            con.execute(
                "CREATE TABLE IF NOT EXISTS tasks ("
                " task_id TEXT PRIMARY KEY, kind TEXT, status TEXT, progress INT,"
                " result TEXT, error TEXT, cancel INT DEFAULT 0, created REAL)"
            )

    def _conn(self):
        return sqlite3.connect(self._path, timeout=5)

    def create(self, kind: str, params: dict) -> Task:
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        with self._conn() as con:
            con.execute(
                "INSERT INTO tasks (task_id, kind, status, progress, created)"
                " VALUES (?,?,?,?, strftime('%s','now'))",
                (task_id, kind, "working", 0),
            )
        return Task(task_id=task_id, kind=kind, status="working")

    def request_cancel(self, task_id: str) -> bool:
        """Set a flag. The worker stops itself; nothing is killed."""
        with self._conn() as con:
            cur = con.execute(
                "UPDATE tasks SET cancel = 1 WHERE task_id = ? AND status = 'working'",
                (task_id,),
            )
        return cur.rowcount > 0
```

**Line by line:**

- **`TaskStore` as a `Protocol`** — structural typing, so the SQLite store and the in-memory test
  store are interchangeable without inheritance. This is the same "backend is pluggable" shape as Day
  47's checkpointer packages, and the reason is identical: **the interface is the design, the backend
  is a deployment choice.**
- `SqliteTaskStore` opening a **new connection per operation** (`_conn()` inside each method). That
  looks wasteful and it is correct here: connections are not shareable across threads or processes,
  and the whole point is that several replicas touch this file. `timeout=5` handles the write lock.
- `task_id = f"task_{uuid.uuid4().hex[:12]}"` — the plan's MCP-08 example literally shows
  `task_abc123`. **A task id must be unguessable**, because possessing it is what authorises polling
  it. Sequential ids would let any caller enumerate other callers' tasks.
- `status` as a `Literal` with a `TERMINAL` frozenset — **countable on Day 71, and the terminal set is
  what makes "is this done?" a set membership rather than a chain of `or`s.**
- `request_cancel` sets a **flag** and returns whether it changed anything. `WHERE ... AND status =
  'working'` means cancelling a finished task is a no-op that reports `False` rather than corrupting
  a completed record.
- **The docstring's cooperative-cancellation paragraph is the design.** Killing a worker mid-write
  leaves half-written state; a flag checked between units of work lets it stop cleanly. The spec calls
  this cooperative, and the plan's MCP-08 row says so.
- `MAX_RESULT_CHARS` — a task result goes into a model's context eventually (AG-04, roughly its tenth
  appearance).
- `TASK_TTL_S` — **task records accumulate.** Day 47 said checkpoints age out and Store entries do not
  unless you make them; the same applies here, and a TTL declared today is a sweep you can write
  before it matters.

### 3.3 Wiring Tasks into the server

```python
@mcp.tool()
def reindex_handbook(scope: str = "handbook") -> str:
    """Start a re-index. Returns a task handle immediately; poll tasks/get.

    This is long work. It returns a HANDLE, not an answer.
    """
    task = STORE.create("reindex", {"scope": scope})
    _spawn(task.task_id, scope)
    return f"task started: {task.task_id}"
```

**Line by line:**

- **The docstring tells the *model* this returns a handle.** Without that, the model reads
  `"task started: task_abc123"` as a final answer and reports success to the user. **Model-facing
  documentation is a correctness requirement here, not politeness.**
- `_spawn` — a thread or a subprocess. **Whatever you use, it must check
  `STORE.cancel_requested(task_id)` between units of work**, or cancellation is a lie.
- Note the tool returns a *string*, not a structured handle, in this sketch. **Find out whether the
  extension defines a proper task-handle response type** (§5) and use it if so — a string handle that
  the client has to parse is exactly the kind of informal protocol the extension exists to replace.

### 3.4 `days/day-57/lab/task_lifecycle.py` — 0 model requests

```python
"""Start a task, poll it, cancel one, and read the store from a SECOND connection.

Run:
    uv run python days/day-57/lab/task_lifecycle.py

Budget: 0 requests. No model is involved in a re-index.
"""

import time
from pathlib import Path

from mandala_mcp.tasks import TERMINAL, SqliteTaskStore

DB = Path(".mandala/tasks.sqlite")
store = SqliteTaskStore(DB)

first = store.create("reindex", {"scope": "handbook"})
print(f"started {first.task_id}")

# THE point: a DIFFERENT store object, as a different replica would have.
other_replica = SqliteTaskStore(DB)
print(f"replica 2 sees it: {other_replica.get(first.task_id)}")

second = store.create("reindex", {"scope": "tickets"})
print(f"cancel requested : {other_replica.request_cancel(second.task_id)}")
print(f"worker should stop: {store.cancel_requested(second.task_id)}")

for _ in range(5):
    task = other_replica.get(first.task_id)
    print(f"  poll: status={task.status} progress={task.progress}")
    if task.status in TERMINAL:
        break
    time.sleep(0.5)
```

**Line by line:**

- **`other_replica` is the whole file.** A second `SqliteTaskStore` over the same database stands in
  for a second server process. If it can see and cancel a task the first one started, the stateless
  story holds; if it cannot, you put state in the process. **Two objects, one file — that is the
  test.**
- The cancel is requested by **replica 2** and observed by **replica 1**, which is the realistic case:
  a load balancer sends the cancel wherever it likes.
- Polling with `TERMINAL` membership rather than `!= "working"` — the set makes the intent explicit
  and survives a new status being added.
- `time.sleep(0.5)` in a **lab** script is fine; in the server it would not be.
- **Extend it:** kill the process mid-task and restart, then poll again. Does the task still exist? Is
  it stuck in `working` forever? **A task whose worker died and is never marked failed is a leak**,
  and deciding what to do about it (a heartbeat? a TTL sweep?) is a real design question you should
  answer today rather than on Day 85.

---

## §4 MCP-09 and MCP-10 — the two 🅿️ reads

### 4.1 Apps: tools that ship a UI

An **App** is a tool that also provides a sandboxed-iframe interface, declared up front. Button clicks
come back over JSON-RPC. The plan's example: *a triage approval panel instead of a typed "approve".*

**Read that against Day 50.** You built approvals four times — every one of them text in, text out,
and the reviewer's interface was your problem. An App means **the server ships the panel**.

**And that is exactly where the risk is**, and you already have the vocabulary from yesterday:

- Day 56 established that elicitation lets a server put **text** on your user's screen, and that this
  is a phishing surface.
- **An App lets a server put a *whole interface* there.**
- Sandboxed iframe is the containment mechanism, and it is doing a lot of work: it is what stops the
  panel reading your page, your storage, or your tokens.

**The questions to answer, and to reuse on Day 66:** what is the sandbox's actual policy? Can the App
make network requests? Does the user see which server supplied the panel? **If your answer to the last
one is "no", the phishing analysis from Day 56 §4.2 applies with a much bigger surface.**

Mandala builds none of this — it is a text-channel system (plan Part 8) — but **the approval panel is
the obvious future use**, and knowing the shape means you can evaluate it when someone proposes it.

### 4.2 EMA: enterprise-managed authorisation

**EMA = IdP-governed allowlists of servers and extensions.** An organisation's identity provider
decides which MCP servers its agents may connect to, and which extensions may be enabled.

**Line up the three layers you now have**, because this is where they resolve:

| Layer | Decides | Enforced by | Day |
|---|---|---|---|
| `ALLOWED_TOOLS` | which tools *my agent* takes | my client | 55 |
| scopes | which tools *this caller* may invoke | the server | 56 |
| **EMA** | **which servers may be connected at all** | **the organisation's IdP** | today |

**Day 55 said the client allowlist was selection, not enforcement, and Day 56 fixed that per-server.
EMA fixes it per-organisation.** Each layer answers a question the one below it cannot, and being able
to draw this table is the MCP-10 competence.

**And the connection to Day 66 is direct:** a registry (MCP-12) makes third-party servers easy to
install; EMA is the control that stops "easy to install" meaning "installed". **On a solo project you
have no IdP — so *you* are the allowlist**, and that is worth writing down as a policy rather than
leaving as a habit.

### 4.3 `days/day-57/lab/capability_probe.py` — 0 model requests

**Write this as a tool you will reuse**, not as a demo. Day 66 points it at a stranger's server.

```python
"""What has this server actually turned on? Reusable -- Day 66 aims it at a stranger.

Run:
    uv run python days/day-57/lab/capability_probe.py            # ticket-db
    uv run python days/day-57/lab/capability_probe.py <url>      # anyone's

Budget: 0 requests. Enumeration is free; that is why you should always do it.
"""

import asyncio
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765/mcp"


async def main() -> None:
    async with streamablehttp_client(URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            # TODO(me): how does a client discover which EXTENSIONS a server supports?
            # There is no `initialize` any more (MCP-02). Find the mechanism and use it.
            tools = await session.list_tools()
            print(f"tools     ({len(tools.tools)})")
            for t in tools.tools:
                print(f"  {t.name:<20} {sorted(t.inputSchema.get('properties', {}))}")

            resources = await session.list_resources()
            print(f"resources ({len(resources.resources)})")
            for r in resources.resources:
                print(f"  {r.uri}")

            prompts = await session.list_prompts()
            print(f"prompts   ({len(prompts.prompts)})")
            for p in prompts.prompts:
                print(f"  {p.name}")
                # A server-supplied prompt goes into MY model's context (Day 56 §4.2).
                # Print it in full. Read it. Every time.


asyncio.run(main())
```

**Line by line:**

- **The `TODO` is the day's central question.** With no `initialize` handshake, how does a client
  learn which extensions a server supports? A well-known document? Headers on a response? A
  `capabilities` method? **Find it, wire it in, and note that this is the cost of the extensions
  framework** — discovery got harder in exchange for independent release cadence.
- Printing every tool's `inputSchema` — third time this habit has appeared (Days 37, 54, today).
  **For a third-party server it is not a habit, it is the review.**
- **The comment under prompts is the most important line in the file.** A server-supplied prompt is
  text that enters your model's context. Printing it in full, every time, is the entire defence
  against a friendly-looking server shipping an instruction you did not read.
- Taking a URL argument makes this a **tool rather than a demo**, which is why Day 66 can reuse it.

---

## §5 The eval that must be able to fail

### `tests/test_mcp_tasks.py`

```python
"""Tasks are state on a stateless server. The store is where that gets decided."""

import time
from pathlib import Path

import pytest

from mandala_mcp.tasks import (
    MAX_RESULT_CHARS,
    TASK_TTL_S,
    TERMINAL,
    SqliteTaskStore,
)


@pytest.fixture
def store(tmp_path) -> SqliteTaskStore:
    return SqliteTaskStore(tmp_path / "tasks.sqlite")


def test_a_task_starts_working(store):
    task = store.create("reindex", {"scope": "handbook"})
    assert task.status == "working"
    assert task.task_id.startswith("task_")


def test_task_ids_are_unguessable(store):
    """Possessing the id authorises polling it. Flip it: use a counter, see red."""
    ids = {store.create("reindex", {}).task_id for _ in range(20)}
    assert len(ids) == 20
    suffixes = [i.split("_", 1)[1] for i in ids]
    assert all(len(s) >= 12 for s in suffixes)
    assert not any(s.isdigit() for s in suffixes), "sequential ids are enumerable"


def test_a_second_replica_sees_the_task(tmp_path):
    """THE stateless test. Flip it: use a module-level dict and this goes red."""
    path = tmp_path / "tasks.sqlite"
    first = SqliteTaskStore(path)
    second = SqliteTaskStore(path)
    task = first.create("reindex", {})
    assert second.get(task.task_id) is not None


def test_a_second_replica_can_cancel(tmp_path):
    path = tmp_path / "tasks.sqlite"
    first, second = SqliteTaskStore(path), SqliteTaskStore(path)
    task = first.create("reindex", {})
    assert second.request_cancel(task.task_id) is True
    assert first.cancel_requested(task.task_id) is True


def test_cancelling_a_finished_task_is_a_no_op(store):
    task = store.create("reindex", {})
    store.update(task.task_id, status="completed")
    assert store.request_cancel(task.task_id) is False


def test_cancellation_is_cooperative_not_a_kill():
    """Grep-as-a-test: nothing terminates a worker. Flip it: add kill(), see red."""
    source = Path("src/mandala_mcp/tasks.py").read_text(encoding="utf-8")
    for banned in ("terminate(", "kill(", "SIGKILL", "_thread.interrupt"):
        assert banned not in source, banned


def test_the_terminal_set_covers_every_non_working_status():
    from typing import get_args

    from mandala_mcp.tasks import Status

    assert set(get_args(Status)) - {"working"} == TERMINAL


def test_results_are_bounded():
    assert MAX_RESULT_CHARS <= 8_000


def test_tasks_have_a_ttl():
    """Task records accumulate. Day 47 said the same about the Store."""
    assert 0 < TASK_TTL_S <= 7 * 24 * 3600


def test_no_module_level_mutable_state():
    """Same AST check as Day 54. A task store in a module dict breaks Day 85."""
    import ast

    tree = ast.parse(Path("src/mandala_mcp/tasks.py").read_text(encoding="utf-8"))
    offenders = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, (ast.Dict, ast.List)):
            if getattr(node.value, "elts", None) or getattr(node.value, "keys", None):
                offenders += [t.id for t in node.targets if isinstance(t, ast.Name)]
            elif not getattr(node.value, "keys", True):
                offenders += [t.id for t in node.targets if isinstance(t, ast.Name)]
    assert offenders == [], offenders


def test_the_tool_docstring_tells_the_model_it_gets_a_handle():
    """Without this the model reports 'done' when the work has not started."""
    source = Path("src/mandala_mcp/server.py").read_text(encoding="utf-8")
    if "reindex_handbook" in source:
        assert "handle" in source.lower() and "poll" in source.lower()
```

**Line by line:**

- `test_a_second_replica_sees_the_task` is today's headline test and it is **two store objects over
  one file.** That is the smallest possible simulation of Day 85's three replicas, and it fails
  instantly if you put the tasks in a dict.
- `test_task_ids_are_unguessable` checks length *and* non-numeric. **The flip-it note names the actual
  wrong design** (a counter), which is what someone reaches for when debugging.
- `test_cancellation_is_cooperative_not_a_kill` is a grep test guarding a design property. Note that
  it can only see *this* file — a `kill` in the worker module would slip past. **Say that limitation**
  and consider widening the glob.
- `test_the_terminal_set_covers_every_non_working_status` is a **cross-definition invariant**: add a
  status to the `Literal` and forget the terminal set, and polling loops forever. One line, real bug.
- `test_no_module_level_mutable_state` is Day 54's AST check, **reused verbatim in a second module.**
  When a test is worth copying, that is a signal it should be a shared helper — consider extracting it
  to `tests/conftest.py` and note the refactor.
- `test_the_tool_docstring_tells_the_model_it_gets_a_handle` guards §3.3's correctness requirement.
  **A docstring test looks silly until you remember the docstring is the prompt.**

---

## §6 `days/day-57/lab/extensions_notes.md`

```markdown
# Extensions — Mandala, 2026-08-__

## Which extensions does mcp==2.0.0 actually implement?
| Extension | In the spec | In the SDK | Mandala uses |
|---|---|---|---|
| Tasks | yes | ? | yes — reindex |
| Apps | yes | ? | no (text channel, Part 8) |
| EMA | yes | ? | no (no IdP on a solo project) |

## How does a client discover a server's extensions with no `initialize`?
<the §4.3 TODO. This is the cost of the extensions framework -- name it.>

## The three authorisation layers
| Layer | Decides | Enforced by | Day |
|---|---|---|---|
| ALLOWED_TOOLS | which tools my agent takes | my client | 55 |
| scopes | which tools this caller may invoke | the server | 56 |
| EMA | which servers may be connected at all | the org's IdP | 57 |

**On this project there is no IdP, so I am the EMA layer.** My policy:
<write it. Which servers may Mandala connect to, and who decides?>

## Apps: the questions I would ask before enabling one
1. what is the iframe sandbox policy, exactly?
2. can the App make network requests?
3. does the user see which server supplied the panel?
4. <yours>

## Tasks: the failure mode I found
<what happens to a task whose worker died? is it stuck in `working` forever?
 what did I decide -- heartbeat, TTL sweep, or accept it?>
```

**The bolded line is today's decision.** EMA does not apply to a solo project, which means the control
does not exist — **unless you write the policy down yourself.** "I will only connect Mandala to
servers I wrote, until Day 66's review process exists" is a perfectly good policy and it takes one
line. An unwritten policy is a habit, and habits do not survive a day when something looks useful.

---

## §7 Traps

- **A module-level task dict.** Works on one replica, fails on three. The AST test catches it.
- **Sequential task ids.** Possessing the id authorises polling it.
- **Kill-based cancellation.** Half-written state. Set a flag; the worker stops itself.
- **A worker that never checks the flag.** Then cancellation is a lie with a passing test.
- **No TTL on task records.** They accumulate, and they contain results.
- **A docstring that does not say "handle".** The model reports success for work that just started.
- **Not printing server-supplied prompts.** Text entering your model's context, unread.
- **Assuming discovery still works like `initialize`.** It does not, and that is the extension
  framework's cost.
- **Treating MCP-09 and MCP-10 as trivia.** Apps are a bigger phishing surface than elicitation, and
  EMA is the layer that makes a registry safe.
- **Leaving the EMA policy unwritten** because you have no IdP. Then you have no policy.

---

## §8 Request budget

**Declared: 0 model requests.**

| What | Requests |
|---|---|
| Everything today | **0** |

**Fifth free day in twelve.** Phase 8 has cost almost nothing so far, and that is the strongest
free-tier argument for MCP in the whole plan: **the boundary layer is testable, probeable and
buildable without a provider.** Compare Phase 5's ~110 requests and Phase 7's ~100. Put the number in
Day 58's gate write-up — *"free-tier friendliness"* is a scorecard row and Phase 8 is about to score
very well on it.

---

## §9 Verify before you code

Written **2026-08-20** against spec revision **2026-07-28** and `mcp==2.0.0`:

- **Does `mcp==2.0.0` implement Tasks at all?** If not, today's `tasks.py` is a faithful model of the
  shape and you should say so in the notes rather than implying you used the extension.
- **The exact method names** — `tasks/get`, `tasks/cancel`. And is there a `tasks/list`?
- **Is there a defined task-handle response type**, or does a tool return a string? §3.3 needs this.
- **How does a client discover supported extensions with no `initialize`?** The §4.3 TODO and the most
  important question of the day.
- **Does the spec say anything about task-id unguessability or authorisation to poll?** If polling is
  unauthenticated, an unguessable id is the *only* control.
- **Apps: the iframe sandbox policy** as specified — what is allowed, what is denied.
- **EMA: where the allowlist lives** and how a client learns it.
- **Extension versioning** — how does a server say *which version* of Tasks it implements, and what
  happens on mismatch?
- The specification's extensions pages — **read today.**

---

## §10 Say it in an interview

> "The 2026-07-28 revision moved capabilities out of the core into versioned extensions, so a server
> can offer long-running Tasks without offering Apps and a client can support neither and still work.
> The engineering cost is discovery — with no initialize handshake, finding out what a server has
> turned on is a separate problem, and that matters because you can't review a third-party server
> without enumerating it. I built the Tasks extension, and the interesting part is the tension: a task
> has state and the core is stateless, so the task store has to be external — I proved it with two
> store objects over one database file, standing in for two replicas, where one can cancel a task the
> other started. Cancellation is cooperative: nothing gets killed, a flag gets set and the worker stops
> itself between units of work, because killing mid-write leaves half-written state. And the two
> concept extensions resolve something that had been open since I moved my tools behind MCP: my client
> allowlist decides which tools my agent takes, scopes decide which tools a caller may invoke, and EMA
> decides which servers may be connected at all — three layers, each answering a question the one below
> it can't. On a solo project there's no identity provider, so I'm the EMA layer, which means the
> policy has to be written down rather than left as a habit."

---

## §11 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 57
```
