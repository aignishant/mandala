---
day: 36
phase: 6
phase_name: "LangChain 1.x"
title: "The 1.x mental model and the provider abstraction"
ids: ["LC-01", "LC-02"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 36 — The 1.x mental model, and the provider abstraction

**Phase 6 · LangChain 1.x** · IDs: **LC-01 🛠️**, **LC-02 🛠️**

> **Yesterday:** the Phase-5 gate — a flow that survived being killed, and three collisions found by
> assembling.
> **Today:** the fourth framework. Not the agent yet — first the **package layout** (which half of
> LangChain died in 1.0, and why), and then `init_chat_model`, which is the vendor-neutrality
> argument you have been making since Day 1 turned into one function call.
> **Tomorrow:** messages and content blocks — the other half of the abstraction.

```bash
./m start 36
./m scaffold 36
```

---

## §1 The story

You have now built the same triage agent three times:

- **Agents SDK** — the model owns the loop. You add tools, guardrails, handoffs.
- **CrewAI Crews** — roles own the loop. You describe a team.
- **CrewAI Flows** — you own the loop, in decorators.

LangChain's answer is the fourth: **the abstraction owns the loop.** One `create_agent` API over any
model, any tool, any provider. That is Day 38. Today is about the thing underneath it, because
LangChain's actual claim is not about agents at all — it is that **everything above the provider
looks the same regardless of which provider is underneath.**

You are unusually well placed to judge that claim, and you should notice why. On Day 1 you wrote
`PROVIDERS` in `models.py` — three OpenAI-compatible endpoints behind one client. On Day 6 you built
a router that falls Gemini → Groq → OpenRouter on a 429. **You have already built a provider
abstraction by hand.** So today's real question is not "is this convenient?" It is:

> **What does LangChain's abstraction give me that my forty lines do not — and what does it take?**

Keep `src/mandala/router.py` open beside the lab file today. The comparison is the lesson.

### 1.1 First: the unsigned amendment

Yesterday's closing instruction, and it is a Principle-14 gate, not a formality.

`docs/03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md` Part 3 records that **LangChain moved 1.2.x →
1.3.x** since the plan's baseline, and Part 5 has a sign-off box that is **still unticked**. Today is
the first day the package is actually installed. So:

1. Read Part 3. It is one page and it argues the drift is minor: LangChain 1.x carries a public
   no-breaking-changes-until-2.0 commitment, and every LC-* ID is a 1.x surface.
2. Decide whether you accept it. **It is your call, not the generator's** — that is what the box is
   for.
3. Tick it, log the acceptance in `docs/CHANGELOG_PLAN.md`, and bump the plan to **v1.1.1**.
4. Then install — with the version you verified *today*, not the one in the addendum.

If you install first and sign off after, you have inverted Principle 14 and the habit is what this
plan is actually teaching.

---

## §2 Setup — run this

### 2.1 Verify, then install

```bash
for p in langchain langchain-core langchain-google-genai langchain-groq langchain-openai; do
  printf "%-26s " "$p"
  curl -s --max-time 30 "https://pypi.org/pypi/$p/json" \
    | python -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
done
```

Compare against `docs/PINS.md`, then install the versions you just saw:

```bash
uv add "langchain==1.3.16" "langchain-core==1.6.0" \
       "langchain-google-genai==4.3.4" "langchain-groq==1.1.3" \
       "langchain-openai==1.6.0"
```

**Line by line:**

- **Five packages, and the split is the lesson (LC-01).** `langchain-core` holds the abstractions,
  `langchain` holds agents and middleware, and the three provider packages hold the adapters.
  Nothing else is required, and that austerity is deliberate — 1.0 was largely an exercise in
  deleting.
- `langchain==1.3.16` — the number Day 1's re-verification found (`docs/CHANGELOG_PLAN.md`,
  2026-08-20 entry), one patch above the addendum's 1.3.15. **Use what your loop above printed.** If
  it prints 1.3.17, pin that and log a line; if it prints 1.4.x, stop — that is a minor bump and it
  needs an addendum before it needs a pin.
- `langchain-openai` is installed and **no OpenAI key exists on this machine.** That is correct: it
  is the adapter used with a `base_url` pointed at OpenRouter's OpenAI-compatible endpoint (plan
  §2.1). The package name is about the *wire protocol*, not the vendor. This confuses people; say it
  once, out loud, and move on.
