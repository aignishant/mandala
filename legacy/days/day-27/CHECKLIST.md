# Day 27 — CHECKLIST

**IDs covered:** CR-09 🛠️ (knowledge sources), CR-10 🛠️ (guardrails & task validation)

## Demo command

```bash
uv run python days/day-27/lab/knowledge_crew.py            # knowledge ON
uv run python days/day-27/lab/knowledge_crew.py --without  # the control
uv run python days/day-27/lab/guardrail_demo.py --off      # Day 24 behaviour, 4 runs
uv run python days/day-27/lab/guardrail_demo.py            # guarded, 4 runs
```

## Setup

- [ ] `./m start 27` and `./m scaffold 27` run
- [ ] No new packages — Day 26's embedder serves both memory and knowledge
- [ ] **Promoted the rule:** `.mandala/` gitignored wholesale, the four specific lines deleted
- [ ] Files created (`crew/knowledge.py`, `crew/guardrails.py`, two lab files, two test files)

## CR-09 — knowledge sources

- [ ] Can recite the three-channels table (tools / knowledge / memory) and pick correctly
- [ ] Understands knowledge is the only channel **I** authored — and that authored ≠ trusted (Day 15)
- [ ] `handbook_sources()` written (the TODO(me)); import path and constructor confirmed for 1.15.17
- [ ] **Verified whether paths resolve relative to a `knowledge/` dir** — this fails silently
- [ ] Corpus is Day 15's `data/kb/` — **not a copy**
- [ ] Empty knowledge base **raises**; can say why silence is worse than a crash
- [ ] Underscore-prefixed files excluded (Day 15's `_poisoned.md`)
- [ ] `MAX_DOC_BYTES` enforced; `CHUNK_SIZE`/`CHUNK_OVERLAP` pinned not defaulted
- [ ] Embedder reused from `crew/memory.py` — **one Principle-5 door, not two**
- [ ] Decided crew-level vs agent-level knowledge, and justified the narrower option

## The knowledge control experiment (§3.3)

- [ ] Ran **both** with and without knowledge
- [ ] Question was discriminating — the answer is only in `data/kb/`, not in the ticket
- [ ] With knowledge: correct + cited? **___**
- [ ] Without knowledge: did it invent a policy? **___**
- [ ] `NO RULE FOUND` escape present — a model with no way to say "I don't know" invents policy

## CR-10 — task guardrails

- [ ] Can state the `(ok, payload)` contract and that the second element **is a prompt**
- [ ] `must_cite_a_ticket` — the plan's CR-10 example, implemented
- [ ] Rejection message names the rule, gives the format, and offers **two** ways out
- [ ] `must_not_quote_the_ticket` — Day 14's `assert_no_raw_ticket`, finally housed
- [ ] Understood why it must be a **closure** (no context parameter in the signature)
- [ ] `WINDOW = 40` carried over from Day 14 **with its justification**
- [ ] Decided whether `SecurityViolation` should subclass `PermissionDenied` (Day 21 chose to)
- [ ] `compose()` written (the TODO(me)) — **and the ordering/disclosure question answered**

## The payoff experiment (§4.3) — do not skip

- [ ] `guardrail_demo.py --off` × 4 — canary in research **___ / 4**, in reply **___ / 4**
- [ ] `guardrail_demo.py` guarded × 4 — canary in reply **must be 0 / 4**: **___ / 4**
- [ ] Runs blocked by the security guardrail: **___ / 4**
- [ ] If the guarded reply ever contained the canary, **found the hole before Day 29**
- [ ] Can state the comparison: a probabilistic defence replaced by a deterministic one
- [ ] **Bake-off gap crossed off with the date:** "Day 27: closed. Three days open."

## Retry is not always a kindness (§4.4)

- [ ] Can recite the quality-vs-security table
- [ ] Can give the three reasons never to retry a security failure, in order
- [ ] Can contrast with Day 12's SDK tripwires: more power means more decisions
- [ ] **Verified what CrewAI does with an exception raised inside a guardrail** — if it converts it
      to a retry, `must_not_quote_the_ticket` does not work and needs another mechanism

## Code before LLM guardrails (§4.5)

- [ ] Every guardrail written today is code — regex or substring, 0 cost, deterministic
- [ ] Can say why an LLM guardrail is a last resort on this project
- [ ] If one is ever used: it runs on `judge_llm()` (RATE_BUDGET rule 1), never `worker_llm()`
- [ ] Checked whether LLM guardrails even allow specifying the model

## Tests that must be able to fail

- [ ] `test_a_cited_answer_passes`
- [ ] `test_an_uncited_answer_is_rejected_with_usable_feedback`
- [ ] `test_quoting_the_ticket_raises_rather_than_rejecting` — **flip it:** return `(False, msg)`
      and watch a security control become a retry loop
- [ ] `test_an_honest_summary_passes_the_security_guardrail` — **the pair**
- [ ] `test_the_window_is_wide_enough_not_to_match_ordinary_english`
- [ ] `test_the_canary_specifically_cannot_pass` — also guards against fixture drift
- [ ] `test_composed_guardrails_do_not_disclose_which_check_tripped` — ships **skipped**
- [ ] `test_the_corpus_is_day_15s_and_not_a_copy`
- [ ] `test_an_empty_knowledge_base_is_loud`
- [ ] `test_underscore_files_are_not_indexed`
- [ ] `test_oversized_documents_are_refused`
- [ ] `test_knowledge_is_off_unless_asked`
- [ ] `test_knowledge_uses_the_free_embedder`
- [ ] Every test costs **0 model requests**

## Understanding check — answer out loud

- [ ] Which of the three channels should carry policy, and why?
- [ ] Why does one guardrail return and its neighbour raise?
- [ ] Why is guardrail feedback a prompt rather than an error message?
- [ ] Why is a silently empty knowledge index worse than a crash?
- [ ] Why does tightening `WINDOW` make the system less safe in practice?
- [ ] What did I gain and lose versus Day 12's SDK guardrails?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~99, Groq)
- [ ] Understood `max_retries=2` means **up to 3× the task cost** — the first multiplier set by kwarg
- [ ] Guardrail signature confirmed: string, `TaskOutput`, or parsed Pydantic object?
- [ ] `max_retries` kwarg name and location (task vs crew) confirmed
- [ ] Knowledge-source import path confirmed
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 27
```

- [ ] Bake-off list updated: mechanical seam check gained; retry-vs-raise decision now mine to make
- [ ] `./m done 27` succeeded — trackers updated automatically
