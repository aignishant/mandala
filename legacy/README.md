# 🗃️ legacy/ — the v1.1.0 repository

This folder is the whole project as it stood under plan **v1.1.0**, moved here on **2026-08-22**
when plan **v2.0.0** replaced the documentation architecture.

**Nothing was deleted.** Every file was moved with `git mv`, so the history is intact and
`git log --follow legacy/days/day-03/LESSON.md` still shows the day it was written.

## Why it exists

v1.1.0 taught each day as a single `LESSON.md`. Every subject a day touched — the loop, tool
calling, the retry policy, the failure modes — sat under one `##` heading in one file. A reader
could not revisit one idea without re-reading four, could not tell a thinly-covered subtopic from a
missing one, and got explanations that had been quietly trimmed to keep the page from growing.

Plan v2.0.0 replaced that with a **hub plus one document per subtopic** (`days/day-NN/parts/`), each
written from zero prior knowledge through to production, with no clock anywhere. The full standard
is the plan's [Part 11](../docs/00_MASTER_PLAN_AGENT_STACKS.md#part-11--the-depth-contract-doc-architecture-v200).

## What is in here

| Path | What it was |
|---|---|
| `days/` | The 91 v1.1.0 single-file lessons (`day-00-setup` … `day-90`) plus their checklists and the old `days/README.md` |
| `docs/` | The v1.1.0 docs, including the previous `CURRICULUM_INDEX.md` with its hand-maintained status column |
| `skills/` | The four v1.1.0 Claude Code skills (`day`, `done`, `freshness`, `gate`) |
| `scripts/mandala.py` | The v1.1.0 driver: frontmatter status, index rewriting, traceability sync |
| `src/`, `tests/` | Code that Days 1–2 had pre-written into the repo, which rule 1 of `days/README.md` says should live in the lesson instead |
| `m`, `CLAUDE.md` | The v1.1.0 driver shim and operating rules |

## How to use it

**It is reference material to mine, never structure to copy** (plan Part 11.8).

When day *N* is rewritten, `legacy/days/day-NN/LESSON.md` is read first. Everything it covered
correctly must survive into the new `parts/` documents — and each surviving topic must gain the
story, the mechanism, the **real** failure text, the production face and the check-yourself that the
v1.1.0 prose did not have. A part that is a legacy section under a new filename is not a written
part; it is the failure mode the amendment exists to prevent.

Two things in here are actively out of date and must **not** be carried forward:

- **Time estimates.** The v1.1.0 prose says things like "half a day" and "this takes an evening".
  Principle 16 removed all of them, and `./m depth` fails a day that reintroduces one.
- **Pre-written source.** `legacy/src/` and `legacy/tests/` contain code the learner should be
  typing from the lesson. All the code lives in the docs.

## Reading a legacy day

```bash
cat legacy/days/day-07/LESSON.md
```

`./m start 7` will tell you when a day exists only here, and point you at `/day 7` to rewrite it.
`docs/TRACKER.md` marks every such day 🗃️ legacy.
