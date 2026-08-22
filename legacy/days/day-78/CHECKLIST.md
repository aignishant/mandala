# Day 78 — CHECKLIST

**IDs covered:** — (capstone assembly per ADR-003: the intake channel)

## Demo command

```bash
uv run pytest tests/test_intake.py -v                       # 0 requests
uv run python days/day-78/lab/drop_ticket.py T-9001 "printer offline"
uv run python days/day-78/lab/drop_ticket.py T-9002 "printer offline"   # duplicate body
echo "{not json" > inbox/broken.json
uv run python days/day-78/lab/watch_inbox.py                # ctrl-c after a few seconds
ls inbox/.dead/
```

Expected: T-9001 accepted with a run id; the duplicate body accepted **zero** times; `broken.json`
in `.dead/` with a `.why` beside it; zero model requests throughout.

## Setup

- [ ] `./m start 78` and `./m scaffold 78` run
- [ ] **No new dependencies**
- [ ] `inbox/` gitignored **before** the first ticket lands
- [ ] `inbox/.dead/` exists on day one
- [ ] Read ADR-003 before writing anything — today implements it, it does not revise it
- [ ] Nothing new learned today; if a framework feature was reached for, an amendment was written

## Provenance — untrusted text as a type

- [ ] `Untrusted` is frozen and carries its `source`
- [ ] `__str__` **raises**, with a message naming both alternatives
- [ ] `.text` escape hatch exists and its docstring sets the right friction
- [ ] `render_as_data()` fences the text **and neutralises fence markers inside it**
- [ ] `digest` used for logs and Day-82 approval binding — body never logged raw
- [ ] Can say what Day 8's agent label could not do that this type does

## Normalisation

- [ ] Single choke point, on the way in
- [ ] Returns `(clean, notes)` — **every transformation leaves a note**
- [ ] Zero-width stripping in place, cross-referenced to **RT-02** in a comment
- [ ] `MAX_BODY_CHARS` set (cost + prompt-stability control)
- [ ] Comment states plainly whether NFKC folds RT-03's homoglyphs, and names the real control
- [ ] Trade recorded: legitimate non-Latin tickets now carry a normalisation note

## Identity, idempotency, dead letter

- [ ] One ticket → one run id → one trace → one budget → one future thread id
- [ ] `run_id` is **human-prefixed and machine-unique**
- [ ] Idempotency keyed on **body digest**; the reasoning written in the docstring
- [ ] Duplicates emit a span and return `None` — counted, not raised
- [ ] Dead letter moves the file **and writes a `.why`**
- [ ] `RunBudget` created at intake — the RT-12 control now wired into the pipeline
- [ ] Timestamps timezone-aware
- [ ] **Intake makes zero model calls** — and can say why that's a security property

## The watcher

- [ ] Polling, not platform-specific file events
- [ ] Deterministic ordering (`sorted`)
- [ ] `TODO(me, Day 79)` marker names the day
- [ ] `days/day-78/lab/notes.md` states plainly: **this is not a queue** (no retries, no visibility
      timeout, no cross-restart ordering) — Day 85 and Day 89 both need this sentence

## Tests that must be able to fail

- [ ] `test_untrusted_text_refuses_to_be_interpolated` — **flip it:** delete `__str__`, watch an
      f-string silently inject a ticket body
- [ ] `test_dot_text_is_available_for_deliberate_use`
- [ ] `test_the_fence_cannot_be_escaped_from_inside`
- [ ] `test_zero_width_characters_are_stripped_and_noted`
- [ ] `test_every_transformation_leaves_a_note`
- [ ] `test_normalisation_does_not_claim_to_fold_homoglyphs` — **fourth known-limit test in the repo**
- [ ] `test_the_same_body_twice_is_accepted_once`
- [ ] `test_malformed_input_goes_to_the_dead_letter_with_a_reason`
- [ ] `test_intake_costs_zero_model_requests`
- [ ] `test_run_ids_are_human_prefixed_and_unique`
- [ ] All cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why is a type better than a convention for untrusted text?
- [ ] What breaks if the attacker can write your closing fence marker?
- [ ] Why key idempotency on the digest rather than the ticket id?
- [ ] Why does the run id need a human prefix?
- [ ] Why must intake never call a model?
- [ ] Name the four known-limit tests you have now written, and why that habit matters

## Budget & freshness

- [ ] **Zero** logged deliberately in `docs/RATE_BUDGET.md`
- [ ] NFKC behaviour on RT-03 confirmed and recorded
- [ ] `dt.UTC` confirmed on 3.12
- [ ] `Path.rename` cross-filesystem behaviour checked **on the Windows machine**
- [ ] `drop_ticket.py` writes to a temp name and renames into place (write-atomicity)
- [ ] `repr()` still usable on `Untrusted` despite the raising `__str__`
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 78
```

- [ ] No ticket bodies committed; `git status` clean of `inbox/`
- [ ] `./m done 78` succeeded
