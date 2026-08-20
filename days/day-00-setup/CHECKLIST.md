# Day 0 — Setup — CHECKLIST

**Not one of the 90 days.** This is the half-day that makes Day 1 start cleanly.

## Verify command

```bash
python --version                                          # must print 3.12.x
uv run python -c "import mandala; print('import OK')"     # must print: import OK
./m status                                                # the dashboard, at 0%
./m check-ids                                             # 138 IDs agree
git log --oneline -1                                      # your day-00 commit
```

## Toolchain

- [ ] Git Bash opened, and `pwd` shows the project folder
- [ ] `python --version` prints **3.12.x** (not 3.11, not 3.13)
- [ ] `uv --version` works
- [ ] `git --version` works
- [ ] `git config user.name` and `user.email` are set
- [ ] Noted that **Docker Desktop is needed by Day 19** (not today)
- [ ] Noted that **Ollama is optional** (offline fallback, first useful Day 6)

## Skeleton

- [ ] `src/mandala/` created, with an empty `__init__.py`
- [ ] `tests/fixtures/cassettes/` created
- [ ] `tests/__init__.py` created
- [ ] `scripts/` created
- [ ] `docs/adr/` created
- [ ] `.github/workflows/` created
- [ ] `find . -type d -not -path './.git*' | sort` matches the expected tree in §3

## Project file

- [ ] `pyproject.toml` created, and you can explain **every line** of it
- [ ] `requires-python = "==3.12.*"` — a hard pin, not `>=`
- [ ] `dependencies = []` — empty on purpose; packages get added the day they are first needed
- [ ] `uv venv --python 3.12` run
- [ ] `uv pip install -e .` run
- [ ] `uv run python -c "import mandala"` succeeds

## Git hygiene

- [ ] `.gitignore` created **before** any `.env` exists
- [ ] `.env` is the first line of `.gitignore`
- [ ] `git status` shows no `.venv/` or `__pycache__/` noise

## The tracker (`TRACKER.md`)

- [ ] Read all 8 explained chunks — not just pasted §9
- [ ] `scripts/mandala.py` created
- [ ] `./m` wrapper created and `chmod +x`-ed
- [ ] `uv run python scripts/mandala.py --help` prints the 7 subcommands
- [ ] `./m status` prints the progress bar at 0/90
- [ ] `./m sync` reports `synced 90 days`
- [ ] `./m check-ids` reports `✓ all 138 declared IDs agree`

## Understanding check — answer these out loud before moving on

- [ ] Why does `ROOT = Path(__file__).resolve().parent.parent` make the script location-independent?
- [ ] Why is `<<'PYEOF'` quoted, and what would break if it were `<<PYEOF`?
- [ ] Why does `git status --porcelain` get used as a condition?
- [ ] Why is an ID only marked covered when **every** day teaching it is done?
- [ ] Why does `./m check` never pass `-m live`?

## Commit

- [ ] Committed — `day-00: setup — toolchain, skeleton, tracker`
- [ ] `./m status` shows Day 1 as "next up"

**Next:** `./m start 1`
