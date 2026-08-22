---
day: 0
phase: 0
phase_name: "Foundry"
title: "Setup — the toolchain, the skeleton, and the driver"
ids: []
principles: [1, 4, 5, 6, 15, 16, 17]
kind: setup
plan_version: "v2.0.0"
parts: 17
generated: "2026-08-22"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 0 — Setup: the toolchain, the skeleton, and the driver

**Before Phase 0.** This is not one of the ninety days. It is the day the workshop gets built, so
that Day 1 starts on a machine where nothing is ambiguous.

> **Yesterday:** nothing — this is where the project begins.
> **Today:** install the tools, create every folder and file the project needs, build the driver
> that will gate the next ninety days, and make the first commit.
> **Tomorrow:** Day 1 — re-verify every pin against live PyPI, create the three free API keys, and
> record today's real rate limits.

---

## §1 The story

Before a surgeon operates, the instruments are laid out. Before a chef cooks, everything is chopped
and measured and within reach — *mise en place*, "everything in its place". Neither of them is being
fussy. Both know that the moment you need something is the worst possible moment to go looking for
it.

Ninety days is long enough that friction compounds. If starting a day means remembering where things
go, hunting for the right command, and then hand-editing three files to record that you finished,
you will skip the recording. Then you will skip the tests. Then you will skip the day.

There is a second, quieter reason this day exists. Almost every mysterious failure a beginner meets
in Python is not a Python problem at all — it is an *ambiguity* problem. Two interpreters on one
machine, so the package you installed is invisible to the code you ran. Two line-ending conventions,
so a script that plainly exists reports that it cannot be found. Two environments, so your test
passes locally and fails in CI. None of those are hard once you can name them. All of them cost an
afternoon the first time, and they arrive on the evening you were trying to learn something else.

So today you remove the ambiguity while there is nothing at stake. One tool owns the environment.
One file says which Python. One folder holds secrets and is invisible to git *before* any secret
exists. One script runs every check and refuses to commit a day you have not finished.

By the end you will have typed a lot and learned a machine, not a framework. That is deliberate. The
agents start on Day 3, and they will be hard enough without your toolchain arguing with you.

---

## §2 The map

Four sections. Each one is a different kind of ownership: **section 1** is who owns your machine's
environment, **section 2** is who owns the project's shape, **section 3** is who runs the daily
loop, and **section 4** is what keeps ninety days honest when you are tired.

Read the parts in order. Each one is standalone, but they build.

### Section 1 — The toolchain: who owns the environment

| Part | Answers | Level |
|---|---|---|
| [1.1 — Why one tool must own the environment](parts/01/1.1-why-one-tool-must-own-the-environment.md) | Why does `pip install` succeed and `import` still fail? | `foundation` |
| [1.2 — Git, Git Bash, and the carriage return that breaks your scripts](parts/01/1.2-git-bash-and-the-carriage-return.md) | Why does a script whose interpreter obviously exists say it does not? | `foundation` |
| [1.3 — `uv`, the one binary that owns the environment](parts/01/1.3-uv-the-one-binary-that-owns-the-environment.md) | What four jobs stop being four tools? | `working` |
| [1.4 — Python 3.12, and why nothing in this project floats](parts/01/1.4-python-3-12-and-why-nothing-floats.md) | Why is the newest Python the worst one to start on? | `working` |
| [1.5 — The editor, and the interpreter it silently picks](parts/01/1.5-the-editor-and-the-interpreter-it-picks.md) | Why does your editor disagree with your terminal? | `working` |
| [1.6 — Docker and Ollama, the two tools you meet before you need them](parts/01/1.6-docker-and-ollama-before-you-need-them.md) | What must already be installed on the day it matters? | `foundation` |

### Section 2 — The repository, built in the right order

| Part | Answers | Level |
|---|---|---|
| [2.1 — The folder skeleton, and what earns a folder](parts/02/2.1-the-folder-skeleton.md) | What rule does each folder promise about its contents? | `foundation` |
| [2.2 — `.gitignore` before the secret exists](parts/02/2.2-gitignore-before-the-secret-exists.md) | Why is the ignore rule written before there is anything to ignore? | `production` |
| [2.3 — `git init`, and what a repository actually is](parts/02/2.3-git-init-and-what-a-repo-is.md) | What is actually inside `.git/`, and why does that make history tamper-evident? | `working` |
| [2.4 — `uv init`, `pyproject.toml`, and the lockfile](parts/02/2.4-uv-init-pyproject-and-the-lockfile.md) | Which file is intent and which is outcome? | `production` |
| [2.5 — The `.venv` you never activate](parts/02/2.5-the-venv-you-never-activate.md) | Why does this project refuse a convenience everyone else uses? | `working` |

### Section 3 — `./m`, the driver you will run a thousand times

| Part | Answers | Level |
|---|---|---|
| [3.1 — `set -euo pipefail`, the four options that make bash safe](parts/03/3.1-set-euo-pipefail.md) | How does a script report success after failing? | `production` |
| [3.2 — The `case` dispatcher, and why `./m` has one](parts/03/3.2-the-case-dispatcher.md) | Where should the correct command live so it cannot go stale? | `working` |
| [3.3 — The `done` gate that refuses to commit](parts/03/3.3-the-done-gate.md) | What is the difference between a check and a gate? | `production` |

