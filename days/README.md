# 📅 days/ — the 90 written days

**Start here every morning:** `docs/CURRICULUM_INDEX.md` → find today's row → open its `LESSON.md`.

---

## What's in a day folder

```
days/day-NN/
  LESSON.md      # the teaching. Written 2026-08-20 in the bulk pass. Read it first.
  CHECKLIST.md   # the definition of done. Tick boxes as you go.
  lab/           # NOT here yet — generated on the day by `/day NN`
```

### Why `lab/` is missing

The lessons were all written up front so you own the curriculum without needing a model in the
loop. The **lab starter code was deliberately not** — because a scaffold written on Day 1 for Day 67
would be guessing at what `src/mandala/` looks like by then, and would rot. Each `LESSON.md` has a
**§ Build brief** that fully specifies the lab: file paths, function signatures, the `TODO(me)`
list, and the acceptance criteria. Two ways to get the lab:

1. Run `/day NN` — generates `lab/` against the code that actually exists today.
2. Write it yourself from the Build brief. This is the better learning, and it is always allowed.

---

## The shape of every LESSON.md

| Section | What it's for |
|---|---|
| **frontmatter** | machine-readable tracking. **You edit `status:` and `lab_scaffolded:`.** |
| **§0 Where we are** | one line each: yesterday, today, tomorrow. Never lose the thread. |
| **§1 The story** | the idea in plain English, with an analogy, before any code. |
| **§2…n Per-ID sections** | one section per ID: the plain idea → why Mandala needs it → the smallest thing that works → watch it break → the interview line. |
| **§ Build brief** | exactly what to build, where, and which parts are yours to write. |
| **§ The eval** | the test that must be able to **fail** (Principle 7). |
| **§ Request budget** | how many free-tier calls today costs (Principle 5). |
| **§ Traps** | the mistakes that eat an evening. |
| **§ Verify before you code** | the live docs pages to check first — because API shapes drift and this file was written on 2026-08-20. |
| **§ Done when** | pointer to `CHECKLIST.md`. |

---

## Rules that apply to every single day

These come from `CLAUDE.md` and the plan's Part 1. They are not optional.

1. **No commit = day not done.** (Principle 1)
2. **Naked before framework.** If a concept has an `AG-` ID, you saw the raw version first.
   Never let a framework be your first exposure to an idea. (Principle 2)
3. **Pin everything.** Every agent sets `model=` explicitly. Every package has an exact version.
   Framework defaults are never trusted. (Principle 4)
4. **$0, always.** Free tiers only: Gemini, Groq, OpenRouter `:free`, optional local Ollama, local
   `sentence-transformers` for embeddings. If a lab seems to need a paid key, you have
   misread it — the free replacement is in the lesson. (Principle 5)
5. **Read-only by default.** A generated tool gets write access only if the day's IDs say so, and
   external writes always sit behind an approval step. (Principle 6)
6. **The test must be able to fail.** A green test that cannot go red is decoration. (Principle 7)
7. **If reality differs from the plan — stop and amend the plan first.** Do not silently adapt.
   (Principle 14)

---

## Tracking, and how a future session picks up where you left off

Everything a future session needs is on disk. There is no hidden state.

```bash
# Where am I?
grep -H '^status:' days/day-*/LESSON.md | grep -v not-started

# What's the next unstarted day?
grep -l '^status: not-started' days/day-*/LESSON.md | head -1

# What have I actually committed?
git log --oneline | grep '^.\{8\} day-'

# Which IDs are still uncovered?
grep '⬜' docs/TRACEABILITY.md | wc -l
```

**The three files that carry state:**

| File | Carries |
|---|---|
| `days/day-NN/LESSON.md` frontmatter | per-day `status`, `lab_scaffolded`, `commit` |
| `days/day-NN/CHECKLIST.md` | the tick-boxes for that day's definition of done |
| `docs/CHANGELOG_PLAN.md` | append-only history: completed days + plan amendments |

`/done NN` updates all three and commits. `/gate N` regenerates `docs/TRACEABILITY.md` and writes a
gate record into `docs/adr/`.

---

## One honest caveat about these docs

They were written on **2026-08-20** against the pins verified that day (`docs/PINS.md`) and against
master plan **v1.1.0**. Library APIs drift. Free-tier model rosters rotate faster than libraries do.

So **every lesson ends with a "Verify before you code" section** pointing at the live docs page for
the exact API it teaches. Check it. It takes ninety seconds and it is the single highest-value habit
in this whole plan — it is Principle 13 in miniature, run daily instead of weekly.

If you find a real drift: **stop, log it in `docs/CHANGELOG_PLAN.md`, and amend the plan** before
you change any code. That reflex is the actual deliverable of these 90 days.
