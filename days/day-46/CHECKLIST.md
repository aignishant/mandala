# Day 46 — CHECKLIST

**IDs covered:** AG-13 🛠️ (retrieval & embeddings — the honest RAG day), AG-14 🅿️ (fine-tuning vs.
RAG vs. prompting)

## Demo command

```bash
uv run python days/day-46/lab/chunk_inspect.py       # 0 requests — do not skip
uv run python days/day-46/lab/bakeoff_retrieval.py   # 0 requests — the deliverable
uv run pytest tests/test_index.py tests/test_retrieval_quality.py -v
```

Expected: a chunk size distribution, a per-query keyword-vs-embeddings table, and a recall floor that
holds.

## Setup

- [ ] `./m start 46` and `./m scaffold 46` run
- [ ] `numpy` version verified live, then pinned; ledger row + changelog line
- [ ] `sentence-transformers==6.0.0` confirmed present from Day 26
- [ ] Model downloaded **before** starting the lab (one-time, not a model request)
- [ ] Model cache location checked and **not inside the repo** (or git-ignored)
- [ ] No vector database installed — Day 41's test still green
- [ ] Files created (`index.py`, two test files, three lab files)

## Chunking

- [ ] `chunk()` written yourself, under 30 lines
- [ ] Splits on **blank lines first**, then merges — does not use fixed-size slicing
- [ ] `max_chars` chosen as a **context-budget** decision (AG-04), and can defend the number
- [ ] `overlap` chosen, and can say what it insures against
- [ ] `chunk_inspect.py` run
- [ ] Size distribution examined; median not far below `max_chars`
- [ ] Shortest three chunks inspected for garbage
- [ ] **Mid-sentence starts counted** — and the chunker fixed if the count was high

## The index

- [ ] `EMBED_MODEL` pinned as a constant — Principle 4 covers embedders too
- [ ] `Chunk` carries a `source` — provenance, so citations are auditable
- [ ] `normalize_embeddings=True` on **both** the corpus and the query
- [ ] Can explain why normalisation makes the search one dot product
- [ ] **Found and fixed the per-call model instantiation** in §3.3
- [ ] Index cached to `.mandala/`, keyed by corpus hash **and** `EMBED_MODEL`
- [ ] Heavy import kept lazy, and the consequence understood

## The Day-15 promise

- [ ] `kb.search(query, k)` signature **unchanged** — verified by a test
- [ ] Nothing that calls `kb.search()` was edited today
- [ ] `USE_EMBEDDINGS` switch kept **permanently**, not deleted after the swap
- [ ] `_keyword_search` kept as the baseline — **not deleted**

## The measurement — the honest part

- [ ] Day 41's chosen yardstick re-read **before** running anything
- [ ] If it was blank, written now and the lateness noted in the write-up
- [ ] `tests/fixtures/retrieval_golden.json` written — **≥12 queries**
- [ ] Includes 3 corpus-vocabulary queries
- [ ] Includes 3 paraphrase queries (different words, same idea)
- [ ] Includes 3 messy realistic customer phrasings
- [ ] **Includes 3 "nothing should match" cases** — the group everyone forgets
- [ ] `bakeoff_retrieval.py` run; **per-query rows** read, not just the totals
- [ ] Latency measured for both
- [ ] Can name **which** queries embeddings won, and why that is the interesting sentence
- [ ] Decision made per §4.3 — and a tie was resolved in favour of the simpler system
- [ ] The metric was **not** changed after seeing results

## Tests that must be able to fail

- [ ] `test_chunks_are_bounded`
- [ ] `test_chunks_overlap`
- [ ] `test_no_chunk_is_uselessly_short`
- [ ] `test_every_chunk_has_a_source`
- [ ] `test_vectors_are_normalised`
- [ ] `test_search_returns_k_results`
- [ ] `test_scores_are_descending`
- [ ] `test_the_embedder_is_pinned`
- [ ] `test_the_model_is_loaded_once` — **flip it:** re-instantiate per call, see red
- [ ] `test_kb_search_signature_is_unchanged_since_day_15`
- [ ] `test_the_golden_set_is_big_enough_and_balanced`
- [ ] `test_recall_at_3_meets_the_floor` — floor set from **your** number, minus slack
- [ ] `test_a_nonsense_query_does_not_return_a_confident_hit` — **the one nobody writes**
- [ ] If that test failed: score floor added to `kb.search()`, and an ADR line written
- [ ] All tests cost **0 model requests**

## AG-14 — `decision_map.md`

- [ ] Three-way table filled (changes / costs / latency / when)
- [ ] The one-line rule written in **your own words**
- [ ] Why fine-tuning is a stated non-goal here (Part 8)
- [ ] Last section **anchored to today's per-query results**, not to the general theory

## Understanding check — answer out loud

- [ ] What is the unit a user's question is about, and why does that decide chunk size?
- [ ] Why is cosine similarity just a dot product here?
- [ ] What does an unpinned embedder silently break?
- [ ] Why keep the keyword matcher forever?
- [ ] What happens to a vector search on a nonsense query, and why is that dangerous?
- [ ] What did today's numbers tell you about when RAG earns its complexity?

## Budget & freshness

- [ ] Logged in `docs/RATE_BUDGET.md`: **0 requests**, plus CPU time
- [ ] Noted that a free day means you can iterate — and actually did try more than one chunker
- [ ] `numpy` and `sentence-transformers` versions confirmed
- [ ] `all-MiniLM-L6-v2` confirmed still sensible; **if changed, the benchmark was re-run**
- [ ] `normalize_embeddings=` confirmed present
- [ ] `encode()` return type confirmed
- [ ] Torch build checked (CPU vs. CUDA) and any surprise noted
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 46
```

- [ ] Bake-off row added: **retrieval — measured, not assumed**, with the recall numbers
- [ ] `./m done 46` succeeded — trackers updated automatically
