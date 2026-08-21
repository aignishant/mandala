---
day: 88
phase: 13
phase_name: "Deployment & interop"
title: "AP2, x402, and the interop capstone"
ids: ["INT-04", "INT-05", "INT-06"]
kind: gate
plan_version: "v1.1.0"
generated: "2026-08-21"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 88 — AP2, x402, and the interop capstone 🎯

**Phase 13 · Deployment & interop** · IDs: **INT-04 🅿️**, **INT-05 🅿️**, **INT-06 🛠️** ·
**Phase-13 gate**

> **Yesterday:** signed cards, verified in the right order, and a hostile partner folded into the
> red-team suite.
> **Today:** the payment layer as concept (**you build none of it**), then the thing you do build —
> the Researcher reachable over **both** MCP and A2A, with one partner-sim exercising both paths.
> Then the Phase-13 gate: the whole system, local, free, and provably distributed.
> **Tomorrow:** the README that a stranger runs in fifteen minutes.

```bash
./m start 88
./m scaffold 88
```

---

## §1 The story

Two halves today, and they are connected by one idea you already built.

**The concept half (INT-04, INT-05).** AP2 mandates answer a question A2A does not: *this agent is
who it says it is — but what is it allowed to do with my money?* The mandate is the authorization,
signed by the user: **agent X may spend ≤ $100, on category Y, until May 1.** Not a prompt saying
"be careful with spending". A signed, scoped, expiring, revocable grant.

Read that sentence and then read Day 84's `Grant`:

```python
Grant(agent, tool, condition, level, granted_on, evidence, review_by)
```

**They are the same object.** Scope (agent + tool + condition), cap (level / amount), expiry
(`review_by`), evidence, revocability. You built an autonomy mandate for your own system four days
ago without calling it that. **This is the most useful realisation in Phase 13** — write it in the
ADR, and it makes AP2 something you understand structurally rather than a spec you skimmed.

x402 and TAP (INT-05) are **awareness only**, and the plan says why: the regulatory ground is still
moving. Know that x402 is a per-request payment challenge (a machine-payable 402 Payment Required)
and TAP-style layers attest identity per transaction. Do not build either. Do not have opinions about
crypto settlement internals; the plan's Part 8 explicitly puts that out of scope.

**The build half (INT-06).** The Researcher — Day 80's organ — exposed two ways:

```
                    ┌── MCP: agent-as-tool  ──►  a client CALLS research(query)
Mandala Researcher ─┤
                    └── A2A: agent-as-peer ──►  a peer DELEGATES a research task
```

**Same organ, two contracts.** That is the day's real lesson: yesterday's MCP-vs-A2A paragraph
becomes concrete when the same code sits behind both, and the differences you have to handle — who
owns the loop, what the response means, how errors surface — are exactly the ones you wrote about.

---

## §2 Setup — run this

No new dependencies (`mcp` from Day 16, `a2a-sdk` from yesterday).

```bash
touch src/mandala/interop/expose_mcp.py
touch src/mandala/interop/expose_a2a.py
touch src/mandala/interop/mandate.py
mkdir -p days/day-88/lab
touch days/day-88/lab/partner_sim_both_paths.py
touch days/day-88/lab/ap2_threat_model.md
touch docs/adr/gate-phase-13.md
touch tests/test_interop_capstone.py
touch tests/test_mandate.py
```

---

## §3 INT-04 — the mandate, as a threat model

You are not implementing AP2. You are writing `days/day-88/lab/ap2_threat_model.md` and one small
dataclass that proves you understood the shape.

