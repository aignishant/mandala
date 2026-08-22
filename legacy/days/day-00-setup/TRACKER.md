# The tracker — `scripts/mandala.py`, explained line by line

> Part of **Day 0 — Setup**. Read [`LESSON.md`](LESSON.md) §1–§4 first.

This is the one piece of infrastructure that is not part of the curriculum but is essential to
finishing it. It replaces four kinds of manual bookkeeping:

| Manual chore it removes | File it edits for you |
|---|---|
| "mark Day 7 as done" | `days/day-07/LESSON.md` frontmatter |
| "update the status column" | `docs/CURRICULUM_INDEX.md` |
| "tick off AG-09 and AG-12" | `docs/TRACEABILITY.md` |
| "log the completed day" | `docs/CHANGELOG_PLAN.md` |
| "commit with the right message" | git |

It also replaces `make` entirely, which matters because `make` is not installed on Windows by
default and this project does not need it.

**Design constraints, and why each one:**

- **Standard library only.** No `pyyaml`, no `click`, no dependencies at all. This script has to run
  on Day 0, *before* you have installed anything, and it must never break because a dependency
  moved.
- **Idempotent.** Every command is safe to run twice. Nothing appends a duplicate line, nothing
  double-commits.
- **Never talks to a network or a model.** It costs zero free-tier quota, forever.
- **`sync` is the rebuild button.** The day-file frontmatter is the single source of truth; the
  index and the traceability table are *derived*. If they ever look wrong, `./m sync` regenerates
  them from the frontmatter.

Read the eight chunks below, then paste the assembled file from §9 at the bottom.

---

## Chunk 1 — the header and the imports

```python
#!/usr/bin/env python3
"""
mandala.py — the tracking automation and task runner for the 90-day plan.

    ./m status          progress dashboard
    ./m start 3         mark Day 3 in-progress
    ./m check           lint + offline tests (no network, no quota)
    ./m done 3          verify -> commit -> update every tracker file
    ./m sync            rebuild index + traceability from day frontmatter
    ./m check-ids       verify lessons and TRACEABILITY.md agree

Standard library only. Never touches a network or a model.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path
```

**Line by line:**

- `#!/usr/bin/env python3` — the shebang. Lets the file be run directly on Unix-like systems. Your
  `./m` wrapper calls it through `uv run python` anyway, so this is belt-and-braces.
- `"""..."""` — the module docstring. `argparse` will print it when you run `./m --help`, so the
  usage summary lives in exactly one place.
- `from __future__ import annotations` — makes Python treat all type hints as strings rather than
  evaluating them at import time. It means you can write `dict[str, str]` and `list[tuple[...]]`
  without worrying about version details, and it speeds up import slightly.
- `import argparse` — the standard library's command-line parser. It gives you subcommands,
  `--flags`, and a generated `--help` for free.
- `import datetime as dt` — for stamping today's date into the changelog. Aliased to `dt` because
  `datetime.datetime.today()` is a mouthful.
- `import re` — regular expressions. Used to find the frontmatter block and to locate table rows in
  the markdown files.
- `import subprocess` — for running `git` and `ruff`/`pytest` as external programs.
- `import sys` — used for `sys.stdout` (encoding fix, next chunk) and `sys.exit`.
- `from pathlib import Path` — the modern way to handle file paths. `Path` objects work identically
  on Windows and Linux, so `ROOT / "docs"` produces the right separator automatically. Never build
  paths with string concatenation.

---

## Chunk 2 — the encoding fix and the constants

```python
# Windows consoles default to the cp1252 encoding and crash on the emoji and
# box-drawing characters this script prints. Force UTF-8 so `./m status` looks
# the same in Git Bash, PowerShell and CI.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # a redirected or wrapped stream
        pass

ROOT = Path(__file__).resolve().parent.parent
DAYS = ROOT / "days"
DOCS = ROOT / "docs"
INDEX = DOCS / "CURRICULUM_INDEX.md"
TRACE = DOCS / "TRACEABILITY.md"
CHANGELOG = DOCS / "CHANGELOG_PLAN.md"

STATUS_EMOJI = {"not-started": "⬜", "in-progress": "🟨", "done": "✅"}
VALID_STATUS = tuple(STATUS_EMOJI)
```

**Line by line:**

- `for _stream in (sys.stdout, sys.stderr):` — loop over the two output streams. The leading
  underscore in `_stream` is a convention meaning "internal, not part of this module's API".
- `_stream.reconfigure(encoding="utf-8", errors="replace")` — change the stream's encoding after it
  has already been created. Without this, printing `⬜` on Windows raises
  `UnicodeEncodeError: 'charmap' codec can't encode character`. `errors="replace"` says: if some
  character still cannot be encoded, print `?` rather than crashing.
- `except (AttributeError, ValueError): pass` — if the output has been redirected into something
  that does not support `reconfigure` (a pipe wrapper, a test harness), do nothing and carry on.
  Never let a cosmetic fix break the program.
- `ROOT = Path(__file__).resolve().parent.parent` — work out the project root from the script's own
  location. `__file__` is this file's path; `.resolve()` makes it absolute and follows symlinks;
  `.parent` is `scripts/`; `.parent.parent` is the repo root. **This is why the script works no
  matter which folder you run it from.**
- `DAYS = ROOT / "days"` — the `/` operator on `Path` joins path parts using the correct separator
  for the operating system.
- `INDEX`, `TRACE`, `CHANGELOG` — the three derived documents. Naming them once at the top means a
  rename later is a one-line change.
- `STATUS_EMOJI = {...}` — the mapping from a status word to the symbol shown in the index table.
  Having it as data (not scattered `if` statements) is what makes adding a status trivial.
- `VALID_STATUS = tuple(STATUS_EMOJI)` — iterating a dict yields its keys, so this is
  `("not-started", "in-progress", "done")`. Used to validate frontmatter.

---

## Chunk 3 — reading and writing frontmatter (no PyYAML)

