---
day: 76
phase: 11
phase_name: "Evals & observability"
title: "Rate limits are the budget; caching and tiering"
ids: ["AG-26", "LG-19", "LG-22"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-21"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 76 — Rate limits are the budget; caching and tiering

**Phase 11 · Evals & observability** · IDs: **AG-26 🛠️**, **LG-19 🅿️**, **LG-22 🛠️**

> **Yesterday:** every model call now emits a span with provider, model, tokens and retry status.
> **Today:** you read those spans and find out what Mandala actually costs — in the only currency
> this project has, which is **requests per minute and per day**. Then you cut it: caching, context
> pruning, model tiering per node, and provider rotation as a resilience pattern.
> **Tomorrow:** the Phase-11 gate, whose central question is *"what did today cost?"* — and today is
> the day you build the thing that answers it.

```bash
./m start 76
./m scaffold 76
```

---

## §1 The story

Every cost article you have ever read is about dollars per million tokens. **On a $0 budget that
number is zero and completely irrelevant.** Your currency is different:

| Conventional | Yours |
|---|---|
| $ per 1M tokens | **requests per minute** (burst ceiling) |
| monthly bill | **requests per day** (hard stop) |
| latency SLO | **tokens per minute** (throughput ceiling) |
| provider outage | **429 → rotate or fail** |

That changes which optimisations matter. Shortening prompts saves tokens, which matters for the TPM
ceiling but does nothing for RPD. **Avoiding a call entirely is the only thing that helps every
ceiling at once** — so the order of attack today is: cache it, then tier it, then prune it.

And one reframe worth having explicitly, because it connects Phase 10 to Phase 11:
**RT-12 from the red team was a denial-of-service attack on your quota.** A ticket engineered to make
the agent loop is indistinguishable from a genuinely hard ticket that makes the agent loop. So
budgets are not only economics — they are the availability control. Today's per-run budget assertion
is the fix you promised on Day 69.

LG-19 is a **🅿️ literacy row**: LangSmith's managed layer (Fleet, Insights, full-workflow cost
tracking) is where a funded team would get this dashboard. You are building the free version, and
you should be able to say in one paragraph what the paid one adds — that comparison is §5.

---

## §2 Setup — run this

No new dependencies. Everything reads yesterday's `.traces/*.jsonl`.

```bash
touch src/mandala/obs/costs.py
touch src/mandala/router/cache.py
touch src/mandala/router/budget.py
mkdir -p days/day-76/lab
touch days/day-76/lab/cost_report.py
touch days/day-76/lab/tiering_experiment.py
touch tests/test_budget.py
touch tests/test_cache.py
```

Before writing anything, **fill in the live numbers**:

```bash
open docs/RATE_BUDGET.md   # Day 1 created it; Days 68/72/73/75 added rows
```

If any provider's RPM/RPD is still marked TBD, go and find it now. **Every optimisation today is
measured against those ceilings, and optimising against a guessed ceiling is how you tune for the
wrong constraint.**

---

## §3 AG-26 — measure first

### 3.1 `src/mandala/obs/costs.py`

```python
"""Read .traces/*.jsonl and answer: what did today cost, and where did it go?

There is no money here. The report is denominated in REQUESTS, because requests are
what run out. Tokens appear only where they touch a TPM ceiling.
"""

from __future__ import annotations

import collections
import json
import pathlib
from dataclasses import dataclass

TRACE_DIR = pathlib.Path(".traces")


@dataclass(frozen=True)
class Usage:
    requests: int
    retries: int
    tokens_in: int
    tokens_out: int

    @property
    def billable_requests(self) -> int:
        """Retries count against your quota. This is the number that runs out."""
        return self.requests


def load_spans(day: str | None = None) -> list[dict]:
    files = sorted(TRACE_DIR.glob(f"{day or '*'}.jsonl"))
    return [json.loads(line) for f in files for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]


def by(key: str, spans: list[dict]) -> dict[str, Usage]:
    acc: dict[str, dict[str, int]] = collections.defaultdict(
        lambda: {"requests": 0, "retries": 0, "tokens_in": 0, "tokens_out": 0}
    )
    for s in spans:
        a = s["attributes"]
        if "llm.provider" not in a:
            continue
        bucket = acc[str(a.get(key, "unknown"))]
        bucket["requests"] += 1
        bucket["retries"] += 1 if a.get("llm.retry_of") else 0
        bucket["tokens_in"] += int(a.get("llm.tokens_in", 0))
        bucket["tokens_out"] += int(a.get("llm.tokens_out", 0))
    return {k: Usage(**v) for k, v in acc.items()}


def headroom(used: int, ceiling: int) -> str:
    pct = used / ceiling if ceiling else 0
    flag = "🟥" if pct > 0.8 else "🟨" if pct > 0.5 else "🟩"
    return f"{flag} {used}/{ceiling} ({pct:.0%})"
```

