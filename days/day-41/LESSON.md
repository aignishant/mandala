---
day: 41
phase: 6
phase_name: "LangChain 1.x"
title: "RAG scoped honestly, and Deep Agents"
ids: ["LC-11", "LC-12"]
kind: concept
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 41 — RAG, scoped honestly · and Deep Agents

**Phase 6 · LangChain 1.x** · IDs: **LC-11 🅿️**, **LC-12 🅿️**

> **Yesterday:** event streaming reduced to four lines, and the exact point where LangChain hands
> memory to LangGraph.
> **Today:** two 🅿️ concept IDs — which in this plan means *read, run one example, and write down a
> decision*, not *skip*. First a scoping decision about RAG that the plan made for you and you should
> be able to defend. Then Deep Agents, LangChain's answer to the harness idea you met as a paid
> feature on Day 19.
> **Tomorrow:** the Phase-6 gate, the LangChain↔LangGraph seam, and ADR-002.

```bash
./m start 41
./m scaffold 41
```

---

## §1 The story

A 🅿️ day is where most curricula lose people, because "concept only" reads as "optional". In this
plan it means something specific: **the deliverable is a written decision rather than a feature.**
Principle 9 — every phase ends with something you could defend to a hiring panel — applies to today
more than to a lab day, not less.

Two decisions today, and they are opposites in an instructive way.

**LC-11 is a decision to do less.** LangChain ships loaders, splitters, vector stores, retrievers, and
an entire RAG ecosystem. Mandala uses **one local index, built once on Day 46**, and no more. Part 8
of the plan lists "full RAG infrastructure" under *checked and deliberately excluded*. Today you
learn what you are not using, well enough to explain the boundary rather than merely assert it.

**LC-12 is a decision to look at something bigger.** `deepagents` is the harness-style layer above
`create_agent`: planning, filesystem and sandbox backends, subagents. It is LangChain's answer to
**OAI-18**, the model-native harness you studied on Day 19 as a paid feature you could not run. Today
you can run one, for free, and the comparison is the point.

The through-line: **on a $0 budget, scope discipline is the primary engineering skill.** Both of
today's IDs are about knowing where to stop.

---

## §2 Setup — run this

### 2.1 Verify, then install one package

```bash
printf "%-14s " deepagents
curl -s --max-time 30 "https://pypi.org/pypi/deepagents/json" \
  | python -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
```

```bash
uv add "deepagents==0.7.7"
```

- The ledger (`docs/PINS.md`) says Day 41, `deepagents==0.7.7`. **Verify the live number first** — if
  it has moved a patch, pin the new one and log a line; a minor bump means release notes before pins
  (Principle 14). The plan's own note flags "v0.4+ pluggable sandboxes, leaner default prompts", so
  this library moves.
- **A `0.x` version number is information.** It means the API may break at a minor bump, and it is a
  reason to keep `deepagents` behind a thin seam rather than threaded through Mandala. §4.3 says
  where that seam goes.
- **Nothing is installed for LC-11.** No `langchain-community`, no vector store, no loader package.
  That absence is the deliverable, and §3 explains why it is a decision rather than an omission.

### 2.2 Create today's files

```bash
mkdir -p days/day-41/lab
touch days/day-41/lab/rag_scope.md
touch days/day-41/lab/deep_agent_demo.py
touch days/day-41/lab/harness_compare.md
```

- Two markdown files and one script. **Today's ratio is deliberate** — the writing is the work.

---

## §3 LC-11 — RAG in 1.x, and the line Mandala draws

### 3.1 What LangChain offers, in one table

| Piece | What it does | Mandala's answer |
|---|---|---|
| **Loaders** | read PDFs, HTML, Notion, Slack… | one JSON fixture file. Read with `open()`. |
| **Splitters** | chunk documents sensibly | Day 46, ~30 lines, by paragraph |
| **Embeddings** | text → vectors | local `sentence-transformers` (**no API**, plan §2.1) |
| **Vector stores** | store and search vectors | Day 46: a numpy array and a dot product |
| **Retrievers** | the query interface | `kb.search(query, k) -> list[Chunk]` (Day 15) |
| **Rerankers, hybrid search, query rewriting** | production RAG quality | **excluded** (Part 8) |

