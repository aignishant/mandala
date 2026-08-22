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
status: in-progress
lab_scaffolded: false
commit: ""
---

# Day 1 — Foundry I: the repo, the pins, and the three free keys

**Phase 0 · Foundry** · Principles served: **4 (pin everything)** and **5 (zero budget)**

> **Before you start:** [`day-00-setup`](../day-00-setup/LESSON.md) must be done — toolchain
> installed, skeleton created, `./m status` working.
> **Yesterday:** nothing. This is the first of the 90.
> **Today:** exact version pins backed by evidence, three free API keys that actually answer, and
> the real rate limits written down.
> **Tomorrow:** the quality machine — CI, an offline test strategy, and the golden ticket set.

```bash
./m start 1
```

---

## §1 The story

Imagine you are opening a workshop you will use every day for three months. Before you build
anything, you do two boring things: you bolt the workbench to the floor, and you label every drawer.

Nobody photographs that day. But every day after it is faster because of it.

That is Day 1. Two boring, load-bearing things.

**First, you bolt down the versions.** Here is the failure this prevents, and it is not
hypothetical — the plan's Principle 4 cites it directly. On a previous project, a framework quietly
changed which model it used by default. No code changed. No release announcement was read. Overnight,
the evaluation scores dropped and a day was lost finding out why. The fix is a rule so simple it
sounds childish: **nothing floats.** Every package gets an exact version. Every agent gets
`model="..."` typed out explicitly. You never accept a default you did not choose, because a default
is a decision somebody else gets to change while you sleep.

**Second, you find out what your budget actually is.** This project has a hard constraint: **$0.**
No card on file, ever (Principle 5). That is not a limitation you work around — it is a design
constraint you build *for*, and it makes you a better engineer. Because on a $0 budget, the thing
you run out of is not money. It is **requests per minute** and **requests per day**. And unlike
money, you cannot top those up at 11pm when a lab is half-finished. So you learn, from Day 1, to
budget calls the way a good engineer budgets memory: know the number, declare it before you spend
it, and have a fallback for when you hit the wall.

Bolt the bench down. Label the drawers. Find out how big the drawers are.

---

## §2 Setup — run this

Everything today needs, in order. Copy each block into Git Bash.

### 2.1 Install today's two packages

```bash
uv add "openai==3.3.1" "python-dotenv==1.2.3"
```

**Line by line:**

- `uv add` — install a package **and** record it in `pyproject.toml` under `dependencies`, **and**
  update `uv.lock`. That three-in-one is why you use `uv add` rather than `uv pip install`: the
  dependency is written down, not just present on your machine.
- `"openai==3.3.1"` — the official OpenAI Python client. You are not using OpenAI's models; you are
  using this library as a **generic client for any OpenAI-compatible endpoint**, which Groq, Gemini
  and OpenRouter all provide. One library, three free providers, zero spend.
- `==3.3.1` — a hard pin. Not `>=3.3.1`, not `~=3.3`. Principle 4. The quotes around the whole
  argument stop the shell from trying to interpret `==` or any special characters.
- `"python-dotenv==1.2.3"` — reads a `.env` file into environment variables so your keys live in a
  file that git ignores rather than being typed into your shell every session.

Confirm it landed in the project file, not just in the environment:

```bash
grep -A5 '^dependencies' pyproject.toml
```

- `grep -A5 'pattern' file` — print matching lines plus the **A**fter 5 lines of context.
- You should now see `dependencies = ["openai==3.3.1", "python-dotenv==1.2.3"]`.

### 2.2 Create today's files

```bash
touch src/mandala/config.py
touch src/mandala/models.py
touch tests/test_config.py
touch .env.example
mkdir -p days/day-01/lab
touch days/day-01/lab/verify_keys.py
```

