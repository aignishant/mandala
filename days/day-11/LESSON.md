---
day: 11
phase: 2
phase_name: "OpenAI Agents SDK core"
title: "Contracts and conversations"
ids: ["OAI-05", "OAI-06"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 11 — Contracts and conversations

**Phase 2 · OpenAI Agents SDK core** · IDs: **OAI-05 🛠️**, **OAI-06 🛠️**

> **Yesterday:** tools, the Runner, and an error policy you chose rather than inherited.
> **Today:** `output_type` and `Session` — Day 4's schema and Day 7's session, handed to you. Both
> are one line. Both have a detail worth checking, and you are the only person who will check them.
> **Tomorrow:** context injection and guardrails.

```bash
./m start 11
./m scaffold 11
```

---

## §1 The story

Today is the day the framework starts to feel like a gift, and it is also the day you learn to be a
slightly suspicious recipient.

`TriageResult` took you a whole day to build properly on Day 4 — the tool-as-schema trick,
`tool_choice` to force the channel, `model_validate_json` at the boundary. Today it is:

```python
Agent(..., output_type=TriageResult)
```

One argument. And it is genuinely better than your version, because the SDK handles retries on
malformed output and picks the right mechanism per provider.

Your session file — atomic writes, tool-call-aware trimming, path validation — took most of Day 7.
Today it is:

```python
session = SQLiteSession("ticket-4521", ".mandala/sessions.db")
result = await Runner.run(agent, question, session=session)
```

Two lines.

**Here is the discipline for days like this.** When a framework hands you something you built by
hand, do not just delete your version and move on. Ask the one question your hand-built version
qualifies you to ask:

> *"I know this problem has a nasty edge. Does theirs handle it?"*

For sessions, you know exactly what that edge is: **naive trimming orphans a tool message whose
assistant request fell outside the window**, and the failure is a silently confused model rather
than an exception. You spent Day 7 on it. So today you find out whether the SDK's history limiting
has the same hole — and if it does, you now know something about your dependency that its own docs
do not tell you.

That is what six days of building from scratch buys you: not nostalgia, but **the ability to
interrogate a dependency.**

---

## §2 Setup — run this

No new packages — `SQLiteSession` uses the standard library's `sqlite3`.

```bash
mkdir -p days/day-11/lab
touch days/day-11/lab/typed_agent.py
touch days/day-11/lab/session_demo.py
touch days/day-11/lab/session_edges.py
touch tests/test_output_type.py
touch tests/test_sdk_session.py
```

Make sure the session database is ignored — it is a run artifact:

```bash
grep -qx '\.mandala/' .gitignore || echo '.mandala/' >> .gitignore
mkdir -p .mandala
```

---

## §3 OAI-05 — Structured outputs (`output_type`)

### The plain idea

Give the `Agent` an `output_type` and `result.final_output` is an instance of that type instead of a
string. The SDK picks the mechanism — provider-native structured output where available, tool-call
enforcement otherwise — and validates before handing it back.

That "picks the mechanism" clause is doing real work. On Day 4 you wrote all three techniques and
measured them because **support varies by provider**, and on the LiteLLM adapter you are talking to
three different providers. The SDK abstracts that choice. Whether it abstracts it *correctly* on
your backend is something you verify today, once, and then stop worrying about.

### 3.1 `days/day-11/lab/typed_agent.py`

```python
"""TriageResult from Day 4, now as output_type. Same schema, one line of wiring.

Run:
    uv run python days/day-11/lab/typed_agent.py T-1001
    uv run python days/day-11/lab/typed_agent.py T-1006     # the vague one
"""

from __future__ import annotations

import asyncio
import json
import sys

from agents import Agent, Runner
from agents.exceptions import ModelBehaviorError

from mandala.prompts import TRIAGE
from mandala.schemas import TriageResult
from mandala.sdk import DEFAULT_SETTINGS, make_model
from mandala.sdk_tools import get_ticket, search_tickets

triage_agent = Agent(
    name="Triage",
    instructions=TRIAGE.render(),
    model=make_model("groq"),
    model_settings=DEFAULT_SETTINGS,
    tools=[get_ticket, search_tickets],
    output_type=TriageResult,
)


async def triage(ticket_id: str) -> TriageResult:
    result = await Runner.run(triage_agent, f"Triage ticket {ticket_id}.", max_turns=6)
    return result.final_output


async def main() -> None:
    ticket_id = sys.argv[1] if len(sys.argv) > 1 else "T-1001"
    try:
        outcome = await triage(ticket_id)
    except ModelBehaviorError as exc:
        print(f"model failed to produce a valid {TriageResult.__name__}: {exc}")
        return

    print(json.dumps(outcome.model_dump(), indent=2))
    print(f"\ntype:               {type(outcome).__name__}")
    print(f"needs_human_review: {outcome.needs_human_review()}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- `output_type=TriageResult` — **the whole feature.** Compare with Day 4: no `SUBMIT_TOOL`
  definition, no `tool_choice`, no `model_validate_json`. The Pydantic class you already had is the
  only input.
- `result.final_output` is now a `TriageResult`, not a `str`. The `-> TriageResult` annotation on
  `triage()` is honest.
- `except ModelBehaviorError` — the SDK's exception when the model cannot produce valid output after
  its retries. **Verify this exception name and import path in 0.22.0** before relying on it. It is
  the SDK's equivalent of your Day-4 `ValidationError` escaping.
- `outcome.needs_human_review()` — **your method from Day 4, still working.** The schema carried its
  behaviour across a framework boundary intact. That is the payoff for putting policy on the model
  rather than in the caller.
- Note the agent still has `tools=[...]`. Structured output and tool use compose: the model may call
  tools for several turns and *then* produce the typed result. That is a genuine improvement over
  Day 4's `tool_choice`-forced single call, which could not look anything up first.

### 3.2 The three things to verify (this is today's real work for OAI-05)

The SDK docs are explicit that the LiteLLM adapter is **best-effort and beta**, and that you should
validate structured output, tool calling and usage reporting on your specific backend. So:

**(1) Which mechanism is actually being used on Groq?**

Run with `litellm.set_verbose = True` (Day 9's technique) and look at the outgoing request. Is there
a `response_format` with a JSON schema, or is there a synthetic tool the SDK invented? Write the
answer down. It determines what happens when the schema gets more complex.

**(2) Does it retry on malformed output, and how many times?**

Force a failure: temporarily add a field with an impossible constraint (say
`weird: int = Field(ge=10, le=5)`), run it, and count requests in
`result.context_wrapper.usage.requests`. **A hidden retry is a hidden request**, and on a free tier
that is a budget line you did not know you had.

**(3) Does `Literal` survive the round trip?**

Day 4's entire argument for `Literal` over `str` was that a drifted label fails loudly. Confirm the
SDK still enforces it — try to make the model emit `"HIGH"` and check you get a
`ModelBehaviorError` rather than a `TriageResult` with a bad value. **A validated boundary you have
not tried to violate is an assumption.**

---

## §4 OAI-06 — Sessions and memory

### 4.1 The session zoo

The SDK ships several backends and a couple of wrappers. Only some are relevant on $0:

| Class | Backend | Use for Mandala? |
|---|---|---|
| `SQLiteSession` | file or `:memory:` | ✅ **yes** — this is your Day-7 replacement |
| `OpenAIConversationsSession` | OpenAI Conversations API | ❌ needs a paid key |
| `OpenAIResponsesCompactionSession` | wrapper, auto-compaction | ❌ Responses-only |
| `AsyncSQLiteSession` | `aiosqlite` | later, if a lab blocks on IO |
| `RedisSession`, `SQLAlchemySession`, `MongoDBSession`, `DaprSession` | external services | ❌ not free/local by default |
| `EncryptedSession` | wrapper over any session | 🅿️ know it exists |
| `AdvancedSQLiteSession` | SQLite + branching/analytics | 🅿️ relevant to Day 51 time travel — note it |

**Two of these rows are the free/paid boundary again**, in a place you would not expect it. Session
storage sounds like plumbing, and two of the built-in options are OpenAI-hosted. Notice that
pattern — it recurs.

### 4.2 The protocol — four methods

Every session implements the same four async methods:

```python
async def get_items(limit: int | None = None) -> list[TResponseInputItem]
async def add_items(items: list[TResponseInputItem]) -> None
async def pop_item() -> TResponseInputItem | None
async def clear_session() -> None
```

Compare with your Day-7 `JsonSession`:

| SDK | Yours | Note |
|---|---|---|
| `get_items(limit=...)` | `load(window=...)` | **the interesting one — see §4.4** |
| `add_items([...])` | `extend([...])` | same |
| `clear_session()` | `clear()` | same |
| `pop_item()` | — | **new**: undo the last item. Useful for "regenerate that answer". |

Because it is a protocol, **you could pass your own `JsonSession`** if it implemented these four
methods. Worth knowing: the seam is open, so a framework's storage choice is not a lock-in.

### 4.3 `days/day-11/lab/session_demo.py`

```python
"""Multi-turn conversation with SQLiteSession. Day 7's file, two lines.

Run it three times with the same id:
    uv run python days/day-11/lab/session_demo.py t-4521 "my login loops after SSO"
    uv run python days/day-11/lab/session_demo.py t-4521 "how many others are affected?"
    uv run python days/day-11/lab/session_demo.py t-4521 "what did I first tell you?"
"""

from __future__ import annotations

import asyncio
import sys

from agents import Agent, Runner, SQLiteSession

from mandala.prompts import TRIAGE
from mandala.sdk import DEFAULT_SETTINGS, make_model
from mandala.sdk_tools import get_ticket, search_tickets

DB = ".mandala/sessions.db"

agent = Agent(
    name="Support",
    instructions=TRIAGE.render(),
    model=make_model("groq"),
    model_settings=DEFAULT_SETTINGS,
    tools=[get_ticket, search_tickets],
)


async def main() -> None:
    session_id = sys.argv[1] if len(sys.argv) > 1 else "scratch"
    user_text = " ".join(sys.argv[2:]) or "hello"

    session = SQLiteSession(session_id, DB)

    before = len(await session.get_items())
    result = await Runner.run(agent, user_text, session=session, max_turns=6)
    after = len(await session.get_items())

    print(result.final_output)
    print(f"\nsession {session_id}: {before} -> {after} items")
    print(f"usage: {result.context_wrapper.usage}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- `SQLiteSession(session_id, DB)` — two arguments: the conversation id and the database file. With
  one argument it is **in-memory** and vanishes when the process exits, which is a fine default for
  tests and a trap in a demo.
- `session=session` passed to `Runner.run` — that is the entire integration. The Runner loads the
  history, prepends it, runs, and appends the new items. **You did all of that by hand on Day 7**,
  and you will notice you are no longer thinking about it.
- `before` / `after` counts — **watch the item count grow.** This is the thing you must keep an eye
  on, because every item is context resent on every turn (Day 4), and nothing here trims it for you
  by default.
- **Note what is missing compared with your Day-7 version:** you never validated `session_id`. If it
  comes from user input, is a malicious id dangerous here? For SQLite it is a row key rather than a
  filename, so path traversal does not apply — but check whether it is parameterised or interpolated
  into SQL. **Reading a dependency's source for one specific worry is a fifteen-minute habit worth
  having**, and this is a good, small one to practise on.

Run it three times, then look at the database:

```bash
uv run python -c "import sqlite3;c=sqlite3.connect('.mandala/sessions.db');print([r for r in c.execute('SELECT name FROM sqlite_master WHERE type=\'table\'')])"
```

### 4.4 `days/day-11/lab/session_edges.py` — the interrogation

This is the day's most valuable half hour.

```python
"""Does the SDK's history limiting have Day 7's tool-orphaning bug?

Day 7 taught you: naively keeping the last N items can retain a `tool` message
whose assistant tool-call fell outside the window. The model then sees an answer
to a question it cannot see, and behaves oddly WITHOUT erroring.

Find out whether SessionSettings(limit=...) and session_input_callback have the
same hole. Whatever you discover, write it down.

Budget: ~12 requests. Groq.

Run:
    uv run python days/day-11/lab/session_edges.py
"""

from __future__ import annotations

import asyncio

from agents import Agent, RunConfig, Runner, SQLiteSession
from agents.run import SessionSettings          # verify this import path in 0.22.0

from mandala.sdk import DEFAULT_SETTINGS, make_model
from mandala.sdk_tools import get_ticket, search_tickets

agent = Agent(
    name="EdgeLab",
    instructions="Answer using the tools. Be brief.",
    model=make_model("groq"),
    model_settings=DEFAULT_SETTINGS,
    tools=[get_ticket, search_tickets],
)


def keep_recent(history: list, new_input: list) -> list:
    """The naive trim from the SDK docs. Day 7 says this shape orphans tool messages."""
    return history[-6:] + new_input


async def main() -> None:
    session = SQLiteSession("edge-test", ":memory:")

    # 1. build a history that definitely contains assistant->tool pairs
    for question in (
        "What severity is T-1001?",
        "And T-1004?",
        "Search for tickets about invoices.",
        "What about T-1010?",
    ):
        await Runner.run(agent, question, session=session, max_turns=4)

    items = await session.get_items()
    print(f"history items: {len(items)}")
    for i, item in enumerate(items):
        role = item.get("role") or item.get("type")
        has_calls = "tool_calls" in item or item.get("type") == "function_call"
        is_result = item.get("type") == "function_call_output" or item.get("role") == "tool"
        print(f"  {i:>2}. {str(role):<18} calls={has_calls} result={is_result}")

    # 2. take a naive window and see whether it starts with an orphaned tool result
    window = items[-6:]
    first = window[0]
    orphaned = (
        first.get("role") == "tool" or first.get("type") == "function_call_output"
    )
    print(f"\nnaive window[-6:] starts with an orphaned tool result: {orphaned}")

    # 3. does the SDK's own limiting produce the same shape?
    result = await Runner.run(
        agent,
        "Summarise what we have discussed.",
        session=session,
        max_turns=4,
        run_config=RunConfig(session_settings=SessionSettings(limit=6)),
    )
    print(f"\nwith SessionSettings(limit=6): {result.final_output[:200]}")

    # 4. and with the docs' own callback example?
    result = await Runner.run(
        agent,
        "Summarise what we have discussed.",
        session=session,
        max_turns=4,
        run_config=RunConfig(session_input_callback=keep_recent),
    )
    print(f"\nwith session_input_callback:   {result.final_output[:200]}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- `SQLiteSession("edge-test", ":memory:")` — in-memory, so the experiment leaves nothing behind.
- Step 1 builds four turns *that involve tools*, because an orphaning bug can only appear where
  assistant→tool pairs exist. A history of plain messages would prove nothing.
- The printing loop checks both dict shapes — `role`/`tool_calls` (Chat Completions style) and
  `type: function_call` / `function_call_output` (Responses style). **You do not yet know which shape
  the SDK stores through LiteLLM.** Printing both and seeing which is populated *is* the finding.
- `items[-6:]` then checking whether `window[0]` is a tool result — **the same check your Day-7
  `_trim_safely` performs.** If this prints `True`, the naive window has the bug, and the docs'
  `keep_recent_history` example has it too.
- Steps 3 and 4 run both official limiting mechanisms. Look for degraded answers — confused
  references, "I don't have that information" about something clearly in the window, or an outright
  provider error about mismatched tool ids.

**Write your finding in `docs/CHANGELOG_PLAN.md` regardless of the outcome.** Both results are
valuable:

- If the SDK handles it → you can delete `_trim_safely` and you know why it is safe to.
- If it does not → you have found a real limitation of a dependency, you can pass a
  `session_input_callback` that reuses your Day-7 logic, and you have a genuinely good interview
  story about a bug you found by having built the thing yourself first.

---

## §5 The eval that must be able to fail

### `tests/test_output_type.py`

```python
"""output_type behaviour, and the guarantees Day 4 depends on."""

import pytest

from mandala.schemas import TriageResult


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_final_output_is_a_typed_object_not_a_string():
    from typed_agent import triage

    result = await triage("T-1001")
    assert isinstance(result, TriageResult)
    assert not isinstance(result, str)


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_schema_behaviour_survives_the_framework():
    """needs_human_review() is policy attached to the schema. It must still work."""
    from typed_agent import triage

    assert (await triage("T-1008")).needs_human_review() is True     # critical


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_literal_constraint_is_still_enforced():
    """Day 4's entire argument for Literal was loud failure. Confirm it survived."""
    from typed_agent import triage

    result = await triage("T-1007")
    assert result.severity in ("low", "medium", "high", "critical")
    assert result.category in ("auth", "billing", "data", "howto", "other")


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_agent_can_use_tools_before_producing_typed_output():
    """A real improvement over Day 4's forced single tool_choice call."""
    from agents import Runner
    from typed_agent import triage_agent

    result = await Runner.run(triage_agent, "Triage ticket T-1004.", max_turns=6)
    kinds = [type(i).__name__ for i in result.new_items]
    assert any("ToolCall" in k for k in kinds), f"never looked the ticket up: {kinds}"
    assert isinstance(result.final_output, TriageResult)


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_structured_output_retries_are_counted():
    """A hidden retry is a hidden request. Know your budget."""
    from typed_agent import triage_agent
    from agents import Runner

    result = await Runner.run(triage_agent, "Triage ticket T-1006.", max_turns=6)
    requests = result.context_wrapper.usage.requests
    assert requests is not None, "usage.requests is not populated on this backend — find out why"
    assert requests <= 6, f"more requests ({requests}) than turns — hidden retries"
```

- `test_agent_can_use_tools_before_producing_typed_output` — asserts the composition that Day 4 could
  not do. **When a framework gives you something genuinely better, test that it does**, so a future
  regression is visible.
- `test_structured_output_retries_are_counted` — the budget test. Its `assert requests is not None`
  half is the important one on this stack: it converts "the docs warned usage may be missing" into
  a fact about *your* backend.

### `tests/test_sdk_session.py`

```python
"""Session behaviour, including the edge Day 7 taught you to look for."""

import pytest
from agents import SQLiteSession


@pytest.mark.asyncio
async def test_session_protocol_round_trip():
    """0 model requests — the four protocol methods are pure storage."""
    session = SQLiteSession("unit-test", ":memory:")
    await session.add_items([{"role": "user", "content": "hi"}])
    assert len(await session.get_items()) == 1

    popped = await session.pop_item()
    assert popped is not None
    assert await session.get_items() == []


@pytest.mark.asyncio
async def test_clear_session_empties_it():
    session = SQLiteSession("unit-test-2", ":memory:")
    await session.add_items([{"role": "user", "content": str(i)} for i in range(5)])
    await session.clear_session()
    assert await session.get_items() == []


@pytest.mark.asyncio
async def test_get_items_limit_returns_the_most_recent():
    session = SQLiteSession("unit-test-3", ":memory:")
    await session.add_items([{"role": "user", "content": str(i)} for i in range(10)])
    recent = await session.get_items(limit=3)
    assert len(recent) == 3
    assert recent[-1]["content"] == "9", "limit must return the MOST RECENT, not the first"


@pytest.mark.asyncio
async def test_naive_window_can_orphan_a_tool_result():
    """Day 7's edge, asserted rather than assumed. Adjust to whatever you FOUND in §4.4."""
    session = SQLiteSession("unit-test-4", ":memory:")
    await session.add_items([
        {"role": "user", "content": "q"},
        {"role": "assistant", "tool_calls": [{"id": "call_1", "type": "function",
                                              "function": {"name": "get_ticket", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "call_1", "content": "{}"},
        {"role": "assistant", "content": "answer"},
    ])
    items = await session.get_items(limit=2)
    first_is_orphan = items[0].get("role") == "tool"
    # TODO(me): assert the behaviour you ACTUALLY observed, and cite your finding
    #           in docs/CHANGELOG_PLAN.md. Do not assert a hope.
    assert first_is_orphan in (True, False)
```

- `test_get_items_limit_returns_the_most_recent` — **verifies which end `limit` takes from.** The
  docs say "N recent items"; this asserts it against your version. Getting this backwards silently
  would mean every conversation resends its *opening*, forever.
- `test_naive_window_can_orphan_a_tool_result` with its `TODO(me)` — deliberately not pre-decided.
  Your job is to run §4.4, observe the truth, and **encode the truth**, not the hope. If the SDK
  handles it, assert that; if it does not, assert that and add a `session_input_callback` using your
  Day-7 logic.

---

## §6 Traps

- **`SQLiteSession("id")` with one argument in a demo.** In-memory; the "persistence" vanishes on
  exit and you will be very confused.
- **Assuming `output_type` costs one request.** Retries on malformed output are extra requests. Count
  them.
- **Deleting `mandala/session.py` today.** Keep it until §4.4 tells you whether you need
  `_trim_safely` as a `session_input_callback`.
- **Reaching for `OpenAIConversationsSession`.** Paid. Same for the compaction wrapper.
- **Letting the session grow unbounded.** Nothing trims by default. Every item is context, resent
  every turn (Day 4).
- **Trusting `SessionSettings(limit=...)` without looking at what it produces.** That is what §4.4 is
  for.
- **Asserting a hope in `test_naive_window_can_orphan_a_tool_result`.** Encode what you measured.
- **Forgetting that `Literal` enforcement is the *provider's* job now.** Verify it on Groq before
  relying on it in Phase 12.

---

## §7 Request budget

| Activity | Requests |
|---|---|
| `typed_agent.py` across a few tickets | ~10 (Groq) |
| The three OAI-05 verifications | ~12 (Groq) |
| `session_demo.py` × 3 runs | ~6 (Groq) |
| `session_edges.py` | ~12 (Groq) |
| Cassettes | ~10 |
| **Total** | **≈ 50, Groq** |

`tests/test_sdk_session.py` costs **0** — session storage is local state, so it is testable offline.

---

## §8 Verify before you code

Written **2026-08-20** against `openai-agents` **0.22.0**.

- `https://openai.github.io/openai-agents-python/sessions/` — the session classes,
  the four protocol methods, `SessionSettings(limit=...)`, and `session_input_callback`.
  **Confirm the import path for `SessionSettings`** — this lesson guesses `agents.run`.
- `https://openai.github.io/openai-agents-python/agents/#output-types` — `output_type`, what happens
  on invalid output, and whether the retry count is configurable.
- `https://openai.github.io/openai-agents-python/ref/exceptions/` — confirm `ModelBehaviorError`.
- The docs' standing note that the LiteLLM adapter is **best-effort/beta** and structured output
  should be validated per backend. §3.2 is that validation; do not skip it.

---

## §9 Say it in an interview

> "Structured output is one argument once you're in the framework — you pass the Pydantic model as
> `output_type` and the SDK picks the mechanism per provider. What I actually checked was the three
> things underneath: which mechanism it chose on my backend, whether retries on malformed output
> cost extra requests I hadn't budgeted, and whether `Literal` enum constraints still failed loudly
> rather than being coerced. That last one matters because the whole reason I use `Literal` instead
> of `str` is that a drifted label should fail at the boundary."

> "Sessions were more interesting. I'd hand-built one earlier, so I knew the nasty edge: naively
> keeping the last N items can retain a tool result whose assistant tool-call fell outside the
> window, and the model gets quietly confused instead of erroring. So the first thing I did with the
> built-in session was construct a history with tool pairs and check whether the documented history
> limiting had the same hole. Having built the thing myself is what let me ask that question at all
> — otherwise I'd have trusted it, shipped it, and found out in production."

---

## §10 Done when

```bash
./m check
./m done 11
```

Tomorrow: context objects and guardrails — dependency injection for agents, and fast checks that
trip before an expensive run continues.
