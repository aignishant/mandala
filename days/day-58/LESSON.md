---
day: 58
phase: 8
phase_name: "MCP (2026-07-28 spec)"
title: "Deprecation drill, agent-over-MCP, and the freshness habit"
ids: ["MCP-11", "MCP-13", "MCP-16"]
kind: gate
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 58 — Deprecation drill, agent-over-MCP, and the Phase-8 gate

**Phase 8 · MCP 2026-07-28** · IDs: **MCP-11 🛠️**, **MCP-13 🛠️**, **MCP-16 🛠️** · **🎯 gate day**

> **Yesterday:** Tasks proved across two replicas, and three authorisation layers finally lined up.
> **Today:** three things and a gate. **MCP-11** — meet an old-style server, recognise it, wrap it.
> **MCP-13** — turn a Mandala *agent* into an MCP server, so the boundary works in both directions.
> **MCP-16** — run the freshness check against the spec and log a nil report *correctly*, because
> that habit is graded at every gate from here to Day 90.
> **Tomorrow:** the bake-off opens.

```bash
./m start 58
./m scaffold 58
```

---

## §1 The story

The plan's Phase-8 gate: *"one stateless `ticket-db` server consumed by all four frameworks;
deprecation-recognition lab passed; freshness drill logged."*

The first clause you did on Day 55. The other two are today, and they are both about **time**.

**MCP-11 is about the past.** Roots, Sampling and Logging are deprecated with a ≥12-month window. That
means servers using them exist *right now*, will keep existing for a year, and you will meet one. The
plan calls this a *"failure-and-migration lab"* and the required skill is not "know they are
deprecated" — it is **recognise an old-style server from its behaviour, and wrap it rather than
rewrite it.**

**MCP-16 is about the future.** Principle 13 says every Friday you check the pins and the spec page.
The plan says today's drill is *"habit installation, graded at every later gate"*. And the honest
version of that habit is the thing people get wrong: **a nil report is the normal outcome and writing
it down is the whole discipline.** "Nothing changed" that you did not record is indistinguishable from
"I did not check".

**MCP-13 is the one that will surprise you.** You have spent six days making data sources reachable by
agents. Today you point it the other way: **an agent, exposed as a tool.** The plan says do it from
at least two frameworks, and contrast it with A2A on Day 87 — agent-as-tool versus agent-as-peer.

---

## §2 Setup — run this

### 2.1 Nothing new

```bash
uv run pytest -q
git status --porcelain
```

- A gate day adds no dependencies.

### 2.2 Create today's files

```bash
touch src/mandala_mcp/legacy_shim.py
touch src/mandala_mcp/agent_server.py
touch tests/test_legacy_shim.py
touch tests/test_agent_server.py
mkdir -p days/day-58/lab
touch days/day-58/lab/old_style_server.py
touch days/day-58/lab/gate_demo.sh
touch days/day-58/lab/freshness_2026-08-__.md
touch docs/adr/ADR-00X-mcp-boundary.md
```

- `old_style_server.py` is a **deliberately outdated server you write yourself.** You cannot practise
  recognising legacy behaviour without something legacy to recognise, and writing it is the fastest
  way to understand what changed.

---

## §3 MCP-11 — the deprecation drill

### 3.1 What was deprecated, and what replaced it

| Deprecated | What it did | Replacement in 2026-07-28 |
|---|---|---|
| **Roots** | client tells the server which filesystem/URI roots it may use | scoped via the request, not a session-level declaration |
| **Sampling** | **the server asks the client to run a model call** | multi-round-trip: `InputRequiredResult` + opaque state |
| **Logging** | server pushes log records to the client over the session | ordinary transport/observability, outside the protocol |

**All three depend on a session**, and that is the pattern: **the stateless core (MCP-02) is what made
them untenable.** Roots and Logging assume the server remembers who you are between calls; Sampling
assumes an open channel back to the client mid-call.

**Sampling is the one worth understanding properly**, because its removal is the most consequential
and the replacement is the least obvious:

- **Old:** the server, mid-tool-call, asks *your* client to run an inference on its behalf. Convenient,
  and it means a server you connected to can spend your model quota and put its text into your model.