```python
FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def lesson_path(day: int) -> Path:
    return DAYS / f"day-{day:02d}" / "LESSON.md"


def read_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = FM_RE.match(text)
    if not match:
        raise SystemExit(f"{path} has no frontmatter block")
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        data[key.strip()] = value.split("#", 1)[0].strip().strip('"').strip("'")
    return data
```

**Line by line:**

- `FM_RE = re.compile(...)` — compile the pattern once at import time rather than on every call.
  Compiled patterns are cached by Python anyway, but naming it documents intent.
- `r"\A---\n(.*?)\n---\n"` — the pattern, piece by piece:
  - `r"..."` — a *raw* string, so `\A` stays as backslash-A instead of being interpreted by Python.
    Always use raw strings for regexes.
  - `\A` — anchor to the very start of the text. Frontmatter is only frontmatter if it is first.
  - `---\n` — the literal opening fence.
  - `(.*?)` — a capturing group holding the block's contents. The `?` makes it **non-greedy**:
    match as *few* characters as possible, so it stops at the *first* closing `---` rather than the
    last one in the document.
  - `\n---\n` — the closing fence.
- `re.DOTALL` — by default `.` does not match a newline. This flag makes it match everything, which
  is what lets `(.*?)` span multiple lines.
- `def lesson_path(day: int) -> Path:` — one function that knows the folder-naming convention, so
  the convention is written down once.
- `f"day-{day:02d}"` — an f-string. `:02d` formats the integer with at least 2 digits, zero-padded:
  `3` becomes `03`. This is why the folders sort correctly in a file listing.
- `path.read_text(encoding="utf-8")` — read the whole file as text. **Always pass `encoding`** on
  Windows; the default is the system codepage and will mangle the emoji in these docs.
- `raise SystemExit(f"...")` — exit with an error message and a non-zero status. Cleaner than
  `print` + `sys.exit(1)`, and it can be caught in tests.
- `match.group(1)` — the text captured by `(.*?)`, i.e. the frontmatter body.
- `.splitlines()` — split into lines without keeping the newline characters.
- `if not line.strip() or ... or ":" not in line: continue` — skip blank lines, comment lines, and
  anything that is not a `key: value` pair. `continue` jumps to the next loop iteration.
- `line.lstrip().startswith("#")` — `lstrip()` removes leading whitespace so an indented comment is
  still recognised as a comment.
- `key, _, value = line.partition(":")` — `partition` splits on the **first** occurrence and always
  returns exactly three parts (before, separator, after). This matters because values like
  `title: "Foundry I — the repo"` contain no colon but `commit: "abc: def"` might; splitting on the
  first colon only is correct. The `_` is a conventional name for "I do not need this value".
- `value.split("#", 1)[0]` — drop any trailing `# inline comment`. The `1` limits it to one split.
- `.strip().strip('"').strip("'")` — remove surrounding whitespace, then surrounding double quotes,
  then surrounding single quotes. So `status: not-started   # comment` yields `not-started`, and
  `title: "The loop, naked"` yields `The loop, naked`.

```python
def write_frontmatter_key(path: Path, key: str, value: str) -> None:
    """Replace one key inside the frontmatter, preserving everything else."""
    text = path.read_text(encoding="utf-8")
    match = FM_RE.match(text)
    if not match:
        raise SystemExit(f"{path} has no frontmatter block")
    block = match.group(1)
    pattern = re.compile(rf"^{re.escape(key)}:.*$", re.MULTILINE)
    replacement = f"{key}: {value}"
    new_block = pattern.sub(replacement, block) if pattern.search(block) else f"{block}\n{replacement}"
    path.write_text(text.replace(match.group(1), new_block, 1), encoding="utf-8")
```

**Line by line:**

- `rf"^{re.escape(key)}:.*$"` — an f-string *and* a raw string. `re.escape(key)` neutralises any
  regex-special characters in the key name, so a key called `a.b` matches literally rather than
  "a, any character, b".
- `^` and `$` with `re.MULTILINE` — anchor to the start and end of **each line**, not the whole
  string. Without `re.MULTILINE`, `^` would only match the very beginning of the block.
- `pattern.sub(replacement, block)` — replace every matching line with the new `key: value`.
- `if pattern.search(block) else f"{block}\n{replacement}"` — a conditional expression. If the key
  is not present at all, append it as a new line instead of silently doing nothing.
- `text.replace(match.group(1), new_block, 1)` — swap the old block for the new one in the full
  document. The trailing `1` limits it to the **first** occurrence, which protects you if the same
  text happens to appear later in the lesson body.

```python
def parse_ids(raw: str) -> list[str]:
    """`ids: ["AG-01", "AG-02"]`  ->  ['AG-01', 'AG-02']"""
    return re.findall(r"[A-Z]{2,3}-\d{2}", raw or "")


def all_days() -> list[tuple[int, dict[str, str]]]:
    out = []
    for path in sorted(DAYS.glob("day-[0-9][0-9]/LESSON.md")):
        try:
            out.append((int(path.parent.name.split("-")[1]), read_frontmatter(path)))
        except (ValueError, SystemExit):
            continue
    return out
```

**Line by line:**

- `re.findall(r"[A-Z]{2,3}-\d{2}", ...)` — find every ID-shaped token. `[A-Z]{2,3}` is two or three
  capital letters (`AG`, `OAI`, `CR`, `LC`, `LG`, `MCP`, `INT`), `-` is literal, `\d{2}` is exactly
  two digits. This is deliberately simpler than parsing YAML: it works whether the frontmatter says
  `["AG-01", "AG-02"]` or `AG-01, AG-02`.
- `raw or ""` — if `raw` is `None` (the key was missing), use an empty string. `findall` on `None`
  would raise.
- `DAYS.glob("day-[0-9][0-9]/LESSON.md")` — find matching files. The `[0-9][0-9]` pattern matches
  exactly two digits, which **excludes `day-00-setup`** — setup is not one of the 90 days and must
  not appear in the progress count.
