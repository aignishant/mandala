# Day 54 — CHECKLIST

**IDs covered:** MCP-03 🛠️ (tools, resources, prompts), MCP-04 🛠️ (build `ticket-db`)

## Demo command

```bash
uv run python days/day-54/lab/inspect_server.py   # 0 requests
uv run pytest tests/test_mcp_server.py -v
```

Expected: three tools with their schemas, two resources, one prompt, and a live `get_ticket` call —
all with no model involved.

## Setup

- [ ] `./m start 54` and `./m scaffold 54` run
- [ ] `mcp==2.0.0` confirmed present from Day 16
- [ ] `httpx` need settled — today is stdio
- [ ] **`src/mandala_mcp/` created as a separate package** from `src/mandala/`, and can say why
- [ ] `data.py` / `server.py` split: logic vs. declarations
- [ ] Files created (server, data, tests, two lab files)

## MCP-03 — the three primitives

- [ ] Can state the distinction by **who initiates**
- [ ] Can give the request-budget argument: a tool costs 2 turns, a resource costs 0
- [ ] `get_ticket`, `search_tickets`, `search_handbook` as **tools**
- [ ] `tickets://recent` and `tickets://{ticket_id}` as **resources**
- [ ] `triage_this_ticket` as a **prompt**
- [ ] `primitive_choice.md` written, every row justified
- [ ] The `get_ticket` / `tickets://{id}` overlap explained, not apologised for
- [ ] Turn savings computed using Day 38's counts
- [ ] **"Prompts: feature or hazard?" answered** — and noted for Day 66

## MCP-04 — the server

- [ ] Server name `ticket-db` fixed — four clients will hard-code it
- [ ] Docstrings written as **model-facing prompt text**, not developer docs
- [ ] Docstring style confirmed against what the SDK actually parses
- [ ] Bad ids return **guidance**, not an exception — and can say why
- [ ] `limit` clamped rather than rejected — and can say when clamping is right
- [ ] Resource URI scheme chosen and understood as **permanent**
- [ ] The prompt carries Day 29's house rule verbatim
- [ ] `_search` moved to `data.py`; `server.py` holds declarations only
- [ ] stdio transport only — **streamable HTTP deliberately deferred**

## Staying stateless (§3.4)

- [ ] No module-level mutable state — verified by the AST test
- [ ] No per-caller counters or rate limiting inside the server
- [ ] No lazy index built on first call — build at import, or accept the per-call cost
- [ ] Can name all three temptations and why each breaks Day 85's proof

## §4 — what the process boundary cost

- [ ] Can fill in the three-row lost/kept table
- [ ] **`InjectedToolArg` is gone** — found where the correlation id goes instead
- [ ] **`permissions.py` no longer applies** — and can say what replaces it (Days 56, 57)
- [ ] Wrote the sentence: *acceptable only because read-only, local, stdio-only*
- [ ] Can state the general shape: portability takes away in-process privileges
- [ ] Yesterday's prediction compared against what actually happened

## Tests that must be able to fail

- [ ] `test_the_server_has_a_stable_name`
- [ ] `test_no_module_level_mutable_state` — **AST, not grep**; flip it: add a dict, see red
- [ ] `test_the_server_does_not_import_the_framework_code`
- [ ] `test_every_tool_has_a_model_facing_docstring`
- [ ] `test_results_are_bounded`
- [ ] `test_a_bad_id_returns_guidance_not_an_exception` — **flip it:** raise, see red
- [ ] `test_an_unknown_id_says_so`
- [ ] `test_the_server_is_read_only`
- [ ] `test_the_prompt_carries_the_house_rule` — MCP-01's payoff, as an assertion
- [ ] `test_server_py_holds_declarations_not_logic`
- [ ] `test_the_resource_uris_are_stable`
- [ ] Handlers called via `.fn(...)` — **no client, no transport, no subprocess**
- [ ] All tests cost **0 model requests**

## `inspect_server.py`

- [ ] Ran successfully over stdio
- [ ] **Printed every tool's `inputSchema`** — the habit to keep for third-party servers
- [ ] Noted where templated resources appear in the listings
- [ ] Noticed content comes back as a **list of typed blocks** — same shape as Day 37
- [ ] **Answered why `ClientSession` exists if the core is stateless**

## Understanding check — answer out loud

- [ ] Tool, resource, or prompt — how do you choose?
- [ ] Why does a resource cost zero model turns?
- [ ] What does a server-supplied prompt buy you, and what does it risk?
- [ ] Name the three ways to accidentally become stateful.
- [ ] What did you lose by moving the tool out of your process?
- [ ] Why is "read-only, local, stdio-only" the reason no auth is acceptable today?

## Budget & freshness

- [ ] Logged in `docs/RATE_BUDGET.md`: **0 requests**
- [ ] Noted for the bake-off: MCP work is testable without a provider
- [ ] `FastMCP` import path confirmed for `mcp==2.0.0`
- [ ] Docstring style the SDK parses — confirmed
- [ ] **Pydantic argument models supported?** — the most valuable question; answered
- [ ] Decorated-tool underlying-function attribute confirmed
- [ ] Templated-resource listing location confirmed
- [ ] **Whether a tool handler can read request metadata** — answered (§4 depends on it)
- [ ] `mcp.run()` transport default confirmed, and the HTTP flag found for Day 55
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 54
```

- [ ] `./m done 54` succeeded — trackers updated automatically