- **New:** the server returns an `InputRequiredResult` with **opaque state**, the client does whatever
  it needs, and calls back carrying that state. **The server holds nothing between the two calls** —
  the state travels with the request.

**Read that against Day 56's CIMD and Day 53's stateless core**, and you have the fourth instance of
one idea: *push state out of the server, make it travel with the request.* **Four instances in one
revision is a thesis**, and being able to name it is the MCP competence this phase is actually
teaching.

**And notice the security improvement**, because it is not incidental: old-style Sampling let a server
spend your quota and inject text into your model on its own initiative. The replacement makes every
round trip an explicit client decision. **Day 56 §4.2's elicitation analysis applies here in
retrospect** — and the deprecation is the spec agreeing with you.

### 3.2 `days/day-58/lab/old_style_server.py`

Write the thing you need to recognise.

```python
"""A deliberately OLD-STYLE server. You cannot practise recognition without a specimen.

This is what a 2025-era MCP server looks like, and one will still be in your registry
a year from now. Read the markers, then close this file and try to spot them from the
OUTSIDE in legacy_shim.py.

Run:
    uv run python days/day-58/lab/old_style_server.py

Budget: 0 requests -- it never actually calls a model; it only ASKS you to.
"""

from __future__ import annotations

#: MARKER 1 -- a session. Modern servers hold nothing between calls.
SESSIONS: dict[str, dict] = {}

#: MARKER 2 -- roots declared at session level, not per request.
ALLOWED_ROOTS: dict[str, list[str]] = {}


def initialize(client_id: str, roots: list[str]) -> dict:
    """MARKER 3 -- an initialize handshake. The 2026-07-28 core has none."""
    SESSIONS[client_id] = {"initialized": True}
    ALLOWED_ROOTS[client_id] = roots
    return {"capabilities": ["tools", "sampling", "logging"], "session": client_id}


def call_tool(client_id: str, name: str, args: dict) -> dict:
    if client_id not in SESSIONS:
        return {"error": "not initialized"}      # MARKER 4 -- state-dependent failure

    if name == "summarise_ticket":
        # MARKER 5 -- SAMPLING: the server asks YOUR client to run a model call.
        return {
            "type": "sampling/createMessage",
            "messages": [{"role": "user", "content": f"Summarise: {args['text'][:200]}"}],
            "maxTokens": 200,
        }

    # MARKER 6 -- LOGGING pushed over the session rather than to a transport.
    return {"result": "ok", "logs": [{"level": "info", "text": f"ran {name}"}]}
```

**Line by line — these six markers are the recognition checklist:**

- **`SESSIONS` at module level.** The single clearest tell. Day 54's AST test would fail this file
  instantly, and that is the point: **your own test suite already encodes the modern rule.**
- **`ALLOWED_ROOTS` keyed by client** — Roots as a session-level declaration.
- **`initialize()`** — if a server has one, it predates the stateless core. **This is the fastest
  external check**, and §3.3 uses it.
- **`{"error": "not initialized"}`** — a state-dependent failure. A stateless server cannot produce
  this error because there is no state to be missing. **Getting this error from a server is a
  positive identification**, and it is the one you will actually see in the wild, because you will
  call a legacy server the modern way and it will refuse.
- **The sampling response** is the one to sit with. The server did not answer; it **asked you to run
  a model call on its behalf**, with a prompt it wrote. Your client, your key, your quota, its text.
- **`logs` in the response body** — logging as protocol payload rather than as observability.

### 3.3 `src/mandala_mcp/legacy_shim.py`

The plan's MCP-11 row: *"connect to an old-style server, recognize it, wrap it."* **Wrap, not
rewrite** — you rarely control the server.

