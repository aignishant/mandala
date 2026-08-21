# Day 89 — CHECKLIST

**IDs covered:** — (Phase 14: README-as-portfolio, architecture diagram, demo video, interview Q&A)

## Demo command

```bash
cd /tmp && rm -rf mandala-stranger && git clone <repo> mandala-stranger && cd mandala-stranger
# timer on — follow ONLY the README
uv run pytest tests/test_readme.py -v
```

Expected: a clean clone reaches a running ticket in **under 15 minutes**, and every README test green.

## The stranger test — do this BEFORE writing

- [ ] Fresh clone into `/tmp`, nothing reused from your dev machine
- [ ] **Timer started**; followed only what the current README says
- [ ] Every out-of-repo assumption written into `days/day-89/lab/stranger_test.md`
      (`.env` values, browser binary, Docker images, Python version, `uv` install…)
- [ ] Time recorded, honestly, including the failures
- [ ] Repeated after the rewrite — **second run under 15 minutes**

## Above the fold (90 seconds)

- [ ] One-line description names the **pipeline**, not the frameworks
- [ ] "$0 of paid API spend" stated up front
- [ ] Diagram appears **before** prose
- [ ] Three-claim table with an **evidence link and a verify command** per row
- [ ] **"Not autonomous, on purpose" paragraph is above the fold**, linked to the autonomy review
- [ ] Nothing in this section is unfalsifiable

## Quick start (15 minutes)

- [ ] Requirements listed, with **which are optional**
- [ ] Only **one** free key required
- [ ] **An offline verification step runs before any key is needed**
- [ ] Timings given for slow steps
- [ ] Docker and Playwright moved to an "optional demos" subsection, off the critical path
- [ ] Every step from the stranger test present, including the ugly ones
- [ ] `.env.example` complete and minimal (names diffed against your real `.env`; no values)
- [ ] `uv.lock` committed

## Below the fold (4 hours)

- [ ] Architecture (3 paragraphs + link)
- [ ] Why these frameworks — links to ADR-003 and the Phase-9 scorecard
- [ ] Safety model, each claim linked to its test
- [ ] Evals: three layers, what runs free in CI, **the judge's actual kappa**
- [ ] **"What I would not deploy"**, harvested from four gate ADRs
- [ ] **Known limits section listing the five known-limit tests by name**
- [ ] Cost: real numbers from `RATE_BUDGET.md`, including the 90-day total
- [ ] Repo map table

## The diagram

- [ ] Mermaid **in git**, not an exported binary
- [ ] Renders on GitHub — checked both standalone and embedded
- [ ] **Exactly one write box**, visually distinct
- [ ] The approval gate is the **only** path to it
- [ ] Checkpointer shown as where state lives
- [ ] First edge labelled `Untrusted`

## Interview Q&A + demo

- [ ] `docs/INTERVIEW_QA.md` **harvested** from 88 "§ Say it in an interview" paragraphs — no new
      content written
- [ ] Grouped into the six themes
- [ ] Each answer cut to ~150 words / 60 seconds spoken
- [ ] Each answer notes **the one artifact you would show**
- [ ] The "what would you not deploy" group rehearsed most
- [ ] `demo_script.md` written: 5 shots, 3 minutes
- [ ] **Demo shows a refusal, not just the happy path**
- [ ] Recording produced, under 25 MB

## Tests that must be able to fail

- [ ] `test_every_internal_link_resolves` — **flip it:** skip it, ship broken links
- [ ] `test_every_claim_in_the_table_has_a_verify_command`
- [ ] `test_the_quick_start_runs_something_offline_before_any_key_is_needed`
- [ ] `test_the_readme_states_what_is_not_deployed`
- [ ] `test_the_readme_does_not_claim_autonomy_it_does_not_have` — couples marketing to code
- [ ] `test_no_secrets_in_the_readme`
- [ ] `test_dev_only_items_are_not_presented_as_features`
- [ ] `test_the_architecture_diagram_is_in_git_not_a_binary`
- [ ] `test_the_diagram_shows_exactly_one_write`
- [ ] `test_the_interview_doc_covers_every_phase_gate`
- [ ] All cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why can't you write setup instructions without the stranger test?
- [ ] Why does every claim need a verify command?
- [ ] Why is the not-autonomous paragraph above the fold rather than hidden?
- [ ] What does an offline first step buy a stranger?
- [ ] Why Mermaid rather than an exported image?
- [ ] Which single artifact would you show if someone said "prove the safety claim"?

## Budget & freshness

- [ ] Request count logged in `docs/RATE_BUDGET.md` (declared: ~10, demo only)
- [ ] **Stranger-test time (minutes) recorded** — tomorrow's gate criterion
- [ ] GitHub Mermaid rendering confirmed in both contexts
- [ ] `uv sync` timed on a cold cache
- [ ] Case-collision check run (`git ls-files | sort -f | uniq -di`)
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 89
```

- [ ] README, architecture doc, diagram source, interview Q&A committed
- [ ] `git grep` for key-shaped strings across the repo — clean
- [ ] `./m done 89` succeeded
