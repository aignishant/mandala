# Day 56 — CHECKLIST

**IDs covered:** MCP-06 🛠️ (auth in 2026), MCP-07 🛠️ (Elicitation)

## Demo command

```bash
uv run python days/day-56/lab/token_checks.py    # 0 requests — ten ways a token can be wrong
uv run python days/day-56/lab/elicit_demo.py     # 0 requests
uv run pytest tests/test_mcp_auth.py tests/test_elicitation.py -v
```

Expected: one ACCEPTED valid token, one ACCEPTED list-audience, one ACCEPTED within-leeway, and
**seven refusals** — including the scope substring trap.

## Setup

- [ ] `./m start 56` and `./m scaffold 56` run
- [ ] **No identity-provider package installed** — four checks, not an IdP
- [ ] Files created (`auth.py`, `elicit.py`, two tests, three lab files)

## MCP-06 — the four checks

- [ ] Can name all four and say why each is skipped in the wild
- [ ] `EXPECTED_ISSUER` configurable, and RFC 9207's purpose understood (mix-up attacks)
- [ ] `AUDIENCE` matches the server name from Day 54
- [ ] **`aud` handled as a string *or* a list**
- [ ] Expiry has leeway; **issuer and audience have none** — and can say why
- [ ] `TOOL_SCOPES` written — **Day 12's `permissions.py`, on the server side**
- [ ] Can state the difference from Day 55's `ALLOWED_TOOLS`: selection vs. enforcement
- [ ] Unknown tool → refused, not defaulted (**fail closed**)
- [ ] Refusal reasons go to **logs, never to callers**
- [ ] `now` injectable, so expiry is testable without sleeping

## The scope trap

- [ ] `token_checks.py` run
- [ ] **`"scope substring trap"` case examined** — accepted or refused?
- [ ] If accepted: the bug was in your code, and the lab found it. Fixed with `.split()`
- [ ] Can explain why `required in scope` is a privilege escalation

## CIMD (§3.3)

- [ ] Four-row DCR vs. CIMD table filled
- [ ] Can name **all three** places the 2026-07-28 revision pushes state out of the server
- [ ] Can say the thesis sentence out loud

## MCP-07 — Elicitation

- [ ] Can fill the five-row HITL table and say why this one is the odd one out
- [ ] Can state the three outcomes and why decline ≠ cancel
- [ ] **The four defences written into `auth_notes.md`**
- [ ] Schema is a **closed enum** — `additionalProperties: False`
- [ ] Can explain why a closed schema is a *structural* defence, not a textual one
- [ ] Prompt carries attribution (`"ticket-db asks:"`)
- [ ] Echoed user query is bounded
- [ ] Choices bounded to `MAX_CHOICES`
- [ ] Decline and cancel handled in **separate branches**
- [ ] No branch raises — a user's "no" is not an error
- [ ] Established which of Day 55's four clients actually support elicitation

## Tests that must be able to fail

- [ ] `test_a_valid_token_passes`
- [ ] `test_a_wrong_issuer_is_refused` — **flip it:** delete the check, see red
- [ ] `test_a_missing_issuer_is_refused`
- [ ] `test_a_wrong_audience_is_refused`
- [ ] `test_a_list_audience_containing_us_passes`
- [ ] `test_an_expired_token_is_refused`
- [ ] `test_clock_skew_within_leeway_is_tolerated`
- [ ] `test_leeway_applies_to_expiry_only`
- [ ] `test_a_missing_scope_is_refused`
- [ ] `test_a_scope_substring_does_not_grant_access` — **the headline test**
- [ ] `test_an_unknown_tool_is_refused`
- [ ] `test_every_server_tool_has_a_scope` — cross-file invariant
- [ ] `test_refusal_messages_are_not_returned_to_callers`
- [ ] `test_the_schema_is_closed` — **flip it:** allow free text, see red
- [ ] `test_no_free_text_field_exists`
- [ ] `test_choices_are_bounded`
- [ ] `test_the_prompt_says_who_is_asking`
- [ ] `test_the_prompt_bounds_the_echoed_query`
- [ ] `test_the_prompt_never_asks_for_a_secret[4]` — **and its limitation stated**
- [ ] `test_decline_and_cancel_are_handled_differently`
- [ ] All tests cost **0 model requests**

## Wiring it in — the honest check

- [ ] **`validate()` is actually called on every tool call** — not just written in a module
- [ ] Found the mechanism by which a handler receives token claims
- [ ] Only then: decided whether Day 55's localhost-only tests can be deleted
- [ ] If deleted, the deletion is deliberate and logged

## Understanding check — answer out loud

- [ ] Which check does RFC 9207 exist for, and what attack does it stop?
- [ ] Why is there leeway on expiry and none on issuer?
- [ ] What is the difference between Day 55's allowlist and today's scopes?
- [ ] Where does DCR's state go under CIMD?
- [ ] Why is elicitation a phishing surface, and what makes a closed schema a real defence?
- [ ] Why must decline and cancel stay separate?

## Budget & freshness

- [ ] Logged in `docs/RATE_BUDGET.md`: **0 requests**
- [ ] Scheduling insight noted in `RATE_BUDGET.md` §2: front-load the free days when quota is tight
- [ ] Whether the SDK provides token validation — answered
- [ ] How a handler receives claims — answered
- [ ] RFC 9207's status in the spec (required / recommended) — answered
- [ ] CIMD publication, contents and verification — answered; DCR removed or deprecated?
- [ ] Elicitation result shape (`action` values, answer location) — confirmed
- [ ] Whether the spec constrains elicitation schemas — **quoted if so**
- [ ] URL mode understood — does it solve "never elicit secrets" structurally?
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 56
```

- [ ] Day 66's third-party review checklist seeded with the four elicitation defences
- [ ] `./m done 56` succeeded — trackers updated automatically
