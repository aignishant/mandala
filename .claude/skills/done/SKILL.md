---
name: done
description: Verify a finished day against its checklist and the depth contract, then commit it
argument-hint: [day-number]
allowed-tools: Read, Grep, Glob, Bash(uv run *), Bash(git *), Bash(./m *)
---

# Close out Day $ARGUMENTS

1. Run `./m depth $ARGUMENTS`. A day that fails the plan's Part 11 depth contract is not finished,
   regardless of whether the code works. Report every failure; do not hand-wave past one.
2. Run the demo command and the tests from `days/day-$ARGUMENTS/CHECKLIST.md`.
3. **Verify at least one test can actually go red** (Principle 7): break the behaviour it guards,
   watch it fail, restore it. A green test that cannot fail is decoration.
4. Grade my `TODO(me)` implementations: correctness first, then idiom, then one improvement
   suggestion max (don't rewrite my work).
5. Check ID coverage: every ID for this day must be exercised by a part document, the lab, or a test.
6. Check the request budget: what the hub's §6 predicted vs. what the day actually spent. If a free
   tier was exhausted, say so — that is a finding for `docs/RATE_BUDGET.md`, not a footnote.
7. If anything fails, list exactly what and stop — no commit.
8. If green: `./m done $ARGUMENTS`, which refuses on unticked boxes, runs the checks, commits, and
   regenerates `docs/TRACKER.md`, `docs/CURRICULUM_INDEX.md` and `docs/TRACEABILITY.md`.

Never tick a checklist box on my behalf. The boxes are my statement that I understood the part, and
`./m done` refusing to commit is the point of the gate.