- `touch <file>` — creates an empty file, or leaves an existing one alone. Safe to re-run.
- `mkdir -p days/day-01/lab` — the day's scratch space. (`./m scaffold 1` does exactly this.)
- **Note there is no `touch .env` here.** That comes in §5, *after* you have confirmed `.gitignore`
  already ignores it. Order matters.

### 2.3 Confirm `.env` is already ignored

Before a key ever exists on disk:

```bash
grep -n '^\.env$' .gitignore && echo "SAFE" || echo "STOP — add .env to .gitignore first"
```

- `grep -n '^\.env$' .gitignore` — search for a line that is *exactly* `.env`. `^` anchors the start,
  `$` anchors the end, `\.` is a literal dot (an unescaped `.` in a regex means "any character").
  `-n` prints the line number.
- `&& echo "SAFE"` — run only if grep found it (exit code 0).
- `|| echo "STOP — ..."` — run only if grep failed.

If it says STOP, fix `.gitignore` before going further. A key in git history outlives the commit
that deleted it.

---

## §3 The pins, and the evidence behind them

`docs/PINS.md` holds a version table verified against PyPI on **2026-08-20**. Your job today is not
to trust it — it is to **re-verify it and then freeze it**. The plan's Part 2 says "re-verify on your
Day 1, then pin," and the kickoff checklist repeats it.

Here is the command that produces the evidence:

```bash
for p in openai-agents openai crewai crewai-tools langchain langchain-core \
         langgraph langsmith litellm mcp a2a-sdk sentence-transformers; do
  printf "%-26s " "$p"
  curl -s "https://pypi.org/pypi/$p/json" \
    | python -c "import sys,json;print(json.load(sys.stdin)['info']['version'])"
done
```

**Line by line:**

- `for p in openai-agents openai ... ; do` — loop over the twelve core packages. `p` holds one name
  per iteration.
- `\` at the end of a line — a line continuation. The shell treats the next line as part of the same
  command. There must be **nothing after the backslash**, not even a space.
- `printf "%-26s " "$p"` — print the package name left-aligned (`-`) in a 26-character field, then a
  space, with no newline. This makes the versions line up in a readable column.
- `curl -s "https://pypi.org/pypi/$p/json"` — PyPI publishes a JSON document for every package.
  `-s` is "silent": suppress the progress meter, which would otherwise corrupt the output.
- `|` — pipe: send `curl`'s output as `python`'s input.
- `python -c "..."` — run the given source directly.
- `json.load(sys.stdin)` — parse the JSON arriving on standard input.
- `['info']['version']` — dig into the document: the `info` object holds the metadata, and `version`
  is the current release. This is the authoritative number — not a blog post, not memory.

Compare the output against `docs/PINS.md`. Three outcomes, each with a required response:

| What you see | What you do |
|---|---|
| Same version | Nothing. Pin it. Move on. |
| Newer **patch** (1.15.17 → 1.15.19) | Pin the new patch; one line in `docs/CHANGELOG_PLAN.md`. |
| Newer **minor or major** | **Stop.** Read the release notes. Write an addendum. *Then* pin. (Principle 14) |

That third row is not bureaucracy. It is the habit the entire plan exists to install. The reflex
"*the ecosystem moved → the plan is amended → then the code changes*" is what separates someone who
can maintain an agent system for a year from someone who can demo one for a week.

> ⚠️ **There is already one open amendment.** The generation pass on 2026-08-20 found that
> `langchain` had moved **1.2.x → 1.3.15** (and `langchain-core` to 1.6.0) since the plan's baseline.
> Minor-version drift needs your sign-off before you pin it. Read
> `docs/03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md` today and tick its boxes. Short version:
> LangChain 1.x promises no breaking changes before 2.0, so nothing in Curriculum D changes meaning —
> only the number you write down.

---

## §4 The three free keys

Three accounts. All free. None asks for a card.

| Provider | Env var | Role in this plan | Sign up at |
|---|---|---|---|
| **Gemini (AI Studio)** | `GEMINI_API_KEY` | Daily workhorse. Big context, good reasoning. | aistudio.google.com |
| **Groq** | `GROQ_API_KEY` | The fast loop. Many small calls, very low latency. | console.groq.com |
| **OpenRouter** | `OPENROUTER_API_KEY` | Diversity, eval judges, reasoning second opinion. | openrouter.ai |
| *(optional)* **Ollama** | *none* | The outage branch. Local, keyless, unlimited, worse. | ollama.com |

**Why three and not one.** It looks like redundancy. It is three separate design decisions that each
pay off later:

1. **Judge ≠ judged.** From Day 72, when a model grades another model's work, the grader must run on
   a *different provider*. A model marking its own homework is not an evaluation; it is a mood.
   Having a second and third provider is what makes honest evals possible at all.
2. **Rate limits become survivable.** Free tiers guarantee 429s. With one provider that ends your
   evening. With three and a router (Day 6), it is a log line.
3. **Vendor-neutrality stops being a slogan.** The plan's thesis is about comparing frameworks
   honestly. Running four frameworks across three providers, daily, is the evidence.

**One warning that applies from today until Day 90.** Free-tier prompts to Gemini may be used by
Google to train models. So: **fixtures only.** Every ticket you ever send this system is invented.
No real customer data, no real names, no real credentials, nothing you would not publish. This is
why `tests/fixtures/` exists and why every lab in these 90 days uses made-up tickets.

---

## §5 Wire the keys, safely

### 5.1 The example file (committed) and the real file (never committed)

```bash
cat > .env.example <<'EOF'
# Copy this file to .env and fill in real values.
# .env is git-ignored. This file is committed, and must never contain a real key.