```python
# src/mandala/interop/mandate.py
"""AP2-shaped mandate. NOT an AP2 implementation — a model for reasoning about one.

Deliberately mirrors mandala.autonomy.ladder.Grant, because they are the same idea:
a scoped, capped, expiring, revocable authorization backed by evidence.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class Mandate:
    agent: str
    granted_by: str          # the human. Not "system", not "config".
    scope: str               # "refund" | "purchase:parts" — narrow, enumerated
    cap_minor_units: int     # integers only. Never float money.
    currency: str
    not_after: str           # ISO date. No open-ended mandates.
    revoked: bool = False

    def permits(self, *, agent: str, scope: str, amount_minor: int, now: str) -> tuple[bool, str]:
        if self.revoked:
            return False, "mandate revoked"
        if now > self.not_after:
            return False, f"mandate expired {self.not_after}"
        if agent != self.agent:
            return False, f"mandate is for {self.agent!r}"
        if scope != self.scope:
            return False, f"mandate scope is {self.scope!r}"
        if amount_minor > self.cap_minor_units:
            return False, f"{amount_minor} exceeds cap {self.cap_minor_units}"
        return True, "permitted"
```

**Line by line:**

- **`cap_minor_units: int`** — pence, cents, paise. Floats for money is the oldest bug in commercial
  software and an agent computing `0.1 + 0.2` against a cap is a bad place to rediscover it.
- `granted_by` is a **human**, and the type system cannot enforce that — so the threat model must.
  "The config granted it" is how a mandate becomes a rubber stamp.
- `permits()` returns `(bool, reason)`, the same shape as Day 71's rubrics. Fifth time; it is your
  house style now.
- **Checks are ordered cheapest-and-most-categorical first**: revoked, expired, wrong agent, wrong
  scope, over cap. A revoked mandate should not need an amount comparison to be refused.
- `revoked` is a field on the mandate, which is the *wrong* design for real revocation — it means the
  holder decides whether it is revoked. **Say so in the docstring**: real revocation needs a check
  against an authority (a revocation list, a fresh signature check), because anything the agent holds
  locally, the agent can be tricked into ignoring. That observation is worth more than the code.

**Then write the threat model.** Four questions, one paragraph each:

1. **What does a mandate prevent that a prompt does not?** (Prompt: a request. Mandate: a
   verifiable authorization an external party can check.)
2. **What happens when the agent is prompt-injected while holding a mandate?** The injection cannot
   raise the cap or widen the scope — but it can absolutely spend the *whole* cap on something
   stupid, within scope. **A mandate bounds blast radius; it does not prevent misuse.** This is the
   honest and most important paragraph.
3. **Where is the mandate checked?** If the agent checks its own mandate, it is a suggestion. If the
   *counterparty* checks it, it is a control. Map this onto Day 82: your approval check runs in the
   write tool, not in the drafter, for the same reason.
4. **What would you require before granting one?** You already have the answer — Day 84's rule.

---

## §4 INT-06 — one organ, two contracts

```python
# src/mandala/interop/expose_mcp.py — agent-as-tool
"""The Researcher as an MCP tool. The CALLER owns the loop."""

from mcp.server.fastmcp import FastMCP

from mandala.organs.research import research
from mandala.intake.types import Untrusted
from mandala.router.budget import RunBudget

server = FastMCP("mandala-researcher")


@server.tool()
def research_ticket(question: str, max_findings: int = 5) -> list[dict]:
    """Search public documentation and return sourced findings. Read-only."""
    findings = research(Untrusted(question, source="mcp:client"),
                        budget=RunBudget(limit=8), run_id="mcp-inbound")
    return [{"claim": f.claim.text, "url": f.url} for f in findings[:max_findings]]
```

```python
# src/mandala/interop/expose_a2a.py — agent-as-peer
"""The Researcher as an A2A skill. WE own the loop; the peer gets a task and a state machine."""

SKILL = {
    "id": "research_ticket",
    "name": "Research a support issue",
    "description": "Returns sourced findings for a technical support question. Read-only.",
    "inputModes": ["text"],
    "outputModes": ["text"],
}


async def handle_task(task):                       # TODO(me): a2a-sdk task handler
    question = Untrusted(task.message.text, source=f"a2a:{task.peer_domain}")
    findings = research(question, budget=RunBudget(limit=8), run_id=f"a2a-{task.id}")
    ...
```

**Line by line:**