- `sorted(...)` — glob order is filesystem-dependent; sorting makes output stable.
- `int(path.parent.name.split("-")[1])` — `path.parent.name` is e.g. `day-07`; `.split("-")` gives
  `['day', '07']`; `[1]` is `'07'`; `int(...)` is `7`.
- `except (ValueError, SystemExit): continue` — if a folder is malformed or a lesson has no
  frontmatter, skip it rather than crashing the whole dashboard.

---

## Chunk 4 — updating the curriculum index

```python
def update_index(day: int, status: str) -> None:
    """Set the Status cell of the Day-N row in docs/CURRICULUM_INDEX.md."""
    if not INDEX.exists():
        return
    emoji = STATUS_EMOJI[status]
    lines = INDEX.read_text(encoding="utf-8").splitlines()
    row_re = re.compile(rf"^\|\s*\[{day}\]\(")
    for i, line in enumerate(lines):
        if row_re.match(line):
            cells = line.split("|")
            gate = "🎯" in cells[-2]
            cells[-2] = f" {emoji}{' 🎯' if gate else ''} "
            lines[i] = "|".join(cells)
            break
    INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8")
```

**Line by line:**

- `if not INDEX.exists(): return` — degrade gracefully. The tracker must still work if you have not
  created the index yet.
- `rf"^\|\s*\[{day}\]\("` — matches a row like `| [7](../days/day-07/LESSON.md) | ...`.
  `\|` is an escaped pipe (a bare `|` means "or" in regex), `\s*` allows optional spaces,
  `\[{day}\]` is the day number in literal square brackets, `\(` is the opening parenthesis of the
  markdown link. Matching the link — not just the number — avoids accidentally hitting a row that
  merely mentions `7` somewhere.
- `for i, line in enumerate(lines):` — `enumerate` gives you the index and the value together, so
  you can write the modified line back into the same position.
- `cells = line.split("|")` — a markdown table row `| a | b |` splits into
  `['', ' a ', ' b ', '']` — note the empty strings at both ends from the leading and trailing pipes.
- `cells[-2]` — the **last real cell**, counting backwards past the trailing empty string. That is
  the Status column.
- `gate = "🎯" in cells[-2]` — remember whether this row was marked as a phase gate, so the marker
  survives the update.
- `f" {emoji}{' 🎯' if gate else ''} "` — rebuild the cell with surrounding spaces so the table
  stays readable in raw markdown.
- `break` — stop after the first match; there is only one row per day.
- `"\n".join(lines) + "\n"` — reassemble, and add the trailing newline that `splitlines()` removed.
  Files should end with a newline; git complains otherwise.

---

## Chunk 5 — updating the traceability table

```python
def update_traceability() -> tuple[int, int]:
    """An ID is covered when EVERY day that lists it is done. Returns (covered, total)."""
    if not TRACE.exists():
        return (0, 0)
    days_for_id: dict[str, list[str]] = {}
    for _, fm in all_days():
        for tid in parse_ids(fm.get("ids", "")):
            days_for_id.setdefault(tid, []).append(fm.get("status", "not-started"))

    covered = {tid for tid, sts in days_for_id.items() if sts and all(s == "done" for s in sts)}

    lines = TRACE.read_text(encoding="utf-8").splitlines()
    total = 0
    for i, line in enumerate(lines):
        m = re.match(r"^\|\s*([A-Z]{2,3}-\d{2})\s", line)
        if not m:
            continue
        total += 1
        cells = line.split("|")
        if len(cells) < 3:
            continue
        cells[-2] = " ✅ " if m.group(1) in covered else " ⬜ "
        lines[i] = "|".join(cells)
    TRACE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return (len(covered), total)
```

**Line by line:**

- `days_for_id: dict[str, list[str]]` — maps an ID to the list of statuses of every day that teaches
  it. Some IDs are taught across two days (`AG-12` on Days 7 and 47), which is exactly why this is a
  list and not a single value.
- `fm.get("ids", "")` — `.get` with a default never raises if the key is missing.
- `days_for_id.setdefault(tid, []).append(...)` — "give me the list for this ID, creating an empty
  one if it does not exist yet, then append". One line instead of an `if tid not in ...` check.
- `covered = {tid for tid, sts in ... if sts and all(s == "done" for s in sts)}` — a **set
  comprehension**. An ID counts as covered only when *every* day that teaches it is done — so
  `AG-12` stays open until both Day 7 and Day 47 are finished. That strictness is the point: the
  traceability table should not claim coverage you have not earned.
- `all(s == "done" for s in sts)` — `all()` returns True when every element of the sequence is
  truthy. The `sts and` guard in front handles the empty-list case, since `all([])` is `True`.
- `re.match(r"^\|\s*([A-Z]{2,3}-\d{2})\s", line)` — matches a traceability row that *starts* with an
  ID cell, e.g. `| AG-01 🛠️ | ... |`. `re.match` anchors at the start of the string.
- `total += 1` — count the rows we recognised, so the dashboard can report `covered/total`.
- `if len(cells) < 3: continue` — a defensive skip for malformed rows.
- `cells[-2] = " ✅ " if ... else " ⬜ "` — set the Covered column.
- `return (len(covered), total)` — the caller prints this.

---

## Chunk 6 — the changelog and git helpers

```python
def append_changelog(day: int, ids: list[str], summary: str, sha: str) -> None:
    """Append one line under '## Completed days'. Idempotent per day."""
    if not CHANGELOG.exists():
        return
    text = CHANGELOG.read_text(encoding="utf-8")
    marker = f"— Day {day} complete —"
    if marker in text:
        print(f"  changelog: Day {day} already logged, skipping")
        return
    today = dt.date.today().isoformat()
    id_str = ", ".join(ids) if ids else "infrastructure"
    entry = f"{today} — Day {day} complete — IDs: {id_str} — `{sha[:8]}` — {summary}"
    text = text.replace("*(nothing yet — Day 1 is waiting)*", "").rstrip() + "\n"
    CHANGELOG.write_text(text + entry + "\n", encoding="utf-8")
```

**Line by line:**

