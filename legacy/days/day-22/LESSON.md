---
day: 22
phase: 3
phase_name: "OpenAI Agents SDK advanced"
title: "Phase-3 gate — long-horizon sandboxed agent + harness explainer"
ids: []
kind: gate
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 22 — Phase-3 gate — long-horizon sandboxed agent + harness explainer

**Phase 3 · OpenAI Agents SDK advanced** · IDs: **— (gate day)** · **PHASE-3 GATE 🎯**

> **Yesterday:** guardrails, permissions and approvals composed into one policy, plus AgentKit
> literacy.
> **Today:** no new ideas. You assemble thirteen days of parts into one agent that runs long, touches
> files, survives a restart, and cannot hurt anything — then you prove it with evidence, not
> assertion.
> **Tomorrow:** a new framework. CrewAI, and the second answer to "who owns the loop?"

```bash
./m start 22
./m scaffold 22
```

---

## §1 The story

A gate day is not a lesson. It is the day you find out whether the previous five were real.

The plan's Phase-3 gate says:

> **a long-horizon file-touching agent runs on free models inside the local Docker sandbox, plus a
> one-page written explainer of the paid harness/sandbox good enough to give in an interview.**

Read that sentence as four separate claims, because that is how you will have to defend it:

1. **long-horizon** — the job is bigger than one context window and more than one turn
2. **file-touching** — it produces artifacts on disk, not just text in a terminal
3. **inside the local Docker sandbox** — the code it writes runs somewhere it cannot do harm
4. **on free models** — $0, and therefore inside rate limits you must actually respect

Every one of those was built on a different day. Today you find out whether they compose.

**And here is the thing gate days actually teach: composition is where systems break.** Each part
passed its own tests. Day 19's sandbox refuses network. Day 20's workflow resumes. Day 21's policy
refuses unapproved writes. None of that guarantees they work *together* — the sandbox is read-only
but a file-touching agent must write; the workflow retries but a retried write must not double; the
policy asks a human but a long-horizon run may have no human awake. Those three sentences are the
whole day, and you resolve each one deliberately rather than by discovering it at 6pm.

There is one more thing today asks of you, and it is the part people skip: **you have to widen the
blast radius on purpose.** A file-touching agent needs somewhere to write. Day 19's box mounts data
read-only, and that was correct for running analysis code. Today's job cannot be done under that
rule, so you change the rule — narrowly, deliberately, and with the justification written down. That
is what engineering a permission looks like, as opposed to loosening one.

---

## §2 Setup — run this

**No new packages.** Everything today needs was installed between Day 9 and Day 20. If you find
yourself reaching for one, stop: a gate day that needs a new dependency is a gate day that is
smuggling in new work.

```bash
mkdir -p days/day-22/lab
mkdir -p docs/adr
touch src/mandala/workspace.py
touch days/day-22/lab/long_run.py
touch days/day-22/lab/gate_evidence.py
touch tests/test_workspace.py
touch tests/test_gate_phase3.py
```

Confirm the machinery from the last three days is actually alive before you build on it:

```bash
docker run --rm hello-world                       # Day 19: the box exists
temporal server start-dev --db-filename .mandala/temporal.db --ui-port 8233 &
uv run pytest -q -m "not docker and not temporal"  # everything that runs without either
uv run python days/day-14/lab/span_tree.py         # Day 14: you can still read a trace
```

**If any of those four fail, today is a repair day, not a gate day.** That is a legitimate outcome
and you should record it as one — a gate you passed by lowering the bar is worth nothing, and you
are the only person who will ever check.

---

## §3 The artifact — a long-horizon agent that touches files

### 3.1 The job

The task has to be genuinely too big for one turn, or "long-horizon" is a word you are using to
describe a demo. So:

> **Read every ticket in the fixture set. Write one analysis file per ticket. Then write a rollup
> report that cites the per-ticket files. Do it inside the sandbox. Survive a kill.**