- **The same `research()` call in both.** If you find yourself writing research logic twice, stop —
  the organ boundary from Day 80 exists precisely so this day is two thin adapters.
- **`Untrusted(..., source="mcp:client")` and `source=f"a2a:{peer}"`** — inbound requests are
  untrusted too. This is easy to forget: you have spent the whole plan treating *outputs* as
  untrusted, and today you are the callee. **A question arriving over MCP is attacker-controlled text
  entering your system**, exactly like a ticket body.
- `RunBudget(limit=8)` on inbound calls — **a stranger must not be able to spend your quota.** An
  exposed endpoint with no budget is a free denial-of-service against your free tier (RT-12, from
  the outside this time). Add it to the corpus as RT-20.
- **The MCP version returns a value; the A2A version manages a task with states.** That is the whole
  MCP-vs-A2A difference, in twenty lines, and it is why this exercise exists rather than just
  exposing one.
- Neither exposes anything but research. **Not the drafter, not the approval, and absolutely not
  `post_reply`.** Check the permission table: the Researcher's tools are read-only, so exposing it is
  bounded by a property you established on Day 8 and have tested ever since.

### 4.1 The partner-sim, both paths

```bash
uv run python days/day-88/lab/partner_sim_both_paths.py
```

It must, in one run:

1. discover and **verify** Mandala's Agent Card (yesterday's checks, now from the other side),
2. delegate a research task over **A2A**, receive a completed task,
3. call the same capability over **MCP** through the Day-85 load balancer,
4. **assert the findings are equivalent**, and
5. attempt three abuses: an over-budget flood, a request for an unexposed skill, and an injected
   instruction in the question.

**Point 4 is the gate artifact.** Same organ, two protocols, equivalent answers — that is INT-06
demonstrated rather than asserted. Point 5 is what makes it a Phase-13 artifact rather than a demo.

---

## §5 The Phase-13 gate

The plan's criteria: *Mandala deployed locally (stateless API + checkpointer-backed workers +
3-replica MCP behind a local LB); partner-sim exercises MCP and A2A paths successfully.*

```bash
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.workers.yml up -d
uv run python days/day-85/lab/any_replica_test.py            # 1 answer, 3 replicas
uv run python days/day-86/lab/two_workers_one_thread.py T-9301
uv run python days/day-88/lab/partner_sim_both_paths.py      # both paths, three abuses refused
uv run python scripts/audit_writes.py                        # still zero unapproved writes
uv run pytest -m "eval_unit or eval_trajectory" -q
uv run python scripts/gen_permission_table.py --check
```

`docs/adr/gate-phase-13.md`:

```markdown
# Gate — Phase 13 (Deployment & interop)

Date: 2026-__-__ · Days 85–88 · Reviewer: me (cold read: +1 day)

| Criterion | Evidence | Verdict |
|---|---|---|
| Stateless API | `statefulness_hunt.md`; AST test; 202 on accept | |
| Checkpointer-backed workers | two-workers-one-thread drill; no node ran twice | |
| 3-replica MCP behind a local LB | 1 distinct answer / 3 replicas hit; survived a replica stop | |
| Partner-sim exercises MCP **and** A2A | equivalent findings both paths; 3 abuses refused | |
| Zero unapproved external writes (still) | `audit_writes.py` exit 0 after distributed runs | |

## AP2 / x402 literacy
`days/day-88/lab/ap2_threat_model.md` — and the Day-84 correspondence.
## What is local-only and would change in a funded deployment
…
## DEV ONLY items to remove
(localhost card exemption, `x-replica` header, SQLite checkpointer, …)
## Debts carried into Phase 14
…
```

**Line by line:**

- **The zero-unapproved-writes row appears again**, deliberately. Phase 12 proved it on a single
  process; distribution is exactly the change that could break it. Re-proving an old criterion after
  an architectural change is what a gate is *for*.
- **"DEV ONLY items to remove" is a new section and it is the honest one.** You accumulated four or
  five deliberate shortcuts this phase. Listing them here means Day 89's README does not accidentally
  present them as design.