- `marker = f"— Day {day} complete —"` then `if marker in text: return` — **this is the idempotency
  guard.** Running `./m done 3` twice must not add two lines. Checking for the marker text is
  simpler and more robust than tracking state elsewhere.
- `dt.date.today().isoformat()` — today's date as `2026-08-21`. ISO format sorts correctly as text,
  which is why every date in this project uses it.
- `", ".join(ids) if ids else "infrastructure"` — infrastructure days (1, 2, 22, 69…) have no IDs;
  say so explicitly rather than printing an empty gap.
- `sha[:8]` — the first 8 characters of the commit hash. Enough to be unique in a repo this size and
  much easier to read.
- `text.replace("*(nothing yet — Day 1 is waiting)*", "")` — remove the placeholder the first time a
  real entry is written.
- `.rstrip() + "\n"` — trim trailing blank lines, then guarantee exactly one newline before the new
  entry. Without this the file grows a widening gap of blank lines.

```python
def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{result.stderr}")
    return result.stdout.strip()
```

**Line by line:**

- `def git(*args: str)` — `*args` collects any number of positional arguments into a tuple, so you
  can call `git("add", "-A")` or `git("commit", "-m", message)`.
- `["git", *args]` — build the command as a **list**, not a string. This is the safe form: the
  arguments are passed to the process directly, so a commit message containing spaces, quotes or
  semicolons cannot be re-interpreted by a shell. Never use `shell=True` with user text.
- `cwd=ROOT` — run git in the repo root regardless of where you invoked the script from.
- `capture_output=True` — collect stdout and stderr instead of letting them print.
- `text=True` — decode the output as text rather than raw bytes.
- `if result.returncode != 0: raise SystemExit(...)` — fail loudly, showing git's own error. A
  silent git failure would produce a "successful" day with no commit, which is the exact thing
  Principle 1 forbids.
- `return result.stdout.strip()` — the trimmed output, so `git("rev-parse", "HEAD")` returns a clean
  hash.

```python
def unchecked_boxes(day: int) -> list[str]:
    path = DAYS / f"day-{day:02d}" / "CHECKLIST.md"
    if not path.exists():
        return [f"{path} is missing"]
    return [line.strip()[5:].strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("- [ ]")]
```

**Line by line:**

- A **list comprehension** with a filter: for each line, keep it only if it starts with `- [ ]`
  (an unticked markdown checkbox), and transform it by cutting off those first 5 characters.
- `line.strip()` first — so indented checkboxes inside a sub-list are still found.
- `[5:]` — slice from character 5 to the end, dropping the literal `- [ ]`.
- A ticked box is `- [x]`, which does not match, so only *outstanding* items come back.

---

## Chunk 7 — the commands

```python
def cmd_scaffold(args) -> None:
    day = args.day
    folder = DAYS / f"day-{day:02d}"
    (folder / "lab").mkdir(parents=True, exist_ok=True)
    print(f"created {folder / 'lab'}")
    print(f"  next: open {lesson_path(day)} and run its '§ Setup — run this' block")


def cmd_start(args) -> None:
    day = args.day
    path = lesson_path(day)
    if not path.exists():
        raise SystemExit(f"no lesson at {path}")
    write_frontmatter_key(path, "status", "in-progress")
    update_index(day, "in-progress")
    fm = read_frontmatter(path)
    print(f"Day {day} — {fm.get('title', '')}")
    print(f"  IDs: {', '.join(parse_ids(fm.get('ids', ''))) or 'none (infrastructure)'}")
    print("  status -> in-progress   (index row updated)")
    print(f"  read: {path}")
```

**Line by line:**

- `.mkdir(parents=True, exist_ok=True)` — the Python equivalent of `mkdir -p`: create parent folders
  as needed, and do not raise if it already exists.
- `write_frontmatter_key(path, "status", "in-progress")` then `update_index(...)` — the two writes
  that keep the day file and the index agreeing. Doing both here is what removes the manual step.
- `', '.join(...) or 'none (infrastructure)'` — in Python, an empty string is falsy, so `or`
  supplies the fallback text when a day has no IDs.

```python
def cmd_check(args) -> None:
    """Lint and run the offline test suite. No network, no quota."""
    steps = [
        ["uv", "run", "ruff", "check", "."],
        ["uv", "run", "ruff", "format", "--check", "."],
        ["uv", "run", "pytest", "-q"],
    ]
    for step in steps:
        print(f"$ {' '.join(step)}")
        if subprocess.run(step, cwd=ROOT).returncode != 0:
            raise SystemExit("✗ check failed")
    print("✓ check green")
```

**Line by line:**

- `steps = [...]` — the three checks, as data. Adding a fourth (say, a type checker) is one line.
- `["uv", "run", "ruff", "check", "."]` — lint every file under the current directory.
- `["uv", "run", "ruff", "format", "--check", "."]` — `--check` means "tell me what is unformatted
  but do not change anything". Formatting is a separate, deliberate act (`ruff format .`), so a
  check never rewrites your files behind your back.
- `["uv", "run", "pytest", "-q"]` — run the tests. Note there is **no `-m live`**: the default run
  is offline and free by construction.
- `print(f"$ {' '.join(step)}")` — echo each command before running it, so the output is
  self-documenting.
- `subprocess.run(step, cwd=ROOT)` — no `capture_output` here, deliberately: you want to *see* ruff
  and pytest output as it happens.
- `raise SystemExit("✗ check failed")` — stop at the first failure. There is no value in running
  tests over code that does not lint.