```python
"""Recognise an old-style MCP server, and wrap it so modern clients can use it.

You will not control the server. A year-long deprecation window means old servers
outlive your patience, so the skill is: detect, adapt, and refuse the dangerous parts.

Three behaviours, three policies:
  ROOTS    -> harmless. Send them per call and move on.
  LOGGING  -> harmless. Strip logs from the payload into our own logger.
  SAMPLING -> REFUSED by default. A server asking to spend my quota with a prompt it
              wrote is the pre-deprecation version of Day 56's phishing surface, and
              the replacement (InputRequiredResult + opaque state) exists precisely
              because this was wrong.

Usage
-----
    >>> classify({"error": "not initialized"})
    'legacy'
"""

from __future__ import annotations

import logging
from typing import Final, Literal

log = logging.getLogger("mandala.mcp.legacy")

Era = Literal["modern", "legacy", "unknown"]

#: Response shapes that positively identify a pre-2026-07-28 server.
LEGACY_MARKERS: Final[tuple[str, ...]] = (
    "not initialized",
    "sampling/createMessage",
    "session",
)

#: Never proxied, whatever the server asks for.
REFUSED_METHODS: Final[frozenset[str]] = frozenset({
    "sampling/createMessage",
    "sampling/create_message",
})


def classify(response: dict) -> Era:
    """Cheap, external detection. No handshake required -- that is the point."""
    blob = str(response).lower()
    if any(marker.lower() in blob for marker in LEGACY_MARKERS):
        return "legacy"
    if "jsonrpc" in blob or "content" in response:
        return "modern"
    return "unknown"


def adapt(response: dict) -> dict:
    """Turn a legacy response into something a modern client can consume."""
    if response.get("type") in REFUSED_METHODS:
        log.warning("refused a sampling request from a legacy server")
        return {
            "content": [{
                "type": "text",
                "text": ("This server asked to run a model call on my behalf "
                         "(deprecated sampling). Refused. Ask it for data instead."),
            }],
            "isError": True,
        }

    for record in response.pop("logs", []):
        log.info("legacy server log: %s", str(record.get("text", ""))[:200])

    if "result" in response:
        return {"content": [{"type": "text", "text": str(response["result"])[:2000]}]}
    return response
```

**Line by line:**

- `classify(response)` works on **a response you already have**, not on a handshake. That matters:
  with no `initialize` in the modern protocol, **you cannot ask a server what era it is — you infer it
  from how it answers.** The cheapest positive signal is the `"not initialized"` error you get for
  free by calling it the modern way.
- `LEGACY_MARKERS` as a tuple of substrings — crude, and honest about it. It will produce false
  positives on a modern server that happens to say "session" in a tool description. **A tell is not a
  proof**, and the shim should log its classification rather than silently branching on it.
- **`REFUSED_METHODS` is the security decision of the day.** Sampling is *refused*, not proxied, by
  default. The docstring gives the reason and it connects three lessons: it is Day 56's phishing
  surface, before the spec had a name for it.
- **The refusal returns model-readable text, not an exception.** Day 54's rule: model-facing errors
  are instructions. *"Ask it for data instead"* tells the model what to do next, and a model that
  reads it will often recover on its own.
- `isError: True` alongside the text — the model sees a failure *and* a recovery instruction.
- `response.pop("logs", [])` — logs are **removed from the payload** and routed to your logger.
  Leaving them in means server-written text flows into your model's context uninvited, which is the
  same class of problem as elicitation.
- Every extracted string is **bounded** (`[:200]`, `[:2000]`). Text from a server you do not control
  is untrusted input, and eleventh-appearance AG-04.
- **`adapt` never raises.** A legacy server is an inconvenience, not an exception. Raising would take
  down a graph node (Day 49) over someone else's release cadence.

---

## §4 MCP-13 — serving an agent over MCP

### 4.1 The inversion

Six days of "make data reachable by agents". Today: **make an agent reachable as a tool.**

```python
@mcp.tool()
def triage_ticket(ticket_id: str) -> str:
    """Classify a ticket. Runs Mandala's triage agent and returns severity/category/summary."""
```

From the caller's side that is an ordinary tool. Behind it is a whole LangGraph run.

**Why this matters, in one comparison the plan sets up for Day 87:**

| | Agent-as-tool (MCP-13, today) | Agent-as-peer (A2A, Day 87) |
|---|---|---|
| Who is in charge | **the caller** | neither — peers |
| Interface | a tool schema | an Agent Card |
| Conversation | one call, one result | a task lifecycle between equals |
| Trust | the caller trusts the tool | **mutual, signed** |
| Good for | capability reuse | cross-organisation work |