Eleven tickets (T-1001…T-1010 plus T-9002), each producing a file, plus a rollup — that is a dozen
artifacts and dozens of steps. It will not fit in one context window, which is the point. It is also
the shape of a real support-ops job, which is why Mandala has been building toward it since Day 1.

### 3.2 The blast-radius decision, made explicitly

Day 19's sandbox mounts data **read-only** (`mode="ro"`). A file-touching agent must write. You have
three options and you should be able to say why you rejected two of them:

| Option | What it buys | Why not |
|---|---|---|
| Keep the mount read-only; return file contents as tool output and let the **host** write them | no widening at all | the model's output becomes the file; you lose the ability for generated *code* to produce artifacts, which is the whole point of a sandbox |
| Mount the whole project read-write | trivially easy | the agent can rewrite your source, your tests, and your git history. Absolutely not |
| **Mount exactly one workspace directory read-write, and nothing else** | the job becomes possible | **this is the answer** — the widening is one directory, per run, and disposable |

**The rule: widen the smallest thing that makes the task possible, and write down why.** Then make
the widening structurally narrow — a fresh directory per run, under `.mandala/` (gitignored since
Day 14), named by run id, with the rest of the filesystem untouched and the network still off.

### 3.3 `src/mandala/workspace.py`

```python
"""A disposable, per-run directory: the only place anything today is allowed to write.

Why this file exists
--------------------
Day 19's sandbox mounts data read-only, which was right for analysis code and is
wrong for a file-touching agent. Rather than loosening that rule, this module
creates ONE writable directory per run and hands out paths inside it. The sandbox
mounts this and nothing else; the network stays off; credentials still never enter.

The widening is: one directory, one run, disposable. Everything else Day 19
established is unchanged, and tests/test_workspace.py asserts that.

Usage
-----
    >>> ws = Workspace.for_run("req-gate-001")
    >>> ws.path.name
    'req-gate-001'
    >>> ws.resolve("report.md").parent == ws.path
    True
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

WORKSPACE_ROOT = Path(".mandala/workspace")

# A run id becomes a directory name. Anything outside this set is a path smuggled
# in as an identifier, so it is rejected rather than sanitised.
SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

MAX_FILES = 40
MAX_FILE_BYTES = 200_000


class WorkspaceViolation(RuntimeError):
    """An attempt to touch something outside the one directory we opened."""


@dataclass(frozen=True)
class Workspace:
    """One run's writable world. Nothing outside `path` is reachable through this object."""

    path: Path

    @classmethod
    def for_run(cls, run_id: str, root: Path = WORKSPACE_ROOT) -> "Workspace":
        if not SAFE_RUN_ID.match(run_id):
            raise WorkspaceViolation(f"unsafe run id {run_id!r}")
        path = root / run_id
        path.mkdir(parents=True, exist_ok=True)
        return cls(path=path.resolve())

    def resolve(self, name: str) -> Path:
        """Turn a requested filename into a real path, or refuse."""
        candidate = (self.path / name).resolve()
        if not candidate.is_relative_to(self.path):
            raise WorkspaceViolation(f"{name!r} escapes the workspace")
        return candidate

    def write(self, name: str, text: str) -> Path:
        if len(self.files()) >= MAX_FILES:
            raise WorkspaceViolation(f"workspace already holds {MAX_FILES} files")
        payload = text.encode("utf-8")
        if len(payload) > MAX_FILE_BYTES:
            raise WorkspaceViolation(f"{name!r} is {len(payload)} bytes; cap is {MAX_FILE_BYTES}")
        target = self.resolve(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        return target

    def files(self) -> list[Path]:
        return sorted(p for p in self.path.rglob("*") if p.is_file())

    def destroy(self) -> None:
        shutil.rmtree(self.path, ignore_errors=True)


def mount_spec(ws: Workspace) -> dict:
    """The docker mount for this workspace. The ONLY read-write mount in the system.

    TODO(me): make this agree with Day 19's container_kwargs(). If Day 19 named the
    mount target something else, one of the two is wrong and the tests will not
    catch it for you -- the container will just fail to find the directory.
    """
    raise NotImplementedError
```

**Line by line:**