- No `langchain-community`. It exists, it is enormous, and nothing in this plan needs it. **Every
  package you do not install is a supply-chain surface you do not have** (AG-17, MCP-15).

### 2.2 Create today's files

```bash
touch src/mandala/lc/__init__.py
touch src/mandala/lc/chat.py
touch tests/test_lc_chat.py
mkdir -p days/day-36/lab
touch days/day-36/lab/what_survived.py
touch days/day-36/lab/provider_swap.py
```

- `src/mandala/lc/` as a package, mirroring `src/mandala/crew/` and `src/mandala/flows/`. **Four
  frameworks, four namespaces, one `schemas.py` shared between them.** That the schema is shared and
  the framework code is not is the structural expression of this plan's whole thesis.
- `what_survived.py` costs **0 requests** and is the LC-01 lab. It is an import test, and §3 explains
  why an import test is the right shape for "what died in 1.0".

---

## §3 LC-01 — the package layout, and what 1.0 deleted

### 3.1 The three-layer split

| Layer | Package | Holds | Changes |
|---|---|---|---|
| Abstractions | `langchain-core` | messages, content blocks, tools, runnables | slowly, and carefully |
| Framework | `langchain` | `create_agent`, middleware | with the 1.x line |
| Adapters | `langchain-google-genai`, `-groq`, `-openai` | one provider each | on the provider's schedule |

**Why this split is the interesting part.** Your Day-1 `models.py` put all three layers in one file:
the abstraction (`Provider`), the framework (nothing yet), and the adapter (`base_url` strings). That
was correct for forty lines. It stops being correct the moment a provider needs behaviour rather than
a URL — Gemini's safety settings, Groq's ignored parameters, OpenRouter's routing headers. **The
split exists so a provider's quirks live in the provider's package and never leak upward.** Whether
they actually stay there is §4's experiment.

### 3.2 What died, and why you care

LangChain 1.0's deprecations are not trivia — they are the most likely thing you will be asked about,
because most LangChain knowledge in the world predates them:

- **`AgentExecutor`** — deprecated, maintenance until Dec 2026, **never used in this plan.** It was
  the pre-1.0 agent loop. `create_agent` replaces it, and `create_agent` returns a *graph*.
- **The old chain classes** (`LLMChain`, `ConversationChain`, and the rest) — gone in favour of LCEL
  composition and, for agents, `create_agent`.
- **`langgraph.prebuilt`** — deprecated in the *other* direction (LG-15, Day 45): LangGraph's prebuilt
  agent now points at LangChain's `create_agent`. **The two libraries converged on one agent
  constructor**, which is the single most useful fact about the current LangChain/LangGraph
  relationship, and it is why Day 42's seam lab exists.

**The reason this matters more than usual:** a model trained on pre-1.0 material — including the one
in your editor — will confidently produce `AgentExecutor` code. So will most tutorials. Today's
`what_survived.py` exists so that you find out from the installed package rather than from a
plausible paragraph.

### 3.3 `days/day-36/lab/what_survived.py` — 0 model requests

```python
"""Ask the installed packages what exists, instead of asking a search engine.

Run:
    uv run python days/day-36/lab/what_survived.py

Budget: 0 requests. Nothing here calls a model.
"""

import importlib

import langchain
import langchain_core

print(f"langchain      {langchain.__version__}")
print(f"langchain-core {langchain_core.__version__}\n")

CANDIDATES = [
    ("langchain.agents", "create_agent"),          # the blessed loop (LC-05)
    ("langchain.agents", "AgentExecutor"),         # deprecated -- is it still importable?
    ("langchain.chat_models", "init_chat_model"),  # LC-02
    ("langchain_core.messages", "HumanMessage"),
    ("langchain_core.tools", "tool"),
    ("langchain.chains", "LLMChain"),              # expected: gone
    ("langgraph.prebuilt", "create_react_agent"),  # expected: deprecated (LG-15)
]

for module_name, attr in CANDIDATES:
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        print(f"  {module_name:<26}.{attr:<20} MODULE MISSING  ({exc.__class__.__name__})")
        continue
    found = hasattr(module, attr)
    print(f"  {module_name:<26}.{attr:<20} {'ok' if found else 'ABSENT'}")
```

**Line by line:**

