# Day 0 — CHECKLIST

**IDs covered:** none (toolchain) · **Principles served:** 1, 4, 5, 6, 15, 16, 17

Not one of the ninety days. This is the day the workshop gets built.
`./m done 0` refuses to commit until every box below is ticked.

## Demo command

```bash
./m check && ./m status && git log --oneline -1
```

Expected: `OK all green`, a progress line reading `1/91 days in the v2.0.0 shape (17 sub-topic
docs)`, and one commit reading `day-00: complete`.

---

## Section 1 — the toolchain

- [ ] Read [1.1 — Why one tool must own the environment](parts/01/1.1-why-one-tool-must-own-the-environment.md), ran its check-yourself, answered its question out loud
- [ ] Read [1.2 — Git, Git Bash, and the carriage return](parts/01/1.2-git-bash-and-the-carriage-return.md), ran its check-yourself, answered its question out loud
- [ ] Read [1.3 — `uv`, the one binary](parts/01/1.3-uv-the-one-binary-that-owns-the-environment.md), ran its check-yourself, answered its question out loud
- [ ] Read [1.4 — Python 3.12](parts/01/1.4-python-3-12-and-why-nothing-floats.md), ran its check-yourself, answered its question out loud
- [ ] Read [1.5 — The editor and the interpreter it picks](parts/01/1.5-the-editor-and-the-interpreter-it-picks.md), ran its check-yourself, answered its question out loud
- [ ] Read [1.6 — Docker and Ollama](parts/01/1.6-docker-and-ollama-before-you-need-them.md), ran its check-yourself, answered its question out loud

**Installed and verified:**

- [ ] Git installed; **Git Bash** opens from the Start menu and `uname -s` prints `MINGW64`
- [ ] `git config --global user.name` / `user.email` / `init.defaultBranch` / `core.autocrlf` all set
- [ ] `core.autocrlf` prints exactly `input`
- [ ] `uv --version` works **after reopening the shell**
- [ ] `uv python list --only-installed` shows a `cpython-3.12.x` entry
- [ ] Editor installed with the Python and Ruff extensions; its status bar shows this project's `.venv`
- [ ] Docker Desktop installed, restarted, and `docker run --rm hello-world` prints its paragraph
- [ ] `docker run --rm --network none python:3.12-slim python -c "print('isolated')"` succeeds
- [ ] Ollama installed and `ollama run llama3.2:3b "Reply with exactly one word: ready"` answers
- [ ] Noted that Docker is first needed on **Day 19** and Ollama on **Day 6**

## Section 2 — the repository

- [ ] Read [2.1 — The folder skeleton](parts/02/2.1-the-folder-skeleton.md), ran its check-yourself, answered its question out loud
- [ ] Read [2.2 — `.gitignore` before the secret exists](parts/02/2.2-gitignore-before-the-secret-exists.md), ran its check-yourself, answered its question out loud
- [ ] Read [2.3 — `git init`](parts/02/2.3-git-init-and-what-a-repo-is.md), ran its check-yourself, answered its question out loud
- [ ] Read [2.4 — `uv init`, `pyproject.toml`, and the lockfile](parts/02/2.4-uv-init-pyproject-and-the-lockfile.md), ran its check-yourself, answered its question out loud
- [ ] Read [2.5 — The `.venv` you never activate](parts/02/2.5-the-venv-you-never-activate.md), ran its check-yourself, answered its question out loud

**Built and verified:**

- [ ] Folders exist: `src/mandala/`, `tests/fixtures/cassettes/`, `days/`, `docs/adr/`, `scripts/`, `.github/workflows/`
- [ ] `src/mandala/__init__.py` and `tests/__init__.py` exist (empty is correct)
- [ ] **`.gitignore` was written *before* `.env` could exist**, and contains a line that is exactly `.env`
- [ ] `git check-ignore -v .env` names the rule that matches it
- [ ] `git check-ignore -v .env.example` finds **nothing** — the example file is committed
- [ ] `.env.example` exists, contains key **names with no values**, and is tracked by git
- [ ] `.gitattributes` exists and covers `m`, `*.sh`, `*.py`, `*.md` with `eol=lf`
- [ ] `git init` run, and `git rev-parse --is-inside-work-tree` prints `true`
- [ ] `pyproject.toml` has `requires-python = "==3.12.*"` and every dependency uses `==`
- [ ] `uv.lock` exists, is tracked, and lists more packages than `pyproject.toml` declares
- [ ] `uv sync --frozen` succeeds (manifest and lockfile agree)
- [ ] `uv run python -c "import mandala; print(mandala.__file__)"` resolves to a path under `src/`
- [ ] `echo "VIRTUAL_ENV=${VIRTUAL_ENV:-<not set>}"` prints `<not set>` — the shell is clean