**Line by line:**

- `by(key, spans)` groups by **any attribute** — `llm.provider`, `llm.model`, or a span-name prefix.
  One function, three reports: cost by provider, by model, by phase of the pipeline. **The third is
  the one that surprises you**, and it is only possible because Day 75 named spans
  `mandala.<phase>.<what>`.
- `billable_requests` includes retries, and the docstring says why. **Excluding retries is the most
  common self-flattering error in agent cost reporting** — the provider counted them, so you must.
- `if "llm.provider" not in a: continue` — non-model spans are free and must not dilute the average.
- `headroom` returns a coloured string against **your real ceiling**, not an abstract number. "412
  requests" means nothing; "🟥 412/500 (82%)" is a decision.
- No dollars anywhere. Resist adding them "for realism" — a fake dollar figure is the number people
  will quote back at you.

### 3.2 The report

```python
# days/day-76/lab/cost_report.py
from mandala.obs.costs import by, headroom, load_spans

CEILINGS = {"groq": 14_400, "gemini": 1_500, "openrouter": 200}   # TODO(me): from RATE_BUDGET.md

spans = load_spans()
for dim in ("llm.provider", "llm.model", "phase"):
    print(f"\n== by {dim} ==")
    for name, u in sorted(by(dim, spans).items(), key=lambda kv: -kv[1].requests):
        print(f"{name:24} {u.requests:5} req  ({u.retries} retries)  {u.tokens_in + u.tokens_out:7} tok")

print("\n== headroom ==")
for provider, u in by("llm.provider", spans).items():
    print(f"{provider:12} {headroom(u.billable_requests, CEILINGS.get(provider, 0))}")
```

Run it. **Write the top three lines of output into your notes before you optimise anything.** You are
about to change things, and without a before-picture you will not know whether you helped.

---

## §4 Cut it: cache, tier, prune

### 4.1 LG-22 — the cache

```python
# src/mandala/router/cache.py
"""Content-addressed response cache. The only optimisation that helps every ceiling.

Keyed on (provider, model, system, user, temperature). Temperature is in the key on
purpose: a cached temperature-0 answer is legitimate; caching a temperature-0.9
answer silently removes the variation you asked for.
"""

from __future__ import annotations

import hashlib
import json
import pathlib

CACHE = pathlib.Path(".cache/llm")
ENABLED_DEFAULT = True


def key(provider: str, model: str, system: str, user: str, temperature: float) -> str:
    payload = json.dumps([provider, model, system, user, temperature], sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get(k: str) -> str | None:
    p = CACHE / k[:2] / k
    return p.read_text(encoding="utf-8") if p.exists() else None


def put(k: str, value: str) -> None:
    p = CACHE / k[:2] / k
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value, encoding="utf-8")


def cacheable(temperature: float, *, tool_result_in_prompt: bool) -> bool:
    """Not everything should be cached. Say why in code, not in a comment."""
    if temperature > 0.0:
        return False
    if tool_result_in_prompt:
        return False       # a search result from an hour ago is a different world
    return True
```

**Line by line:**

- `k[:2]` subdirectory sharding — 10,000 files in one directory is slow on every filesystem and
  unbrowsable on all of them.