**Read the right-hand column downward.** Each row is small and unglamorous, and together they are the
whole of Mandala's retrieval. The plan is not claiming that is enough for a real product; it is
claiming it is enough to *understand* retrieval, and that production RAG infrastructure is a
different course.

### 3.2 The three reasons — and one is not what you expect

1. **Zero budget (Principle 5).** Hosted embedding APIs cost money and rate limits. Local
   `sentence-transformers` costs neither and is genuinely good enough for a handbook of a few dozen
   passages. **This is the weakest of the three reasons** and it is the one people give first.
2. **Blast radius (Principle 6).** Every loader is a parser, and parsers are attack surface. A PDF
   loader that will happily parse a customer-supplied PDF is a code path you did not write, reading
   bytes a stranger chose. Day 65's injection lab and MCP-15's supply-chain review both point here.
   **Each package you do not install is a package you do not have to review.**
3. **The honest one: RAG is usually the wrong tool for triage.** Mandala's retrieval need is *"find
   the handbook passage about refunds"* over a corpus of dozens of documents. That is a search
   problem, not a semantic-similarity problem, and Day 15 already solved it with keyword matching.
   AG-13 (Day 46) upgrades the matcher to embeddings *and says so out loud* — the interface
   (`kb.search`) was designed on Day 15 to make that swap a body change, not an API change.

**Reason 3 is the interview answer.** Anyone can say "we used a local embedder to save money".
Saying *"our retrieval need was small and well-specified, so we designed the interface first and
deferred the implementation until we could tell whether embeddings actually beat keywords on our
corpus"* is an engineer talking.

### 3.3 `days/day-41/lab/rag_scope.md` — the deliverable

```markdown
# Mandala's retrieval scope — decided 2026-08-__

## What we build
- One local index over `tests/fixtures/handbook/` (Day 46, AG-13).
- Interface: `kb.search(query: str, k: int) -> list[Chunk]`, fixed since Day 15.
- Embeddings: local `sentence-transformers`. No API, no key, no rate limit.

## What we deliberately do not build
| Excluded | Why | What would change my mind |
|---|---|---|
| Document loaders | parser attack surface; our corpus is one fixture dir | |
| A vector database | dozens of chunks; numpy is faster than a network hop | |
| Rerankers | | |
| Hybrid / BM25 + vector | | |
| Query rewriting | | |

## The measurement I will actually run on Day 46
<how will I know whether embeddings beat Day 15's keyword matcher on MY corpus?>

## The interview sentence
<one sentence, out loud, no notes>
```

**Why the "what would change my mind" column exists:** a scoping decision with no stated reversal
condition is a prejudice. Filling it in forces you to name the observation that would justify the
extra machinery — *"if the handbook exceeds a few hundred passages", "if recall@3 on the golden set
drops below X"* — and that is what makes the decision defensible rather than merely firm.

**The measurement question is the important one.** Day 46 is called "the one honest RAG day" in the
plan, and honesty there means having a number. Decide today what you will measure, so Day 46 is not
the day you invent the yardstick and the result at the same time.

---

## §4 LC-12 — Deep Agents

### 4.1 What it is, and what it rhymes with

`deepagents` sits **above** `create_agent` and adds four things:

| Capability | What it means | Where you have met it |
|---|---|---|
| **Planning** | the agent writes a todo list and works it | AG-06, Day 5 (plan vs. react) |
| **A filesystem** | scratch files that persist across turns | Day 19's Docker mount |
| **Subagents** | delegate a sub-task to a fresh context | AG-10 Day 8; OAI-10 Day 13; CR-05 Day 25 |
| **Sandbox backends** | where that filesystem actually lives | AG-18, Day 67 |

**Nothing in that list is new to you.** That is the observation worth having: Deep Agents is a
*packaging* of four ideas this plan already taught separately, and the interesting question is not
"what can it do" but **"what does the packaging cost?"**

