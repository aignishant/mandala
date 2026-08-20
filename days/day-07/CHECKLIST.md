# Day 7 — CHECKLIST

**IDs covered:** AG-09 🛠️ (conversation state & sessions), AG-12 🛠️ 🔁 (memory taxonomy — part 1 of 2, completed Day 47)

## Demo command

```bash
uv run python days/day-07/lab/multi_turn.py ticket-4521 "my login loops after SSO"
uv run python days/day-07/lab/multi_turn.py ticket-4521 "how many other people?"
uv run python days/day-07/lab/multi_turn.py ticket-4521 "what did I first tell you?"
uv run python days/day-07/lab/poison.py
```

Expected: the third run answers from history (proving persistence across processes), and `poison.py`
prints three BLOCKED and one WROTE.

## Setup

- [ ] `./m start 7` and `./m scaffold 7` run
- [ ] No new packages
- [ ] `.mandala/sessions/` created and `.mandala/` added to `.gitignore` (idempotently)
- [ ] Files created (`src/mandala/session.py`, `memory.py`, `lab/multi_turn.py`, `lab/poison.py`, two test files)

## AG-09 — sessions

- [ ] `JsonSession` — `append`, `extend`, `load`, `clear`
- [ ] Session ids validated against an **allowlist regex**, with a length cap
- [ ] `BadSessionId` raised for `../../.env`, `a/b`, `""`, 65+ chars
- [ ] Writes are **atomic** (temp file + `Path.replace`)
- [ ] JSON written with `indent=2` (you will read these files)
- [ ] `_trim_safely` pins the **system message**
- [ ] `_trim_safely` drops **leading orphaned tool messages**
- [ ] `_trim_safely` drops assistant tool-calls whose results fell off the end
- [ ] Handles tool_calls as **both dicts and objects** (JSON round-trip vs. SDK)
- [ ] Trimming happens on **read/send**, never on write
- [ ] `multi_turn.py` prints which provider answered (Day-6 provenance)
- [ ] Ran it 3× and confirmed memory across separate processes
- [ ] Opened `.mandala/sessions/ticket-4521.json` and read it

## AG-12 — memory taxonomy (part 1)

- [ ] Can state the three tiers and give a Mandala example of each
- [ ] `MemoryStore` — `remember`, `recall`, `provenance`, `forget`
- [ ] `WRITABLE_KEYS` is a **`frozenset` allowlist** (not a denylist)
- [ ] `MAX_VALUE_LEN` cap enforced
- [ ] `source` is **keyword-only and mandatory**
- [ ] Rejected writes `return False` — they do not raise
- [ ] History is **append-only**; `recall()` shows latest, `provenance()` shows all
- [ ] Repeating an identical fact does not duplicate it
- [ ] Timestamps are **timezone-aware UTC**
- [ ] Writes are atomic

## The poison preview

- [ ] `poison.py` run
- [ ] Observed 2 blocked by the **allowlist**
- [ ] Observed 1 blocked by the **length cap**
- [ ] **Observed 1 get through** — a poisoned value for an allowed key
- [ ] Can explain what the allowlist actually buys, and which later days add the other layers

## Tests that must be able to fail

- [ ] `test_dangerous_session_ids_are_rejected` (6 cases)
- [ ] `test_session_survives_a_new_object`
- [ ] `test_system_message_is_never_trimmed`
- [ ] `test_trim_does_not_orphan_a_tool_message`
- [ ] `test_write_is_atomic`
- [ ] `test_unlisted_keys_are_rejected`
- [ ] `test_allowlisted_keys_are_accepted`
- [ ] `test_oversized_values_are_rejected`
- [ ] `test_repeating_a_fact_does_not_duplicate_it`
- [ ] `test_history_is_append_only` — change `remember()` to overwrite and confirm it goes **red**
- [ ] `test_every_fact_records_provenance`
- [ ] All tests use `tmp_path` — none touch the real `.mandala/`
- [ ] **All of today's tests cost 0 model requests**

## Understanding check — answer out loud

- [ ] Why is memory "a decision about what you resend" rather than a model feature?
- [ ] What exactly goes wrong with a naive `history[-10:]`?
- [ ] Why trim on read instead of on write?
- [ ] Why does the write use a temp file and a rename?
- [ ] What is the difference in kind between a transcript and a long-term fact?
- [ ] Why an allowlist rather than a denylist, and why is the allowlist still not sufficient?
- [ ] Why must `source` be keyword-only?
- [ ] Which later day replaces `JsonSession`, and which replaces `MemoryStore`?

## Budget

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~26)

## Commit

```bash
./m check
./m done 7
```

- [ ] `./m done 7` succeeded — trackers updated automatically
- [ ] Note: **AG-12 stays ⬜ in TRACEABILITY** until Day 47 also completes — that is correct, not a bug