# https://aistudio.google.com  — daily workhorse
GEMINI_API_KEY=

# https://console.groq.com     — fast loop, tool-calling drills
GROQ_API_KEY=

# https://openrouter.ai        — diversity, eval judges
OPENROUTER_API_KEY=
EOF

cp .env.example .env
```

- `cat > .env.example <<'EOF' ... EOF` — the heredoc from Day 0 §4: write everything up to the line
  `EOF` into the file. The quotes around `EOF` stop the shell interpreting `$` or backslashes.
- `cp .env.example .env` — copy it to the real file. Now open `.env` in an editor and paste your
  three keys after the `=` signs. **No quotes, no spaces around the `=`.**

Prove git is not watching the real one:

```bash
git status --porcelain | grep -c '\.env$'
```

- `git status --porcelain` — a compact, script-friendly status listing.
- `grep -c '\.env$'` — count lines ending in `.env`.
- **The answer must be `0`.** If it is 1, stop and fix `.gitignore`.

### 5.2 `src/mandala/config.py`

```python
"""Loads the three free-tier API keys, and fails loudly when one is missing.

Why this file exists
--------------------
A missing key otherwise surfaces as an HTTP 401 four layers deep inside a
framework, at 11pm, and costs you forty minutes. Failing early with a message
that says exactly what to do costs you four seconds.

Usage
-----
    >>> from mandala.config import load_keys
    >>> keys = load_keys()
    >>> keys.groq[:6]
    'gsk_ab'

    >>> import os; os.environ.pop("GROQ_API_KEY", None)
    >>> load_keys()
    Traceback (most recent call last):
    mandala.config.MissingKey: GROQ_API_KEY is not set. ...
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


class MissingKey(RuntimeError):
    """Raised when a required provider key is absent from the environment."""


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
    """The three free-tier keys. Frozen so nothing can reassign one mid-run."""

    gemini: str
    groq: str
    openrouter: str


def load_keys() -> Keys:
    """Read all three keys from the environment. Raises MissingKey on the first absent one."""
    return Keys(
        gemini=_require("GEMINI_API_KEY"),
        groq=_require("GROQ_API_KEY"),
        openrouter=_require("OPENROUTER_API_KEY"),
    )
```

**Line by line:**

- The module docstring — includes a **Usage** section with doctest-style examples. Every file you
  write in these 90 days gets one. Six months from now the example is what you will actually read.
- `from __future__ import annotations` — type hints become strings rather than being evaluated at
  import. Lets you write modern hint syntax freely, and speeds up import.
- `import os` — access to environment variables via `os.environ`.
- `from dataclasses import dataclass` — the decorator that generates `__init__`, `__repr__` and
  `__eq__` for a simple data-holding class, so you do not write them by hand.
- `from dotenv import load_dotenv` — the function that reads `.env`.
- `load_dotenv()` at module level — runs **once, when the module is first imported**. It looks for a
  `.env` file in the current directory and its parents, and copies each `KEY=value` into
  `os.environ`. It does **not** overwrite a variable that is already set, which is exactly right:
  a real environment variable (in CI, say) beats the local file.
- `class MissingKey(RuntimeError)` — a custom exception type. Subclassing `RuntimeError` rather than
  `Exception` means `except RuntimeError` still catches it, while a specific `except MissingKey`
  can single it out. Defining your own type lets tests assert on *this* failure rather than any
  failure.
- `def _require(name: str) -> str:` — the leading underscore marks it private by convention:
  "internal to this module, do not import elsewhere."
- `os.environ.get(name, "")` — read the variable, returning `""` if absent. Using `.get` rather than
  `os.environ[name]` means you control the error instead of getting a bare `KeyError`.
- `.strip()` — remove surrounding whitespace. This catches the very common paste error of a trailing
  space or newline on a copied key, which otherwise produces a baffling 401.
- `if not value:` — in Python an empty string is falsy, so this catches both "missing" and "present
  but blank". A blank `GROQ_API_KEY=` in `.env` is a real thing that happens.
- The error message — names the variable, names the fix, names the doc. An error message that does
  not say what to do next is only half an error message.
- `@dataclass(frozen=True)` — `frozen=True` makes instances immutable: `keys.groq = "x"` raises
  instead of silently succeeding. Credentials should not be reassignable halfway through a run.
- `gemini: str` etc. — the dataclass fields. The type annotations are what the decorator reads to
  generate the constructor.
- `load_keys()` — one function that gathers all three. Called at the top of every script from now
  on, so a missing key fails on line 3 rather than on line 300.

### 5.3 `src/mandala/models.py`

```python
"""The model pins. One place, so a rotated free model is a one-line fix.