- **`cacheable()` is the interesting function**, and it exists so the *policy* is testable. Two rules:
  temperature > 0 is never cached (you asked for variation; do not silently remove it), and prompts
  containing tool results are never cached (yesterday's search result is stale by definition).
- **The trap this avoids:** a cache that makes your eval suite pass because it is replaying answers
  from a previous version of the prompt. Include the full system prompt in the key — it is why
  `system` is a key component rather than a version string you would forget to bump.
- `.cache/` goes in `.gitignore` today, next to `.traces/`.
- **Measure the hit rate on your eval suite specifically.** Running the golden set twice should be
  ~100% hits on the second run; if it is not, your key includes something non-deterministic and
  finding out what is a genuinely useful half hour.

### 4.2 LG-22 — tiering per node

Not every step needs the same model. Your pipeline has:

| Step | Needs | Tier |
|---|---|---|
| routing / classification | a label from a closed set | **small** |
| extraction into a schema | structure, not eloquence | **small** |
| research synthesis | reasoning across sources | **large** |
| customer-facing draft | fluency | **large** |
| the judge (Day 72) | a *different provider*, always | fixed |

```python
# days/day-76/lab/tiering_experiment.py — the experiment, not the assumption
"""Run the golden set with routing on the small tier; compare against the D73 baseline."""
```

**The experiment is the point, not the table.** Move *one* step to the small tier, re-run
`run_experiment.py`, and use Day 73's `compare.py`. Three outcomes, all informative:

- Same pass rate, fewer large-tier requests → **keep it**, record the saving.
- Pass rate drops → you learned where the capability floor is. Record which examples broke.
- Pass rate rises → suspicious. Check whether the small model is failing in a way your rubrics
  reward (shorter outputs pass length checks). **This happens, and catching it is worth the day.**

### 4.3 Context pruning, and the budget assertion

```python
# src/mandala/router/budget.py
"""A per-run request budget. This is the RT-12 fix promised on Day 69."""

from __future__ import annotations

from dataclasses import dataclass, field


class BudgetExceeded(RuntimeError):
    """The run asked for more requests than it declared. Availability control, not economics."""


@dataclass
class RunBudget:
    limit: int
    spent: int = 0
    by_phase: dict[str, int] = field(default_factory=dict)

    def charge(self, phase: str, n: int = 1) -> None:
        self.spent += n
        self.by_phase[phase] = self.by_phase.get(phase, 0) + n
        if self.spent > self.limit:
            raise BudgetExceeded(
                f"{self.spent}/{self.limit} requests; by phase: {self.by_phase}"
            )
```

**Line by line:**

- **`by_phase` in the exception message.** A budget error that says "24/20" sends you hunting; one
  that says `{'triage': 2, 'research': 21, 'draft': 1}` tells you the research loop is not
  terminating. Failure messages are UX — third time this phase.
- `charge()` is called by the router, not by each caller. Same choke-point logic as Day 75's
  redaction and Day 70's dispatch fix. **This is now a pattern you have applied three times; name it
  out loud in the interview answer.**
- The budget is **per run**, not per day. A daily budget protects your quota; a per-run budget
  protects it *from one ticket*, which is the RT-12 threat.
- Context pruning belongs here too: cap conversation history at N turns before it becomes a token
  problem. Do the cheap version (keep first + last N) and note that Day 47's checkpointing gives you
  a better one.

---

## §5 LG-19 — what the paid layer adds (literacy, one paragraph)

Write this in `days/day-76/lab/managed_layer.md`, from the docs, in your own words:

> LangSmith's managed layer adds **Fleet** (deploying and managing agents as a hosted fleet),
> **Insights** (aggregated pattern discovery across runs rather than per-trace inspection), and
> **full-workflow cost tracking** across model, tool and infrastructure spend. What I built today
> covers per-provider and per-phase request accounting from my own spans; what I do not have is
> cross-run pattern mining, hosted alerting, or a shared team view. **The gap that would actually
> hurt at scale is [your answer].**

**That last sentence must be your own and specific.** The point of a 🅿️ literacy row is to be able to
say, in an interview, exactly what you gave up and what it would have bought — not to be vaguely
aware a paid product exists. Cite the docs page you read and the date.

---

## §6 The tests

```python
# tests/test_budget.py + tests/test_cache.py
import pytest

from mandala.router.budget import BudgetExceeded, RunBudget
from mandala.router.cache import cacheable, key

pytestmark = pytest.mark.eval_unit


def test_a_runaway_run_is_stopped():
    b = RunBudget(limit=3)
    for _ in range(3):
        b.charge("research")
    with pytest.raises(BudgetExceeded):
        b.charge("research")


def test_the_budget_error_names_the_guilty_phase():
    b = RunBudget(limit=1)
    b.charge("triage")
    with pytest.raises(BudgetExceeded, match="research"):
        b.charge("research")


def test_rt12_is_now_a_permanent_test():
    """Day 69's quota attack, as a standing regression test."""
    b = RunBudget(limit=12)
    with pytest.raises(BudgetExceeded):
        for _ in range(50):
            b.charge("loop")


def test_temperature_above_zero_is_never_cached():
    assert not cacheable(0.7, tool_result_in_prompt=False)


def test_prompts_containing_tool_results_are_never_cached():
    assert not cacheable(0.0, tool_result_in_prompt=True)


def test_the_system_prompt_is_part_of_the_cache_key():
    """Flip it: drop `system` from the key and your evals replay answers from an old prompt."""
    assert key("groq", "m", "SYS-A", "u", 0.0) != key("groq", "m", "SYS-B", "u", 0.0)


def test_retries_count_against_the_quota():
    from mandala.obs.costs import Usage

    u = Usage(requests=10, retries=4, tokens_in=0, tokens_out=0)
    assert u.billable_requests == 10        # not 6


def test_non_model_spans_do_not_dilute_the_report():
    from mandala.obs.costs import by

    spans = [{"attributes": {"llm.provider": "groq", "llm.tokens_in": 5, "llm.tokens_out": 5}},
             {"attributes": {"ticket_id": "T-1"}}]
    assert by("llm.provider", spans)["groq"].requests == 1
```

**Line by line:**

- `test_the_system_prompt_is_part_of_the_cache_key` is the day's headline flip-it. A cache keyed on
  the user message alone makes your Day-74 gate pass by replaying answers to a prompt you deleted.
  **That is a silent, total loss of eval integrity**, and it is a one-line bug.
- `test_rt12_is_now_a_permanent_test` closes the Day-69 loop explicitly. Cross-reference it in
  `docs/REDTEAM.md`.
- `test_retries_count_against_the_quota` defends the honest number against a future "optimisation".

---

## §7 Traps

- **Optimising tokens when your constraint is RPD.** Avoid calls, don't shorten them.
- **Excluding retries from the count.** The provider didn't.
- **Caching temperature > 0.** You silently removed the variation you asked for.
- **Caching prompts that contain tool results.** Stale search results, presented as fresh.
- **A cache key missing the system prompt.** Eval integrity gone, silently.
- **Tiering by assumption.** Run the comparison; sometimes the small model "wins" by gaming a rubric.
- **A daily budget only.** RT-12 is a single-run attack.
- **A budget error without the phase breakdown.** Sends you hunting.
- **Dollar figures on a $0 project.** Someone will quote them.
- **Optimising before the before-picture.** Print the report first, keep the numbers.
- **Guessed ceilings.** Fill in `RATE_BUDGET.md` for real.
- **Treating LG-19 as "there's a paid thing".** Name the specific gap.

---

## §8 Request budget

**Declared: ~45 model requests, Groq + Gemini — and the second run should be near zero.**

| What | Requests |
|---|---|
| `cost_report.py` (reads yesterday's traces) | **0** |
| All tests | **0** |
| `tiering_experiment.py` — one full golden-set run on the small tier | ≤ 20 |
| Re-run for the cache hit-rate measurement | ~0 (that is the experiment) |
| Provider-rotation drill (force a 429, watch the fallback) | ≤ 5 |
| Spot-checks | ≤ 20 |

**The near-zero second run is the deliverable.** Record the cache hit rate in `docs/RATE_BUDGET.md`
and note what it means for Day 74's re-record step and for Day 78's capstone: the marginal cost of
re-running your eval suite just dropped to roughly nothing, and that changes how often you will run
it.

---

## §9 Verify before you code

Written **2026-08-21**:

- **The real RPM / RPD / TPM for each free tier**, today. These change without notice. Fill every
  TBD in `docs/RATE_BUDGET.md` before optimising.
- **Does your Day-6 router already rotate on 429**, and does the span record *which* provider
  answered? If not, that is today's first fix — provider rotation is a resilience pattern (AG-26),
  not just a cost one.
- **Does any provider count retries differently** (e.g. a 429 that never reached the model)? Ask the
  docs, not your intuition.
- **LangGraph node-level caching** (LG-22) in `langgraph==1.2.11` — is there a built-in node cache,
  and does it key on state? If it exists, compare it against your own cache rather than duplicating.
- **Prompt caching** on any of your free providers — supported at all on free tiers?
- **LangSmith Fleet / Insights** — read the current docs page for §5 and cite it with today's date.
- `https://docs.langchain.com/oss/python/langgraph/caching` — read today.

---

## §10 Say it in an interview

> "On a zero-budget project the currency isn't dollars, it's requests per minute and per day, which
> changes which optimisations matter — shortening prompts helps a token ceiling but does nothing for
> a daily request cap, so avoiding calls entirely is the only thing that helps every ceiling at once.
> I built the cost report off my own OTel spans, grouped by provider, by model, and by pipeline
> phase, and the phase view was the one that surprised me. I counted retries as billable, because the
> provider does, and excluding them is the most common way these reports flatter you. Then three
> cuts: a content-addressed cache keyed on the full system prompt — leaving the system prompt out of
> the key is a one-line bug that makes your eval suite replay answers to a prompt you've deleted;
> model tiering per node, validated by re-running the golden set and diffing per example rather than
> assumed, because sometimes a small model 'wins' by gaming a rubric like a length check; and a
> per-run request budget whose error message names the phase that overspent. That budget is also a
> security control — my red team had an attack that engineered a ticket to make the agent loop and
> burn the quota, so a per-run cap is the availability fix, not just an economic one."

---

## §11 Done when

```bash
./m check
./m done 76
```