- `import langchain; langchain.__version__` — print the version you are *running*, not the one in
  `pyproject.toml`. They agree today. They will disagree the first time an environment is stale, and
  that is a twenty-minute debugging session avoided.
- `importlib.import_module(name)` — import by **string at runtime**, so a missing module is a caught
  exception instead of a file that will not run. Same technique as `getattr` on Day 1; the general
  skill is "reach into the runtime by name so absence is data".
- `hasattr(module, attr)` rather than `from x import y` — you want a boolean, not a crash. This whole
  file is a survey, and a survey that stops at the first surprise is not a survey.
- **`AgentExecutor` is in the list on purpose.** Deprecated does not mean absent: it very likely
  imports fine and works. Knowing the difference between "gone" and "there but deprecated" is exactly
  the LC-01 competence, and printing it is how you learn it rather than assume it.
- `langgraph.prebuilt` is listed even though LangGraph is not installed until Day 43. Expect
  `MODULE MISSING`, and note it — you will re-run this file on Day 45 when LG-15 makes the same
  point from the other side.
- **The output of this file goes in your notes.** On Day 63 the bake-off asks about lock-in and API
  churn; "here is what the 1.0 line deleted, verified from the installed package on 2026-08-__" is
  evidence.

---

## §4 LC-02 — `init_chat_model`, and the abstraction under test

### 4.1 `src/mandala/lc/chat.py`

```python
"""Mandala's LangChain model factory. Three free providers, one function.

Why this file exists at all
---------------------------
init_chat_model already abstracts providers. Wrapping it looks redundant until you
notice what it does NOT do: it does not know about docs/RATE_BUDGET.md, it does not
know Mandala pins models by ROLE (Day 1), and it has no opinion about which provider
may judge which. Those are our policies, and policy belongs in our code.

So: init_chat_model handles the wire; this file handles the rules.

Usage
-----
    >>> from mandala.lc.chat import workhorse, judge
    >>> workhorse().model_name          # doctest: +SKIP
    'gemini-3.7-flash'
"""

from __future__ import annotations

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from mandala.config import load_keys
from mandala.models import FAST_LOOP, JUDGE, WORKHORSE

_KEYS = load_keys()

#: Which langchain provider string each Mandala role uses. Roles, not vendors (Day 1).
_ROLE_PROVIDER = {
    "workhorse": ("google_genai", WORKHORSE),
    "fast_loop": ("groq", FAST_LOOP),
    "judge": ("openai", JUDGE),          # openai ADAPTER, OpenRouter ENDPOINT -- see below
}


def _build(role: str, *, temperature: float = 0.0) -> BaseChatModel:
    provider, model_id = _ROLE_PROVIDER[role]
    kwargs: dict = {"temperature": temperature, "max_retries": 0}

    if provider == "google_genai":
        kwargs["google_api_key"] = _KEYS.gemini
    elif provider == "groq":
        kwargs["groq_api_key"] = _KEYS.groq
    elif provider == "openai":
        kwargs["api_key"] = _KEYS.openrouter
        kwargs["base_url"] = "https://openrouter.ai/api/v1"

    return init_chat_model(model_id, model_provider=provider, **kwargs)


def workhorse(**kw) -> BaseChatModel:
    """Gemini. Labs, long context, the daily driver."""
    return _build("workhorse", **kw)


def fast_loop(**kw) -> BaseChatModel:
    """Groq. Many small calls, tool-calling drills."""
    return _build("fast_loop", **kw)


def judge(**kw) -> BaseChatModel:
    """OpenRouter. Evals only. MUST differ from the provider under test (plan §2.1)."""
    return _build("judge", **kw)
```

**Line by line:**

- `from langchain.chat_models import init_chat_model` — **one function, any provider.** You pass a
  model id and a provider string and get back a `BaseChatModel`. Everything downstream — tools,
  agents, middleware, streaming — is written against that interface and does not know which vendor
  answered.
- `_ROLE_PROVIDER` keyed by **role**, importing `WORKHORSE` / `FAST_LOOP` / `JUDGE` from Day 1's
  `models.py`. Five weeks later, that decision is still paying: rotate a free model and this file
  does not change. **Do not write a model id in this file.** Day 1's rule, fourth framework.
- `temperature: float = 0.0` as a **keyword-only default**. Determinism by default is the right call
  for a system that is graded on Day 71; anything that wants creativity asks for it explicitly at the
  call site, where a reviewer can see it.