Free-tier rosters rotate WITHOUT NOTICE — especially OpenRouter's `:free` list.
Never write a model id anywhere else in this project. Import from here.

Re-checked every Friday by the freshness routine (Principle 13).

Usage
-----
    >>> from mandala.models import FAST_LOOP, PROVIDERS
    >>> PROVIDERS["groq"].base_url
    'https://api.groq.com/openai/v1'
"""

from __future__ import annotations

from dataclasses import dataclass

# --------------------------------------------------------------------------
# Model pins — FILL THESE IN from the live provider consoles on Day 1.
# The test `test_model_pins_are_explicit` fails while a placeholder remains.
# --------------------------------------------------------------------------
WORKHORSE = "<gemini-free-flash-model-id>"    # Gemini: labs, capstone, long context
FAST_LOOP = "<groq-open-model-id>"            # Groq:   dev loop, tool-calling drills
JUDGE = "<openrouter-free-model-id>"          # OpenRouter: evals. MUST differ from the judged.
OFFLINE = "<ollama-local-model>"              # Ollama: optional outage branch


@dataclass(frozen=True)
class Provider:
    """One OpenAI-compatible endpoint: which key it uses and where it lives."""

    key_attr: str        # the attribute name on mandala.config.Keys
    base_url: str        # the OpenAI-compatible endpoint
    default_model: str   # the pinned model for this provider


PROVIDERS: dict[str, Provider] = {
    "gemini": Provider(
        key_attr="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        default_model=WORKHORSE,
    ),
    "groq": Provider(
        key_attr="groq",
        base_url="https://api.groq.com/openai/v1",
        default_model=FAST_LOOP,
    ),
    "openrouter": Provider(
        key_attr="openrouter",
        base_url="https://openrouter.ai/api/v1",
        default_model=JUDGE,
    ),
}
```

**Line by line:**

- `WORKHORSE = "<gemini-free-flash-model-id>"` — **a deliberate placeholder.** This lesson does not
  hardcode a model id, because free rosters rotate and an id written on 2026-08-20 may be dead by
  the time you read this. You fill it in from the console today, and a test (§7) fails until you do.
- The four constants have *role* names, not *provider* names — `WORKHORSE`, not `GEMINI_FLASH`. So
  when Gemini retires a model, or you decide Groq should be the workhorse, you change one line and
  every lab follows. Naming by role rather than by vendor is the whole reason this file exists.
- `JUDGE` with its comment — encodes the standing rule from plan §2.1: the eval judge must run on a
  different provider than the agent under test. Writing the rule next to the constant means you
  cannot forget it while choosing a model.
- `@dataclass(frozen=True) class Provider` — bundles the three facts you need to build a client:
  which key, which URL, which model.
- `key_attr: str` — stores the *name* of the attribute on `Keys` (`"groq"`), not the key itself.
  This keeps secrets out of this module entirely, so `models.py` is safe to print, log, or paste
  into a bug report.
- `base_url` for Gemini ends in `/v1beta/openai/` — that is Google's **OpenAI-compatibility**
  endpoint, which is what lets the `openai` library talk to Gemini. The trailing slash matters; the
  library joins paths onto it.
- `PROVIDERS: dict[str, Provider]` — a lookup table. From Day 6 the router will iterate this dict
  in order to implement the fallback chain, so having it as data (rather than three `if` branches)
  is what makes the router ten lines instead of forty.

---

## §6 Find out how big the drawers are

This is the part people skip, and it is what makes the next 89 days predictable.

Go to each provider console and **write the real numbers** into `docs/RATE_BUDGET.md`: requests per
minute, requests per day, tokens per minute, for the exact model id you pinned.

Then verify with **one** request per provider — not a loop, one — and read the response headers.

### `days/day-01/lab/verify_keys.py`

```python
"""One request per provider. Confirms the key works, the model id is real,
and shows the live rate-limit headers.

