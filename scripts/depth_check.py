#!/usr/bin/env python
"""Enforce the plan's Part 11 depth contract on a day folder.

A day is written when it is a hub plus one document per subtopic (Principle 15), each taken from
zero prior knowledge through to production (Principle 17), with no clock anywhere (Principle 16).
This script is the machine-readable half of that contract: it cannot judge whether an explanation
is good, but it can refuse a day that has no parts, a numbering gap, a missing required section, a
code block nobody walked through, a time estimate, a part loose outside its section folder, or a hub
that quietly went back to teaching.

    uv run python scripts/depth_check.py          # every day that has a parts/ directory
    uv run python scripts/depth_check.py 4        # just day 4
    uv run python scripts/depth_check.py 4 5 6    # several days

Exit code 0 means every checked day satisfies the contract. Anything else is a failure list.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAYS = ROOT / "days"

# parts/<NN>/<section>.<subtopic>-<kebab-slug>.md
#   ->  "parts/02/2.3-why-the-model-never-runs-your-tool.md"
PART_NAME_RE = re.compile(r"^(\d+)\.(\d+)-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")

# A section folder is the section number, zero-padded to two digits: 01, 02, ... 12.
SECTION_DIR_RE = re.compile(r"^\d{2}$")

# The ten required sections of a part document, in order (plan Part 11.4). Section 1 is the
# frontmatter, checked separately; these are the nine that appear in the body.
PART_SECTIONS = [
    ("one-line answer", re.compile(r"^#{2,3}\s.*one[- ]line answer", re.I | re.M)),
    ("the story", re.compile(r"^#{2,3}\s.*the story", re.I | re.M)),
    ("the idea in plain language", re.compile(r"^#{2,3}\s.*idea in plain language", re.I | re.M)),
    ("why Mandala needs it", re.compile(r"^#{2,3}\s.*why mandala needs it", re.I | re.M)),
    ("the mechanism", re.compile(r"^#{2,3}\s.*mechanism", re.I | re.M)),
    ("line by line", re.compile(r"^#{2,3}\s.*line by line|^\*\*Line by line:?\*\*", re.I | re.M)),
    ("when it breaks", re.compile(r"^#{2,3}\s.*when it breaks", re.I | re.M)),
    ("in production", re.compile(r"^#{2,3}\s.*in production", re.I | re.M)),
    ("check yourself", re.compile(r"^#{2,3}\s.*check yourself", re.I | re.M)),
]

PART_FRONTMATTER_KEYS = ["day", "part", "title", "ids", "level", "prerequisites", "prev", "next"]

# Principle 17: every part declares where it leaves the reader.
LEVELS = {"foundation", "working", "production"}

# Principle 16: a day is a unit of subject, not a unit of time. Nothing in a day folder may
# suggest a duration or a pace - not "takes 20 minutes", not "reading_minutes", not "half a day".
TIME_BANS = [
    (
        re.compile(
            r"^\s*(reading_minutes|duration|time_estimate|minutes|est_time|pace)\s*:", re.I | re.M
        ),
        "a duration field in frontmatter",
    ),
    (
        re.compile(r"\b\d+\s*[-–]?\s*\d*\s*(minutes?|mins?|hours?|hrs?)\b(?!\s*(of |the ))", re.I),
        "a time estimate in the prose",
    ),
    (re.compile(r"\*\*Time:?\*\*", re.I), "a **Time:** line"),
    (re.compile(r"should take (about |around |roughly )?\w+", re.I), "a 'should take ...' pace"),
    (re.compile(r"\b(half|full) a? ?day\b", re.I), "a day-length estimate"),
    (re.compile(r"\bin (one|two|three|a single) (evening|sitting|session)s?\b", re.I), "a pace"),
]

HUB_FRONTMATTER_KEYS = [
    "day",
    "phase",
    "phase_name",
    "title",
    "ids",
    "principles",
    "kind",
    "plan_version",
    "parts",
    "generated",
    "status",
    "lab_scaffolded",
    "commit",
]

# The twelve required hub sections (plan Part 11.5). Frontmatter and the yesterday/today/tomorrow
# blockquote are checked separately; these ten are the numbered headings.
HUB_SECTIONS = [
    (1, "The story"),
    (2, "The map"),
    (3, "Setup"),
    (4, "Build brief"),
    (5, "The eval"),
    (6, "Request budget"),
    (7, "Traps"),
    (8, "Verify before you code"),
    (9, "Say it in an interview"),
    (10, "Done when"),
]

# Fences whose contents are error output or a bare check command - they need no walkthrough.
NO_WALKTHROUGH_LANGS = {
    "",
    "text",
    "console",
    "traceback",
    "mermaid",
    "json",
    "toml",
    "yaml",
    "ini",
}

# Headings under which a code block is evidence, not teaching, so no walkthrough is required.
EXEMPT_HEADINGS = re.compile(r"when it breaks|check yourself|verify|request budget", re.I)


@dataclass
class Report:
    day: int
    failures: list[str] = field(default_factory=list)
    parts: int = 0

    @property
    def ok(self) -> bool:
        return not self.failures

    def fail(self, where: str, message: str) -> None:
        self.failures.append(f"{where}: {message}")


def frontmatter(text: str) -> dict[str, str] | None:
    """Return the YAML-ish frontmatter as a flat dict, or None when there is none."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end]
    out: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition(":")
            out[key.strip()] = value.strip()
    return out


