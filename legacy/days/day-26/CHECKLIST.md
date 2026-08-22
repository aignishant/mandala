# Day 26 — CHECKLIST

**IDs covered:** CR-07 🛠️ (structured task output), CR-08 🛠️ (memory system)

## Demo command

```bash
uv run python days/day-26/lab/typed_output.py T-1004
uv run python days/day-26/lab/memory_across_runs.py --wipe    # run 1, clean slate
uv run python days/day-26/lab/memory_across_runs.py           # run 2, same store
grep -ril "PINEAPPLE-7731" .mandala/crew_memory/ || echo "canary not found"
```

## Setup

- [ ] `./m start 26` and `./m scaffold 26` run
- [ ] `uv add "sentence-transformers==6.0.0"` — **pulled forward from Day 46**; read the ledger
      amendment in `docs/CHANGELOG_PLAN.md` and agree with it (or overrule it)
- [ ] Understood the distinction: the **dependency** moves early, the **teaching** stays on Day 46
- [ ] `.mandala/crew_memory/` gitignored **before** the first memory run
- [ ] Considered gitignoring `.mandala/` wholesale — third time this rule has come up
- [ ] Files created (`crew/memory.py`, two lab files, two test files)

## CR-07 — typed task output

- [ ] `TriageResult` imported from `mandala.schemas` **unchanged** — no CrewAI-flavoured copy
- [ ] Can recite the four-spellings table (Day 4 / Day 11 / today / Day 38)
- [ ] `expected_output` **kept** alongside `output_pydantic` — can say why both are needed
- [ ] `out.pydantic` attribute confirmed for 1.15.17
- [ ] Printed `out.pydantic` and `out.raw` side by side
- [ ] `isinstance` checked rather than assumed
- [ ] **Confirmed what happens when validation fails** — retry, fall back to raw, or raise?

## What typing did NOT fix (§3.3)

- [ ] Constructed a valid `TriageResult` containing the canary, and saw it validate
- [ ] Can recite which rows of the table typing fixed and which it did not
- [ ] `TriageResult` list fields carry `max_length` — **added the bounds if missing**
- [ ] Bake-off entry **updated, not deleted**: "Day 26: seam typed; content still prompt-enforced"

## CR-08 — memory

- [ ] Can name the three memories and their lifetimes
- [ ] `free_embedder()` written (the TODO(me)) — **provider string sourced and noted where from**
- [ ] `EMBED_MODEL` pinned; understands the **silent** failure of changing it without a wipe
- [ ] `assert_free()` rejects paid providers **and** an unset one
- [ ] Memory enabled from exactly **one** call site (`memory_kwargs`) — `grep` proves it
- [ ] `wipe()` works and was actually used
- [ ] Chose sentence-transformers over Ollama and can say why (a gate must not depend on an optional part)

## The recall experiment (§4.3)

- [ ] Confirmed which fixture ids share a customer — **or added the linkage** to `tickets.json`
- [ ] Run 1 with `--wipe` (clean slate), run 2 without
- [ ] Run 2 `RECALLED:` line: **_______________**
- [ ] Recall observed? **yes / no** — and understood the self-report is weak evidence

## Read the store (§4.4) — do not skip

- [ ] `find .mandala/crew_memory -type f` — looked at what is actually there
- [ ] Grepped for the canary: found? **yes / no**
- [ ] **Retention** — how long does it keep this? **_______________**
- [ ] **Scope** — could a fact from customer A surface on customer B's ticket? **_______________**
- [ ] **Deletion** — what exactly would I delete if asked to forget a customer? **_______________**
- [ ] "I don't know yet" written where true — Day 65 and Day 70 come back for these
- [ ] Noticed that memory is a **new route** to Day 12's `no_other_customers` guardrail

## What memory costs (§4.5)

- [ ] Embedding calls: **0** — verified local, no API
- [ ] Noticed prompts got longer (retrieved context) — Day 4's budget
- [ ] **Understood memory is a hidden input**: runs are no longer reproducible from their inputs
- [ ] Memory left **off** in every test that is not about memory

## Tests that must be able to fail

- [ ] `test_the_schema_is_the_day_4_one`
- [ ] `test_literal_fields_still_reject_free_text`
- [ ] `test_list_fields_are_length_bounded`
- [ ] `test_a_valid_object_can_still_carry_the_canary` — **flip it:** try to fix it with a tighter
      schema, and understand why you cannot
- [ ] `test_memory_is_off_by_default` — the fifth "safe value is the default"
- [ ] `test_a_paid_embedder_is_refused` — **flip it:** remove `assert_free`
- [ ] `test_an_unset_provider_is_refused`
- [ ] `test_the_ollama_alternative_is_also_free`
- [ ] `test_enabling_memory_produces_a_free_embedder`
- [ ] `test_the_store_is_gitignored`
- [ ] `test_wipe_actually_removes_it`
- [ ] `test_the_canary_never_reaches_the_memory_store` — ships **skipped**; write it first tomorrow
- [ ] `autouse` wipe fixture present — the safe state is automatic, not remembered
- [ ] Every test costs **0 model requests**

## Understanding check — answer out loud

- [ ] What did `output_pydantic` fix, and what did it not?
- [ ] Why keep `expected_output` when the schema already constrains the output?
- [ ] Why is an **unset** embedder provider more dangerous than a wrong one?
- [ ] Why does changing the embedding model break retrieval without any error?
- [ ] What are the three questions memory raises that no tutorial covers?
- [ ] Why does memory break reproducibility in a way `temperature=0.0` cannot fix?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~54, Groq; 0 embedding calls)
- [ ] Embedder provider string verified from CrewAI source or docs
- [ ] Memory types and on-disk locations confirmed for 1.15.17
- [ ] Investigated what the **pluggable memory backend** offers — it may beat the embedder config
- [ ] `task_output.pydantic` name and validation-failure behaviour confirmed
- [ ] **Checked `chromadb` version pulled by crewai against the Day-46 pin** — a conflict is a real
      amendment, not a warning to ignore
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 26
```

- [ ] `./m done 26` succeeded — trackers updated automatically
