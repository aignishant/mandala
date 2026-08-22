---
day: 0
phase: -1
phase_name: "Setup (before Day 1)"
title: "Setup — the toolchain, the skeleton, and the tracker"
ids: []
kind: setup
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 0 — Setup: the toolchain, the skeleton, and the tracker

**Before Phase 0.** This is not one of the 90 days. It is the half-day of installing and typing that
makes Day 1 start cleanly.

> **Today:** install what's missing, create every folder and file the project needs, and build the
> small program that will track your progress for the next 90 days so you never update a checklist
> by hand.
> **Tomorrow:** Day 1 — pins, keys, and the real rate limits.

---

## §0 How to read every doc in `days/`

Three rules that apply to all 91 documents:

1. **All the code lives in these docs.** Nothing is pre-written in the repo. You type it (or
   copy it), you own it. That is the point — you cannot debug on Day 60 what you never read.
2. **Every code block is followed by a line-by-line walkthrough.** If a line is not explained,
   that is a bug in the doc — write it down and tell me.
3. **Every command is given in full.** `mkdir`, `touch`, `uv add`, everything. You should never have
   to guess "and now presumably I create a folder".

### Which terminal to use

You are on **Windows 11**. You have two shells and this project uses **Git Bash** throughout, because
every command in these docs is written in POSIX form (`mkdir -p`, `touch`, forward slashes).

**Open Git Bash** (it came with Git): press Start, type `Git Bash`, hit enter. Then:

```bash
cd /c/Users/nisha_gnzw/OneDrive/Desktop/Projects/mandala
pwd
```

You should see the project path. If you prefer PowerShell for something, here is the translation
table — but you will have an easier 90 days in Git Bash:

| Git Bash (used in these docs) | PowerShell equivalent |
|---|---|
| `mkdir -p a/b/c` | `New-Item -ItemType Directory -Force a/b/c` |
| `touch file.py` | `if (-not (Test-Path file.py)) { New-Item -ItemType File file.py }` |
| `cat file.py` | `Get-Content file.py` |
| `rm -rf folder` | `Remove-Item -Recurse -Force folder` |
| `export FOO=bar` | `$env:FOO = "bar"` |
| `ls -la` | `Get-ChildItem -Force` |

---

## §1 The story

Before a surgeon operates they lay out instruments. Before a chef cooks they do *mise en place* —
everything chopped, measured, in its own little bowl, within reach.

Ninety days is long enough that friction compounds. If starting a day means remembering where things
go, hunting for the right command, and then hand-editing three markdown files to record that you
finished — you will skip the recording, then skip the tests, then skip the day.

So today you build the *mise en place*:

- **The toolchain** — Python 3.12, `uv`, `git`, and the optional-but-needed-later ones.
- **The skeleton** — every folder, created now, empty and waiting.
- **The tracker** — a ~250-line Python program that reads your day files and updates the index, the
  traceability table, the changelog, and the git commit **for** you. You type
  `./m done 3` and everything is consistent. You never hand-edit a status again.

That last one is the piece people never build, and it is why most 90-day plans die around day 20.

---

## §2 Check what you already have

Run this. It tells you the state of your machine in one shot.

```bash
for t in python uv git make docker ollama; do
  printf "%-8s: " "$t"
  command -v "$t" 2>/dev/null || echo "NOT FOUND"
done
python --version
```

**Line by line:**

- `for t in python uv git make docker ollama; do` — loop over the six tools this project can use.
  `t` holds one name each time round.
- `printf "%-8s: " "$t"` — print the tool name padded to 8 characters so the output lines up.
  `printf` (unlike `echo`) does not add a newline, so the result appears on the same line.
- `command -v "$t" 2>/dev/null` — ask the shell "where is this program?". It prints the path if
  found and exits 0; prints nothing and exits non-zero if not. `2>/dev/null` throws away the error
  message so the output stays clean.
- `|| echo "NOT FOUND"` — `||` means "if the previous command failed, run this one". So a missing
  tool prints `NOT FOUND` instead of a blank line.
- `done` — end of loop.
- `python --version` — confirm the interpreter version. **It must say 3.12.x.**

### What each tool is for, and whether you need it today

