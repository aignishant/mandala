# Day 75 — CHECKLIST

**IDs covered:** AG-25 🛠️ (observability & tracing concepts, OTel as the neutral layer), LG-17 🛠️
(LangSmith tracing & debugging)

## Demo command

```bash
uv run pytest tests/test_tracing.py -v                          # 0 requests
uv run python days/day-75/lab/trace_one_ticket.py T-9001        # ≤ 6 requests
uv run python days/day-75/lab/read_traces.py                    # 0 — prints the span tree
LANGSMITH_TRACING=true uv run python days/day-75/lab/trace_one_ticket.py T-9002
```

Expected: a nested span tree printed from `.traces/*.jsonl`; every model span carrying provider,
model, tokens in/out; no email, phone or canary anywhere in the file.

## Setup

- [ ] `./m start 75` and `./m scaffold 75` run
- [ ] `opentelemetry-sdk==1.44.0` + `opentelemetry-exporter-otlp==1.44.0` verified live, then pinned
- [ ] `.traces/` created **and gitignored before the first run**
- [ ] `src/mandala/obs/` created
- [ ] Span-naming convention (`mandala.<phase>.<what>`) added to `CLAUDE.md`

## AG-25 — spans and attributes

- [ ] One memoised `tracer()` — and can say what two providers would do
- [ ] Console exporter on by default; **JSONL file exporter always on**
- [ ] `trace_id` / `span_id` written as hex; `parent` recorded explicitly
- [ ] `duration_ms` computed at export, not left as nanoseconds
- [ ] `record_model_call` used everywhere — **one vocabulary across four frameworks**
- [ ] `llm.retry_of` set on retries — and can say why its absence flatters the cost model
- [ ] Instrumented the triage path only; resisted instrumenting everything at once

## AG-25 — redaction

- [ ] `redact()` applied at the **single choke point** in `span()`, never at call sites
- [ ] Emails and phone numbers stripped
- [ ] **Canary replaced** — and can explain why that specific rule exists
- [ ] `MAX_ATTR_CHARS` truncation in place (a cost control *and* a privacy control)
- [ ] Docstring states plainly that this is **not anonymisation**, with an example of what it misses

## LG-17 — LangSmith, deliberately

- [ ] `LANGSMITH_TRACING` enabled **per-command**, never in `.env` or CI
- [ ] Ran one ticket with it on; compared the hosted view against the local JSONL
- [ ] Duplication between your spans and LangChain's spans noticed; decision recorded
- [ ] **Permission table reopened and the question asked out loud:** is the hosted backend now a
      place private data lives?
- [ ] Answer written into `docs/PERMISSION_TABLE.md`'s prose section or a short ADR
- [ ] Confirmed the red-team corpus is **never** run with hosted tracing on

## Tests that must be able to fail

- [ ] `test_emails_and_phones_are_redacted`
- [ ] `test_the_canary_never_reaches_a_span` — **flip it:** remove the rule, watch your own tracing
      exfiltrate the tripwire
- [ ] `test_attributes_are_truncated`
- [ ] `test_one_tracer_only`
- [ ] `test_spans_land_in_the_jsonl_file`
- [ ] `test_token_attribute_names_are_canonical`
- [ ] `test_traces_are_gitignored`
- [ ] `test_langsmith_tracing_is_not_enabled_in_the_repo` — scans config, not code
- [ ] All cost **0 model requests**

## Understanding check — answer out loud

- [ ] What is a span, in one sentence, and what is a trace?
- [ ] Why is naming the product rather than an afterthought?
- [ ] What breaks if one framework reports `prompt_tokens` and another `tokens_in`?
- [ ] Why redact at a choke point rather than at each call site?
- [ ] Why does the canary rule exist, and what would happen without it?
- [ ] What changed about your data-flow picture when you enabled hosted tracing?
- [ ] Why keep the local JSONL when the hosted UI is nicer?

## Budget & freshness

- [ ] Model request count logged in `docs/RATE_BUDGET.md` (declared: ~10)
- [ ] **Spans-per-ticket measured** and extrapolated against the LangSmith free cap — written down
- [ ] `SpanExporter.export()` return type confirmed (`SpanExportResult`, not `None`)
- [ ] `force_flush()` need confirmed — otherwise the last spans of every run vanish
- [ ] Attribute type restrictions confirmed (nested structures, `None`)
- [ ] `ReadableSpan.attributes` shape confirmed on 1.44
- [ ] Checked whether LangChain 1.3.16 emits OTel natively
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 75
```

- [ ] `git status` clean of `.traces/` — verified, not assumed
- [ ] Data-flow decision committed alongside the code
- [ ] `./m done 75` succeeded