```python
def cmd_done(args) -> None:
    day = args.day
    path = lesson_path(day)
    if not path.exists():
        raise SystemExit(f"no lesson at {path}")
    fm = read_frontmatter(path)
    ids = parse_ids(fm.get("ids", ""))

    remaining = unchecked_boxes(day)
    if remaining and not args.force:
        print(f"✗ Day {day} has {len(remaining)} unchecked checklist item(s):")
        for item in remaining[:12]:
            print(f"    - [ ] {item}")
        if len(remaining) > 12:
            print(f"    ... and {len(remaining) - 12} more")
        print("\nFix them, or re-run with --force if you deliberately deferred one.")
        raise SystemExit(1)

    if not args.skip_check:
        cmd_check(args)

    summary = args.summary or fm.get("title", f"day {day}")
    id_str = ", ".join(ids) if ids else "infrastructure"
    message = f"day-{day:02d}: {id_str} — {summary}"
    git("add", "-A")
    if git("status", "--porcelain"):
        git("commit", "-m", message)
    sha = git("rev-parse", "HEAD")

    write_frontmatter_key(path, "status", "done")
    write_frontmatter_key(path, "commit", f'"{sha[:8]}"')
    update_index(day, "done")
    covered, total = update_traceability()
    append_changelog(day, ids, summary, sha)

    git("add", "-A")
    if git("status", "--porcelain"):
        git("commit", "--amend", "--no-edit")
    sha = git("rev-parse", "HEAD")

    print(f"\n✓ Day {day} closed — {sha[:8]}")
    print(f"  {message}")
    print(f"  traceability: {covered}/{total} IDs covered")
    print(f"  next: ./m start {day + 1}")
```

This is the important one. **The order of operations is the design.** Line by line:

- `remaining = unchecked_boxes(day)` … `raise SystemExit(1)` — **gate one: the checklist.** You
  cannot close a day with outstanding boxes. `remaining[:12]` shows at most twelve so the output
  stays readable.
- `not args.force` — the escape hatch. `--force` exists because sometimes you genuinely defer an
  item on purpose; making it an explicit flag means you cannot do it by accident.
- `if not args.skip_check: cmd_check(args)` — **gate two: the code must be green.** This is
  Principle 1 and Principle 7 enforced by a program instead of by willpower.
- `summary = args.summary or fm.get("title", ...)` — use the summary you typed, or fall back to the
  lesson's title. So `./m done 3` works with no arguments.
- `message = f"day-{day:02d}: {id_str} — {summary}"` — the commit message convention from the
  project's `/done` skill: `day-03: AG-01, AG-02 — The loop, naked`. Consistent messages make
  `git log --oneline` a readable progress report.
- `git("add", "-A")` — stage everything.
- `if git("status", "--porcelain"):` — `--porcelain` prints a compact, machine-readable status, and
  prints **nothing at all** when the tree is clean. So this reads as "only commit if there is
  actually something to commit", which is what makes re-running safe.
- `sha = git("rev-parse", "HEAD")` — the hash of the commit just made.
- The four tracker updates — frontmatter status, frontmatter commit, index row, traceability,
  changelog. These happen **after** the commit because the changelog entry needs the sha.
- `git("commit", "--amend", "--no-edit")` — fold the tracker updates into that same commit rather
  than leaving a trailing "update trackers" commit. `--no-edit` keeps the existing message. The
  result: one clean commit per day, containing both the work and its bookkeeping.
- `print(f"  next: ./m start {day + 1}")` — always tell yourself the next command. Small thing;
  removes a decision at the exact moment you are most likely to stop.

```python
def cmd_sync(args) -> None:
    """Rebuild index + traceability from day frontmatter. Safe to run anytime."""
    days = all_days()
    for day, fm in days:
        status = fm.get("status", "not-started")
        if status not in VALID_STATUS:
            print(f"  ! day {day}: unknown status {status!r}, treating as not-started")
            status = "not-started"
        update_index(day, status)
    covered, total = update_traceability()
    print(f"synced {len(days)} days · traceability {covered}/{total} IDs covered")
```

- `{status!r}` — the `!r` conversion prints the `repr()` of the value, i.e. with quotes. Useful in
  error messages because it makes a stray space or newline visible.
- This command is your undo button. If the index ever disagrees with reality — a merge conflict, a
  hand edit — `./m sync` regenerates it from the day files.

```python
def cmd_status(args) -> None:
    days = all_days()
    by_day = dict(days)
    done = [d for d, fm in days if fm.get("status") == "done"]
    active = [d for d, fm in days if fm.get("status") == "in-progress"]
    covered, total = update_traceability()

    width = 50
    filled = int(width * len(done) / max(len(days), 1))
    bar = "█" * filled + "░" * (width - filled)

    print(f"\n  Project Mandala — {len(done)}/{len(days)} days")
    print(f"  {bar} {len(done) / max(len(days), 1):.0%}")
    print(f"  IDs covered: {covered}/{total}")
    for d in active:
        print(f"  🟨 in progress: Day {d} — {by_day[d].get('title', '')}")
    nxt = next((d for d, fm in days if fm.get("status", "not-started") == "not-started"), None)
    if nxt is not None:
        fm = by_day[nxt]
        print(f"  ⬜ next up:     Day {nxt} — {fm.get('title', '')}")
        print(f"                 IDs: {', '.join(parse_ids(fm.get('ids', ''))) or 'infrastructure'}")
        print(f"                 ./m start {nxt}")
    print()

    phases: dict[str, list[str]] = {}
    for d, fm in days:
        phases.setdefault(fm.get("phase", "?"), []).append(fm.get("status", "not-started"))
    print("  phase  done/total")
    for phase in sorted(phases, key=lambda p: int(p) if p.isdigit() else 99):
        sts = phases[phase]
        print(f"    {phase:>2}   {sum(s == 'done' for s in sts)}/{len(sts)}")
    print()
```

**Line by line:**

- `by_day = dict(days)` — `days` is a list of `(number, frontmatter)` pairs, and `dict()` turns a
  list of pairs straight into a lookup table.
- `max(len(days), 1)` — guard against dividing by zero before any lessons exist.
- `"█" * filled + "░" * (width - filled)` — multiplying a string repeats it. That is the whole
  progress bar: two block characters and some arithmetic.
- `{...:.0%}` — format a fraction as a percentage with no decimal places: `0.0777` → `8%`.
- `next((d for d, fm in days if ...), None)` — `next()` pulls the first item from a generator; the
  second argument is the default returned when the generator is empty. This is the idiomatic
  "find the first match or None" in Python, and it stops scanning as soon as it finds one.