| Tool | Needed | Why | First used |
|---|---|---|---|
| **Python 3.12** | ✅ today | The language. 3.12 is the version every framework in this plan supports. | Day 0 |
| **uv** | ✅ today | Installs packages and manages the virtual environment. Much faster than pip and it produces the lockfile that makes Principle 4 real. | Day 0 |
| **git** | ✅ today | Every day ends in a commit (Principle 1). | Day 0 |
| **make** | ❌ never | Not installed on your machine, and this project does **not** use it. The tracker script replaces it. | — |
| **Docker Desktop** | ⏳ by Day 19 | Runs agent-generated code inside a throwaway container with no network (AG-18/OAI-19). | Day 19 |
| **Ollama** | ⏳ optional | A local, keyless model for when all three free tiers are rate-limited. | Day 6 (optional) |

**You do not need Docker or Ollama today.** Install them the weekend before Day 19. They are listed
here so nothing surprises you later.

### If Python is missing or is not 3.12

```bash
winget install --id Python.Python.3.12 -e --source winget
```

- `winget` — Windows' built-in package installer.
- `--id Python.Python.3.12` — the exact package identifier. Using `--id` avoids installing a
  similarly-named package by accident.
- `-e` — "exact": match the id exactly, do not fuzzy-search.
- `--source winget` — use the official winget repository.

Close and reopen Git Bash afterwards so the new `PATH` is picked up, then re-run the check.

### If `uv` is missing

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

- `powershell -c "..."` — run one PowerShell command from Git Bash.
- `-ExecutionPolicy ByPass` — allow the downloaded script to run this once (Windows blocks unsigned
  scripts by default).
- `irm <url>` — `Invoke-RestMethod`: download the installer script as text.
- `| iex` — `Invoke-Expression`: run that text. This is the standard install path published by
  Astral, the makers of `uv`.

Reopen Git Bash, then confirm:

```bash
uv --version
```

---

## §3 Create the skeleton

Every folder, right now, so nothing has to be improvised later.

```bash
cd /c/Users/nisha_gnzw/OneDrive/Desktop/Projects/mandala

mkdir -p src/mandala
mkdir -p tests/fixtures/cassettes
mkdir -p scripts
mkdir -p docs/adr
mkdir -p .github/workflows
```

**Line by line:**

- `mkdir -p src/mandala` — create the package folder. `-p` means "create parent folders as needed,
  and do not complain if it already exists". That second half is why every command in these docs
  is safe to run twice.
- `mkdir -p tests/fixtures/cassettes` — `fixtures/` holds your invented tickets;
  `cassettes/` holds recorded API responses so tests replay for free (built on Day 2).
- `mkdir -p scripts` — home of the tracker you write in §5.
- `mkdir -p docs/adr` — architecture decision records. ADR-001 arrives on Day 16.
- `mkdir -p .github/workflows` — GitHub Actions CI, wired on Day 2.

Now the files that must exist for Python to treat `src/mandala` as a package:

```bash
touch src/mandala/__init__.py
touch tests/__init__.py
```

- `touch <file>` — create an empty file if it does not exist; if it does exist, just update its
  timestamp and leave the contents alone. Safe to re-run.
- `src/mandala/__init__.py` — its presence is what makes `import mandala` work. Empty is correct.

Check it:

```bash
find . -type d -not -path './.git*' | sort
```

- `find .` — walk the current directory tree.
- `-type d` — only directories.
- `-not -path './.git*'` — skip git's internals, which are noisy and not yours.
- `| sort` — alphabetical, so it reads like a diagram.

Expected:

```
.
./.github
./.github/workflows
./days
./days/day-00-setup
./days/day-01
...
./docs
./docs/adr
./scripts
./src
./src/mandala
./tests
./tests/fixtures
./tests/fixtures/cassettes
```

---

## §4 The project file — `pyproject.toml`

This one file tells `uv` the Python version, the dependencies, and how to find your package. Create
it with a **heredoc**, which is the safe way to write a multi-line file from the shell.

```bash
cat > pyproject.toml <<'EOF'
[project]
name = "mandala"
version = "0.1.0"
description = "Project Mandala — a 90-day multi-agent curriculum, built on free tiers only"
requires-python = "==3.12.*"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mandala"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
markers = [
    "live: hits a real provider; costs free-tier quota; excluded from the default run",
    "cassette: replays a recorded response; free and offline",
]
EOF
```

**What the heredoc syntax means:**