def body(text: str) -> str:
    """The document with its frontmatter removed, so heading checks cannot match inside it."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4 :]
    return text


def find_day(number: int) -> Path | None:
    candidates = [DAYS / f"day-{number:02d}", DAYS / f"day-{number}"]
    if number == 0:
        candidates.insert(0, DAYS / "day-00-setup")
    return next((p for p in candidates if p.is_dir()), None)


def unexplained_code_blocks(text: str) -> list[int]:
    """Line numbers of code fences that no 'Line by line' walkthrough follows.

    Walks the document once, tracking the current heading. A fence is exempt when its language
    carries no logic (plain output, a diagram, a config dump) or when it sits under a heading
    whose job is showing evidence rather than teaching.
    """
    lines = text.splitlines()
    offenders: list[int] = []
    heading = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#"):
            heading = line
            i += 1
            continue
        fence = re.match(r"^(`{3,})(\w*)\s*$", line)
        if not fence:
            i += 1
            continue

        # A fence may be longer than three backticks so it can contain a shorter one - which
        # is how a lesson shows the contents of a Markdown file. The closing fence must be at
        # least as long as the opening one, so a nested block cannot end the outer one.
        ticks = len(fence.group(1))
        closing = re.compile(rf"^`{{{ticks},}}\s*$")
        lang = fence.group(2).lower()
        start = i
        i += 1
        while i < len(lines) and not closing.match(lines[i]):
            i += 1
        i += 1  # step over the closing fence

        if lang in NO_WALKTHROUGH_LANGS or EXEMPT_HEADINGS.search(heading):
            continue

        # Look ahead for a walkthrough before the next fence or the next heading of the same rank.
        j = i
        explained = False
        while j < len(lines):
            nxt = lines[j]
            if re.search(r"line by line", nxt, re.I):
                explained = True
                break
            if re.match(r"^`{3,}\w", nxt) or nxt.startswith("## "):
                break
            j += 1
        if not explained:
            offenders.append(start + 1)
    return offenders


def check_no_clocks(text: str, where: str, report: Report) -> None:
    """Principle 16: no time estimates anywhere in a day folder.

    Content is never trimmed to fit a schedule, so no document may imply one. Code fences are
    stripped first - a real command may legitimately mention a timeout.
    """
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    for pattern, description in TIME_BANS:
        hit = pattern.search(prose)
        if hit:
            snippet = hit.group(0).strip().replace("\n", " ")
            report.fail(where, f"{description} ({snippet!r}) - a day has no clock (Principle 16)")


def check_part(path: Path, day: int, report: Report) -> tuple[int, int] | None:
    """Validate one parts/<NN>/ document. Returns its (section, subtopic) numbers."""
    where = f"parts/{path.parent.name}/{path.name}"
    match = PART_NAME_RE.match(path.name)
    if not match:
        report.fail(where, "filename must be <section>.<subtopic>-<kebab-slug>.md")
        return None
    section, subtopic = int(match.group(1)), int(match.group(2))

    folder = path.parent.name
    if folder != f"{section:02d}":
        report.fail(
            where,
            f"lives in parts/{folder}/ but its number says section {section} - "
            f"it belongs in parts/{section:02d}/",
        )

    text = path.read_text(encoding="utf-8")
    meta = frontmatter(text)
    if meta is None:
        report.fail(where, "no YAML frontmatter")
    else:
        missing = [k for k in PART_FRONTMATTER_KEYS if k not in meta]
        if missing:
            report.fail(where, f"frontmatter missing {', '.join(missing)}")
        if meta.get("day") not in {str(day), f'"{day}"'}:
            report.fail(where, f"frontmatter day is {meta.get('day')!r}, expected {day}")
        if meta.get("part", "").strip('"') != f"{section}.{subtopic}":
            report.fail(where, f"frontmatter part should be {section}.{subtopic}")
        level = meta.get("level", "").strip('"').lower()
        if level and level not in LEVELS:
            report.fail(where, f"level is {level!r}, must be one of {sorted(LEVELS)}")

    content = body(text)
    seen_at: list[int] = []
    for name, pattern in PART_SECTIONS:
        found = pattern.search(content)
        if not found:
            report.fail(where, f"missing required section: {name}")
        else:
            seen_at.append(found.start())
    if len(seen_at) == len(PART_SECTIONS) and seen_at != sorted(seen_at):
        report.fail(where, "required sections are out of contract order (plan Part 11.4)")

    for line_no in unexplained_code_blocks(content):
        report.fail(where, f"code block at line {line_no} has no 'Line by line' walkthrough")

    check_no_clocks(text, where, report)
    return section, subtopic


def check_numbering(numbers: list[tuple[int, int]], report: Report) -> None:
    """Sections start at 1 and are contiguous; so are the subtopics inside each section."""
    if not numbers:
        return
    sections = sorted({s for s, _ in numbers})
    if sections[0] != 1:
        report.fail("parts/", f"section numbering starts at {sections[0]}, must start at 1")
    expected = list(range(1, len(sections) + 1))
    if sections != expected:
        report.fail("parts/", f"section numbering has a gap: {sections} (expected {expected})")
    for section in sections:
        subs = sorted(sub for s, sub in numbers if s == section)
        if subs != list(range(1, len(subs) + 1)):
            report.fail(
                "parts/", f"section {section} subtopics are {subs}, expected 1..{len(subs)}"
            )


def check_hub(folder: Path, day: int, part_count: int, report: Report) -> None:
    hub = folder / "LESSON.md"
    if not hub.is_file():
        report.fail("LESSON.md", "missing - every day needs a hub")
        return

    text = hub.read_text(encoding="utf-8")
    meta = frontmatter(text)
    if meta is None:
        report.fail("LESSON.md", "no YAML frontmatter")
    else:
        missing = [k for k in HUB_FRONTMATTER_KEYS if k not in meta]
        if missing:
            report.fail("LESSON.md", f"frontmatter missing {', '.join(missing)}")
        declared = meta.get("parts", "").strip('"')
        if declared.isdigit() and int(declared) != part_count:
            report.fail(
                "LESSON.md", f"frontmatter says parts: {declared}, parts/ holds {part_count}"
            )
        if meta.get("plan_version", "").strip('"') != "v2.0.0":
            report.fail("LESSON.md", "plan_version must be v2.0.0")

    content = body(text)
    for number, name in HUB_SECTIONS:
        if not re.search(rf"^##\s*§{number}\b", content, re.M):
            report.fail("LESSON.md", f"missing section §{number} ({name})")

    if not re.search(r"^>\s*\*\*Yesterday", content, re.M | re.I):
        report.fail("LESSON.md", "missing the yesterday / today / tomorrow blockquote")

    if re.search(r"line by line", content, re.I):
        report.fail("LESSON.md", "the hub must not teach - move the walkthrough into a part")

    check_no_clocks(text, "LESSON.md", report)

    linked = set(re.findall(r"parts/(\d+/[\w.\-]+\.md)", content))
    on_disk = {
        f"{d.name}/{f.name}"
        for d in (folder / "parts").iterdir()
        if d.is_dir()
        for f in d.glob("*.md")
    }
    for name in sorted(on_disk - linked):
        report.fail("LESSON.md", f"§2 map does not link parts/{name}")


def check_day(number: int) -> Report:
    report = Report(day=number)
    folder = find_day(number)
    if folder is None:
        report.fail("days/", f"no folder for day {number}")
        return report

    parts_dir = folder / "parts"
    if not parts_dir.is_dir():
        report.fail("parts/", "missing - a day with no parts/ is not written (plan Part 11.2)")
        return report

    for stray in sorted(parts_dir.glob("*.md")):
        report.fail(
            f"parts/{stray.name}",
            "loose in parts/ - every part lives in its section folder, e.g. parts/01/",
        )

    for entry in sorted(parts_dir.iterdir()):
        if entry.is_dir() and not SECTION_DIR_RE.match(entry.name):
            report.fail(
                f"parts/{entry.name}/",
                "section folders are the section number zero-padded to two digits (01, 02, ...)",
            )

    files = sorted(
        (f for d in parts_dir.iterdir() if d.is_dir() for f in d.glob("*.md")),
        key=lambda f: (f.parent.name, f.name),
    )
    if not files:
        report.fail("parts/", "empty - no section folders holding part documents")
        return report

    report.parts = len(files)
    numbers = [n for f in files if (n := check_part(f, number, report)) is not None]
    check_numbering(numbers, report)
    check_hub(folder, number, len(files), report)

    checklist = folder / "CHECKLIST.md"
    if not checklist.is_file():
        report.fail("CHECKLIST.md", "missing")
    else:
        check_no_clocks(checklist.read_text(encoding="utf-8"), "CHECKLIST.md", report)
    return report


def written_days() -> list[int]:
    """Every day that has attempted the v2.0.0 shape, so an unwritten day is not a failure."""
    found: list[int] = []
    for folder in sorted(DAYS.glob("day-*")):
        if not (folder / "parts").is_dir():
            continue
        digits = re.search(r"day-(\d+)", folder.name)
        if digits:
            found.append(int(digits.group(1)))
    return sorted(found)


def main(argv: list[str]) -> int:
    requested = [int(a) for a in argv if a.isdigit()]
    days = requested or written_days()
    if not days:
        print("no day has a parts/ directory yet - nothing to check")
        return 0

    reports = [check_day(d) for d in days]
    failed = [r for r in reports if not r.ok]

    for report in reports:
        if report.ok:
            print(f"OK   day {report.day:>3}  {report.parts} parts")
        else:
            print(f"FAIL day {report.day:>3}  {len(report.failures)} problems")
            for failure in report.failures:
                print(f"       - {failure}")

    print()
    if failed:
        print(f"depth contract: {len(reports) - len(failed)}/{len(reports)} days pass")
        return 1
    print(f"depth contract: all {len(reports)} checked days pass")
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    sys.exit(main(sys.argv[1:]))
