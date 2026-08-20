# Day 6 — CHECKLIST

**IDs covered:** AG-07 🛠️ (prompting as interface design), AG-08 🛠️ (errors, retries, idempotency)
**⭐ Also builds:** `src/mandala/router.py` — the shared provider-fallback router (plan §2.1, rule 2)

## Demo command

```bash
cd days/day-06/lab
uv run python prompt_ablation.py     # the six-variant table
uv run python router_demo.py         # watch the chain fall through on a 429
cd ../../..
uv run pytest tests/test_router.py -v   # 0 network requests, milliseconds
```

## Setup

- [ ] `./m start 6` and `./m scaffold 6` run
- [ ] `uv add "tenacity==9.1.4"`
- [ ] Files created (`src/mandala/router.py`, `prompts.py`, `idempotency.py`, `lab/prompt_ablation.py`, `lab/router_demo.py`, and three test files)

## AG-07 — prompts as APIs

- [ ] `src/mandala/prompts.py` — `Prompt` dataclass, frozen, with a `version`
- [ ] All five parts separated: role / contract / constraints / refusals / output_contract
- [ ] `constraints` and `refusals` are **tuples**, not lists (frozen dataclass)
- [ ] `render(*, drop=...)` is keyword-only and supports ablation
- [ ] Constraints render **one per line**, bulleted
- [ ] `output_contract` renders **last**
- [ ] Every negative instruction offers a positive alternative
- [ ] The prompt-injection refusal is present (Day-65 defence, started today)
- [ ] `TRIAGE` wired into `triage_naked.py` in place of the ad-hoc string

## The ablation — actually run it

- [ ] All six variants run over all ten tickets
- [ ] Baseline row (`drop=None`) recorded
- [ ] **Observed the `refusals` row** — overconfidence on T-1006/T-1007 rises
- [ ] Observed what dropping `contract` does (scope creep)
- [ ] Observed what dropping `constraints` does (invented ids return)
- [ ] **Table saved** — it is interview evidence

## AG-08 — the router ⭐

- [ ] `Router` with a `chain` and one client per provider, built **once** in `__init__`
- [ ] `sleep` is **injected**, not `time.sleep` hardcoded
- [ ] `RateLimitError` caught **before** `APIStatusError`
- [ ] 429 → sleep + `continue` (retry same provider)
- [ ] `APIConnectionError` → sleep + `continue`
- [ ] Non-429 `APIStatusError` → **`break`** (abandon provider, do not retry)
- [ ] `MAX_ATTEMPTS_PER_PROVIDER` then move on
- [ ] `_backoff_seconds` honours `retry-after`, caps it, and survives an HTTP-date value
- [ ] Backoff is **jittered**
- [ ] `Reply` records `provider`, `model`, `attempts`
- [ ] `raw` field has `repr=False`
- [ ] `AllProvidersFailed` carries a per-provider `failures` dict
- [ ] `router_demo.py` observed falling through a real 429

## AG-08 — idempotency

- [ ] `idempotency_key()` hashes `{op, args}` with `sort_keys=True`
- [ ] Key is derived from **arguments**, not a fresh UUID
- [ ] `IdempotentStore.run()` returns the **original** result on a repeat
- [ ] Understood why the in-memory store is acceptable today and what replaces it (Day 11, Day 49)

## Tests that must be able to fail

- [ ] `test_backoff_prefers_the_providers_retry_after`
- [ ] `test_backoff_caps_absurd_retry_after`
- [ ] `test_backoff_falls_back_when_retry_after_is_a_date`
- [ ] `test_backoff_is_jittered` — remove the jitter and confirm it goes **red**
- [ ] `test_falls_through_to_the_next_provider_on_429` (yours to write)
- [ ] `test_does_not_retry_a_400` — asserts `client.calls == 1` (yours to write)
- [ ] `test_raises_when_every_provider_fails` — checks `exc.value.failures` (yours to write)
- [ ] `test_reply_records_which_provider_answered` (yours to write)
- [ ] `test_key_is_stable_across_argument_order`
- [ ] `test_key_changes_with_arguments`
- [ ] `test_retry_does_not_repeat_the_side_effect`
- [ ] `test_prompt_has_a_version`
- [ ] `test_every_negative_instruction_offers_an_alternative`
- [ ] `test_output_contract_is_last`
- [ ] `test_injection_refusal_is_present`
- [ ] **All router tests run with 0 network requests** and finish in well under a second

## Understanding check — answer out loud

- [ ] Why does a 429 get `continue` but a 400 get `break`?
- [ ] What breaks if `APIStatusError` is caught before `RateLimitError`?
- [ ] What exactly does jitter prevent?
- [ ] Why hash the arguments instead of generating a UUID for the idempotency key?
- [ ] Why is injecting `sleep` the most important testability decision in the router?
- [ ] Why does dropping `refusals` cause hallucination rather than silence?
- [ ] Which two later days will replace `IdempotentStore`, and with what?

## Budget

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~100, Groq)

## Freshness

- [ ] Confirmed `RateLimitError` still subclasses `APIStatusError` in `openai` 3.3.1
- [ ] Read tenacity's API and noted in the commit message what it gives you that your router does not

## Commit

```bash
./m check
./m done 6
```

- [ ] `./m done 6` succeeded — trackers updated automatically
