---
name: day
description: Generate the hub, the parts/ sub-documents, the lab scaffold and the checklist for a given day of the Mandala plan
argument-hint: [day-number]
---

# Generate Day $ARGUMENTS of the Mandala plan (v2.0.0 — hub + `parts/`)

> **Read `docs/00_MASTER_PLAN_AGENT_STACKS.md` Part 11 before writing a single line.** It is the
> depth contract this skill implements. This skill is the procedure; Part 11 is the standard.

## The three commitments (Part 11.1 — everything below follows from these)

1. **One idea per document.** If it needs "also" to introduce its second half, it is two documents.
2. **No clocks.** Never write a time estimate, a duration, a "should take ~2 hours", or a pace —
   not in frontmatter, not in prose, not in the checklist. A topic is finished when it is
   understood, and a reader may spend five sittings on one part. **Never trim an explanation
   because the day is getting long — split it into another part instead.**
3. **Zero to production, in one document.** Open where a reader who has never heard of the idea can
   stand. End where a professional stands: the real-system version, what breaks under load or a
   provider outage, what a senior reviewer says, what an interviewer probes.

## Step 1 — gather

1. Read the plan (Part 4 matrices, Part 5 phase map, **Part 11 depth contract**) and
   `docs/CURRICULUM_INDEX.md`. Collect every ID slotted to Day $ARGUMENTS, the phase theme, the
   day's `kind`, and the gate that phase feeds.
2. Read `docs/TRACKER.md` for what is already written and at what depth.
3. Read `days/` for what exists. Build on prior days' code in `src/mandala/` — never duplicate it.
   If the previous day's `CHECKLIST.md` has unticked boxes, warn me and ask before proceeding.
4. **Read `legacy/days/day-NN/LESSON.md`.** It is the v1.1.0 draft: **mine it for correctness, then
   discard its structure.** Everything it covered must survive into the parts, and each surviving
   topic must gain the story, the mechanism, the real failure text, the production face and the
   check it did not have. Never copy a legacy section across wholesale.
5. **Fetch the live docs page for every API the day teaches** (Principle 13, run daily). Do not
   write a code block from memory. If the live page contradicts the plan, STOP and propose an
   amendment (Principle 14) — do not silently adapt.

## Step 2 — plan the split (do this before writing prose)

6. List the day's subtopics. Group them into **sections** that share one mental model — usually one
   section per curriculum ID, per stage of the agent loop, or per layer of the framework's stack.
   State the grouping; an unexplained numbering is a bug.
7. Split by **idea boundaries, never by length or pace**. There is no target part count. Five parts
   if the subject needs five; twenty if it needs twenty. `setup` days split per tool or file;
   `lab` days per mechanism → behaviour → edge case → failure mode → production use; `concept` days
   one claim per part; `gate` days one acceptance criterion per part; `capstone` days one component
   per part in build order.
8. Assign each part a `level` — `foundation` (knows what it is), `working` (can use it in their own
   code), `production` (knows what changes in a real system). A day should climb. A day that is all
   `foundation` is a tutorial; a day opening at `production` has skipped the reader.
9. Apply the **one-idea test** and the **no-shortcut test** (no "for now, just accept that" without
   a forward link to the part that explains it) to each planned part *before* writing.
10. Print the planned part list to me before writing. If it looks thin, I will say so.

## Step 3 — write the parts (`days/day-NN/parts/<NN>/<section>.<sub>-<slug>.md`)

11. **One folder per section**, named with two zero-padded digits — `parts/01/`, `parts/02/`,
    `parts/12/`. Every part lives inside its section's folder; none is ever loose in `parts/`, and
    the folder number must match the number before the dot in the filename.
12. One file per subtopic, named `<section>.<subtopic>-<kebab-slug>.md`. The slug says what the part
    *teaches*, never where it sits. Numbering starts at `1`, has no gaps.
13. **Links are relative to the part's own folder**: a sibling in the same section is
    `1.2-<slug>.md`; a part in another section is `../01/1.5-<slug>.md`; the hub is
    `../../LESSON.md`. `prev` and `next` in the frontmatter use the same form. The hub's §2 map
    links the full path from the day folder: `parts/01/1.1-<slug>.md`.
