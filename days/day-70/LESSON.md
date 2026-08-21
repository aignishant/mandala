---
day: 70
phase: 10
phase_name: "Safety & security"
title: "Fixes, and the permission table"
ids: []
kind: gate
plan_version: "v1.1.0"
generated: "2026-08-21"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 70 — Fixes, and the permission table 🎯

**Phase 10 · Safety & security** · IDs: **—** · **Phase-10 gate**

> **Yesterday:** twelve attacks, one scorecard, and a set called `BREACHED_TODAY` with your own
> system's name on it.
> **Today:** you empty that set, and you publish the artifact Phase 10 has been building towards
> since Day 8 — a permission table generated from code, that proves separation rather than asserting
> it. Then you sit the gate.
> **Tomorrow:** Phase 11 opens on evals. Everything you built in the last six days becomes something
> that runs on every commit.

```bash
./m start 70
./m scaffold 70
```

---

## §1 The story

The plan's Phase-10 gate reads:

> *the lethal-trifecta table proves separation; sandbox demo (both SDK-native and e2b-style);
> computer-use demo confined to the local dummy site.*

Read the first clause again: **proves**. Not "documents". A table you typed by hand documents what
you believed on the day you typed it. A table *generated from `permissions.py`* proves what the code
does right now, and a test that regenerates it and compares proves it is still true today.

That distinction is the whole of Day 70, and it generalises past security:

> **Any security document maintained by hand is a security document that is wrong.**

It is wrong not through carelessness but through time. Day 15 added search tools. Day 16 mounted an
MCP server. Day 19 added code execution. Day 68 added a browser. Each of those was a real capability
change, and a hand-maintained table would have drifted at every one of them. Your `permissions.py`
did not drift, because Days 12, 14, 15 and 16 each wrote a test asserting the code matched the table.
**Today you close the loop: the published document becomes an output of the code, and a test fails
if the checked-in copy is stale.**

Today has three movements:

1. **Fix.** Empty `BREACHED_TODAY`. For each breach, decide whether the control was *missing*,
   *wrong*, or *not wired in* — three different fixes.
2. **Publish.** Generate `docs/PERMISSION_TABLE.md` from `permissions.py`, plus the trifecta
   separation proof.
3. **Gate.** Run the three demos, produce a pass/fail table, write `docs/adr/gate-phase-10.md`, run
   the freshness check, tag the repo.

---

## §2 Setup — run this

```bash
touch scripts/gen_permission_table.py
touch docs/PERMISSION_TABLE.md
touch docs/adr/gate-phase-10.md
mkdir -p days/day-70/lab
touch days/day-70/lab/fixes.md
touch tests/test_permission_table_is_current.py
```

- `scripts/` rather than `src/` — this is a tool that maintains the repo, not part of Mandala. Same
  place as Day 0's tracker scripts.
