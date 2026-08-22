---
day: 28
phase: 4
phase_name: "CrewAI Crews"
title: "`crewai test`, `crewai train`, and crew observability"
ids: ["CR-11", "CR-12"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 28 — `crewai test`, `crewai train`, and crew observability

**Phase 4 · CrewAI Crews** · IDs: **CR-11 🛠️**, **CR-12 🛠️**

> **Yesterday:** knowledge sources, and the guardrail that closed a gap you had been carrying since
> Day 24.
> **Today:** the framework's own evaluation harness — which is not the same thing as an eval — a
> training command that changes your prompts without asking, and callbacks that make a CrewAI run
> readable by the trace viewer you wrote two weeks ago.
> **Tomorrow:** Mandala-mini, the Phase-4 gate crew.

```bash
./m start 28
./m scaffold 28
```

---

## §1 The story

The Phase-4 gate says Mandala-mini must **pass `crewai test` thresholds.** So today, the day before
the gate, you find out what that command actually measures — *before* you are graded on it rather
than during.

The answer is going to be uncomfortable, and it is the most useful thing in this lesson:

> **`crewai test` runs your crew several times and asks an LLM to score each task out of ten.**

That is a smoke test with opinions. It is genuinely useful — it catches "the crew got dramatically
worse", it costs you nothing to interpret, and it produces a number you can watch. It is **not** an
eval in the sense Principle 7 means: *"a behavior isn't done until a test can fail when it
regresses."* An LLM scorer drifts, flatters, and disagrees with itself between runs.

Mandala already has the other kind — `tests/test_golden_set.py` from Day 8, deterministic, free, red
when behaviour breaks. **Today's job is to run both and be clear about which is which**, because the
gate names one of them and Principle 7 names the other, and a person who confuses them ships a crew
that scores 8.4 and cannot triage a ticket.

Then `crewai train`, which is the one to be genuinely careful about. It runs the crew, collects your
feedback, and writes learned prompt adjustments into a file that is loaded on subsequent runs. Read
that again with Day 6 in mind — *prompts are APIs: versioned, testable, ablatable* — and you will see
why §3.4 spends real words on it.

And finally the good news. CrewAI's callbacks let you write a run's events wherever you like. You
already have a trace format and a viewer: Day 14's JSONL processor and `span_tree.py`. **By the end
of today, `span_tree.py` renders a CrewAI run** — the same reader, two frameworks. That is Principle
8's portability claim stopping being a claim.

---

## §2 Setup — run this

No new packages. **OpenTelemetry is Day 75** and the ledger says so; today's exporter is the one you
already wrote.

```bash
mkdir -p days/day-28/lab
touch src/mandala/crew/observability.py
touch days/day-28/lab/traced_crew.py
touch days/day-28/lab/score_report.py
touch tests/test_crew_observability.py
```

`crewai test` and `crewai train` are CLI commands that expect the **generated project layout** you
declined on Day 23 (§2.1) — `crew.py` with `@CrewBase`, `main.py`, `config/`. Mandala's crew lives in
`src/mandala/crew/` instead.

**Decide this deliberately rather than discovering it tomorrow.** Two honest options:

| Option | What it costs | What it buys |
|---|---|---|
| **A. Adopt the CLI layout for one crew** — add a thin `@CrewBase` wrapper that builds the existing objects | ~30 lines of adapter | `crewai test` / `crewai train` work as documented; the gate criterion is literally satisfiable |
| **B. Call the evaluation API directly** from a script | you must find the API under the CLI | no layout change, but the gate wording ("passes `crewai test`") gets fuzzy |

**Take option A.** The gate names the command, the adapter is small, and a wrapper that constructs
objects you already own does not duplicate anything. Write it in `src/mandala/crew/crew_entry.py`
as a `@CrewBase` class whose `@crew` method returns the crew that `days/day-27` already builds.

**TODO(me):** confirm what `crewai test` requires to discover a crew in 1.15.17 — a `crew.py` at a
specific path, an entry in `pyproject.toml`, or a `@CrewBase` subclass anywhere importable. Get this
right today; tomorrow is the gate.

---

## §3 CR-11 — Testing and training crews

### 3.1 What `crewai test` actually does

```bash
uv run crewai test -n 3 -m openrouter/<a-free-model>
```

- `-n 3` — run the crew three times
- `-m` — **the model used to score**, not the model the crew runs on
- output — a table of tasks × runs with scores out of 10, plus averages

**`-m` is the flag that matters on this project**, for a reason `docs/RATE_BUDGET.md` has stated
since Day 1: **rule 1, judge ≠ judged.** Your crew runs on Groq. If the scorer also runs on Groq, you
have a model grading its own family's output, and the number moves for reasons that have nothing to
do with your crew. Point it at OpenRouter — the provider `judge_llm()` has used since Day 23,
existing precisely for this moment.

If `-m` did not exist, `crewai test` would be unusable here on principle. Check that it does.

### 3.2 What the score is, and is not

| | `crewai test` | `tests/test_golden_set.py` (Day 8) |
|---|---|---|
| Verdict | a number, 1–10, from an LLM | pass/fail, from an assertion |
| Deterministic | **no** | yes |
| Costs model requests | yes — crew runs **plus** scorer calls | **no** |
| Can fail in CI | not meaningfully | **yes** |
| Detects "slightly worse" | sometimes | no |
| Detects "completely broken" | yes | **yes** |
| Tells you *what* broke | no | the failing case |
| Satisfies Principle 7 | **no** | **yes** |

**Both rows are worth having and neither replaces the other.** The honest framing:

> `crewai test` is a **thermometer**. `test_golden_set.py` is a **tripwire**. You want the tripwire in
> CI and the thermometer on the wall.

So Mandala's position for tomorrow's gate: the crew must pass the golden set (deterministic, the real
requirement under Principle 7) **and** meet a `crewai test` threshold you set today. Setting the
threshold before you are graded is not gaming it — it is the only way the number means anything.
A threshold chosen after seeing the score is a threshold that always passes.

**Set it now:** run `crewai test -n 3` once on the Day-27 crew, look at the per-task averages, and
write a threshold into your CHECKLIST that the current crew clears **with a little room, not much**.
If the crew scores 8.1, a threshold of 7.5 is honest and 6.0 is theatre.

### 3.3 `days/day-28/lab/score_report.py`

Run it several times and look at the spread, because the spread is the point:

```python
"""Run crewai test repeatedly and report the VARIANCE, not just the score.

A single score tells you almost nothing. Three scores tell you whether the number
is a signal or a mood.

Run:
    uv run python days/day-28/lab/score_report.py --rounds 3
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
from pathlib import Path

OUT = Path(".mandala/crew_scores.json")
SCORE_LINE = re.compile(r"([\d.]+)\s*$")


def one_round(scorer_model: str) -> list[float]:
    """TODO(me): crewai test prints a table. Parse it, or find the API that returns
    the scores as data. Screen-scraping a CLI table is fragile and you will know it
    is fragile the first time the column widths change -- prefer the API if one exists."""
    raise NotImplementedError


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--model", default="openrouter/<pin-a-free-model>")
    args = parser.parse_args()

    rounds = [one_round(args.model) for _ in range(args.rounds)]
    flat = [s for r in rounds for s in r]

    print(f"rounds     : {args.rounds}")
    print(f"all scores : {flat}")
    print(f"mean       : {statistics.mean(flat):.2f}")
    print(f"stdev      : {statistics.pstdev(flat):.2f}")
    print(f"range      : {min(flat):.1f} - {max(flat):.1f}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"rounds": rounds}, indent=2), encoding="utf-8")
    print(f"\nwritten to {OUT}  <- commit-adjacent history, gitignored")


if __name__ == "__main__":
    main()
```

**Line by line:**

- **The variance is the finding, not the mean.** If the same unchanged crew scores 8.4, 6.9 and 8.0,
  then a drop to 7.2 next week means nothing, and your threshold has to sit below the noise floor.
  Most people run this once, see 8.4, and treat it as a measurement.
- `--model` defaults to an OpenRouter pin — the judge-≠-judged rule expressed as a default rather
  than as a thing to remember (the sixth time this curriculum has made the safe value the default).
- `one_round` is a **`TODO(me)`** with the trade written into the docstring: parsing a CLI table is
  fragile, so look for the underlying API first. Finding out whether one exists is the rep, and the
  answer also determines whether §5 can test any of this.
- Writing to `.mandala/crew_scores.json` — gitignored (yesterday you promoted that rule), but kept,
  because **a score without history is a number and a score with history is a trend.**
- `pstdev` over `stdev` — population, because these are all the samples you have, not an estimate.
  A small thing; the wrong one on three samples is misleading in the direction that flatters you.

### 3.4 `crewai train`, and why Mandala does not use it by default

```bash
uv run crewai train -n 5 -f trained_agents_data.pkl
```

It runs the crew, asks you for feedback after each iteration, and writes learned prompt adjustments
to a file that is loaded automatically on later runs.

The idea is good. The artifact is the problem:

| Day 6 said a prompt should be… | A trained-agents pickle is… |
|---|---|
| **versioned** | a binary blob with no version |
| **reviewable in a diff** | unreadable in `git diff` |
| **testable / ablatable** | not addressable — you cannot A/B one adjustment |
| **explicit at the call site** | **loaded implicitly, changing behaviour with no code change** |

That last row is the serious one. **A file that silently alters your prompts is a change to your
system that never went through review.** Six weeks later, someone clones the repo, the pickle is or
is not present, and the crew behaves differently for reasons no diff explains.

**Mandala's position, and it is a position rather than a rule:**

> Run `crewai train` as a **prompt-discovery tool** — use it to find out *what* feedback improves the
> crew — then hand-write the improvement into `mandala.prompts` where it is versioned, diffable and
> testable. Do not ship the pickle.

You lose the automation and keep the audit trail. If you disagree, that is fine — but write the
disagreement down in the bake-off list, because it is exactly the kind of trade Phase 9 is for.

**And if you do ship it:** gitignore it or commit it deliberately, never leave it ambiguous, and add
its presence to the gate evidence table. A hidden input is only dangerous when it is hidden.

---

## §4 CR-12 — Crew observability

### 4.1 Two callbacks, and what each can see

```python
Crew(
    ...,
    step_callback=on_step,      # fires per agent step (thought / tool call / observation)
    task_callback=on_task,      # fires when a task completes
)
```

Compare with what you have had:

| | `verbose=True` (Day 25) | callbacks (today) | Day 14's SDK tracing |
|---|---|---|---|
| Destination | your terminal | **anywhere you want** | a JSONL file |
| Structured | no | **yes** | yes |
| Queryable later | no | yes | yes |
| Redactable | **no — it prints ticket bodies** | **yes** | yes (allowlist) |
| Survives the process | no | yes | yes |

**Row four is why today matters more than it looks.** `verbose=True` has been printing customer
ticket text into your scrollback since Day 25. Callbacks let you write the *shape* of a run without
the *content* — which is the exact decision Day 14 made with `SAFE_SPAN_FIELDS`, arriving now in a
second framework.

### 4.2 `src/mandala/crew/observability.py`

```python
"""CrewAI callbacks that write Day 14's trace format. One reader, two frameworks.

Why this file exists
--------------------
Principle 8 says the trace is the truth, and that a truth you can only read inside
one vendor's tooling is one you lose when you switch frameworks -- which this plan
does four times. Day 14 built a JSONL span format and days/day-14/lab/span_tree.py
to read it. This module makes a CrewAI run emit the SAME format, so span_tree.py
renders it with no changes.

That is the whole claim of Principle 8, made checkable: if span_tree.py can draw a
CrewAI run, the format is portable. If it cannot, it was never portable and Day 75's
OTel migration will be worse than expected.

Redaction is Day 14's rule, unchanged: an ALLOWLIST of fields, capped lengths, and
nothing that can carry a ticket body.

Usage
-----
    >>> from mandala.crew.observability import crew_callbacks
    >>> set(crew_callbacks("req-1")) == {"step_callback", "task_callback"}
    True
"""

from __future__ import annotations

import uuid
from typing import Any

from mandala.tracing import JsonlTraceProcessor, _shrink

SAFE_STEP_FIELDS = ("tool", "tool_name", "action", "thought_present", "finish_reason")
SAFE_TASK_FIELDS = ("name", "agent", "expected_output_present", "retry_count")


def _record(kind: str, payload: dict) -> dict:
    return {"kind": kind, **{k: _shrink(v) for k, v in payload.items()}}


def crew_callbacks(request_id: str, processor: JsonlTraceProcessor | None = None) -> dict:
    """Build step/task callbacks that append to one trace file for this run."""
    proc = processor or JsonlTraceProcessor()
    trace_id = f"crew-{request_id}"
    proc._write(trace_id, {"kind": "trace_start", "trace_id": trace_id,
                           "workflow_name": "mandala.crew", "group_id": request_id})

    def on_step(step: Any) -> None:
        fields = {f: getattr(step, f, None) for f in SAFE_STEP_FIELDS}
        # `thought` may contain reasoning ABOUT ticket text -- record only that it existed.
        fields["thought_present"] = bool(getattr(step, "thought", None))
        proc._write(trace_id, _record("span", {
            "span_id": uuid.uuid4().hex[:16], "parent_id": None,
            "trace_id": trace_id, "data": fields,
        }))

    def on_task(task_output: Any) -> None:
        fields = {f: getattr(task_output, f, None) for f in SAFE_TASK_FIELDS}
        fields["expected_output_present"] = bool(getattr(task_output, "expected_output", None))
        fields["output_len"] = len(str(getattr(task_output, "raw", "")))   # LENGTH, not content
        proc._write(trace_id, _record("span", {
            "span_id": uuid.uuid4().hex[:16], "parent_id": None,
            "trace_id": trace_id, "data": fields,
        }))

    return {"step_callback": on_step, "task_callback": on_task}
```

**Line by line:**

- Importing `JsonlTraceProcessor` and `_shrink` **from `mandala.tracing`** — Day 14's module, reused
  rather than reimplemented. If the redaction rule changes, it changes once for both frameworks.
  (Importing an underscore-prefixed helper across modules is a smell; **TODO(me): promote `_shrink`
  to `shrink` in `mandala/tracing.py` now that it has a second caller.** A private name with two
  callers is public and should say so.)
- `SAFE_STEP_FIELDS` / `SAFE_TASK_FIELDS` — **allowlists again**, the fourth time (span data, search
  ops, workspace paths, now callbacks). By now the reflex should be automatic: when writing
  model-adjacent data to disk, name what goes in, never what stays out.
- `fields["thought_present"] = bool(getattr(step, "thought", None))` — this is the line to notice. An
  agent's *thought* is reasoning about the ticket and frequently quotes it. **Record that a thought
  happened, not what it said.** Day 5's naked trace made the same call with `result_len`; Day 14
  repeated it; here it is again.
- `fields["output_len"] = len(...)` — length, not content, for the same reason. A trace that tells
  you a task produced 40 characters when it normally produces 400 has told you almost everything you
  need, without storing a word of it.
- `parent_id: None` on every span — honest and unsatisfying: CrewAI's callbacks do not hand you a
  parent relationship, so today's crew traces render **flat** in `span_tree.py`, while Day 14's SDK
  traces render as a tree. **TODO(me): can you reconstruct nesting from task boundaries?** That is a
  real, bounded piece of work and it is where today's payoff gets better.
- `proc._write(...)` for `trace_start` — reusing the file format's opening record so `span_tree.py`'s
  header (`workflow`, `group_id`) populates. The reader was written to expect it; matching the format
  exactly is what makes "one reader, two frameworks" true rather than nearly true.

### 4.3 `days/day-28/lab/traced_crew.py` — the payoff

```python
"""Run yesterday's guarded crew with callbacks, then read it with Day 14's viewer.

Run:
    uv run python days/day-28/lab/traced_crew.py T-1004
    uv run python days/day-14/lab/span_tree.py          # <- the Agents SDK viewer, unchanged
"""

from __future__ import annotations

import sys

from crewai import Crew, Process

from guardrail_demo import build as build_guarded_crew    # Day 27's crew
from mandala.crew.observability import crew_callbacks
from mandala.sdk_tools import RAW_TICKETS


def main() -> None:
    ticket_id = sys.argv[1] if len(sys.argv) > 1 else "T-1004"
    request_id = f"req-{ticket_id}"

    base = build_guarded_crew(guarded=True)
    crew = Crew(
        agents=base.agents,
        tasks=base.tasks,
        process=Process.sequential,
        memory=False,
        verbose=False,                      # callbacks replace it -- see the §4.1 table
        **crew_callbacks(request_id),
    )

    result = crew.kickoff(inputs={"ticket_id": ticket_id,
                                  "ticket_body": RAW_TICKETS[ticket_id]["body"]})
    print(f"done. tokens={result.token_usage}")
    print("now run: uv run python days/day-14/lab/span_tree.py")


if __name__ == "__main__":
    main()
```

**Then run `span_tree.py` and check three things:**

1. It renders without crashing. *(The format matched.)*
2. `grep -ril "PINEAPPLE" .mandala/traces/` finds nothing. *(The allowlist held — run the T-9002
   ticket to test this properly.)*
3. `model_calls` reports something sensible, or reports **0** — and if it reports 0, that is the
   Day-14 open verification item finally biting: the counter matches on `"Generation"` in the span
   data type, and CrewAI callbacks do not produce that. **Fix the counter to recognise both
   frameworks' shapes**, and note that this is the third time that open item has mattered.

**Line by line:**

- `verbose=False` with the pointed comment — today is the day you turn it off for good. Callbacks give
  you more information, structured, redacted, and persistent.
- Importing Day 27's `build` rather than constructing a new crew — **the guardrails stay on while you
  add observability.** Adding a cross-cutting concern to a crew that has lost its security controls
  is how you end up shipping the observable version of the wrong thing.
- The printed instruction to run `span_tree.py` — because the payoff is the second command, and a lab
  whose punchline is in a different file should say so.

---

## §5 The eval that must be able to fail

### `tests/test_crew_observability.py`

```python
"""Callbacks must be redacting, cheap, and format-compatible with Day 14. 0 model requests."""

import json

import pytest

from mandala.crew.observability import SAFE_STEP_FIELDS, SAFE_TASK_FIELDS, crew_callbacks
from mandala.tracing import JsonlTraceProcessor

CANARY = "PINEAPPLE-7731"


class FakeStep:
    tool = "get_ticket"
    thought = f"The customer mentioned {CANARY} in their message"
    finish_reason = "stop"


class FakeTaskOutput:
    name = "research"
    agent = "Senior Support Triage Analyst"
    expected_output = "CATEGORY, FINDINGS, ACTION"
    raw = f"Customer wrote: {CANARY}"


def _trace_text(tmp_path) -> str:
    return "".join(p.read_text(encoding="utf-8") for p in tmp_path.glob("*.jsonl"))


def test_a_thought_is_recorded_as_a_boolean_not_as_text(tmp_path):
    """The line that matters. FLIP IT: record `thought` itself and watch the canary land."""
    cbs = crew_callbacks("t1", JsonlTraceProcessor(tmp_path))
    cbs["step_callback"](FakeStep())
    text = _trace_text(tmp_path)
    assert CANARY not in text
    assert "thought_present" in text


def test_task_output_is_recorded_as_a_length_not_as_content(tmp_path):
    cbs = crew_callbacks("t1", JsonlTraceProcessor(tmp_path))
    cbs["task_callback"](FakeTaskOutput())
    text = _trace_text(tmp_path)
    assert CANARY not in text
    assert "output_len" in text


def test_unknown_fields_never_reach_disk(tmp_path):
    """The allowlist fails CLOSED -- the fourth time this project has needed that."""

    class Sneaky:
        tool = "get_ticket"
        ticket_body = f"raw body containing {CANARY}"

    cbs = crew_callbacks("t1", JsonlTraceProcessor(tmp_path))
    cbs["step_callback"](Sneaky())
    assert CANARY not in _trace_text(tmp_path)


def test_every_record_is_one_json_line(tmp_path):
    cbs = crew_callbacks("t1", JsonlTraceProcessor(tmp_path))
    cbs["step_callback"](FakeStep())
    cbs["task_callback"](FakeTaskOutput())
    for path in tmp_path.glob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            json.loads(line)          # must not raise


def test_the_trace_opens_with_a_trace_start_record(tmp_path):
    """Day 14's reader expects it. Format compatibility is the whole point."""
    crew_callbacks("t1", JsonlTraceProcessor(tmp_path))
    first = json.loads(_trace_text(tmp_path).splitlines()[0])
    assert first["kind"] == "trace_start"
    assert first["workflow_name"] == "mandala.crew"


def test_day_14s_reader_can_load_a_crew_trace(tmp_path):
    """Principle 8, asserted rather than claimed. If this fails, 'portable' was a word."""
    import sys

    sys.path.insert(0, "days/day-14/lab")
    from span_tree import load                      # noqa: E402

    cbs = crew_callbacks("t1", JsonlTraceProcessor(tmp_path))
    cbs["step_callback"](FakeStep())
    path = next(tmp_path.glob("*.jsonl"))
    records = load(path)
    assert records and all("kind" in r for r in records)


def test_a_broken_callback_does_not_kill_the_run(tmp_path):
    """Day 14's rule: instrumentation that can take down the run is worse than none."""

    class Explodes:
        def __getattr__(self, name):
            raise RuntimeError("boom")

    cbs = crew_callbacks("t1", JsonlTraceProcessor(tmp_path))
    cbs["step_callback"](Explodes())          # must not raise
    assert True


@pytest.mark.skip(reason="TODO(me): score parsing depends on §3.3's unanswered question")
def test_the_score_threshold_is_recorded_and_below_the_noise_floor():
    """Once score_report.py works: assert the committed threshold is below mean - stdev."""
```

**Line by line:**

- `FakeStep.thought` **contains the canary on purpose.** The fake is built to be hostile, which is the
  only way a redaction test means anything — a fake with clean data passes whatever you write.
- `test_a_thought_is_recorded_as_a_boolean_not_as_text` carries the flip, and it is a one-character
  change (`bool(...)` → the value) that turns a safe tracer into a leaking one. That is exactly the
  kind of edit a well-meaning refactor makes.
- `test_unknown_fields_never_reach_disk` with the `Sneaky` class — the allowlist proved against a
  field nobody anticipated, which is the only interesting case. A denylist passes this test only if
  you thought of `ticket_body` in advance.
- `test_day_14s_reader_can_load_a_crew_trace` is the **Principle 8 test**, and it is the reason
  today's file was written to match a two-week-old format instead of inventing a nicer one. If it
  fails, "portable" was a word in a document.
- `test_a_broken_callback_does_not_kill_the_run` — Day 14 made this argument for its processor;
  callbacks run *inside* the agent loop, so the argument is stronger here, not weaker. Note the test
  passes only because `JsonlTraceProcessor._write` swallows exceptions; if your `on_step` does
  attribute access **outside** that `try`, this goes red and it should.
- The skipped threshold test closes the loop with §3.2: once you can parse scores, the committed
  threshold should be asserted to sit **below the noise floor**, so a passing gate means something.

---

## §6 Traps

- **Treating a `crewai test` score as an eval.** It is an LLM's opinion, it drifts, and it cannot
  fail in CI. Principle 7 wants a tripwire; this is a thermometer. **The trap of the day.**
- **Scoring with the same provider the crew runs on.** `docs/RATE_BUDGET.md` rule 1 — judge ≠ judged.
  Pass `-m` and point it at OpenRouter.
- **Running `crewai test` once and believing the number.** Run it three times and look at the spread
  before you choose a threshold.
- **Choosing the threshold after seeing the score.** That is a threshold that always passes.
- **Shipping `trained_agents_data.pkl`.** A binary file that silently changes your prompts is a
  behaviour change that never went through review, and `git diff` cannot show it.
- **Leaving the pickle's presence ambiguous.** Gitignore it or commit it on purpose. A hidden input
  is only dangerous while it is hidden.
- **Recording an agent's `thought` verbatim.** Thoughts quote ticket text. Record that one happened.
- **Inventing a nicer trace format.** You have a reader. A second format means a second reader and
  Principle 8 quietly becomes false.
- **Leaving `verbose=True` on now that callbacks exist.** It prints customer text to a terminal that
  redacts nothing and persists nothing useful.
- **Adding observability to an unguarded crew.** You end up with an excellent trace of the wrong
  system. Keep Day 27's guardrails on.
- **Ignoring `model_calls` reporting 0.** That is Day 14's open verification item, third time of
  asking, and tomorrow's gate quotes a call count.
- **Doing the `crewai test` layout work tomorrow.** The gate names the command; discovering the
  adapter is needed on gate day is how a gate gets narrowed.

---

## §7 Request budget

| Activity | Requests |
|---|---|
| `crewai test -n 3` — crew runs | ~45 (Groq) |
| `crewai test -n 3` — scorer calls | ~9 (**OpenRouter — watch the ~50/day cap**) |
| `score_report.py --rounds 3` | ~135 Groq + ~27 OpenRouter |
| `traced_crew.py` × 2 | ~18 (Groq) |
| `crewai train -n 3` (optional, discovery only) | ~45 (Groq) + your attention |
| **Total** | **≈ 240 Groq, ≈ 36 OpenRouter** |

**This is the most expensive day in the plan, and one line of it is genuinely risky.** OpenRouter's
free tier is roughly **50 requests per day** (`docs/RATE_BUDGET.md`), and `score_report.py --rounds 3`
spends ~27 of them. Options, in order of preference:

1. **Run `score_report.py` with `--rounds 2`** and say so — enough to see spread, half the judge cost.
2. Run the variance check once today and never again; the threshold only needs setting once.
3. Skip `crewai train` entirely — it is discovery, not a deliverable, and §3.4 says not to ship its
   output anyway.

**Do not spend tomorrow's judge budget today.** The gate needs scorer calls, and an exhausted
OpenRouter quota on Day 29 means the gate criterion cannot be evaluated at all.

---

## §8 Verify before you code

Written **2026-08-20** against `crewai` **1.15.17**.

- **How `crewai test` discovers a crew in 1.15.17** — a `crew.py` at a fixed path, a `pyproject.toml`
  entry, or any importable `@CrewBase`? This decides §2's adapter and it must be settled **today**.
- **Confirm `-m` selects the scoring model** and accepts a LiteLLM provider string
  (`openrouter/...`). If it does not, `crewai test` cannot satisfy judge ≠ judged and the gate
  criterion needs an amendment — log it in `docs/CHANGELOG_PLAN.md` rather than quietly scoring with
  the wrong model.
- **Is there an API under the `crewai test` CLI** that returns scores as data? §3.3's `TODO(me)` and
  §5's skipped test both depend on the answer.
- `https://docs.crewai.com/concepts/crews` — confirm `step_callback` and `task_callback` exist at
  crew level in 1.15.17, their exact signatures, and **what object each receives**. This lesson uses
  defensive `getattr` because it does not know; replace that with real attribute access once you do.
- Confirm whether callbacks can also be set **per agent**, and whether an exception inside a callback
  propagates into the run. §5's last test assumes the processor's `try` is what saves you.
- CR-12 mentions **LLM events** — `finish_reason`, sampling params, response ids. Find where these
  surface. **`finish_reason == "length"` is worth alerting on**: a truncated response is the usual
  cause of a `output_pydantic` validation failure, and it looks like a model quality problem.
- Confirm `crewai train`'s output path and format, and whether its effect is automatic on later runs.
  §3.4's whole argument rests on "loaded implicitly".

---

## §9 Say it in an interview

> "`crewai test` runs the crew a few times and has an LLM score each task out of ten. It's useful —
> it catches a crew that's got dramatically worse — but I'd push back on calling it an eval. It's
> non-deterministic, it can't fail in CI, and it doesn't tell you *what* broke. So I ran it three
> times on an unchanged crew first and looked at the spread, because a single score is a mood. Then
> I set a threshold below the noise floor and wrote it down before I was graded on it. Alongside it I
> kept a deterministic golden-set test that costs zero model calls and goes red when behaviour
> regresses. The thermometer goes on the wall; the tripwire goes in CI."

> "The observability piece is the one I'm happiest with. Two weeks earlier I'd written a JSONL trace
> format and a little span-tree viewer for the OpenAI Agents SDK, with an allowlist so customer text
> never reaches disk. When I got to CrewAI's callbacks I deliberately emitted the *same* format
> instead of inventing a nicer one — so the same viewer renders both frameworks, and I have a test
> asserting the old reader can load a new trace. That's what 'portable traces' has to mean if it
> means anything: not that you *could* migrate, but that you did, and a test proves it. The redaction
> rule carried over too — I record that an agent had a thought, not what the thought said, because
> agent reasoning quotes the customer's text constantly."

---

## §10 Done when

```bash
./m check
./m done 28
```

Tomorrow is the **Phase-4 gate**: Mandala-mini — three agents, real tools, memory on, knowledge
attached, structured outputs, guardrails — passing both the golden set and the threshold you set
today. Everything from Days 23–28 assembles into one crew. Check your OpenRouter quota before you
start, and re-read the note about `model_calls` reporting zero.
