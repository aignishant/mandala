# Day 65 — CHECKLIST

**IDs covered:** AG-15 🛠️ (prompt injection), AG-16 🛠️ (the lethal trifecta)

## Demo command

```bash
uv run python days/day-65/lab/attack.py         # ~12 requests — run the full set ONCE
uv run pytest tests/test_trifecta.py tests/test_injection.py -v
cat docs/PERMISSIONS.md
```

## Scope

- [ ] Everything runs against **your own system, your own fixtures, a local server you wrote**
- [ ] No real customer data anywhere — "fixtures only, forever" (Day 1)

## Setup

- [ ] `./m start 65` and `./m scaffold 65` run
- [ ] No new packages
- [ ] `ticket-db` running and `build_core()` green **before** attacking
- [ ] Files created (`injections.json`, `trifecta.py`, two tests, `attack.py`, `findings.md`,
      `docs/PERMISSIONS.md`)

## AG-15 — the corpus

- [ ] **Twelve cases across four families** written
- [ ] Every case declares `family`, `targets` and `expected_defence`
- [ ] **`expected_defence` written BEFORE running** — predictions, not memories
- [ ] `inj-10` (the summary seam) honestly predicted, including "I expect this to work"
- [ ] Written as a **fixture**, not a scratch file — Day 74's CI will run it

## The attack

- [ ] `attack.py` checks **properties, not vibes**
- [ ] Every breach check corresponds to a guarantee built on a named day
- [ ] Full corpus run **once**; iterated only on the cases that landed
- [ ] `ticket_id` deliberately not a real fixture id
- [ ] Results recorded in `findings.md` with prediction vs. outcome

## The seam deferred since Day 31

- [ ] `inj-10` result recorded
- [ ] Answered: **was the three-time deferral justified, or was I hoping?**
- [ ] If it landed: fix chosen, and identified as **architectural**, not a prompt tweak
- [ ] `AgentProfile("researcher", untrusted_input=...)` **corrected to match reality**
- [ ] `docs/PERMISSIONS.md` "the seam that carries risk" section filled with the real result

## AG-16 — the trifecta

- [ ] Can name the three legs and why any two are survivable
- [ ] Can say why defence is **separation, not detection**
- [ ] `trifecta.py` written with **"can" meaning CAN, not "does today"**
- [ ] classifier: untrusted input, **no tools**
- [ ] researcher: private data, receives only the summary
- [ ] drafter: **zero legs, zero tools**
- [ ] poster (Day 82): write only, reads nothing — profiled **before** it exists
- [ ] `holds_two()` available for residual-risk reasoning

## `docs/PERMISSIONS.md`

- [ ] Table complete with a Legs column and a Tools column
- [ ] "No agent holds more than one leg" claim, and the test that asserts it
- [ ] **"What would break this table" written** — three plausible, well-intentioned changes

## Tests that must be able to fail

- [ ] `test_no_agent_holds_all_three_legs` — **flip it:** give the classifier a read tool, see red
- [ ] `test_no_agent_holds_private_data_and_untrusted_input` — the stricter pair
- [ ] `test_no_agent_holds_untrusted_input_and_write`
- [ ] `test_every_agent_has_a_note`
- [ ] `test_the_drafter_holds_nothing`
- [ ] `test_the_profile_matches_the_code` — the anti-drift test
- [ ] `test_the_corpus_covers_every_family`
- [ ] `test_every_case_declares_what_it_targets_and_expects`
- [ ] `test_structural_defences_hold[12 cases]`
- [ ] `test_no_injection_produced_cross_ticket_content`
- [ ] **Recorded fixtures written**, so CI costs 0 requests

## `findings.md` — the deliverable

- [ ] Prediction-vs-result table for all twelve
- [ ] For each breach: which property broke, and whether the fix is prompt / bound / architecture
- [ ] **Probabilistic vs. structural defence table filled**
- [ ] **Counted how many defences are structural**
- [ ] The sentence you will repeat for the rest of the project, written down

## Understanding check — answer out loud

- [ ] Why is checking properties better than checking outputs?
- [ ] Why can't you prompt your way out of injection?
- [ ] Why does "can" have to mean capability rather than behaviour?
- [ ] Which pair of legs is the exfiltration precondition, and why hold a stricter line than the
      trifecta requires?
- [ ] Which of your defences will fail eventually, and why?
- [ ] What would break the permission table, and who would propose it?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~15, Groq)
- [ ] **Recorded results written for replay** — an unaffordable suite is an unrun suite
- [ ] Structured-output-constrains-generation question (Day 38 §4.1) **answered**
- [ ] `<ticket>` delimiter confirmed still present after Phase 9
- [ ] One injection tried on **two providers** — is the defence model-dependent?
- [ ] `ResearchState` confirmed to still lack `ticket_body`
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 65
```

- [ ] `docs/PERMISSIONS.md` staged — it is the **Phase-10 gate artifact** (Day 70 publishes it)
- [ ] `./m done 65` succeeded — trackers updated automatically