14. Every part carries all ten sections of Part 11.4, in this order:
    - **frontmatter** — `day`, `part`, `title`, `ids`, `level`, `prerequisites`, `prev`, `next`.
      **No duration field of any kind.**
    - **One-line answer** — the claim in one sentence, before anything else
    - **The story** — a concrete scene first: a person, a machine, a failure, a decision. No jargon
      at all in this section. This is the hook the definition hangs on.
    - **The idea in plain language** — the concept assuming zero prior knowledge; every term defined
      on first use, **including terms from earlier days**, with a link to the part that introduced
      them. No code.
    - **Why Mandala needs it** — the concrete downstream day that breaks without this
    - **The mechanism** — how it actually works: runnable code, the protocol exchange written out
      message by message, or the diagram. Nothing skipped as "obvious".
    - **Line by line** — a `**Line by line:**` list **immediately after each code block**: every
      non-obvious token, and *why that line and not another*
    - **When it breaks** — the **real** error text verbatim, what it means, the smallest fix
    - **In production** — the real-system version of this idea: what a professional writes instead
      of the teaching version, what degrades under load, concurrency or a provider outage, the
      blast radius, the failure that only shows with real traffic, the review comment a senior
      engineer leaves, and the interview question that finds out whether you have actually shipped
      it. **Not optional. This is the section that makes the document professional rather than
      introductory.**
    - **Check yourself** — one command to run now, one question to answer out loud
15. Mermaid diagram whenever the concept is spatial, sequential, or a state machine.
16. Each part must pass the **standalone test**: readable cold, with its prerequisite part named
    and linked.

## Step 4 — write the hub (`days/day-NN/LESSON.md`)

17. The hub orients and assembles; **it never teaches**. No `Line by line:` in the hub. Required
    sections, in order (Part 11.5):
    - YAML frontmatter (`day`, `phase`, `phase_name`, `title`, `ids`, `principles`, `kind`,
      `plan_version: "v2.0.0"`, `parts`, `generated`, `status`, `lab_scaffolded`, `commit`)
    - a yesterday / today / tomorrow blockquote — **no time estimate**
    - `## §1 The story` — a scene and an analogy, plain language, NO code, NO jargon
    - `## §2 The map` — a table of every part: number, linked title (`parts/01/1.1-<slug>.md`), what
      it answers, `level`, grouped by section with one line saying what each *section* means.
      **No minutes column, ever.**
    - `## §3 Setup — run this` — every `mkdir`, `touch`, `uv add` the day needs, pinned
    - `## §4 Build brief` — files to create, with `TODO(me)` markers for the learner's reps
    - `## §5 The eval that must be able to fail` — pytest that is RED before the TODOs are done
    - `## §6 Request budget` — model calls, which provider, which free tier, cost (`0` is an
      answer; state it)
    - `## §7 Traps` — the mistakes that eat an evening
    - `## §8 Verify before you code` — live docs URLs, actually fetched, never from memory
    - `## §9 Say it in an interview` — one paragraph, spoken voice
    - `## §10 Done when` — pointer to `CHECKLIST.md`, defined by understanding and green checks,
      never by elapsed time

## Step 5 — the checklist (`days/day-NN/CHECKLIST.md`)

18. Demo command, setup boxes, **one box per part document** (read it, run its check-yourself,
    answer its out-loud question), build-brief boxes, a test box per test **including at least one
    "break it, watch it go red, fix it"**, the request budget actually spent, and the commit box.
    No time estimates.

## Step 6 — verify

19. Run `./m depth $ARGUMENTS`. Fix every failure; never hand-wave past one.
20. Run `./m tracker`.
21. Finish by printing: today's IDs, the part count, the demo command, and the request budget.

## Always

- Honor `CLAUDE.md`: exact pins, naked-before-framework, read-only by default, writes behind an
  approval step, at least one failing-able test, zero-budget model calls only.
- Every agent in every code block sets `model=` explicitly. No framework defaults, ever.
- Do **not** solve the `TODO(me)` sections. Teach; don't do the reps.
- Never name a person, instructor, author, channel, academy, bootcamp or training company anywhere
  in the output. The plan is self-contained and cites no external course or author; do not invent a
  lineage for it. Tool, library and specification names are fine.
- The failures this format exists to prevent (Part 11.8): splitting without deepening · summary in
  place of explanation · **stopping at the toy example** · assuming the previous day · code without
  failure · **trimming to fit** · solved reps. If a part gained no story, no mechanism, no failure
  text and no production section versus the `legacy/` prose, it is not done.