- `sum(s == 'done' for s in sts)` — in Python `True` equals `1`, so summing booleans counts them.
- `sorted(phases, key=lambda p: int(p) if p.isdigit() else 99)` — sort phases numerically rather
  than as text (otherwise `10` sorts before `2`). The `else 99` parks any non-numeric phase at the
  end instead of crashing.
- `{phase:>2}` — right-align in a field 2 characters wide, so single- and double-digit phase
  numbers line up.

```python
def cmd_check_ids(args) -> None:
    """Every ID in TRACEABILITY.md must appear in the days it claims."""
    declared: dict[str, list[int]] = {}
    for day, fm in all_days():
        for tid in parse_ids(fm.get("ids", "")):
            declared.setdefault(tid, []).append(day)

    problems = []
    for line in TRACE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*([A-Z]{2,3}-\d{2})\s.*?\|\s*([^|]*?)\s*\|\s*[⬜✅]", line)
        if not m:
            continue
        tid, day_cell = m.group(1), m.group(2)
        claimed = {int(x) for x in re.findall(r"\d+", day_cell)}
        actual = set(declared.get(tid, []))
        if not actual:
            problems.append(f"{tid}: traceability claims {sorted(claimed)}, no LESSON declares it")
        elif not actual & claimed:
            problems.append(f"{tid}: traceability says {sorted(claimed)}, lessons say {sorted(actual)}")

    if problems:
        print("✗ traceability drift:")
        for p in problems:
            print(f"    {p}")
        raise SystemExit(1)
    print(f"✓ all {len(declared)} declared IDs agree with docs/TRACEABILITY.md")
```

- This is a **consistency test for your own documentation**. If a lesson's frontmatter says it
  teaches `AG-09` but the traceability table slots `AG-09` on a different day, you find out here
  rather than at a phase gate.
- `actual & claimed` — set intersection. Non-empty means at least one day agrees.
- Run it at every phase gate. It is the cheapest audit in the project.

---

## Chunk 8 — the argument parser

