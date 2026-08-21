---
day: 55
phase: 8
phase_name: "MCP (2026-07-28 spec)"
title: "One server, four clients"
ids: ["MCP-05", "OAI-15"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 55 — One server, four clients

**Phase 8 · MCP 2026-07-28** · IDs: **MCP-05 🛠️ 🔁**, **OAI-15 🛠️**

> **Yesterday:** `ticket-db` — three primitives, stateless, read-only, tested without a model.
> **Today:** the payoff. **The same server, mounted into all four frameworks, in one day.** This is
> the lab Principle 11 exists for, and it is the day the plan's thesis stops being a claim. Then the
> transport question: stdio got you here; streamable HTTP is what Day 85 replicates.
> **Tomorrow:** auth and Elicitation.

```bash
./m start 55
./m scaffold 55
```

---

## §1 The story

Day 53 made you count: **four declarations of one function**, and they had drifted. Today you delete
three of them.

That is the concrete version of MCP-01's arithmetic, and it is why the plan calls today *"the payoff
lab for Principle 11."* But the interesting part is not the deletion — it is what you find while
mounting the same server four times:

**Every framework has an opinion about MCP**, and the differences are the most direct
framework-comparison data you will ever collect, because **the thing being mounted is byte-identical
in all four cases.** Every other comparison in this plan has had a confound: different code, different
prompts, different tool declarations. Today the only variable is the framework.

**So today is a bake-off day disguised as an integration day.** Fill in the comparison table as you
go (§4), because on Day 63 you will want it and reconstructing it later is impossible.

OAI-15 is the Agents SDK's mount, and it has a wrinkle the others do not: **approvals for MCP tool
calls.** The SDK is the only one of the four that treats "a tool from a server I do not control" as a
distinct trust category. That is a genuine design insight and it belongs in Day 66's notes.

---

## §2 Setup — run this

### 2.1 The transport question, first

```bash
grep -n 'httpx' pyproject.toml || echo "not installed"
```

- Yesterday's server ran over **stdio**: the client spawns the server as a subprocess. That is right
  for local development and **wrong for four frameworks at once**, because each one would spawn its
  own copy.
- Today you want **one server process, four clients.** That means **streamable HTTP**, which is the
  plan's MCP-04 row (*"Python SDK, Streamable HTTP, stateless; stdio for local dev"*) and the reason
  `httpx==0.28.1` is on the ledger for Day 53.
- Verify and install if you have not:

```bash
printf "%-10s " httpx
curl -s --max-time 30 "https://pypi.org/pypi/httpx/json" \
  | python -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
uv add "httpx==0.28.1"
```

**Check whether the `mcp` SDK already depends on `httpx`** before adding it — if it does, you are
pinning a transitive dependency you now use directly, which is the same situation as Day 42's
`langgraph` and deserves the same one-line changelog entry rather than silence.

### 2.2 Create today's files

```bash
touch src/mandala_mcp/http_server.py
touch src/mandala/mcp_mount.py
touch tests/test_mcp_mount.py
mkdir -p days/day-55/lab
touch days/day-55/lab/mount_all_four.py
touch days/day-55/lab/mcp_bakeoff.md
```

- **`src/mandala/mcp_mount.py` is the one new file in `mandala/`**, and it is the seam: one place that
  knows where the server lives and how to reach it. Four framework adapters import it. **If each
  framework file hard-codes the URL, you have rebuilt the N×M problem one layer up.**

---

## §3 MCP-05 — mounting the same server four times

### 3.1 `src/mandala_mcp/http_server.py`

```python
"""ticket-db over streamable HTTP. Same tools, same code, one process, many clients.

stdio (Day 54) spawns one server per client. Four frameworks would mean four copies
of the same fixtures, four startups, and no way to prove the stateless story. HTTP
means ONE process that any number of clients reach -- which is also the shape Day 85
replicates three times behind nginx.

Nothing about the tools changes. That is the point: transport is configuration.

Run:
    uv run python -m mandala_mcp.http_server
"""

from __future__ import annotations

import os

from mandala_mcp.server import mcp

HOST = os.environ.get("MANDALA_MCP_HOST", "127.0.0.1")
PORT = int(os.environ.get("MANDALA_MCP_PORT", "8765"))

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host=HOST, port=PORT)
```

**Line by line:**

- **`from mandala_mcp.server import mcp` — the server object is imported unchanged.** Zero tool code
  is duplicated or modified for a new transport. That is worth pausing on: **transport is
  configuration, not architecture**, and a protocol that got that right is a protocol you can deploy
  in more than one way.
- `HOST` defaults to **`127.0.0.1`, not `0.0.0.0`.** Day 54 established the server has **no auth**
  (§4 of that lesson). Binding to localhost is the only thing keeping it off the network, and that is
  a deliberate, temporary answer until Day 56. **Binding `0.0.0.0` today would expose an unauthenticated
  ticket database to your LAN.**
- Environment variables with defaults — configuration in the environment, per Day 1's `.env`
  discipline, and it is what Day 85's docker-compose will set.
- `transport="streamable-http"` — **confirm the exact string in `mcp==2.0.0`** (§8). It has been
  `"sse"` and `"streamable-http"` across revisions, and SSE is the legacy transport the 2026-07-28
  spec deprecated.

### 3.2 `src/mandala/mcp_mount.py` — the seam

```python
"""Where ticket-db lives, and how each framework reaches it. ONE place.

Four frameworks mount the same server today. If each one hard-codes the URL and the
tool names, the N x M problem has been rebuilt one layer up -- which would be a
funny way to fail Principle 11 on the day it pays off.

So: this module owns the endpoint, the timeout and the allowed tool set. The four
adapters below own only their framework's syntax.

Usage
-----
    >>> from mandala.mcp_mount import ENDPOINT, ALLOWED_TOOLS
    >>> sorted(ALLOWED_TOOLS)
    ['get_ticket', 'search_handbook', 'search_tickets']
"""

from __future__ import annotations

import os
from typing import Final

SERVER_NAME: Final = "ticket-db"
ENDPOINT: Final = os.environ.get("MANDALA_MCP_URL", "http://127.0.0.1:8765/mcp")

#: An allowlist, not everything the server offers. Principle 6, restated at the mount.
ALLOWED_TOOLS: Final[frozenset[str]] = frozenset({
    "get_ticket",
    "search_tickets",
    "search_handbook",
})

#: A hung tool server must not hang the agent. Day 49's policy, at the boundary.
MOUNT_TIMEOUT_S: Final = 20
```

**Line by line:**

- `ENDPOINT` from the environment with a local default — one string, four consumers.
- **`ALLOWED_TOOLS` is the important line, and it is not redundant.** The server exposes three tools
  today; it will expose more later, and a third-party server (Day 66) exposes whatever it likes.
  **Mounting means "give my agent these tools", and the client should say which ones.** This is the
  partial answer to Day 54 §4's lost `permissions.py`: you cannot enforce per-agent permissions on the
  server, but you can enforce them at the mount. **Not the same guarantee — a determined caller can
  still reach the server directly — and worth stating plainly rather than overselling.**
- `MOUNT_TIMEOUT_S` — Day 49's node policy, applied one layer down. A tool server that stops
  responding must not turn into a hung graph node.
- `Final` throughout, and no functions: **this module is configuration.** The four adapters are
  separate because each is framework-specific and each should be deletable.

### 3.3 The four mounts

Write each adapter in its framework's own module, importing from `mcp_mount`. The shapes differ and
**the differences are the data you came for.**

```python
# --- Agents SDK (OAI-15) ---------------------------------------------------
# src/mandala/sdk.py
from agents.mcp import MCPServerStreamableHttp

async def mcp_server():
    return MCPServerStreamableHttp(
        params={"url": ENDPOINT, "timeout": MOUNT_TIMEOUT_S},
        cache_tools_list=True,          # the 2026-07-28 cacheable-list property, used
    )

# agent = Agent(name="triage", model=..., mcp_servers=[server],
#               mcp_config={"require_approval": {"never": {"tool_names": ["get_ticket"]}}})


# --- CrewAI ---------------------------------------------------------------
# src/mandala/crew/tools.py
from crewai_tools import MCPServerAdapter

# with MCPServerAdapter({"url": ENDPOINT}) as tools:
#     analyst = Agent(..., tools=[t for t in tools if t.name in ALLOWED_TOOLS])


# --- LangChain / LangGraph ------------------------------------------------
# src/mandala/lc/tools.py
from langchain_mcp_adapters.client import MultiServerMCPClient

# client = MultiServerMCPClient({SERVER_NAME: {"url": ENDPOINT, "transport": "streamable_http"}})
# tools = [t for t in await client.get_tools() if t.name in ALLOWED_TOOLS]
```

**Line by line, and what to notice:**

- **The Agents SDK is the only one with a first-class approval concept for MCP tools.** `require_approval`
  distinguishes tools you trust from tools you do not, per server. **That is the OAI-15 insight** and
  it exists because the SDK's authors treated a remote server as a different trust category from a
  local function. The other three treat MCP tools as ordinary tools. **Write that down — it is a real
  design difference and Day 66 will care.**
- `cache_tools_list=True` — **this is the 2026-07-28 cacheable-list property being used by a client.**
  Yesterday it was a spec bullet; today it is a keyword argument that saves a round trip per run.
  Check whether the other three offer it; if they do not, that is a row in the table.
- **CrewAI's adapter is a context manager**, which tells you it holds a connection. That is a
  lifecycle question the others do not obviously raise: who opens it, when does it close, and what
  happens if the agent runs longer than the block? **Find out and note it.**
- **LangChain's is `MultiServerMCPClient` — plural.** The abstraction assumes several servers from the
  start, which is a different bet from the SDK's per-agent list. And note the transport string differs
  (`"streamable_http"` with an underscore, versus the server's `"streamable-http"` with a hyphen) —
  **if that is real, it is exactly the kind of detail that costs an hour**, so verify both.
- **Each adapter filters by `ALLOWED_TOOLS`.** Three filters, one allowlist. Do not skip the filter in
  the framework that makes it awkward.
- **New packages may be needed** — `langchain-mcp-adapters` is not in `docs/PINS.md`, and
  `crewai-tools` may already carry `MCPServerAdapter`. **Verify what is actually required, pin
  exactly, and add ledger rows** (Principle 4). If `langchain-mcp-adapters` is needed, that is a
  genuine gap in the plan's ledger and it deserves a `CHANGELOG_PLAN.md` line, not a quiet `uv add`.

### 3.4 `days/day-55/lab/mount_all_four.py`

```python
"""The same question, four frameworks, one server. The Principle-11 payoff.

Prerequisite -- in another terminal:
    uv run python -m mandala_mcp.http_server

Run:
    uv run python days/day-55/lab/mount_all_four.py

Budget: 4 requests (one per framework) + list_tools calls, which cost nothing.
"""

QUESTION = "What is ticket T-1004 about? Use the tools."

# For each framework: mount, list the tools it sees, ask ONE question, print the answer.
# Record for each: lines of mount code, tool names as the framework reports them,
# whether the schema survived intact, and whether approvals are available.

# TODO(me): implement the four mounts. Keep each one to <10 lines by importing
# from mandala.mcp_mount. If one takes 30 lines, that IS the finding -- write it down.
```

**Line by line:**

- **The server runs in another terminal.** One process, four clients — that is the demonstration, and
  spawning four stdio subprocesses would quietly undo it.
- **The same question in all four** so the only variable is the framework.
- The `TODO` names the acceptance criterion (**under ten lines each**) *and* tells you what to do if a
  framework fails it: **record it rather than fighting it.** A framework that needs thirty lines to
  mount a server has told you something, and that is a scorecard row.
- `list_tools` costs nothing — **do it in all four and compare what each reports.** Do the names
  survive? The descriptions? The schemas? **A framework that mangles your tool descriptions is
  mangling your prompt**, and you would never notice without looking.

---

## §4 The comparison — today's real deliverable

### `days/day-55/lab/mcp_bakeoff.md`

```markdown
# One server, four clients — Mandala, 2026-08-__

The only variable is the framework. Same server, same tools, same question.

| | Agents SDK | CrewAI | LangChain | LangGraph |
|---|---|---|---|---|
| Mount package | | | | |
| Lines to mount | | | | |
| Sync or async | | | | |
| Connection lifecycle | | context manager | | |
| Tool names survive intact | | | | |
| Descriptions survive intact | | | | |
| Schemas survive intact | | | | |
| Per-tool **approval** support | **yes** | | | |
| Caches `tools/list` | **yes** | | | |
| Multi-server by design | no | | **yes** | |
| Can I filter which tools to take | | | | |
| Error when the server is down | | | | |

## Declarations deleted today
<Day 53 counted 3 per-framework tool files. How many survived? Update
 tests/test_tool_parity.py's recorded count and note the milestone.>

## The one that surprised me

## Which framework treats a remote tool as a different trust category?
<and why that matters -- Day 66>

## What still lives on my side
<per-agent permissions, correlation ids, blast radius -- what did the mount give back,
 and what is still gone since Day 54 §4?>
```

**The "declarations deleted" line is the milestone.** Day 53's `test_the_count_of_declarations_is_recorded`
was written to go red today with a message telling you to celebrate. **Update the number and log the
before/after in `docs/CHANGELOG_PLAN.md`** — it is the most quantifiable win in the plan.

**And answer the last question honestly.** The mount's `ALLOWED_TOOLS` filter gave you *some* of Day
12's `permissions.py` back — per-agent tool selection — but not enforcement, because the server still
answers anyone who reaches it. **The gap closes on Day 56 (auth) and Day 57 (EMA), and until then it
is a gap, not a solved problem.**

---

## §5 The eval that must be able to fail

### `tests/test_mcp_mount.py`

```python
"""The mount is a boundary. 0 model requests -- the server is faked or run in-process."""

from pathlib import Path

import pytest

from mandala.mcp_mount import ALLOWED_TOOLS, ENDPOINT, MOUNT_TIMEOUT_S, SERVER_NAME


def test_the_endpoint_is_defined_in_one_place():
    """Flip it: hard-code the URL in a framework adapter and this goes red."""
    offenders = []
    for path in Path("src/mandala").rglob("*.py"):
        if path.name == "mcp_mount.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "8765" in text or "/mcp" in text.replace("mcp_mount", ""):
            offenders.append(path.name)
    assert offenders == [], offenders


def test_the_allowlist_is_a_subset_of_what_the_server_offers():
    """A mount that asks for a tool the server does not have fails at runtime, silently late."""
    from mandala_mcp import server as srv

    offered = {"get_ticket", "search_tickets", "search_handbook"}
    assert ALLOWED_TOOLS <= offered, ALLOWED_TOOLS - offered
    for name in ALLOWED_TOOLS:
        assert hasattr(srv, name), name


def test_the_allowlist_excludes_nothing_dangerous_by_accident():
    """Every offered tool is either allowed or deliberately excluded -- no silent drift."""
    from mandala_mcp import server as srv

    offered = {n for n in dir(srv) if hasattr(getattr(srv, n), "fn")}
    unexplained = offered - ALLOWED_TOOLS
    assert unexplained == set(), (
        f"{unexplained} is offered but not mounted -- allow it or document the exclusion"
    )


def test_the_mount_has_a_timeout():
    """Day 49: a hung tool server must not become a hung graph node."""
    assert 0 < MOUNT_TIMEOUT_S <= 60


def test_the_server_name_matches_the_server():
    source = Path("src/mandala_mcp/server.py").read_text(encoding="utf-8")
    assert SERVER_NAME in source


def test_the_endpoint_is_localhost_by_default():
    """Day 54 §4: no auth yet. Flip it: default to 0.0.0.0 and this goes red."""
    assert "127.0.0.1" in ENDPOINT or "localhost" in ENDPOINT


def test_the_http_server_does_not_bind_all_interfaces_by_default():
    source = Path("src/mandala_mcp/http_server.py").read_text(encoding="utf-8")
    assert '"0.0.0.0"' not in source


def test_every_framework_filters_by_the_allowlist():
    """Three adapters, one allowlist. Flip it: drop the filter in one and this goes red."""
    adapters = [
        "src/mandala/sdk.py",
        "src/mandala/crew/tools.py",
        "src/mandala/lc/tools.py",
    ]
    for path in adapters:
        text = Path(path).read_text(encoding="utf-8")
        assert "ALLOWED_TOOLS" in text, path


def test_the_declaration_count_went_down():
    """Day 53's milestone test, from the other side. Update the number and celebrate."""
    remaining = [
        p for p in (
            Path("src/mandala/sdk_tools.py"),
            Path("src/mandala/crew/tools.py"),
            Path("src/mandala/lc/tools.py"),
        )
        if p.exists() and "lookup_ticket" in p.read_text(encoding="utf-8")
    ]
    assert len(remaining) <= 1, (
        f"{[p.name for p in remaining]} still declare the ticket tool locally; "
        "MCP-05 was supposed to collapse these"
    )
```

**Line by line:**

- `test_the_endpoint_is_defined_in_one_place` is the **N×M-rebuilt-one-layer-up** guard, and it is the
  most important test today. Four adapters hard-coding a URL would be a funny way to fail Principle 11
  on the day it pays off.
- `test_the_allowlist_is_a_subset_of_what_the_server_offers` catches a typo in `ALLOWED_TOOLS` that
  would otherwise surface as a tool silently missing at runtime.
- `test_the_allowlist_excludes_nothing_dangerous_by_accident` is the **inverse** and the subtler one:
  it asserts every tool the server offers is *deliberately* handled. Add a tool to the server and this
  goes red until you allow it or write down why not. **Allowlists rot silently in the direction of
  omission; this test is the antidote.**
- `test_the_endpoint_is_localhost_by_default` and its `http_server.py` sibling pin the §3.1 security
  reasoning. **They are meant to be deleted on Day 56, when auth exists** — and deleting a test
  deliberately, because a guarantee moved somewhere better, is a good habit to practise.
- `test_every_framework_filters_by_the_allowlist` is a grep across three adapters. It is the kind of
  thing that is true on the day you write it and false three commits later.
- `test_the_declaration_count_went_down` is the milestone from the other side, with the celebration in
  the failure message. **`<= 1` rather than `== 0`** because one framework may legitimately keep a
  local tool for something the server does not expose — but three is the old world.

---

## §6 Traps

- **Four stdio subprocesses instead of one HTTP server.** You have four copies and no stateless proof.
- **Binding `0.0.0.0` before Day 56.** An unauthenticated ticket database on your LAN.
- **Hard-coding the URL in each adapter.** N×M, rebuilt one layer up.
- **Skipping the `ALLOWED_TOOLS` filter** in whichever framework makes it awkward.
- **Overselling the filter.** It is client-side tool selection, not server-side enforcement. The
  server still answers anyone who reaches it.
- **`uv add`-ing an MCP adapter package without a ledger row.** `langchain-mcp-adapters` is not in
  `docs/PINS.md`; if you need it, that is a plan gap worth logging.
- **Confusing the transport strings** — hyphen on the server, underscore in one client, `sse` for the
  deprecated one. Verify all three.
- **Not comparing what each framework reports from `list_tools`.** A framework that mangles your
  descriptions is mangling your prompt.
- **Fighting a framework that needs thirty lines.** Record it; that is a scorecard row.
- **Forgetting to delete the old declarations.** The whole point was 4+K, and the deletion is the
  evidence.

---

## §7 Request budget

**Declared: ~6 model requests, Groq.**

| What | Requests |
|---|---|
| `tests/test_mcp_mount.py` | **0** |
| `list_tools` in all four frameworks | **0** |
| `mount_all_four.py` — one question × four frameworks | 4 |
| One retry allowance | 2 |

**Note that the comparison itself is nearly free.** Listing tools, reading schemas and counting mount
lines cost nothing; only the four end-to-end questions cost anything. **That is the shape of a good
comparison day** — spend on the confirmation, not on the analysis.

---

## §8 Verify before you code

Written **2026-08-20** against `mcp==2.0.0`, spec revision **2026-07-28**:

- **The transport string** — `"streamable-http"` on the server, and what each client wants. SSE is
  the deprecated legacy transport; make sure you are not on it.
- **The HTTP path** — is it `/mcp`, or does `FastMCP` mount elsewhere? `ENDPOINT` assumes `/mcp`.
- **Does `mcp.run()` take `host` and `port`,** or does streamable HTTP need an ASGI server (uvicorn)?
  If it needs uvicorn, that is a ledger row (and Day 85 needs it anyway).
- **The four mount packages** — `agents.mcp`, `crewai_tools.MCPServerAdapter`,
  `langchain_mcp_adapters`. Which exist, which are already installed, which need pinning.
- **Is `langchain-mcp-adapters` in `docs/PINS.md`?** If not, this is a plan gap — log it.
- **`require_approval` shape in the SDK** — per tool, per server, or both? OAI-15's distinguishing
  feature.
- **Does any client other than the SDK cache `tools/list`?** A row in the table.
- **CrewAI's context-manager lifecycle** — what happens if the crew outlives the `with` block?
- **What does each client do when the server is down** — raise at mount, or at first call? That
  changes where your error handling goes.
- `https://docs.crewai.com`, the Agents SDK MCP docs, and LangChain's MCP adapter docs — today.

---

## §9 Say it in an interview

> "I built one MCP server and mounted it into four frameworks in a day, and the thing that makes that
> comparison worth anything is that the server is byte-identical in all four cases — every other
> framework comparison I'd done had a confound. Three per-framework tool declarations got deleted,
> which is the 4×K to 4+K arithmetic as a diff rather than a slide. The differences I found are the
> real output: only the Agents SDK has a first-class approval concept for MCP tools, meaning it treats
> a tool from a server you don't control as a different trust category from a local function — the
> other three treat them as ordinary tools. Only one caches the tools listing, which is a property the
> 2026-07-28 revision added and most clients haven't picked up yet. And LangChain's client is
> multi-server by design where the SDK's is per-agent, which is a different bet about how many servers
> you end up with. I kept one seam module owning the endpoint and an allowlist of tools each mount may
> take — otherwise you rebuild the N×M problem one layer up — and I'd be precise that the allowlist is
> client-side selection, not server-side enforcement. The server still answers anyone who reaches it,
> which is why it's bound to localhost and why the auth day exists."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 55
```