- `max_retries=0` — **turn the framework's retries off.** This is the most important line in the file
  and it is easy to miss. LangChain will happily retry a 429 for you. You already have a 429 strategy:
  Day 6's router, with backoff, jitter and provider fallback, whose behaviour is traced and tested.
  Two retry layers stacked means your budget is silently multiplied and your traces lie about how
  many requests you made. **Pick one layer and disable the other.** Principle 4's spirit — no
  inherited defaults — applied to behaviour rather than versions.
- The `if provider ==` ladder is three branches and it is deliberately not clever. Each provider names
  its key argument differently (`google_api_key`, `groq_api_key`, `api_key`), which is the
  abstraction leaking on its very first contact. **Note that.** It is a real answer to §1's question,
  and pretending it did not happen is how comparison notes become marketing.
- `("openai", JUDGE)` with `base_url` — the OpenAI *adapter* speaking to OpenRouter's OpenAI-
  compatible *endpoint*. Identical to Day 1's `PROVIDERS["openrouter"]`, one abstraction layer up.
  The comment is there because someone will otherwise "fix" this to a nonexistent `openrouter`
  provider string.
- Three named functions instead of `get_model("workhorse")` — so a call site reads `judge()` and a
  grep for `judge(` finds every place an eval judge is constructed. **Names beat strings when you
  will need to audit the call sites**, and Day 72 will need to.

### 4.2 `days/day-36/lab/provider_swap.py`

The LC-02 claim, tested: *same code, two providers, same assertions.*

```python
"""One prompt, three providers, one interface. The vendor-neutrality claim, measured.

Run:
    uv run python days/day-36/lab/provider_swap.py

Budget: 3 requests, one per provider. Not a loop.
"""

import time

from langchain_core.messages import HumanMessage, SystemMessage

from mandala.lc.chat import fast_loop, judge, workhorse

PROMPT = [
    SystemMessage("You classify support tickets. Answer with one word: the severity."),
    HumanMessage("The checkout page returns a 500 for every customer."),
]

for name, factory in [("workhorse", workhorse), ("fast_loop", fast_loop), ("judge", judge)]:
    started = time.monotonic()
    try:
        reply = factory().invoke(PROMPT)
    except Exception as exc:                     # noqa: BLE001 - surveying failure modes
        print(f"{name:<10} FAILED {type(exc).__name__}: {str(exc)[:90]}")
        continue
    elapsed = time.monotonic() - started

    print(f"{name:<10} {elapsed:5.2f}s  type={type(reply).__name__:<10} "
          f"content={str(reply.content)[:40]!r}  meta={sorted(reply.response_metadata)[:4]}")
```

**Line by line:**

- `SystemMessage` / `HumanMessage` from `langchain_core.messages` — the typed message classes. Day 1
  used `{"role": "user", "content": ...}` dicts against the raw client; this is the same thing with a
  type. Tomorrow (LC-03) goes into what is actually inside `content`.
- `factory().invoke(PROMPT)` — **`invoke` is the universal verb.** Models, tools, agents and graphs
  all have it. Learning that one word buys you most of the LangChain surface, and it is the strongest
  ergonomic argument the framework has.
- `time.monotonic()` around each call — **`monotonic`, not `time.time()`**, because it cannot jump
  backwards when the system clock adjusts. For measuring durations it is always the right call, and
  the numbers matter: Groq should be dramatically faster, and "route by shape" in `RATE_BUDGET.md`
  rule 4 is easier to believe once you have watched it.
- `except Exception` with a reasoned `# noqa` — Day 1's `verify_keys.py` convention. You want to see
  all three outcomes, and a `:free` model that 429s (as one did on Day 1) is a result, not a crash.
- `type(reply).__name__` printed — **is it the same class for all three providers?** That is the LC-02
  claim in one column. If any provider returns something different, that is the finding of the day.
- `sorted(reply.response_metadata)[:4]` — the **keys**, not the values. This is where the abstraction
  is most likely to be uneven: token counts, finish reasons, and safety fields are named differently
  by different vendors, and `response_metadata` is the bag they land in. Comparing the key sets across
  three providers is a five-second experiment with a genuinely useful answer.
- Three requests total, stated in the docstring. Same budget discipline as Day 1's `verify_keys.py`,
  and for the same reason.

