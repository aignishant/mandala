---
day: 56
phase: 8
phase_name: "MCP (2026-07-28 spec)"
title: "Auth in 2026, and Elicitation"
ids: ["MCP-06", "MCP-07"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 56 — Auth in 2026, and Elicitation

**Phase 8 · MCP 2026-07-28** · IDs: **MCP-06 🛠️**, **MCP-07 🛠️**

> **Yesterday:** one server, four clients, three deleted declarations — and an honest note that the
> mount gives you tool *selection*, not *enforcement*.
> **Today:** closes that gap. OAuth2 with **RFC 9207 issuer validation**, and **client metadata
> documents** replacing dynamic client registration. Then **Elicitation** — the server asking the
> *user* a typed question mid-tool-call, which is the fifth and strangest human-in-the-loop
> mechanism in this plan.
> **Tomorrow:** Tasks, Apps, and the extensions framework.

```bash
./m start 56
./m scaffold 56
```

---

## §1 The story

Day 54 §4 said it plainly: moving the tool out of your process cost you `permissions.py`, and the
server answers anyone who reaches it. Yesterday you bound it to localhost and called that a
temporary answer. **Today is the day the temporary answer expires.**

Two IDs, and they are more related than they look.

**MCP-06 is about *who is calling*.** OAuth2 is not new; what the 2026-07-28 revision cares about is
two specific things that fix real, recent failures:

- **RFC 9207 issuer validation** — the token response must say *which* authorisation server issued
  it, and the client must check. This exists because mix-up attacks are real: a client talking to
  several authorisation servers can be tricked into sending a token to the wrong one.
- **Client metadata documents (CIMD) replacing Dynamic Client Registration.** DCR meant every client
  registered itself with every server at runtime, and every server accumulated a registration
  database. CIMD means a client **publishes a document describing itself** and servers read it. **The
  state moved out of the server** — which should sound familiar, because it is exactly the same move
  as the stateless core (MCP-02).

**MCP-07 is about *who is answering*.** Elicitation lets a server pause a tool call to ask the user a
typed question: accept, decline, or cancel. It is the fifth HITL mechanism you have met, and it is the
only one where **the request comes from the other side of the boundary.** That inversion is what makes
it interesting and what makes it a security question.

**Zero-budget note:** neither ID needs a model. Today is protocol work again — free, and testable
without a provider.

---

## §2 Setup — run this

### 2.1 What you need

```bash
grep -n 'mcp\|httpx' pyproject.toml
```

- Nothing new should be required. **If a full OAuth flow tempts you toward an identity-provider
  package, stop**: this is a $0 project and you are learning the *shape*, not running Okta. §3.4
  explains what to build instead and why it is enough.

### 2.2 Create today's files

```bash
touch src/mandala_mcp/auth.py
touch src/mandala_mcp/elicit.py
touch tests/test_mcp_auth.py
touch tests/test_elicitation.py
mkdir -p days/day-56/lab
touch days/day-56/lab/token_checks.py
touch days/day-56/lab/elicit_demo.py
touch days/day-56/lab/auth_notes.md
```

---

## §3 MCP-06 — auth, and what the client must check

### 3.1 The flow, and the two places it goes wrong

The shape is ordinary OAuth2: the client gets a token from an authorisation server and presents it to
the resource server (your MCP server). **The two failure modes worth building for:**

1. **A token from the wrong issuer.** The client asked authorisation server A; the token came back
   claiming to be from B. Without checking, the client forwards it and A's token ends up somewhere it
   should not. **RFC 9207 makes the issuer explicit in the response so the client can compare.**
2. **A token for the wrong audience.** A valid token, issued by the right server, but minted for a
   *different* resource. The server must check that it is the intended audience.

**Both are checks, both are three lines, and both are routinely skipped.** They are the whole of
practical MCP auth for someone who is not writing an identity provider.

### 3.2 `src/mandala_mcp/auth.py`

```python
"""Token validation for ticket-db. Small, explicit, and about CHECKS not crypto.

We are not building an authorisation server. We are building the four checks a
resource server must perform, because those are the ones that get skipped:

  1. ISSUER   -- RFC 9207: does the token come from the AS we actually asked?
  2. AUDIENCE -- is this token minted for US, or for some other resource?
  3. EXPIRY   -- is it still valid?
  4. SCOPE    -- does it permit the tool being called?

Check 4 is where Day 54 §4's lost permissions.py comes back: per-caller tool
permissions live in the token's scopes, enforced by the server, rather than in a
client-side allowlist that only constrains well-behaved callers.

Usage
-----
    >>> claims = {"iss": EXPECTED_ISSUER, "aud": AUDIENCE, "exp": 9e9, "scope": "tickets:read"}
    >>> validate(claims, tool="get_ticket")
    True
"""

from __future__ import annotations

import os
import time
from typing import Final

EXPECTED_ISSUER: Final = os.environ.get("MANDALA_MCP_ISSUER", "https://auth.local/mandala")
AUDIENCE: Final = "ticket-db"
LEEWAY_S: Final = 30

#: Which scope each tool requires. THIS is per-caller permission, server-side.
TOOL_SCOPES: Final[dict[str, str]] = {
    "get_ticket": "tickets:read",
    "search_tickets": "tickets:read",
    "search_handbook": "handbook:read",
}


class AuthError(Exception):
    """Refused. The message is for a log, never for the caller."""


def validate(claims: dict, *, tool: str, now: float | None = None) -> bool:
    """Run all four checks. Raises AuthError on the first failure."""
    now = time.time() if now is None else now

    if claims.get("iss") != EXPECTED_ISSUER:
        raise AuthError(f"issuer mismatch: {claims.get('iss')!r}")

    audiences = claims.get("aud")
    audiences = [audiences] if isinstance(audiences, str) else (audiences or [])
    if AUDIENCE not in audiences:
        raise AuthError(f"audience mismatch: {audiences!r}")

    exp = claims.get("exp")
    if exp is None or float(exp) + LEEWAY_S < now:
        raise AuthError("token expired")

    required = TOOL_SCOPES.get(tool)
    if required is None:
        raise AuthError(f"unknown tool {tool!r}")
    if required not in str(claims.get("scope", "")).split():
        raise AuthError(f"missing scope {required!r} for {tool!r}")

    return True
```

**Line by line:**

- `EXPECTED_ISSUER` from the environment — **the client and the server must agree on this string, and
  RFC 9207 exists so it can be compared rather than assumed.** Hard-coding it would be worse in
  production and is fine here only because it is configurable.
- `AUDIENCE = "ticket-db"` — the same name as the server (Day 54). **One identity, used for routing,
  tracing and now authorisation.** Consistency here is cheap and it pays off in logs.
- **`TOOL_SCOPES` is the important structure**, and it is Day 12's `permissions.py` reincarnated on the
  correct side of the boundary. Yesterday's `ALLOWED_TOOLS` was client-side: it constrained *your*
  agent and nothing else. **A scope check constrains every caller, including one you did not write.**
  Say that difference out loud; it is the whole of today's first half.
- Four checks, **each raising with a specific message.** Ordering is deliberate: issuer first (cheapest
  and most fundamental), scope last (needs the tool name).
- `audiences = [audiences] if isinstance(audiences, str) else ...` — **`aud` may be a string or a
  list.** That is in the spec and it is exactly the sort of detail that produces a working
  implementation for a year and then fails against one identity provider.
- `LEEWAY_S = 30` — clock skew is real between two machines. **Leeway on expiry is correct; leeway on
  issuer or audience is not**, and the asymmetry is worth noticing: time is approximate, identity is
  not.
- `raise AuthError(...)` with a message **for a log, not for the caller.** The docstring says so
  explicitly. Telling an unauthenticated caller *why* they failed is free reconnaissance — "audience
  mismatch" tells them the token type was right. **The handler returns a generic refusal; the log
  gets the detail.**
- `now: float | None = None` — injectable time, so §5 can test expiry without sleeping. **Any function
  that reads the clock should let a test set it.**

### 3.3 CIMD, and why it is the same idea as MCP-02

**Dynamic Client Registration:** every client POSTs its details to every server at runtime; each
server keeps a registration record. **N clients × M servers registrations, all stateful.**

**Client metadata documents:** the client publishes one document at a URL describing itself — name,
redirect URIs, public keys. Servers fetch it, verify it, and keep nothing.

| | DCR | CIMD |
|---|---|---|
| Where the client's identity lives | in every server's database | **at one URL the client owns** |
| Server-side state | a registration table | **none** |
| Rotating a key | re-register everywhere | **update one document** |
| Shape | N×M records | **N documents** |

**Read that last row against Day 53's N×M argument.** MCP-01 said: one boundary turns 4×K
integrations into 4+K. CIMD says: one document turns N×M registrations into N documents. **It is the
same move applied to identity, and the stateless core (MCP-02) is the same move applied to
connections.** Three instances of one idea in one spec revision is not a coincidence — **the 2026-07-28
revision has a thesis, and the thesis is "push state out of the server".** Being able to say that
sentence is the point of today's reading.

### 3.4 `days/day-56/lab/token_checks.py` — 0 model requests

Build the checks, not the identity provider.

```python
"""Every way a token can be wrong, and whether we catch it. No IdP, no network.

Run:
    uv run python days/day-56/lab/token_checks.py

Budget: 0 requests. This is a validation lab.
"""

import time

from mandala_mcp.auth import AUDIENCE, EXPECTED_ISSUER, AuthError, validate

NOW = 1_800_000_000.0


def token(**over) -> dict:
    base = {
        "iss": EXPECTED_ISSUER,
        "aud": AUDIENCE,
        "exp": NOW + 300,
        "scope": "tickets:read handbook:read",
        "sub": "agent-triage",
    }
    return {**base, **over}


CASES = [
    ("valid", token(), "get_ticket"),
    ("wrong issuer", token(iss="https://evil.example/as"), "get_ticket"),
    ("no issuer at all", token(iss=None), "get_ticket"),
    ("wrong audience", token(aud="some-other-server"), "get_ticket"),
    ("audience as a list", token(aud=[AUDIENCE, "other"]), "get_ticket"),
    ("expired", token(exp=NOW - 3600), "get_ticket"),
    ("expired within leeway", token(exp=NOW - 10), "get_ticket"),
    ("missing scope", token(scope="tickets:read"), "search_handbook"),
    ("unknown tool", token(), "delete_everything"),
    ("scope substring trap", token(scope="tickets:readonly"), "get_ticket"),
]

for label, claims, tool in CASES:
    try:
        validate(claims, tool=tool, now=NOW)
        print(f"  ACCEPTED  {label:<24} tool={tool}")
    except AuthError as exc:
        print(f"  refused   {label:<24} {exc}")
```

**Line by line:**

- `NOW` as a **fixed timestamp**, so the output is identical every run. A validation lab whose results
  change with the wall clock is a lab you cannot diff.
- `token(**over)` — the factory pattern from Day 31 and Day 47. One base, one override per case.
- **`"audience as a list"` must be ACCEPTED**, and it is in the list because that is the branch in
  §3.2 that exists for a spec detail. A test suite that only uses string audiences never exercises it.
- **`"expired within leeway"` must be ACCEPTED.** Ten seconds past expiry with 30 seconds of leeway is
  clock skew, not an attack.
- **`"scope substring trap"` is the one to stare at.** `"tickets:readonly"` *contains*
  `"tickets:read"` as a substring. If §3.2 had written `required in claims["scope"]` instead of
  splitting on whitespace, this would be **accepted** — a scope-escalation bug from one missing
  `.split()`. **Run this case, and if it is accepted, you have found a real vulnerability in your own
  code in five minutes.** That is the argument for building the checks rather than reading about them.
- `"unknown tool"` — a tool with no scope entry is refused, not defaulted. **Fail closed**, same rule
  as Day 47's Store allowlist and Day 49's retry policy.

---

## §4 MCP-07 — Elicitation

### 4.1 The fifth HITL mechanism, and the odd one out

| Mechanism | Who asks | Who answers | Day |
|---|---|---|---|
| SDK tool approvals | the agent framework | a human | 21 |
| CrewAI pause | your flow | a human | 33 |
| LangChain HITL middleware | the framework | a human | 39 |
| LangGraph `interrupt()` | your node | a human | 50 |
| **MCP Elicitation** | **the server** | **a human, via the client** | **today** |

**Four of these are initiated by code you wrote. The fifth is initiated by code you did not.**

The plan's MCP-07 example is a good one: `close_ticket` finds three duplicates and asks *"Close all
4?"* — a question only the server knows to ask, because only the server can see the duplicates.

**Three outcomes: accept, decline, cancel.** Note that is three, matching Day 33's approve/reject/edit
in count but not in meaning: *decline* is "no, continue without it" and *cancel* is "stop the whole
operation". **A binary answer cannot express that difference**, and the same argument that made Day 33
use three outcomes applies here.

### 4.2 The security question you must answer today

**A server can make your client display arbitrary text to a user.**

Think about what that means with a third-party server from the registry (Day 53's MCP-12):

- The elicitation prompt is **written by the server**, rendered by **your client**, and read by **your
  user**, who reasonably assumes your application is asking.
- A malicious server could elicit *"Enter your API key to continue"*, and it would look exactly like a
  legitimate request.
- Even without malice, a compromised or careless server can put unescaped content on your screen.

**So elicitation is a phishing surface with a protocol specification.** The defences are the ordinary
ones and they must be decided before you enable it:

1. **Attribute the question.** The UI must say *which server* is asking. Never render a server's text
   as if it came from your application.
2. **Escape it.** It is untrusted text, exactly like a ticket body (Day 65).
3. **Never elicit secrets.** Your client should refuse to render a prompt asking for credentials, and
   the URL-mode flow exists precisely so credential entry happens at the identity provider, not in a
   chat box.
4. **Allowlist which servers may elicit at all.** For `ticket-db`, which you wrote, yes. For a
   registry server, start at no.

**Write these four into `auth_notes.md` today.** Day 66's third-party review will use them as its
checklist, and finding them yourself — by asking "what can the other side do to me?" — is the habit
that day is really teaching.

### 4.3 `src/mandala_mcp/elicit.py`

```python
"""One elicitation, done carefully. The server asks; the human answers; nothing is assumed.

Mandala is READ-ONLY until Day 82, so there is no close_ticket to confirm. Instead
we elicit the one genuinely ambiguous read: a search that matched several tickets
and needs the user to pick.

Design rules, decided here because §4.2 says elicitation is a phishing surface:
  - the prompt says WHO is asking ("ticket-db asks:")
  - the schema is CLOSED -- an enum of ids we found, never free text
  - no secret is ever requested, and the schema makes that structurally true
  - decline and cancel are handled DIFFERENTLY

Usage
-----
    >>> disambiguation_schema(["T-1004", "T-1009"])["properties"]["ticket_id"]["enum"]
    ['T-1004', 'T-1009']
"""

from __future__ import annotations

MAX_CHOICES = 5


def disambiguation_schema(ticket_ids: list[str]) -> dict:
    """A CLOSED schema: the user picks from what we found, and cannot type anything."""
    choices = ticket_ids[:MAX_CHOICES]
    return {
        "type": "object",
        "properties": {
            "ticket_id": {
                "type": "string",
                "enum": choices,
                "description": "Which ticket did you mean?",
            }
        },
        "required": ["ticket_id"],
        "additionalProperties": False,
    }


def prompt_for(query: str, ticket_ids: list[str]) -> str:
    """Attributed, bounded, and it never asks for anything secret."""
    listed = ", ".join(ticket_ids[:MAX_CHOICES])
    return f"ticket-db asks: {len(ticket_ids)} tickets match {query[:60]!r}. Which one? ({listed})"
```

**Line by line:**

- `enum: choices` — **a closed schema is the structural defence.** A free-text elicitation can ask for
  anything, including a password. An enum of ticket ids the server just found **cannot** ask for a
  secret, no matter what the prompt text says. **Constrain the answer shape and the question's danger
  drops with it** — this is the same instinct as Day 37's `pattern` and Day 47's allowlist.
- `additionalProperties: False` — the client should reject anything not in the schema. Without it, a
  server could smuggle an extra field into the form.
- `"ticket-db asks:"` prefixed to the prompt — **attribution in the text itself**, as a belt to the UI's
  braces. If the client renders the string plainly, the user still knows who is asking.
- `query[:60]!r` — the user's own query, **bounded and repr'd.** Even echoing the user's input back
  deserves a bound; a 10,000-character query would otherwise become a 10,000-character dialog.
- `MAX_CHOICES = 5` — an elicitation with fifty options is not a question, it is a paste.
- **What is deliberately absent:** any free-text field, any field named like a credential, any
  server-supplied HTML. The schema is the security control and it is eleven lines.

### 4.4 Handling the three outcomes

```python
    if result.action == "accept":
        return get_ticket(result.content["ticket_id"])
    if result.action == "decline":
        return "No ticket selected. Narrow the search and try again."
    return "Cancelled."     # action == "cancel"
```

- **`decline` and `cancel` must not be collapsed.** Decline is "I will not answer this question" —
  the operation continues, degraded. Cancel is "stop everything". Treating them the same is how a
  user's "no" becomes an abort, or worse, how an abort becomes a "continue anyway".
- Every branch **returns text a model can act on**, per Day 54's rule about model-facing errors being
  instructions.
- **No branch raises.** A user declining is not an error.

---

## §5 The eval that must be able to fail

### `tests/test_mcp_auth.py`

```python
"""Four checks. Each one is skipped in the wild. 0 model requests."""

import pytest

from mandala_mcp.auth import (
    AUDIENCE,
    EXPECTED_ISSUER,
    LEEWAY_S,
    TOOL_SCOPES,
    AuthError,
    validate,
)

NOW = 1_800_000_000.0


def token(**over) -> dict:
    base = {"iss": EXPECTED_ISSUER, "aud": AUDIENCE, "exp": NOW + 300,
            "scope": "tickets:read handbook:read", "sub": "agent-triage"}
    return {**base, **over}


def test_a_valid_token_passes():
    assert validate(token(), tool="get_ticket", now=NOW) is True


def test_a_wrong_issuer_is_refused():
    """RFC 9207. Flip it: delete the issuer check and this goes red."""
    with pytest.raises(AuthError, match="issuer"):
        validate(token(iss="https://evil.example/as"), tool="get_ticket", now=NOW)


def test_a_missing_issuer_is_refused():
    with pytest.raises(AuthError, match="issuer"):
        validate(token(iss=None), tool="get_ticket", now=NOW)


def test_a_wrong_audience_is_refused():
    with pytest.raises(AuthError, match="audience"):
        validate(token(aud="some-other-server"), tool="get_ticket", now=NOW)


def test_a_list_audience_containing_us_passes():
    """`aud` may be a string or a list. A suite that only tests strings misses a branch."""
    assert validate(token(aud=[AUDIENCE, "other"]), tool="get_ticket", now=NOW)


def test_an_expired_token_is_refused():
    with pytest.raises(AuthError, match="expired"):
        validate(token(exp=NOW - 3600), tool="get_ticket", now=NOW)


def test_clock_skew_within_leeway_is_tolerated():
    assert validate(token(exp=NOW - (LEEWAY_S // 2)), tool="get_ticket", now=NOW)


def test_leeway_applies_to_expiry_only():
    """Time is approximate; identity is not. There is no leeway on issuer or audience."""
    with pytest.raises(AuthError):
        validate(token(iss=EXPECTED_ISSUER + "/"), tool="get_ticket", now=NOW)


def test_a_missing_scope_is_refused():
    with pytest.raises(AuthError, match="scope"):
        validate(token(scope="tickets:read"), tool="search_handbook", now=NOW)


def test_a_scope_substring_does_not_grant_access():
    """THE bug. Flip it: use `required in scope` instead of splitting, and this goes red."""
    with pytest.raises(AuthError, match="scope"):
        validate(token(scope="tickets:readonly"), tool="get_ticket", now=NOW)


def test_an_unknown_tool_is_refused():
    """Fail closed. A tool with no scope entry gets no access, not a default."""
    with pytest.raises(AuthError, match="unknown tool"):
        validate(token(), tool="delete_everything", now=NOW)


def test_every_server_tool_has_a_scope():
    """A tool the server offers with no scope entry is unreachable -- or unprotected."""
    from mandala_mcp import server as srv

    offered = {n for n in dir(srv) if hasattr(getattr(srv, n), "fn")}
    assert offered <= set(TOOL_SCOPES), offered - set(TOOL_SCOPES)


def test_refusal_messages_are_not_returned_to_callers():
    """Grep-as-a-test: AuthError text goes to logs, never into a tool response."""
    from pathlib import Path

    source = Path("src/mandala_mcp/server.py").read_text(encoding="utf-8")
    assert "AuthError" not in source or "str(exc)" not in source
```

### `tests/test_elicitation.py`

```python
"""Elicitation is a phishing surface with a spec. Constrain the answer shape."""

import pytest

from mandala_mcp.elicit import MAX_CHOICES, disambiguation_schema, prompt_for


def test_the_schema_is_closed():
    """THE defence. Flip it: allow free text and a server can ask for a password."""
    schema = disambiguation_schema(["T-1004", "T-1009"])
    assert schema["properties"]["ticket_id"]["enum"] == ["T-1004", "T-1009"]
    assert schema["additionalProperties"] is False


def test_no_free_text_field_exists():
    schema = disambiguation_schema(["T-1004"])
    for prop in schema["properties"].values():
        assert "enum" in prop, prop


def test_choices_are_bounded():
    schema = disambiguation_schema([f"T-{i:04d}" for i in range(50)])
    assert len(schema["properties"]["ticket_id"]["enum"]) == MAX_CHOICES


def test_the_prompt_says_who_is_asking():
    """Attribution in the text, as a belt to the UI's braces."""
    assert prompt_for("refund", ["T-1004"]).startswith("ticket-db asks:")


def test_the_prompt_bounds_the_echoed_query():
    out = prompt_for("x" * 5000, ["T-1004"])
    assert len(out) < 300


@pytest.mark.parametrize("secret_word", ["password", "api key", "token", "secret"])
def test_the_prompt_never_asks_for_a_secret(secret_word):
    assert secret_word not in prompt_for("refund", ["T-1004"]).lower()


def test_decline_and_cancel_are_handled_differently():
    """Flip it: collapse them into one branch and this goes red."""
    from pathlib import Path

    source = Path("src/mandala_mcp/elicit.py").read_text(encoding="utf-8")
    assert "decline" in source and "cancel" in source
```

**Line by line on the ones that matter:**

- `test_a_scope_substring_does_not_grant_access` is the day's headline test, and the bug it catches is
  a genuine scope escalation from one missing `.split()`. **If your implementation fails this, you
  wrote the bug and the test caught it — which is the best possible outcome for a lesson.**
- `test_leeway_applies_to_expiry_only` uses a **trailing-slash issuer**, which is how issuer mismatches
  actually happen in practice. It pins the asymmetry: approximate time, exact identity.
- `test_every_server_tool_has_a_scope` is a **cross-file invariant** between `server.py` and `auth.py`.
  Add a tool to the server and it is either scoped or the test tells you.
- `test_the_schema_is_closed` and `test_no_free_text_field_exists` are the elicitation defence, and the
  flip-it note names the actual threat. **A test whose docstring names an attack is a test nobody
  deletes.**
- `test_the_prompt_never_asks_for_a_secret` is parametrized over four words. Crude — it cannot stop a
  cleverly-worded prompt — and **worth having anyway** as a tripwire against the obvious case. Say the
  limitation rather than implying coverage.

---

## §6 `days/day-56/lab/auth_notes.md`

```markdown
# MCP auth and elicitation — Mandala, 2026-08-__

## The four checks, and which I had skipped before today
| Check | Why it exists | Did I have it on Day 55? |
|---|---|---|
| issuer (RFC 9207) | mix-up attacks | |
| audience | a valid token for someone else | |
| expiry (+leeway) | | |
| scope | **per-caller permissions, server-side** | no — Day 55 only had a client allowlist |

## DCR vs. CIMD, and the pattern
<N x M registrations -> N documents. Where else does this revision push state out of
 the server? Name all three instances.>

## Elicitation: the four defences
1. attribute the question
2. escape it
3. never elicit secrets — and make it structurally true with a closed schema
4. allowlist which servers may elicit at all

## What changes when the server is third-party (Day 66)
<the prompt is written by someone else and rendered by my client to my user>

## What I can now delete
<Day 55 shipped test_the_endpoint_is_localhost_by_default as a temporary guarantee.
 Can it go? Only if auth is actually enforced on every tool call -- check, then decide.>
```

**The last section is the honest one.** Yesterday's localhost binding was a placeholder for auth. **It
can only be removed if the checks are wired into the request path**, not merely written in a module.
Validating tokens in a file nothing calls is the most common way security work becomes decorative.
**Check that `validate()` is actually invoked per tool call before you widen the bind address.**

---

## §7 Traps

- **Writing `validate()` and never calling it.** Decorative security. Check the request path.
- **Widening the bind address before auth is enforced.** Day 55's test exists to stop exactly this.
- **`required in scope` instead of splitting.** A scope-escalation bug in one operator.
- **Leeway on issuer or audience.** Time is approximate; identity is not.
- **Assuming `aud` is a string.** It may be a list.
- **Returning the refusal reason to the caller.** Free reconnaissance.
- **Defaulting an unknown tool to allowed.** Fail closed.
- **A free-text elicitation schema.** A server can then ask your user for anything.
- **Rendering a server's prompt as your application's own voice.** That is the phishing surface.
- **Collapsing decline and cancel.** A user's "no" becomes an abort, or an abort becomes a "continue".
- **Reaching for an identity-provider package.** You are building four checks, not an IdP.

---

## §8 Request budget

**Declared: 0 model requests.**

| What | Requests |
|---|---|
| Everything today | **0** |

**Fourth free day in eleven, and all four have been protocol or decision days.** Notice the pattern
and use it deliberately: **on a $0 budget, front-load the days that cost nothing** when your quota is
tight, and save the expensive framework days for when it is fresh. That is a scheduling insight the
ledger gave you, and it is worth a line in `RATE_BUDGET.md` §2.

---

## §9 Verify before you code

Written **2026-08-20** against spec revision **2026-07-28** and `mcp==2.0.0`:

- **Does the SDK provide token validation**, or is it your job? If it provides it, use it and keep
  §3.2 as the explanation of what it does.
- **How does a tool handler get the token/claims?** §3.2 assumes something passes them in. Find the
  actual mechanism — this is the same question as Day 54 §8's "can a handler read request metadata".
- **RFC 9207 in the spec** — is issuer validation required of clients, recommended, or assumed?
- **CIMD specifics** — where is the document published, what must it contain, how is it verified, and
  is DCR removed or merely deprecated?
- **Elicitation's exact result shape** — `action` values (`accept`/`decline`/`cancel`?), and where the
  answer lives (`.content`?).
- **Does the spec constrain elicitation schemas?** If it forbids or discourages free-text or
  credential-shaped fields, quote it in `auth_notes.md` — that turns your house rule into a citation.
- **URL mode** for OAuth/card entry — how does it work, and does it solve the "never elicit secrets"
  problem structurally?
- **Which of the four clients (Day 55) actually support elicitation?** A client that ignores it means
  a server's question silently never reaches a human, which is its own failure mode.
- The specification's authorization and elicitation pages — **read today.**

---

## §10 Say it in an interview

> "Moving tools behind MCP cost me per-agent permissions — the server answers anyone who reaches it —
> and the client-side allowlist I'd added only constrains well-behaved callers. Scopes are what put
> that back on the right side of the boundary. I implemented the four checks a resource server owes:
> issuer, which is RFC 9207 and exists because mix-up attacks are real; audience, because a valid
> token minted for someone else is still valid; expiry with leeway, because clock skew is real and
> identity mismatches aren't — so there's leeway on time and none on issuer; and scope, per tool. The
> bug I'd point at is one my own test caught: checking `required in scope` instead of splitting on
> whitespace means the scope `tickets:readonly` grants `tickets:read`, which is a privilege escalation
> from one missing operator. On the other half, elicitation lets a server ask my user a typed question
> mid-tool-call — the only human-in-the-loop mechanism in the system that's initiated by code I didn't
> write, which makes it a phishing surface with a specification. My defence is structural rather than
> textual: the answer schema is a closed enum of ids the server just found, with additionalProperties
> false, so it *cannot* ask for a credential regardless of what the prompt says. And the pattern I'd
> point out across the whole revision is that stateless connections, client metadata documents instead
> of dynamic registration, and cacheable listings are all the same move — push state out of the server."

---

## §11 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 56
```
