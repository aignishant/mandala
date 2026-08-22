---
day: 80
phase: 12
phase_name: "Capstone build"
title: "Capstone III — the research organ"
ids: []
kind: capstone
plan_version: "v1.1.0"
generated: "2026-08-21"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 80 — Capstone III: the research organ

**Phase 12 · Capstone build** · IDs: **—** (ADR-003: *a CrewAI crew as one subgraph organ*)

> **Yesterday:** the spine runs, checkpoints, and resumes. `research` is a node that raises
> `NotImplementedError`.
> **Today:** you fill it — with a CrewAI crew, called as one node, holding **no write tool**, whose
> outputs are `Untrusted` because search results are attacker-influenced (RT-04). Also: Day 77's
> deferred context-pruning debt bites today, exactly as predicted.
> **Tomorrow:** drafting with citations — and the citations come from what you build now.

```bash
./m start 80
./m scaffold 80
```

---

## §1 The story

ADR-003's most interesting choice was not the LangGraph spine — it was keeping a **CrewAI crew as one
organ inside it**. The justification, from Phase 9's scorecard, was roughly: role-based delegation is
genuinely good at open-ended "go find out about this" work, and terrible as a control plane. So it
gets one node, with a hard boundary around it.

The boundary is today's real content, and it has three walls:

1. **No write tools. Ever.** The Researcher is the agent that reads attacker-controlled text and
   fetches more of it from the internet. Day 8's trifecta test exists to make sure this agent never
   acquires the third leg. When you wire the crew, the temptation to give it "just a note-saving
   tool" will appear. **That is the trifecta, wearing a hat.**
2. **Its output is untrusted.** A search snippet is text a stranger wrote. RT-04 injected through
   exactly this channel. So findings come back wrapped in `Untrusted`, and tomorrow's drafter fences
   them the same way today's classifier fenced the ticket.
3. **It is bounded.** Requests, findings, time. An open-ended research loop on a free tier is how you
   discover your daily quota at 3pm. Day 76's `RunBudget` is threaded in, and the crew gets a slice
   of it, not the whole thing.

The seam between graph and crew is one function. Keep it that way: **the crew must not know it is
inside a graph, and the graph must not know it is calling a crew.** That is what lets Day 84 replace
the organ, and it is the entire practical value of the bake-off you did in Phase 9.

---

## §2 Setup — run this

No new dependencies (`crewai` from Day 23, `ddgs` from Day 15).

```bash
touch src/mandala/organs/__init__.py
touch src/mandala/organs/research.py
touch src/mandala/organs/tools_readonly.py
mkdir -p days/day-80/lab
touch days/day-80/lab/research_only.py
touch days/day-80/lab/prune_experiment.py
touch tests/test_research_organ.py
```

**Line by line:**

- `organs/` rather than `crew/` — **name the role, not the framework.** ADR-003 says an organ may be
  replaced; a module called `crew/` makes replacement a rename-and-refactor, while `organs/research.py`
  makes it an implementation swap behind a stable name. This is a five-second decision that Day 84
  will thank you for.
- Reuse Day 23's crew definitions rather than writing new ones. If they need changes, that is a
  finding about Phase 4, not a fresh design.

---

## §3 Wall one — a read-only toolbelt, derived from the permission table

```python
# src/mandala/organs/tools_readonly.py
"""Tools the Researcher may hold. Derived from permissions.py, asserted at import.

This module cannot contain a write tool. Not 'should not' — the assertion at the
bottom raises at import time, so a write tool here breaks the process, loudly,
during CI, before anything runs.
"""

from __future__ import annotations

from crewai.tools import tool
from ddgs import DDGS

from mandala.intake.types import Untrusted
from mandala.permissions import TOOLS

MAX_RESULTS = 5


@tool("search_kb")
def search_kb(query: str) -> str:
    """Search public documentation. Returns snippets. Read-only."""
    with DDGS() as ddgs:
        hits = list(ddgs.text(query, max_results=MAX_RESULTS))
    return "\n".join(f"- {h['title']} :: {h['href']} :: {h['body'][:300]}" for h in hits)


RESEARCHER_TOOLS = [search_kb]

_names = {t.name for t in RESEARCHER_TOOLS}
assert _names <= set(TOOLS), f"undeclared tools: {_names - set(TOOLS)}"
assert not any(TOOLS[n].writes for n in _names), (
    f"a write tool reached the Researcher: {[n for n in _names if TOOLS[n].writes]}"
)
```

