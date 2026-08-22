---
day: 90
phase: 14
phase_name: "Portfolio & handoff"
title: "Retrospective, and the standing habit"
ids: []
kind: gate
plan_version: "v1.1.0"
generated: "2026-08-21"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 90 — Retrospective, and the standing habit 🎯

**Phase 14 · Portfolio & handoff** · IDs: **—** · **Phase-14 gate · the last day**

> **Yesterday:** a README a stranger can run, a diagram in git, and eighty-eight interview answers
> harvested into one document.
> **Today:** three things. The **gate** — a stranger runs Mandala in under fifteen minutes, timed and
> recorded. The **retrospective** — an honest ledger of what ninety days produced and what it did not.
> And the **standing habit** — the weekly freshness check, scheduled somewhere that outlives this
> repo, because the ecosystem will move and the plan told you so on Day 1.
> **Tomorrow:** week 91. §6 is about that.

```bash
./m start 90
```

---

## §1 The story

There is a particular failure at the end of a long project: you finish, you feel good, you write
"learned a lot!" and close the laptop. Six weeks later the pins are stale, the free tiers have
rotated, one framework has renamed a class, and the repo you would show someone no longer runs.

The plan anticipated this on Day 1. Principle 13 is the standing weekly freshness check, and Part 5's
Day-90 entry says explicitly: *schedule the standing weekly freshness check beyond the plan; write
`02_MASTER_PLAN_ADDENDUM_*.md` if the ecosystem moved during the 90 days (it will).*

**It did.** You logged it: `langchain` drifted a minor on Day 1, `crewai` moved patches, the MCP spec
held at 2026-07-28. Ninety days of `CHANGELOG_PLAN.md` is a dataset about how fast this ground moves,
and today you read it as one.

Three jobs, in this order — **gate first, because it is the only one that can fail.**

---

## §2 The gate — the stranger test, for real

The Phase-14 criterion: **a stranger can run Mandala from the README in <15 minutes.**

Yesterday you ran it on yourself, which is the weakest possible version — you cannot un-know your own
setup. Today, do the strongest version available:

**Best:** hand the README to an actual person, watch silently, take notes, **do not help.** Every
time you want to say "oh, you also need to—", that is a README bug. Write it down instead of saying
it.

**Next best:** a clean VM or container.

```bash
docker run -it --rm -v "$PWD":/repo:ro python:3.12-slim bash
# inside: install uv, clone from the remote (not the mount), follow the README, timer running
```

**Note the `:ro` mount and the "clone from the remote".** A container that can see your working tree
will pick up your `.env`, your `.venv`, and your cached Playwright binary, and the test will pass for
the wrong reason. **The point is a machine that has never met your project.**

Record in `docs/adr/gate-phase-14.md`:

| | |
|---|---|
| Time to first offline test green | ____ |
| Time to first ticket run end-to-end | ____ |
| Blockers hit | ____ |
| README fixes made as a result | ____ |
| **Re-run time after fixes** | ____ |

**If the second run is over fifteen minutes, the gate fails and today is a README day.** That is a
legitimate outcome and it is better than a passed gate you fudged. The most common blockers, in
order: a missing `.env.example` variable, `playwright install` not mentioned, `uv.lock` uncommitted,
a Docker image pull nobody warned about, and a case-sensitive filename collision.

---

## §3 The retrospective — an honest ledger

`docs/RETROSPECTIVE.md`. Six sections, and the numbers come from files you already have.

### 3.1 What was built

Pull from the repo, not from memory:

```bash
uv run pytest --collect-only -q | tail -1          # test count
wc -l docs/*.md days/*/LESSON.md | tail -1         # written material
git log --oneline | wc -l                          # commits
grep -c "^| " docs/TRACEABILITY.md                 # IDs covered
uv run python scripts/daily_report.py              # today's cost picture
```

Then one table: phases completed, gates passed, IDs covered vs. the 138 in the plan. **Report IDs
honestly** — some are 🅿️ literacy rows where the deliverable was a paragraph, and saying so is more
credible than claiming 138/138 hands-on.

### 3.2 What the 90 days actually cost

From `docs/RATE_BUDGET.md`: total model requests, the most expensive day (Day 83, ~120), the cheapest
phase, cache hit rate, and **$0 in paid API spend**. Also: hours. Estimate honestly.

**The most interesting number is the ratio of deterministic to model-dependent verification.** Count
it: how many of your tests cost zero requests? If it is above 90%, say so — it is the single most
transferable engineering result in the project, and it is why the whole suite runs in CI for free.

### 3.3 What the ecosystem did in 90 days

Read `docs/CHANGELOG_PLAN.md` end to end and summarise:

- Which pins moved, and by how much (patch / minor / major).
- How many amendments you had to write (Principle 14).
- **What broke as a result** — and be specific. "LangChain drifted a minor and the `create_agent`
  signature changed" is a data point; "things moved fast" is not.