- `WORKSPACE_ROOT = Path(".mandala/workspace")` — under the directory you gitignored on Day 14, so
  a run's artifacts can never be committed by accident. The same instinct as trace files: **output
  that a process generates does not belong in source control.**
- `SAFE_RUN_ID` **rejects rather than sanitises.** A sanitiser that strips `../` invites you to
  wonder whether it stripped enough; a regex that only admits known-good characters has no such
  question. This is the allowlist-not-denylist rule for the third time (Day 14's span fields, Day
  15's search ops, now paths) — by now it should feel automatic.
- `raise WorkspaceViolation(f"unsafe run id {run_id!r}")` — the run id arrives from *your* code
  today, and from a caller you do not control eventually. Validate at the boundary anyway.
- `def resolve(...)` with `.resolve()` then `.is_relative_to(self.path)` — **this is the path
  traversal check, and the order matters.** You must resolve symlinks and `..` *first*, then ask
  whether the real destination is inside. Checking the string before resolving is the classic
  mistake: `workspace/../../etc/passwd` starts with `workspace/`.
- `MAX_FILES` and `MAX_FILE_BYTES` — a long-horizon agent that loops will fill your disk. Caps turn
  "the laptop died overnight" into "the run stopped with a clear error". Day 4's context budget, the
  same idea applied to storage.
- `def destroy()` — disposability is a feature. A workspace you can delete without thinking is a
  workspace you will actually clean up.
- `mount_spec` is a `TODO(me)`, and the docstring says exactly why it is dangerous to guess: **this
  is the one place where today's code has to agree with Day 19's, and no test can tell you it does
  not** — you get a container that starts fine and cannot find its directory. Go read your own
  `container_kwargs()` and make them match. That five-minute cross-check is the rep.

### 3.4 The three composition problems, and how you resolve each

This is the section to read slowly. Each row is a place where two days' correct decisions collide.

| Collision | Day A says | Day B says | Resolution |
|---|---|---|---|
| **Writes vs. read-only** | Day 19: mounts are read-only | today: the agent must write files | one workspace, read-write, per run (§3.2) — nothing else changes |
| **Retries vs. one-effect** | Day 20: activities retry | Day 6: an effect must happen once | writes are **idempotent by path** — the same step writing the same file twice is a no-op, not a duplicate. Deriving the filename from the ticket id rather than from a counter is what makes this true |
| **Approvals vs. unattended runs** | Day 21: writes need a human | today: the run may be long and nobody is watching | **classify by consequence, not by "is it a write".** Writing to a disposable workspace is not an external side effect; it is scratch. `post_reply` still stops and waits. The rule: *approval gates guard consequences that leave the building*, and the workspace never leaves |

**That third row is the most important idea on this page.** It is easy to write a policy that says
"all writes need approval", feel safe, and then discover your long-horizon agent stops eleven times
to ask permission to save a scratch file. The person clicking approve learns to click approve
without reading, and now your gate is worse than useless (Day 21's approval fatigue). **A gate that
fires on scratch is a gate that will be ignored when it fires on something real.**

So the workspace write is *not* gated, and the reason is written down: it is disposable, local,
inside a directory that is gitignored, capped in size and count, and destroyed at the end. If any of
those five stopped being true, the classification would have to change.

### 3.5 `days/day-22/lab/long_run.py`

```python
"""The Phase-3 gate artifact: a long-horizon, file-touching, sandboxed, resumable run.

Nothing here is new. It is Day 14's tracing, Day 18's coordinator, Day 19's sandbox,
Day 20's durability and Day 21's policy, wired together and pointed at eleven tickets.

Run:
    uv run python days/day-22/lab/long_run.py                  # all tickets
    uv run python days/day-22/lab/long_run.py --tickets 3      # a short rehearsal first
"""

from __future__ import annotations

import argparse
import asyncio
import json

from agents import Runner

from mandala.context import MandalaContext
from mandala.topologies import researcher
from mandala.tracing import install_local_tracing
from mandala.workspace import Workspace

RUN_ID = "gate-phase3"


def ticket_ids(limit: int | None) -> list[str]:
    """TODO(me): read the ids from the fixture file rather than hard-coding them.

    Hard-coding eleven ids works today and rots the moment you add a fixture. The
    rep is small and the habit is the point.
    """
    raise NotImplementedError


async def analyse_one(ticket_id: str, ws: Workspace, context: MandalaContext) -> str:
    """One ticket -> one file. Idempotent by path: rerunning overwrites, never duplicates."""
    name = f"tickets/{ticket_id}.md"
    target = ws.resolve(name)
    if target.exists():
        print(f"  {ticket_id}: already done, skipping")     # this line is why a kill is survivable
        return name

    result = await Runner.run(
        researcher(),
        f"Research ticket {ticket_id}. Summarise findings; cite ticket ids.",
        context=context,
        max_turns=8,
    )
    brief = result.final_output
    ws.write(name, f"# {ticket_id}\n\n{brief.model_dump_json(indent=2)}\n")
    print(f"  {ticket_id}: written")
    return name


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickets", type=int, default=None)
    args = parser.parse_args()

    install_local_tracing()
    ws = Workspace.for_run(RUN_ID)
    context = MandalaContext(actor="agent:researcher", request_id=RUN_ID)

    written: list[str] = []
    for ticket_id in ticket_ids(args.tickets):
        written.append(await analyse_one(ticket_id, ws, context))

    rollup = "\n".join(f"- [{n}]({n})" for n in written)
    ws.write("report.md", f"# Mandala — phase-3 gate run\n\n{rollup}\n")

    print(f"\n{len(written)} analyses + 1 rollup in {ws.path}")
    print(json.dumps({"files": [p.name for p in ws.files()]}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- `if target.exists(): return name` — **four lines that make the whole run resumable**, and they do
  it without Temporal, without a checkpoint file, and without any state you have to keep consistent.
  The filesystem *is* the checkpoint. Kill the process at ticket seven, run it again, and it does
  four tickets' worth of work instead of eleven. Compare with Day 20's machinery and notice the
  trade honestly: this is cruder, has no retry policy, no history and no visibility — but for a job
  whose steps are naturally keyed by a stable id, it is a great deal of durability for four lines.
  **Knowing when you need the engine and when you need an `if` is the senior version of Day 20.**
- Deriving `name` from `ticket_id` rather than from a loop counter — that is what makes the skip
  correct. A counter-derived name (`analysis_07.md`) would resume into a different file after a
  partial run and quietly produce duplicates. **The idempotency key is the ticket id** (Day 6), and
  here it is spelled as a path.
- `--tickets 3` — **rehearse on three before you run eleven.** On a free tier a full run is a real
  slice of your daily budget (Principle 5), and the mistake you make will be in the wiring, not in
  ticket nine.
- `researcher()` from `topologies.py` — the read-only agent, unchanged since Day 14. Note what is
  *not* here: no `run_code`, no write tool, no `post_reply`. The long-horizon agent that reads
  untrusted ticket text still holds no dangerous capability, eight days later.
- `install_local_tracing()` — the run must be traceable, because §4's evidence table asks for a span
  tree and "it worked" is not evidence.
- `ws.write(...)` rather than `open(...)` — every write goes through the capped, path-checked
  object. If it does not, the guarantees in §3.3 are decoration.

### 3.6 The kill test

Do this exactly, and record what you see:

```bash
uv run python days/day-22/lab/long_run.py          # let it write 4 or 5 files, then Ctrl-C
ls .mandala/workspace/gate-phase3/tickets/         # count them
uv run python days/day-22/lab/long_run.py          # run it again
```

The second run must print `already done, skipping` for everything the first run finished, and only
pay for the rest. **Write the two numbers in your CHECKLIST** — files completed before the kill, and
model calls made by the second run. If the second run costs the same as the first, your resumption
is decorative and you have not passed this criterion.

---

## §4 The gate

### 4.1 Evidence, not assertion

A gate is passed with commands and their output. For each row, run the command, paste or summarise
what it printed, and mark it honestly. **A criterion you cannot produce evidence for is a criterion
you failed**, and recording that is worth far more than a green table you do not believe.

| # | Criterion | Command that produces the evidence | Pass? |
|---|---|---|---|
| 1 | The run is long-horizon — many steps, more than one context | `long_run.py` finishes; count files | ⬜ |
| 2 | It touches files | `ls .mandala/workspace/gate-phase3/` | ⬜ |
| 3 | Artifacts are inside the workspace and nowhere else | `git status --short` is clean | ⬜ |
| 4 | Generated code runs in the Docker sandbox | `days/day-19/lab/sandbox_demo.py` | ⬜ |
| 5 | The sandbox refuses network, writes outside the mount, and long loops | `days/day-19/lab/escape_attempts.py` | ⬜ |
| 6 | No container survives the run | `docker ps -a --filter label=mandala.sandbox` is empty | ⬜ |
| 7 | It runs on free models only | `grep -rn "OPENAI_API_KEY" src/ days/` returns nothing | ⬜ |
| 8 | The run is traced end to end | `days/day-14/lab/span_tree.py` | ⬜ |
| 9 | Model-call count is known and within budget | `model_calls()` from the trace | ⬜ |
| 10 | A kill mid-run resumes rather than restarts | §3.6, both numbers recorded | ⬜ |
| 11 | Guardrails still trip | `days/day-21/lab/policy_demo.py` | ⬜ |
| 12 | Permissions still hold; no trifecta | `pytest tests/test_permissions.py -q` | ⬜ |
| 13 | Approvals still gate external writes | the `post_reply` row of the Day-21 battery | ⬜ |
| 14 | The suite is green with no Docker and no Temporal | `pytest -q -m "not docker and not temporal"` | ⬜ |
| 15 | The harness explainer exists and reads well cold | §4.2 | ⬜ |

**Row 7 deserves a second look.** Grepping for the string is the cheap version. The real check is
that you can unplug every paid path and the system still runs, which has been true since Day 9 and
is worth confirming rather than assuming.

### 4.2 The harness explainer

The plan asks for **"a one-page written explainer of the paid harness/sandbox good enough to give in
an interview."** You drafted it on Day 19 at `docs/explainers/paid-harness-and-sandbox.md`. Today you
finish it and then do the thing that makes it real: **read it cold, out loud, a day later.**

It has to answer these, in your words, in about a page:

- What the model-native harness actually provides — the three opinions (filesystem, memory,
  execution environment) and why an SDK grew them.
- What the native sandbox guarantees, and what it does not.
- What you built instead, and the honest list of what yours does worse.
- What yours does *better*, which is not nothing: you can read every flag, test every guarantee
  without a daemon, and change any of it.
- When you would pay for theirs. **An explainer with no "I would buy it when…" paragraph reads as
  defensiveness rather than judgement**, and interviewers hear the difference immediately.

Do not let this be a summary of documentation. The value is that you built the free version and can
compare from experience — that is the sentence that makes it interview-grade.

### 4.3 The freshness check (Principle 13)

A gate includes a freshness pass. Re-verify every pin in `docs/PINS.md` and the MCP spec revision:

```bash
for p in openai-agents openai litellm mcp temporalio docker ddgs rich; do
  curl -s "https://pypi.org/pypi/$p/json" \
    | python -c "import sys,json;d=json.load(sys.stdin);print('$p', d['info']['version'])"
done
```

Report each as **unchanged / changed-cosmetic / changed-material**. A patch bump is one line in
`docs/CHANGELOG_PLAN.md`. A minor or major bump means: stop, read the release notes, write an
addendum, *then* pin (Principle 14). **"Checked, unchanged" is a real result** — write it down, or
in three weeks you will not know whether you checked.

While you are there, clear what you can from the **Open verification items** table at the bottom of
`docs/CHANGELOG_PLAN.md`. Two of those rows have been open since Day 14 and one of them silently
affects a number you are about to quote in an interview.

### 4.4 `docs/adr/gate-phase-3.md`

If the gate passes, write the record. Use `docs/adr/ADR-TEMPLATE.md` and keep it short — the
evidence table plus what you learned. Then:

```bash
git tag phase-3-complete
```

Two things belong in the "Consequences" section and are easy to leave out:

- **What you would not do again.** Six days of Phase 3 produced one thing you now think was a
  mistake. Name it while you remember.
- **What is still unproven.** You have not run this for eight hours. You have not run it against a
  ticket that is genuinely adversarial. Say so — a gate record that claims more than it tested is
  the document that embarrasses you later.

### 4.5 If the gate fails

Then it fails, and you write that down instead. The honest failure modes at this point are:

| Symptom | Likely cause | Where to look |
|---|---|---|
| second run costs as much as the first | filename derived from a counter, not the ticket id | §3.5 |
| container cannot find the workspace | `mount_spec` disagrees with Day 19's `container_kwargs` | §3.3 `TODO(me)` |
| the run asks for approval eleven times | workspace writes classified as external side effects | §3.4 |
| `model_calls()` reports 0 | the span-type question from Day 14 §8, still open | §4.3 |
| suite red without Docker | a test missing its marker | Day 19 §5 |

**Do not tag a failed gate.** The tag is the only cheap signal your future self has.

---

## §5 The eval that must be able to fail

### `tests/test_workspace.py`

```python
"""The one widened permission in the system. Every boundary of it is asserted."""

import pytest

from mandala.workspace import MAX_FILES, Workspace, WorkspaceViolation


def test_a_run_id_that_is_a_path_is_refused():
    """Reject, do not sanitise. FLIP IT: strip '../' instead and watch this pass wrongly."""
    with pytest.raises(WorkspaceViolation):
        Workspace.for_run("../../etc")


def test_a_filename_that_escapes_is_refused(tmp_path):
    ws = Workspace.for_run("r1", root=tmp_path)
    with pytest.raises(WorkspaceViolation):
        ws.resolve("../../secrets.txt")


def test_a_symlink_cannot_be_used_to_escape(tmp_path):
    """The check resolves BEFORE comparing. This is why the order matters."""
    ws = Workspace.for_run("r1", root=tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("x", encoding="utf-8")
    (ws.path / "link").symlink_to(outside)
    with pytest.raises(WorkspaceViolation):
        ws.resolve("link")


def test_file_count_is_capped(tmp_path):
    ws = Workspace.for_run("r1", root=tmp_path)
    for i in range(MAX_FILES):
        ws.write(f"f{i}.txt", "x")
    with pytest.raises(WorkspaceViolation):
        ws.write("one-too-many.txt", "x")


def test_file_size_is_capped(tmp_path):
    ws = Workspace.for_run("r1", root=tmp_path)
    with pytest.raises(WorkspaceViolation):
        ws.write("big.txt", "x" * 300_000)


def test_writing_the_same_path_twice_is_one_file(tmp_path):
    """Idempotent by path — the property that makes §3.6's resume correct."""
    ws = Workspace.for_run("r1", root=tmp_path)
    ws.write("a.md", "first")
    ws.write("a.md", "second")
    assert len(ws.files()) == 1
    assert ws.resolve("a.md").read_text(encoding="utf-8") == "second"


def test_destroy_removes_everything(tmp_path):
    ws = Workspace.for_run("r1", root=tmp_path)
    ws.write("a.md", "x")
    ws.destroy()
    assert not ws.path.exists()
```

### `tests/test_gate_phase3.py`

```python
"""Gate criteria that can be checked without running anything expensive."""

from pathlib import Path

import pytest

from mandala.permissions import AGENTS, TOOLS, trifecta_violations


def test_no_agent_holds_untrusted_input_and_write_ability():
    """The invariant the whole plan is built around. Still []."""
    assert trifecta_violations() == []


def test_the_long_run_agent_has_no_write_tool():
    """A long-horizon agent reading untrusted text is the worst place to grant a write."""
    from mandala.topologies import researcher

    for tool in researcher().tools:
        spec = TOOLS.get(getattr(tool, "name", ""))
        assert spec is None or not spec.writes


def test_workspace_writes_are_not_classified_as_external_side_effects():
    """§3.4 row three, asserted. If this flips, the run will stop to ask eleven times."""
    assert "workspace_write" not in TOOLS, (
        "a workspace write is scratch, not a tool with a blast radius"
    )


def test_no_paid_provider_is_referenced_anywhere():
    """Principle 5, as a grep you cannot forget to run."""
    offenders = []
    for path in Path("src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "OPENAI_API_KEY" in text or "api.openai.com" in text:
            offenders.append(str(path))
    assert offenders == []


def test_the_explainer_exists_and_is_about_a_page():
    """A gate artifact that does not exist is a gate you did not pass."""
    explainer = Path("docs/explainers/paid-harness-and-sandbox.md")
    assert explainer.exists(), "Day 19 asked you to draft this"
    words = len(explainer.read_text(encoding="utf-8").split())
    assert 300 <= words <= 1200, f"{words} words — a page, not a paragraph and not an essay"


@pytest.mark.skip(reason="TODO(me): assert the resumed run costs strictly fewer model calls")
def test_resuming_costs_less_than_starting():
    """The §3.6 property, as a test. You need two traces and Day 14's model_calls()."""
```

**Line by line:**

- `test_a_run_id_that_is_a_path_is_refused` — with the flip written into the docstring. Replace the
  regex with a sanitiser and watch how comfortable the wrong version feels.
- `test_a_symlink_cannot_be_used_to_escape` — **the test most people do not write**, and the one that
  proves the resolve-then-compare order was deliberate. If you wrote the check the other way round,
  this is the only test in the file that catches it.
- `test_writing_the_same_path_twice_is_one_file` — the durability property of §3.6, asserted at the
  level where it is actually decided. The resume behaviour in `long_run.py` is a consequence of this,
  not an independent feature.
- `test_workspace_writes_are_not_classified_as_external_side_effects` — an unusual test that encodes
  a *decision* rather than a behaviour, with the reason in the assertion message. When someone adds
  `workspace_write` to the permission table in six weeks because it seems tidier, this tells them
  what they are about to break.
- `test_the_explainer_exists_and_is_about_a_page` — checking a written artifact from a test feels
  like cheating and is not: the gate says the explainer is required, and a required artifact with no
  check is an artifact that goes missing. The word bounds are deliberately loose; they catch "I left
  the template headings in", not style.
- The final test **ships skipped with a `TODO(me)`.** A skip with a reason is an honest open item; a
  missing test is an open item you will forget. Day 9 shipped a deliberately-failing test for the
  same reason.

---

## §6 Traps

- **Classifying scratch writes as external side effects.** Your long-horizon run stops eleven times,
  a human learns to approve without reading, and the gate that guards `post_reply` is now noise.
  **The trap of the day**, and it is a design error, not a bug.
- **Mounting the project read-write "just to get it working".** The agent can now edit its own
  tests. There is no smaller version of this mistake.
- **Checking the path string before resolving it.** `workspace/../../etc/passwd` starts with
  `workspace/`. Resolve first, compare second.
- **Filenames derived from a counter.** Resumption silently produces duplicates, and the run looks
  like it worked.
- **Running eleven tickets before rehearsing three.** You will find the wiring bug on ticket one and
  pay for it eleven times.
- **`mount_spec` and Day 19's `container_kwargs` disagreeing.** No test catches it; the container
  just cannot find its directory. Cross-check them by eye.
- **Passing the gate by narrowing it.** "It's long-horizon if you squint" is how a gate becomes a
  formality. You are the only reviewer, which cuts both ways.
- **Tagging a gate you did not pass.** The tag is your future self's only cheap signal.
- **Skipping the freshness check because nothing feels stale.** "Checked, unchanged" is the result
  you are producing; the point is the record, not the surprise.
- **Leaving the workspace on disk between runs while debugging.** Every run resumes into stale
  artifacts and you debug a ghost. `destroy()` exists — use it when you change the format.
- **Writing the explainer as a documentation summary.** Its value is that you built the free version.
  If it has no "I would buy theirs when…" paragraph, it reads as defensiveness.
- **Treating a green table as the deliverable.** The deliverable is a system you would defend. The
  table is how you check.

---

## §7 Request budget

| Activity | Requests |
|---|---|
| Rehearsal — `long_run.py --tickets 3` | ~15 (Groq) |
| Full run — eleven tickets | ~55 (Groq) |
| The kill test — partial first run + resumed second | ~25 (Groq) |
| Day-21 policy battery (row 11, 13) | ~9 |
| Wiring iteration | ~20 |
| **Total** | **≈ 124, Groq** |

**This is the most expensive day of the plan so far, and it is worth flagging as a planning lesson
rather than an accident:** gate days cost more than lesson days because they re-run everything. If
124 requests is more than ~10% of your Groq daily allowance (`docs/RATE_BUDGET.md` rule 3), **split
the gate across two sittings** — the artifact in one, the evidence table and freshness check in the
other. Splitting a gate is legitimate; quietly running a smaller gate is not.

Rows 3, 5, 6, 7, 12, 14 and every test in §5 cost **0 model requests** — seven of fifteen criteria
are free, because the properties they check live in data structures and config rather than in model
behaviour. That is not luck; it is the payoff for thirteen days of putting decisions in testable
places.

---

## §8 Verify before you code

Written **2026-08-20** against `openai-agents` **0.22.0**, `docker` **7.2.0**, `temporalio`
**1.31.0**.

- Nothing new to learn today — but re-read your own **Day 19 §4** before writing `mount_spec`, and
  your own **Day 21 §3** before deciding what the policy does with a workspace write. Today's bugs
  live in the seams between days, not in an API.
- `pathlib.Path.is_relative_to` — confirm the behaviour you expect on Windows, since that is where
  this project runs. Path semantics differ, and a traversal check that is correct on POSIX and loose
  on Windows is worse than none.
- Run the §4.3 freshness loop and record results in `docs/CHANGELOG_PLAN.md`.
- **Clear the open verification items** in `docs/CHANGELOG_PLAN.md` while you have the machinery
  running — especially whether the model call produces a **generation** or a **response** span,
  because criterion 9 quotes a number that depends on it.
- If a pin moved materially, write the addendum before you tag (Principle 14). A gate tagged on top
  of unlogged drift is a gate that lies.

---

## §9 Say it in an interview

> "Phase three ended with a gate: a long-horizon, file-touching agent running on free models inside
> a local Docker sandbox. The interesting part wasn't the agent — it was the three places where
> decisions from different days collided. My sandbox mounted data read-only, but a file-touching
> agent has to write, so I widened exactly one directory per run instead of loosening the rule. My
> workflow retried, but retries can double-write, so file names are derived from the ticket id and
> a rerun is a no-op. And my policy said writes need human approval, which would have made an
> unattended run stop eleven times to approve scratch files — so I reclassified: approval gates
> guard consequences that leave the building, and a disposable local workspace doesn't."

> "The resumption is the bit I'd defend hardest, because it's four lines: if the output file for a
> ticket already exists, skip it. I'd built a whole Temporal workflow two days earlier, and for this
> job the filesystem was the checkpoint — the work is keyed by a stable id, so the artifact *is* the
> state. I killed the run at ticket five, restarted it, and the second run cost about half the first.
> Knowing when you need a durable execution engine and when you need an `if` statement is most of
> what durability engineering actually is."

---

## §10 Done when

```bash
./m check
./m done 22
git tag phase-3-complete        # only if the evidence table is honestly green
```

Phase 3 is finished. Tomorrow the plan changes shape: **CrewAI**, and the second answer to the
question the whole plan hangs on — *who owns the loop?* The Agents SDK said the model owns it. CrewAI
says **roles** own it. Notice, from the first hour, how much of what you built by hand for thirteen
days arrives as a default — and keep a list, because Day 59's bake-off is decided by matrix, not by
whichever framework you met most recently.