Run:
    uv run python days/day-01/lab/verify_keys.py

Budget: exactly 3 requests. Do not put this in a loop.
"""

from openai import OpenAI

from mandala.config import load_keys
from mandala.models import PROVIDERS

KEYS = load_keys()

for name, provider in PROVIDERS.items():
    api_key = getattr(KEYS, provider.key_attr)
    client = OpenAI(api_key=api_key, base_url=provider.base_url)

    try:
        raw = client.chat.completions.with_raw_response.create(
            model=provider.default_model,
            messages=[{"role": "user", "content": "reply with the single word: ok"}],
            max_tokens=5,
        )
    except Exception as exc:                      # noqa: BLE001 - we want every failure shown
        print(f"{name:<12} FAILED  {type(exc).__name__}: {exc}")
        continue

    reply = raw.parse().choices[0].message.content
    remaining = raw.headers.get("x-ratelimit-remaining-requests", "(not reported)")
    reset = raw.headers.get("x-ratelimit-reset-requests", "(not reported)")
    print(f"{name:<12} ok  reply={reply!r}  requests_left={remaining}  resets_in={reset}")
```

**Line by line:**

- `from openai import OpenAI` — the client class. One class, three providers.
- `KEYS = load_keys()` — at the top, so a missing key stops the script immediately.
- `for name, provider in PROVIDERS.items():` — `.items()` yields `(key, value)` pairs from a dict,
  so you get both the provider's name and its `Provider` record.
- `getattr(KEYS, provider.key_attr)` — fetch an attribute **by name at runtime**. `provider.key_attr`
  is the string `"groq"`, so this is equivalent to `KEYS.groq`. This is what lets one loop body
  handle all three providers.
- `OpenAI(api_key=..., base_url=...)` — **the whole $0 trick, in one line.** The library does not
  care whose server is at `base_url`; it speaks the OpenAI wire format, and all three providers
  answer it. Same library, free models, no OpenAI key.
- `client.chat.completions.with_raw_response.create(...)` — `with_raw_response` returns the HTTP
  response object rather than the parsed result, so you can read the headers. Without it you get the
  answer but not the rate-limit information, which is the whole point today.
- `messages=[{"role": "user", "content": "..."}]` — the conversation. A list of dicts, each with a
  role and content. This is the shape you will see for the next 90 days.
- `max_tokens=5` — cap the reply. This is a connectivity check, not a conversation; do not spend
  tokens per minute you will want later.
- `except Exception as exc:` — catch everything, because today you want to *see* every failure mode
  (bad key, dead model id, wrong URL), not stop at the first.
- `# noqa: BLE001` — a comment telling ruff to allow this blind `except`. Suppressing a lint warning
  is fine **when you say why**; a bare `# noqa` with no code and no reason is not.
- `type(exc).__name__` — the exception class name, e.g. `AuthenticationError` or `NotFoundError`.
  The class name usually tells you more than the message does.
- `continue` — move to the next provider rather than aborting.
- `raw.parse()` — turn the raw HTTP response into the normal typed object.
- `.choices[0].message.content` — the model's reply. `choices` is a list because the API can return
  several candidates; you asked for one, so index 0.
- `raw.headers.get("x-ratelimit-remaining-requests", "(not reported)")` — read the header if the
  provider sends it. Not all do, hence the default; `.get` never raises.
- `{name:<12}` — left-align in a 12-character column.
- `{reply!r}` — print the `repr()`, i.e. with quotes, so a reply of `" ok\n"` is visibly different
  from `"ok"`.

Run it:

```bash
uv run python days/day-01/lab/verify_keys.py
```

Expected — three lines, all starting `ok`. If one says `FAILED`, the exception name tells you which
of the three things is wrong: the key, the model id, or the URL.

---

## §7 The eval that must be able to fail

Even Day 1 gets a test that can go red (Principle 7).

### `tests/test_config.py`

```python
"""Day-1 guardrails: keys fail loudly, and model pins are real."""

import pytest

from mandala import models
from mandala.config import MissingKey, load_keys


def test_missing_key_fails_loudly(monkeypatch):
    """A missing key must raise MissingKey naming the variable, not a bare KeyError."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(MissingKey, match="GEMINI_API_KEY"):
        load_keys()