- The prediction worth recording: **at this rate, what is stale in three months?**

If anything material moved that you have not yet amended, **write
`docs/04_MASTER_PLAN_ADDENDUM_<topic>.md` today**, per the plan's own instruction. Amend first,
always — even on the last day.

### 3.4 What I would do differently

Be specific enough to be useful. Candidates from the actual arc of this repo:

- **The permission table should have been generated from day one**, not on Day 70. Sixty days of
  hand-maintained truth was luck.
- **Untrusted should have been a type on Day 3**, not Day 78. Every fence between them was a
  convention.
- **The eval markers should have predated the golden set.** You tiered tests seventy days after
  writing the first one.
- **The bake-off's cost-to-learn column** turned out to be the most decision-relevant one and you
  added it late.

**Each item needs "and here is how I would know to do it earlier next time."** Otherwise it is a
regret, not a lesson.

### 3.5 The honest limits — one consolidated list

You wrote a "what I would not deploy" section in four gate ADRs (Days 70, 77, 84, 88) and five
known-limit tests (Days 68, 69, 75, 78, 81). **Consolidate them here in one list**, each with the day
it was found and the test that asserts it. This is the section a senior engineer reads first, and
almost nobody has one.

### 3.6 What Mandala is not

Three sentences. Suggested: it is not autonomous; it is not multi-tenant or authenticated beyond a
shared key; it has never seen real customer data or a real support channel. **Say it plainly.** A
project that knows its own boundaries reads as finished; one that implies more than it does reads as
unfinished no matter how much is in it.

---

## §4 The standing habit

The plan's Principle 13 has to outlive the plan, and a `/freshness` skill in a repo you stop opening
is not a habit.

**Pick a mechanism that does not depend on your attention:**

| Option | Cost | Survives you forgetting? |
|---|---|---|
| GitHub Actions `schedule:` cron on your repo | free | **yes** |
| LangGraph Server cron (Day 86) | free, but only while the server runs | no |
| Calendar reminder | free | partly |

**Use the GitHub Actions cron.** It is free, it runs whether or not you open the laptop, and it can
open an issue.

```yaml
# .github/workflows/freshness.yml
name: freshness
on:
  schedule: [{cron: "0 9 * * 5"}]      # Fridays, 09:00 UTC — Principle 13
  workflow_dispatch:
permissions:
  contents: read
  issues: write
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: Compare pins against PyPI
        run: uv run python scripts/freshness_check.py --format=markdown > drift.md
      - name: Open an issue if anything moved
        if: ${{ hashFiles('drift.md') != '' }}
        uses: actions/github-script@v7
        with:
          script: |
            const body = require('fs').readFileSync('drift.md', 'utf8');
            if (body.trim().length > 0) {
              github.rest.issues.create({...context.repo, title: `Pin drift ${new Date().toISOString().slice(0,10)}`, body});
            }
```

**Line by line:**

- **`scripts/freshness_check.py` is a real script you write today**, not a prompt. It reads
  `docs/PINS.md`, queries PyPI, and prints a markdown table of differences. `/freshness` as a
  Claude skill is for *judgement* (is this material?); the script is for *detection*, and detection
  must be automatic.
- `permissions: issues: write`, and nothing else. Least privilege for a workflow that opens issues.
- **It opens an issue rather than emailing or failing.** An issue is durable, has a thread, and is
  visible to anyone who inherits the repo. A red CI badge on a scheduled job just gets ignored.
- `workflow_dispatch` so you can run it by hand the day before an interview.
- **Friday, matching Principle 13's own cadence.** Consistency with the plan you followed for ninety
  days is worth something.
- **What it deliberately does not do: update anything.** Detection opens an issue; a human decides
  whether it is material and whether it needs an addendum. Principle 14 survives automation.

---

## §5 Closing the tracker

```bash
uv run pytest -q                                    # everything
uv run python scripts/audit_writes.py
uv run python scripts/gen_permission_table.py --check
uv run python scripts/daily_report.py
./m status                                          # should read 90/90
git tag -a phase-14-complete -m "90 days"
git tag -a mandala-v1.0 -m "Mandala v1.0 — 90-day agentic AI curriculum, complete"
```

Then the last mechanical items:

- [ ] **Remove the DEV ONLY list** from Day 88's gate ADR, or convert each into a documented,
  clearly-labelled dev affordance. Do not leave them ambiguous.
- [ ] `docs/CURRICULUM_INDEX.md` shows ✅ for all 90 — via `./m done`, never by hand.
- [ ] `docs/TRACEABILITY.md` regenerated one final time.
- [ ] The final `CHANGELOG_PLAN.md` entry: `Day 90 complete — plan v1.1.0 finished`.
- [ ] **Cold-read `gate-phase-14.md` tomorrow and sign it.** The last gate gets the same treatment as
  the first four.

