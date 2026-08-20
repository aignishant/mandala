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
        ids = ", ".join(parse_ids(fm.get("ids", ""))) or "infrastructure"
        print(f"  ⬜ next up:     Day {nxt} — {fm.get('title', '')}")
        print(f"                 IDs: {ids}")
        print(f"                 ./m start {nxt}")
    print()

    phases: dict[str, list[str]] = {}
    for _day, fm in days:
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
