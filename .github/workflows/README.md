# .github/workflows/ - you write this on Day 2

Nothing is pre-written here, on purpose (see `days/README.md`, rule 1).

`days/day-02/LESSON.md` contains the full `check.yml`, line by line, with an explanation of why
every step is there - including the one line that keeps CI free forever:

```yaml
run: uv run python -m pytest -q -m "not live"
```

CI runs only the offline tests. No key is present in CI, no test asks for one, and no build can
spend a free-tier quota (Principle 5). A red build therefore always means you broke something.

The v1.1.0 workflow is archived at `legacy/check.yml` - reference material to mine, not structure
to copy.
