---
day: 75
phase: 11
phase_name: "Evals & observability"
title: "Tracing everything"
ids: ["AG-25", "LG-17"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-21"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 75 — Tracing everything

**Phase 11 · Evals & observability** · IDs: **AG-25 🛠️**, **LG-17 🛠️**

> **Yesterday:** a gate that runs on every PR for nothing. It tells you *that* something broke.
> **Today:** the other half — *why*. Spans, traces, token and cost accounting, and the decision
> Principle 8 has been pointing at since Day 1: **one neutral trace layer, four frameworks.**
> **Tomorrow:** the money. Today's cost attributes are what Day 76 spends.

```bash
./m start 75
./m scaffold 75
```

---

## §1 The story

You have four frameworks in this repo, and each has its own opinion about observability: the Agents
SDK has traces (Day 14), CrewAI has its own hooks (Day 28), LangGraph has LangSmith (LG-17), and
your naked Phase-1 loop has `print`. **Principle 8 says pick a neutral layer, and OpenTelemetry is
it** — not because it is pleasant, but because it is the only one that all four can emit into and the
only one that will still exist when one of the four is out of fashion.

Three ideas, and the third is the one worth the day:

1. **A span is a unit of work with a start, an end, and attributes.** A trace is a tree of them. That
   is the entire data model. Everything else is exporters and naming.
2. **Naming is the product.** `span.name = "llm"` tells you nothing at 2am. `llm.triage` with
   attributes `{provider, model, ticket_id, tokens_in, tokens_out, retry_of}` answers a question.
   You will get this wrong once and then have opinions for life.
3. **Trace data is customer data.** A ticket body inside a span attribute is a ticket body sitting in
   whatever backend you exported to. Day 73 kept `LANGSMITH_TRACING=false` for exactly this reason,
   and today you turn it on **deliberately, with a redaction step in front of it**, and write the
   decision down beside the permission table.

The shape you are building:

```
your code ──► OpenTelemetry SDK ──┬──► console exporter   (always, free, local)
                                  ├──► file exporter      (always — Day 76 reads these)
                                  └──► LangSmith          (opt-in, redacted, capped)
```

---

## §2 Setup — run this

```bash
uv add "opentelemetry-sdk==1.44.0" "opentelemetry-exporter-otlp==1.44.0"
```

```bash
touch src/mandala/obs/__init__.py
touch src/mandala/obs/tracing.py
touch src/mandala/obs/redact.py
touch src/mandala/obs/costs.py
mkdir -p days/day-75/lab
touch days/day-75/lab/trace_one_ticket.py
touch days/day-75/lab/read_traces.py
touch tests/test_tracing.py
```

Create the directory traces land in, and **gitignore it today, before the first run**:

```bash
mkdir -p .traces && echo ".traces/" >> .gitignore
```

**Line by line:**

- `.traces/` holds ticket text. It is the single most likely thing in this repo to be committed by
  accident, and the gitignore line costs you four seconds now versus a history rewrite later.
- `opentelemetry-exporter-otlp` is added today even though you will not run a collector — Day 85's
  deployment work uses it, and installing it now means the code path exists and is pinned.

---

## §3 AG-25 — spans, attributes, and one place to configure it

### 3.1 `src/mandala/obs/tracing.py`

```python
"""One tracer, configured once. Every framework emits into it.

Design rules:
  - names are dotted and stable: mandala.<phase>.<what>
  - attributes are flat scalars (OTel rejects nested structures)
  - anything customer-written goes through redact.py first
  - the console + file exporters are ALWAYS on; hosted export is opt-in
"""

from __future__ import annotations

import json
import os
import pathlib
import time
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SpanExporter

from mandala.obs.redact import redact

TRACE_DIR = pathlib.Path(".traces")
_TRACER = None


class JsonlFileExporter(SpanExporter):
    """One JSON object per span, appended. Day 76 reads this; Day 77 charts it."""

    def __init__(self, path: pathlib.Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def export(self, spans) -> None:  # noqa: ANN001
        with self._path.open("a", encoding="utf-8") as fh:
            for s in spans:
                fh.write(
                    json.dumps(
                        {
                            "name": s.name,
                            "trace_id": f"{s.context.trace_id:032x}",
                            "span_id": f"{s.context.span_id:016x}",
                            "parent": f"{s.parent.span_id:016x}" if s.parent else None,
                            "start_ns": s.start_time,
                            "duration_ms": (s.end_time - s.start_time) / 1e6,
                            "attributes": dict(s.attributes or {}),
                            "status": s.status.status_code.name,
                        }
                    )
                    + "\n"
                )

    def shutdown(self) -> None:
        return None


def tracer():
    global _TRACER
    if _TRACER is None:
        provider = TracerProvider()
        if os.getenv("MANDALA_TRACE_CONSOLE", "1") == "1":
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        provider.add_span_processor(
            BatchSpanProcessor(JsonlFileExporter(TRACE_DIR / f"{time.strftime('%Y-%m-%d')}.jsonl"))
        )
        trace.set_tracer_provider(provider)
        _TRACER = trace.get_tracer("mandala")
    return _TRACER


@contextmanager
def span(name: str, **attrs: object):
    with tracer().start_as_current_span(name) as s:
        for k, v in attrs.items():
            s.set_attribute(k, redact(v) if isinstance(v, str) else v)
        yield s


def record_model_call(s, *, provider: str, model: str, tokens_in: int, tokens_out: int, retry_of: str = "") -> None:
    s.set_attribute("llm.provider", provider)
    s.set_attribute("llm.model", model)
    s.set_attribute("llm.tokens_in", tokens_in)
    s.set_attribute("llm.tokens_out", tokens_out)
    if retry_of:
        s.set_attribute("llm.retry_of", retry_of)
```

**Line by line:**

- **One `tracer()`, memoised.** Configuring OTel in two places gives you two providers and half your
  spans vanish. It is a confusing bug and this is the whole prevention.
- `JsonlFileExporter` is ~20 lines and worth every one: **your trace data stays on your disk, in a
  format you can `grep`, forever, for free.** A hosted backend is a convenience on top of that, never
  the only copy. This is the same "direction of truth" rule as Day 73.
- `trace_id` formatted as hex — the integers are unreadable and every other tool shows hex. Matching
  the ecosystem's format saves you conversions later.
- `parent` recorded explicitly so Day 76 can reconstruct the tree without an OTel dependency.
- `duration_ms` computed at export — nanosecond timestamps are correct and unusable.
- **`redact(v)` on every string attribute, at the choke point.** Redaction that is applied at each
  call site is redaction that is forgotten at one of them. One place, no exceptions.
- `record_model_call` exists so token counts are named **identically everywhere**. `tokens_in` vs
  `input_tokens` vs `prompt_tokens` across four frameworks is how a cost dashboard silently
  undercounts by a third. Pick one; enforce it in a test.
- `llm.retry_of` is the attribute nobody adds. Without it, a 429 retry looks like a second, real
  call, and Day 76's cost picture is wrong in the direction that flatters you.

### 3.2 `src/mandala/obs/redact.py`

```python
"""Everything customer-written passes through here before it becomes an attribute."""

from __future__ import annotations

import re

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_PHONE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
MAX_ATTR_CHARS = 512


def redact(text: str) -> str:
    from mandala.redteam.canary import CANARY

    out = _EMAIL.sub("<email>", text)
    out = _PHONE.sub("<phone>", out)
    out = out.replace(CANARY, "<canary>")
    return out[:MAX_ATTR_CHARS] + ("…" if len(out) > MAX_ATTR_CHARS else "")
```

**Line by line:**

- **The canary replacement is the clever bit**: Day 69's exfiltration tripwire would otherwise be
  faithfully exported to a third-party service by your own observability layer. Redacting it means a
  canary appearing in a trace is *your bug*, not a leak.
- `MAX_ATTR_CHARS = 512` — truncation is a cost control and a privacy control at once. Full ticket
  bodies in every span is how a free trace tier evaporates in two days.
- This is **not anonymisation and you should say so in the docstring.** A regex catches emails and
  phone numbers; it does not catch "the customer is Priya from the Delhi office". Write the
  limitation down, the way you did for the canary's paraphrase blind spot on Day 69 and the
  irreversibility heuristic on Day 68. **Third time. It is a habit now.**

---

## §4 LG-17 — LangSmith, turned on deliberately

```python
# days/day-75/lab/trace_one_ticket.py (excerpt)
import os

from mandala.obs.tracing import record_model_call, span

os.environ.setdefault("LANGSMITH_TRACING", "false")   # explicit, every time

with span("mandala.triage", ticket_id="T-9001") as s:
    with span("mandala.triage.classify") as c:
        result = classify(body)                        # TODO(me)
        record_model_call(c, provider="groq", model=MODEL, tokens_in=..., tokens_out=...)
    with span("mandala.research.search", query=redacted_query):
        ...
```

To enable LangSmith for a single run — never in `.env`, never as a default:

```bash
LANGSMITH_TRACING=true uv run python days/day-75/lab/trace_one_ticket.py T-9001
```

**Line by line:**

- **Enabling per-command rather than per-environment** is the control. An env var in `.env` is on
  forever, including the day you run the red-team corpus and export twelve attack payloads to a
  third party.
- Span names are `mandala.<phase>.<what>` — dotted, stable, greppable. Add the naming convention to
  `CLAUDE.md` today so future days do not invent their own.
- LangGraph/LangChain will emit their own spans when tracing is on. **Note the duplication**: you now
  have your spans and theirs. Decide today whether that is useful (it is, briefly, for verifying your
  instrumentation matches reality) or noise (it is, permanently, afterwards).
- **Before enabling: open the permission table and the trifecta section.** Ask out loud whether the
  hosted backend now constitutes a place private data lives. Write the answer into
  `docs/PERMISSION_TABLE.md`'s prose section or a short ADR. That two-minute question is the actual
  content of LG-17; the SDK call is trivial.

---

## §5 The tests

```python
# tests/test_tracing.py
import json
import pathlib

import pytest

from mandala.obs.redact import MAX_ATTR_CHARS, redact
from mandala.obs.tracing import span, tracer

pytestmark = pytest.mark.eval_unit


def test_emails_and_phones_are_redacted():
    out = redact("contact priya@example.test or +91 98765 43210")
    assert "@example.test" not in out and "98765" not in out


def test_the_canary_never_reaches_a_span():
    """Flip it: remove the canary rule and your OWN tracing exfiltrates the tripwire."""
    from mandala.redteam.canary import CANARY

    assert CANARY not in redact(f"note {CANARY} here")


def test_attributes_are_truncated():
    assert len(redact("x" * 5000)) <= MAX_ATTR_CHARS + 1


def test_redaction_is_not_claimed_to_be_anonymisation():
    assert "not anonymisation" in redact.__doc__.lower() or redact.__module__


def test_one_tracer_only():
    assert tracer() is tracer()


def test_spans_land_in_the_jsonl_file(tmp_path, monkeypatch):
    monkeypatch.setattr("mandala.obs.tracing.TRACE_DIR", tmp_path)
    monkeypatch.setattr("mandala.obs.tracing._TRACER", None)
    with span("mandala.test.unit", ticket_id="T-1"):
        pass
    rows = [json.loads(l) for f in tmp_path.glob("*.jsonl") for l in f.read_text().splitlines()]
    assert any(r["name"] == "mandala.test.unit" for r in rows)


def test_token_attribute_names_are_canonical():
    """Four frameworks, one vocabulary. Flip it: allow 'prompt_tokens' and the cost dashboard
    undercounts by whatever fraction that framework contributes."""
    import inspect

    from mandala.obs.tracing import record_model_call

    params = inspect.signature(record_model_call).parameters
    assert {"tokens_in", "tokens_out", "provider", "model"} <= set(params)


def test_traces_are_gitignored():
    assert ".traces/" in pathlib.Path(".gitignore").read_text(encoding="utf-8")


def test_langsmith_tracing_is_not_enabled_in_the_repo():
    for f in (".env.example", ".github/workflows/evals.yml"):
        assert "LANGSMITH_TRACING=true" not in pathlib.Path(f).read_text(encoding="utf-8")
```

**Line by line:**

- `test_the_canary_never_reaches_a_span` is the day's headline and the flip-it is genuinely alarming:
  without that rule, your observability layer becomes an exfiltration channel operated by you.
- `test_traces_are_gitignored` runs before you have any traces, which is exactly when it is useful.
- `test_langsmith_tracing_is_not_enabled_in_the_repo` scans **config files, not code**. The failure
  it prevents is a helpful commit six weeks from now that "fixes" tracing by flipping the default.
- `test_token_attribute_names_are_canonical` is a small test defending a large number. Day 76's whole
  cost picture is built on these four attribute names agreeing across four frameworks.

---

## §6 Traps

- **Two tracer providers.** Half your spans disappear and nothing errors.
- **Redacting at call sites.** One will be missed; it will be the one with the ticket body.
- **Full bodies in attributes.** Free tier gone in two days, plus a privacy problem.
- **Unstable span names.** `llm_call_2` is a name you will regret at 2am.
- **Different token attribute names per framework.** Silent undercounting.
- **Not marking retries.** 429 retries inflate your call count and flatter your cost model.
- **`LANGSMITH_TRACING=true` in `.env`.** On forever, including red-team day.
- **Committing `.traces/`.** Add the gitignore line before the first run.
- **Treating the hosted backend as the only copy.** Keep the JSONL.
- **Skipping the "is this a new home for private data?" question.** That question *is* LG-17.
- **Instrumenting everything at once.** Start with the triage path; add spans when a question needs
  one.

---

## §7 Request budget

**Declared: ~10 model requests, Groq.**

| What | Requests |
|---|---|
| `tests/test_tracing.py` | **0** |
| `trace_one_ticket.py` (one ticket, fully instrumented) | ≤ 6 |
| Same ticket with `LANGSMITH_TRACING=true`, to compare | ≤ 4 |
| `read_traces.py` | **0** |

**Add a second budget row today: LangSmith traces consumed.** One instrumented ticket can emit a
dozen spans; at that rate a free monthly cap is a few hundred tickets, not a few thousand. Measure
it on this one run and extrapolate honestly in `docs/RATE_BUDGET.md` — Day 76 needs the number and
Day 85 needs it more.

---

## §8 Verify before you code

Written **2026-08-21** against `opentelemetry-sdk==1.44.0`:

- **`SpanExporter.export()` return type** — it expects a `SpanExportResult`, not `None`. Confirm and
  fix the sketch above; returning the wrong thing fails silently in a batch processor.
- **`BatchSpanProcessor` flush on exit** — confirm whether you need `provider.force_flush()` before
  process end, or you will lose the last spans of every run and think your exporter is broken.
- **Attribute value types**: OTel rejects nested dicts/lists of mixed type. Confirm what happens to
  a `None` attribute.
- **`s.attributes` on a `ReadableSpan`** — mapping or list of tuples in 1.44?
- **Does LangChain 1.3.16 emit OTel spans natively**, or only LangSmith's own format? If natively,
  you may be able to drop a layer; if not, note the duplication.
- **LangSmith free-tier trace cap** and whether spans or traces are counted.
- `https://opentelemetry.io/docs/languages/python/instrumentation/` — read today.

---

## §9 Say it in an interview

> "I picked OpenTelemetry as a neutral layer because I had four frameworks emitting four kinds of
> telemetry, and I wanted one vocabulary that would outlive whichever framework I stop using. The
> part that took thought wasn't the SDK, it was three decisions. First, naming: dotted stable span
> names and a single `record_model_call` helper, because when four frameworks each call it
> `prompt_tokens`, `input_tokens` and `tokens_in`, your cost dashboard silently undercounts — and I
> tag retries explicitly, or a 429 retry looks like a real second call and flatters the numbers.
> Second, redaction at a single choke point rather than at call sites, because one call site always
> gets missed and it's the one with the ticket body — and it strips the canary token I use for
> exfiltration detection, since otherwise my own observability layer becomes the exfiltration
> channel. Third, direction of truth: spans always go to a local JSONL file I own, and the hosted
> backend is an opt-in extra enabled per-command, never in `.env`. Turning on hosted tracing means
> customer text now lives somewhere new, so I treated it as a permission-table change and wrote the
> decision down rather than flipping an env var."

---

## §10 Done when

```bash
./m check
./m done 75
```
