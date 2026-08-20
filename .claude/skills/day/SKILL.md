---
name: day
description: Generate the lesson, lab scaffold, and checklist for a given day of the master plan
argument-hint: [day-number]
---

# Generate Day $ARGUMENTS of the Mandala plan

1. Read docs/00_MASTER_PLAN_AGENT_STACKS.md. From Part 4 (matrices) and Part 5
   (phase map), collect every ID slotted to Day $ARGUMENTS, plus the phase theme
   and the phase gate it feeds.
2. Read days/ to see what already exists — build on prior days' code in src/mandala/,
   never duplicate it. If the previous day's CHECKLIST.md has unchecked items, warn me
   and ask whether to proceed.
3. Create days/day-$ARGUMENTS/ containing:
   - LESSON.md — for each ID today: (a) simple explanation in the plan's voice,
     (b) why it matters for Mandala, (c) a minimal runnable example, (d) one
     "interview line" I could say aloud. End with links to the official docs
     pages you actually verified (fetch them; do not trust memory for API shapes).
   - lab/ — starter code with TODO(me) markers for the parts I must write myself
     (the learning), and completed plumbing for the parts that are boilerplate.
     Wire it into src/mandala/ when the day contributes capstone code.
   - CHECKLIST.md — the day's definition-of-done: demo command to run, at least
     one pytest that fails before the TODOs are done and passes after, the ID
     coverage list, and a "commit made" checkbox.
4. Honor CLAUDE.md rules: pinned models, cheap tier by default, read-only tools,
   naked-before-framework ordering, eval included.
5. Do NOT solve my TODO(me) sections. Teach; don't do the reps for me.
6. Finish by printing: today's IDs, the demo command, and the estimated token/cost
   footprint of running the lab.