- Freshness sweep, `git tag -a phase-13-complete`, **cold read tomorrow**. Fourth gate, same
  discipline.

---

## §6 The eval that must be able to fail

```python
# tests/test_mandate.py + tests/test_interop_capstone.py
import pytest

from mandala.interop.mandate import Mandate

pytestmark = pytest.mark.eval_unit
NOW = "2026-08-21"


def _m(**kw) -> Mandate:
    base = dict(agent="resolver", granted_by="you", scope="refund",
                cap_minor_units=10_000, currency="INR", not_after="2026-12-31")
    return Mandate(**{**base, **kw})


def test_money_is_integers_not_floats():
    """Flip it: make the cap a float and rediscover 0.1 + 0.2 against a spending limit."""
    assert isinstance(_m().cap_minor_units, int)
    assert "float" not in Mandate.__annotations__.values().__str__()


def test_a_revoked_mandate_permits_nothing():
    ok, why = _m(revoked=True).permits(agent="resolver", scope="refund", amount_minor=1, now=NOW)
    assert not ok and "revoked" in why


def test_an_expired_mandate_permits_nothing():
    assert not _m(not_after="2020-01-01").permits(
        agent="resolver", scope="refund", amount_minor=1, now=NOW)[0]


def test_scope_and_agent_are_both_checked():
    assert not _m().permits(agent="researcher", scope="refund", amount_minor=1, now=NOW)[0]
    assert not _m().permits(agent="resolver", scope="purchase:parts", amount_minor=1, now=NOW)[0]


def test_the_cap_is_inclusive_and_enforced():
    assert _m().permits(agent="resolver", scope="refund", amount_minor=10_000, now=NOW)[0]
    assert not _m().permits(agent="resolver", scope="refund", amount_minor=10_001, now=NOW)[0]


def test_there_are_no_open_ended_mandates():
    import inspect

    assert "not_after" in inspect.signature(Mandate).parameters
    with pytest.raises(TypeError):
        Mandate(agent="a", granted_by="b", scope="c", cap_minor_units=1, currency="INR")


def test_only_research_is_exposed_over_either_protocol():
    """Flip it: expose the drafter or post_reply and the whole trifecta argument collapses."""
    from mandala.interop import expose_a2a, expose_mcp

    for mod in (expose_mcp, expose_a2a):
        src = inspect.getsource(mod)
        for forbidden in ("post_reply", "approve", "draft("):
            assert forbidden not in src, f"{forbidden} exposed in {mod.__name__}"


def test_inbound_questions_are_untrusted():
    import inspect

    from mandala.interop import expose_a2a, expose_mcp

    for mod in (expose_mcp, expose_a2a):
        assert "Untrusted(" in inspect.getsource(mod)


def test_inbound_calls_are_budgeted():
    """A stranger must not be able to spend your free tier. RT-20, from the outside."""
    import inspect

    from mandala.interop import expose_a2a, expose_mcp

    for mod in (expose_mcp, expose_a2a):
        assert "RunBudget(" in inspect.getsource(mod)


def test_both_paths_call_the_same_organ():
    import inspect

    from mandala.interop import expose_a2a, expose_mcp

    assert all("research(" in inspect.getsource(m) for m in (expose_mcp, expose_a2a))


def test_the_exposed_agent_holds_no_write_tool():
    from mandala.permissions import AGENTS, TOOLS

    assert not any(TOOLS[t].writes for t in AGENTS["researcher"].tools)
```

**Line by line:**

- `test_only_research_is_exposed_over_either_protocol` is the day's headline. Exposing an organ to
  the internet is safe **only** because of a property you established on Day 8 and have re-tested
  every phase since; this test keeps that link explicit.
- `test_inbound_calls_are_budgeted` covers the direction you have never defended before — you have
  spent 87 days making sure *you* do not overspend, and today someone else can.
- `test_there_are_no_open_ended_mandates` uses a `TypeError` on a missing required field. Structural,
  not conventional.