### 4.3 What to write down

Answer these in your bake-off notes today, from the run and not from memory:

1. Was the reply object the **same class** for all three providers?
2. Did `response_metadata` have the **same keys**? Which provider is the odd one out?
3. How many **provider-specific branches** did `chat.py` need? (Three key-argument names, one
   `base_url`. Is that leakage, or reasonable configuration? Argue both sides in one sentence each.)
4. Compared with `src/mandala/router.py`: what does LangChain give you that your router does not, and
   **what does your router still have to do** that LangChain will not?

Question 4 is the one that matters. The honest answer is that `init_chat_model` abstracts the
*interface* and does nothing about the *budget* — no request accounting, no cross-provider fallback
on a 429, no knowledge that OpenRouter has 50 requests a day. **The abstraction is orthogonal to the
constraint that actually governs this project**, which is why `max_retries=0` is in §4.1 and why Day
6's router does not get deleted today.

---

## §5 The eval that must be able to fail

### `tests/test_lc_chat.py`

```python
"""Policy tests for the model factory. 0 model requests -- nothing here invokes."""

from pathlib import Path

import pytest

from mandala.lc import chat
from mandala.models import FAST_LOOP, JUDGE, WORKHORSE


def test_every_role_maps_to_a_pinned_model():
    ids = {model_id for _, model_id in chat._ROLE_PROVIDER.values()}
    assert ids == {WORKHORSE, FAST_LOOP, JUDGE}


def test_no_model_id_is_written_in_this_file():
    """Day 1's rule, fourth framework. Flip it: paste a model id, watch this go red."""
    source = Path("src/mandala/lc/chat.py").read_text(encoding="utf-8")
    for banned in ("gemini-", "gpt-oss", "nemotron", ":free"):
        assert banned not in source, banned


def test_the_judge_is_not_the_workhorse():
    """Plan §2.1 standing rule 1: judge != judged."""
    assert chat._ROLE_PROVIDER["judge"][0] != chat._ROLE_PROVIDER["workhorse"][0]
    assert chat._ROLE_PROVIDER["judge"][0] != chat._ROLE_PROVIDER["fast_loop"][0]


def test_framework_retries_are_disabled(monkeypatch):
    """THE budget test. Two retry layers = a silently doubled request budget."""
    captured: dict = {}

    def fake_init(model_id, **kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(chat, "init_chat_model", fake_init)
    chat.workhorse()
    assert captured["max_retries"] == 0


def test_temperature_defaults_to_zero(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(chat, "init_chat_model",
                        lambda model_id, **kw: captured.update(kw) or object())
    chat.fast_loop()
    assert captured["temperature"] == 0.0


@pytest.mark.parametrize("role", ["workhorse", "fast_loop", "judge"])
def test_every_role_supplies_a_key(monkeypatch, role):
    captured: dict = {}
    monkeypatch.setattr(chat, "init_chat_model",
                        lambda model_id, **kw: captured.update(kw) or object())
    chat._build(role)
    assert any("key" in k for k in captured), captured


def test_agent_executor_is_not_used_anywhere():
    """LC-01: the deprecated loop stays out of this repo, importable or not."""
    offenders = [
        p.name
        for p in Path("src/mandala").rglob("*.py")
        if "AgentExecutor" in p.read_text(encoding="utf-8")
    ]
    assert offenders == [], offenders
```

**Line by line:**

- Every test **monkeypatches `init_chat_model`** rather than calling it. You are testing *your
  policy*, not LangChain's constructor — the same boundary Day 32 drew about the checkpoint store.
  Zero requests, instant, and it works with no keys in CI (Day 74 will care).
- `test_no_model_id_is_written_in_this_file` greps the source for model-id fragments. Crude, and it
  enforces the single rule that has survived from Day 1 to Day 36 unchanged.
- `test_the_judge_is_not_the_workhorse` encodes a **plan-level standing rule** as a test. Plan §2.1
  rule 1 is a sentence in a document; here it becomes something that fails. That translation — prose
  rule to executable assertion — is worth doing wherever it is cheap.
- `test_framework_retries_are_disabled` is today's flip-it test and the most valuable one on the page.
  Delete `max_retries=0` and a 429 quietly becomes several requests, your ledger under-reports, and
  Day 76's cost analysis is built on sand.
