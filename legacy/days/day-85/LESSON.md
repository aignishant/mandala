---
day: 85
phase: 13
phase_name: "Deployment & interop"
title: "Shipping the services — FastAPI + stateless MCP at scale"
ids: ["OAI-26", "MCP-14"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-21"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 85 — Shipping the services: FastAPI + stateless MCP at scale

**Phase 13 · Deployment & interop** · IDs: **OAI-26 🛠️**, **MCP-14 🛠️**

> **Yesterday:** the Phase-12 gate, cold-read this morning. Mandala works end to end and is allowed
> to do nothing on its own.
> **Today:** it stops being a script. A FastAPI service in front, `ticket-db` replicated three times
> behind a local load balancer, and the property that makes both possible: **no request may depend on
> which process handles it.** All local, all free — the plan's Phase-13 rule.
> **Tomorrow:** the stateful half — LangGraph Server, and where state is allowed to live.

```bash
./m start 85
./m scaffold 85
```

---

## §1 The story

Phase 13's constraint is stated plainly in the plan: **local-first and free**. Docker Compose, MCP
replicated ×3 behind a local nginx, managed clouds as 🅿️ literacy only. That is not a compromise you
should apologise for — it is the version that actually proves the property. "It runs on Cloud Run"
proves someone else's platform works; "any of my three replicas answers any request identically"
proves *your code* has no hidden state.

The whole day reduces to one sentence:

> **Statelessness is not a feature you add. It is the absence of something you must go and look for.**

Where it hides, in roughly descending order of how often it bites:

| Hiding place | Looks like | Bites when |
|---|---|---|
| module-level mutable | `_CACHE = {}`, `_TRACER`, a client pool | replica 2 answers differently from replica 1 |
| lazily-built singletons | `if _x is None: _x = build()` | first request after a restart is slow or wrong |
| local filesystem | `.state/`, `outbox/`, `.traces/` | replica 3 cannot see replica 1's approval |
| in-process memory saver | `MemorySaver()` | the resume lands on a different worker |
| sticky assumptions | "the same client always hits the same box" | the LB round-robins |

**Your `tracer()` from Day 75 is a module-level singleton.** That one is fine (each process gets its
own, spans carry `run_id`, exporters append). **Your `.state/mandala.sqlite` is not fine**, and today
is where you find out. Do not fix it by pinning a replica; fix it by naming which component is
allowed to be stateful (tomorrow's answer: the worker, not the API).

Two IDs, two different jobs:

- **OAI-26** — a FastAPI wrapper around the agent path: stateless service, key management, rate
  limits. The service accepts a ticket and returns a run id. **It does not wait for the agent.**
- **MCP-14** — the addendum's Cloud Run story, relived on your infra: three `ticket-db` instances,
  one nginx, prove any instance answers any request.

---

## §2 Setup — run this

```bash
uv add "fastapi==0.141.1" "uvicorn==0.52.4"
```

Verify both are live on PyPI before adding (Principle 4), and note that `fastapi` pulls `starlette`
and `pydantic` — the latter is already pinned at 2.13.4, so **check `uv` did not move it**.

```bash
mkdir -p src/mandala/service deploy
touch src/mandala/service/__init__.py
touch src/mandala/service/api.py
touch src/mandala/service/deps.py
touch deploy/docker-compose.yml
touch deploy/nginx.conf
touch deploy/Dockerfile.mcp
mkdir -p days/day-85/lab
touch days/day-85/lab/any_replica_test.py
touch days/day-85/lab/statefulness_hunt.md
touch tests/test_service.py
touch tests/test_stateless.py
```

**Before writing code, do the hunt.** Fill in `days/day-85/lab/statefulness_hunt.md`:

```bash
grep -rn "^_[A-Z_]* *= *\(\[\]\|{}\|None\)" src/mandala/ | tee -a days/day-85/lab/statefulness_hunt.md
grep -rn "MemorySaver\|global " src/mandala/
grep -rn "Path(\"\.\|pathlib.Path('\." src/mandala/
```

For every hit, write one line: **fine (per-process, idempotent) / must move / must be external.**
That document is the day's most valuable artifact and it takes fifteen minutes.

---

## §3 OAI-26 — the service

```python
# src/mandala/service/api.py
"""A stateless HTTP front door. Accepts work, returns a run id, never blocks on an agent.

Design rules:
  - no module-level mutable state
  - the response never depends on which process handled it
  - long work is accepted, not awaited
  - no secret ever appears in a response or an error
"""

from __future__ import annotations

import os
import uuid

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from mandala.intake.channel import accept_payload
from mandala.obs.tracing import span

app = FastAPI(title="Mandala", version=os.getenv("MANDALA_VERSION", "dev"))


class TicketIn(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    body: str = Field(min_length=1, max_length=8_000)


class Accepted(BaseModel):
    run_id: str
    duplicate: bool
    replica: str


def require_key(x_api_key: str = Header(default="")) -> None:
    expected = os.environ.get("MANDALA_API_KEY", "")
    if not expected or not _constant_eq(x_api_key, expected):
        raise HTTPException(status_code=401, detail="unauthorized")


def _constant_eq(a: str, b: str) -> bool:
    import hmac

    return hmac.compare_digest(a.encode(), b.encode())


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "replica": os.getenv("HOSTNAME", "local"), "version": app.version}


@app.post("/tickets", response_model=Accepted, status_code=202, dependencies=[Depends(require_key)])
def post_ticket(ticket: TicketIn, request: Request) -> Accepted:
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    with span("mandala.service.post_ticket", request_id=request_id, ticket_id=ticket.id):
        result = accept_payload({"id": ticket.id, "body": ticket.body}, channel="http")
    if result is None:
        return Accepted(run_id="", duplicate=True, replica=os.getenv("HOSTNAME", "local"))
    return Accepted(run_id=result[0].run_id, duplicate=False, replica=os.getenv("HOSTNAME", "local"))
```

**Line by line:**

- **`status_code=202`, not 200.** You accepted work; you did not do it. A synchronous endpoint that
  runs an agent gives you a 90-second HTTP request, a gateway timeout, and a client that retries —
  which, with a write tool in the system, is how you get a double-send. **202 is a safety decision,
  not a REST-pedantry one.**
- `require_key` uses `hmac.compare_digest`, not `==`. String comparison short-circuits and leaks
  timing. Cheap, correct, and the kind of thing an interviewer notices.
- `if not expected` — **an unset `MANDALA_API_KEY` fails closed.** The version that fails open
  ("no key configured, so allow everything") is how a dev default reaches a demo.
- `detail="unauthorized"` and nothing else. No "wrong key", no echo of what was sent. §6 tests that
  no secret ever appears in a response body.
- `replica` in the response is **for today's proof only** — it is how `any_replica_test.py` shows the
  LB is actually distributing. Note in the docstring that a production service would not advertise
  its hostname.
- `Field(max_length=8_000)` mirrors Day 78's `MAX_BODY_CHARS`. **Two limits in two places is one
  limit that will drift** — import the constant instead, and add a test that they agree.
- `x-request-id` honoured if the client sent one, generated if not. That id is what ties an nginx
  access-log line to a span to a run, and without it a three-replica debugging session is guesswork.
- **No `global`, no module-level dict, no lazily-built client.** Read the file again and confirm.

---

## §4 MCP-14 — three replicas, one answer

```nginx
# deploy/nginx.conf
events {}
http {
  upstream ticketdb {
    server mcp1:8080;
    server mcp2:8080;
    server mcp3:8080;
  }
  log_format withid '$remote_addr "$request" $status upstream=$upstream_addr rid=$http_x_request_id';
  server {
    listen 8080;
    access_log /var/log/nginx/access.log withid;
    location / {
      proxy_pass http://ticketdb;
      proxy_set_header X-Request-Id $http_x_request_id;
      proxy_next_upstream error timeout http_502;
    }
  }
}
```

```yaml
# deploy/docker-compose.yml (excerpt)
services:
  mcp1: &mcp
    build: {context: .., dockerfile: deploy/Dockerfile.mcp}
    environment: [MANDALA_DB=/data/tickets.sqlite]
    volumes: ["../.state/shared:/data:ro"]
  mcp2: *mcp
  mcp3: *mcp
  lb:
    image: nginx:1.29-alpine
    ports: ["8080:8080"]
    volumes: ["./nginx.conf:/etc/nginx/nginx.conf:ro"]
    depends_on: [mcp1, mcp2, mcp3]
```

**Line by line:**

- **No `upstream ... ip_hash;`.** Sticky routing would make the demo pass while proving nothing. The
  default round-robin is the point.
- `proxy_set_header X-Request-Id` — the id survives the hop, so nginx's log line and your span share
  a key. **This is the single most useful line in the file** the first time a replica misbehaves.
- The shared volume is mounted **`:ro`**. `ticket-db` is a read tool (check its row in
  `permissions.py`); mounting read-only makes that structural instead of aspirational, and it means
  three replicas cannot race each other on writes because none of them can write.
- `proxy_next_upstream` — a 502 from one replica retries on another. **Safe here only because the
  tool is read-only.** If you ever put a write endpoint behind this, that line becomes a double-send
  machine. Write that warning as a comment in the file.
- YAML anchors (`&mcp` / `*mcp`) keep the three replicas genuinely identical. Copy-pasted service
  blocks drift, and a drifted replica makes the whole demo meaningless.

### 4.1 The proof

```python
# days/day-85/lab/any_replica_test.py
"""Fire the same MCP request N times through the LB. Every answer identical, every replica used."""

from __future__ import annotations

import collections
import json
import uuid

import httpx

REQ = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
       "params": {"name": "get_ticket", "arguments": {"ticket_id": "T-9001"}}}

if __name__ == "__main__":
    answers, replicas = collections.Counter(), collections.Counter()
    with httpx.Client(base_url="http://127.0.0.1:8080", timeout=10) as c:
        for _ in range(30):
            r = c.post("/mcp", json=REQ, headers={"x-request-id": uuid.uuid4().hex[:12]})
            answers[json.dumps(r.json().get("result"), sort_keys=True)] += 1
            replicas[r.headers.get("x-replica", "?")] += 1
    print(f"distinct answers: {len(answers)}  (must be 1)")
    print(f"replicas hit: {dict(replicas)}  (must be 3)")
    assert len(answers) == 1 and len(replicas) == 3
```

**Line by line:**

- **Two assertions, and both matter.** One distinct answer proves statelessness; three replicas hit
  proves you actually tested it. A test that passes because nginx sent all 30 requests to `mcp1` is
  the failure mode here, and it is silent without the second assertion.
- `json.dumps(..., sort_keys=True)` — canonicalise before comparing, or key ordering makes identical
  answers look distinct. Same discipline as Day 70's fingerprint.
- `x-replica` must be a header your MCP server sets from `HOSTNAME`. Add it today; remove it (or
  gate it behind a debug flag) before anything real.
- Run it **twice**: once normally, once with `docker compose stop mcp2` mid-run. The second run
  should still produce one distinct answer, with two replicas. **That is the actual value of the
  stateless story**, and it is worth ten seconds to demonstrate.

---

## §5 The eval that must be able to fail

```python
# tests/test_stateless.py + tests/test_service.py
import ast
import pathlib

import pytest
from fastapi.testclient import TestClient

from mandala.service.api import app

pytestmark = pytest.mark.eval_unit
SERVICE = pathlib.Path("src/mandala/service")


def test_the_service_has_no_module_level_mutable_state():
    """Flip it: add `_CACHE = {}` at module scope and watch replicas disagree."""
    for path in SERVICE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, (ast.Dict, ast.List, ast.Set)):
                pytest.fail(f"module-level mutable in {path}: line {node.lineno}")


def test_the_service_uses_no_globals():
    for path in SERVICE.rglob("*.py"):
        assert "global " not in path.read_text(encoding="utf-8")


def test_an_unset_api_key_fails_closed(monkeypatch):
    monkeypatch.delenv("MANDALA_API_KEY", raising=False)
    r = TestClient(app).post("/tickets", json={"id": "T-1", "body": "hello there"})
    assert r.status_code == 401


def test_a_wrong_key_reveals_nothing(monkeypatch):
    monkeypatch.setenv("MANDALA_API_KEY", "s3cret-value")
    r = TestClient(app).post("/tickets", json={"id": "T-1", "body": "x" * 30},
                             headers={"x-api-key": "wrong"})
    assert r.status_code == 401 and "s3cret" not in r.text and "wrong" not in r.text


def test_key_comparison_is_constant_time():
    import inspect

    from mandala.service import api

    assert "compare_digest" in inspect.getsource(api)


def test_accepting_work_returns_202_not_200(monkeypatch):
    """Flip it: run the agent synchronously and a client timeout becomes a double-send."""
    monkeypatch.setenv("MANDALA_API_KEY", "k")
    r = TestClient(app).post("/tickets", json={"id": "T-1", "body": "printer offline in the office"},
                             headers={"x-api-key": "k"})
    assert r.status_code == 202


def test_the_body_limit_matches_intake():
    from mandala.intake.normalise import MAX_BODY_CHARS
    from mandala.service.api import TicketIn

    assert TicketIn.model_fields["body"].metadata[-1].max_length == MAX_BODY_CHARS


def test_healthz_needs_no_key_and_leaks_no_config():
    r = TestClient(app).get("/healthz")
    assert r.status_code == 200 and "MANDALA_API_KEY" not in r.text and "key" not in r.text.lower()


def test_no_write_endpoint_exists_yet():
    """The service accepts tickets. It does not expose post_reply. Flip it and re-run Day 82."""
    paths = {r.path for r in app.routes if hasattr(r, "path")}
    assert not any("reply" in p or "approve" in p for p in paths)


def test_the_load_balancer_does_not_use_sticky_routing():
    conf = pathlib.Path("deploy/nginx.conf").read_text(encoding="utf-8")
    assert "ip_hash" not in conf and "hash " not in conf


def test_the_shared_volume_is_read_only():
    compose = pathlib.Path("deploy/docker-compose.yml").read_text(encoding="utf-8")
    assert ":/data:ro" in compose
```

**Line by line:**

- `test_the_service_has_no_module_level_mutable_state` **parses the AST** rather than grepping. It is
  the day's headline test and it catches the exact class of bug that makes a replica misbehave once
  every few hundred requests — the worst kind to debug.
- `test_a_wrong_key_reveals_nothing` asserts the *absence* of two strings. Absence-testing is the
  right shape for leakage, and you have used it before (Day 74's no-keys-in-CI step).
- `test_no_write_endpoint_exists_yet` freezes a scope decision. Exposing `post_reply` over HTTP means
  the approval gate now has an unauthenticated-ish network path in front of it, and that is a
  redesign, not an endpoint.
- `test_the_load_balancer_does_not_use_sticky_routing` tests infrastructure config from pytest — same
  move as Day 74's workflow tests, and for the same reason: config is code nothing else checks.

---

## §6 Traps

- **Synchronous agent endpoints.** Gateway timeout → client retry → double-send.
- **Module-level `{}` or `[]`.** Replicas disagree intermittently.
- **Lazily-built singletons holding request data.**
- **`ip_hash` to make the demo pass.** It proves nothing.
- **Not asserting all three replicas were hit.** Silent false pass.
- **Unset API key failing open.**
- **`==` on secrets.** Timing leak.
- **Echoing the submitted key in an error.**
- **Two body limits in two files.** Import the constant.
- **A writable shared volume across replicas.** Races, and it contradicts the tool's own permission row.
- **`proxy_next_upstream` in front of a write.** Double-send by configuration.
- **Advertising `HOSTNAME` in production responses.** Fine today; gate it.
- **Putting `.state/` on a container-local filesystem** and calling it deployed.

---

## §7 Request budget

**Declared: ~6 model requests. Deployment is almost entirely free.**

| What | Requests |
|---|---|
| All tests, compose, nginx, the replica proof | **0** |
| One ticket submitted through the API and run to the gate | ≤ 6 |

**Note the shape of Phase 13:** you are moving code, not calling models. Record the zero, and note
that the three-replica proof — the headline artifact of MCP-14 — cost nothing at all. That is worth a
line in the Day-89 README: *the distributed-systems claim in this repo is verifiable by a stranger
with Docker and no API keys.*

---

## §8 Verify before you code

Written **2026-08-21** against `fastapi==0.141.1`, `uvicorn==0.52.4`, `mcp==2.0.0`:

- **Did `uv add fastapi` move your `pydantic` pin?** Check `uv.lock` diff. If it did, that is a
  Principle-14 moment, not a shrug.
- **`Header(default="")` vs `Header(None)`** semantics in this FastAPI version, and whether a missing
  header 422s before your dependency runs.
- **Reading a field's `max_length` from `model_fields`** — the metadata shape changed in Pydantic 2.x;
  confirm before writing that test, or write it as a plain constant comparison instead.
- **Does `mcp==2.0.0`'s HTTP transport genuinely require no server-side session** for `tools/call`?
  That is the stateless-core claim MCP-14 rests on — verify it rather than assuming.
- **nginx `proxy_next_upstream` defaults** — confirm what it retries out of the box, since the default
  may already include cases you do not want.
- **Docker on your Windows machine**: confirm the bind-mount path syntax works from `deploy/` and that
  `:ro` is honoured.
- `https://fastapi.tiangolo.com/tutorial/dependencies/` — read today.

---

## §9 Say it in an interview

> "Deploying it locally was more useful than deploying it to a cloud, because 'any of my three
> replicas answers any request identically' proves my code has no hidden state, whereas 'it runs on
> Cloud Run' proves someone else's platform works. The work was mostly *finding* state rather than
> removing it — I did an explicit hunt for module-level mutables, lazily-built singletons, local
> filesystem writes and in-process checkpointers, and classified each as fine, must-move, or
> must-be-external. There's an AST-based test that fails if anyone adds a module-level dict to the
> service package, because that's the bug that makes one replica disagree once every few hundred
> requests. On the API, the decision I'd defend hardest is returning 202 rather than running the agent
> synchronously: a long request times out at the gateway, the client retries, and with a write tool in
> the system a retry is a double-send — so 202 is a safety decision, not REST pedantry. Key checks are
> constant-time and fail closed when unconfigured, and errors reveal nothing about what was sent. For
> the MCP side I ran three replicas behind nginx with plain round-robin — no sticky routing, because
> that would make the demo pass while proving nothing — and the proof asserts both that all answers
> were identical *and* that all three replicas were actually hit, since a test where the balancer sent
> everything to one box would otherwise pass silently."

---

## §10 Done when

```bash
./m check
./m done 85
```
