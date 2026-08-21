# Day 85 — CHECKLIST

**IDs covered:** OAI-26 🛠️ (deploying an Agents SDK service — FastAPI, stateless, key management),
MCP-14 🛠️ (stateless MCP at scale, three replicas behind a local LB)

## Demo command

```bash
uv run pytest tests/test_service.py tests/test_stateless.py -v      # 0 requests
uv run uvicorn mandala.service.api:app --port 8000 &
curl -s -XPOST localhost:8000/tickets -H "x-api-key: $MANDALA_API_KEY" \
  -H "content-type: application/json" -d '{"id":"T-9101","body":"printer offline again"}'
docker compose -f deploy/docker-compose.yml up -d
uv run python days/day-85/lab/any_replica_test.py
docker compose -f deploy/docker-compose.yml stop mcp2 && uv run python days/day-85/lab/any_replica_test.py
```

Expected: 202 with a run id; **1 distinct answer, 3 replicas hit**; after stopping mcp2, still
1 distinct answer across 2 replicas.

## Setup

- [ ] `./m start 85` and `./m scaffold 85` run
- [ ] `fastapi==0.141.1` and `uvicorn==0.52.4` verified live, then pinned
- [ ] **`uv.lock` diff checked** — `pydantic` pin did not move (if it did: amendment, not a shrug)

## The statefulness hunt — do this BEFORE writing code

- [ ] All three greps run; output saved to `days/day-85/lab/statefulness_hunt.md`
- [ ] Every hit classified: **fine / must move / must be external**
- [ ] `tracer()` classified and reasoning written (per-process singleton — fine, and why)
- [ ] `.state/mandala.sqlite` classified — **must be external**, deferred to Day 86 deliberately
- [ ] `outbox/`, `.traces/`, `.cache/` each classified
- [ ] No hit left unclassified

## OAI-26 — the service

- [ ] **No module-level mutable state; no `global`; no lazy singletons holding request data**
- [ ] `POST /tickets` returns **202**, not 200 — and can say why that's a safety decision
- [ ] Key check uses `hmac.compare_digest`
- [ ] Unset `MANDALA_API_KEY` **fails closed**
- [ ] Errors reveal neither the expected nor the submitted key
- [ ] Body limit **imported from intake**, not re-declared
- [ ] `x-request-id` honoured if sent, generated if not, attached to the span
- [ ] `/healthz` needs no key and leaks no config
- [ ] `replica` field noted as demo-only in the docstring
- [ ] **No write/approve endpoint exposed** — and can say why that would be a redesign

## MCP-14 — three replicas

- [ ] Three identical services via YAML anchors (no copy-paste drift)
- [ ] nginx **round-robin**, no `ip_hash`, no `hash`
- [ ] `X-Request-Id` propagated through the proxy
- [ ] Shared volume mounted **`:ro`** — matches `ticket-db`'s permission row
- [ ] `proxy_next_upstream` present, with a **comment warning** it must never front a write
- [ ] `x-replica` header set from `HOSTNAME` (demo-only; noted)

## The proof

- [ ] 30 requests through the LB
- [ ] **1 distinct answer** asserted (canonicalised with `sort_keys`)
- [ ] **3 replicas hit** asserted — and can say why omitting this makes the test silently useless
- [ ] Re-run with one replica stopped; still one distinct answer
- [ ] Both runs recorded in the day's notes

## Tests that must be able to fail

- [ ] `test_the_service_has_no_module_level_mutable_state` — **flip it:** add `_CACHE = {}`
- [ ] `test_the_service_uses_no_globals`
- [ ] `test_an_unset_api_key_fails_closed`
- [ ] `test_a_wrong_key_reveals_nothing`
- [ ] `test_key_comparison_is_constant_time`
- [ ] `test_accepting_work_returns_202_not_200` — **flip it:** run the agent synchronously
- [ ] `test_the_body_limit_matches_intake`
- [ ] `test_healthz_needs_no_key_and_leaks_no_config`
- [ ] `test_no_write_endpoint_exists_yet`
- [ ] `test_the_load_balancer_does_not_use_sticky_routing`
- [ ] `test_the_shared_volume_is_read_only`
- [ ] All cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why is local three-replica proof stronger evidence than a cloud deploy?
- [ ] Name the five places state hides, with an example of each from your own repo
- [ ] Why does a synchronous agent endpoint become a double-send?
- [ ] Why must the replica-count assertion exist alongside the identical-answer assertion?
- [ ] Why is `proxy_next_upstream` safe here and dangerous in front of a write?
- [ ] Which component is allowed to be stateful, and where does it live? (tomorrow's answer)

## Budget & freshness

- [ ] Request count logged in `docs/RATE_BUDGET.md` (declared: ~6)
- [ ] Noted: the MCP-14 proof cost **0** — a stranger can verify it with Docker and no keys
- [ ] `Header(default=...)` semantics confirmed on this FastAPI version
- [ ] `model_fields` metadata shape confirmed (or the test written as a constant comparison)
- [ ] **`mcp==2.0.0` HTTP transport confirmed genuinely session-free for `tools/call`**
- [ ] nginx `proxy_next_upstream` defaults confirmed
- [ ] Docker bind-mount + `:ro` confirmed on the Windows machine
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 85
```

- [ ] `statefulness_hunt.md` committed — it is a Phase-13 gate artifact
- [ ] `deploy/` committed; no secrets in compose or nginx config
- [ ] `./m done 85` succeeded
