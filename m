#!/usr/bin/env bash
# Project Mandala daily driver. Replaces `make` (not installed on Windows).
set -euo pipefail

DAY="${2:-}"
pad() { printf "%02d" "$1"; }

daydir() {
  local n="$1"
  if [ -d "days/day-$(pad "$n")" ]; then echo "days/day-$(pad "$n")"
  elif [ -d "days/day-$n" ]; then echo "days/day-$n"
  elif [ "$n" = "0" ] && [ -d "days/day-00-setup" ]; then echo "days/day-00-setup"
  else echo ""; fi
}

case "${1:-help}" in
  start)
    [ -z "$DAY" ] && { echo "usage: ./m start <day>"; exit 1; }
    D="$(daydir "$DAY")"
    [ -n "$D" ] || { echo "no day folder for day $DAY - see docs/TRACKER.md"; exit 1; }
    if [ -f "$D/LESSON.md" ] && [ -d "$D/parts" ]; then
      echo "-> open $D/LESSON.md   (the hub - read its §2 map, then work through parts/ in order)"
      find "$D/parts" -name '*.md' | sort | sed "s|^$D/|     |"
    elif [ -f "legacy/days/day-$(pad "$DAY")/LESSON.md" ]; then
      echo "!! day $DAY is not written yet in the v2.0.0 shape (plan Part 11)."
      echo "-> the v1.1.0 lesson is at legacy/days/day-$(pad "$DAY")/LESSON.md - reference only."
      echo "-> regenerate it with:  /day $DAY"
      exit 1
    else
      echo "no lesson written yet for day $DAY - see docs/TRACKER.md"; exit 1
    fi
    ;;

  parts)
    [ -z "$DAY" ] && { echo "usage: ./m parts <day>"; exit 1; }
    D="$(daydir "$DAY")"
    [ -d "$D/parts" ] || { echo "day $DAY has no parts/ - it is not written (plan Part 11)"; exit 1; }
    find "$D/parts" -name '*.md' | sort | sed "s|^$D/parts/||"
    ;;

  depth)
    if [ -n "$DAY" ]; then uv run python scripts/depth_check.py "$DAY"
    else uv run python scripts/depth_check.py; fi
    ;;

  scaffold)
    [ -z "$DAY" ] && { echo "usage: ./m scaffold <day>"; exit 1; }
    D="$(daydir "$DAY")"
    [ -n "$D" ] || D="days/day-$(pad "$DAY")"
    mkdir -p "$D/lab"
    echo "-> created $D/lab"
    ;;

  check)
    uv run ruff check .
    uv run ruff format --check .
    rc=0
    uv run python -m pytest -q -m "not live" || rc=$?
    if [ "$rc" -eq 5 ]; then
      echo "   (pytest collected no tests yet - expected until the first lab writes one)"
    elif [ "$rc" -ne 0 ]; then
      echo "FAIL pytest exited $rc"; exit "$rc"
    fi
    uv run python scripts/depth_check.py
    echo "OK all green"
    ;;

  tracker)
    uv run python scripts/tracker.py
    ;;

  status)
    uv run python scripts/tracker.py --summary
    ;;

  done)
    [ -z "$DAY" ] && { echo "usage: ./m done <day>"; exit 1; }
    D="$(daydir "$DAY")"
    [ -n "$D" ] || { echo "no day folder for $DAY"; exit 1; }
    C="$D/CHECKLIST.md"
    [ -f "$C" ] || { echo "FAIL no $C"; exit 1; }
    if grep -q '^- \[ \]' "$C"; then
      echo "FAIL unticked boxes remain in $C"; grep -n '^- \[ \]' "$C"; exit 1
    fi
    "$0" check
    uv run python scripts/tracker.py
    git add -A && git commit -m "day-$(pad "$DAY"): complete"
    echo "OK day $DAY committed"
    ;;

  *)
    cat <<'USAGE'
usage: ./m <command> [day]

  status         how many days are written / complete
  tracker        regenerate docs/TRACKER.md
  start N        point at day N's hub and list its parts/
  parts N        list day N's sub-topic documents
  depth [N]      check day N (or every written day) against the plan's Part 11 depth contract
  scaffold N     create days/day-NN/lab/
  check          ruff + ruff format + offline pytest + the depth contract
  done N         refuse unless the checklist is ticked and checks are green, then commit
USAGE
    ;;
esac
