---
name: freshness
description: Friday freshness check across all pinned packages, the free-tier limits, and the MCP spec (Principle 13)
allowed-tools: Read, WebFetch, WebSearch, Bash(git *), Bash(uv *)
---

# Weekly freshness check

For each pin in `docs/00_MASTER_PLAN_AGENT_STACKS.md` Part 2 — `openai-agents`, `crewai`,
`crewai-tools`, `langchain`, `langchain-core`, `langgraph`, `langsmith`, `mcp`, the **MCP spec
revision page**, and A2A — fetch its changelog/release page and compare against the pinned baseline.

Then re-check the things that rot faster than libraries:

- **The free-tier limits** in `docs/RATE_BUDGET.md` — RPM/RPD/TPM from each provider console.
  These change without notice and are the actual budget (Principle 5).
- **The OpenRouter `:free` roster** — every `:free` model id is perishable. A vanished id is a
  finding, not a bug to work around.

Log one line per item in `docs/CHANGELOG_PLAN.md` under today's date — **including explicit nil
reports** ("checked, unchanged"). A freshness check with no nil reports is indistinguishable from a
freshness check that never ran.

If anything is material, propose an addendum per the plan's amendment protocol (Principle 14) and
**stop there**. Do not modify code in this session.
