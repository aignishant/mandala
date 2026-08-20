---
name: freshness
description: Friday freshness check across all pinned packages and the MCP spec (Principle 13)
allowed-tools: Read, WebFetch, WebSearch, Bash(git *)
---

# Weekly freshness check

For each pin in docs/00_MASTER_PLAN_AGENT_STACKS.md Part 2 (openai-agents, crewai,
langchain, langgraph, langsmith, MCP spec, A2A): fetch its changelog/release page,
compare against the pinned baseline, and log one line per item in
docs/CHANGELOG_PLAN.md under today's date — including explicit nil reports
("checked, unchanged"). If anything is material, propose an addendum per the
plan's amendment protocol and stop there.