- `cat > pyproject.toml` — `cat` copies its input to its output; `>` redirects that output into the
  file, replacing whatever was there.
- `<<'EOF'` — "read the following lines as input until you see a line that is exactly `EOF`".
  The **quotes around `EOF` matter**: they tell the shell *not* to interpret `$`, backticks or
  backslashes inside. Without the quotes, a `$` in your file would be eaten as a variable.

**The file, line by line:**

- `[project]` — the standard Python project metadata block (PEP 621). Every modern tool reads it.
- `name = "mandala"` — the importable/installable name of your package.
- `version = "0.1.0"` — required by the standard; you will not bump it much.
- `requires-python = "==3.12.*"` — **a hard pin to the 3.12 series**. Not `>=3.12`. This is
  Principle 4 (pin everything) applied to the interpreter itself. `crewai` currently refuses
  Python ≥3.14 and `openai-agents` refuses <3.10, so 3.12 is the safe intersection across all four
  frameworks — and pinning it means a future `uv` cannot silently pick 3.13 for you.
- `dependencies = []` — **empty on purpose.** You add each package on the day you first need it,
  with its exact version, so you always know why a dependency is present.
- `[build-system]` … `hatchling` — the machinery that turns your `src/` folder into an installable
  package. You never interact with it directly; `uv` needs it to exist.
- `packages = ["src/mandala"]` — tells the build backend that the code lives under `src/`, not at
  the repository root. This is the "src layout", and it prevents the classic bug where your tests
  accidentally import the folder next to them instead of the installed package.
- `[tool.ruff]` — settings for the linter/formatter.
- `line-length = 100` — a little wider than the 88 default, because agent code has long strings.
- `target-version = "py312"` — lint for 3.12 syntax; lets ruff suggest modern constructs.
- `select = ["E", "F", "I", "UP", "B"]` — which rule families are on:
  - `E` = pycodestyle errors (spacing, indentation),
  - `F` = pyflakes (unused imports, undefined names — the ones that are real bugs),
  - `I` = import sorting,
  - `UP` = pyupgrade (rewrite old syntax to modern),
  - `B` = flake8-bugbear (likely-wrong patterns, e.g. mutable default arguments).
- `[tool.pytest.ini_options]` — pytest settings.
- `testpaths = ["tests"]` — only look in `tests/`, so pytest does not crawl `days/`.
- `addopts = "-q"` — quiet output by default.
- `markers = [...]` — **declares the two custom markers up front.** Declaring them here means
  pytest will *error* on a typo like `@pytest.mark.livee` instead of silently ignoring it.

Now create the environment and install the project itself:

```bash
uv venv --python 3.12
uv pip install -e .
```

- `uv venv --python 3.12` — create a virtual environment in `.venv/` using Python 3.12. A virtual
  environment is a private copy of Python for this project, so installs here cannot break anything
  else on your machine.
- `uv pip install -e .` — install the current directory (`.`) in **editable** mode (`-e`). Editable
  means Python imports your code *from `src/`* rather than from a copy, so edits take effect
  immediately with no reinstall.

Verify:

```bash
uv run python -c "import mandala; print('mandala imports OK')"
```

- `uv run <cmd>` — run a command inside the project's virtual environment. **Use `uv run` for
  everything in these 90 days**; it means you never have to remember to "activate" anything.
- `python -c "..."` — run the given Python source directly instead of a file.

---

## §5 The tracker — `scripts/mandala.py`

This is the program that keeps `docs/CURRICULUM_INDEX.md`, `docs/TRACEABILITY.md`,
`docs/CHANGELOG_PLAN.md` and every `LESSON.md` frontmatter block in sync, and makes the commit.

**Full source and a line-by-line walkthrough are in [`TRACKER.md`](TRACKER.md)** in this same folder.
It is ~250 lines of plain-stdlib Python, split into eight explained chunks. Go and build it now —
it is the tool you will use every single day — then come back here for §6.

When you finish, this must work:

```bash
uv run python scripts/mandala.py status
```

---

## §6 The `./m` shortcut

Typing `uv run python scripts/mandala.py` ninety times is a tax. Make a two-line wrapper.

```bash
cat > m <<'EOF'
#!/usr/bin/env bash
exec uv run python "$(dirname "$0")/scripts/mandala.py" "$@"
EOF
chmod +x m
```

**Line by line:**

