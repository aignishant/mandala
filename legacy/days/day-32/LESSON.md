---
day: 32
phase: 5
phase_name: "CrewAI Flows"
title: "Persistence and checkpoint restore"
ids: ["CR-18"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 32 — Persistence and checkpoint restore

**Phase 5 · CrewAI Flows** · IDs: **CR-18 🛠️**

> **Yesterday:** the flow grew branches, and one branch spends twenty requests inside an autonomous
> crew.
> **Today:** that becomes survivable. `@persist` writes state after every step, so a process killed
> mid-crew resumes instead of paying for those twenty requests again.
> **Tomorrow:** a human is allowed to *stop* the flow on purpose — which only works because of today.

```bash
./m start 32
./m scaffold 32
```

---

## §1 The story

Yesterday's deep lane costs about twenty model requests. Today, ask the question that makes
persistence a budget feature rather than an ops feature:

**What happens if the process dies at request nineteen?**

Without persistence: you pay all twenty again. On Groq's 1000 RPD that is annoying. On OpenRouter's
50 RPD (`docs/RATE_BUDGET.md` §1) it is 40% of your day, twice, for one ticket. **On a free tier,
durability is not a production nicety — it is how you afford to develop at all.**

This is **AG-27** — durable execution — meeting its first real implementation in this plan. The plan
lists four:

| Framework | Mechanism | Granularity | Day |
|---|---|---|---|
| **CrewAI Flows** | **`@persist` + checkpoint restore** | **per step** | **today** |
| OpenAI Agents SDK | Temporal workflow | per activity | 20 |
| LangGraph | checkpointers | per super-step | 47, 49 |
| MCP | Tasks extension (task handles) | per task | 57 |

Today is the *cheapest* of the four to adopt — one decorator — and that cheapness is the interesting
part. When durability costs one line, the question stops being "is this worth persisting?" and
becomes "what did I just persist, and who can read it?" That second question is the one this lesson
spends its length on, because Day 30 already told you: **state is global to the run**, and now it is
also *global to disk*.

There is also a version-specific correctness story here worth your attention. The plan's CR-18 row
flags it: *"resume gated by flag — a 1.14/1.15 correctness fix worth reading."* Resuming by default
sounds helpful and is dangerous: a flow that silently picks up a stale checkpoint from three days ago
will happily skip your new step. §4 makes you meet that behaviour on purpose.

---

## §2 Setup — run this

### 2.1 No new packages

```bash
grep -n 'crewai' pyproject.toml
```

- `@persist` and its SQLite backend ship inside `crewai==1.15.17`. Nothing to add.
- **If your run creates a database file you did not ask for, that is today's most important
  observation.** Find out where it landed *before* you commit anything (§2.3).

### 2.2 Create today's files

```bash
touch src/mandala/flows/persistence.py
touch tests/test_persistence.py
mkdir -p days/day-32/lab
touch days/day-32/lab/kill_and_resume.py
touch days/day-32/lab/inspect_checkpoints.py
```

- `persistence.py` holds the storage decision — *where* checkpoints live, *what* is scrubbed before
  they are written, and *how long* they are kept. Those are three policy questions and they do not
  belong scattered through `intake.py`.
- `inspect_checkpoints.py` is the file that makes today honest. A checkpoint you have never read is a
  claim, not a capability.

### 2.3 Make sure the checkpoint store is ignored **before** it exists

```bash
grep -n '^\.mandala/$' .gitignore && echo "SAFE" || echo "STOP - add .mandala/ to .gitignore"
```

- Same move as Day 1's `.env` check, and for the same reason. **Checkpoints contain flow state, and
  flow state has contained a raw customer ticket body at least once per run.** A checkpoint database
  committed to git is a customer-data leak with a permanent home.
- Add `.mandala/` to `.gitignore` if that printed STOP, and do it now — not after the first run.
- Then check the default location too: some versions write `db_storage/` or a file in the CWD. If a
  run produces an untracked file anywhere, it goes in `.gitignore` in the same commit.

---

## §3 CR-18 — `@persist`, and where state actually goes

### 3.1 The decorator, and the two places it can go

```python
from crewai.flow.persistence import persist
```

`@persist` can decorate either:

- **the flow class** — every step's completion checkpoints the whole state, or
- **a single method** — only that step's completion checkpoints.

Mandala uses the **class-level** form, and the reason is yesterday's shape. The expensive thing is
`deep_research`, and a checkpoint taken *after* the organ finishes is worth twenty requests. But a
checkpoint after `classify` is worth one, and a checkpoint after `route` is worth zero and still
useful, because it records **which lane the run took** before it died. Cheap insurance on the cheap
steps, real savings on the expensive one.

### 3.2 `src/mandala/flows/persistence.py`

```python
"""Where flow checkpoints live, what is scrubbed out of them, and for how long.

Three policy questions, one file
--------------------------------
@persist is one decorator, which makes it easy to adopt without deciding anything.
That is the trap. A checkpoint is a copy of MandalaState on disk, and MandalaState
has held raw customer text (Day 30 §4.4). So before turning it on, decide:

  1. WHERE   - not the repo, not a temp dir that a reboot clears mid-run.
  2. WHAT    - scrub anything that must not outlive the process.
  3. HOW LONG- a checkpoint store with no expiry is a growing pile of ticket data.

Usage
-----
    >>> from mandala.flows.persistence import CHECKPOINT_DIR, scrub
    >>> CHECKPOINT_DIR.name
    'flows'
"""

from __future__ import annotations

from pathlib import Path

from mandala.flows.state import MandalaState

#: Repo-local, git-ignored, and stable across reboots. Not /tmp -- see §3.3.
CHECKPOINT_DIR = Path(".mandala") / "flows"
CHECKPOINT_DB = CHECKPOINT_DIR / "checkpoints.sqlite"

#: Fields that must never reach disk, whatever a future step puts in them.
NEVER_PERSIST = frozenset({"ticket_body"})

#: A checkpoint older than this is stale: resuming it would skip steps you have
#: since added. Day 33's human pauses need hours, not days.
MAX_CHECKPOINT_AGE_HOURS = 24


def ensure_store() -> Path:
    """Create the checkpoint directory. Idempotent, safe to call on every run."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    return CHECKPOINT_DB


def scrub(state: MandalaState) -> MandalaState:
    """Return a copy of state with the never-persist fields cleared.

    Belt and braces: Day 30's drop_body() should already have removed the body
    before any expensive step runs. This makes the guarantee hold even for a run
    that dies BETWEEN load and drop_body -- the one window where the body is
    legitimately in state and a crash could freeze it there forever.
    """
    return state.model_copy(update={name: None for name in NEVER_PERSIST})
```

**Line by line:**

- `CHECKPOINT_DIR = Path(".mandala") / "flows"` — repo-local so it survives reboots and is trivially
  findable, `.`-prefixed so it reads as machinery, and git-ignored per §2.3. **Not `/tmp`:** a
  temp-dir checkpoint is deleted by exactly the kind of event you adopted persistence to survive.
- `Path(...) / "flows"` — the `/` operator on `Path` joins path segments and gets the separator right
  on Windows and Linux both. You will run this on Windows; `os.path.join` semantics matter.
- `NEVER_PERSIST` as a **frozenset of field names**, not an inline check. A future step that adds
  `raw_attachment` should be one entry here, not a new code path.
- `MAX_CHECKPOINT_AGE_HOURS = 24` — an explicit staleness policy, and the number is a judgement you
  should be able to defend: long enough for tomorrow's human approval step to be slow, short enough
  that a checkpoint written before today's code change cannot resume into it.
- `ensure_store()` returns the path and is idempotent — `exist_ok=True` means calling it every run is
  free. Functions that are safe to call repeatedly are functions nobody has to remember to call once.
- `scrub()` uses `model_copy(update=...)` — Pydantic's **copy-with-changes**, which returns a new
  object rather than mutating the live state. Mutating here would be a real bug: you would be
  deleting the body from the *running* flow to protect the *stored* one.
- The docstring names the exact window the scrub exists for: **a crash between `load` and
  `drop_body`.** That window is milliseconds wide and it is the only moment the body is legitimately
  in state. Persistence turns a millisecond of exposure into a file that lives until you delete it —
  which is precisely the kind of amplification Principle 6 asks you to look for.

### 3.3 Wiring it into `intake.py`

```python
from crewai.flow.persistence import persist

from mandala.flows.persistence import ensure_store


@persist()
class IntakeFlow(Flow[MandalaState]):
    """A typed state machine you can read top to bottom -- and now, restart."""

    def __init__(self, *args, **kwargs) -> None:
        ensure_store()
        super().__init__(*args, **kwargs)
```

**Line by line:**

- `@persist()` **with the parentheses.** It is a decorator factory; `@persist` without them is a
  different (and usually broken) thing. Confirm which form 1.15.17 wants — §8.
- Decorating the **class**, per §3.1, so every step boundary is a checkpoint.
- `ensure_store()` in `__init__` rather than at import time. Import-time filesystem side effects make
  a module impossible to import in a test, in CI, or in a read-only container — and Day 74's CI
  imports everything.
- `super().__init__(*args, **kwargs)` **after** the store exists. `Flow.__init__` may load a
  checkpoint; it cannot load from a directory that is not there yet.
- **Note what is *not* here:** no `id=` argument yet. §4.2 is about the identity question, and it is
  the part people get wrong.

### 3.4 `days/day-32/lab/inspect_checkpoints.py` — 0 model requests

Read your own checkpoints before you trust them.

```python
"""Open the checkpoint store and print what is actually in it.

Run:
    uv run python days/day-32/lab/inspect_checkpoints.py

Budget: 0 requests. This is a filesystem lab.
"""

import json
import sqlite3

from mandala.flows.persistence import CHECKPOINT_DB, NEVER_PERSIST

con = sqlite3.connect(CHECKPOINT_DB)
con.row_factory = sqlite3.Row

tables = [r[0] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type='table'")]
print(f"tables: {tables}\n")

for table in tables:
    rows = list(con.execute(f"SELECT * FROM {table} LIMIT 5"))   # noqa: S608 - local, fixed names
    print(f"--- {table} ({len(rows)} shown) ---")
    for row in rows:
        blob = json.dumps(dict(row))
        for field in NEVER_PERSIST:
            if f'"{field}"' in blob and f'"{field}": null' not in blob:
                print(f"  !! {field} PRESENT IN CHECKPOINT -- scrub() is not wired")
        print("  " + blob[:400])
```

**Line by line:**

- `sqlite3` from the standard library — no dependency, and the checkpoint store is a plain SQLite
  file you are allowed to open. **A durability mechanism you cannot inspect is a durability mechanism
  you cannot audit.**
- `con.row_factory = sqlite3.Row` — makes rows behave like dicts, so `dict(row)` works and the dump
  is readable.
- `SELECT name FROM sqlite_master WHERE type='table'` — the schema query. You did not write this
  schema; the framework did, and today is the day you find out what it decided to store.
- `LIMIT 5` — you want the shape, not the contents of a hundred runs.
- `# noqa: S608 - local, fixed names` — an f-string in SQL is normally an injection smell, and ruff
  is right to flag it. The suppression carries a **reason**, per Day 1's rule: the table names came
  from `sqlite_master` on a local file, not from user input.
- The `NEVER_PERSIST` scan is the point of the whole file: it **greps your own checkpoints for the
  thing that must not be there** and prints a loud line if it is. Run this after your first real
  flow, not after your tenth.
- `blob[:400]` — truncated. You are looking for field names, not reading serialized state by eye.

---

## §4 Resume, and the two ways it goes wrong

### 4.1 `days/day-32/lab/kill_and_resume.py`

This is the Phase-5 gate rehearsal (Day 35: *"kill the process mid-run and resume it on camera"*).

```python
"""Start a deep-lane run, die on purpose inside the crew, then resume.

Run:
    uv run python days/day-32/lab/kill_and_resume.py T-9002 crash
    uv run python days/day-32/lab/kill_and_resume.py T-9002 resume

Budget: ~20 requests for the crash run, ~0-5 for the resume -- and proving that
gap is the entire point of the exercise.
"""

import sys

from mandala.flows.intake import IntakeFlow
from mandala.flows.persistence import CHECKPOINT_DB

ticket_id, mode = sys.argv[1], sys.argv[2]
run_id = f"demo-{ticket_id}"

if mode == "crash":
    flow = IntakeFlow()
    flow.kickoff(inputs={"ticket_id": ticket_id, "id": run_id, "crash_after": "organ"})
elif mode == "resume":
    flow = IntakeFlow()
    state = flow.kickoff(inputs={"id": run_id})
    print(f"trail  {' -> '.join(state.steps)}")
    print(f"stage  {state.stage}")
    print(f"body   {state.ticket_body!r}   <- must be None")
else:
    raise SystemExit("mode must be 'crash' or 'resume'")

print(f"store  {CHECKPOINT_DB}  ({CHECKPOINT_DB.stat().st_size} bytes)")
```

**Line by line:**

- `run_id = f"demo-{ticket_id}"` — **a stable identity is the whole mechanism.** A checkpoint is
  useless unless the resuming process can name the run it wants. Deriving it from the ticket id makes
  the demo reproducible; §4.2 explains why deriving it that way is wrong in production.
- `inputs={"id": run_id}` — CrewAI's persistence keys on an `id` passed through `kickoff` inputs.
  **Confirm the exact key name for 1.15.17 (§8);** if it differs, that is a changelog line, not a
  silent fix.
- `crash_after="organ"` — you add a small hook in `deep_research` that raises after the organ returns
  but before `finish`. Deliberate, targeted, and it costs the twenty requests exactly once. **Do not
  simulate the crash with `Ctrl+C`** the first time: you want the failure at a known step so the
  resume result is interpretable.
- The resume branch passes **only** `{"id": run_id}` — no `ticket_id`. If the resume works, state
  comes back from disk; if you have to pass `ticket_id` again, then you did not resume, you restarted
  with the same input. That distinction is what the printed trail proves.
- `' -> '.join(state.steps)` — the trail should show the *pre-crash* steps followed by the resumed
  ones, in one list. If the trail starts at `load` again, resume did not happen.
- `print(f"body {state.ticket_body!r}")` — the §3.2 scrub, verified after a round trip through disk.
  A security property that holds in memory and not across serialization is not a property.
- `CHECKPOINT_DB.stat().st_size` — watch it grow. This is how the §5 retention test stops being
  abstract.

### 4.2 The identity trap

Deriving the run id from the ticket id is convenient and wrong. Consider:

- The same customer files ticket **T-9002** twice. Second run resumes the first run's checkpoint,
  skips `load`, and answers the new ticket with the old ticket's findings. **Nothing errors.**
- You fix a bug in `classify` and re-run T-9002 to check. It resumes past `classify` and you observe
  the old behaviour, conclude your fix did nothing, and go looking in the wrong place for an hour.

The rule that avoids both:

> **A run id identifies an *attempt*, not a *subject*.**

So: `run_id = f"{ticket_id}:{request_id}"` where `request_id` is generated once per attempt (Day 30's
state already carries one) — or a UUID stored alongside the ticket. Resuming is then something you
ask for by naming a specific attempt, which is what you actually meant. Yesterday's `route_table.py`
demo can stay on the stable id because it never persists; the moment persistence is on, identity is a
correctness question.

### 4.3 The resume-gating fix, and why a flag is the right answer

The plan's CR-18 row points at a **1.14/1.15 correctness fix: resume is gated by a flag.** Earlier
behaviour — resume whenever a checkpoint exists for the id — is the friendlier default and the more
dangerous one, for a reason worth internalising:

**A checkpoint is a snapshot of state under an old version of your code.** Resume replays the
remaining steps of *today's* class using *yesterday's* state. If you added a field, it is missing. If
you renamed a step, the trail lies. If you fixed a routing bug, the stored route is the buggy one.

So the fix makes resume **explicit**: the caller must ask. That converts a class of silent wrong
answers into an error the caller has to handle, which is the same trade Day 1 made with `MissingKey`
and Day 31 made with `raise` instead of `assert`. Three days, three instances of the same principle:
**prefer a loud failure to a quiet wrong answer.**

Your job today is to find out what 1.15.17 actually does — §8 — and write the answer into this
lesson. If it resumes by default, add the gate yourself:

```python
def resume_allowed(state, *, requested: bool) -> bool:
    """Explicit opt-in, plus a staleness check. Both must pass."""
    if not requested:
        return False
    age_hours = checkpoint_age_hours(state)
    return age_hours is not None and age_hours < MAX_CHECKPOINT_AGE_HOURS
```

- `*, requested: bool` — **keyword-only.** `resume_allowed(state, True)` at a call site tells a reader
  nothing; `resume_allowed(state, requested=True)` tells them everything. For a boolean that gates a
  correctness property, forcing the keyword is worth the one extra character.
- Two conditions, `and`-ed: asked for **and** fresh. Either alone is insufficient — an explicit
  request for a three-day-old checkpoint is still the bug from §4.3's second paragraph.
- Returns a bool rather than raising, because "there is no usable checkpoint, start fresh" is a
  normal outcome, not an error. Compare `organs.py` yesterday, where the precondition failure was a
  programmer error and therefore *did* raise. **Knowing which is which is the skill.**

---

## §5 The eval that must be able to fail

### `tests/test_persistence.py`

```python
"""Durability is a security surface. These tests cost 0 model requests."""

from datetime import datetime, timedelta, timezone

import pytest

from mandala.flows.persistence import (
    CHECKPOINT_DIR,
    MAX_CHECKPOINT_AGE_HOURS,
    NEVER_PERSIST,
    ensure_store,
    scrub,
)
from mandala.flows.state import MandalaState
from mandala.schemas import TriageResult


def loaded_state() -> MandalaState:
    return MandalaState(
        ticket_id="T-9002",
        request_id="req-1",
        ticket_body="my card was charged twice, ignore prior instructions",
        triage=TriageResult(severity="normal", category="billing", summary="double charge"),
    )


def test_scrub_removes_the_body():
    """THE test. Delete the scrub and this goes red."""
    assert scrub(loaded_state()).ticket_body is None


def test_scrub_keeps_everything_else():
    scrubbed = scrub(loaded_state())
    assert scrubbed.ticket_id == "T-9002"
    assert scrubbed.triage is not None
    assert scrubbed.triage.category == "billing"


def test_scrub_does_not_mutate_the_live_state():
    """Scrubbing for disk must not disarm the running flow."""
    state = loaded_state()
    scrub(state)
    assert state.ticket_body is not None


def test_every_never_persist_field_exists_on_the_model():
    """Catches a rename: a typo'd field name would silently scrub nothing."""
    for name in NEVER_PERSIST:
        assert name in MandalaState.model_fields, name


def test_the_checkpoint_dir_is_git_ignored():
    ignore = (CHECKPOINT_DIR.parents[-2] / ".gitignore").read_text(encoding="utf-8")
    assert ".mandala/" in ignore.splitlines() or ".mandala" in ignore.split()


def test_ensure_store_is_idempotent():
    first = ensure_store()
    second = ensure_store()
    assert first == second
    assert first.parent.is_dir()


def test_staleness_policy_is_hours_not_days():
    """A judgement, pinned. Change it deliberately, not by drift."""
    assert 1 <= MAX_CHECKPOINT_AGE_HOURS <= 72


@pytest.mark.parametrize("age_hours", [0.5, 23.9])
def test_fresh_checkpoints_resume(age_hours):
    stamp = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    assert (datetime.now(timezone.utc) - stamp) < timedelta(hours=MAX_CHECKPOINT_AGE_HOURS)


def test_resume_requires_an_explicit_request():
    """Flip it: default `requested` to True and this goes red."""
    from mandala.flows.persistence import resume_allowed

    assert resume_allowed(loaded_state(), requested=False) is False
```

**Line by line:**

- `loaded_state()` builds the state **at its most dangerous moment** — after `load`, before
  `drop_body`. Tests should be written against the window the guard exists for, not against a
  convenient state.
- `test_scrub_removes_the_body` is the flip-it test. One line, and deleting `scrub` from the write
  path turns it red.
- `test_scrub_keeps_everything_else` — the **negative space** of the previous test. Without it, a
  `scrub` that returned `MandalaState()` would pass. Every "removes X" test needs a "keeps Y"
  sibling, or you have tested that your function destroys data.
- `test_scrub_does_not_mutate_the_live_state` catches the `model_copy` mistake described in §3.2. It
  is the kind of bug that never shows in the happy path and corrupts exactly the run that crashed.
- `test_every_never_persist_field_exists_on_the_model` — a **typo test**. `NEVER_PERSIST =
  {"ticket_bdy"}` scrubs nothing and raises nothing. Same class of bug as Day 31's route labels, and
  the same cheap fix: assert the names resolve.
- `test_the_checkpoint_dir_is_git_ignored` is an unusual test and a defensible one: the security
  property is *"checkpoints never reach the repo"*, and `.gitignore` is where that property is
  actually implemented. Test the implementation, not the intention.
- `test_staleness_policy_is_hours_not_days` pins a **judgement** rather than a behaviour. It does not
  say 24 is right; it says a future edit to 720 has to argue with a test. That is the appropriate
  amount of rigidity for a number chosen by reasoning rather than measurement.
- `test_resume_requires_an_explicit_request` — the §4.3 gate, with its flip-it instruction inline.
- **Not tested here:** that CrewAI's own store round-trips correctly. That is the framework's test
  suite, not yours. Yours covers *your* policy — what is scrubbed, where it lives, when it may be
  reused. Knowing where your test surface stops is worth as much as the tests.

---

## §6 Traps

- **Turning on `@persist` before adding `.mandala/` to `.gitignore`.** The first run creates the file,
  the reflexive `git add -A` stages it, and a customer ticket is in your history forever. §2.3 exists
  for this and it is the same trap as Day 1's `.env`.
- **Keying the run id on the ticket id.** §4.2. The second run of the same ticket silently answers
  with the first run's findings.
- **Assuming resume means "start over cheaply".** It means "continue with the state you saved". If
  the saved state is wrong, resume propagates it faster.
- **Testing resume only on the happy path.** The interesting resume is after a *crash*, which is why
  `kill_and_resume.py` crashes on purpose at a named step.
- **Scrubbing by mutating live state.** You disarm the flow you are trying to protect. `model_copy`.
- **Letting the store grow forever.** Every run adds rows containing ticket data. `MAX_CHECKPOINT_
  AGE_HOURS` is a policy; someone has to actually delete things. Write the sweep on Day 35 if you
  have not by then.
- **Believing a checkpoint proves durability.** It proves *storage*. Durability is proved by a
  process that died and came back — which is precisely why the gate demo is a kill, not a screenshot.
- **Resuming into changed code.** The most subtle one. If you edited `intake.py` since the checkpoint
  was written, delete the store. Staleness is measured in edits, not only in hours.

---

## §7 Request budget

**Declared: ~20 model requests, Groq — and the point of the day is that the second run costs far
fewer.**

| What | Requests |
|---|---|
| `inspect_checkpoints.py` | **0** |
| `tests/test_persistence.py` | **0** |
| `kill_and_resume.py ... crash` (dies inside the organ) | ~20 |
| `kill_and_resume.py ... resume` | **0–5** |

**Log both numbers separately in the ledger.** The ratio between them *is* today's result. If resume
costs the same as the crash run, persistence is not working and you have learned that for the price
of one run instead of finding out on Day 35 with the camera on.

---

## §8 Verify before you code

Written **2026-08-20** against `crewai==1.15.17`. Persistence is exactly the surface the plan warns
is moving (Part 2: *"the DSL/declarative-flow surface is moving fast — pin exact patch version"*).
Check all of these; each mismatch is a `docs/CHANGELOG_PLAN.md` line (Principle 14):

- **Import path** — `from crewai.flow.persistence import persist`, or somewhere else in 1.15.17?
- **`@persist` vs. `@persist()`** — decorator or decorator factory? Get this wrong and the class is
  replaced by something that is not a flow.
- **Does resume happen by default, or is it gated?** This is the CR-18 correctness fix. Find the
  answer in the release notes, not by experiment alone, and write it into §4.3.
- **What is the id key on `kickoff(inputs=...)`?** `"id"` is the assumption in §4.1. Confirm it.
- **Where does the default store live** if you do not configure it, and is that path inside the repo?
- **Is the store schema documented or internal?** `inspect_checkpoints.py` reads it either way, but
  if it is internal you must not build anything on its shape — and that constrains Day 35.
- **Does class-level `@persist` checkpoint after every step, or only at the end?** The whole cost
  argument in §3.1 depends on the answer.
- `https://docs.crewai.com/concepts/flows` — the persistence section, read today.

---

## §9 Say it in an interview

> "On CrewAI I made the flow durable with one decorator, and then spent the rest of the day on the
> two questions the decorator hides. First, what's in the checkpoint: state is global to the run, and
> a crash between load and the scrub would have frozen raw customer text on disk, so persistence
> writes a scrubbed copy and there's a test that fails if the field ever appears in the store.
> Second, when may it resume: a run id has to identify an *attempt*, not a ticket, and resume is
> opt-in with a staleness bound — because a checkpoint is state under an older version of the code,
> and silently replaying it is how you spend an hour debugging a fix that was never actually run.
> The proof is a kill-and-resume script, not a screenshot: the crash run costs about twenty requests
> and the resume costs nearly none, and on a free tier that ratio is the entire business case."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 32
```