- `lambda model_id, **kw: captured.update(kw) or object()` — `dict.update` returns `None`, so `or
  object()` supplies the return value. A compact idiom; use it knowingly, and if it reads badly to
  you in six months, write the three-line function instead.
- `test_every_role_supplies_a_key` parametrized over roles — catches "added a fourth role, forgot the
  key branch", which is the exact failure the `if` ladder in §4.1 invites.
- `test_agent_executor_is_not_used_anywhere` — fourth day running for the grep-as-a-test pattern. Here
  it guards against the strongest force acting on this repo: **every LangChain example you or an
  assistant will encounter was written pre-1.0.**

---

## §6 Traps

- **Installing before signing the amendment.** §1.1. Principle 14 is the habit; today is when it
  costs you two minutes instead of nothing.
- **Pinning the addendum's 1.3.15 without re-checking.** Day 1 already found 1.3.16. Verify today.
- **Leaving `max_retries` at its default.** Two retry layers, one budget, silently doubled.
- **Writing a model id in `chat.py`.** Five weeks of discipline, one paste.
- **Assuming `langchain-openai` means OpenAI.** It means the OpenAI *wire format*, and it is how you
  reach OpenRouter for free.
- **Installing `langchain-community` "just in case".** Enormous, unnecessary, and a supply-chain
  surface you would then have to review (MCP-15).
- **Reaching for `AgentExecutor` because a search result did.** It is deprecated. So is most of the
  LangChain text on the internet, including whatever your editor autocompletes.
- **Deleting `router.py` because LangChain "does that now".** It does not do the part you need — §4.3
  question 4.
- **Concluding vendor-neutrality is a lie because of three key-argument names.** It is leakage, it is
  small, and the honest write-up says *how* small.

---

## §7 Request budget

**Declared: 3 model requests, one per provider.**

| What | Requests |
|---|---|
| `what_survived.py` | **0** |
| `tests/test_lc_chat.py` | **0** |
| `provider_swap.py` | 3 |

Today is a wiring day, exactly like Day 1 and Day 23 were. **Notice the pattern across the plan:
first days of a framework cost almost nothing, and gate days cost twenty.** That shape is worth
naming in your notes, because it tells you how to schedule a week against a daily quota.

---

## §8 Verify before you code

Written **2026-08-20** against `langchain==1.3.16` / `langchain-core==1.6.0`. This is the package
with an open amendment against it, so read carefully and log everything (Principle 14):

- **The 1.2 → 1.3 release notes.** Day 36 carries an explicit instruction from the addendum to read
  them and log anything surprising. Do it before writing code, not after.
- **Is `init_chat_model` in `langchain.chat_models` in 1.3.16?** It has moved between packages
  historically. If it is elsewhere, fix §4.1 and log the line.
- **The provider strings** — `"google_genai"`, `"groq"`, `"openai"`. Confirm each; a wrong provider
  string fails at construction, which is at least loud.
- **Does `init_chat_model` accept `base_url` for the openai provider**, or does it need
  `ChatOpenAI(...)` directly? The OpenRouter path depends on the answer.
- **Is `max_retries` the right parameter name** on all three adapters, and is it honoured? Check by
  reading, not by hoping — this is the §5 budget test's whole premise.
- **`response_metadata` key names per provider** — you will discover these empirically in §4.2, but
  check whether the docs promise any of them are standard.
- `https://docs.langchain.com/oss/python/langchain/models` — read today, not from memory.

---

## §9 Say it in an interview

> "LangChain 1.x splits into core abstractions, the agent framework, and per-provider adapters, and
> `init_chat_model` means everything above the adapter is provider-agnostic — I ran the same prompt
> across Gemini, Groq and OpenRouter through one interface and got the same message class back. I'd
> already hand-built a provider abstraction earlier in the project, so I could be specific about what
> it added and what it didn't: it abstracts the *interface* and knows nothing about the *budget*.
> There's no cross-provider fallback on a 429 and no request accounting, so my own router stayed, and
> I explicitly set `max_retries=0` on every model — two retry layers would silently multiply my
> request count and make my traces lie. The leakage I found was small and real: each provider names
> its API-key argument differently, so the factory has a three-branch ladder. I'd call that
> configuration rather than a broken abstraction, but I'd rather say the number than the adjective."

---

## §10 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 36
```