**Write this table today**, while MCP-13 is fresh, and finish it on Day 87. The plan's INT-03 row asks
for *"one paragraph you can say aloud in an interview without notes"*, and half of it is today's
experience.

### 4.2 `src/mandala_mcp/agent_server.py` — and the hard part

```python
"""Mandala's triage agent, exposed as an MCP tool.

The inversion: six days of making data reachable by agents; now an agent reachable
as a tool. From outside it is one tool call. Inside it is a LangGraph run.

THE PROBLEM, and it is not incidental:
    Every other tool in ticket-db is read-only, fast, and stateless. This one is
    none of those. It costs ~11 model requests, takes ~15 seconds, and runs a
    stateful graph. Putting it in the SAME server as get_ticket would give
    ticket-db a tool whose blast radius and cost profile are completely different
    from everything around it.

So it is a SEPARATE server ("mandala-triage") with its own process, its own scopes,
and its own rate limit. Mixing them would be the mistake.

Usage
-----
    uv run python -m mandala_mcp.agent_server
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mandala-triage")

#: This tool costs real model requests. That fact belongs in the schema.
COST_PER_CALL = 11
MAX_CONCURRENT = 2


@mcp.tool()
def triage_ticket(ticket_id: str) -> str:
    """Classify one ticket. EXPENSIVE: runs a multi-step agent (~11 model calls).

    Prefer get_ticket from ticket-db if you only need the ticket's text.

    Args:
        ticket_id: a Mandala ticket id, e.g. T-1004.
    """
    if not _valid_id(ticket_id):
        return f"invalid ticket id {ticket_id!r}; ids look like T-1004"
    if not _slot_available():
        return "triage is busy; retry shortly"

    from mandala.graph.core import build_core

    graph = build_core().compile()
    final = graph.invoke({"ticket_id": ticket_id, "stage": "new"})
    triage = final.get("triage")
    if triage is None:
        return "triage failed; escalate to a human"
    return f"{triage.severity} / {triage.category} / {triage.summary}"
```

**Line by line:**

- **A separate server, and the docstring argues for it at length.** This is the design decision of
  §4 and it is worth the words: a server is a **blast-radius and cost boundary**, not just a namespace.
  `ticket-db` is read-only, instant and free; `mandala-triage` is expensive, slow and stateful.
  **Different profiles, different servers** — and it means Day 56's scopes can grant `tickets:read`
  without granting the ability to spend eleven requests.
- **`"EXPENSIVE: runs a multi-step agent (~11 model calls)"` in the model-facing docstring.** The
  model choosing between tools should know one is two orders of magnitude more expensive. **Cost
  belongs in the schema** — that is a genuinely useful idea and it is not in the spec.
- *"Prefer get_ticket if you only need the ticket's text"* — steering the model toward the cheap tool
  in the description. Free, and it works.
- `_slot_available()` and `MAX_CONCURRENT = 2` — **a concurrency limit, because a tool that costs 11
  requests must not be callable 20 times in parallel.** This is Day 44's fan-out cap arriving at the
  server boundary. **Note the tension with statelessness:** a per-process counter is state. Either
  accept that this server is deliberately not horizontally scalable, or put the counter in the shared
  store from Day 57. **Decide, and write down which.**
- **The heavy import is inside the function.** `from mandala.graph.core import build_core` at module
  level would pull LangGraph, LangChain and torch into startup — and Day 54's
  `test_the_server_does_not_import_the_framework_code` exists for `ticket-db`. **This server is the
  exception, and the test must be scoped to exclude it deliberately** rather than quietly weakened.
- Failures return **guidance strings**, not exceptions. Day 54's rule, third server.
- `graph.invoke` with **no checkpointer** — a tool call is one-shot. If a caller wants durability they
  should use Tasks (Day 57). **Say that in the notes**; "why is this not a task?" is a good question
  and the answer is "it should be, once it exceeds a request timeout."

---

## §5 MCP-16 — the freshness drill, done properly

### 5.1 The drill