---

## §6 Week 91

The plan ends; the repo should not. Three concrete continuations, in order of value:

1. **Run the freshness issue queue for a month.** Four Fridays, four issues, four decisions
   (material / cosmetic / nil). That is the standing habit actually standing, and it is provable in
   your commit history — which is a much stronger signal than a finished project.
2. **Earn one autonomy level.** Day 84's rule needs 40 decisions over 28 days with zero rejections.
   Run tickets through Mandala for a month and see whether it qualifies. **Either answer is a good
   outcome**: a grant with evidence, or a written record of why it did not qualify. The second is
   rarer and more interesting.
3. **Replace one organ.** ADR-003's whole architecture claim is that organs are swappable. Swap the
   CrewAI researcher for a LangGraph subgraph and measure the delta on your existing eval suite. It
   is a weekend, it tests the claim, and it produces a fourth ADR.

**Do not start a new 90-day plan.** The value now is in depth on this one — a project you have run
for six months with a maintenance record is worth more than two projects you finished and abandoned.

---

## §7 Traps

- **Closing the laptop on Day 90.** Six weeks later it does not run.
- **Testing the stranger path on your own machine.** You cannot un-know your setup.
- **A container mounted read-write on your working tree.** Passes for the wrong reason.
- **Helping the human tester.** Every urge to help is a README bug.
- **Fudging a failed gate.** A README day is a legitimate Day 90.
- **Claiming 138/138 IDs.** Separate hands-on from literacy.
- **"Learned a lot" as a retrospective.** Numbers, from files.
- **Regrets without "how I would notice earlier".**
- **A freshness habit that needs you to remember.** Cron it.
- **A freshness job that auto-updates pins.** Detection is automatic; judgement is not.
- **Leaving DEV ONLY items ambiguous.**
- **Skipping the final cold read** because it is the last day.
- **Starting a new 90-day plan tomorrow.**

---

## §8 Request budget

**Declared: ~0–5 model requests.**

| What | Requests |
|---|---|
| Gate, retrospective, freshness workflow | **0** |
| Any final demo re-recording | ≤ 5 |

**Then compute the 90-day total** from `docs/RATE_BUDGET.md` and put it in the retrospective beside
the `$0` figure. Ninety days of agentic AI development, four frameworks, a distributed local
deployment, a red-team suite and a capstone, for **zero dollars** — that number is the headline of the
whole project and today is the day it becomes final.

---

## §9 Verify before you code

Written **2026-08-21**:

- **GitHub Actions `schedule:` reliability** — scheduled runs can be delayed or skipped on free tiers,
  and are disabled after 60 days of repo inactivity. **That last one matters**: note it in the
  retrospective, since the habit dies quietly if you stop committing.
- **`actions/github-script@v7`** current major, and the exact `issues.create` call shape.
- **`hashFiles()` on a file that exists but is empty** — confirm your `if:` condition behaves; the
  script's own emptiness check is the reliable guard.
- **PyPI JSON API rate limits** for `freshness_check.py` — you query ~15 packages weekly, which is
  fine, but confirm.
- **Does `./m status` handle 90/90** without an off-by-one? Day 0 exists, so 91 rows.
- **Final `/freshness` sweep**, nil reports included. Last one inside the plan; the first automated
  one runs Friday.

---

## §10 Say it in an interview

> "The last day was three things: the handoff gate, the retrospective, and making the maintenance
> habit survive me. The gate was a timed stranger test — not on my machine, because you can't un-know
> your own setup, but in a clean container cloning from the remote, and ideally with an actual person
> where every urge I had to say 'oh, you also need to—' was a README bug I wrote down instead of
> saying. The retrospective is numbers pulled from files rather than impressions: total requests,
> zero dollars of paid API spend across ninety days, and the ratio I care about most — over ninety
> percent of my tests cost zero model requests, which is why the whole suite including the red team
> runs on every commit for free. It also has a consolidated honest-limits list: four gate ADRs each
> ended with 'what I would not deploy', and five tests assert the limits of my own controls, so
> they're in one place with the day each was found. And the standing habit is a scheduled GitHub
> Action, not a calendar reminder — it compares my pins against PyPI every Friday and opens an issue
> if anything moved. Deliberately it doesn't update anything: detection is automatic, judgement isn't,
> because deciding whether a minor bump is material is exactly the thing that needs a person. What I
> would do differently is mostly about ordering — the permission table should have been generated from
> code on day one rather than day seventy, and untrusted text should have been a type from the start
> rather than a convention I formalised in week twelve."

---

## §11 Done when

```bash
./m check
./m done 90
```

Ninety days. **Cold-read `docs/adr/gate-phase-14.md` tomorrow and sign it** — same discipline as the
first gate, on the last day.

Then open the freshness issue on Friday.