```python
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mandala", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    for name, fn, helptext in [
        ("scaffold", cmd_scaffold, "create days/day-NN/lab/"),
        ("start", cmd_start, "mark a day in-progress"),
    ]:
        p = sub.add_parser(name, help=helptext)
        p.add_argument("day", type=int)
        p.set_defaults(func=fn)

    p = sub.add_parser("done", help="verify, commit, and update every tracker")
    p.add_argument("day", type=int)
    p.add_argument("--summary", help="one-line summary for the commit + changelog")
    p.add_argument("--force", action="store_true", help="commit despite unchecked boxes")
    p.add_argument("--skip-check", action="store_true", help="skip lint+tests (don't)")
    p.set_defaults(func=cmd_done)

    for name, fn, helptext in [
        ("check", cmd_check, "lint + offline tests"),
        ("sync", cmd_sync, "rebuild index + traceability from frontmatter"),
        ("status", cmd_status, "progress dashboard"),
        ("check-ids", cmd_check_ids, "verify lessons and traceability agree"),
    ]:
        p = sub.add_parser(name, help=helptext)
        p.set_defaults(func=fn)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

**Line by line:**

- `argparse.ArgumentParser(prog="mandala", description=__doc__, ...)` — `__doc__` is the module
  docstring from Chunk 1, so `./m --help` prints the usage summary you already wrote.
- `formatter_class=argparse.RawDescriptionHelpFormatter` — by default argparse re-wraps the
  description text and destroys your line breaks. This class preserves them.
- `parser.add_subparsers(dest="command", required=True)` — enable subcommands (`start`, `done`, …).
  `required=True` means running `./m` with no subcommand prints help instead of doing nothing.
- The `for name, fn, helptext in [...]` loops — register several similar subcommands from a table
  rather than repeating six near-identical blocks.
- `p.add_argument("day", type=int)` — a positional argument, automatically converted to an integer.
  `./m start abc` therefore fails with a clear message rather than deep inside the code.
- `action="store_true"` — makes `--force` a flag: present means `True`, absent means `False`.
- `p.set_defaults(func=fn)` — attach the handler function to the parsed arguments. Then
  `args.func(args)` dispatches to the right command with no `if/elif` chain at all. This is the
  standard argparse subcommand idiom.
- `if __name__ == "__main__": main()` — only run `main()` when the file is executed directly, not
  when it is imported. Without this guard, importing the module for a test would run the CLI.

---

## §9 Now create the file

Everything above, assembled. Paste this whole block into Git Bash:

```bash
cat > scripts/mandala.py <<'PYEOF'
#!/usr/bin/env python3
"""
mandala.py — the tracking automation and task runner for the 90-day plan.

    ./m status          progress dashboard
    ./m start 3         mark Day 3 in-progress
    ./m check           lint + offline tests (no network, no quota)
    ./m done 3          verify -> commit -> update every tracker file
    ./m sync            rebuild index + traceability from day frontmatter
    ./m check-ids       verify lessons and TRACEABILITY.md agree

Standard library only. Never touches a network or a model.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
DAYS = ROOT / "days"
DOCS = ROOT / "docs"
INDEX = DOCS / "CURRICULUM_INDEX.md"
TRACE = DOCS / "TRACEABILITY.md"
CHANGELOG = DOCS / "CHANGELOG_PLAN.md"

STATUS_EMOJI = {"not-started": "⬜", "in-progress": "🟨", "done": "✅"}
VALID_STATUS = tuple(STATUS_EMOJI)
GATE = "🎯"

FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def lesson_path(day: int) -> Path:
    return DAYS / f"day-{day:02d}" / "LESSON.md"


def read_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = FM_RE.match(text)
    if not match:
        raise SystemExit(f"{path} has no frontmatter block")
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        data[key.strip()] = value.split("#", 1)[0].strip().strip('"').strip("'")
    return data


def write_frontmatter_key(path: Path, key: str, value: str) -> None:
    text = path.read_text(encoding="utf-8")
    match = FM_RE.match(text)
    if not match:
        raise SystemExit(f"{path} has no frontmatter block")
    block = match.group(1)
    pattern = re.compile(rf"^{re.escape(key)}:.*$", re.MULTILINE)
    replacement = f"{key}: {value}"
    if pattern.search(block):
        new_block = pattern.sub(replacement, block)
    else:
        new_block = f"{block}\n{replacement}"
    path.write_text(text.replace(match.group(1), new_block, 1), encoding="utf-8")


def parse_ids(raw: str) -> list[str]:
    return re.findall(r"[A-Z]{2,3}-\d{2}", raw or "")


def all_days() -> list[tuple[int, dict[str, str]]]:
    out = []
    for path in sorted(DAYS.glob("day-[0-9][0-9]/LESSON.md")):
        try:
            out.append((int(path.parent.name.split("-")[1]), read_frontmatter(path)))
        except (ValueError, SystemExit):
            continue
    return out


def update_index(day: int, status: str) -> None:
    if not INDEX.exists():
        return
    emoji = STATUS_EMOJI[status]
    lines = INDEX.read_text(encoding="utf-8").splitlines()
    row_re = re.compile(rf"^\|\s*\[{day}\]\(")
    for i, line in enumerate(lines):
        if row_re.match(line):
            cells = line.split("|")
            suffix = f" {GATE}" if GATE in cells[-2] else ""
            cells[-2] = f" {emoji}{suffix} "
            lines[i] = "|".join(cells)
            break
    INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_traceability() -> tuple[int, int]:
    if not TRACE.exists():
        return (0, 0)
    days_for_id: dict[str, list[str]] = {}
    for _, fm in all_days():
        for tid in parse_ids(fm.get("ids", "")):
            days_for_id.setdefault(tid, []).append(fm.get("status", "not-started"))

    covered = {tid for tid, sts in days_for_id.items() if sts and all(s == "done" for s in sts)}

    lines = TRACE.read_text(encoding="utf-8").splitlines()
    total = 0
    for i, line in enumerate(lines):
        m = re.match(r"^\|\s*([A-Z]{2,3}-\d{2})\s", line)
        if not m:
            continue
        total += 1
        cells = line.split("|")
        if len(cells) < 3:
            continue
        cells[-2] = " ✅ " if m.group(1) in covered else " ⬜ "
        lines[i] = "|".join(cells)
    TRACE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return (len(covered), total)


def append_changelog(day: int, ids: list[str], summary: str, sha: str) -> None:
    if not CHANGELOG.exists():
        return
    text = CHANGELOG.read_text(encoding="utf-8")
    marker = f"— Day {day} complete —"
    if marker in text:
        print(f"  changelog: Day {day} already logged, skipping")
        return
    today = dt.date.today().isoformat()
    id_str = ", ".join(ids) if ids else "infrastructure"
    entry = f"{today} — Day {day} complete — IDs: {id_str} — `{sha[:8]}` — {summary}"
    text = text.replace("*(nothing yet — Day 1 is waiting)*", "").rstrip() + "\n"
    CHANGELOG.write_text(text + entry + "\n", encoding="utf-8")


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{result.stderr}")
    return result.stdout.strip()


def unchecked_boxes(day: int) -> list[str]:
    path = DAYS / f"day-{day:02d}" / "CHECKLIST.md"
    if not path.exists():
        return [f"{path} is missing"]
    return [
        line.strip()[5:].strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("- [ ]")
    ]


def cmd_scaffold(args) -> None:
    day = args.day
    folder = DAYS / f"day-{day:02d}"
    (folder / "lab").mkdir(parents=True, exist_ok=True)
    print(f"created {folder / 'lab'}")
    print(f"  next: open {lesson_path(day)} and run its Setup block")


def cmd_start(args) -> None:
    day = args.day
    path = lesson_path(day)
    if not path.exists():
        raise SystemExit(f"no lesson at {path}")
    write_frontmatter_key(path, "status", "in-progress")
    update_index(day, "in-progress")
    fm = read_frontmatter(path)
    print(f"Day {day} — {fm.get('title', '')}")
    print(f"  IDs: {', '.join(parse_ids(fm.get('ids', ''))) or 'none (infrastructure)'}")
    print("  status -> in-progress   (index row updated)")
    print(f"  read: {path}")


def cmd_check(args) -> None:
    steps = [
        ["uv", "run", "ruff", "check", "."],
        ["uv", "run", "ruff", "format", "--check", "."],
        ["uv", "run", "pytest", "-q"],
    ]
    for step in steps:
        print(f"$ {' '.join(step)}")
        if subprocess.run(step, cwd=ROOT).returncode != 0:
            raise SystemExit("✗ check failed")
    print("✓ check green")


def cmd_done(args) -> None:
    day = args.day
    path = lesson_path(day)
    if not path.exists():
        raise SystemExit(f"no lesson at {path}")
    fm = read_frontmatter(path)
    ids = parse_ids(fm.get("ids", ""))

    remaining = unchecked_boxes(day)
    if remaining and not args.force:
        print(f"✗ Day {day} has {len(remaining)} unchecked checklist item(s):")
        for item in remaining[:12]:
            print(f"    - [ ] {item}")
        if len(remaining) > 12:
            print(f"    ... and {len(remaining) - 12} more")
        print("\nFix them, or re-run with --force if you deliberately deferred one.")
        raise SystemExit(1)

    if not args.skip_check:
        cmd_check(args)

    summary = args.summary or fm.get("title", f"day {day}")
    id_str = ", ".join(ids) if ids else "infrastructure"
    message = f"day-{day:02d}: {id_str} — {summary}"
    git("add", "-A")
    if git("status", "--porcelain"):
        git("commit", "-m", message)
    sha = git("rev-parse", "HEAD")

    write_frontmatter_key(path, "status", "done")
    write_frontmatter_key(path, "commit", f'"{sha[:8]}"')
    update_index(day, "done")
    covered, total = update_traceability()
    append_changelog(day, ids, summary, sha)

    git("add", "-A")
    if git("status", "--porcelain"):
        git("commit", "--amend", "--no-edit")
    sha = git("rev-parse", "HEAD")

    print(f"\n✓ Day {day} closed — {sha[:8]}")
    print(f"  {message}")
    print(f"  traceability: {covered}/{total} IDs covered")
    print(f"  next: ./m start {day + 1}")


def cmd_sync(args) -> None:
    days = all_days()
    for day, fm in days:
        status = fm.get("status", "not-started")
        if status not in VALID_STATUS:
            print(f"  ! day {day}: unknown status {status!r}, treating as not-started")
            status = "not-started"
        update_index(day, status)
    covered, total = update_traceability()
    print(f"synced {len(days)} days · traceability {covered}/{total} IDs covered")


def cmd_status(args) -> None:
    days = all_days()
    by_day = dict(days)
    done = [d for d, fm in days if fm.get("status") == "done"]
    active = [d for d, fm in days if fm.get("status") == "in-progress"]
    covered, total = update_traceability()

    width = 50
    filled = int(width * len(done) / max(len(days), 1))
    bar = "█" * filled + "░" * (width - filled)

    print(f"\n  Project Mandala — {len(done)}/{len(days)} days")
    print(f"  {bar} {len(done) / max(len(days), 1):.0%}")
    print(f"  IDs covered: {covered}/{total}")
    for d in active:
        print(f"  🟨 in progress: Day {d} — {by_day[d].get('title', '')}")
    nxt = next((d for d, fm in days if fm.get("status", "not-started") == "not-started"), None)
    if nxt is not None:
        fm = by_day[nxt]
        print(f"  ⬜ next up:     Day {nxt} — {fm.get('title', '')}")
        print(f"                 IDs: {', '.join(parse_ids(fm.get('ids', ''))) or 'infrastructure'}")
        print(f"                 ./m start {nxt}")
    print()

    phases: dict[str, list[str]] = {}
    for d, fm in days:
        phases.setdefault(fm.get("phase", "?"), []).append(fm.get("status", "not-started"))
    print("  phase  done/total")
    for phase in sorted(phases, key=lambda p: int(p) if p.isdigit() else 99):
        sts = phases[phase]
        print(f"    {phase:>2}   {sum(s == 'done' for s in sts)}/{len(sts)}")
    print()


def cmd_check_ids(args) -> None:
    declared: dict[str, list[int]] = {}
    for day, fm in all_days():
        for tid in parse_ids(fm.get("ids", "")):
            declared.setdefault(tid, []).append(day)

    problems = []
    for line in TRACE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*([A-Z]{2,3}-\d{2})\s.*?\|\s*([^|]*?)\s*\|\s*[⬜✅]", line)
        if not m:
            continue
        tid, day_cell = m.group(1), m.group(2)
        claimed = {int(x) for x in re.findall(r"\d+", day_cell)}
        actual = set(declared.get(tid, []))
        if not actual:
            problems.append(f"{tid}: traceability claims {sorted(claimed)}, no LESSON declares it")
        elif not actual & claimed:
            problems.append(
                f"{tid}: traceability says {sorted(claimed)}, lessons say {sorted(actual)}"
            )

    if problems:
        print("✗ traceability drift:")
        for p in problems:
            print(f"    {p}")
        raise SystemExit(1)
    print(f"✓ all {len(declared)} declared IDs agree with docs/TRACEABILITY.md")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mandala",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    for name, fn, helptext in [
        ("scaffold", cmd_scaffold, "create days/day-NN/lab/"),
        ("start", cmd_start, "mark a day in-progress"),
    ]:
        p = sub.add_parser(name, help=helptext)
        p.add_argument("day", type=int)
        p.set_defaults(func=fn)

    p = sub.add_parser("done", help="verify, commit, and update every tracker")
    p.add_argument("day", type=int)
    p.add_argument("--summary", help="one-line summary for the commit + changelog")
    p.add_argument("--force", action="store_true", help="commit despite unchecked boxes")
    p.add_argument("--skip-check", action="store_true", help="skip lint+tests (don't)")
    p.set_defaults(func=cmd_done)

    for name, fn, helptext in [
        ("check", cmd_check, "lint + offline tests"),
        ("sync", cmd_sync, "rebuild index + traceability from frontmatter"),
        ("status", cmd_status, "progress dashboard"),
        ("check-ids", cmd_check_ids, "verify lessons and traceability agree"),
    ]:
        p = sub.add_parser(name, help=helptext)
        p.set_defaults(func=fn)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
PYEOF
```

> **One difference from the explained chunks:** the assembled version adds a `GATE = "🎯"` constant
> near the top and uses it inside `update_index`. That is purely to keep the emoji out of the
> f-string expression, which is easier to read and impossible to get wrong. Behaviour is identical.
>
> **Paste this in Git Bash, not PowerShell.** The `<<'PYEOF'` heredoc passes the UTF-8 emoji through
> byte-for-byte. PowerShell's here-strings would re-encode them and the file would break.

---

## §10 Verify the tracker

```bash
uv run python scripts/mandala.py --help
uv run python scripts/mandala.py status
uv run python scripts/mandala.py sync
uv run python scripts/mandala.py check-ids
```

- `--help` should print the docstring from Chunk 1 plus the seven subcommands.
- `status` should print the progress bar at 0%.
- `sync` should report `synced 90 days`.
- `check-ids` should print `✓ all 138 declared IDs agree with docs/TRACEABILITY.md`.

If `check-ids` reports drift, that is a genuine inconsistency between a lesson's frontmatter and
`docs/TRACEABILITY.md` — fix whichever is wrong, then re-run.

Then make the shortcut from [`LESSON.md`](LESSON.md) §6 and confirm:

```bash
./m status
```

---

## §11 What you just built, in one sentence for an interview

> "I automated my own project bookkeeping on day zero — a small stdlib-only CLI that treats the
> per-document frontmatter as the source of truth and regenerates the index, the coverage table and
> the changelog from it, then gates the commit on the checklist and the test suite. It meant that
> ninety days later my documentation still matched my code, because keeping them in sync was never a
> thing I had to remember to do."
