# Day 81 — CHECKLIST

**IDs covered:** — (capstone assembly: the drafting node and deterministic citation verification)

## Demo command

```bash
uv run pytest tests/test_draft.py -v                             # 0 requests
uv run python days/day-81/lab/draft_only.py T-9003
uv run python days/day-81/lab/hallucination_probe.py             # run it several times
uv run python days/day-79/lab/run_spine.py T-9003                # draft node now real
```

Expected: drafts with only real citations; invented URLs raising `UnsupportedCitation`; the probe
producing all three outcomes at least once.

## Setup

- [ ] `./m start 81` and `./m scaffold 81` run
- [ ] **No new dependencies** — sixth consecutive day
- [ ] Decision made and recorded: does the node catch `ValidationError` or let it propagate?

## The shape of a draft

- [ ] `Resolution` is a validated Pydantic model, not a string
- [ ] `body` has a `min_length` — Day 71's emptiness check promoted from **graded to impossible**
- [ ] Citations capped
- [ ] `confident` and `escalate` are **separate flags** — and can say why
- [ ] `_https_only` validator blocks `http://`, `file://`, `javascript:`
- [ ] `content_hash` **sorts** citations (reorder is not a change)
- [ ] `content_hash` **includes** citations (an added source is a change)
- [ ] `content_hash` **excludes** `confident`/`escalate` — reasoning written down
- [ ] Can state tomorrow's approval semantics in one sentence, from these three decisions

## The drafter

- [ ] Allowlist computed from the findings **passed into this call**, never a global
- [ ] Both untrusted sources fenced with `render_as_data()` / an explicit SOURCES block
- [ ] System prompt characterises injected text (customer's complaint / third party's webpage)
      rather than saying "ignore injections"
- [ ] `budget.charge("draft")` happens whether or not the output parses
- [ ] Both verifiers **raise**, not warn

## Citation verification

- [ ] URLs extracted from **the body as well as** the citations field
- [ ] `UnsupportedCitation` raised on anything not in the findings
- [ ] Docstring states plainly: **provenance, not truth**
- [ ] Claim-support left to the Day-72 judge as a **score**, never a gate — and can say why
- [ ] URL regex tested against real model output (trailing punctuation)

## Internal-text leakage

- [ ] Canary check wired in (Day 69 → Day 71 → now a hard gate)
- [ ] Own fence markers (`SOURCES>>>`, `TICKET>>>`) treated as leakage
- [ ] `"as an AI"` and `"system prompt"` markers included

## The hallucination probe (§4.1)

- [ ] Run with findings that cannot answer the question
- [ ] All three outcomes observed and **written verbatim** into `days/day-81/lab/notes.md`
- [ ] Outcome 2 (real URL, unrelated claim) captured as the example to show a reviewer
- [ ] **Invented-citation rate estimated and recorded** — Day 84 needs this number

## Tests that must be able to fail

- [ ] `test_an_invented_citation_is_rejected`
- [ ] `test_a_url_inlined_in_the_body_is_also_checked` — **flip it:** check only `citations`
- [ ] `test_a_real_citation_passes`
- [ ] `test_no_citations_with_no_findings_is_fine`
- [ ] `test_non_https_citations_are_rejected_at_validation`
- [ ] `test_the_canary_never_reaches_a_draft`
- [ ] `test_fence_markers_in_the_draft_are_treated_as_leakage`
- [ ] `test_an_empty_draft_cannot_be_constructed`
- [ ] `test_the_content_hash_ignores_citation_order`
- [ ] `test_the_content_hash_changes_when_a_citation_is_added`
- [ ] `test_the_content_hash_ignores_the_confidence_flag`
- [ ] `test_provenance_is_not_truth` — **fifth known-limit test in the repo**
- [ ] All cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why check the body for URLs and not just the citations list?
- [ ] Why raise rather than warn on an invented citation?
- [ ] What exactly does citation verification prove, and what does it not?
- [ ] Why is claim-support scored rather than gated?
- [ ] Which changes to a draft should invalidate a human approval, and why those?
- [ ] Why does a draft with no findings still succeed?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~20)
- [ ] **Invented-citation rate recorded** as the justification for the deterministic gate
- [ ] `Field(max_length=...)` semantics on a list confirmed for Pydantic 2.13
- [ ] `@field_validator` / `@classmethod` ordering confirmed
- [ ] `route_chat` usage reporting confirmed on **every** provider (a `None` zeroes the cost report)
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 81
```

- [ ] `notes.md` with all three probe outcomes committed
- [ ] `./m done 81` succeeded
