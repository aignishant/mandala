---
day: 39
phase: 6
phase_name: "LangChain 1.x"
title: "Middleware — the 1.x extension story"
ids: ["LC-07", "LC-08"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 39 — Middleware: the 1.x extension story

**Phase 6 · LangChain 1.x** · IDs: **LC-07 🛠️**, **LC-08 🛠️**

> **Yesterday:** one function built the whole agent, and it turned out to be a compiled graph.
> **Today:** how you change that agent without touching it. Middleware is 1.x's answer to "the
> framework does 90% of what I want" — hooks before and after the model, around tool calls, and over
> the context itself. It is also Mandala's **third** implementation of a guardrail, and the
> comparison is the day's real content.
> **Tomorrow:** streaming and short-term memory.

```bash
./m start 39
./m scaffold 39
```

---

## §1 The story

Every framework eventually faces the same question: **the user needs to change behaviour we did not
anticipate. How?**

- **Subclassing** — the 2010s answer. Override a method, inherit the rest. Brittle: your subclass is
  coupled to internals, and a minor release breaks it.
- **Callbacks** — CrewAI's answer (Day 28, CR-12). Observe, do not intervene. Great for tracing,
  useless for stopping something.
- **Guardrails** — the Agents SDK's answer (Day 12, OAI-08). Validators that trip before or after a
  run. Intervening, but at the edges only.
- **Middleware** — LangChain 1.x's answer, and today's. Hooks at named points *inside* the loop, each
  one able to read, rewrite, or halt.

The plan's LC-07 row is explicit that this replaces subclassing, and that is a deliberate design
stance worth respecting: **1.x would rather give you five named hook points than one open class.**
Fewer places to reach in means fewer places a minor release can break — the same trade CEL made on
Day 34 by refusing to be Turing-complete.

Today you build one middleware (a PII scrubber) and tour the built-ins (LC-08), of which **two matter
disproportionately for Mandala**: summarization, because Day 4's context budget has been a manual
concern for thirty-five days; and HITL, because you built that by hand on Day 33 and can now compare.

---

## §2 Setup — run this

### 2.1 No new packages

```bash
grep -n 'langchain' pyproject.toml
```

### 2.2 Create today's files

```bash
touch src/mandala/lc/middleware.py
touch tests/test_lc_middleware.py
mkdir -p days/day-39/lab
touch days/day-39/lab/hook_order.py
touch days/day-39/lab/scrub_demo.py
```

- `hook_order.py` costs **0 requests** and is the most useful file today: it prints the order the
  hooks actually fire in. Documentation tells you they exist; a run tells you when.

---

## §3 LC-07 — writing a middleware

### 3.1 The hook points

| Hook | Fires | Can it stop the run? | Mandala's use |
|---|---|---|---|
| `before_agent` | once, at the start | yes | request-id stamping |
| `before_model` | before **every** model call | yes | **PII scrub, context trim** |
| `wrap_tool_call` | around each tool call | yes | permission check (Day 12) |
| `after_model` | after every model call | yes | output validation |
| `after_agent` | once, at the end | — | audit record |

**The row to internalise is `before_model`, and the word is *every*.** A ReAct loop calls the model
once per iteration, so a `before_model` hook on a six-step agent runs six times. If your hook is
expensive — a regex over a growing message list, or worse, another model call — you have made every
turn slower and possibly costlier. **Write `before_model` hooks as if they run in a loop, because
they do.**

### 3.2 `src/mandala/lc/middleware.py`

```python
"""Mandala's middleware: guardrails, LangChain-style.

Third implementation of the same idea:
  Day 12  SDK guardrails      -- validators at the run boundary
  Day 27  CrewAI task guards  -- validators on a task's output, with retries
  Day 39  LC middleware       -- hooks INSIDE the loop, before and after each call

The difference that matters: middleware sees every turn, not just the edges. That
is more power and more responsibility -- a before_model hook runs once per model
call, so its cost is multiplied by the loop length.

Blast radius (Principle 6): scrubbing REWRITES what the model sees. A scrubber
with a bad regex silently changes the input to every call. Hence §5's tests.

Usage
-----
    >>> from mandala.lc.middleware import PIIScrubber
    >>> PIIScrubber().scrub("card 4111 1111 1111 1111")
    'card [REDACTED:card]'
"""

from __future__ import annotations

import re

from langchain.agents.middleware import AgentMiddleware

#: Ordered, named, and testable. A tuple of (label, compiled pattern).
PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("card", re.compile(r"\b(?:\d[ -]*?){13,16}\b")),
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b")),
    ("bearer", re.compile(r"\b(?:sk|gsk|sk-or)[-_][A-Za-z0-9]{16,}\b")),
)

MAX_SCRUB_CHARS = 20_000


class PIIScrubber(AgentMiddleware):
    """Redact secrets and personal data before they reach any provider.

    Why this exists on THIS project specifically: docs/RATE_BUDGET.md standing rule
    6 records that Gemini free-tier prompts may be used to train Google models. A
    fixture that accidentally contains a real-looking key is a fixture that leaves.
    """

    def scrub(self, text: str) -> str:
        if len(text) > MAX_SCRUB_CHARS:
            text = text[:MAX_SCRUB_CHARS]
        for label, pattern in PATTERNS:
            text = pattern.sub(f"[REDACTED:{label}]", text)
        return text

    def before_model(self, state, runtime):
        """Rewrite message content in place-ish: return updated state, do not mutate."""
        messages = state["messages"]
        cleaned = [
            m.model_copy(update={"content": self.scrub(m.content)})
            if isinstance(m.content, str) else m
            for m in messages
        ]
        if cleaned == messages:
            return None
        return {"messages": cleaned}
```

**Line by line:**

- `PATTERNS` as a **module-level tuple of compiled patterns**, not regexes inline in the method.
  Compiled once at import rather than on every one of six turns (§3.1's "runs in a loop"), and
  importable by the tests so §5 can assert on the set rather than on behaviour alone.
- Each pattern is `(label, pattern)` so the replacement says **what** was redacted:
  `[REDACTED:card]`, not `[REDACTED]`. A scrubbed transcript you cannot interpret is a debugging
  problem you have created for yourself.
- `r"\b(?:\d[ -]*?){13,16}\b"` for cards — deliberately loose, and it will produce false positives on
  long digit strings. **That is the correct bias here:** over-redacting a ticket costs you a slightly
  worse answer; under-redacting sends a card number to a provider that may train on it. Say the
  trade-off out loud rather than pretending the regex is right.
- The `bearer` pattern matches `sk`, `gsk` and `sk-or` prefixes — **your own three providers' key
  formats** (Day 1: `gsk_` for Groq, `sk-or-v1-` for OpenRouter). The most likely secret to leak into
  a prompt on this project is one of your own keys, pasted into a fixture during debugging.
- `MAX_SCRUB_CHARS` — a regex over an unbounded string is a denial-of-service on yourself. Truncating
  before scrubbing bounds the work per turn. **Note what this trades:** content past 20k characters is
  dropped entirely rather than scrubbed, which is safe for leakage and lossy for meaning. Correct
  for Mandala (tickets are small); write it down so nobody is surprised.
- `class PIIScrubber(AgentMiddleware)` — subclassing the *middleware base*, not the agent. The
  framework's extension point is a class you implement, and the framework internals stay closed. That
  is the §1 argument made concrete.
- `def before_model(self, state, runtime)` — receives graph state (Day 38: the agent is a graph, so
  `state["messages"]` is the same list you printed yesterday) and a runtime handle.
- `m.model_copy(update={"content": ...})` — **copy, never mutate.** Same rule as Day 32's `scrub()`,
  and the reason is the same: mutating shared objects corrupts anything else holding a reference,
  and here that includes the trace.
- `if isinstance(m.content, str) else m` — Day 37's lesson applied. Content may be a **list of
  blocks**, and a naive `re.sub` on a list raises. This branch skips block-lists rather than handling
  them, which is a **known gap**: a secret inside a text block is not scrubbed. Write that in the
  checklist as an open item rather than leaving it implicit — an incomplete security control that
  you have documented is honest; one you have forgotten is a hole.
- `if cleaned == messages: return None` — **returning `None` means "no change".** Returning a state
  update on every turn even when nothing changed makes every checkpoint and every trace noisier, and
  on Day 47 it would mean writing a checkpoint per turn for nothing.

### 3.3 `days/day-39/lab/hook_order.py` — 0 model requests

```python
"""Print the order hooks actually fire in. Documentation says what; this says when.

Run:
    uv run python days/day-39/lab/hook_order.py

Budget: 0 requests -- the fake model returns a canned reply.
"""

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.language_models.fake_chat_models import FakeListChatModel

CALLS: list[str] = []


class Tracer(AgentMiddleware):
    def before_agent(self, state, runtime):
        CALLS.append("before_agent")

    def before_model(self, state, runtime):
        CALLS.append(f"before_model#{sum(c.startswith('before_model') for c in CALLS) + 1}")

    def after_model(self, state, runtime):
        CALLS.append("after_model")

    def after_agent(self, state, runtime):
        CALLS.append("after_agent")


model = FakeListChatModel(responses=["severity: high"])
agent = create_agent(model=model, tools=[], middleware=[Tracer()])
agent.invoke({"messages": [("user", "checkout is down")]})

print(" -> ".join(CALLS))
```

**Line by line:**

- `FakeListChatModel(responses=[...])` — **LangChain ships a fake model, and this is the single most
  practical thing in today's lesson.** It satisfies the `BaseChatModel` interface and returns canned
  replies, so the entire agent machinery runs at zero cost with no key. Every framework in this plan
  has some version of this; the ones that do not are much harder to test.
- `middleware=[Tracer()]` — a **list**, and order matters. §3.4.
- The `before_model` counter uses a generator expression over `CALLS` so the printed trace shows
  `before_model#1`, `#2`... **making §3.1's "every turn" claim visible** rather than asserted.
- `" -> ".join(CALLS)` — one line of output that answers the day's structural question. Paste it in
  your notes; Day 42's ADR-002 comparison table wants it.
- **Extend this file yourself:** add a tool, make the fake model emit a tool call, and watch how many
  times `before_model` fires. That experiment is where the cost intuition actually forms.

### 3.4 Order, and the sandwich

Middleware composes as a **stack**: `before_*` hooks run in list order, `after_*` hooks run in
reverse. Standard middleware semantics, and it has one consequence worth stating:

> **The scrubber must be first in the list.** Anything before it sees unscrubbed content.

So `middleware=[PIIScrubber(), SummarizationMiddleware(...)]`, never the reverse. §5 tests the order,
because it is the kind of thing that gets shuffled during a merge and produces no error at all.

---

## §4 LC-08 — the built-in tour

The plan names three families. Take each personally, because you have hand-built two of them.

### 4.1 Summarization — context compaction

**What it does:** when the message history approaches a token budget, it replaces older messages with
a summary.

**Why it matters here:** Day 4 (AG-04) established the context window as a budget and you have
managed it by hand ever since — Day 30's `max_length` on state fields, Day 37's `le=5` on `k`, Day
39's `MAX_SCRUB_CHARS`. This is the first time a framework offers to do it automatically.

**The two things to check before trusting it, and neither is optional:**

1. **It costs a model call.** Summarizing is generation. On a free tier, an automatic summarizer is an
   automatic request you did not budget, and it fires at an unpredictable moment. Find out whether it
   uses your agent's model or takes its own, and **give it `fast_loop()` explicitly** — summarizing on
   the 50-RPD provider would be a poor use of a scarce resource.
2. **It rewrites history.** Day 8's separation rule says the writer never sees raw ticket text. A
   summarizer that compacts twelve messages into one paragraph has just produced *new* text derived
   from all of them — including, potentially, the raw body you were careful about. **Compaction can
   undo a data-flow guarantee**, and this is the sort of thing that never appears in a tutorial.
   Note it for Day 65.

### 4.2 HITL middleware — versus Day 33

You built this by hand thirty-three days ago. Compare honestly:

| | Day 33 (CrewAI, by hand) | LC-08 HITL middleware |
|---|---|---|
| Pause mechanism | raise, checkpoint, exit | interrupt inside the graph |
| Survives process death | **yes** — via `@persist` | only with a checkpointer (Day 47) |
| Reviewer is a separate process | **yes**, by design | depends on your wiring |
| Records *why* | **yes** — `Decision.reason` | probably not; it is control flow, not audit |
| Lines you wrote | ~120 | ~3 |

**Neither column wins outright, and that is the useful conclusion.** The middleware gives you the
control flow in three lines and gives you nothing that would answer "who approved this and why" at an
audit. Day 33's `Decision` model is still the right artifact; what changes is that the *pausing* no
longer has to be hand-rolled. Write that in `four_ways.md` — "framework supplies the mechanism, I
still supply the record" is a sentence that will serve you in a design review.

### 4.3 Retry and fallback

**Read this one and do not adopt it.** Day 36 §4.1 set `max_retries=0` on every model deliberately,
because Day 6's router already owns retries, backoff and provider fallback, and two stacked layers
silently multiply the request count. A retry middleware would be a **third** layer.

The general principle, worth stating cleanly: **retry belongs in exactly one place in a system, and
that place should be the one that knows the budget.** In Mandala that is `router.py`. Say no to the
built-in, and write down why — a deliberate omission you can explain is worth more in an interview
than a feature you adopted because it was there.

---

## §5 The eval that must be able to fail

### `tests/test_lc_middleware.py`

```python
"""A scrubber rewrites every prompt. Test it like the security control it is."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from mandala.lc.middleware import MAX_SCRUB_CHARS, PATTERNS, PIIScrubber


@pytest.fixture
def scrubber() -> PIIScrubber:
    return PIIScrubber()


@pytest.mark.parametrize(
    ("raw", "label"),
    [
        ("my card is 4111 1111 1111 1111 ok", "card"),
        ("write to alice@example.com please", "email"),
        ("key gsk_abcdefghijklmnopqrstuvwx here", "bearer"),
        ("token sk-or-v1-abcdefghijklmnopqrst", "bearer"),
    ],
)
def test_each_pattern_redacts(scrubber, raw, label):
    out = scrubber.scrub(raw)
    assert f"[REDACTED:{label}]" in out


def test_our_own_key_formats_are_covered(scrubber):
    """The likeliest leak on this project is one of MY keys in a fixture."""
    assert "[REDACTED:bearer]" in scrubber.scrub("GROQ_API_KEY=gsk_" + "a" * 40)


def test_ordinary_text_survives(scrubber):
    """The negative-space test. A scrubber that redacts everything passes the others."""
    text = "Ticket T-1004: checkout returns 500 since the 14:02 deploy."
    assert scrubber.scrub(text) == text


def test_scrubbing_is_bounded(scrubber):
    out = scrubber.scrub("a" * (MAX_SCRUB_CHARS * 2))
    assert len(out) <= MAX_SCRUB_CHARS


def test_patterns_are_precompiled():
    """Compiled once at import, not once per turn (§3.1)."""
    for _label, pattern in PATTERNS:
        assert hasattr(pattern, "sub")


def test_before_model_does_not_mutate_the_input(scrubber):
    original = HumanMessage("card 4111 1111 1111 1111")
    state = {"messages": [original]}
    scrubber.before_model(state, runtime=None)
    assert original.content == "card 4111 1111 1111 1111"


def test_before_model_returns_none_when_nothing_changed(scrubber):
    state = {"messages": [HumanMessage("nothing sensitive here")]}
    assert scrubber.before_model(state, runtime=None) is None


def test_block_content_is_skipped_not_crashed(scrubber):
    """KNOWN GAP: blocks are not scrubbed. Assert the gap so it stays visible."""
    blocky = AIMessage(content=[{"type": "text", "text": "card 4111 1111 1111 1111"}])
    state = {"messages": [blocky]}
    assert scrubber.before_model(state, runtime=None) is None


def test_the_scrubber_is_first_in_the_stack():
    """§3.4. Flip it: reorder the list and this goes red."""
    from mandala.lc.agent import MIDDLEWARE

    assert isinstance(MIDDLEWARE[0], PIIScrubber)
```

**Line by line:**

- `@pytest.fixture` for the scrubber — one construction, reused. Fixtures are pytest's dependency
  injection, and this is the smallest useful example of one.
- The parametrized pattern test covers **all four patterns including both key prefixes**, so a failure
  names the pattern that broke.
- `test_our_own_key_formats_are_covered` exists because of the actual threat model on this project.
  Day 1 recorded the key prefixes; this test consumes that fact.
- `test_ordinary_text_survives` is the **negative-space sibling**, and it is the one that catches an
  over-greedy regex. A scrubber that redacts everything passes every other test on this page. Third
  time this pattern has appeared (Days 32, 37, 39) — by now it should be automatic.
- `test_scrubbing_is_bounded` asserts the truncation, which also documents the lossy behaviour: the
  test's existence is where a future reader learns that content past the bound is dropped.
- `test_before_model_does_not_mutate_the_input` — the copy rule, asserted on the *original object*.
  This is the test that catches an accidental in-place edit during a refactor.
- `test_before_model_returns_none_when_nothing_changed` pins the §3.2 optimisation. Without it,
  someone "simplifies" the early return away and every turn writes a state update.
- `test_block_content_is_skipped_not_crashed` **asserts a known gap**, which is unusual and
  deliberate. The test documents that block content is not scrubbed and guarantees the code does not
  crash on it. When someone closes the gap, this test fails — and that failure is the prompt to
  update it. **A test that encodes a limitation is better than a comment that describes one.**
- `test_the_scrubber_is_first_in_the_stack` requires a `MIDDLEWARE` list exported from `agent.py`.
  Add it today and pass it to `create_agent`; ordering is a security property (§3.4) and security
  properties get tests.
- **Zero model requests in this file**, and no keys needed — the fourth day running.

---

## §6 Traps

- **A `before_model` hook that calls a model.** You have just doubled every turn. If you need a model
  in a hook, you probably want `after_agent` or a separate pass.
- **Regexes compiled inside the hook.** Six turns, six compilations, for nothing.
- **Mutating messages in place.** Corrupts the trace and anything else holding the list.
- **Assuming `content` is a `str`.** Day 37 taught this; §3.2 skips block-lists and §5 pins the gap.
- **Putting the scrubber anywhere but first.** Silent, and it defeats the control entirely.
- **Adopting the summarization middleware without checking which model it uses.** An unbudgeted
  request at an unpredictable moment.
- **Forgetting that summarization rewrites history.** It can quietly undo Day 8's separation rule.
- **Adding retry middleware.** Third retry layer. `router.py` owns retries.
- **Testing only that redaction happens.** Test that non-secrets survive, or you have shipped a
  function that returns `[REDACTED]`.
- **Treating middleware as observability.** It can halt a run; a callback cannot. That is power, and
  it means a buggy middleware breaks the agent rather than the logs.

---

## §7 Request budget

**Declared: ~6 model requests, Groq.**

| What | Requests |
|---|---|
| `hook_order.py` (fake model) | **0** |
| `tests/test_lc_middleware.py` | **0** |
| `scrub_demo.py` — one real run with the scrubber attached | ≤ 6 |

`FakeListChatModel` is why today is nearly free, and it deserves a note in the bake-off: **"can I run
this framework's full loop without a provider?"** is a testability row, and LangChain answers yes out
of the box. Check whether the other three do — the Agents SDK and CrewAI both needed a real endpoint
in your labs, and if that is a gap in your knowledge rather than in the frameworks, find out.

---

## §8 Verify before you code

Written **2026-08-20** against `langchain==1.3.16`:

- **`AgentMiddleware` import path** — `langchain.agents.middleware` is the assumption. Confirm.
- **The exact hook names and signatures.** `before_model(self, state, runtime)` is the assumption;
  1.x may pass different arguments or use a decorator style. `hook_order.py` will tell you loudly.
- **Is `wrap_tool_call` the name?** You are not using it today, but Day 66's least-privilege lab
  wants it; know it exists and what it wraps.
- **Does returning `None` from a hook mean "no change"?** §3.2 and a test both depend on it.
- **Is `middleware=` a `create_agent` parameter**, and is it ordered as a stack (before in order,
  after in reverse)? §3.4 is a security claim, so verify rather than assume.
- **Which model does `SummarizationMiddleware` use** if you do not pass one? A budget question.
- **Does `FakeListChatModel` still live in `langchain_core.language_models.fake_chat_models`?** It has
  moved before, and it is the load-bearing import for cheap testing all week.
- `https://docs.langchain.com/oss/python/langchain/middleware` — read today.

---

## §9 Say it in an interview

> "LangChain 1.x extends agents through middleware rather than subclassing — named hooks before and
> after the model, around tool calls, and at the agent boundary — so the framework's internals stay
> closed and there are five places to reach in instead of one open class. I wrote a PII scrubber as a
> `before_model` hook, and the two things I'd point at are that it copies rather than mutates, and
> that it has to be first in the stack, because anything ahead of it sees unscrubbed content — so
> ordering is a security property and there's a test asserting it. I also wrote a test that asserts a
> *gap*: message content can be a list of typed blocks, my scrubber only handles the string case, and
> I'd rather that limitation be a failing-able assertion than a comment. The built-in I deliberately
> didn't adopt was retry — I already have a rate-limit-aware router with provider fallback, and two
> retry layers silently multiply your request count and make your traces lie about it."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 39
```
