# Day 41 — CHECKLIST

**IDs covered:** LC-11 🅿️ (RAG in 1.x, scoped honestly), LC-12 🅿️ (Deep Agents)

## Demo command

```bash
uv run python days/day-41/lab/deep_agent_demo.py   # <= 15 requests — ONCE
uv run pytest tests/test_scope.py -v
cat days/day-41/lab/rag_scope.md days/day-41/lab/harness_compare.md
```

**A 🅿️ day's deliverable is two written decisions.** The code is the evidence.

## Setup

- [ ] `./m start 41` and `./m scaffold 41` run
- [ ] `deepagents` version verified live **before** `uv add`
- [ ] Pinned exactly; ledger row and changelog line written
- [ ] Noticed `0.x` means minor bumps can break the API — and drew a conclusion from it
- [ ] **Nothing installed for LC-11** — and can say why that absence is the deliverable
- [ ] Files created (two markdown, one script, `tests/test_scope.py`)

## LC-11 — the retrieval scope

- [ ] Can fill in the six-row table of what LangChain offers vs. Mandala's answer
- [ ] Can give all three reasons **in the right order** — and knows why "cheaper" is the weakest
- [ ] Can explain the loader-as-parser blast-radius argument (Day 65, MCP-15)
- [ ] Can state reason 3 as an engineer would: interface first, implementation deferred
- [ ] `rag_scope.md` written
- [ ] **"What would change my mind" column filled for every excluded row**
- [ ] **The Day-46 measurement decided today**, not on Day 46
- [ ] Day 15's `kb.search(query, k)` interface confirmed unchanged

## LC-12 — Deep Agents

- [ ] Can map all four capabilities back to IDs you already learned
- [ ] Understood the framing: a *packaging* of four known ideas, not four new ones
- [ ] Connected it to **OAI-18** — the paid harness you could only read about on Day 19
- [ ] `deep_agent_demo.py` run **once**
- [ ] Model pinned explicitly — the harness did not choose a provider for you
- [ ] Tools limited to `READ_TOOLS` — blast radius not relaxed for a harness
- [ ] **`AIMessage` count recorded** — that is the request count
- [ ] Compared against Day 38's plain agent on a comparable task; ratio computed
- [ ] Read the final output and judged **honestly** whether the plan beat no plan

## §4.3 — where the seam would go

- [ ] Could name the branch it would attach to, and why only that one
- [ ] Could name the file it would hide behind, and why a `0.x` dep needs one
- [ ] Could say why its filesystem must be a sandbox, not the repo
- [ ] Recognised this as the **third** appearance of the same boundary pattern

## `harness_compare.md`

- [ ] Table filled, including turn counts and the ratio
- [ ] Answered: was the plan better than no plan on this task?
- [ ] Answered: what shape of task would make a harness earn its turns?
- [ ] **Day 19's explainer revisited and corrected** — the highest-value half-hour of the day

## Tests that must be able to fail

- [ ] `test_no_rag_infrastructure_crept_in` — **flip it:** `uv add chromadb`, see red
- [ ] `test_no_hosted_embedding_package`
- [ ] `test_deepagents_is_pinned_exactly`
- [ ] `test_deepagents_is_not_wired_into_src` — designed to fail on the day you adopt it
- [ ] `test_the_scope_documents_exist_and_are_filled_in` — **and its weakness stated out loud**
- [ ] `test_the_retrieval_interface_has_not_drifted`
- [ ] All tests cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why is a 🅿️ day not an optional day in this plan?
- [ ] Give the three RAG-scoping reasons in order, strongest last-said-first
- [ ] What makes a scoping decision defensible rather than merely firm?
- [ ] Which four already-learned ideas does a harness package together?
- [ ] What did planning cost you, in turns, on a real task?
- [ ] Why does a `0.x` dependency belong behind a named function?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~15, Groq)
- [ ] Logged against Day 38's count so the ratio is recoverable
- [ ] `deepagents` version and `create_deep_agent` signature confirmed
- [ ] Default sandbox backend location established **before** running it in the repo
- [ ] Whether it defaults to a model if `model=` is omitted — checked; hazard noted if so
- [ ] Whether subagents inherit your tools or a superset — checked, noted for Day 66
- [ ] LangChain retrieval docs skimmed; §3.1's split confirmed still accurate
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 41
```

- [ ] Bake-off rows updated: **harness availability on $0** and **retrieval story**
- [ ] `./m done 41` succeeded — trackers updated automatically
