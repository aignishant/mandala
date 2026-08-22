---
day: 87
phase: 13
phase_name: "Deployment & interop"
title: "A2A v1.0 — signed cards, peer tasks, the agent economy"
ids: ["INT-01", "INT-02", "INT-03", "AG-30"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-21"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 87 — A2A v1.0: signed cards, peer tasks, the agent economy

**Phase 13 · Deployment & interop** · IDs: **INT-01 🛠️**, **INT-02 🛠️**, **INT-03 🅿️**, **AG-30 🅿️**

> **Yesterday:** stateless API, checkpointer-backed workers, no node executing twice.
> **Today:** Mandala talks to an agent it did not build. That is a different trust problem from
> everything in the last 86 days — **the peer is not your code, and its Agent Card is a claim, not a
> fact.** You verify a signature before you believe a word of it.
> **Tomorrow:** mandates, micropayments, and the Phase-13 gate.

```bash
./m start 87
./m scaffold 87
```

---

## §1 The story

Every integration so far has been *inward*: you called a model, a tool, an MCP server you wrote. A2A
is the first *outward* one — a peer agent, run by someone else, with its own goals.

The plan's INT-03 asks for one paragraph you can say aloud, and it is the frame for the whole day:

> **MCP is agent-as-tool. A2A is agent-as-peer.** When Mandala mounts `ticket-db` over MCP, it is
> holding a tool: Mandala decides what to call, when, and what the result means; the server does what
> it is told and returns data. When Mandala calls a partner over A2A, it is delegating a *task* to
> something that has its own loop, its own tools, and its own judgement. The tool returns a value;
> the peer returns a **claim**. That is why MCP's security story is mostly about tool descriptions
> and permissions, and A2A's is mostly about **identity, signatures, and treating the response as
> untrusted input.**

Which gives today's three walls, and you have built all three before in other forms:

1. **Verify before you trust (INT-01).** An Agent Card declares skills and endpoints and carries a
   cryptographic signature from the publishing domain. **Unverified card → no call.** This is
   Day 66's third-party MCP review (MCP-15) with real crypto instead of a hash.
2. **The peer's output is `Untrusted` (INT-02).** Day 78's type, third source. A partner agent's
   response is text a stranger's model produced; it goes through the same fence as a ticket body and
   a search snippet.
3. **The peer gets a task, not a capability.** You do not hand a peer your tools. You hand it a
   bounded question and a deadline, and you keep the write.

AG-30 is 🅿️ literacy: know the identity/trust/payments map — A2A cards, AP2 mandates, x402/TAP —
**and build only A2A**. Tomorrow covers the payment half; today is identity.

---

## §2 Setup — run this

```bash
uv add "a2a-sdk==1.1.2"
```

Verify it is live first; it is the Day-87 row of the `PINS.md` ledger.

```bash
mkdir -p src/mandala/interop
touch src/mandala/interop/__init__.py
touch src/mandala/interop/cards.py
touch src/mandala/interop/peer.py
mkdir -p days/day-87/lab/partner
touch days/day-87/lab/partner/agent_card.json
touch days/day-87/lab/partner/serve_partner.py
touch days/day-87/lab/partner_sim.py
touch days/day-87/lab/mcp_vs_a2a.md
touch tests/test_a2a_cards.py
```

**The partner is a simulator you write and run on localhost.** Same discipline as Day 68's dummy
site: you build the counterparty so you can also build a *hostile* counterparty. Nothing today points
at a stranger's real endpoint.

---

## §3 INT-01 — the card, and refusing to trust it

```python
# src/mandala/interop/cards.py
"""An Agent Card is a CLAIM by a domain about an agent. Verify, then read.

Order matters and it is the whole ID: signature first, then skills, then endpoint.
Reading skills off an unverified card and 'checking the signature later' is how
supply-chain compromises work.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import urlparse


class CardRejected(RuntimeError):
    """The card is not trustworthy. No call is made. Never caught and retried."""


TRUSTED_DOMAINS: frozenset[str] = frozenset({"partner.localtest"})


@dataclass(frozen=True)
class Card:
    name: str
    domain: str
    url: str
    skills: tuple[str, ...]
    raw: dict


def verify(raw: dict, *, now: str) -> Card:
    domain = raw.get("provider", {}).get("organization", "")
    if domain not in TRUSTED_DOMAINS:
        raise CardRejected(f"domain {domain!r} not on the allowlist")

    if not _signature_valid(raw):                       # TODO(me): the SDK's verifier
        raise CardRejected(f"signature invalid for {domain!r}")

    url = raw.get("url", "")
    host = urlparse(url).hostname or ""
    if not (host == domain or host.endswith(f".{domain}") or host in {"127.0.0.1", "localhost"}):
        raise CardRejected(f"endpoint {host!r} does not belong to signing domain {domain!r}")

    if raw.get("expires_at", "9999") < now:
        raise CardRejected("card expired")

    skills = tuple(s["id"] for s in raw.get("skills", []))
    return Card(name=raw.get("name", ""), domain=domain, url=url, skills=skills, raw=raw)
```

**Line by line:**

- **`TRUSTED_DOMAINS` first, before any crypto.** A valid signature from a domain you have never
  agreed to work with is a valid signature from a stranger. Signature verification answers *"is this
  really from X?"* — it never answers *"should I trust X?"* Conflating those is the single most
  common misunderstanding about signed anything.
- **The endpoint-vs-signer check is the one people omit**, and it is the attack that matters: a
  legitimately signed card from `partner.localtest` whose `url` points at `evil.test`. The signature
  is valid, the domain is trusted, and you have just been redirected. Four lines, and it closes the
  whole class. **If you implement one thing from this file, implement this.**
- The localhost exemption is explicit and ugly on purpose. It is there so the simulator works, and
  its ugliness reminds you it must not survive contact with a real deployment. Put a `# DEV ONLY`
  comment on it and add it to Day 90's ledger of things to remove.
- `expires_at` — cards expire. Same instinct as Day 84's `review_by` on autonomy grants: a trust
  decision with no expiry is a permanent decision made with temporary evidence.
- `skills` are read **only after** every check passes, and `verify` returns a `Card` — so there is no
  way to hold skill data that did not come out of a successful verification. **Make the unsafe state
  unrepresentable** rather than remembering not to enter it.
- `CardRejected` is never caught and retried. A rejected card is a decision, not a transient failure.

---

## §4 INT-02 — tasks with a peer

```python
# src/mandala/interop/peer.py
"""Delegate a bounded task to a peer. Its answer is untrusted, always."""

from __future__ import annotations

from dataclasses import dataclass

from mandala.interop.cards import Card, CardRejected
from mandala.intake.types import Untrusted
from mandala.obs.tracing import span
from mandala.router.budget import RunBudget

PEER_TIMEOUT_S = 30
PEER_SHARE = 4


@dataclass(frozen=True)
class PeerAnswer:
    peer: str
    skill: str
    task_id: str
    state: str                      # "completed" | "failed" | "timeout" | "rejected"
    content: Untrusted | None


def ask_peer(card: Card, skill: str, question: str, *, budget: RunBudget, run_id: str) -> PeerAnswer:
    if skill not in card.skills:
        raise CardRejected(f"{card.name} does not declare skill {skill!r}")

    with span("mandala.interop.peer_task", run_id=run_id, peer=card.domain, skill=skill) as s:
        budget.charge("peer", 1)
        result = _send_task(card.url, skill, question, timeout=PEER_TIMEOUT_S)   # TODO(me): a2a-sdk
        s.set_attribute("peer.state", result.state)
        s.set_attribute("peer.task_id", result.task_id)

    if result.state != "completed":
        return PeerAnswer(card.domain, skill, result.task_id, result.state, None)

    return PeerAnswer(
        peer=card.domain,
        skill=skill,
        task_id=result.task_id,
        state="completed",
        content=Untrusted(result.text, source=f"a2a:{card.domain}/{skill}"),
    )
```

**Line by line:**

- **`skill not in card.skills` → reject.** You may only ask for what the *verified* card declared.
  This is Day 8's permission check pointed outward, and it means a peer cannot expand its own surface
  by advertising new skills at call time.
- `Untrusted(..., source=f"a2a:{domain}/{skill}")` — **third untrusted source in the system**, and the
  provenance chain now covers it. When Day 88's partner-sim returns a hostile answer, the trace shows
  exactly which peer and skill it came from.
- Four states, not two. `timeout` and `rejected` are different from `failed`, and Day 83's report
  needs to count them separately — a peer that times out is an availability problem, one that rejects
  is a contract problem.
- `budget.charge("peer", 1)` **before** the call, and the peer gets a slice (`PEER_SHARE`) like Day
  80's research organ. A peer that is slow or chatty must not consume the approval step's budget.
- `PEER_TIMEOUT_S = 30`, explicit. **A peer has its own loop and may think for a long time**; without
  a timeout, your worker's lease (Day 86) expires while it waits and another worker picks up the
  thread. That interaction is subtle and worth writing in the notes.
- Note what is absent: **no tools are passed to the peer, no credentials, no ticket id scheme, no raw
  ticket body.** The `question` should be a distilled, minimal ask. Write down what you send and
  confirm it contains nothing internal — this is the same discipline as Day 82's approval payload.

### 4.1 The hostile partner

Build two partner cards in `days/day-87/lab/partner/`: an honest one and a hostile one. The hostile
one should attempt, at minimum:

| Attack | What it tests |
|---|---|
| unsigned card | signature verification exists at all |
| valid signature, untrusted domain | allowlist precedes crypto |
| valid signature, endpoint at another host | the check most people omit |
| card declaring a skill it does not implement | your handling of a `failed` task |
| answer containing "IGNORE PREVIOUS INSTRUCTIONS…" | the `Untrusted` fence, third source |
| answer containing a canary-shaped exfil URL | Day 69's tripwire, now on a peer path |
| expired card | expiry checking |

**Add these to the Day-69 red-team corpus as RT-13…RT-19.** They are attacks on your system, they
have machine-checkable win conditions, and Day 74's CI already runs that file. Phase 10's work
absorbing a new integration is exactly what it was built for — and it costs you twenty minutes.

---

## §5 INT-03 and AG-30 — the map, in your words

Write `days/day-87/lab/mcp_vs_a2a.md`. Two short sections, both from the docs you read today, and
**both in your own words** — the plan asks for a paragraph you can say aloud without notes.

**Section 1 — MCP vs A2A.** Start from §1's framing, then add the operational differences you
actually hit today: who owns the loop, what the response means, what "the other side changed" looks
like (MCP: a tool description mutates — Day 66's rug pull; A2A: a card is re-signed with a new
endpoint), and what your defence is in each case.

**Section 2 — the economy map (AG-30).** Three rows, one honest sentence each:

| Layer | What it answers | Status |
|---|---|---|
| **A2A v1.0** | who is this agent, and can I delegate a task to it? | built today |
| **AP2** | what is this agent *authorised to spend*, and by whom? | Day 88, concept |
| **x402 / TAP** | how does a machine pay, and prove who it is, per request? | awareness only |

Then the sentence the plan actually wants: **what you would need before letting an agent transact on
your behalf.** You already have most of the answer — Day 84's autonomy ladder is the same shape as an
AP2 mandate: a scoped, capped, expiring, revocable grant with evidence behind it. **Notice that
out loud.** It is the strongest connection in the last three weeks and it is tomorrow's opening.

---

## §6 The eval that must be able to fail

```python
# tests/test_a2a_cards.py
import pytest

from mandala.interop.cards import CardRejected, TRUSTED_DOMAINS, verify

pytestmark = pytest.mark.eval_unit
NOW = "2026-08-21"


def _card(**kw) -> dict:
    base = {"name": "Partner", "provider": {"organization": "partner.localtest"},
            "url": "https://partner.localtest/a2a", "skills": [{"id": "lookup_model"}],
            "expires_at": "2027-01-01", "signature": "VALID"}
    return {**base, **kw}


def test_an_unsigned_card_is_rejected():
    with pytest.raises(CardRejected, match="signature"):
        verify(_card(signature=None), now=NOW)


def test_a_valid_signature_from_an_untrusted_domain_is_rejected():
    """Flip it: check crypto first and 'genuinely signed by a stranger' becomes 'trusted'."""
    with pytest.raises(CardRejected, match="allowlist"):
        verify(_card(provider={"organization": "unknown.test"}), now=NOW)


def test_an_endpoint_outside_the_signing_domain_is_rejected():
    """THE attack: legitimately signed card pointing somewhere else."""
    with pytest.raises(CardRejected, match="does not belong"):
        verify(_card(url="https://evil.test/a2a"), now=NOW)


def test_a_subdomain_endpoint_is_accepted():
    assert verify(_card(url="https://eu.partner.localtest/a2a"), now=NOW).domain == "partner.localtest"


def test_an_expired_card_is_rejected():
    with pytest.raises(CardRejected, match="expired"):
        verify(_card(expires_at="2020-01-01"), now=NOW)


def test_skills_are_only_readable_from_a_verified_card():
    """Make the unsafe state unrepresentable: there is no path to skills without verify()."""
    import inspect

    from mandala.interop import cards

    src = inspect.getsource(cards)
    assert src.count("skills") <= 3 and "def skills_of(" not in src


def test_an_undeclared_skill_cannot_be_requested():
    from mandala.interop.peer import ask_peer
    from mandala.router.budget import RunBudget

    card = verify(_card(), now=NOW)
    with pytest.raises(CardRejected, match="does not declare"):
        ask_peer(card, "transfer_funds", "hi", budget=RunBudget(limit=10), run_id="T-1-a")


def test_a_peer_answer_is_untrusted():
    from mandala.intake.types import Untrusted
    from mandala.interop.peer import PeerAnswer

    a = PeerAnswer("partner.localtest", "lookup_model", "t1", "completed",
                   Untrusted("hello", source="a2a:partner.localtest/lookup_model"))
    with pytest.raises(TypeError):
        f"peer said: {a.content}"


def test_the_peer_gets_no_credentials_or_tools():
    import inspect

    from mandala.interop import peer

    src = inspect.getsource(peer.ask_peer)
    for forbidden in ("API_KEY", "tools=", "credential", "os.environ"):
        assert forbidden not in src


def test_card_rejection_is_never_retried():
    import pathlib

    src = pathlib.Path("src/mandala/interop").rglob("*.py")
    assert not any("except CardRejected" in p.read_text(encoding="utf-8") for p in src)


def test_the_localhost_exemption_is_marked_dev_only():
    import inspect

    from mandala.interop import cards

    assert "DEV ONLY" in inspect.getsource(cards)
```

**Line by line:**

- `test_a_valid_signature_from_an_untrusted_domain_is_rejected` and
  `test_an_endpoint_outside_the_signing_domain_is_rejected` are the two that matter. The first
  encodes *ordering* (allowlist before crypto), the second closes the redirect attack. Both are four
  lines.
- `test_a_subdomain_endpoint_is_accepted` exists so you do not "fix" the endpoint check into
  something that breaks legitimate multi-region partners. Encode the boundary in both directions.
- `test_the_peer_gets_no_credentials_or_tools` greps for four things you must never pass outward.
  Crude, and it is the check that would catch a well-meaning "let me give the partner our search
  tool so it can help better".
- `test_the_localhost_exemption_is_marked_dev_only` makes a temporary hack visible to Day 90's
  removal ledger instead of letting it quietly become permanent.

---

## §7 Traps

- **Crypto before allowlist.** A stranger's genuine signature is still a stranger's.
- **Skipping the endpoint-vs-signer check.** The redirect attack, wide open.
- **Reading skills off an unverified card** "to see what it offers".
- **Calling a skill the card did not declare.**
- **Treating a peer's answer as data you produced.** It is a third untrusted source.
- **Passing tools, keys, or the raw ticket body to a peer.**
- **No timeout.** Your worker lease expires while a peer thinks.
- **Two task states instead of four.** Timeout and rejection are different problems.
- **Catching and retrying `CardRejected`.** It is a decision, not a blip.
- **A card with no expiry.**
- **A localhost exemption with no `DEV ONLY` marker.**
- **Pointing today's lab at a real third-party endpoint.** Build the counterparty.
- **Not adding the hostile-partner cases to the red-team corpus.** Twenty minutes, permanent coverage.

---

## §8 Request budget

**Declared: ~10 model requests (your side) + whatever the simulator spends.**

| What | Requests |
|---|---|
| All card tests | **0** |
| Partner simulator (scripted answers, no model) | **0** |
| One Mandala run that delegates to the peer | ≤ 6 |
| Hostile-partner attacks through the red-team harness | ≤ 4 |

**Make the simulator scripted, not model-backed.** A partner that returns fixed strings is
deterministic, free, and lets you write the exact hostile payload you want. A model-backed partner is
a second system to debug and it will not reliably produce the attack you are testing for.

---

## §9 Verify before you code

Written **2026-08-21** against `a2a-sdk==1.1.2`:

- **The v1.0 Agent Card schema** — exact field names for provider/organization, `url`, `skills[].id`,
  and how the signature is carried (JWS in a field? detached? a `.well-known` path?). **Do not guess
  this**; the whole day's structure depends on it.
- **Does the SDK provide a verifier**, and what does it check — signature only, or signature + domain
  binding? If it does the domain binding for you, use it and keep your endpoint check as
  defence-in-depth.
- **Where is a card published?** (`/.well-known/agent.json` or similar.) Your simulator must serve it
  at the right path or you will learn nothing about real discovery.
- **Task lifecycle states** in v1.0 — the real names, so your four-state enum maps onto them.
- **Streaming / push-notification support** — does the SDK expect a callback URL? That is another
  inbound network path and it needs the same thinking as yesterday's webhook.
- **Key material for the simulator**: generate a throwaway keypair, keep it in `days/day-87/lab/`,
  and **gitignore the private key** before you generate it.
- `https://a2a-protocol.org/` — read today, and cite the version you read.

---

## §10 Say it in an interview

> "A2A was the first outward integration — every other one was me calling something I wrote. The
> framing I use is that MCP is agent-as-tool and A2A is agent-as-peer: with MCP I own the loop and the
> server returns a value, whereas with A2A I delegate a task to something with its own loop and it
> returns a *claim*. So the security work is entirely different. The card is a claim by a domain about
> an agent, and I verify in a specific order: allowlist first, then signature, then endpoint binding —
> because a valid signature answers 'is this really from X', never 'should I trust X', and those get
> conflated constantly. The check I'd emphasise is endpoint-versus-signer: a legitimately signed card
> from a trusted partner whose URL points at a different host is the attack that actually works, and
> it's four lines. I also structured it so skills are only readable from a successfully verified card
> — there's no function that hands you skills off a raw dict, so the unsafe state isn't
> representable rather than just discouraged. The peer's answer comes back as the same untrusted type
> I use for ticket bodies and search snippets, so it goes through the same fence, and I built a
> hostile partner simulator and folded its attacks into my existing red-team suite, which now runs on
> every PR. And the peer gets a bounded question and a deadline — never a tool, a credential, or the
> raw ticket."

---

## §11 Done when

```bash
./m check
./m done 87
```