## Section 3 — the driver

- [ ] Read [3.1 — `set -euo pipefail`](parts/03/3.1-set-euo-pipefail.md), ran its check-yourself, answered its question out loud
- [ ] Read [3.2 — The `case` dispatcher](parts/03/3.2-the-case-dispatcher.md), ran its check-yourself, answered its question out loud
- [ ] Read [3.3 — The `done` gate](parts/03/3.3-the-done-gate.md), ran its check-yourself, answered its question out loud

**Built and verified:**

- [ ] `chmod +x m` applied, and `./m` with no arguments prints the usage text
- [ ] `./m chekc` (a deliberate typo) also prints usage — the catch-all works
- [ ] Ran the `set -e` / `set -u` / `pipefail` demos from 3.1 and **saw each one change the exit status**
- [ ] `head -3 m` shows the shebang, the comment, and `set -euo pipefail`
- [ ] `./m check` prints `OK all green`
- [ ] Can say **out loud** what makes `./m done` refuse, and what it does when the checklist file is missing

## Section 4 — the three machines

- [ ] Read [4.1 — The depth check](parts/04/4.1-the-depth-check.md), ran its check-yourself, answered its question out loud
- [ ] Read [4.2 — The tracker you never hand-edit](parts/04/4.2-the-tracker-you-never-hand-edit.md), ran its check-yourself, answered its question out loud
- [ ] Read [4.3 — The first commit](parts/04/4.3-the-first-commit.md), ran its check-yourself, answered its question out loud

**Built and verified:**

- [ ] `./m depth 0` reports `OK   day   0  17 parts`
- [ ] Deleted a section from a **copy** of a part in `/tmp` and watched `depth_check.py` refuse it
- [ ] `./m tracker` regenerates `docs/TRACKER.md`, and `grep -c "^| [0-9]" docs/TRACKER.md` prints `91`
- [ ] Understand why `docs/CURRICULUM_INDEX.md` has **no** status column

## The eval (Principle 7)

- [ ] `tests/test_repo_shape.py` created, with all three `TODO(me)` assertions written by me
- [ ] `uv run pytest tests/test_repo_shape.py -v` — all three pass
- [ ] **Broke it and watched it go red:** `git add -f .env` made `test_env_is_not_tracked` **fail**, then `git reset .env` restored green
- [ ] **Broke it and watched it go red:** renaming `src/mandala/__init__.py` made `test_package_is_importable` **fail**, then restored
- [ ] **Broke it and watched it go red:** removing line 3 of `m` made `test_driver_has_strict_mode` **fail**, then restored

## Request budget (Principle 5)

- [ ] Model API calls made today: **0** — confirmed, because no key exists yet
- [ ] Free-tier quota spent: **0**

## Commit (Principle 1)

- [ ] `git status --short` reviewed line by line before staging
- [ ] `git ls-files | grep -E "^\.env$"` returns **nothing**
- [ ] `./m done 0` committed successfully
- [ ] `git status --porcelain` prints **nothing** afterwards

## Understanding check — answer out loud

- [ ] Why does this project never type bare `pip install`?
- [ ] Why was `.gitignore` written before `git init` rather than after?
- [ ] Which file is *intent* and which is *outcome* — `pyproject.toml` or `uv.lock` — and what breaks if you commit only one?
- [ ] What does `set -euo pipefail` protect you from that plain `set -e` does not?
- [ ] Why does `./m check` pass `-m "not live"` to pytest, and what does that protect that has nothing to do with correctness?
- [ ] Name two things `depth_check.py` can verify and two it cannot. Why does stating the boundary matter?
- [ ] Why is `docs/TRACKER.md` generated rather than maintained?
