---
name: gate
description: Run a phase gate from Part 5 of the master plan, including the freshness check
argument-hint: [phase-number]
allowed-tools: Read, Grep, Glob, Bash(uv run *), Bash(git *), WebFetch, WebSearch
---

# Phase $ARGUMENTS gate review

1. Read the Phase $ARGUMENTS gate in docs/00_MASTER_PLAN_AGENT_STACKS.md Part 5.
2. Verify each gate criterion against the actual repo (run tests/demos; don't take
   my word for it). Produce a pass/fail table.
3. Run the standing freshness check (Principle 13): fetch the release-notes /
   changelog pages for every pin in the plan's Part 2 and the MCP spec page.
   Report: unchanged / changed-cosmetic / changed-material.
4. If anything changed materially: draft docs/NN_MASTER_PLAN_ADDENDUM_<topic>.md in
   the same format as 01_MASTER_PLAN_ADDENDUM_GAPS.md (amend first — Principle 14).
   Do not modify code in this session.
5. If the gate passes: write docs/adr/gate-phase-$ARGUMENTS.md summarizing evidence,
   and tag the repo `phase-$ARGUMENTS-complete`.