**Line by line:**

- **Two module-level assertions.** Import-time failure is the strongest guarantee available in Python
  short of a type system, and it fires in CI, in the test suite, and in production, without anyone
  remembering to call a checker. Day 70's chokepoint pattern, applied a fourth time.
- `_names <= set(TOOLS)` catches the tool that exists in code but was never declared in the permission
  table — which means it never appeared in Day 70's generated document and nobody reviewed it.
- `MAX_RESULTS = 5` and `h['body'][:300]` — **bounding at the tool, not at the prompt.** A tool that
  can return 40 KB of stranger-written text is a tool that decides your context budget for you.
- The snippet format is `title :: href :: body`, which tomorrow's citation checker parses. Decide the
  format here, once, rather than having the drafter guess at it.

---

## §4 Wall two — the organ, and untrusted output

```python
# src/mandala/organs/research.py
"""The research organ. One function in, one list of findings out.

The crew does not know it is in a graph. The graph does not know it is calling a
crew. That seam is the whole reason ADR-003 could pick different tools per organ.
"""

from __future__ import annotations

from dataclasses import dataclass

from mandala.intake.types import Untrusted
from mandala.obs.tracing import span
from mandala.organs.tools_readonly import RESEARCHER_TOOLS
from mandala.router.budget import BudgetExceeded, RunBudget

MAX_FINDINGS = 6
RESEARCH_SHARE = 8          # requests this organ may spend, out of the run's budget


@dataclass(frozen=True)
class Finding:
    claim: Untrusted
    url: str
    query: str


def research(question: Untrusted, *, budget: RunBudget, run_id: str) -> list[Finding]:
    with span("mandala.research.organ", run_id=run_id) as s:
        organ_budget = RunBudget(limit=min(RESEARCH_SHARE, budget.limit - budget.spent))
        try:
            raw = _run_crew(question, organ_budget)          # TODO(me): wire Day 23's crew
        except BudgetExceeded as e:
            s.set_attribute("research.truncated", str(e))
            return []
        finally:
            budget.charge("research", organ_budget.spent)
        findings = _parse(raw)[:MAX_FINDINGS]
        s.set_attribute("research.findings", len(findings))
        return findings


def _parse(raw: str) -> list[Finding]:
    out: list[Finding] = []
    for line in raw.splitlines():
        if line.count("::") != 2:
            continue
        title, href, body = (p.strip() for p in line.lstrip("- ").split("::"))
        out.append(Finding(claim=Untrusted(f"{title}: {body}", source=f"search:{href}"), url=href, query=""))
    return out
```

**Line by line:**

- **`Finding.claim` is `Untrusted`, and `source` records the URL it came from.** This is the
  provenance chain paying off: on Day 83, when a draft says something wrong, you can trace the claim
  to the snippet to the URL to the query. That chain is what makes an incident investigable.
- `organ_budget` is a **slice**, computed from what the run has left. The crew cannot spend the
  approval step's budget. Note it is `min(SHARE, remaining)` — if the classifier already burned most
  of the run, research gets less, not more.
- `finally: budget.charge(...)` — **the parent budget is charged whether or not the crew succeeded.**
  A failed crew still consumed requests; forgetting this is how a retry loop silently doubles your
  spend.
- `BudgetExceeded` returns `[]` rather than propagating. **Deliberate**: no findings is a degraded
  but valid outcome, and tomorrow's drafter must handle it anyway (a ticket with no research is
  normal for `route == "draft"`). Record the truncation in the span so Day 83's report can count it.
- `MAX_FINDINGS` bounds at the organ boundary in addition to the tool. Two bounds, different reasons:
  the tool bound stops one query flooding you, the organ bound stops twelve queries doing it.
- `_parse` **skips malformed lines** rather than raising. The input is model-formatted text; strict
  parsing here turns a cosmetic LLM wobble into a failed run. Contrast with Day 79's
  `model_validate_json` on the classifier — **strict where the value is structured, lenient where it
  is a list of snippets.** Being able to explain that difference is a real interview answer.

---

## §5 Wall three — the pruning debt, now due

Day 77 deferred proper context pruning with the note *"bites on Day 80: research organ has long
contexts"*. Open `days/day-77/lab/debts.md` and read the row before you continue. This is the day.

The naive version (keep first + last N) fails here specifically because **research context is a list
of independent findings, not a conversation** — the first and last are not more valuable than the
middle. Two better options, and you should measure rather than assume:

```python
# days/day-80/lab/prune_experiment.py
"""Three pruning strategies over the same findings. Compare on the golden set."""

STRATEGIES = {
    "first_last": lambda f, n: f[: n // 2] + f[-(n // 2) :],
    "dedupe_by_url": lambda f, n: list({x.url: x for x in f}.values())[:n],
    "shortest_first": lambda f, n: sorted(f, key=lambda x: len(x.claim.text))[:n],
}
```

Run each through `run_experiment.py` and diff with Day 73's `compare.py`. **Expect `dedupe_by_url` to
win**, because search results repeat themselves and duplicates cost tokens while adding nothing — but
run it, because "expected" is how you end up shipping folklore. Record the three numbers.

**One caution on `shortest_first`:** it optimises for the thing your cost metric measures rather than
the thing you want, and it may score well because short findings produce short drafts that pass a
length check. This is exactly the rubric-gaming failure Day 76 warned about. **Check the per-example
diff, not the aggregate.**

---

## §6 The eval that must be able to fail

```python
# tests/test_research_organ.py
import pytest

from mandala.intake.types import Untrusted
from mandala.organs.research import MAX_FINDINGS, Finding, _parse, research
from mandala.organs.tools_readonly import RESEARCHER_TOOLS
from mandala.router.budget import RunBudget

pytestmark = pytest.mark.eval_unit


def test_the_researcher_holds_no_write_tool():
    """The trifecta test, at the organ. Flip it: add a 'save_note' tool, watch import fail."""
    from mandala.permissions import TOOLS

    assert not any(TOOLS[t.name].writes for t in RESEARCHER_TOOLS)


def test_every_researcher_tool_is_declared_in_the_permission_table():
    from mandala.permissions import TOOLS

    assert {t.name for t in RESEARCHER_TOOLS} <= set(TOOLS)


def test_findings_are_untrusted_and_carry_their_source():
    f = _parse("- HP docs :: https://example.test/a :: reset the spooler")[0]
    assert isinstance(f.claim, Untrusted) and f.claim.source.startswith("search:")


def test_a_finding_cannot_be_interpolated_into_a_prompt():
    f = _parse("- t :: https://e.test/a :: b")[0]
    with pytest.raises(TypeError):
        f"context: {f.claim}"


def test_malformed_lines_are_skipped_not_fatal():
    assert _parse("garbage\n- t :: https://e.test/a :: b\nmore garbage") != []


def test_findings_are_bounded(monkeypatch):
    monkeypatch.setattr("mandala.organs.research._run_crew",
                        lambda q, b: "\n".join(f"- t{i} :: https://e.test/{i} :: b" for i in range(50)))
    out = research(Untrusted("q", source="inbox"), budget=RunBudget(limit=20), run_id="T-1-a")
    assert len(out) <= MAX_FINDINGS


def test_the_organ_cannot_spend_the_whole_run_budget(monkeypatch):
    """Flip it: pass `budget` straight through and one bad ticket eats the approval step's quota."""
    b = RunBudget(limit=20)
    monkeypatch.setattr("mandala.organs.research._run_crew", lambda q, ob: _burn(ob))
    research(Untrusted("q", source="inbox"), budget=b, run_id="T-1-a")
    assert b.spent <= 8


def test_a_failed_crew_still_charges_the_parent_budget(monkeypatch):
    b = RunBudget(limit=20)

    def boom(q, ob):
        ob.charge("research", 3)
        raise RuntimeError("crew died")

    monkeypatch.setattr("mandala.organs.research._run_crew", boom)
    with pytest.raises(RuntimeError):
        research(Untrusted("q", source="inbox"), budget=b, run_id="T-1-a")
    assert b.spent == 3


def test_no_findings_is_a_valid_outcome_not_an_error(monkeypatch):
    monkeypatch.setattr("mandala.organs.research._run_crew", lambda q, ob: "")
    assert research(Untrusted("q", source="inbox"), budget=RunBudget(limit=20), run_id="T-1-a") == []


def test_the_organ_signature_mentions_no_framework():
    import inspect

    from mandala.organs import research as mod

    assert "crew" not in inspect.signature(mod.research).__str__().lower()
```

**Line by line:**

- `test_the_researcher_holds_no_write_tool` is the trifecta assertion, now at the organ as well as
  the system level. Its flip-it is the exact temptation §1 warned about.
