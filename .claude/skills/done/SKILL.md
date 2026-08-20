---
name: done
description: Verify a finished day against its checklist, then commit it
argument-hint: [day-number]
allowed-tools: Read, Grep, Glob, Bash(uv run *), Bash(git *), Bash(make *)
---

# Close out Day $ARGUMENTS

1. Run the demo command and the tests from days/day-$ARGUMENTS/CHECKLIST.md.
2. Grade my TODO(me) implementations: correctness first, then idiom, then one
   improvement suggestion max (don't rewrite my work).
3. Check ID coverage: every ID for this day must be exercised by lesson, lab, or test.
4. If anything fails, list exactly what and stop — no commit.
5. If green: update CHECKLIST.md boxes, append one line to docs/CHANGELOG_PLAN.md
   ("Day $ARGUMENTS complete — IDs: ..."), and commit with message
   "day-$ARGUMENTS: <IDs> — <one-line summary>".