- `test_money_is_integers_not_floats` is slightly cheeky and entirely serious.

---

## §7 Traps

- **Implementing AP2 or x402.** Concept only; the plan is explicit.
- **Floats for money.**
- **A mandate the agent checks on itself.** Then it is a suggestion.
- **Believing a mandate prevents injection.** It bounds blast radius. Say so.
- **`granted_by="system"`.** A rubber stamp with a field name.
- **Open-ended mandates.**
- **Two copies of the research logic.** Two thin adapters, one organ.
- **Forgetting inbound text is untrusted.** You are the callee today.
- **An exposed endpoint with no budget.** Free DoS on your free tier.
- **Exposing the drafter or the write tool.** The trifecta argument collapses.
- **Not re-proving zero-unapproved-writes after distributing.** That is what a gate is for.
- **Leaving DEV ONLY hacks unlisted.** Day 89 will present them as design.
- **Skipping the abuse cases in the partner-sim.** Then it is a demo, not a gate artifact.

---

## §8 Request budget

**Declared: ~20 model requests.**

| What | Requests |
|---|---|
| All tests, mandate model, threat model | **0** |
| Partner-sim both paths (research runs twice) | ≤ 12 |
| Three abuse attempts | ≤ 4 |
| Gate re-runs | ≤ 4 |

**The abuse flood is the one to watch.** If your inbound budget works, the over-budget attempt costs
you ~8 requests and stops; if it does not, it costs whatever the attacker wants. **Run that one
first**, before the polite cases, so you find out cheaply.

---

## §9 Verify before you code

Written **2026-08-21**:

- **A2A skill declaration schema** — the exact fields (`inputModes`, `outputModes`?) and how a task
  handler is registered in `a2a-sdk==1.1.2`.
- **Serving an Agent Card for *your* agent** — path, signing, and what key material you need. You
  verified cards yesterday; publishing one is the other half.
- **`FastMCP` tool return types** on `mcp==2.0.0` — does a `list[dict]` serialise as you expect, and
  what does an exception become on the wire?
- **Does your MCP exposure need to go through the Day-85 LB** for the gate, or does the gate accept a
  direct call? Decide and state it in the ADR.
- **AP2 current status** — read the spec page today and cite the date; this is a moving area and your
  literacy note should say what was true when you wrote it.
- **x402 / TAP** — one paragraph, awareness only, cited.
- **Full `/freshness` sweep** for the gate, nil reports included.

---

## §10 Say it in an interview

> "The payments layer I deliberately didn't build — the plan scoped AP2 and x402 as literacy — but the
> useful part was recognising that an AP2 mandate is structurally identical to the autonomy grant I'd
> built four days earlier: a scoped, capped, expiring, revocable authorization with evidence behind
> it. The honest paragraph in my threat model is that a mandate bounds blast radius but doesn't
> prevent misuse: if my agent gets prompt-injected while holding one, the injection can't raise the
> cap or widen the scope, but it can absolutely spend the whole cap on something stupid within scope.
> And a mandate the agent checks on itself is a suggestion — it's only a control if the counterparty
> checks it, which is the same reason my approval check lives in the write tool rather than in the
> drafter. What I built was the same research organ exposed over both MCP and A2A, and the partner
> simulator asserts the findings are equivalent across both paths, which makes the agent-as-tool
> versus agent-as-peer distinction concrete rather than rhetorical: one returns a value, the other
> manages a task with a state machine. Two things I had to get right that I'd never needed before:
> inbound questions are untrusted text — I'd spent the whole project defending against untrusted
> *outputs* and today I was the callee — and inbound calls get a request budget, because an exposed
> endpoint with no budget is a free denial-of-service against my own free tier. Exposing the organ at
> all was only safe because of a property from week two: that agent holds no write tool, and there's
> been a test asserting it ever since."

---

## §11 Done when

```bash
./m check
./m done 88
```

Phase 13 closes here. **Cold-read `docs/adr/gate-phase-13.md` tomorrow before Day 89.**