- `#!/usr/bin/env bash` — the "shebang". It tells the operating system which program should
  interpret this file. `/usr/bin/env bash` finds bash wherever it happens to live rather than
  hardcoding a path.
- `exec` — replace this shell process with the command that follows, instead of starting a child and
  waiting. Slightly cheaper, and it means Ctrl-C behaves properly.
- `uv run python ...` — run the tracker inside the project environment.
- `"$(dirname "$0")/scripts/mandala.py"` — `$0` is the path this script was invoked as; `dirname`
  strips the filename off it, leaving the folder. So the wrapper finds the tracker relative to
  itself, and works no matter which directory you call it from.
- `"$@"` — pass along every argument you typed, each one properly quoted. (`$*` would mash them into
  one string and break arguments containing spaces — always use `"$@"`.)
- `chmod +x m` — mark the file executable, so `./m` runs it instead of the shell saying
  "permission denied".

Now every command in every day-doc is short:

```bash
./m status              # progress dashboard
./m start 1             # begin Day 1
./m check               # lint + tests, offline and free
./m done 1              # verify, commit, and update every tracker file
```

> **PowerShell users:** `./m` is a bash script. In PowerShell, either run `bash ./m status`, or
> just type the long form `uv run python scripts/mandala.py status`. In Git Bash, `./m` works.

---

## §7 Git, if this is not a repo yet

Your project **is** already a git repository (there is a `.git` folder). If you were starting fresh:

```bash
git init
git branch -M main
```

- `git init` — create the repository.
- `git branch -M main` — rename the current branch to `main`. `-M` forces the rename even if the
  branch already exists.

Set your identity if it is not already set — every commit for 90 days carries it:

```bash
git config user.name  "Your Name"
git config user.email "you@example.com"
```

And create the ignore file **before** you ever create a `.env`. This ordering is the entire trick
for never leaking an API key:

```bash
cat > .gitignore <<'EOF'
# secrets — this line must exist before .env does
.env

# python
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/

# project artifacts
*.sqlite
*.sqlite3
.langgraph_api/
EOF
```

**Line by line:**

- `.env` — your real API keys. **Never** committed. First line, because it is the one that matters.
- `.venv/` — the virtual environment. Hundreds of megabytes, machine-specific, always regenerable.
- `__pycache__/`, `*.pyc` — Python's compiled bytecode caches.
- `.pytest_cache/`, `.ruff_cache/` — tool caches.
- `*.sqlite`, `*.sqlite3` — from Day 11 onward your agents store sessions and checkpoints in SQLite.
  Those are run artifacts, not source.
- `.langgraph_api/` — created by `langgraph dev` on Day 86.

Commit the skeleton:

```bash
git add -A
git commit -m "day-00: setup — toolchain, skeleton, tracker"
```

- `git add -A` — stage every change (new, modified, deleted) across the whole repo.
- `git commit -m "..."` — record the snapshot with that message.

---

## §8 Verify the whole thing

Run these four. All four must succeed before you start Day 1.

```bash
python --version                                          # 3.12.x
uv run python -c "import mandala; print('import OK')"     # import OK
./m status                                                # the dashboard
git log --oneline -1                                      # your setup commit
```

Expected dashboard:

```
  Project Mandala — 0/90 days
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0%
  IDs covered: 0/138
  ⬜ next up:     Day 1 — Foundry I — the repo, the pins, and the three free keys
                 IDs: infrastructure
                 ./m start 1
```

---

## §9 Traps

- **Running commands in PowerShell that were written for Git Bash.** `mkdir -p` fails, `touch` does
  not exist, `2>/dev/null` is wrong. Use Git Bash, or use the translation table in §0.
- **Forgetting `uv run`.** Without it you get the *system* Python, which does not have your
  packages, and you get a confusing `ModuleNotFoundError`.
- **Creating `.env` before `.gitignore`.** Do it in the order given. A key in git history outlives
  the commit that deleted it.
- **Installing Python 3.13.** Everything here is pinned to 3.12 for a reason (§4).
- **Skipping `TRACKER.md` because it looks long.** It is the tool that removes bookkeeping from the
  next 90 days. Twenty minutes now saves an hour a week.
- **Installing Docker today.** You do not need it until Day 19. Do not add setup friction to Day 0.

---

## §10 Done when

See `CHECKLIST.md` in this folder. Then: `./m start 1`.