### Section 4 — The three machines that make ninety days self-enforcing

| Part | Answers | Level |
|---|---|---|
| [4.1 — The depth check, and turning a writing standard into an exit code](parts/04/4.1-the-depth-check.md) | How do you stop a standard decaying when nobody is watching? | `production` |
| [4.2 — The tracker you never hand-edit](parts/04/4.2-the-tracker-you-never-hand-edit.md) | Why is progress derived rather than recorded? | `working` |
| [4.3 — The first commit, and the habit it installs](parts/04/4.3-the-first-commit.md) | Why is a commit the definition of a finished day? | `production` |

---

## §3 Setup — run this

Open **Git Bash** (Start → type `Git Bash`) and move into your projects folder. Everything below is
POSIX shell; the PowerShell translations are in [`../README.md`](../README.md).

**Install the tools** — the details, and what each flag means, are in section 1:

```bash
# Git, from https://git-scm.com/download/win
#   -> "Checkout as-is, commit Unix-style line endings"   (part 1.2)
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main
git config --global core.autocrlf input

# uv, the one binary that owns the environment              (part 1.3)
curl -LsSf https://astral.sh/uv/install.sh | sh
#   -> close Git Bash and reopen it, so PATH is re-read

uv python install 3.12                                    # part 1.4
```

**Install the two tools you will not use today** — both are large downloads and Docker needs a
restart, which is the entire reason they are installed now (part 1.6):

```bash
# Docker Desktop, from https://www.docker.com/products/docker-desktop/   -> needed Day 19, Day 67
# Ollama,         from https://ollama.com/download                        -> needed Day 6
ollama pull llama3.2:3b
```

**Create the skeleton** — order matters, and part 2.2 explains why `.gitignore` comes before
`git init`:

```bash
mkdir -p src/mandala tests/fixtures/cassettes days docs/adr scripts .github/workflows .vscode
touch src/mandala/__init__.py tests/__init__.py
# write .gitignore and .env.example                        (part 2.2)
# then, and only then:
git init                                                  # part 2.3
```

**Create the environment and prove it:**

```bash
uv sync                                                   # part 2.5
uv run python -c "import sys; print(sys.executable)"
uv run python -c "import mandala; print('package imports')"
```

**Make the driver runnable:**

```bash
chmod +x m                                                # part 3.2
./m
```

No packages are installed today beyond what `pyproject.toml` already pins. Day 1 adds the first
ones, on the day they are first used.

---

## §4 Build brief

Everything in this list already exists in the repository — **your job today is to read each file,
understand why every line is there, and re-derive the three marked `TODO(me)`.** Reading a file you
did not write is not the same as being able to write it, and Day 1 assumes you can.

| File | What it is | Part |
|---|---|---|
| `.gitignore` | secrets and regenerable files, excluded before they exist | 2.2 |
| `.env.example` | the names of every key, with no values, committed | 2.2 |
| `.gitattributes` | forces LF on `m`, `*.sh`, `*.py`, `*.md` | 1.2 |
| `pyproject.toml` | `requires-python`, pinned deps, ruff and pytest config | 1.4, 2.4 |
| `uv.lock` | the resolved tree with hashes — committed | 2.4 |
| `.vscode/settings.json` | points the editor at `.venv`; disables Markdown formatting | 1.5 |
| `m` | the dispatcher: `status`, `start`, `parts`, `depth`, `check`, `done` | 3.1, 3.2, 3.3 |
| `scripts/depth_check.py` | enforces the plan's Part 11 contract | 4.1 |
| `scripts/tracker.py` | regenerates `docs/TRACKER.md` from the index plus disk | 4.2 |

**Your three reps.** Create `tests/test_repo_shape.py` and write these yourself. They are the eval
for §5, and they must be able to go red:

```python
# tests/test_repo_shape.py
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_env_is_not_tracked() -> None:
    """.env must never appear in git's index (part 2.2)."""
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    # TODO(me): assert that no tracked path is exactly ".env"
    #           Hint: `.env.example` IS tracked and must still pass.
    raise NotImplementedError


def test_package_is_importable() -> None:
    """The src layout must actually be installed, not merely present (part 2.1)."""
    # TODO(me): import mandala and assert its __file__ lives under src/
    raise NotImplementedError


def test_driver_has_strict_mode() -> None:
    """./m must open with set -euo pipefail (part 3.1)."""
    # TODO(me): read the first few lines of ROOT / "m" and assert the option line is present
    raise NotImplementedError
```

Do not delete the `raise NotImplementedError` lines until you have written the assertion above them.
A test that passes before you implement it has taught you nothing.

---

## §5 The eval that must be able to fail

```bash
uv run pytest tests/test_repo_shape.py -v
```

Before you write the assertions, all three tests **fail** with `NotImplementedError`. That is the
red you need. After you write them, all three pass.

Then — and this is the box people skip — **prove each one can still go red**:

