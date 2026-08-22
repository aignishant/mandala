---
day: 53
phase: 8
phase_name: "MCP (2026-07-28 spec)"
title: "Why MCP, and what the stateless core changed"
ids: ["MCP-01", "MCP-02", "MCP-12"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 53 — Why MCP, and what the stateless core changed

**Phase 8 · MCP 2026-07-28** · IDs: **MCP-01 🛠️**, **MCP-02 🛠️**, **MCP-12 🅿️**

> **Yesterday:** the Phase-7 gate — a durable core graph, killed, resumed, paused and rewound.
> **Today:** the boundary that makes the last forty days portable. You have written the same tool
> four times, once per framework. **MCP-01 is the argument that you should have written it once**, and
> **MCP-02 is what the 2026-07-28 revision changed** — a stateless core, which is a deployment
> decision disguised as a protocol detail.
> **Tomorrow:** you build `ticket-db`, the server every later phase reuses.

```bash
./m start 53
./m scaffold 53
```

---

## §1 ⚠️ First task: resolve the missing reference

**Before anything else today.** (Principle 14, and Day 52's checklist asked you to settle it last
night.)

`CLAUDE.md` line 5 and the master plan's Part 2 both name
**`docs/01_MASTER_PLAN_ADDENDUM_GAPS.md` Part 2** as *"the standing MCP reference analysis"*. That
file does not exist in this repo. `docs/03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md` Part 4
logged it and named Day 53 as the day to resolve it.

Two options, and **it is your call, not the generator's**:

1. **Carry it over** from the previous plan's repo, as the master plan's Part-10 kickoff item says.
   Then everything in Phase 8 has the reference it claims.
2. **Repoint the references.** Amend `CLAUDE.md` and the plan's Part 2 to name the MCP specification
   page plus `docs/PINS.md` as the standing reference, and delete the claim that a local analysis
   exists.

**Do one of them now and log it in `docs/CHANGELOG_PLAN.md`.** Option 2 takes five minutes and is
entirely defensible — a pointer to the live spec ages better than a snapshot of it. What is *not*
defensible is teaching six days of MCP against a reference the repo says exists and does not.

**Then verify the spec revision itself:**

```bash
# The plan is built on the 2026-07-28 revision. Confirm it is still current.
```

Open the specification's revisions page and check. If a newer revision exists, **stop and write an
addendum before teaching Phase 8** — this is the exact scenario Principle 14 was written for, and the
plan's own Part 9 notes that "the flagship protocol rewrote itself two weeks before this plan was
drafted."

---

## §2 MCP-01 — the N×M problem, and your own evidence

### 2.1 The argument

Four frameworks. K data sources. Without a boundary you write **4 × K** integrations; with one you
write **4 + K**.

That is the standard pitch and it is abstract. **You have concrete evidence, and it is better.** Count
what you actually wrote for one data source — the ticket lookup:

| Day | Framework | File | What you wrote |
|---|---|---|---|
| 10 | Agents SDK | `sdk_tools.py` | `@function_tool` wrapper |
| 25 | CrewAI | `crew/tools.py` | a `BaseTool` subclass |
| 37 | LangChain | `lc/tools.py` | `@tool` + Pydantic args schema |
| 44/48 | LangGraph | via `lc/tools.py` | (reused LangChain's — one saving already) |

**Four declarations of one function.** The function body — `RAW_TICKETS[ticket_id]` — has been
identical since Day 10. What changed each time was the *declaration*: name, schema, description,
permission wiring.

**Now count the divergence, because that is the real cost.** Go and read all four right now and
answer:

1. Do all four have the **same tool name**?
2. Does the `T-\d{4}` pattern constraint (Day 37) exist in all four, or only in LangChain's?
3. Does each one bound its result?
4. Do the descriptions — **which are prompt text** — say the same thing?

**Whatever you find is today's headline finding.** If they have drifted, that is the N×M problem
costing you correctness rather than typing, which is a much stronger argument than "it is more
lines". If they have not drifted, you have been disciplined and you should say what that discipline
cost.

### 2.2 Principle 11, and what it means for Mandala

The plan's Principle 11: **MCP is the boundary. Every data source lives behind an MCP server.**

So `RAW_TICKETS` and `kb.search()` become one server, and the four framework tool files become four
*mounts* of it. **Predict now, before Day 55 shows you:** what happens to `lc/tools.py`'s
`InjectedToolArg` (Day 37), and to `permissions.py` (Day 12), when the tool no longer lives in your
process? Write the prediction down; Day 55 will grade it.

---

## §3 MCP-02 — the stateless core

### 3.1 What the 2026-07-28 revision changed

| | Before | 2026-07-28 |
|---|---|---|
| Connection setup | an `initialize` handshake | **none** |
| Session | pinned; the client belongs to one server process | **none** |
| Routing information | inside the JSON-RPC body | **`Mcp-Method` / `Mcp-Name` HTTP headers** |
| List results | fetch per session | **cacheable, stably ordered** |

**Every row is a deployment consequence, not a protocol nicety**, and this is the framing to hold:

- **No `initialize`** → any request can go to any instance. There is no warm-up to redo.
- **No session pinning** → **no sticky sessions in your load balancer.** That single line is what lets
  Day 85 run `ticket-db` behind nginx with three replicas and prove any instance answers any request.
- **Headers carry the method and tool name** → a load balancer, a cache or a WAF can route and enforce
  **without parsing a JSON body.** The plan's MCP-02 example is exactly this: *"a load balancer routes
  `search_tickets` to a dedicated pool without parsing bodies."*
- **Cacheable, stably-ordered lists** → `tools/list` can sit behind a CDN or a local cache, and a
  client can diff two listings meaningfully. **Stable ordering is what makes "did the server's tools
  change?" answerable**, which matters more than it sounds: it is how you detect a supply-chain
  change in a third-party server (MCP-15, Day 66).

### 3.2 Why this is the most important thing in Phase 8

Stateful protocols push complexity into operations. Sticky sessions mean a deploy drops in-flight
work, autoscaling is fiddly, and a crashed instance loses its clients' context.

**Statelessness moves that complexity into the request** — every call carries what it needs — and the
result is that scaling becomes boring. **Boring scaling is the whole point.**

You have just spent ten days on the opposite discipline: LangGraph's checkpointers make your *agent*
stateful on purpose. **Those are not in tension, and being able to say why is a genuinely good
interview answer:** state belongs where it can be checkpointed and reasoned about — one place, your
graph — and the *tool boundary* stays stateless so it can be replicated freely. **Stateful core,
stateless edges.** Day 86 (LG-21) makes exactly this point from the LangGraph side, and the plan says
so: *"rhymes with MCP's stateless core on purpose."*

### 3.3 `days/day-53/lab/wire_shape.py` — 0 model requests

See the protocol on the wire before you use a library.

```python
"""What an MCP request actually looks like in 2026-07-28. No SDK, no model.

Run:
    uv run python days/day-53/lab/wire_shape.py

Budget: 0 requests. This is a protocol lab, not a model lab.
"""

import json

#: A tools/call request under the 2026-07-28 stateless core.
#: NOTE the headers -- routing information is OUTSIDE the body on purpose.
HEADERS = {
    "Content-Type": "application/json",
    "Mcp-Method": "tools/call",          # what kind of request this is
    "Mcp-Name": "search_tickets",        # which tool -- a router can read this
    # NOTE what is ABSENT: no session id, no connection token.
}

BODY = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "search_tickets",
        "arguments": {"query": "refund", "limit": 5},
    },
}

print("--- headers a load balancer can route on ---")
for k, v in HEADERS.items():
    print(f"  {k}: {v}")

print("\n--- body ---")
print(json.dumps(BODY, indent=2))

print("\n--- questions to answer from the SPEC, not from this file ---")
for q in [
    "Are Mcp-Method / Mcp-Name required, or optional hints?",
    "Must the header name match params.name, and who enforces it?",
    "What replaces `initialize` for capability discovery?",
    "What exactly makes a tools/list response cacheable -- an ETag? a version?",
    "What does 'stably ordered' guarantee, and across what -- instances? restarts?",
]:
    print(f"  - {q}")
```

**Line by line:**

- **The headers are the lesson.** Print them separately from the body, because the whole point of the
  revision is that routing information left the body. A reader who only ever sees a JSON-RPC payload
  will not notice what changed.
- The `# NOTE what is ABSENT` comment — **absences are the hard thing to see.** No session id, no
  connection token, nothing to establish. Naming the absence is how you notice it.
- The body still carries `params.name` **as well as** the header. That redundancy raises the enforcement
  question, and it is a real one: if a router trusts `Mcp-Name` and the server dispatches on
  `params.name`, a mismatch is a routing bypass. **Find out what the spec says**, because "which one
  is authoritative" is exactly the sort of question that turns into a CVE.
- **The five questions are the assignment**, and they are deliberately unanswered here. This lesson
  was written on 2026-08-20 against a spec you must read yourself (§1). Answer them from the
  specification and write the answers into this file as comments — **that turns a lab script into
  your own reference**, which is what §1's option 2 promised.

---

## §4 MCP-12 — governance, and why it matters commercially

🅿️. Three facts and one sentence you can say out loud.

- **The Agentic AI Foundation** (Linux Foundation, December 2025) governs MCP. It is not a vendor's
  protocol any more.
- **There is an official registry** of MCP servers.
- **The extensions framework** (Apps, Tasks, EMA — Day 57) means capabilities ship on independent
  timelines rather than in one monolithic spec version.

**Why an engineer should care, and it is not idealism:** a vendor-controlled protocol is a
vendor-controlled data boundary. If your ticket database speaks a protocol one company owns, your
"portable" architecture is portable at that company's discretion. **Foundation governance is what
makes Principle 11 a durable decision rather than a bet.**

The plan's own interview line, and it is a good one: *"MCP is vendor-neutral — that's why the data
boundary is safe."*

And a governance fact with immediate operational teeth: **an official registry is a supply chain.**
Day 66 (MCP-15) reviews third-party servers, and the reason that day exists is that a registry makes
installing someone else's tool server as easy as `pip install` — with the same risks, plus the tool
descriptions going straight into your model's prompt. **Note that today; it reframes MCP-15 from
paranoia into ordinary dependency hygiene.**

---

## §5 The eval that must be able to fail

Today's target is **the drift you found in §2.1**. Four declarations of one function should agree, and
until Day 54 collapses them into one server, a test is what keeps them honest.

### `tests/test_tool_parity.py`

```python
"""Four frameworks, one data source. Until MCP, a test is what keeps them agreeing."""

import re
from pathlib import Path

import pytest

FRAMEWORK_TOOLS = {
    "sdk": Path("src/mandala/sdk_tools.py"),
    "crew": Path("src/mandala/crew/tools.py"),
    "langchain": Path("src/mandala/lc/tools.py"),
}


def source(name: str) -> str:
    return FRAMEWORK_TOOLS[name].read_text(encoding="utf-8")


@pytest.mark.parametrize("name", sorted(FRAMEWORK_TOOLS))
def test_every_framework_uses_the_same_tool_name(name):
    """Flip it: rename it in one framework and this goes red."""
    assert "lookup_ticket" in source(name), name


@pytest.mark.parametrize("name", sorted(FRAMEWORK_TOOLS))
def test_every_framework_constrains_the_ticket_id(name):
    """Day 37 added a regex in ONE framework. The other three are the N x M problem."""
    text = source(name)
    assert re.search(r"T-\\?\\d\{4\}|T-\\d\{4\}", text) or "ticket_id" in text, name


@pytest.mark.parametrize("name", sorted(FRAMEWORK_TOOLS))
def test_no_framework_tool_writes(name):
    """Principle 6, across all four. The first write is Day 82, behind an approval."""
    for banned in ("RAW_TICKETS[", "= RAW_TICKETS", ".update(", "del "):
        assert f"{banned}" not in source(name).replace("RAW_TICKETS[ticket_id]", ""), (name, banned)


@pytest.mark.parametrize("name", sorted(FRAMEWORK_TOOLS))
def test_every_framework_bounds_its_result(name):
    """An unbounded tool result is an unbounded prompt (AG-04)."""
    text = source(name)
    assert any(marker in text for marker in ("[:", "max_length", "le=", "limit")), name


def test_the_underlying_function_is_shared():
    """The BODY was always the same. Only the declarations diverged -- that is MCP-01."""
    bodies = {name: "RAW_TICKETS" in source(name) for name in FRAMEWORK_TOOLS}
    assert all(bodies.values()), bodies


def test_the_count_of_declarations_is_recorded():
    """A test that documents the N x M cost. Update it when Day 55 collapses them."""
    assert len(FRAMEWORK_TOOLS) == 3, (
        "the number of per-framework tool declarations changed -- "
        "if Day 55's MCP mount removed one, update this number and celebrate"
    )
```

**Line by line:**

- `FRAMEWORK_TOOLS` as a dict of paths — **the N×M problem, as data.** Three entries (LangGraph reuses
  LangChain's), and the count itself is asserted.
- Every test is `@pytest.mark.parametrize`d over the frameworks, so a failure **names which framework
  drifted.** That is the whole point: an aggregate assertion would tell you something is wrong; this
  tells you where.
- `test_every_framework_constrains_the_ticket_id` is deliberately loose, and **it is the test most
  likely to be red today.** Day 37 added the regex in LangChain only. If it fails for `sdk` and
  `crew`, **do not weaken the test — fix those two, or write down that you are deferring it to Day
  55 when MCP makes the question moot.** Either is fine; silently loosening is not.
- `test_the_count_of_declarations_is_recorded` is unusual: a test whose job is to **notice a good
  change**. When Day 55 mounts one MCP server into all four frameworks and you delete a per-framework
  declaration, this test goes red and its message tells you to celebrate. **A test that fails on
  progress, with a message explaining why, is a nice way to make a milestone visible.**
- **Zero model requests**, and no MCP dependency yet — today is reading and comparison.

---

## §6 Traps

- **Teaching Phase 8 without resolving §1.** Six days built on a reference the repo says exists and
  does not.
- **Skipping the spec-revision check.** The plan's own history says this protocol moves fast.
- **Reading "stateless" as "no state anywhere".** Your *graph* is stateful on purpose. The *boundary*
  is stateless.
- **Assuming the headers are cosmetic.** They are what lets a router work without parsing bodies —
  and they raise a real authority question when they disagree with the body.
- **Not counting your own four declarations.** The N×M argument is abstract until it is your code.
- **Weakening `test_every_framework_constrains_the_ticket_id` because it is red.** Fix it or defer it
  in writing.
- **Treating MCP-12 as trivia.** Governance is why the boundary is safe, and a registry is a supply
  chain.
- **Installing anything today.** `mcp==2.0.0` came on Day 16; `httpx` is Day 53's ledger row but is
  needed for the **streamable-HTTP deep dive**, which is Day 55's transport work — check whether you
  actually need it before Day 54's stdio server.

---

## §7 Request budget

**Declared: 0 model requests.**

| What | Requests |
|---|---|
| Everything today | **0** |

**Two free days in ten (Day 46 and today).** Both are days where the deliverable is a decision or a
comparison rather than a behaviour. Notice the correlation and use it: **the days that cost nothing
are the days that produce the artifacts you will quote in an interview.**

---

## §8 Verify before you code

Written **2026-08-20** against **MCP spec revision 2026-07-28** and `mcp==2.0.0`:

- **Is 2026-07-28 still the current revision?** §1. This is the load-bearing check for six days.
- **Are `Mcp-Method` and `Mcp-Name` required or optional?** And on which transports — do they apply to
  stdio at all, or only to HTTP?
- **If `Mcp-Name` and `params.name` disagree, which wins?** A routing-bypass question.
- **What replaced `initialize`?** How does a client learn capabilities with no handshake — a
  `tools/list` call, a well-known document, headers?
- **What makes a `tools/list` response cacheable** — ETag, a version field, a TTL?
- **What is "stably ordered" a guarantee across** — one instance? all instances? restarts? This is
  what makes change-detection possible on Day 66.
- **`mcp==2.0.0` still current**, and does its major version still track the 2026-07-28 revision?
- **Is `httpx` needed on Day 54** (stdio) or only Day 55 (streamable HTTP)? Move the ledger row if the
  plan has it in the wrong place, and log the fix.
- The specification's own revisions page — **read today, not from memory.**

---

## §9 Say it in an interview

> "I'd written the same ticket-lookup tool four times — once per framework — and the function body
> was identical every time; only the declarations differed, and they'd drifted: one had a regex
> constraint on the ticket id and the others didn't. That's the N×M problem costing correctness
> rather than typing, which is a stronger argument than the line count. MCP makes it 4+K: one server,
> four mounts. The part of the 2026-07-28 revision I'd talk about is that the core went stateless —
> no initialize handshake, no session pinning, and the method and tool name moved into HTTP headers.
> Every one of those is a deployment consequence: no sticky sessions, so any replica answers any
> request, and a load balancer can route on the tool name without parsing a JSON body. And it sits
> deliberately opposite the design I'd just spent ten days on — my agent graph is stateful on purpose
> because state belongs somewhere it can be checkpointed and replayed. Stateful core, stateless edges.
> The governance point matters commercially too: it's a Linux Foundation protocol now, which is what
> makes 'my data boundary is portable' a durable claim rather than a bet on one vendor."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 53
```