```bash
# 1. The spec revision
#    Open the specification's revisions page. Is 2026-07-28 still current?

# 2. The SDK
printf "%-10s " mcp
curl -s --max-time 30 "https://pypi.org/pypi/mcp/json" \
  | python -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"

# 3. The clients
for p in crewai-tools langchain-mcp-adapters openai-agents; do
  printf "%-26s " "$p"
  curl -s --max-time 30 "https://pypi.org/pypi/$p/json" \
    | python -c "import sys,json;print(json.load(sys.stdin)['info']['version'])" 2>/dev/null \
    || echo "(not installed / not found)"
done

# 4. Compare every number against docs/PINS.md.
```

### 5.2 `days/day-58/lab/freshness_2026-08-__.md` — and how to write a nil report

**This is the graded artifact.** Every later gate checks that you can do this.

```markdown
# Freshness check — 2026-08-__

Ran by: <you> · Scope: MCP spec + SDK + four clients · Method: spec revisions page, PyPI JSON API

## Results

| Item | Pinned | Live | Verdict |
|---|---|---|---|
| MCP specification | 2026-07-28 | | |
| `mcp` | 2.0.0 | | |
| `crewai-tools` | 1.15.17 | | |
| `langchain-mcp-adapters` | | | |
| `openai-agents` | 0.22.0 | | |

## Verdict
- [ ] **Checked, unchanged.** (A nil report. This is the normal outcome and it is a RESULT.)
- [ ] Patch drift: pinned the new patch, one line in CHANGELOG_PLAN.md.
- [ ] **Minor/major drift: STOPPED. Addendum written before any pin changed.** (Principle 14)

## What I looked at, so a future me can repeat it exactly
<the URLs, the command, and where the answer was on the page>

## Time taken
<minutes. If it was more than ten, the process needs fixing, not more discipline.>
```

**Why a nil report is the deliverable:**

- **"Nothing changed" that is not written down is indistinguishable from "I did not check."** A month
  from now, the only evidence you ran this is the file.
- The **"what I looked at" section** is what makes the habit survivable. A check you have to
  re-derive each Friday is a check you will skip by week six. Write the URL and where on the page the
  answer lives.
- **Time taken is a real metric.** Principle 13 asks for this weekly for the rest of your career. If
  it takes forty minutes, the process is broken and the fix is automation, not willpower — that is a
  legitimate finding and it belongs in the file.
- `docs/CHANGELOG_PLAN.md` gets **one line either way.** Its header says so: *"Nil reports from the
  Friday freshness check belong here too — 'checked, unchanged' is a real result and writing it down
  is the whole habit."*

---

## §6 The evidence table

| # | Claim | Proved by | ✓ |
|---|---|---|---|
| 1 | One stateless `ticket-db` consumed by **all four** frameworks | `mount_all_four.py` (Day 55) | ⬜ |
| 2 | Per-framework tool declarations were deleted | `test_the_declaration_count_went_down` | ⬜ |
| 3 | The server holds no module-level mutable state | `test_no_module_level_mutable_state` (AST) | ⬜ |
| 4 | Any replica answers any request | Day 57's two-store proof | ⬜ |
| 5 | Tokens are validated: issuer, audience, expiry, scope | `tests/test_mcp_auth.py` | ⬜ |
| 6 | A scope substring does not grant access | `test_a_scope_substring_does_not_grant_access` | ⬜ |
| 7 | Elicitation cannot ask for a secret | `test_the_schema_is_closed` | ⬜ |
| 8 | Long work returns a handle and can be cancelled | `task_lifecycle.py` | ⬜ |
| 9 | **A legacy server is recognised** | `test_classify_spots_a_legacy_server` | ⬜ |
| 10 | **A sampling request is refused, not proxied** | `test_sampling_is_refused` | ⬜ |
| 11 | An agent is reachable as an MCP tool | `agent_server.py` + a live call | ⬜ |
| 12 | The expensive tool is a **separate server** with its cost in the schema | `test_the_agent_tool_declares_its_cost` | ⬜ |
| 13 | **The freshness drill is logged, nil report included** | `days/day-58/lab/freshness_*.md` + changelog | ⬜ |
| 14 | Whole suite green, not just today's | `pytest -q` | ⬜ |
| 15 | Pins re-verified; drift logged or nil-reported | `docs/CHANGELOG_PLAN.md` | ⬜ |

