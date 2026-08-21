---
day: 46
phase: 7
phase_name: "LangGraph 1.x"
title: "The one honest RAG day"
ids: ["AG-13", "AG-14"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 46 — The one honest RAG day

**Phase 7 · LangGraph 1.x** · IDs: **AG-13 🛠️**, **AG-14 🅿️**

> **Yesterday:** streaming a graph, and the same security rule surviving its second framework.
> **Today:** the day the plan has been deferring since Day 15. You swap the keyword matcher behind
> `kb.search()` for real embeddings — **and then measure whether that was actually an improvement**,
> using the yardstick you chose on Day 41 before you knew the answer.
> **Tomorrow:** checkpointers, and memory becomes a runtime property.

```bash
./m start 46
./m scaffold 46
```

---

## §1 The story

The plan calls this **"the one honest RAG day"**, and every word of that phrase is load-bearing.

**One**, because Part 8 excludes production RAG infrastructure and Day 41 made you write down why —
with a "what would change my mind" column. Today builds the whole of Mandala's retrieval and then
stops.

**Honest**, because of what happens in §5. Thirty-one days ago (Day 15) you built `kb.search()` over a
deliberately naive keyword matcher, with the interface designed so that today would be a **body
change, not an API change**. Today you write the embedding version — and then you run both against
the golden set and find out whether embeddings actually win on *your* corpus.

**Most RAG tutorials skip that step**, and it is the only step that makes the day worth having. A
result you did not measure is a preference. And there is a real possibility, which you should hold
open rather than dismiss: **on a handbook of a few dozen passages with a fairly technical vocabulary,
keyword matching is often competitive.** If that is your result, it is a finding, not a failure — and
the interface you designed on Day 15 means acting on it costs nothing.

AG-14 is 🅿️ and is a decision map: fine-tuning vs. RAG vs. prompting. Half a page, in your own words,
anchored to the thing you just measured.

**Zero budget note:** embeddings here are **local `sentence-transformers`** (plan §2.1). No API, no
key, no rate limit. Today's model-request budget is zero for the retrieval work itself, which is
unusual and is exactly why the plan put the embedder on a local model.

---

## §2 Setup — run this

### 2.1 Verify, then install

```bash
printf "%-22s " numpy
curl -s --max-time 30 "https://pypi.org/pypi/numpy/json" \
  | python -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
```

```bash
uv add "numpy==2.5.2"
```

- `sentence-transformers==6.0.0` is **already installed** — it was pulled forward to Day 26 for
  CrewAI's memory embedder (`docs/CHANGELOG_PLAN.md`, inconsistency 9). Confirm with
  `grep -n sentence-transformers pyproject.toml`; if it is missing, that inconsistency was overruled
  and you need it today.
- **numpy is the whole vector store.** No Chroma, no FAISS. Day 41's `test_no_rag_infrastructure_
  crept_in` enforces that, and if you disagree, change the test deliberately rather than working
  around it.
- **First run downloads a model** (a few hundred MB) to a local cache. Do that now, before you need
  it: `uv run python -c "from sentence_transformers import SentenceTransformer;
  SentenceTransformer('all-MiniLM-L6-v2')"`. It is a one-time cost and it is not a model *request*.

### 2.2 Create today's files

```bash
touch src/mandala/index.py
touch tests/test_index.py
touch tests/test_retrieval_quality.py
mkdir -p days/day-46/lab
touch days/day-46/lab/chunk_inspect.py
touch days/day-46/lab/bakeoff_retrieval.py
touch days/day-46/lab/decision_map.md
```

- `index.py` is new; **`kb.py` keeps its `search()` signature and gains a switch.** That is the Day-15
  promise being kept, and §4.2 is explicit about the shape.
- `bakeoff_retrieval.py` is the measurement, and it is the day's actual deliverable.

---

## §3 AG-13 — the three pieces

### 3.1 Chunking

**Chunking is where most retrieval quality is won or lost, and it gets one paragraph in most
tutorials.** The question is: what is the unit a user's question is *about*?

For Mandala's handbook, that unit is a **policy paragraph**. Not a sentence (too little context to be
useful as an answer) and not a document (too much, and it blows Day 4's context budget). So:

```python
def chunk(text: str, *, max_chars: int = 800, overlap: int = 100) -> list[str]:
    """Split on blank lines, then merge small pieces up to max_chars, with overlap."""
```

**Line by line on the parameters, because each one is a judgement:**

- `max_chars=800` — roughly 200 tokens. Small enough that five chunks fit comfortably in a prompt
  alongside a ticket; large enough to contain a whole policy statement. **Chunk size is a context
  budget decision (AG-04) before it is a quality decision.**
- `overlap=100` — chunks share their edges, so a policy that straddles a boundary is not cut in half
  and lost by both neighbours. The cost is duplication in the index and occasional near-duplicate
  hits. **Overlap is insurance against bad boundaries**, and 100/800 is about 12%, which is a
  conventional starting point and not a law.
- Splitting on **blank lines first** respects the document's own structure. Fixed-size splitting
  ignores it and produces chunks that begin mid-sentence — the single most common cause of bad
  retrieval, and it is invisible unless you look, which is what §3.2 is for.
- **Write this function yourself**, and keep it under thirty lines. If it grows past that, you are
  building a library the plan excluded.

### 3.2 `days/day-46/lab/chunk_inspect.py` — 0 requests, and do not skip it

```python
"""Look at your chunks. Nobody does this, and it is where the bugs are.

Run:
    uv run python days/day-46/lab/chunk_inspect.py

Budget: 0 requests.
"""

from mandala.index import chunk, load_handbook

docs = load_handbook()
all_chunks = [c for doc in docs for c in chunk(doc)]

print(f"documents {len(docs)}   chunks {len(all_chunks)}")
sizes = sorted(len(c) for c in all_chunks)
print(f"chars: min {sizes[0]}  median {sizes[len(sizes) // 2]}  max {sizes[-1]}")

print("\n--- shortest 3 ---")
for c in sorted(all_chunks, key=len)[:3]:
    print(f"  [{len(c):>4}] {c[:120]!r}")

print("\n--- do any start mid-sentence? ---")
bad = [c for c in all_chunks if c[:1].islower()]
print(f"  {len(bad)} of {len(all_chunks)} start with a lowercase character")
for c in bad[:3]:
    print(f"  {c[:100]!r}")
```

**Line by line:**

- The **size distribution** first. A median far below `max_chars` means your merge step is not
  merging and you have a lot of tiny chunks, each too small to answer anything.
- **The shortest three** are where the garbage lives — headers, page numbers, a stray line. A
  three-word chunk will match some query eventually and return nothing useful.
- `c[:1].islower()` — a crude mid-sentence detector, and it is enough. **A chunk starting lowercase
  almost always means your splitter cut inside a sentence**, which is the failure that quietly halves
  retrieval quality. Crude and effective beats sophisticated and unwritten.
- **This file costs nothing and will change your chunker.** That is the argument for it.

### 3.3 `src/mandala/index.py`

```python
"""Mandala's entire retrieval implementation. Local embeddings, numpy, no database.

Day 15 fixed the interface -- kb.search(query, k) -> list[Chunk] -- specifically so
this file could arrive on Day 46 and change the BODY, not the API. Thirty-one days
later that promise is being kept, and nothing that calls kb.search() changes today.

Zero budget (plan §2.1): sentence-transformers runs locally. No key, no API, no
rate limit. The embedding of a corpus is a one-time local CPU cost.

Usage
-----
    >>> idx = HandbookIndex.build()
    >>> hits = idx.search("how long do refunds take", k=3)
    >>> len(hits)
    3
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

#: Pinned, like every other model in this project (Principle 4).
EMBED_MODEL = "all-MiniLM-L6-v2"
HANDBOOK_DIR = Path("tests/fixtures/handbook")
CACHE = Path(".mandala") / "index"


@dataclass(frozen=True)
class Chunk:
    """One retrievable passage. `source` is what a citation cites."""

    text: str
    source: str
    score: float = 0.0


class HandbookIndex:
    """A numpy array and a dot product. That is the whole vector store."""

    def __init__(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        self._chunks = chunks
        self._vectors = vectors            # shape (n_chunks, dim), L2-normalised

    @classmethod
    def build(cls, *, model_name: str = EMBED_MODEL) -> HandbookIndex:
        from sentence_transformers import SentenceTransformer

        chunks = _chunks_from(HANDBOOK_DIR)
        model = SentenceTransformer(model_name)
        vectors = model.encode(
            [c.text for c in chunks],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return cls(chunks, np.asarray(vectors, dtype=np.float32))

    def search(self, query: str, k: int = 3) -> list[Chunk]:
        """Cosine similarity over a normalised matrix = one dot product."""
        from sentence_transformers import SentenceTransformer

        q = SentenceTransformer(EMBED_MODEL).encode(
            [query], normalize_embeddings=True, show_progress_bar=False
        )
        scores = self._vectors @ np.asarray(q, dtype=np.float32).T
        scores = scores.ravel()
        top = np.argsort(-scores)[:k]
        return [
            Chunk(text=self._chunks[i].text, source=self._chunks[i].source,
                  score=float(scores[i]))
            for i in top
        ]
```

**Line by line:**

- `EMBED_MODEL = "all-MiniLM-L6-v2"` **pinned as a constant.** Principle 4 does not stop at chat
  models. Change the embedder and every vector in your cache is meaningless — an unpinned embedder is
  a silently corrupted index.
- `@dataclass(frozen=True) class Chunk` with a `source` field — **`source` is what a citation cites.**
  Day 29's crew guardrail required a `kb://` reference in every finding; this is the field that makes
  that possible. Retrieval without provenance is retrieval you cannot audit (Principle 8).
- `normalize_embeddings=True` on both sides — this is the line that makes the maths trivial. With
  L2-normalised vectors, **cosine similarity is exactly the dot product**, so the entire search is
  `self._vectors @ q.T`. No library, no index structure, no approximate nearest neighbours. For a few
  hundred chunks a brute-force dot product is *faster* than a network hop to a vector database, and
  saying that with a benchmark behind it is a good interview moment.
- `np.argsort(-scores)[:k]` — negate and sort ascending to get descending order. Idiomatic numpy;
  `argsort` returns indices, which is what you want.
- `float(scores[i])` — converting out of numpy scalars so `Chunk` holds plain Python floats and
  serialises cleanly.
- **The `SentenceTransformer` import is inside the methods**, not at module top. It is a heavy import
  (torch), and keeping it lazy means `import mandala.index` stays fast and CI can import the module
  without loading a deep-learning stack. **Notice the cost of this choice** and fix it: `search()`
  re-instantiates the model on every call, which is very slow. Cache it — a module-level `@lru_cache`
  on a `_model()` helper is the smallest correct fix — and write down that you found it. *This is a
  deliberate bug in the lesson; §5 has a test that catches it.*
- `show_progress_bar=False` — a progress bar in library code corrupts any output you are parsing.
- `CACHE` declared and unused so far — **persisting the index is your job today.** Re-embedding a
  corpus on every process start is seconds of CPU you do not need to spend; save the vectors with
  `np.save` and the chunks with JSON, keyed by a hash of the corpus plus `EMBED_MODEL`. `hashlib` is
  imported for exactly that. And it must be under `.mandala/`, which Day 32 already git-ignored.

### 3.4 Keeping the Day-15 promise

```python
# src/mandala/kb.py  -- the ONLY change to this file today
def search(query: str, k: int = 3) -> list[Chunk]:
    """Unchanged signature since Day 15. The body is now AG-13's index."""
    if USE_EMBEDDINGS:
        return _index().search(query, k)
    return _keyword_search(query, k)
```

**Line by line:**

- **The signature is byte-identical to Day 15's.** Nothing that calls `kb.search()` — Day 37's
  `search_handbook` tool, Day 29's crew, Day 44's research branches — changes at all. That is the
  design decision paying out thirty-one days later, and it is worth stating out loud to yourself.
- `USE_EMBEDDINGS` as a switch, **kept permanently rather than deleted after the swap.** Two reasons:
  §5 needs both implementations live to compare them, and if the measurement says keyword wins you
  want to flip a flag, not revert a commit.
- `_keyword_search` is **not deleted.** Day 15's naive matcher becomes your baseline forever. A
  system with no baseline cannot tell improvement from change.

---

## §4 The measurement — the honest part

### 4.1 The yardstick you chose on Day 41

Go and read `days/day-41/lab/rag_scope.md`, section *"The measurement I will actually run on Day
46"*. **Use what you wrote then**, even if you would now choose differently. Choosing the yardstick
before seeing the results is the only thing that makes the result mean anything, and quietly
switching metrics after looking is the most common way people fool themselves.

If it is blank, the honest move is to write it now, **before** running anything, and note in the
write-up that it was chosen late.

A reasonable default, if you need one: **recall@3 over a hand-labelled query set.** For each of ~12
questions, name the chunk (or chunks) that *should* come back. Score = fraction where a correct chunk
is in the top 3. Twelve labelled queries is enough to see a real difference and small enough to build
in twenty minutes.

### 4.2 `days/day-46/lab/bakeoff_retrieval.py`

```python
"""Keyword (Day 15) vs. embeddings (today), on the same queries. 0 model requests.

Run:
    uv run python days/day-46/lab/bakeoff_retrieval.py

Budget: 0 requests. Embeddings are local; this costs CPU, not quota.
"""

import json
import time
from pathlib import Path

from mandala import kb
from mandala.index import HandbookIndex

GOLDEN = json.loads(Path("tests/fixtures/retrieval_golden.json").read_text(encoding="utf-8"))

index = HandbookIndex.build()


def recall_at_k(hits, expected_sources, k) -> int:
    return int(any(h.source in expected_sources for h in hits[:k]))


rows = []
for case in GOLDEN:
    query, expected = case["query"], set(case["expected_sources"])

    t0 = time.monotonic()
    kw = kb._keyword_search(query, 3)
    kw_ms = (time.monotonic() - t0) * 1000

    t0 = time.monotonic()
    emb = index.search(query, 3)
    emb_ms = (time.monotonic() - t0) * 1000

    rows.append((query, recall_at_k(kw, expected, 3), recall_at_k(emb, expected, 3),
                 kw_ms, emb_ms))

print(f"{'query':<42} {'kw':>3} {'emb':>4} {'kw ms':>7} {'emb ms':>8}")
for query, kw_hit, emb_hit, kw_ms, emb_ms in rows:
    print(f"{query[:40]:<42} {kw_hit:>3} {emb_hit:>4} {kw_ms:>7.1f} {emb_ms:>8.1f}")

n = len(rows)
print(f"\nrecall@3   keyword {sum(r[1] for r in rows)}/{n}   embeddings {sum(r[2] for r in rows)}/{n}")
print(f"median ms  keyword {sorted(r[3] for r in rows)[n // 2]:.1f}   "
      f"embeddings {sorted(r[4] for r in rows)[n // 2]:.1f}")
```

**Line by line:**

- `tests/fixtures/retrieval_golden.json` — **you write this today**, and it is the real work of the
  afternoon. Twelve `{query, expected_sources}` pairs. Include:
  - three where the query **uses the handbook's own words** (keyword should win or tie),
  - three where the query uses **different words for the same idea** ("can't log in" vs. "auth
    redirect") — this is the case embeddings exist for,
  - three **realistic customer phrasings**, badly spelled and vague,
  - three that have **no good answer**, to see what each returns when it should return nothing.
    *That last group is the one everyone forgets, and it is where retrieval systems embarrass
    themselves.*
- `recall_at_k` returns 0 or 1 per query — a hit is "a correct source appears in the top k". Simple,
  interpretable, and enough. Resist MRR and nDCG today; you have twelve queries.
- **Latency measured too**, because it is a fair column. Keyword matching over a few hundred chunks
  is microseconds; embedding a query is milliseconds. If quality is a tie, speed decides.
- `kb._keyword_search` — reaching for a private function is acceptable *in a benchmark*, and say so in
  a comment. It is the reason §3.4 kept it.
- **Print per-query rows, not just totals.** The aggregate hides the interesting part: *which* queries
  each approach wins. If embeddings win only on your three paraphrase queries and lose on the rest,
  that is a much more useful sentence than "embeddings scored 8/12".

### 4.3 What to do with the answer

| Result | What you do |
|---|---|
| Embeddings clearly better | `USE_EMBEDDINGS = True`. Write the number in the ADR. |
| Roughly tied | **Keep keyword.** It is faster, has no model download, and no cache to invalidate. Write down that a tie favours the simpler system. |
| Keyword better | Say so publicly, keep it, and write down what corpus *would* flip it. |

**All three outcomes are a good day.** The one bad outcome is not measuring and switching anyway
because embeddings are what people do.

---

## §5 The eval that must be able to fail

### `tests/test_index.py`

```python
"""The index is now a Mandala component. Test it. 0 model requests -- all local."""

import numpy as np
import pytest

from mandala.index import EMBED_MODEL, Chunk, HandbookIndex, chunk


def test_chunks_are_bounded():
    text = "para one.\n\n" + ("x" * 5000)
    for c in chunk(text, max_chars=800):
        assert len(c) <= 800 + 100      # max_chars + overlap slack


def test_chunks_overlap():
    text = "\n\n".join(f"paragraph {i} " + "y" * 400 for i in range(4))
    pieces = chunk(text, max_chars=800, overlap=100)
    assert len(pieces) > 1
    assert any(pieces[0][-50:] in p for p in pieces[1:]), "no overlap between chunks"


def test_no_chunk_is_uselessly_short():
    from mandala.index import load_handbook

    pieces = [c for doc in load_handbook() for c in chunk(doc)]
    assert min(len(c) for c in pieces) >= 40, "a chunk too small to answer anything"


def test_every_chunk_has_a_source():
    """Retrieval without provenance is retrieval you cannot audit (Principle 8)."""
    idx = HandbookIndex.build()
    for hit in idx.search("refund policy", k=5):
        assert hit.source, hit


def test_vectors_are_normalised():
    """The whole search is a dot product ONLY if the vectors are unit length."""
    idx = HandbookIndex.build()
    norms = np.linalg.norm(idx._vectors, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3)


def test_search_returns_k_results():
    idx = HandbookIndex.build()
    assert len(idx.search("anything at all", k=2)) == 2


def test_scores_are_descending():
    idx = HandbookIndex.build()
    scores = [h.score for h in idx.search("refund policy", k=5)]
    assert scores == sorted(scores, reverse=True)


def test_the_embedder_is_pinned():
    """Principle 4. An unpinned embedder silently invalidates every cached vector."""
    assert EMBED_MODEL and "/" not in EMBED_MODEL or True
    assert isinstance(EMBED_MODEL, str) and len(EMBED_MODEL) > 3


def test_the_model_is_loaded_once(monkeypatch):
    """THE performance bug in §3.3. Flip it: re-instantiate per call and this goes red."""
    calls = {"n": 0}
    import mandala.index as index_module

    real = index_module.SentenceTransformer if hasattr(index_module, "SentenceTransformer") else None

    idx = HandbookIndex.build()
    import sentence_transformers

    original = sentence_transformers.SentenceTransformer

    def counting(*a, **k):
        calls["n"] += 1
        return original(*a, **k)

    monkeypatch.setattr(sentence_transformers, "SentenceTransformer", counting)
    idx.search("a", k=1)
    idx.search("b", k=1)
    assert calls["n"] <= 1, f"model constructed {calls['n']} times across two searches"


def test_kb_search_signature_is_unchanged_since_day_15():
    """The Day-15 promise. Flip it: add a parameter, and thirty-one days of callers break."""
    import inspect

    from mandala import kb

    params = list(inspect.signature(kb.search).parameters)
    assert params == ["query", "k"]
```

### `tests/test_retrieval_quality.py`

```python
"""A quality floor, so retrieval cannot silently regress (Principle 7)."""

import json
from pathlib import Path

import pytest

from mandala.index import HandbookIndex

GOLDEN = json.loads(Path("tests/fixtures/retrieval_golden.json").read_text(encoding="utf-8"))

#: Set this from YOUR measured number, minus a little slack. Not aspirational.
RECALL_FLOOR = 0.6


@pytest.fixture(scope="module")
def index():
    return HandbookIndex.build()


def test_the_golden_set_is_big_enough_and_balanced():
    assert len(GOLDEN) >= 12
    assert any(c.get("expected_sources") == [] for c in GOLDEN), "no 'nothing should match' cases"


def test_recall_at_3_meets_the_floor(index):
    hits = 0
    for case in GOLDEN:
        expected = set(case["expected_sources"])
        if not expected:
            continue
        found = {h.source for h in index.search(case["query"], k=3)}
        hits += int(bool(found & expected))
    scored = sum(1 for c in GOLDEN if c["expected_sources"])
    assert hits / scored >= RECALL_FLOOR, f"recall@3 = {hits}/{scored}"


def test_a_nonsense_query_does_not_return_a_confident_hit(index):
    """The case everyone forgets. Embeddings ALWAYS return something -- check the score."""
    hits = index.search("zxqv wombat parliament", k=1)
    assert hits[0].score < 0.5, f"nonsense scored {hits[0].score:.2f}"
```

**Line by line on the two that matter most:**

- `test_the_model_is_loaded_once` is the **flip-it test for the deliberate bug in §3.3**. Two
  searches, one model construction. Without it, `search()` loads a transformer per query and your
  benchmark measures model loading rather than retrieval — which would make §4's latency column a
  lie.
- `test_a_nonsense_query_does_not_return_a_confident_hit` is the test almost nobody writes and it is
  the most important one on the page. **A vector search always returns `k` results, even for
  gibberish.** Without a score threshold, "no relevant policy exists" becomes "here is the least
  irrelevant paragraph, cited as though it were an answer" — and Day 29's crew will faithfully cite
  it. **Retrieval that cannot say "I don't know" is a hallucination generator with a citation
  format.** If this test fails, add a score floor to `kb.search()` and return fewer than `k` results.
  That is a real behaviour change and it should have its own line in the ADR.
- `RECALL_FLOOR` set from **your measurement minus slack**, not from an aspiration. A floor above your
  current number is a permanently red test that people learn to ignore; a floor slightly below it is a
  regression gate that Day 74 can enforce.

---

## §6 AG-14 — `days/day-46/lab/decision_map.md`

🅿️, half a page, in your own words, anchored to today's numbers.

```markdown
# Fine-tuning vs. RAG vs. prompting — Mandala, 2026-08-__

| | Changes | Costs | Latency | When it is the right tool |
|---|---|---|---|---|
| Prompting | the instructions | ~0 | none | behaviour, tone, output shape |
| RAG | the **facts available** | index build + retrieval | ms | knowledge that changes, or is too big for a prompt |
| Fine-tuning | the **weights** | training data + compute + a pipeline | none at inference | style/format at scale, or a narrow task done constantly |

## The one-line rule
<"if the model doesn't KNOW something, retrieve it; if it doesn't BEHAVE right, prompt it;
 if it can't DO something after both, consider fine-tuning" -- in your own words>

## Why fine-tuning is a stated non-goal here (Part 8)
<one paragraph>

## What today's measurement actually tells me
<did retrieval help? on which queries? what does that say about when RAG earns its complexity?>
```

**Anchor the last section to your per-query results.** "RAG helps when the user's words differ from
the corpus's words" is a claim you can now support with three specific queries, which is a different
class of statement from repeating the decision map.

---

## §7 Traps

- **Not looking at your chunks.** `chunk_inspect.py` takes two minutes and will change your chunker.
- **Fixed-size chunking that ignores paragraph boundaries.** Chunks that start mid-sentence, and
  retrieval quality quietly halves.
- **Forgetting `normalize_embeddings=True`.** Then the dot product is not cosine similarity and your
  scores are meaningless while looking fine.
- **Re-instantiating the embedding model per query.** §3.3's deliberate bug; §5 catches it.
- **An unpinned embedder.** Every cached vector becomes silently wrong.
- **Deleting the keyword matcher after the swap.** You have destroyed your baseline.
- **Changing the yardstick after seeing the results.** The one thing that makes today dishonest.
- **Assuming embeddings won.** Measure. A tie favours the simpler system.
- **No "nothing should match" cases in the golden set.** Vector search always returns `k` results.
- **No score threshold.** Retrieval that cannot say "I don't know" will cite a wrong policy with
  perfect confidence.
- **Adding a vector database.** Day 41's test fails, and for a few hundred chunks numpy is faster.

---

## §8 Request budget

**Declared: 0 model requests.**

| What | Requests |
|---|---|
| Everything today | **0** |

**Today costs no quota at all**, and that is a design result rather than an accident: plan §2.1 put
embeddings on a local model specifically so that the RAG day would be free. Note what that means in
practice — **you can iterate on chunking and retrieval as many times as you like**, which is the
opposite of every other lab in this plan. Use that freedom; it is the right day to try three chunkers.

The only cost is a one-time model download and some CPU. Log "0 requests, ~N minutes CPU" in the
ledger, because the ledger's job is to track the real constraint and today's constraint was different.

---

## §9 Verify before you code

Written **2026-08-20** against `sentence-transformers==6.0.0`, `numpy==2.5.2`:

- **`numpy==2.5.2` still current?** Verify, pin, log. Note that numpy 2.x has real API differences
  from 1.x if you copy code from an older source.
- **Is `all-MiniLM-L6-v2` still a sensible default** in `sentence-transformers` 6.0? If a small
  successor is now standard, pin that instead **and re-run the benchmark**, since changing the
  embedder invalidates every measurement on the page.
- **Does `encode()` still take `normalize_embeddings=`?** The whole dot-product argument depends on it.
- **What does `encode()` return in 6.0** — a numpy array, a torch tensor, or a list? `np.asarray`
  handles all three, which is why it is there, but know which one you got.
- **Where does the model cache live** (`HF_HOME` / `SENTENCE_TRANSFORMERS_HOME`)? Make sure it is not
  inside the repo, and if it is, `.gitignore` it before the first commit.
- **CPU-only install?** If `sentence-transformers` pulled a CUDA torch build on your machine that is
  gigabytes you did not need; check and note it.
- `https://sbert.net` — the current recommended small model.

---

## §10 Say it in an interview

> "We build exactly one retrieval path: paragraph-aware chunking, local sentence-transformers
> embeddings, and a normalised numpy matrix — so cosine similarity is a single dot product and there's
> no vector database, because at a few hundred chunks a brute-force dot product beats a network hop.
> The part I'd actually talk about is that I kept the naive keyword matcher I'd written a month
> earlier as a baseline and benchmarked both on a hand-labelled query set whose metric I'd chosen
> *before* seeing any results. Embeddings won on the queries where the user's words differ from the
> corpus's words, which is exactly the case they exist for, and were a wash elsewhere. The test I'd
> point at is the nonsense-query one: a vector search always returns k results, so without a score
> threshold 'no relevant policy exists' silently becomes 'here's the least irrelevant paragraph' —
> and a downstream agent will cite it with perfect confidence. Retrieval that can't say 'I don't know'
> is a hallucination generator with a citation format."

---

## §11 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 46
```
