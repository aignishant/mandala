# Day 69 — CHECKLIST

**IDs covered:** — (consumes AG-15…AG-19 and MCP-15; produces `docs/REDTEAM.md`, a Phase-10 gate artifact)

## Demo command

```bash
uv run python days/day-68/lab/serve_site.py &        # RT-11 needs the dummy site
uv run python days/day-69/lab/run_redteam.py         # writes docs/REDTEAM.md
uv run pytest tests/test_redteam.py -v               # xfails are expected TODAY
git grep MANDALA_CANARY -- ':!src/mandala/redteam'   # must return nothing
```

Expected: twelve rows printed with ✅/⏸/❌; `docs/REDTEAM.md` written; the pytest run shows
`xfailed` for every attack in `BREACHED_TODAY` and `passed` for the rest — **zero unexpected passes.**

## Setup

- [ ] `./m start 69` and `./m scaffold 69` run
- [ ] **No new dependencies added** — and can say why that is a good sign
- [ ] `src/mandala/redteam/` created
- [ ] All files written with explicit `encoding="utf-8"` (RT-03 is Cyrillic)
- [ ] Yesterday's dummy site still serves on `127.0.0.1:8731`
- [ ] Confirmed every attack targets **your own repo / localhost / your own keys** — no exceptions

## The threat model

- [ ] The twelve-row entry-point table printed and pinned somewhere visible
- [ ] Can say why it is organised by **entry point** rather than by attack technique
- [ ] Can state the one sentence every real incident reduces to (Day 8's trifecta)
- [ ] Can name, for each entry point, which day built the control

## The corpus (§3.1)

- [ ] `corpus.py` written with attacks as **data**
- [ ] Every attack has a non-empty `wins_if` **written before the attack was run**
- [ ] Every attack names the `control` it should hit, and the day that built it
- [ ] RT-03's payload pasted into a REPL — `len()` and `.encode()` inspected, confusables identified
- [ ] Decision recorded: normalise at intake, or not, and why

## The detector (§3.2)

- [ ] `CANARY` planted inside **private context**, not inside the attack payload
- [ ] `exfiltration_urls` separated from plain `leaked` — and can say why URLs are worse
- [ ] The canary's blind spot (paraphrase) written into `docs/REDTEAM.md`
- [ ] `git grep MANDALA_CANARY` run before commit — clean outside `redteam/`

## The harness (§3.3)

- [ ] `judge` is **deterministic** — no model anywhere in the judging path
- [ ] Three verdicts implemented: `held` / `gated` / `breached` (+ `error`)
- [ ] URL exfiltration checked **before** plain leakage
- [ ] `requests` threaded through every row so RT-12 uses the same judge

## The run (§4)

- [ ] `run_one` implemented — every attack wired to the real seam it enters through
- [ ] Any attack that was **hard to wire** recorded as a finding in its own right
- [ ] RT-10 and RT-11 run first (0 requests)
- [ ] RT-08 run as **two** runs — poison, then a clean follow-up ticket
- [ ] RT-09 run across **two** connects, or honestly marked `error`
- [ ] **Nothing fixed today** — findings only
- [ ] `docs/REDTEAM.md` written, with the control column beside every verdict
- [ ] `days/day-69/lab/findings.md` holds the raw transcripts

## Tests that must be able to fail

- [ ] `test_the_corpus_covers_every_entry_point` — completeness of the threat model
- [ ] `test_every_attack_declares_a_machine_checkable_win_condition`
- [ ] `test_attack_ids_are_unique`
- [ ] `test_the_canary_detects_a_plain_leak`
- [ ] `test_the_canary_detects_url_exfiltration_specifically`
- [ ] `test_a_paraphrased_leak_is_NOT_detected` — **asserts the blind spot on purpose**
- [ ] `test_gated_is_not_counted_as_held`
- [ ] `test_quota_attack_is_judged_on_requests_not_text`
- [ ] `test_attack_does_not_succeed[RT-01…RT-12]` — parametrised, IDs render as `[RT-05]`
- [ ] `test_no_agent_holds_the_lethal_trifecta`
- [ ] `BREACHED_TODAY` filled in from **your own run**, not guessed
- [ ] `xfail` confirmed **strict** — a silently-passing xfail would defeat the whole file

## Understanding check — answer out loud

- [ ] Why is "the model said something bad" a weaker finding than "a write happened"?
- [ ] Why must `wins_if` be written before the attack runs?
- [ ] Why not use an LLM to judge the red team?
- [ ] What is the difference between `gated` and `held`, and when does `gated` become `breached`?
- [ ] Why is RT-08 (memory poisoning) the highest-severity class in the corpus?
- [ ] Why is RT-09 untestable in a single session, and what does that force the control to be?
- [ ] What does `xfail(strict=True)` protect against that a TODO comment does not?

## Budget & freshness

- [ ] Actual total request count logged in `docs/RATE_BUDGET.md` (declared: ~40)
- [ ] Compared honestly against the declaration — **an over-budget red team is itself RT-12 succeeding**
- [ ] 429 behaviour observed during the burst; noted whether the router rotated and whether the
      trace recorded which provider answered
- [ ] `pytest.xfail()` vs `@mark.xfail(strict=True)` semantics confirmed on pytest 9.1.1
- [ ] Parametrised `ids=` rendering confirmed
- [ ] MCP client caching of tool descriptions confirmed (decides tomorrow's RT-09 fix)
- [ ] Docker resource limits re-confirmed **on this machine**
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 69
```

- [ ] `docs/REDTEAM.md` committed
- [ ] Attack corpus committed **with** the scorecard beside it for context
- [ ] Canary not present anywhere outside `src/mandala/redteam/`
- [ ] `./m done 69` succeeded — trackers updated automatically