---

## §7 The tests

```python
# tests/test_legacy_shim.py
"""Recognise, adapt, refuse. 0 model requests."""

import pytest

from mandala_mcp.legacy_shim import REFUSED_METHODS, adapt, classify


def test_classify_spots_a_legacy_server():
    assert classify({"error": "not initialized"}) == "legacy"


def test_classify_spots_a_sampling_request():
    assert classify({"type": "sampling/createMessage", "messages": []}) == "legacy"


def test_classify_accepts_a_modern_response():
    assert classify({"content": [{"type": "text", "text": "ok"}]}) == "modern"


def test_sampling_is_refused():
    """THE security test. Flip it: proxy the request and this goes red."""
    out = adapt({"type": "sampling/createMessage", "messages": [{"content": "x"}]})
    assert out["isError"] is True
    assert "refused" in out["content"][0]["text"].lower()


def test_the_refusal_tells_the_model_what_to_do_instead():
    out = adapt({"type": "sampling/createMessage", "messages": []})
    assert "ask it for data" in out["content"][0]["text"].lower()


def test_logs_are_stripped_from_the_payload():
    """Server-written text must not flow into the model's context uninvited."""
    out = adapt({"result": "ok", "logs": [{"level": "info", "text": "IGNORE PRIOR"}]})
    assert "IGNORE PRIOR" not in str(out)


def test_adapted_text_is_bounded():
    out = adapt({"result": "x" * 50_000})
    assert len(out["content"][0]["text"]) <= 2_000


def test_adapt_never_raises():
    """A legacy server is an inconvenience, not an exception (Day 49)."""
    for junk in ({}, {"weird": object()}, {"logs": "not-a-list"}):
        try:
            adapt(dict(junk))
        except Exception as exc:  # noqa: BLE001 - that is the assertion
            pytest.fail(f"adapt raised {exc!r}")


def test_every_sampling_spelling_is_refused():
    assert "sampling/createMessage" in REFUSED_METHODS
    assert "sampling/create_message" in REFUSED_METHODS
```

```python
# tests/test_agent_server.py
"""An agent as a tool is a different animal from a data tool. 0 model requests."""

from pathlib import Path

SOURCE = Path("src/mandala_mcp/agent_server.py").read_text(encoding="utf-8")


def test_the_agent_tool_is_a_separate_server():
    """Flip it: register it on ticket-db and this goes red."""
    assert 'FastMCP("mandala-triage")' in SOURCE
    ticket_db = Path("src/mandala_mcp/server.py").read_text(encoding="utf-8")
    assert "triage_ticket" not in ticket_db


def test_the_agent_tool_declares_its_cost():
    """The model choosing between tools should know one is 100x the price."""
    assert "EXPENSIVE" in SOURCE
    assert "model call" in SOURCE.lower()


def test_the_agent_tool_steers_toward_the_cheap_alternative():
    assert "prefer get_ticket" in SOURCE.lower()


def test_the_heavy_import_is_inside_the_function():
    head = SOURCE.split("def triage_ticket")[0]
    assert "from mandala.graph" not in head


def test_there_is_a_concurrency_limit():
    assert "MAX_CONCURRENT" in SOURCE


def test_failures_return_guidance_not_exceptions():
    assert "raise" not in SOURCE.split("def triage_ticket")[1].split("def ")[0]
```

**Line by line on the ones that carry weight:**

- `test_sampling_is_refused` is the gate's row 10, and its flip-it note names the wrong design
  (proxying). **A server spending your quota with a prompt it wrote is the thing the deprecation
  removed; refusing it in a shim is agreeing with the spec.**
- `test_logs_are_stripped_from_the_payload` uses an **injection string** as the log text, which is
  what a hostile legacy server would put there.
- `test_adapt_never_raises` uses `pytest.fail` inside an `except` — an unusual shape and the clearest
  way to assert "no exception, whatever the input".
- `test_the_agent_tool_is_a_separate_server` asserts **both** halves: the new server exists *and*
  `ticket-db` does not carry the expensive tool. One-sided assertions miss the drift.
