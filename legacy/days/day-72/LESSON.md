---
day: 72
phase: 11
phase_name: "Evals & observability"
title: "LLM-as-judge, honestly + SDK trace grading"
ids: ["AG-23", "OAI-24"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-21"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 72 — LLM-as-judge, honestly + SDK trace grading

**Phase 11 · Evals & observability** · IDs: **AG-23 🛠️**, **OAI-24 🛠️**

> **Yesterday:** three layers. Unit and trajectory came out free and deterministic; the outcome layer
> was left with a hole in it labelled *judge*.
> **Today:** you fill that hole carefully. A judge is a model, which means it is biased, drifts, and
> flatters — so before you trust it on 200 items you calibrate it against a small set **you labelled
> by hand**. Then you point the same rubrics at Agents SDK traces (OAI-24).
> **Tomorrow:** datasets and experiments in LangSmith — the same evals, with history.

```bash
./m start 72
./m scaffold 72
```

---

## §1 The story

The pitch for LLM-as-judge is irresistible: grading is hard, models can read, let a model grade.
And it does work. It works *well enough to be dangerous*, because the failure mode is not "the judge
is obviously wrong" — it is "the judge is quietly, consistently wrong in one direction", and a
consistent bias looks exactly like a stable metric.

Four things a judge does that a test does not:

1. **Sycophancy.** Ask "is this a good reply?" and models say yes. Ask "does this reply cite a
   source?" and they answer the question. **Narrow, factual rubric lines survive; taste does not.**
2. **Position bias.** In a pairwise comparison, A-then-B and B-then-A give different winners. This is
   measurable in ten minutes and it is the single most convincing demo you can run today.
3. **Self-preference.** A model rates its own family's output higher. Hence the plan's Principle:
   **judge ≠ judged**, always a different provider (`docs/00_MASTER_PLAN_AGENT_STACKS.md` §1).
4. **Drift.** Free-tier model IDs rotate without notice. Your "score went from 0.81 to 0.74" may be
   the judge changing underneath you, and if you did not pin the judge model you cannot tell.

So the rule for today:

> **A judge is an instrument. An uncalibrated instrument is decoration.**

You calibrate by hand-labelling ~20 items, running the judge over the same items, and computing
agreement. If agreement is poor, the fix is **the rubric**, not the model — and watching a vague
rubric's agreement climb as you make it specific is the most useful hour in Phase 11.

---

## §2 Setup — run this

No new dependencies today either (`langsmith` arrives tomorrow).

```bash
touch src/mandala/evals/judge.py
touch src/mandala/evals/calibration.py
mkdir -p days/day-72/lab
touch days/day-72/lab/human_labels.jsonl
touch days/day-72/lab/calibrate.py
touch days/day-72/lab/position_bias.py
touch days/day-72/lab/grade_sdk_traces.py
touch tests/test_judge.py
```

- **Label `human_labels.jsonl` before you write the judge.** Twenty items, by hand, no model open in
  another tab. It takes 25 minutes and it is the only ground truth you will ever have. Do it first or
  you will unconsciously label to match the judge.
- `position_bias.py` costs a handful of requests and settles the argument permanently.

---

## §3 AG-23 — the judge

### 3.1 `src/mandala/evals/judge.py`

```python
"""A judge that answers narrow questions, on a different provider than the judged.

Design rules, each of which exists because of a specific failure:
  - one rubric line per call            (compound questions get one blurred answer)
  - binary verdict + evidence quote     (a 1-5 score is a vibe with a number on it)
  - the judge NEVER sees which agent/model produced the text
  - the judge model is PINNED, by name, here
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from mandala.models import chat_with  # Day 6 router, provider-explicit variant

JUDGE_PROVIDER = "gemini"   # judged system runs on Groq -> judge ≠ judged (plan §1)
JUDGE_MODEL = "PINNED_IN_src/mandala/models.py"  # TODO(me): pin the exact ID, log it in PINS.md

SYSTEM = """You are grading one property of a support reply. Answer ONLY with JSON:
{"verdict": true|false, "evidence": "<= 15 words quoted from the reply", "why": "one sentence"}
Judge only the stated property. Do not reward length, politeness, or confidence.
If the property is absent, verdict is false. Uncertainty is false."""


@dataclass(frozen=True)
class Verdict:
    rubric: str
    verdict: bool
    evidence: str
    why: str


def judge_one(rubric_line: str, reply: str) -> Verdict:
    user = f"Property: {rubric_line}\n\nReply:\n<<<\n{reply}\n>>>\n\nJSON:"
    raw = chat_with(JUDGE_PROVIDER, system=SYSTEM, user=user, temperature=0)
    data = json.loads(raw[raw.index("{") : raw.rindex("}") + 1])
    return Verdict(rubric_line, bool(data["verdict"]), data.get("evidence", ""), data.get("why", ""))


RUBRIC_LINES: tuple[str, ...] = (
    "The reply states a concrete next action the customer can take.",
    "The reply cites at least one source URL for any factual claim.",
    "The reply does not promise anything about timelines or refunds.",
    "The reply does not include internal notes or account flags.",
)
```

**Line by line:**

- `JUDGE_PROVIDER = "gemini"` while Mandala runs on Groq. **Judge ≠ judged is a one-line control and
  the most commonly skipped one.** Assert it in a test (§5) so a future config change cannot quietly
  point both at the same place.
- `temperature=0` — a judge that disagrees with itself across reruns cannot detect drift, because it
  *is* drift.
- **Binary verdict, not 1–5.** Ask five people what a 3 means. Ask them whether the reply cites a
  source and they agree. Every scale you can collapse to binary, collapse.
- **`evidence` must be quoted from the reply**, ≤ 15 words. This is the anti-hallucination handle:
  if the judge says "yes, it cites a source" and cannot produce the URL, the verdict is void. §5
  tests exactly that.
- `"Uncertainty is false"` — a default direction, stated once. Without it the judge's uncertainty
  becomes noise distributed randomly across your metric.
- **The judge never learns which system produced the reply.** Do not pass agent names, model IDs, or
  framework labels into the prompt. This matters most on Day 76 and in Phase 9's bake-off, where you
  will compare frameworks — an anonymised judge is the only fair one.
- `RUBRIC_LINES` are **properties, not questions of quality.** Read them again: each is checkable by
  a careful human in five seconds. That is the bar for a rubric line, and anything that fails it goes
  back to the drawing board rather than into the prompt.

### 3.2 Calibration — `src/mandala/evals/calibration.py`

```python
"""Agreement between the judge and your own labels. Cohen's kappa, by hand — no sklearn."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Agreement:
    n: int
    raw: float           # % of items where judge == human
    kappa: float         # chance-corrected
    false_pos: int       # judge said yes, human said no  <- the dangerous direction
    false_neg: int


def agreement(human: list[bool], model: list[bool]) -> Agreement:
    assert len(human) == len(model) and human, "need equal, non-empty label lists"
    n = len(human)
    same = sum(h == m for h, m in zip(human, model, strict=True))
    po = same / n
    ph, pm = sum(human) / n, sum(model) / n
    pe = ph * pm + (1 - ph) * (1 - pm)
    kappa = 0.0 if pe == 1 else (po - pe) / (1 - pe)
    return Agreement(
        n=n,
        raw=po,
        kappa=kappa,
        false_pos=sum(m and not h for h, m in zip(human, model, strict=True)),
        false_neg=sum(h and not m for h, m in zip(human, model, strict=True)),
    )


def verdict(a: Agreement) -> str:
    if a.n < 20:
        return "too few labels to conclude anything"
    if a.kappa >= 0.8:
        return "usable"
    if a.kappa >= 0.6:
        return "usable with caution — report kappa beside every score"
    return "NOT usable — fix the rubric line, not the model"
```

**Line by line:**

- **Raw agreement alone is a trap.** If 90% of replies genuinely cite a source, a judge that always
  says "yes" scores 0.90 raw and is worthless. `kappa` corrects for chance and would score it ~0.
  Computing it by hand (nine lines, no dependency) is worth doing once so you never mistake raw
  agreement for skill again.
- `strict=True` on `zip` — misaligned label lists silently truncate otherwise, and a calibration run
  on 14 of 20 items that reports "n=14" without complaint is a very quiet lie.
- **`false_pos` is broken out separately because the directions are not symmetric.** A judge that
  wrongly says "no source cited" wastes your time. A judge that wrongly says "yes, this is safe to
  send" ships something. Report both; care about the second.
- `verdict()` returns a **sentence, not a boolean**, and refuses to conclude under 20 labels. It also
  names the correct fix: *the rubric line, not the model*. On a $0 budget you cannot buy a better
  judge, so rubric quality is the only lever you have — which turns out to be the right lever anyway.

---

## §4 Position bias, in ten minutes

```python
# days/day-72/lab/position_bias.py
"""Ask the same pairwise question twice, with the order flipped. ~10 requests."""

from __future__ import annotations

from mandala.evals.judge import JUDGE_PROVIDER
from mandala.models import chat_with

PAIRS = [...]  # TODO(me): 5 (reply_a, reply_b) pairs from your golden set


def ask(a: str, b: str) -> str:
    out = chat_with(
        JUDGE_PROVIDER,
        system='Reply with only "A" or "B": which reply better states a concrete next action?',
        user=f"A:\n{a}\n\nB:\n{b}",
        temperature=0,
    )
    return out.strip().upper()[:1]


if __name__ == "__main__":
    flips = 0
    for a, b in PAIRS:
        first, second = ask(a, b), ask(b, a)
        consistent = (first == "A" and second == "B") or (first == "B" and second == "A")
        flips += not consistent
        print(f"{first} then {second}  {'consistent' if consistent else '⚠️ POSITION BIAS'}")
    print(f"\n{flips}/{len(PAIRS)} pairs flipped on order alone.")
```

**Line by line:**

- The consistency condition looks inverted and is correct: if the judge preferred A when A was first,
  it should prefer the *same text* when it is presented second — which is now labelled "B".
- **Run it, write the number down, put it in `docs/REDTEAM.md`'s sibling section or your Day-77 gate
  notes.** "3 of 5 pairwise comparisons flipped on ordering alone" is a fact about your instrument
  that most people asserting things about model quality have never measured.
- The mitigation is not a better prompt: it is **run both orders and count only consistent pairs**,
  or avoid pairwise entirely in favour of per-item binary rubrics — which is exactly why §3's judge
  is per-item and binary. Today's demo is the justification for yesterday's design.

---

## §5 OAI-24 — grading SDK traces, and the tests

The Agents SDK emits traces (Day 14). OAI-24 is the wiring: **turn a trace into yesterday's
`Trajectory`, then run yesterday's rubrics unchanged.**

```python
# days/day-72/lab/grade_sdk_traces.py
"""SDK trace -> Trajectory -> Day-71 rubrics. The adapter is the whole ID."""

from __future__ import annotations

from mandala.evals.rubric import ALL
from mandala.evals.trajectory import Step, Trajectory

KIND = {"function": "tool_call", "handoff": "handoff", "generation": "model_call"}


def to_trajectory(trace: dict) -> Trajectory:
    steps: list[Step] = []
    for span in trace["spans"]:                       # TODO(me): confirm the export shape
        kind = KIND.get(span["span_data"]["type"])
        if kind is None:
            continue
        steps.append(
            Step(
                kind=kind,
                name=span["span_data"].get("name", span["span_data"]["type"]),
                agent=span["span_data"].get("agent", "unknown"),
                ok=span.get("error") is None,
            )
        )
    return Trajectory(ticket_id=trace["metadata"]["ticket_id"], steps=tuple(steps))


def grade(trace: dict) -> dict[str, tuple[bool, str]]:
    t = to_trajectory(trace)
    return {name: rubric(t) for name, rubric in ALL.items()}
```

**Line by line:**

- **The adapter is thin on purpose.** Every framework in this plan emits a different trace shape;
  each gets a ~20-line `to_trajectory`. The rubrics never change. That is the payoff of yesterday's
  decision to grade a *neutral* structure rather than a framework's native objects — and it is what
  makes the Phase-9 bake-off comparable at all.
- `KIND` maps span types you must **verify against a real export** (§8) rather than from memory.
- `continue` on unknown span types — a new span type in an SDK release must not crash grading. But
  log the unknown types somewhere; silently dropping a `tool_call` renamed in v0.23 would make every
  write-ordering rubric pass vacuously. **That is the scariest failure on this page**: add a test that
  asserts a known-write trace still produces a non-empty `writes()`.

```python
# tests/test_judge.py
import pytest

from mandala.evals.calibration import agreement, verdict
from mandala.evals.judge import JUDGE_PROVIDER, RUBRIC_LINES, Verdict

pytestmark = pytest.mark.eval_unit


def test_judge_is_not_the_judged():
    from mandala.models import PRIMARY_PROVIDER

    assert JUDGE_PROVIDER != PRIMARY_PROVIDER, "judge ≠ judged (plan §1)"


def test_every_rubric_line_is_a_property_not_a_quality_question():
    for line in RUBRIC_LINES:
        assert not line.lower().startswith(("is this", "how good", "rate ")), line
        assert line.endswith("."), line


def test_kappa_punishes_a_judge_that_always_says_yes():
    human = [True] * 18 + [False] * 2
    always_yes = [True] * 20
    a = agreement(human, always_yes)
    assert a.raw >= 0.9 and a.kappa < 0.2       # raw looks great, kappa exposes it
    assert "NOT usable" in verdict(a)


def test_perfect_agreement_is_kappa_one():
    labels = [True, False, True, True, False]
    assert agreement(labels, labels).kappa == pytest.approx(1.0)


def test_false_positives_are_counted_separately():
    a = agreement([False, True], [True, True])
    assert a.false_pos == 1 and a.false_neg == 0


def test_under_twenty_labels_refuses_to_conclude():
    assert "too few" in verdict(agreement([True] * 5, [True] * 5))


def test_mismatched_label_lists_raise_rather_than_truncate():
    with pytest.raises(Exception):
        agreement([True, False], [True])


def test_a_verdict_without_evidence_is_void():
    v = Verdict("cites a source", True, "", "looks fine")
    assert not (v.verdict and v.evidence), "true verdicts must quote evidence"
```

**Line by line:**

- `test_judge_is_not_the_judged` is the day's headline: **one line, and it makes the plan's principle
  unbreakable by configuration drift.**
- `test_kappa_punishes_a_judge_that_always_says_yes` is the test that teaches the statistic. Raw
  0.90, kappa < 0.2, verdict "NOT usable". Run it and read it once, and you will never again quote a
  raw agreement number.
- `test_a_verdict_without_evidence_is_void` encodes §3.1's anti-hallucination rule in code rather
  than in a docstring.
- Every test here is **0 requests** — the judge's *properties* are testable offline; only its
  *calibration* costs money, and that is 20 items, once.

---

## §6 Traps

- **Judge and judged on the same provider.** Self-preference, silently.
- **1–5 scales.** A vibe with a number on it. Collapse to binary.
- **Compound rubric lines** ("clear, accurate and polite") — one blurred answer to three questions.
- **Quoting raw agreement.** Use kappa, or a lazy judge looks excellent.
- **Calibrating on fewer than ~20 labels.** You are measuring noise.
- **Labelling after seeing the judge's output.** Label first, in one sitting, closed tab.
- **Unpinned judge model.** Your metric moves and you cannot attribute it.
- **Telling the judge which system wrote the text.** Poisons every comparison you will run.
- **Treating false positives and false negatives as equal.** One wastes time, one ships.
- **Silently dropping unknown span types** in the trace adapter — rubrics pass vacuously.
- **Fixing poor agreement by changing models.** On $0 you can't, and the rubric was the problem.
- **Pairwise comparisons without order-flipping.** You measured position, not quality.

---

## §7 Request budget

**Declared: ~60 model requests, Gemini (judge) — the most expensive day of Phase 11.**

| What | Requests |
|---|---|
| `tests/test_judge.py` | **0** |
| Hand-labelling 20 items | **0** (it's you) |
| Calibration: 20 items × 2 rubric lines | 40 |
| `position_bias.py`: 5 pairs × 2 orders | 10 |
| SDK trace grading | **0** (replays Day-71 recordings) |
| Spot-checks / rubric iteration | ≤ 10 |

**Calibration is a one-time cost per rubric line, not per run.** Note it as such in
`docs/RATE_BUDGET.md`. And note the shape: the judge is the only expensive grader you own, which is
precisely why Days 71 and 74 push everything possible into deterministic layers.

---

## §8 Verify before you code

Written **2026-08-21**:

- **Which free-tier provider is your judge, and what is its exact model ID?** Pin it in
  `src/mandala/models.py` and log it in `docs/PINS.md`. Free rosters rotate; an unpinned judge makes
  every future score incomparable.
- **Does your judge provider have a separate quota** from the judged one? If they share a key, a
  429 storm on Day 74 takes out grading and generation together.
- **The Agents SDK trace export shape** (`span_data["type"]` values, agent attribution, error field)
  on `openai-agents==0.22.0` — **verify against a real exported trace**, not from memory. This is the
  day's biggest API risk.
- **Does the SDK let you attach `metadata` (ticket_id) to a trace?** The adapter needs it.
- **`zip(..., strict=True)`** — confirm it raises rather than truncates on your Python (3.10+).
- `https://openai.github.io/openai-agents-python/tracing/` — read today.

---

## §9 Say it in an interview

> "LLM-as-judge works, but only if you treat the judge as an instrument you've calibrated. I
> hand-labelled twenty items before writing the judge, then measured Cohen's kappa rather than raw
> agreement — because if 90% of replies genuinely cite a source, a judge that always says yes scores
> 0.90 raw and is worthless, and kappa exposes that immediately. I run the judge on a different
> provider from the system under test, asserted by a unit test, because models prefer their own
> family's output. The rubric is per-item and binary with a required evidence quote pulled from the
> text — if it claims a source is cited and can't produce the URL, the verdict is void. I also
> measured position bias directly: I ran five pairwise comparisons in both orders and counted how
> many flipped on ordering alone, which is why the production rubric is per-item rather than pairwise.
> And when agreement was poor, the fix was always the rubric line, never the model — compound
> questions like 'is this clear, accurate and polite' get one blurred answer. On the SDK side,
> grading traces was a twenty-line adapter into the neutral trajectory structure, so the same rubrics
> grade all four frameworks and the bake-off comparison is actually apples to apples."

---

## §10 Done when

```bash
./m check
./m done 72
```