```bash
git add -f .env && uv run pytest tests/test_repo_shape.py::test_env_is_not_tracked
git reset .env
```

`-f` forces git to stage an ignored file. The test must **fail**. If it passes, your assertion is
not testing what you think, and you have a green test that cannot go red — which Principle 7 calls
decoration. `git reset .env` unstages it again.

Do the equivalent for the other two: temporarily rename `src/mandala/__init__.py`, and temporarily
comment out line 3 of `m`. Watch each test fail, then put it back.

---

## §6 Request budget

| Item | Count |
|---|---|
| Model API calls | **0** |
| Free-tier quota spent | **0** |
| Network use | tool downloads only — Git, uv, Python 3.12, Docker Desktop, one Ollama model |
| Cost | **$0** |

Today spends no quota at all, because there are no keys yet — Day 1 creates them. The Ollama pull is
a one-time local download and is free forever after. State the budget on every day, including the
days where the answer is zero; a budget you only state when it is large is a budget you are not
really tracking (Principle 5).

---

## §7 Traps

- **Installing `uv` and then typing `uv --version` in the same shell.** The installer edits your
  shell's startup file, and a running shell does not re-read it. Close it, reopen it. This is not a
  failed install (part 1.3).
- **Writing `.gitignore` after creating `.env`.** `.gitignore` has no effect on files git already
  tracks. Write the rule first. On Day 1 this stops being recoverable by tidiness and becomes a key
  rotation (part 2.2).
- **`.env*` instead of explicit lines.** It also ignores `.env.example`, which you want committed —
  and nobody notices until a new clone has no idea what variables to set (part 2.2).
- **Editing `pyproject.toml` by hand to add a package.** The lockfile then disagrees, and
  `uv sync --frozen` refuses. Use `uv add "name==version"`, which updates both (part 2.4).
- **Letting your editor format Markdown.** It will reformat the Python inside these lessons, which
  is written to be read rather than to satisfy a formatter. `pyproject.toml` protects the command
  line; only the editor setting protects the editor (part 1.5).
- **`./m` failing with `bad interpreter: /usr/bin/env^M`.** Windows line endings on the shebang.
  `.gitattributes` and `core.autocrlf input` prevent it; `sed -i 's/\r$//' m` repairs it (part 1.2).
- **This repository lives in a OneDrive folder**, which refuses hardlinks, so `uv` is configured
  with `link-mode = "copy"`. If you move the project, the setting is harmless; if you clone it
  somewhere unsynced, you can delete it for a speed-up (part 1.3).
- **Ticking a checklist box you did not earn.** The gate cannot detect it, which is exactly why it
  is worth not doing (part 3.3).

---

## §8 Verify before you code

Everything here was verified on **2026-08-22**. Tool installers change; check the live page rather
than trusting a command from a document (Principle 13, run daily instead of weekly):

- uv — installation and `uv add` / `uv sync` / `uv run`: <https://docs.astral.sh/uv/>
- uv — `[tool.uv]` settings, including `link-mode`: <https://docs.astral.sh/uv/reference/settings/>
- Python 3.12 release notes: <https://docs.python.org/3/whatsnew/3.12.html>
- `pyproject.toml` `[project]` specification: <https://packaging.python.org/en/latest/specifications/pyproject-toml/>
- Git — `gitignore` patterns: <https://git-scm.com/docs/gitignore>
- Git — `gitattributes` and `eol`: <https://git-scm.com/docs/gitattributes>
- ruff — rules and configuration: <https://docs.astral.sh/ruff/>
- pytest — exit codes (why 5 means "no tests collected"): <https://docs.pytest.org/en/stable/reference/exit-codes.html>
- Docker — `docker run` reference, including `--network`: <https://docs.docker.com/reference/cli/docker/container/run/>
- Ollama — models and `ollama pull`: <https://ollama.com/library>

---

## §9 Say it in an interview

> "Before writing any application code I make the environment unambiguous, because most of the
> baffling failures early in a project are ambiguity rather than logic — two interpreters, two line
> ending conventions, two copies of a package. So one tool owns the environment and the interpreter
> version is declared in a file; dependencies are pinned exactly and the resolved tree is locked
> with hashes and committed, so intent and outcome are both recorded; secrets are excluded before
> they exist, because git history is append-only and a committed key means rotation rather than
> deletion. Then I put the project's commands in one script in the repository, so the correct
> incantation is versioned with the code it runs and CI executes the identical command. The last
> piece is a gate: it refuses to commit while the definition of done is unmet, and it fails closed
> if it cannot determine the answer. None of that is ceremony — it is what makes a green test
> trustworthy, and an untrustworthy green test is worse than a red one because you believe it."

---

## §10 Done when

Every box in [`CHECKLIST.md`](CHECKLIST.md) is ticked and `./m done 0` commits without complaint.

Not when a duration has elapsed, and not when you have skimmed all seventeen parts. A day is a unit
of subject, not a unit of time (Principle 16) — this one may take several sittings, and taking
several is the day being done properly.

The gate you are about to run is the one you built in
[3.3](parts/03/3.3-the-done-gate.md). Running it on the day that created it is the point.

```bash
./m check
./m done 0
```