- `test_the_heavy_import_is_inside_the_function` is the same top-of-file grep technique as Day 50's
  `test_nothing_expensive_happens_above_the_interrupt`. **Second use of the trick; it is a house
  pattern now.**

---

## §8 The ADR and the demo

**`docs/adr/ADR-00X-mcp-boundary.md`** — four questions:

1. **Was Principle 11 worth it?** You deleted three tool declarations and gained a process boundary.
   Count both sides: what did the boundary *cost* (Day 54 §4's lost `InjectedToolArg` and
   `permissions.py`, a second process to run, a discovery problem) and what did it buy?
2. **The four instances of one idea.** Stateless core, CIMD, cacheable listings, `InputRequiredResult`.
   Name the thesis in one sentence.
3. **The three authorisation layers** (Day 57 §4.2), and which one Mandala actually relies on today.
4. **Prediction for Day 87:** agent-as-tool versus agent-as-peer. Fill in §4.1's table now and finish
   it then.

**`days/day-58/lab/gate_demo.sh`** — read from it:

```bash
#!/usr/bin/env bash
set -euo pipefail
echo "== 1. one server ==================================================="
uv run python -m mandala_mcp.http_server &          # background, killed at the end
sleep 2
echo "== 2. four clients, same server ===================================="
uv run python days/day-55/lab/mount_all_four.py
echo "== 3. probe it as a stranger would ================================="
uv run python days/day-57/lab/capability_probe.py
echo "== 4. a task, seen by a second replica ============================="
uv run python days/day-57/lab/task_lifecycle.py
echo "== 5. a legacy server, recognised and refused ======================"
uv run python days/day-58/lab/legacy_drill.py
echo "== 6. the agent, as a tool ========================================="
uv run python -m mandala_mcp.agent_server &
sleep 2
uv run python days/day-58/lab/call_agent_tool.py T-9002
echo "== 7. everything green ============================================="
uv run pytest -q
kill %1 %2 2>/dev/null || true
```

- `&` and `kill %1 %2` — **background the servers and clean them up.** A demo that leaves processes
  holding port 8765 makes the next take fail confusingly.
- Step 3 probes your own server *as a stranger would*, which previews Day 66 and takes ten seconds.

---

## §9 Traps

- **Reading MCP-11 instead of doing it.** You cannot recognise legacy behaviour without a specimen.
- **Proxying a sampling request** because it is easier than refusing. Your key, your quota, its prompt.
- **Leaving `logs` in the payload.** Server text into your model's context, uninvited.
- **`adapt` raising.** It takes down a graph node over someone else's release cadence.
- **Putting the agent tool on `ticket-db`.** A read-only, free, instant server suddenly has an
  eleven-request tool.
- **Omitting the cost from the agent tool's description.** The model cannot choose well without it.
- **A per-process concurrency counter without deciding about statelessness.** Pick, and write it down.
- **A module-level heavy import in `agent_server.py`.** Startup pulls in torch.
- **Skipping the nil report** because nothing changed. That is exactly when it must be written.
- **A freshness process that takes forty minutes.** The fix is automation, not willpower — and saying
  so in the report is a legitimate finding.

---

## §10 Request budget

**Declared: ~13 model requests, Groq.**

| What | Requests |
|---|---|
| All tests, probes, drills, task lifecycle | **0** |
| `mount_all_four.py` (gate step 2) | 4 |
| One live call to the agent-as-tool server | ~11 |
| Contingency | 0 |

**Phase 8 total should land near 25 requests across six days** — against Phase 5's ~110 and Phase 7's
~100. **Put that number in the ADR.** It is the strongest free-tier result in the plan and the reason
is structural: **a protocol boundary is testable without a provider.** That belongs in the Day-63
scorecard as a row, not as a remark.

---

## §11 Done when

Phase 8 is complete when every row in §6 is green, the ADR exists, and the freshness report — nil or
not — is written and logged.

```bash
./m check
./m done 58
```

Then read Day 59's §1. **The bake-off starts tomorrow**: the same Mandala slice, built four times, one
framework per day, timeboxed. Every comparison table you have been filling since Day 30 is about to
be cashed in — go and collect them into one place tonight, because looking for them on Day 63 is how
a scorecard becomes an opinion.
