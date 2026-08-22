# Day 15 — CHECKLIST

**IDs covered:** OAI-13 🛠️ (web & file search, the free way), OAI-14 🅿️ (hosted tools, concept only)

## Demo command

```bash
cd days/day-15/lab
uv run python search_shapes.py                              # 0 model calls
uv run python research_with_search.py T-1004                # cites kb:// and https:// alike
MANDALA_OFFLINE=1 uv run python poisoned_kb.py              # run this FOUR times
cd ../../..
```

## Setup

- [ ] `./m start 15` and `./m scaffold 15` run
- [ ] `uv add "ddgs==9.15.0"` — **pin what actually resolved**, and check the PINS ledger row for Day 15
- [ ] Files created (`src/mandala/search.py`, `src/mandala/kb.py`, three lab files, two test files)
- [ ] `data/kb/refunds.md`, `sso.md`, `rate_limits.md` **written by me**, invented, 10–20 lines each
- [ ] `tmp_kb` fixture added to `tests/conftest.py` (tests must never read `data/kb/`)
- [ ] Read the plan-inconsistency note at the top of the lesson and the `docs/CHANGELOG_PLAN.md` entry

## OAI-13 — the hosted shape 🅿️

- [ ] Can write `WebSearchTool()` / `FileSearchTool(vector_store_ids=[...])` from memory
- [ ] Can recite the §3.1 table, especially **row five — who sees the raw results**
- [ ] Can name **four things the hosted version does better**, without flinching
- [ ] `search_shapes.py` run — both descriptions read as **different jobs**, not two spellings of "search"

## OAI-13 — web search, built

- [ ] `SearchHit` caps `title`, `url` and `snippet` **in the schema**, not only in a helper
- [ ] `web_hits()` is separate from the tool — testable, fakeable, replaceable
- [ ] `MANDALA_OFFLINE=1` honoured; `offline()` checked in exactly one place
- [ ] One malformed hit does not lose the other four
- [ ] Empty results return **a sentence**, not `[]`
- [ ] `UNTRUSTED_ENVELOPE` applied to web **and** kb results
- [ ] Can rank the three defences and say **which one is real**
- [ ] `ddgs` import name, call and result keys **verified in a REPL**, not from the lesson

## OAI-13 — file search, built

- [ ] `search(query, k) -> list[Chunk]` — the signature Day 46 must keep
- [ ] Docstring names the Day-46 relationship **in capitals**
- [ ] `score()` written (the TODO(me)) — five minutes, not fifty
- [ ] Overlapping chunks; blank windows skipped; `STOPWORDS` applied
- [ ] `Chunk.ref` is `kb://doc.md#L4-L9` — **opened the file and checked the lines match**
- [ ] `search()` filters `score > 0` before taking `k`

## The permission table (§3.5) — before the agent, not after

- [ ] `web_search` and `kb_search` added to `permissions.TOOLS`
- [ ] Both marked `reads_untrusted=True`
- [ ] `web_search`'s `blast_radius` is **not** "none" — can say why
- [ ] Granted in `AGENTS["researcher"].tools`
- [ ] `uv run pytest tests/test_permissions.py -q` green
- [ ] `trifecta_violations()` still `[]`

## The citation contract

- [ ] `sources` added to `Brief` as **optional with a default** — can say why that is compatible
- [ ] `./m check` run **immediately after** the schema edit — yesterday's cassettes still pass
- [ ] Both `SearchHit.ref` and `Chunk.ref` exist — one format, two sources
- [ ] Ran `research_with_search.py` and **read the `ok`/`BAD` citation output**
- [ ] Observed at least one model citing a source it did not use (or noted that it did not)

## The injection experiment (§3.7) — do not skip

- [ ] `poisoned_kb.py` run **4 times**
- [ ] Did the agent ever **act** on the injection? (expected: never) — **___**
- [ ] How often did it **relay** the marker into its output? — **___ / 4**
- [ ] Can state which of those two is structural and which is prompt-strength
- [ ] Can explain the third-order risk: a relayed injection riding inside a `Brief` across the
      Day-14 pipeline seam into a write-capable agent
- [ ] `data/kb/_poisoned.md` deleted — **`git status` checked**

## OAI-14 🅿️ — concept only

- [ ] Can say what code interpreter *is* in one sentence (a loop plus a sandbox)
- [ ] Can say what computer use *is* in one sentence (Day 3's loop with pixels)
- [ ] Knows where each free equivalent lands (Day 19 / Day 67, Day 68)
- [ ] Can name honestly what buying the hosted version gets you
- [ ] Four sentences written into the ADR-001 draft

## Tests that must be able to fail

- [ ] `test_the_suite_is_offline` — `autouse` fixture, whole file
- [ ] `test_a_hostile_field_cannot_blow_the_context_budget`
- [ ] `test_every_hit_is_wrapped_in_the_untrusted_envelope` — **flip it:** return the payload bare
- [ ] `test_web_and_kb_sources_share_one_citation_format`
- [ ] `test_the_new_tools_are_in_the_permission_table`
- [ ] `test_researcher_still_holds_no_write_tool` + `trifecta_violations() == []`
- [ ] `test_chunk_ref_points_at_real_lines`
- [ ] `test_every_chunk_is_bounded`
- [ ] `test_ranking_prefers_the_document_that_answers_the_question` — must survive Day 46's rewrite
- [ ] `test_no_match_returns_nothing_rather_than_the_best_of_nothing`
- [ ] `test_search_signature_is_the_day_46_contract` — an executable note to my future self
- [ ] `test_every_finding_in_a_brief_carries_a_source`
- [ ] `test_the_agent_does_not_act_on_an_injected_instruction` — asserts the **structural** property only
- [ ] No test asserts the relay rate (probabilistic properties do not belong in CI)
- [ ] All tests but the last cost **0 model requests**; suite runs with no network

## Understanding check — answer out loud

- [ ] What does a hosted tool hide that a function tool forces you to name?
- [ ] Why is "my code sits in the middle" both the cost and the benefit?
- [ ] Why is `reads_untrusted=True` on `web_search` more important than `writes=False`?
- [ ] Why is `data/kb/` untrusted even though it is internal?
- [ ] Which defence stopped the injection, and which one merely varied?
- [ ] Why is adding an optional field to `Brief` safe when adding a required one is not?
- [ ] What does Day 46 change in `kb.py`, and what must it not change?

## Budget & freshness

- [ ] Model requests logged in `docs/RATE_BUDGET.md` (declared: ~53, Groq)
- [ ] **HTTP requests to DuckDuckGo kept in the tens** — it is a courtesy, not a tier
- [ ] `ddgs` throttling exception identified and caught specifically (not bare `Exception`)
- [ ] Hosted-tool constructor arguments verified against the live docs
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 15
```

- [ ] `./m done 15` succeeded — trackers updated automatically
- [ ] **ADR-001 drafted tonight** — Day 16 is the phase gate
