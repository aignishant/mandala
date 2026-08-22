# Day 87 — CHECKLIST

**IDs covered:** INT-01 🛠️ (signed Agent Cards), INT-02 🛠️ (A2A tasks & messages),
INT-03 🅿️ (MCP vs A2A), AG-30 🅿️ (agent economy: identity, trust, payments)

## Demo command

```bash
uv run pytest tests/test_a2a_cards.py -v                     # 0 requests
uv run python days/day-87/lab/partner/serve_partner.py &     # honest partner
uv run python days/day-87/lab/partner_sim.py --card honest
uv run python days/day-87/lab/partner_sim.py --card hostile  # all attacks must be refused
uv run pytest tests/test_redteam.py -v                       # RT-13…RT-19 now included
```

Expected: honest peer task completes and its answer arrives as `Untrusted`; every hostile card
variant rejected with a distinct reason; red-team suite green with the new attacks.

## Setup

- [ ] `./m start 87` and `./m scaffold 87` run
- [ ] `a2a-sdk==1.1.2` verified live, then pinned (Day-87 ledger row)
- [ ] **Private key for the simulator gitignored BEFORE it is generated**
- [ ] Partner is a **local simulator** — nothing points at a real third-party endpoint
- [ ] Simulator is **scripted, not model-backed** — and can say why

## INT-01 — the card

- [ ] Verification order: **allowlist → signature → endpoint → expiry**
- [ ] Can say why a valid signature never answers "should I trust X"
- [ ] **Endpoint-vs-signer check implemented** — the attack most people omit
- [ ] Subdomain endpoints accepted; different hosts rejected (boundary encoded both ways)
- [ ] `expires_at` checked
- [ ] Skills read **only after** all checks pass; no function returns skills from a raw dict
- [ ] `CardRejected` never caught and retried anywhere
- [ ] Localhost exemption marked **`# DEV ONLY`** and added to Day 90's removal ledger
- [ ] Card schema fields taken from the **verified** v1.0 spec, not guessed

## INT-02 — peer tasks

- [ ] Only skills declared on the verified card may be requested
- [ ] Peer answer wrapped as `Untrusted` with `source="a2a:<domain>/<skill>"` — third untrusted source
- [ ] **Four** task states: completed / failed / timeout / rejected
- [ ] Explicit `PEER_TIMEOUT_S` — and can say how it interacts with Day 86's worker lease
- [ ] Peer gets a **budget slice**, charged before the call
- [ ] **No tools, no credentials, no raw ticket body, no internal id scheme sent outward**
- [ ] What is actually sent to the peer written down and reviewed

## The hostile partner (§4.1)

- [ ] Unsigned card — refused
- [ ] Valid signature, untrusted domain — refused
- [ ] Valid signature, endpoint elsewhere — refused
- [ ] Card declaring an unimplemented skill — handled as `failed`, not a crash
- [ ] Injected instructions in the answer — fence held
- [ ] Canary-shaped exfil URL in the answer — tripwire fired
- [ ] Expired card — refused
- [ ] **All seven added to the corpus as RT-13…RT-19** with `wins_if` and `control`
- [ ] `tests/test_redteam.py` green with the additions

## INT-03 / AG-30 — the map

- [ ] `mcp_vs_a2a.md` written **in your own words**
- [ ] Section 1 covers: who owns the loop, value vs claim, what "the other side changed" looks like
      in each, and your defence in each
- [ ] Section 2: the three-layer economy map (A2A / AP2 / x402-TAP), one honest sentence each
- [ ] **Connection noticed and written down:** Day 84's autonomy grant has the same shape as an AP2
      mandate — scoped, capped, expiring, revocable, evidence-backed
- [ ] Can deliver the MCP-vs-A2A paragraph aloud without notes
- [ ] Docs cited with today's date and the spec version read

## Tests that must be able to fail

- [ ] `test_an_unsigned_card_is_rejected`
- [ ] `test_a_valid_signature_from_an_untrusted_domain_is_rejected` — **flip it:** crypto first
- [ ] `test_an_endpoint_outside_the_signing_domain_is_rejected` — **the attack**
- [ ] `test_a_subdomain_endpoint_is_accepted`
- [ ] `test_an_expired_card_is_rejected`
- [ ] `test_skills_are_only_readable_from_a_verified_card`
- [ ] `test_an_undeclared_skill_cannot_be_requested`
- [ ] `test_a_peer_answer_is_untrusted`
- [ ] `test_the_peer_gets_no_credentials_or_tools`
- [ ] `test_card_rejection_is_never_retried`
- [ ] `test_the_localhost_exemption_is_marked_dev_only`
- [ ] All cost **0 model requests**

## Understanding check — answer out loud

- [ ] MCP vs A2A in one paragraph, no notes
- [ ] Why allowlist before signature?
- [ ] Describe the endpoint-vs-signer attack and its fix
- [ ] Why is a peer's answer untrusted when a tool's result is (mostly) not?
- [ ] What happens if a peer takes longer than your worker's lease?
- [ ] What would you need before letting an agent spend money on your behalf?

## Budget & freshness

- [ ] Request count logged in `docs/RATE_BUDGET.md` (declared: ~10)
- [ ] A2A v1.0 card schema verified field by field
- [ ] SDK verifier capabilities confirmed (signature only, or domain binding too?)
- [ ] Card publication path confirmed (`.well-known/...`) and the simulator serves it correctly
- [ ] Task lifecycle state names confirmed against the spec
- [ ] Push-notification / callback support checked — treated as an inbound path like Day 86's webhook
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 87
```

- [ ] `mcp_vs_a2a.md`, partner simulator and new red-team rows committed
- [ ] No private key committed — verified with `git status` and `git grep`
- [ ] `./m done 87` succeeded
