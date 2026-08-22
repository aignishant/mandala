---
name: gate
description: Run a phase gate from Part 5 of the master plan, including the depth sweep and the freshness check
argument-hint: [phase-number]
allowed-tools: Read, Grep, Glob, Bash(uv run *), Bash(git *), Bash(./m *), WebFetch, WebSearch
---

# Phase $ARGUMENTS gate review

1. Read the Phase $ARGUMENTS gate in `docs/00_MASTER_PLAN_AGENT_STACKS.md` Part 5.
2. Verify each gate criterion against the actual repo — run the tests and demos; don't take my word
   for it. Produce a pass/fail table with the evidence (command run, output seen).
3. **Depth sweep.** Run `./m depth` across every day in the phase. A phase whose days do not satisfy
   the plan's Part 11 contract has not been taught, whatever the demos show. Report the part count
   per day; flag any day that looks thin against its subject.
4. Run the standing freshness check (Principle 13): fetch the release-notes/changelog pages for
   every pin in the plan's Part 2, the MCP spec revision page, and the live free-tier limits for
   `docs/RATE_BUDGET.md`. Report: unchanged / changed-cosmetic / changed-material.
5. If anything changed materially: draft `docs/NN_MASTER_PLAN_ADDENDUM_<topic>.md` in the same
   format as the existing addenda (amend first — Principle 14). **Do not modify code in this
   session.**
6. If the gate passes: write `docs/adr/gate-phase-$ARGUMENTS.md` summarizing the evidence, run
   `./m tracker`, and tag the repo `phase-$ARGUMENTS-complete`.

A gate is a cold read. If I ask you to pass a criterion on the strength of "it basically works",
fail it and say why.
