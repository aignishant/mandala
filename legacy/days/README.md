# 📅 days/ — the 90 written days

**Never done this before?** Start at [`day-00-setup/LESSON.md`](day-00-setup/LESSON.md).
**Already set up?** Run `./m status`, it tells you which day is next.
**Want the map?** [`../docs/CURRICULUM_INDEX.md`](../docs/CURRICULUM_INDEX.md).

---

## The three rules these docs follow

1. **All the code lives in the docs. None of it is pre-written in the repo.**
   You type it, you own it. There is no `src/mandala/*.py` waiting for you — every line you will
   ever run is written out in a lesson, and you create the file yourself. You cannot debug on Day 60
   what you never read on Day 12.

2. **Every code block is followed by a line-by-line walkthrough.**
   Not a summary — an explanation of what each line does and *why it is that line and not another*.
   If a line is unexplained anywhere in these 91 documents, that is a bug in the doc.

3. **Every command is given in full.**
   `mkdir -p`, `touch`, `uv add package==1.2.3`, the run command, the test command. You should never
   have to infer "and now presumably I create a folder".

---

## Which shell

You are on **Windows 11**. Everything here is written for **Git Bash** (installed with Git).
Open it from the Start menu and:

```bash
cd /c/Users/nisha_gnzw/OneDrive/Desktop/Projects/mandala
```

If you must use PowerShell:

| Git Bash (used in these docs) | PowerShell |
|---|---|
| `mkdir -p a/b/c` | `New-Item -ItemType Directory -Force a/b/c` |
| `touch f.py` | `if (-not (Test-Path f.py)) { New-Item -ItemType File f.py }` |
| `cat > f <<'EOF' … EOF` | `@'…'@ \| Set-Content -Encoding utf8 f` |
| `rm -rf folder` | `Remove-Item -Recurse -Force folder` |
| `./m status` | `bash ./m status` |
| `cmd1 && cmd2` | `cmd1; if ($?) { cmd2 }` |

**`make` is not used anywhere in this project** and is not installed on your machine. The `./m`
script (built on Day 0) replaces it.

---

## What's in a day folder

```
days/day-NN/
  LESSON.md      # the teaching + every line of code + every command
  CHECKLIST.md   # the definition of done. `./m done NN` refuses to commit until it's ticked.
  lab/           # you create this; `./m scaffold NN` makes the folder
```

### The shape of every LESSON.md

| Section | What it's for |
|---|---|
| **frontmatter** | machine-readable tracking. **`./m` edits this, not you.** |
| **§ Where we are** | yesterday / today / tomorrow, in one line each |
| **§ The story** | the idea in plain English with an analogy, before any code |
| **§ Setup — run this** | every `mkdir`, `touch`, `uv add` and `export` today needs |
| **§ per-ID sections** | plain idea → why Mandala needs it → the code → **line by line** → watch it break → the interview line |
| **§ Build brief** | the file list, and which parts are yours to write |
| **§ The eval** | the test that must be able to **fail** (Principle 7) |
| **§ Request budget** | how many free-tier calls today costs (Principle 5) |
| **§ Traps** | the mistakes that eat an evening |
| **§ Verify before you code** | the live docs pages to check — these files were written 2026-08-20 |
| **§ Done when** | pointer to `CHECKLIST.md` |

---

## The daily rhythm

```bash
./m status              # what's next?
./m start 7             # marks Day 7 in-progress, prints its IDs
./m scaffold 7          # creates days/day-07/lab/
                        # ... read LESSON.md, run its Setup block, write the code ...
./m check               # lint + offline tests. Free. No network.
                        # ... tick the boxes in CHECKLIST.md ...
./m done 7              # refuses if boxes are unticked or check is red;
                        # otherwise commits and updates every tracker file
```

**You never hand-edit a status, an index row, a coverage table, or the changelog.** `./m done`
owns all four. That is the whole point of building it on Day 0.

---

## Rules that apply to every single day

From `CLAUDE.md` and the plan's Part 1. Not optional.

1. **No commit = day not done.** (Principle 1) — enforced by `./m done`.
2. **Naked before framework.** If a concept has an `AG-` ID, you saw the raw version first.
   (Principle 2)
3. **Pin everything.** Every agent sets `model=` explicitly; every package has an exact version.
   (Principle 4)
4. **$0, always.** Gemini · Groq · OpenRouter `:free` · optional local Ollama · local
   `sentence-transformers` for embeddings. If a lab seems to need a paid key, you have misread it —
   the free replacement is in the lesson. (Principle 5)
5. **Read-only by default.** Write access only when the day's IDs say so; external writes always
   behind an approval step. (Principle 6)
6. **The test must be able to fail.** A green test that cannot go red is decoration. (Principle 7)
7. **Reality differs from the plan → amend the plan first.** Never silently adapt. (Principle 14)

---

## How a future session picks up where you left off

Everything is on disk. There is no hidden state.

```bash
./m status                                   # the dashboard
./m sync                                     # rebuild index+traceability from the day files
./m check-ids                                # prove lessons and TRACEABILITY.md agree
git log --oneline | head -20                 # what you actually committed
grep -c '⬜' ../docs/TRACEABILITY.md          # IDs still open
```

**The four files that carry state:**

| File | Carries |
|---|---|
| `days/day-NN/LESSON.md` frontmatter | `status`, `commit` |
| `days/day-NN/CHECKLIST.md` | that day's tick-boxes |
| `docs/CURRICULUM_INDEX.md` | the status column (derived — regenerate with `./m sync`) |
| `docs/CHANGELOG_PLAN.md` | append-only history: completed days + plan amendments |

---

## One honest caveat

These docs were written on **2026-08-20** against the pins verified that day
([`../docs/PINS.md`](../docs/PINS.md)) and master plan **v1.1.0**. Library APIs drift. Free-tier
model rosters rotate faster than libraries do.

So **every lesson ends with "Verify before you code"** — the live docs page for the exact API it
teaches. Check it. Ninety seconds, and it is the highest-value habit in the whole plan: Principle 13
run daily instead of weekly.

If you find real drift: **stop, log it in `docs/CHANGELOG_PLAN.md`, amend the plan**, *then* change
code. That reflex is the actual deliverable of these 90 days.