And note the shape of the row you cannot otherwise reach: **OAI-18, the model-native harness, is
paid-only** and you studied it at docs level on Day 19 (the plan marks it 🅿️ *"docs-level mastery —
interviewers ask"*). `deepagents` is a free, open implementation of the same idea. **Today is the day
you can actually compare a harness against something you ran**, which is exactly what Day 19's
written explainer could not do.

### 4.2 `days/day-41/lab/deep_agent_demo.py`

Run the example. Once. Read the trace.

```python
"""Run one deep agent on a Mandala task, then read what it actually did.

Run:
    uv run python days/day-41/lab/deep_agent_demo.py

Budget: <= 15 requests. Planning + subagents multiply turns -- that is the POINT
of the measurement, not an accident. Run it ONCE.
"""

from deepagents import create_deep_agent

from mandala.lc.chat import fast_loop
from mandala.lc.tools import READ_TOOLS

TASK = (
    "Read tickets T-1001, T-1004 and T-9002. Produce a short report grouping them "
    "by category, with one recommended action per group. Cite ticket ids."
)

agent = create_deep_agent(model=fast_loop(), tools=READ_TOOLS)
result = agent.invoke({"messages": [("user", TASK)]})

messages = result["messages"]
ai_turns = sum(1 for m in messages if type(m).__name__ == "AIMessage")
tool_turns = sum(1 for m in messages if type(m).__name__ == "ToolMessage")

print(f"messages   {len(messages)}")
print(f"AI turns   {ai_turns}      <- this is your request count")
print(f"tool calls {tool_turns}")
print(f"\n--- final ---\n{str(messages[-1].content)[:800]}")
```

**Line by line:**

- `create_deep_agent(model=..., tools=...)` — **the model is pinned explicitly**, Day 1's rule, even
  for a library you are evaluating and will not keep. Especially then: a harness that picks its own
  default model would spend on a provider you did not choose.
- `tools=READ_TOOLS` — Day 37's read-only list. **A harness with a filesystem and subagents is exactly
  where you do not relax the blast radius** (Principle 6). Give it the same tools your triage agent
  has, no more.
- `TASK` is a **multi-ticket, multi-step** request, chosen because a single lookup would not exercise
  planning at all and would tell you nothing. Three tickets, a grouping, and a citation requirement.
- **Counting `AIMessage`s is the measurement.** Day 38 established that count as the honest request
  number. Compare it against Day 38's plain `create_agent` on a comparable task: if the harness costs
  three times the turns, that is the price of planning, and it is a number for `harness_compare.md`
  rather than an impression.
- `str(messages[-1].content)[:800]` — read the actual output. **Ask whether the plan it made was
  better than no plan**, honestly. On a small task, planning frequently loses: it spends turns
  deciding what a direct agent would have just done.
- The docstring's "run it ONCE" is a real instruction: 15 requests is 30% of OpenRouter's daily 50
  (`RATE_BUDGET.md` §1). Read the output rather than re-running it.

### 4.3 Where the seam goes if you ever adopt it

You are **not** adopting `deepagents` into Mandala today, and the plan does not ask you to. But write
down where it would attach, because that is the reusable thinking:

- It would be **one branch**, exactly like Day 31's `organs.py` — the deep-research lane, and nothing
  else. Planning is worth its turns on open-ended research and wastes them on classification.
- It would go **behind a named function in `src/mandala/`**, so a `0.x` library's breaking change is
  a one-file fix. Day 31's `run_research_organ` is the template and it exists precisely for this
  shape of dependency.
- Its filesystem would be a **sandbox**, not your repo. Day 19 built the Docker version; Day 67 makes
  it real. An agent that writes files needs somewhere disposable to write them, and "my project
  directory" is not that.

**Notice this is the third time the same pattern has appeared** — expensive autonomous thing behind
one named boundary with a request budget attached (Day 31's crew, Day 39's refused retry layer,
today's hypothetical harness). By now it should feel like a reflex rather than a rule.

### 4.4 `days/day-41/lab/harness_compare.md`

```markdown
# Harnesses: OAI-18 (paid, read) vs. deepagents (free, ran) — 2026-08-__

| | OpenAI model-native harness (Day 19, 🅿️) | deepagents (today, ran) |
|---|---|---|
| Planning | | |
| Filesystem | | |
| Subagents | | |
| Sandbox | native, paid | pluggable backends |
| Could I run it on $0? | **no** | **yes** |
| Turns for my 3-ticket task | n/a | |
| Same task, plain `create_agent` (Day 38) | n/a | |
| Ratio | | |

## Was the plan better than no plan, on this task?
<honest answer, with the turn counts>

## When would a harness earn its turns?
<one paragraph — and name the shape of task, not a vibe>

## What Day 19's explainer got wrong or missed
<having now run one, revisit what you wrote on Day 19>
```

**The last row is the one that makes today worth a day.** You wrote an explainer on Day 19 about a
feature you could not run. Now you have run its free cousin. **Going back and correcting your own
earlier write-up is the single most valuable habit in this plan** — it is Principle 14's spirit
applied to your own understanding rather than to the ecosystem.

---

## §5 The eval that must be able to fail

A 🅿️ day still gets a test (Principle 7). Today's target is the **scope decision**, because a scope
decision that nothing enforces decays into an aspiration within a month.

### `tests/test_scope.py`

```python
"""Principle 7 on a concept day: the scoping decisions are enforced, not just written."""

from pathlib import Path

import tomllib

PYPROJECT = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
DEPS = " ".join(PYPROJECT["project"]["dependencies"])


def test_no_rag_infrastructure_crept_in():
    """Part 8 of the plan. Flip it: uv add chromadb, and this goes red."""
    for banned in ("langchain-community", "chromadb", "faiss", "pinecone", "weaviate", "qdrant"):
        assert banned not in DEPS, banned


def test_no_hosted_embedding_package():
    """Plan §2.1: embeddings are local, never an API."""
    for banned in ("openai-embeddings", "cohere", "voyageai"):
        assert banned not in DEPS, banned


def test_deepagents_is_pinned_exactly():
    assert "deepagents==" in DEPS, "Principle 4: exact pin, not a range"


def test_deepagents_is_not_wired_into_src():
    """LC-12 is 🅿️ today. If that changes, it changes deliberately (§4.3)."""
    offenders = [
        p.relative_to("src").as_posix()
        for p in Path("src/mandala").rglob("*.py")
        if "deepagents" in p.read_text(encoding="utf-8")
    ]
    assert offenders == [], offenders


def test_the_scope_documents_exist_and_are_filled_in():
    """A template with placeholders left in it is not a decision."""
    for name in ("rag_scope.md", "harness_compare.md"):
        text = Path("days/day-41/lab") / name
        body = text.read_text(encoding="utf-8")
        assert len(body) > 400, name
        assert "<" not in body.split("## ")[-1], f"{name} still has a placeholder"


def test_the_retrieval_interface_has_not_drifted():
    """Day 15 fixed the signature so Day 46 can swap the body. Keep the promise."""
    from mandala import kb

    assert hasattr(kb, "search")
```

**Line by line:**

- `tomllib` — **standard library since 3.11**, so reading `pyproject.toml` costs no dependency. Note
  it is read-only (`tomllib` cannot write TOML), which is fine here and is the kind of small fact
  worth knowing before you need it.
- `test_no_rag_infrastructure_crept_in` names the packages the plan excluded. **This is a scoping
  decision made executable**, and it is the whole point of testing on a concept day: six months from
  now someone adds `chromadb` "just to try", and a test asks them to justify it. The flip-it
  instruction is in the docstring.
- `test_no_hosted_embedding_package` guards plan §2.1's zero-budget commitment at the dependency
  level, which is where it can actually be enforced.
- `test_deepagents_is_pinned_exactly` — Principle 4, and it matters more than usual for a `0.x`
  package where a minor bump may break the API.
- `test_deepagents_is_not_wired_into_src` asserts today's 🅿️ status structurally. **It is designed to
  fail on the day you adopt it**, which is correct: adoption should be a deliberate change that
  includes deleting or rewriting this test, not something that happens by drift.
- `test_the_scope_documents_exist_and_are_filled_in` checks length and looks for a leftover `<`
  placeholder in the final section. Crude — a test cannot judge whether your reasoning is any good —
  and honest about it: it enforces that **something was written**, which is the strongest mechanical
  guarantee available for a prose deliverable. Say that limitation out loud rather than pretending
  the test validates the thinking.
- `test_the_retrieval_interface_has_not_drifted` protects the Day-15 promise that Day 46 relies on.
  One line, guarding a twenty-day-old design decision.
- **Zero model requests.** A concept day's tests should cost nothing at all.

---

## §6 Traps

- **Treating 🅿️ as "skip".** The deliverable is a written decision. Day 63's bake-off and Day 89's
  portfolio both consume today's two documents.
- **Installing a vector store "to see how it works".** That is Day 46, with numpy, and §5 will fail.
- **Giving the reason as "it's cheaper".** True, weakest, and the one everyone says. Lead with the
  scoping argument.
- **Leaving "what would change my mind" blank.** A decision without a reversal condition is a
  prejudice.
- **Deciding the Day-46 measurement on Day 46.** Inventing the yardstick and reading the result at
  the same time is how you get the answer you wanted.
- **Running `deep_agent_demo.py` repeatedly.** 15 requests is 30% of an OpenRouter day. Read the
  output instead.
- **Letting the deep agent pick its own model.** Day 1's rule; a harness with a default model spends
  on a provider you did not choose.
- **Giving the harness more tools than your triage agent has.** Filesystem plus subagents plus write
  access is the lethal trifecta assembling itself (AG-16).
- **Wiring `deepagents` into `src/` "just as an experiment".** A `0.x` dependency in your spine.
- **Not going back to Day 19's explainer.** Correcting your own earlier write-up is the highest-value
  half-hour of the day.

---

## §7 Request budget

**Declared: ~15 model requests, Groq — and all of them in one script.**

| What | Requests |
|---|---|
| `tests/test_scope.py` | **0** |
| `rag_scope.md`, `harness_compare.md` | **0** |
| `deep_agent_demo.py` | ≤ 15 |

**This is the most expensive single script in Phase 6**, and the cost is the measurement: planning
and subagents multiply turns, and the number you get is the answer to "what does a harness cost".
Log it against Day 38's plain-agent count for the ratio.

---

## §8 Verify before you code

Written **2026-08-20**. `deepagents` is `0.x` and the plan flags it as moving:

- **`deepagents==0.7.7` still current?** Check PyPI. A patch → pin and log; a minor → release notes
  first, because `0.x` minors break APIs (Principle 14).
- **Is `create_deep_agent` the constructor**, and does it take `model=` and `tools=`? The plan notes
  "v0.4+ pluggable sandboxes, leaner default prompts", so the constructor signature has moved before.
- **What is the default sandbox backend?** If it writes to the current working directory, know that
  *before* you run it in your repo — and consider running from a scratch directory.
- **Does it default to a model if you omit `model=`?** If yes, that is a zero-budget hazard worth a
  line in `docs/RATE_BUDGET.md`.
- **Does it spawn subagents with your tools or a superset?** A harness that grants its subagents
  extra capability is a blast-radius question (Principle 6), and it belongs in your notes for Day 66.
- **LangChain's RAG docs** — skim, do not implement, and confirm the loader/splitter/store split is
  still shaped as §3.1 describes.
- `https://docs.langchain.com/oss/python/langchain/retrieval` and the `deepagents` README — today.

---

## §9 Say it in an interview

> "Two scoping calls. On retrieval, we build one local index with a fixed
> `search(query, k)` interface and nothing else — and the reason I lead with isn't cost, it's that
> our retrieval need was small and well specified, so we designed the interface first and deferred
> the implementation until we could measure whether embeddings actually beat keyword matching on our
> own corpus. The second reason is blast radius: every document loader is a parser reading bytes a
> stranger chose, and every package we don't install is a package we don't have to review. On
> harnesses, I'd studied the paid model-native one at docs level and then ran the open-source
> equivalent on a real multi-ticket task, counted the turns, and compared them against a plain agent
> on the same task — so I can tell you what planning costs rather than whether it sounds good. If I
> adopted it, it would sit behind one named function in one branch of the flow, with a request budget
> attached and a sandboxed filesystem, because it's a 0.x dependency and I want its breaking changes
> to be a one-file problem."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 41
```