def test_blank_key_is_treated_as_missing(monkeypatch):
    """A key line left empty in .env is the same failure as no line at all."""
    monkeypatch.setenv("GROQ_API_KEY", "   ")
    with pytest.raises(MissingKey, match="GROQ_API_KEY"):
        load_keys()


@pytest.mark.parametrize("name", ["WORKHORSE", "FAST_LOOP", "JUDGE"])
def test_model_pins_are_explicit(name):
    """Principle 4: no placeholders. Red until you visit the consoles and fill them in."""
    value = getattr(models, name)
    assert value, f"{name} is empty"
    assert "<" not in value, f"{name} is still the placeholder {value!r}"
```

**Line by line:**

- `import pytest` — needed for `pytest.raises`, `pytest.mark`, and fixtures.
- `def test_missing_key_fails_loudly(monkeypatch):` — `monkeypatch` is a **built-in pytest fixture**.
  You get it by naming it as a parameter; pytest supplies it. It makes temporary changes to the
  environment and **undoes them automatically** when the test ends, so tests cannot leak state into
  each other.
- `monkeypatch.delenv("GEMINI_API_KEY", raising=False)` — remove the variable for the duration of
  this test. `raising=False` means "do not error if it was not set to begin with", which keeps the
  test passing on a machine where the key is absent anyway.
- `with pytest.raises(MissingKey, match="GEMINI_API_KEY"):` — assert that the block raises that
  exact exception type **and** that its message matches the pattern. The `match` half is what makes
  this a real test: without it, any `MissingKey` would pass, including one naming the wrong variable.
- `monkeypatch.setenv("GROQ_API_KEY", "   ")` — set it to whitespace. This is the test for the
  `.strip()` in `_require`; delete that `.strip()` and this test goes red.
- `@pytest.mark.parametrize("name", ["WORKHORSE", "FAST_LOOP", "JUDGE"])` — run the same test body
  three times, once per value. You get **three separate test results**, so a failure report names
  exactly which constant is unfilled rather than just "something is wrong".
- `getattr(models, name)` — fetch the module attribute by name, same technique as in `verify_keys.py`.
- `assert value, f"{name} is empty"` — the second argument to `assert` is the message shown on
  failure. Always give one; `assert x` alone tells you nothing useful when it fails.
- `assert "<" not in value` — the placeholder check. **This test is red right now**, on purpose, and
  goes green only once you have actually visited the consoles and written down real model ids. A
  test that enforces you did the boring thing is a perfectly good test.

Run them:

```bash
uv run pytest tests/test_config.py -v
```

- `-v` — verbose: print one line per test with its name and result, instead of a row of dots.

---

## §8 Request budget

**≤ 3 model requests total** — one per provider, from `verify_keys.py`. Today is a filesystem day,
not a model day.

Record the actual number in the ledger table at the bottom of `docs/RATE_BUDGET.md`.

---

## §9 Traps

- **Creating `.env` before `.gitignore` ignores it**, then staging it by reflex with `git add -A`.
  §2.3 exists to prevent exactly this.
- **Pinning with `>=` or `~=`.** That is not a pin, it is a wish. Exact versions only.
- **Trusting a model id you read somewhere** — including in this file. Free rosters rotate. The only
  trustworthy source is the provider console, today.
- **A trailing newline on a pasted key.** `.strip()` in `_require` handles it; without that you get
  a 401 that looks like a wrong key.
- **Skipping `docs/RATE_BUDGET.md` because "I'll fill it later".** You will not, and on Day 46 you
  will burn a day's Gemini quota on embeddings that never needed an API at all.
- **Putting `verify_keys.py` in a loop** "to be sure". Three requests. That is the whole budget.
- **Writing a model id in a lab file** instead of importing from `mandala.models`. One rotation and
  you are grepping ninety folders.

---

## §10 Verify before you code

This lesson was written **2026-08-20**. Check these first:

- `docs/PINS.md` — then re-run the §3 loop and compare.
- `docs/03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md` — **sign it off today.**
- Your three provider consoles — live model ids and live rate limits. Nothing else is authoritative.
- `https://ai.google.dev/gemini-api/docs/openai` — confirm Gemini's OpenAI-compatibility `base_url`
  is still `.../v1beta/openai/`. This path has changed before.
- `https://console.groq.com/docs/openai` — Groq's compatibility notes, including which parameters it
  silently ignores.

---

## §11 Say it in an interview

> "Every model call in that system names its model explicitly, and every package is exact-pinned with
> a committed lockfile. I got burned once by a framework silently changing its default model — evals
> dropped overnight and nothing in my diff explained it. So now defaults are something I choose, not
> something I inherit. And the model ids live behind role names like `WORKHORSE` and `JUDGE`, because
> on free tiers the roster rotates and I wanted a rotation to be a one-line change."

---

## §12 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 1
```

`./m check` runs Ruff's lint and format checks, then the offline pytest suite. On Windows systems
where Application Control blocks the `pytest.exe` launcher, run tests directly with
`uv run python -m pytest -q`; `./m check` already uses this project-local Python module invocation.
It does not change or use another project's environment. `./m done` refuses to commit while a box
is unticked or the checks are red. That is the point.
