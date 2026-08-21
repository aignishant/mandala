# Day 55 — CHECKLIST

**IDs covered:** MCP-05 🛠️ 🔁 (client integration ×4), OAI-15 🛠️ (MCP in the Agents SDK)

## Demo command

```bash
# terminal 1
uv run python -m mandala_mcp.http_server
# terminal 2
uv run python days/day-55/lab/mount_all_four.py   # 4 requests
uv run pytest tests/test_mcp_mount.py -v
```

Expected: one server process, four frameworks, the same tools, the same answer — and three deleted
tool declarations.

## Setup

- [ ] `./m start 55` and `./m scaffold 55` run
- [ ] **Streamable HTTP chosen over stdio**, and can say why (one process, four clients)
- [ ] Transport string verified on the server **and** in each client
- [ ] `httpx` need checked against the `mcp` SDK's own deps; pinned + logged if added directly
- [ ] Any MCP adapter packages verified, **pinned exactly, ledger rows added**
- [ ] `langchain-mcp-adapters` absence from `docs/PINS.md` logged as a plan gap if needed
- [ ] Files created (`http_server.py`, `mcp_mount.py`, tests, two lab files)

## The seam

- [ ] `mcp_mount.py` owns the endpoint, the allowlist and the timeout — **one place**
- [ ] `ENDPOINT` read from the environment with a **localhost** default
- [ ] `HOST` defaults to `127.0.0.1`, **not** `0.0.0.0` — and can say why that matters today
- [ ] `ALLOWED_TOOLS` allowlist present, and understood as **client-side selection, not enforcement**
- [ ] `MOUNT_TIMEOUT_S` set — Day 49's policy at the boundary
- [ ] `http_server.py` imports the **unchanged** `mcp` object — transport is configuration

## MCP-05 — the four mounts

- [ ] Agents SDK mounted
- [ ] CrewAI mounted
- [ ] LangChain mounted
- [ ] LangGraph mounted (via LangChain's adapter, or its own)
- [ ] **Each mount under ~10 lines** — or the excess recorded as a finding
- [ ] Every adapter imports from `mcp_mount`, hard-codes nothing
- [ ] Every adapter filters by `ALLOWED_TOOLS`
- [ ] `list_tools` compared across all four: **names, descriptions, schemas**
- [ ] Noted any framework that mangles descriptions — that is your prompt being mangled

## OAI-15 — the SDK's distinguishing feature

- [ ] `require_approval` wired, and its shape recorded (per tool? per server?)
- [ ] Can say why treating a remote tool as a **different trust category** is a design insight
- [ ] `cache_tools_list=True` used — the 2026-07-28 cacheable-list property, in practice
- [ ] Checked whether any other client caches the listing
- [ ] Noted for Day 66

## The deletion — the milestone

- [ ] Old per-framework tool declarations **deleted**
- [ ] Day 53's `test_the_count_of_declarations_is_recorded` went red, and the number updated
- [ ] Before/after count logged in `docs/CHANGELOG_PLAN.md`
- [ ] Can state the 4×K → 4+K result **with your own numbers**

## `mcp_bakeoff.md` — today's real deliverable

- [ ] Twelve-row table filled for all four frameworks
- [ ] "Declarations deleted today" recorded
- [ ] "The one that surprised me" written
- [ ] Which framework treats a remote tool as a different trust category — answered
- [ ] **"What still lives on my side" answered honestly** — the mount gave back tool *selection*, not
      *enforcement*; the gap closes on Days 56–57

## Tests that must be able to fail

- [ ] `test_the_endpoint_is_defined_in_one_place` — **flip it:** hard-code a URL, see red
- [ ] `test_the_allowlist_is_a_subset_of_what_the_server_offers`
- [ ] `test_the_allowlist_excludes_nothing_dangerous_by_accident` — the anti-rot test
- [ ] `test_the_mount_has_a_timeout`
- [ ] `test_the_server_name_matches_the_server`
- [ ] `test_the_endpoint_is_localhost_by_default` — **to be deleted on Day 56, deliberately**
- [ ] `test_the_http_server_does_not_bind_all_interfaces_by_default`
- [ ] `test_every_framework_filters_by_the_allowlist`
- [ ] `test_the_declaration_count_went_down` — the milestone, with the celebration in the message
- [ ] All tests cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why is today's framework comparison better than every previous one?
- [ ] Why one HTTP server rather than four stdio subprocesses?
- [ ] What would go wrong if each adapter hard-coded the endpoint?
- [ ] What does `ALLOWED_TOOLS` actually guarantee, and what does it not?
- [ ] Which framework treats an MCP tool as a distinct trust category, and why does that matter?
- [ ] What is still missing since Day 54 §4, and which day closes it?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~6, Groq)
- [ ] Noted that the comparison itself was nearly free
- [ ] Transport strings confirmed (server, and each client)
- [ ] HTTP path confirmed (`/mcp`?)
- [ ] Whether `mcp.run()` needs uvicorn — answered (Day 85 needs the answer too)
- [ ] `require_approval` shape confirmed
- [ ] CrewAI adapter's connection lifecycle established
- [ ] Server-down behaviour recorded per framework
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 55
```

- [ ] Bake-off rows updated: **MCP mount ergonomics**, **approval support**, **list caching**,
      **multi-server design**
- [ ] `./m done 55` succeeded — trackers updated automatically
