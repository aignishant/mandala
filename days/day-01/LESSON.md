---
day: 1
phase: 0
phase_name: "Foundry"
title: "Foundry I — the repo, the pins, and the three free keys"
ids: []
principles: ["P1 build daily", "P4 pin everything", "P5 zero budget"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 1 — Foundry I: the repo, the pins, and the three free keys

**Phase 0 · Foundry** · Principles served: **4 (pin everything)** and **5 (zero budget)**

> **Yesterday:** nothing — this is the start.
> **Today:** a repo that can hold 90 days of work, exact version pins backed by evidence, and three
> free API keys that actually answer.
> **Tomorrow:** the quality machine around it — CI, lint, tests, and the docs habit.

---

## §1 The story

Imagine you are opening a workshop that you will use every day for three months. Before you build
anything, you do two boring things: you bolt the workbench to the floor, and you label every drawer.

Nobody photographs that day. But every day after it is faster because of it.

That is Day 1. Two boring, load-bearing things:

**First, you bolt down the versions.** Here is the failure this prevents, and it is not
hypothetical — the plan's Principle 4 cites it directly. On a previous project, a framework quietly
changed which model it used by default. No code changed. No release announcement was read. Overnight,
the evaluation scores dropped and a day was lost finding out why. The fix is a rule so simple it
sounds childish: **nothing floats.** Every package gets an exact version. Every agent gets
`model="..."` typed out explicitly. You never accept a default you did not choose, because a default
is a decision somebody else gets to change while you sleep.

**Second, you find out what your budget actually is.** This project has a hard constraint: **$0.**
No card on file, ever (Principle 5). That is not a limitation you work around — it is a design
constraint you build *for*, and it turns out to make you a better engineer. Because on a $0 budget,
the thing you can run out of is not money. It is **requests per minute** and **requests per day**.
And unlike money, you cannot top those up at 11pm when a lab is half-finished. So you learn, from
Day 1, to budget calls the way a good engineer budgets memory: know the number, declare it before you
spend it, and have a fallback when you hit the wall.

That is the whole day. Bolt the bench down. Label the drawers. Find out how big the drawers are.

---

## §2 The repo shape

Everything for 90 days lives in one repository. Not fifteen. One. Here is what you are building
toward — most of these folders will be empty today, and that is fine; you are laying out the
workshop, not filling it.

```
mandala/
├── CLAUDE.md               # already exists — the operating rules
├── Makefile                # `make check` is the one command that must stay green
├── pyproject.toml          # uv-managed, Python 3.12, every dep exact-pinned
├── uv.lock                 # committed. This is what makes a build reproducible.
├── .env.example            # names of the keys, never the values
├── .gitignore              # .env must be in here. Check twice.
├── docs/                   # the plan, the pins, the tracker, the ADRs
├── days/                   # day-01 … day-90 — lessons, checklists, labs
├── src/mandala/            # the capstone. Grows a little every single day.
│   ├── __init__.py
│   ├── config.py           # loads keys, fails loudly if one is missing
│   ├── models.py           # ← the model pins live here as named constants
│   └── router.py           # ← built Day 6. Every model call in the project goes through it.
└── tests/
    ├── fixtures/           # golden tickets, cassettes — all $0 to re-run
    └── test_config.py
```

Two of those deserve a sentence each, because they are the ones people get wrong.

**`src/mandala/models.py`** exists so that when a free model id gets retired (and one will), you fix
it in exactly one place. Do not scatter model strings through 90 days of labs. Give them names:

```python
# src/mandala/models.py  — pinned 2026-08-20, re-checked every Friday by /freshness
WORKHORSE  = "gemini/<the-free-flash-model-id-you-verified-today>"
FAST_LOOP  = "groq/<the-open-model-id-you-verified-today>"
JUDGE      = "openrouter/<a-free-roster-model-you-verified-today>"   # perishable!
OFFLINE    = "ollama/<a-local-model>"                                 # optional
```

Note the angle brackets. **This lesson deliberately does not hardcode model ids**, because free
rosters rotate and a model id written on 2026-08-20 may be gone by the time you read this. You fill
them in today from the live consoles — that is part of the lab.

**`uv.lock` is committed.** `pyproject.toml` says "I want these versions"; `uv.lock` says "and here is
the exact resolved tree, hashes included". Committing the lockfile is what turns "it works on my
machine" into "it works on any machine". It is Principle 4 applied to the whole dependency graph
rather than to the handful of packages you happened to think about.

---

## §3 The pins, and the evidence behind them

`docs/PINS.md` already holds a version table verified against PyPI on **2026-08-20**. Your job today
is not to trust it — it is to **re-verify it and then freeze it**. The plan's own Part 2 says
"re-verify on your Day 1, then pin," and the kickoff checklist repeats it. Do it.

Here is the one-liner that produces the evidence:

```bash
for p in openai-agents openai crewai crewai-tools langchain langchain-core \
         langgraph langsmith litellm mcp a2a-sdk sentence-transformers; do
  curl -s "https://pypi.org/pypi/$p/json" \
    | python -c "import sys,json;d=json.load(sys.stdin);print('$p', d['info']['version'])"
done
```

Then compare against `docs/PINS.md`. Three outcomes, and each has a required response:

| What you see | What you do |
|---|---|
| Same version | Nothing. Pin it. Move on. |
| Newer **patch** (1.15.17 → 1.15.19) | Pin the new patch, one line in `CHANGELOG_PLAN.md`. |
| Newer **minor or major** | **Stop.** Read the release notes. Write an addendum. Then pin. (Principle 14) |

That third row is not bureaucracy. It is the habit the entire plan is trying to install in you. The
reflex "the ecosystem moved → the plan is amended → *then* the code changes" is what separates
someone who can maintain an agent system for a year from someone who can demo one for a week.

> ⚠️ **There is already one open amendment.** The bulk-generation pass on 2026-08-20 found that
> `langchain` had moved **1.2.x → 1.3.15** (and `langchain-core` to 1.6.0) since the plan's baseline.
> That is a minor-version drift, so it needs your sign-off before you pin it. Read
> `docs/03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md` today and tick its boxes. The short version:
> LangChain 1.x promises no breaking changes before 2.0, so nothing in Curriculum D changes meaning —
> only the number you write in `pyproject.toml`.

---

## §4 The three free keys

You need three accounts. All three are free, and none of them asks for a card.

| Provider | Env var | What it's for in this plan | Get it from |
|---|---|---|---|
| **Gemini (AI Studio)** | `GEMINI_API_KEY` | Daily workhorse. Big context, decent reasoning. | aistudio.google.com |
| **Groq** | `GROQ_API_KEY` | The fast loop. Many small calls, very low latency. | console.groq.com |
| **OpenRouter** | `OPENROUTER_API_KEY` | Diversity + eval judges + a reasoning second opinion. | openrouter.ai |
| *(optional)* **Ollama** | *none* | The outage branch. Local, keyless, unlimited, worse. | ollama.com |

**Why three and not one.** It looks like redundancy. It is actually three separate design decisions
that pay off later:

1. **Judge ≠ judged.** From Day 72 onward, when a model grades another model's work, the grader must
   run on a *different provider*. A model marking its own homework is not an evaluation; it is a
   mood. Having a second and third provider is what makes honest evals possible at all.
2. **Rate limits become survivable.** Free tiers guarantee you will hit 429s. With one provider that
   ends your evening. With three and a router, it is a log line.
3. **Vendor-neutrality stops being a slogan.** The plan's whole thesis is about comparing frameworks
   honestly. Running four frameworks across three providers, daily, is the evidence.

**One serious warning, and it applies from today until Day 90.** Free-tier prompts to Gemini may be
used by Google to train models. So: **fixtures only.** Every ticket you ever send this system is
invented. No real customer data, no real names, no real credentials, nothing you would not be
comfortable publishing. This is not paranoia — it is the reason `tests/fixtures/` exists and why
every lab in these 90 days uses made-up tickets.

### Wiring the keys, safely

```python
# src/mandala/config.py
import os
from dataclasses import dataclass

class MissingKey(RuntimeError):
    """Raised at import time, loudly, so you never debug a silent 401 at 11pm."""

def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise MissingKey(
            f"{name} is not set. Copy .env.example to .env and fill it in. "
            f"See docs/RATE_BUDGET.md for where to get the key."
        )
    return value

@dataclass(frozen=True)
class Keys:
    gemini: str
    groq: str
    openrouter: str

def load_keys() -> Keys:
    return Keys(_require("GEMINI_API_KEY"), _require("GROQ_API_KEY"), _require("OPENROUTER_API_KEY"))
```

The point of `_require` is the error message. A missing key otherwise surfaces as an HTTP 401 four
layers deep inside a framework, and you will spend forty minutes on it. Fail early, fail readable.

And in `.gitignore`, before you write a single key:

```gitignore
.env
.venv/
*.sqlite
__pycache__/
```

`.env` first. Commit the `.gitignore` **before** you create the `.env`. That ordering is the whole
trick — it makes it impossible to accidentally stage a key.

---

## §5 Find out how big the drawers are

This is the part people skip, and it is the part that makes the next 89 days predictable.

Go to each provider's console and **write down the actual numbers** into `docs/RATE_BUDGET.md`:
requests per minute, requests per day, tokens per minute, for the exact model id you pinned.

Then verify with **one** request per provider — not a loop, one — and read the response headers.
Most OpenAI-compatible endpoints return `x-ratelimit-remaining-requests` and friends. That single
request tells you three things at once: the key works, the model id is real, and the quota is what
the console claimed.

```python
# a scratch check — one request per provider, then stop
from openai import OpenAI

client = OpenAI(api_key=KEYS.groq, base_url="https://api.groq.com/openai/v1")
resp = client.chat.completions.with_raw_response.create(
    model=FAST_LOOP,
    messages=[{"role": "user", "content": "reply with the single word: ok"}],
    max_tokens=5,
)
print(resp.headers.get("x-ratelimit-remaining-requests"))
print(resp.parse().choices[0].message.content)
```

Notice something already: that is the **plain `openai` client pointed at Groq**. Same library, free
model, no OpenAI key. That trick — the OpenAI-compatible `base_url` swap — is what makes the entire
Phase 1 "naked agent" possible at $0, and you have just proved it works on Day 1.

---

## §6 Build brief

Create these files. Parts marked `TODO(me)` are yours — they are the reps, and doing them is the
learning.

```
pyproject.toml          # Python 3.12, uv, exact pins from your re-verified PINS.md
uv.lock                 # committed
.gitignore              # .env first
.env.example            # key NAMES only, with a comment saying where to get each
Makefile                # `make check` → ruff check && ruff format --check && pytest
src/mandala/__init__.py
src/mandala/config.py   # TODO(me): load_keys() + the loud MissingKey error
src/mandala/models.py   # TODO(me): WORKHORSE / FAST_LOOP / JUDGE / OFFLINE constants,
                        #           filled from the ids you verified in the consoles today
tests/test_config.py    # TODO(me): assert MissingKey is raised when a var is absent
docs/RATE_BUDGET.md     # TODO(me): fill the table with LIVE numbers
docs/PINS.md            # TODO(me): re-verify; update anything that moved
```

**`make check` must be green before you commit.** From today it is the one command that tells you the
repo is healthy, and every later day depends on it staying that way.

---

## §7 The eval that must be able to fail

Even Day 1 gets a test that can go red (Principle 7). Today's is small but real:

```python
# tests/test_config.py
import pytest
from mandala.config import load_keys, MissingKey

def test_missing_key_fails_loudly(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(MissingKey, match="GEMINI_API_KEY"):
        load_keys()

def test_model_pins_are_explicit():
    """No model constant may be empty or a placeholder. Principle 4."""
    from mandala import models
    for name in ("WORKHORSE", "FAST_LOOP", "JUDGE"):
        value = getattr(models, name)
        assert value and "<" not in value, f"{name} is still a placeholder"
```

The second test is the interesting one. It fails right now, on purpose — the `models.py` in this
lesson is full of `<placeholders>`. It goes green only when you have actually gone to the consoles
and written down real model ids. **A test that enforces that you did the boring thing** is a
perfectly good test.

---

## §8 Request budget

**≤ 3 model requests total** — one per provider, to prove the keys work. That's it. Today is a
filesystem day, not a model day.

---

## §9 Traps

- **Creating `.env` before `.gitignore`.** Then staging it by reflex with `git add -A`. Do the
  ignore file first, always.
- **Pinning with `>=` or `^`.** That is not a pin, it is a wish. Exact versions only.
- **Trusting a model id you read somewhere.** Free rosters rotate. The only trustworthy source is
  the provider console, today.
- **Skipping `docs/RATE_BUDGET.md` because "I'll fill it later".** You won't, and on Day 46 you will
  burn a day's Gemini quota on embeddings you did not need to send to an API at all.
- **Installing Python 3.13.** `crewai` currently caps at `<3.14` and everything is happiest on
  **3.12**. Use 3.12. It is the safe intersection across all four frameworks.
- **Committing `uv.lock`? Yes.** People skip this because "it's generated". Generated *and*
  load-bearing.

---

## §10 Verify before you code

This lesson was written **2026-08-20**. Check these before you type:

- `docs/PINS.md` in this repo — then re-run the PyPI loop above and compare.
- `docs/03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md` — **sign it off today**.
- Your three provider consoles — for live model ids and live rate limits. Nothing else is authoritative.
- `https://docs.astral.sh/uv/` — for the current `uv` workspace/lockfile commands.

---

## §11 Say it in an interview

> "Every model call in that system names its model explicitly, and every package is exact-pinned with
> a committed lockfile. I got burned once by a framework silently changing its default model — evals
> dropped overnight and nothing in my diff explained it. So now defaults are something I choose, not
> something I inherit."

---

## §12 Done when

See `CHECKLIST.md`. Short version: `make check` is green, three keys answer, `RATE_BUDGET.md` has
real numbers in it, and there is a commit.