- `test_a_finding_cannot_be_interpolated_into_a_prompt` extends Day 78's guarantee to the **second**
  untrusted source. Tomorrow's drafter handles two kinds of untrusted text; both raise on
  interpolation.
- `test_a_failed_crew_still_charges_the_parent_budget` is the subtle one. Without the `finally`, a
  crashing crew is free, and a retry loop around a crashing crew is infinitely free — until your
  quota is gone. **This test costs nothing and prevents an outage.**
- `test_the_organ_signature_mentions_no_framework` enforces the seam mechanically. Slightly cheeky;
  entirely in keeping with the "generated, not asserted" discipline from Day 70.

---

## §7 Traps

- **"Just a note-saving tool" for the Researcher.** That is the trifecta.
- **Findings as plain strings.** You lose provenance and the fence.
- **Passing the whole run budget to the organ.** One bad ticket eats the approval step's quota.
- **No `finally` on the budget charge.** A crashing crew is free; a retry loop is infinitely free.
- **Strict parsing of model-formatted snippet text.** A cosmetic wobble becomes a failed run.
- **Lenient parsing of the classifier's JSON.** Opposite direction, same mistake. Know which is which.
- **Bounding only at the tool, or only at the organ.** Two bounds, two different floods.
- **Naming the module `crew/`.** Makes replacement a refactor.
- **Assuming `dedupe_by_url` wins.** Measure it.
- **Judging pruning by the aggregate.** `shortest_first` may be gaming a length rubric.
- **Skipping the Day-77 debts file.** Today is its due date.
- **Fetching from a URL a search result suggested** — that is RT-05's channel. Read snippets; do not
  follow links without an allowlist.

---

## §8 Request budget

**Declared: ~35 model requests, Groq — the crew is the most expensive organ.**

| What | Requests |
|---|---|
| All tests (crew monkeypatched) | **0** |
| `research_only.py` on 3 questions | ≤ 12 |
| `prune_experiment.py` — 3 strategies × golden subset | ≤ 20 (cache should absorb much of it) |
| Spot-checks | ≤ 5 |

**Compare against Day 79's spine (~12).** One organ costs three times the spine, and that ratio is
worth writing into the Day-89 portfolio: it is the honest answer to "why not make everything a crew?"
Also record the crew's requests-per-finding — it is the number Day 84 will use when deciding whether
this organ has earned any autonomy.

---

## §9 Verify before you code

Written **2026-08-21** against `crewai==1.15.17`, `ddgs==9.15.0`:

- **`@tool` decorator import path** (`crewai.tools` vs `crewai_tools`) and whether the tool name is
  taken from the decorator argument or the function name.
- **How a Crew returns output** — `CrewOutput` object, `.raw`, or a string? `_parse` depends on it.
- **Can you cap a Crew's iterations / max_rpm** natively? If so, use it *as well as* your budget, and
  note which fires first.
- **`ddgs` result keys** (`title`/`href`/`body`) on 9.15.0 — these have changed with the package's
  rename history.
- **Does the crew's LLM config still point at your pinned free-tier model** (Day 23), or has a
  default crept back in? Principle 4.
- **Day-77 debts file**: read it, and update the row you are clearing today.
- `https://docs.crewai.com/concepts/tools` — read today.

---

## §10 Say it in an interview

> "The research organ is a CrewAI crew, but it's called as one node behind a plain function — the
> crew doesn't know it's in a graph and the graph doesn't know it's calling a crew, which is what
> makes the organ replaceable. Three boundaries matter. It holds no write tool, and I enforce that
> with an import-time assertion derived from the same permission table the runtime uses, so a write
> tool reaching the Researcher breaks the process in CI rather than being caught in review — that
> agent reads attacker-controlled text and fetches more of it, so it must never get the third leg of
> the trifecta. Its outputs come back as untrusted values carrying the URL they came from, so a wrong
> claim in a draft traces back to a snippet, a URL and a query. And it gets a *slice* of the run's
> request budget, charged in a `finally` block — without that, a crashing crew is free and a retry
> loop around it is infinitely free, which is how a free tier disappears. One detail I'd defend:
> I parse the classifier's output strictly with a schema and the search snippets leniently, skipping
> malformed lines, because strict parsing of a list of snippets turns a cosmetic model wobble into a
> failed run, while lenient parsing of a structured decision is how format-hijack attacks land."

---

## §11 Done when

```bash
./m check
./m done 80
```