- `docs/PERMISSION_TABLE.md` is **generated and checked in**. Both. Generated so it cannot drift;
  checked in so a reviewer (and Day 89's portfolio reader) can see it without running your code.
- `days/day-70/lab/fixes.md` records, per breach, the *class* of fix. That analysis is worth more
  than the diffs.

No new dependencies. Two days in a row.

---

## §3 Movement one — fix what fell over

### 3.1 Classify before you patch

For every ID in yesterday's `BREACHED_TODAY`, write one line in `fixes.md` under one of three
headings — **and write it before you touch code**:

| Class | Means | Typical fix | Danger |
|---|---|---|---|
| **Missing** | there was no control; you had not thought of this | add one, and add a test | scope creep — fix the class, not the instance |
| **Wrong** | the control exists and does not do what you thought | correct it; keep the old test and add the case that fooled it | you will "fix" it by special-casing yesterday's exact payload |
| **Not wired** | the control is correct and this path does not call it | call it — and ask what *else* skips it | there is almost always a second unwired path |

**"Not wired" is the most common and the most instructive.** Day 8's `permissions.check()` is
correct; the question is whether every dispatch path in six days of frameworks actually calls it.
When you find one that doesn't, do not fix only that one — **grep for every dispatch site** and make
the check impossible to skip. A control you must remember to call is a control that will be forgotten
on Day 81 at 11pm.

### 3.2 The fixes that carry past today

You will have your own list. These four are the ones that most often come out of this corpus, and
each is a small change with a large radius:

**Fix A — a dispatch chokepoint.** If `permissions.check()` is called at four call sites, make it
three, then one. One function through which every tool call passes, and the check inside it. Then
`test_every_dispatch_path_goes_through_the_chokepoint` can be a real test rather than an aspiration.

**Fix B — normalise at intake, once.** RT-03's Cyrillic homoglyphs argue for `unicodedata.normalize`
at the boundary. Do it in exactly one place, on the way in, and **record what it breaks**: a
customer legitimately writing in Cyrillic now has their ticket mangled. That is a real trade and it
belongs in `fixes.md`, not in a silent commit.

**Fix C — split "draft" from "send", everywhere.** Day 8 split them in the table. RT-07 usually finds
somewhere they are still one operation. This is the fix that makes Day 82's approval gate possible at
all.

**Fix D — a description hash for MCP servers.** RT-09's control has to be mechanical: record the hash
of every tool's name + description + schema at approval time, compare at connect, refuse on change.
Three lines and it closes the entire rug-pull class.

```python
# sketch — src/mandala/mcp/pinning.py
import hashlib
import json


def tool_fingerprint(tools: list[dict]) -> str:
    """Stable hash of the tool surface a human approved."""
    canon = json.dumps(
        sorted(
            {"name": t["name"], "description": t["description"], "schema": t.get("inputSchema", {})}
            for t in tools
        ),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()
```

**Line by line:**

- `sorted(...)` **and** `sort_keys=True` — a server returning its tools in a different order must not
  invalidate the fingerprint, or you will train yourself to click through the warning. Ordering
  instability is how security prompts become noise.
- `separators=(",", ":")` — no incidental whitespace in the hash input.
- **`description` is in the hash, and that is the whole point.** MCP-15's rug pull changes the
  *description*, not the name or the schema, because the description is what the model reads. A
  fingerprint over names alone would have passed RT-09 while being completely useless.
- `sha256` over a canonical JSON string, not `hash()` — Python's `hash()` is salted per process and
  would differ between runs.

### 3.3 Empty the set

```python
BREACHED_TODAY: set[str] = set()
```

Delete the corresponding `xfail`s. Run `uv run pytest tests/test_redteam.py -v` and expect **twelve
passes and zero xfails**. If one attack genuinely cannot be fixed today, it does not stay as an
xfail — it becomes an **accepted risk with a named compensating control**, written into
`docs/REDTEAM.md`:

```markdown
## Accepted risks

| ID | Why not fixed | Compensating control | Review by |
|---|---|---|---|
| RT-0x | … | … | Day 84 (graduated autonomy review) |
```

**An accepted risk with a date and a compensating control is professional. An xfail that survives the
gate is debt pretending to be a decision.**

---

## §4 Movement two — the generated permission table

### 4.1 `scripts/gen_permission_table.py`

```python
"""Generate docs/PERMISSION_TABLE.md from src/mandala/permissions.py.

The document is an OUTPUT of the code. It is checked in so a reviewer can read it
without running anything, and tests/test_permission_table_is_current.py fails if
the checked-in copy has drifted. That pair — generated + drift-tested — is what
turns 'we document our permissions' into 'our permissions are documented'.
"""

from __future__ import annotations

import pathlib
import sys

from mandala.permissions import AGENTS, TOOLS, trifecta_violations

OUT = pathlib.Path("docs/PERMISSION_TABLE.md")


def render() -> str:
    lines = [
        "# 🔐 PERMISSION_TABLE.md — generated, do not edit",
        "",
        "> Generated by `scripts/gen_permission_table.py` from `src/mandala/permissions.py`.",
        "> `tests/test_permission_table_is_current.py` fails if this file is stale.",
        "",
        "## Tools",
        "",
        "| Tool | Writes? | Returns untrusted text? | Blast radius |",
        "|---|---|---|---|",
    ]
    for name in sorted(TOOLS):
        t = TOOLS[name]
        lines.append(
            f"| `{name}` | {'✍️ yes' if t.writes else 'read-only'} "
            f"| {'⚠️ yes' if t.reads_untrusted else 'no'} | {t.blast_radius} |"
        )

    lines += ["", "## Agents", "", "| Agent | Tools | Sees untrusted text? | May write? |", "|---|---|---|---|"]
    for name in sorted(AGENTS):
        a = AGENTS[name]
        writes = any(TOOLS[t].writes for t in a.tools)
        tools = ", ".join(f"`{t}`" for t in sorted(a.tools)) or "—"
        lines.append(
            f"| **{name}** | {tools} | {'⚠️ yes' if a.sees_untrusted_text else 'no'} "
            f"| {'✍️ yes' if writes else 'no'} |"
        )

    lines += [
        "",
        "## Lethal-trifecta separation proof",
        "",
        "An agent is a trifecta risk if it holds untrusted input **and** any write capability.",
        "",
        "| Agent | Untrusted input | Write capability | Both? |",
        "|---|---|---|---|",
    ]
    for name in sorted(AGENTS):
        a = AGENTS[name]
        writes = any(TOOLS[t].writes for t in a.tools)
        both = a.sees_untrusted_text and writes
        lines.append(
            f"| {name} | {'yes' if a.sees_untrusted_text else 'no'} "
            f"| {'yes' if writes else 'no'} | {'❌ **VIOLATION**' if both else '✅ no'} |"
        )

    violations = trifecta_violations()
    lines += [
        "",
        f"**Violations: {len(violations)}** — {violations or 'none'}",
        "",
        "## Computer use (Day 68)",
        "",
        "A click is not an enumerable capability, so the browser is constrained by **reach**:",
        "exact-origin allowlist, closed action vocabulary, context-level request gate, popups closed,",
        "downloads off, hard step budget, human approval before anything irreversible.",
        "See `src/mandala/computer/leash.py` and `tests/test_computer_leash.py`.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    text = render()
    if "--check" in sys.argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        sys.exit(0 if current == text else 1)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT} — {len(TOOLS)} tools, {len(AGENTS)} agents, "
          f"{len(trifecta_violations())} violations")
```

**Line by line:**

- **`do not edit` in the first line of the output.** Generated files get hand-edited by well-meaning
  people, including you, in eight weeks.
- `sorted(TOOLS)` and `sorted(a.tools)` everywhere — **deterministic output is what makes the drift
  test possible.** Iterate a dict in insertion order and the file churns on every unrelated edit,
  the diff becomes noise, and the drift test becomes something people regenerate reflexively.
- The **untrusted-text column on tools** is the one nobody has. Day 8's `reads_untrusted` field pays
  off here: the table now shows, per tool, whether its *output* is attacker-influenced. That column
  is why the trifecta proof can be computed rather than argued.
- The trifecta section **recomputes** `both` from the same fields rather than calling
  `trifecta_violations()` per row, then prints `trifecta_violations()` as the summary. Two
  independent paths to the same answer, in the published artifact. If they ever disagree, the
  document shows it.
- `--check` mode exits 1 on drift with no output — that is the CI shape. Day 74 wires it in; today
  the pytest below does the same job locally.
- The computer-use section is **prose in a generated file**, and that is a deliberate compromise:
  the leash's rules are not in `permissions.py` because they are not capabilities. Note the seam
  honestly rather than pretending the generator covers everything. If it bothers you — and it should
  — the fix is to move `ALLOWED_ORIGINS` and `MAX_STEPS` into a structure the generator can read.
  That is a good Day-77 buffer task.

### 4.2 The drift test

```python
# tests/test_permission_table_is_current.py
"""The checked-in permission table must equal what the code generates. 0 requests."""

from __future__ import annotations

import pathlib

from mandala.permissions import AGENTS, TOOLS, trifecta_violations

from scripts.gen_permission_table import render

DOC = pathlib.Path("docs/PERMISSION_TABLE.md")


def test_the_checked_in_table_is_not_stale():
    """Flip it: add a tool to permissions.py and don't regenerate — this goes red."""
    assert DOC.exists(), "run scripts/gen_permission_table.py"
    assert DOC.read_text(encoding="utf-8") == render()


def test_the_table_is_deterministic():
    assert render() == render()


def test_no_agent_holds_the_lethal_trifecta():
    assert trifecta_violations() == []


def test_every_agent_tool_exists_in_the_tool_registry():
    for agent in AGENTS.values():
        for tool in agent.tools:
            assert tool in TOOLS, f"{agent.name} grants unknown tool {tool!r}"


def test_every_write_tool_has_a_non_empty_blast_radius():
    for name, tool in TOOLS.items():
        if tool.writes:
            assert tool.blast_radius.strip(), f"{name} writes and has no blast radius written down"


def test_the_generated_doc_says_it_is_generated():
    assert "do not edit" in DOC.read_text(encoding="utf-8").splitlines()[0].lower()
```

**Line by line:**

- `test_the_checked_in_table_is_not_stale` is the day's headline test, and its flip-it instruction is
  the exact thing that will happen on Day 82 when the capstone adds a write tool. **The test fails,
  you regenerate, and the diff makes you look at a new write capability.** That is the mechanism —
  not the document.
- `test_the_table_is_deterministic` catches set-ordering leaking into output. Two calls, same string.
  Cheap, and it will save the drift test from becoming flaky-and-therefore-ignored.
- `test_every_write_tool_has_a_non_empty_blast_radius` enforces Principle 6 *mechanically*. You
  cannot add a write tool without writing a sentence about what it can destroy. Sixty-two days after
  Day 8 introduced the field, it becomes a rule.
- Importing `render` from `scripts/` — check that `scripts/` is importable under your layout
  (`__init__.py`, or `pythonpath` in `pyproject.toml`'s pytest config). §8 flags it.

---

## §5 Movement three — the gate

### 5.1 The three demos

```bash
# 1 — separation proof
uv run python scripts/gen_permission_table.py
uv run pytest tests/test_permission_table_is_current.py -v

# 2 — sandbox (AG-18, Day 67), both flavours
uv run python days/day-67/lab/sandbox_demo.py
uv run python days/day-67/lab/escape_suite.py          # every escape must fail

# 3 — computer use confined (AG-19, Day 68)
uv run python days/day-68/lab/serve_site.py &
uv run python days/day-68/lab/escape_attempts.py
uv run python days/day-68/lab/computer_loop.py "Read T-9002 and summarise it."

# 4 — the red team, now green
uv run pytest tests/test_redteam.py -v
```

**On the plan's "SDK-native and e2b-style" phrasing:** that row was written before the zero-budget
addendum. e2b is a paid hosted sandbox, so the free equivalent is what Day 67 built — a local Docker
box with no network, read-only root, and resource caps. **Say that explicitly in the ADR** rather
than quietly skipping the clause. Principle 14 is about naming where reality diverged from the plan,
and this is a small, clean example of doing it properly.

### 5.2 The pass/fail table

Write this into `docs/adr/gate-phase-10.md` — evidence, not adjectives:

```markdown
# Gate — Phase 10 (Safety & security)

Date: 2026-__-__ · Days 65–70 · Reviewer: me (cold read scheduled: +1 day)

| Criterion (from plan Part 5) | Evidence | Verdict |
|---|---|---|
| Lethal-trifecta table proves separation | `docs/PERMISSION_TABLE.md`, generated; `test_no_agent_holds_the_lethal_trifecta` green; drift test green | |
| Sandbox demo (free equivalent of e2b) | `days/day-67/lab/escape_suite.py` — N/N escapes blocked | |
| Computer-use demo confined to the dummy site | `escape_attempts.py` 6/6 blocked; loop stopped at ⏸ on `danger.html` | |
| Red team: no unfixed breach | `tests/test_redteam.py` 12/12 pass, 0 xfail | |
| Accepted risks documented | `docs/REDTEAM.md` § Accepted risks, each with a control and a review date | |
| Freshness check logged | `docs/CHANGELOG_PLAN.md` entry for today | |

## What changed as a result of Phase 10
…
## What I would still not deploy, and why
…
```

**The last section is the one that matters.** Six days of security work whose conclusion is "it's
secure now" is six days of theatre. Name the things you would not put in front of a real customer
yet — the keyword-based irreversibility heuristic, the canary's paraphrase blind spot, whatever
accepted risks you carried — and Day 84's graduated-autonomy review will start exactly there.

### 5.3 The freshness check (Principle 13)

Run `/freshness` and log one line per pin in `docs/CHANGELOG_PLAN.md`, **including nil reports**.
Phase 10 makes two of them load-bearing: `playwright` (added yesterday) and the MCP spec revision
(RT-09's fix depends on what the client exposes). A material change means an addendum before code —
Principle 14 — and that is true even on a gate day, especially on a gate day.

### 5.4 Tag it

```bash
git tag phase-10-complete
```

Then **schedule the cold read**: reopen `docs/adr/gate-phase-10.md` tomorrow before starting Day 71
and sign it, the way ADR-003 was signed a day late on Day 64. A gate you signed while still warm
from writing it is a gate you graded yourself on.

---

## §6 Traps

- **Fixing without classifying.** Missing / wrong / not-wired need different fixes; patching the
  payload rather than the class is how the same bug returns with different wording.
- **Special-casing yesterday's exact string.** RT-01 with a synonym is a different test that passes.
- **Fixing one unwired call site.** Grep for all of them, then make skipping impossible.
- **Normalising unicode silently.** It breaks legitimate non-Latin input. Record the trade.
- **Hand-editing the generated table.** It says "do not edit" in line one for a reason.
- **Non-deterministic generator output.** The drift test becomes flaky, then ignored, then deleted.
- **Leaving an xfail through the gate.** Either fixed, or an accepted risk with a control and a date.
- **Claiming the e2b clause was met.** Say what you built instead, and why.
- **Signing the ADR the same day you wrote it.** Cold read, next day.
- **Skipping freshness because it's a gate day.** Gate days are when it matters most.
- **Treating "the tests pass" as "the system is safe".** Your tests cover the attacks you thought of.
  §5.2's last section is where that gets said out loud.

---

## §7 Request budget

**Declared: ~10 model requests — the cheapest day in Phase 10.**

| What | Requests |
|---|---|
| Permission table generation + drift tests | **0** |
| Sandbox escape suite | **0** |
| Browser escape attempts | **0** |
| `computer_loop.py` on `danger.html` (gate demo) | ≤ 2 |
| `tests/test_redteam.py` — the model-dependent attacks, re-run after fixes | ≤ 8 |

**The number to notice is the zeroes.** The gate for the security phase is almost entirely
deterministic: generated documents, escape suites, drift tests. That is not a budget accident — it is
what it means for a control to live in code rather than in a prompt. Put the comparison in the
bake-off notes: a security posture whose verification costs nothing is a security posture that gets
verified on every commit, and Day 74 is about to prove it.

---

## §8 Verify before you code

Written **2026-08-21**:

- **Is `scripts/` importable from `tests/`?** Either add `scripts/__init__.py` or set
  `pythonpath = [".", "src"]` under `[tool.pytest.ini_options]`. Confirm before writing the drift
  test, or you will debug an `ImportError` and blame the test.
- **`ruff` on a generated markdown-producing script** — confirm your line-length rules don't fight
  the long f-strings; add a targeted `noqa` rather than reformatting the output.
- **Does `./m check` already run `gen_permission_table.py --check`?** If not, add it today —
  the drift test in pytest covers local runs, and the `--check` exit code is what Day 74 wires to CI.
- **MCP client tool-description caching** — confirm whether your SDK re-reads descriptions per
  session before you rely on `tool_fingerprint` firing at connect.
- **`unicodedata.normalize("NFKC", ...)`** on RT-03's payload — confirm it actually folds those
  specific Cyrillic confusables. **It may not.** NFKC handles compatibility characters, not all
  visually-confusable ones; if it doesn't fold them, your Fix B is a different fix (a confusables
  table, or a tool-name allowlist — and the allowlist is the better answer anyway).
- **`git tag` vs. `git tag -a`** — an annotated tag carries a date and message; for a gate record,
  use `-a`.
- `https://docs.pytest.org/en/stable/reference/customize.html` — read today.

---

## §9 Say it in an interview

> "The Phase-10 deliverable wasn't a hardened system, it was a *verifiable* one. The permission table
> is generated from the code that defines the permissions, checked into the repo so a reviewer can
> read it, and there's a test that fails if the checked-in copy has drifted — so the next time
> someone adds a write tool, the test goes red and the diff makes them look at a new write
> capability. That's the mechanism; the document is just the artifact. The trifecta proof is computed
> from two fields I've been maintaining since week two: does this tool write, and is its output
> attacker-influenced. The second field is the one most people don't record, and it's what lets
> separation be *proved* rather than asserted. When I fixed the red-team findings I classified each
> one as missing, wrong, or not-wired, because they need different fixes — and 'not wired' was the
> most common, which told me the real fix was a single dispatch chokepoint rather than four call
> sites that each remember to check. What I'd flag honestly is what I wrote in the gate ADR under
> 'what I would still not deploy': my irreversible-action detector is keyword-based and misses
> 'Finalise' and 'Yes', and my exfiltration canary misses paraphrase. Both are written down with
> review dates rather than quietly carried."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 70
```

Phase 10 closes here. **Do not start Day 71 before the cold read.**
