# Day 72 — CHECKLIST

**IDs covered:** AG-23 🛠️ (LLM-as-judge, honestly), OAI-24 🛠️ (trace-based grading of SDK runs)

## Demo command

```bash
uv run pytest tests/test_judge.py -v                    # 0 requests
uv run python days/day-72/lab/calibrate.py              # ~40 requests, prints kappa
uv run python days/day-72/lab/position_bias.py          # ~10 requests
uv run python days/day-72/lab/grade_sdk_traces.py       # 0 requests — replays recordings
```

Expected: a kappa with a plain-English verdict; an explicit count of pairwise flips; SDK traces
graded by the **unchanged** Day-71 rubrics.

## Setup

- [ ] `./m start 72` and `./m scaffold 72` run
- [ ] **`human_labels.jsonl` written FIRST** — 20 items, by hand, one sitting, no model open
- [ ] Can honestly say the labels were not influenced by any model output
- [ ] Judge model **pinned by exact ID** in `src/mandala/models.py` and logged in `docs/PINS.md`

## AG-23 — the judge

- [ ] `JUDGE_PROVIDER` differs from the judged system's provider
- [ ] `temperature=0`
- [ ] Verdicts are **binary**, not 1–5 — and can say why
- [ ] Every rubric line is a **property a careful human checks in five seconds**
- [ ] No compound rubric lines
- [ ] Required `evidence` quote, ≤ 15 words, from the reply
- [ ] "Uncertainty is false" stated once, as a default direction
- [ ] Judge is **never told** which agent, model or framework produced the text

## AG-23 — calibration

- [ ] `agreement()` written by hand — no new dependency
- [ ] **Kappa**, not raw agreement, is the headline number
- [ ] `false_pos` and `false_neg` reported separately — and can say which one you care about
- [ ] `zip(strict=True)` so misaligned lists raise
- [ ] `verdict()` refuses to conclude under 20 labels
- [ ] Ran the calibration; kappa recorded per rubric line
- [ ] Where agreement was poor: **rubric rewritten**, not judge swapped
- [ ] Re-ran after the rewrite and recorded the improvement

## Position bias (§4)

- [ ] Five pairs run in both orders
- [ ] Flip count recorded verbatim in the day's notes
- [ ] Can explain why this justifies the per-item binary design
- [ ] Number carried into the Day-77 gate notes

## OAI-24 — grading SDK traces

- [ ] `to_trajectory()` adapter written against a **real exported trace**
- [ ] Span-type mapping verified, not remembered
- [ ] Day-71 rubrics run **unchanged** on SDK traces
- [ ] Unknown span types skipped **and logged** — never silently dropped
- [ ] Test added: a known-write trace still yields a non-empty `writes()`
- [ ] Can say why grading a neutral structure makes the Phase-9 bake-off fair

## Tests that must be able to fail

- [ ] `test_judge_is_not_the_judged` — one line, unbreakable by config drift
- [ ] `test_every_rubric_line_is_a_property_not_a_quality_question`
- [ ] `test_kappa_punishes_a_judge_that_always_says_yes` — raw 0.90, kappa < 0.2
- [ ] `test_perfect_agreement_is_kappa_one`
- [ ] `test_false_positives_are_counted_separately`
- [ ] `test_under_twenty_labels_refuses_to_conclude`
- [ ] `test_mismatched_label_lists_raise_rather_than_truncate`
- [ ] `test_a_verdict_without_evidence_is_void`
- [ ] All of the above cost **0 model requests**

## Understanding check — answer out loud

- [ ] Why is raw agreement misleading, and what does kappa fix?
- [ ] Why judge ≠ judged, in one sentence?
- [ ] Why binary rather than 1–5?
- [ ] Why must a "true" verdict quote evidence?
- [ ] What did your position-bias run show, and what did you change because of it?
- [ ] Why is the fix for poor agreement the rubric rather than the model?
- [ ] What breaks if the trace adapter silently drops an unknown span type?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~60)
- [ ] Calibration recorded as a **one-time cost per rubric line**, not per run
- [ ] Judge provider's quota confirmed **separate** from the judged provider's
- [ ] SDK trace export shape verified on `openai-agents==0.22.0`
- [ ] Trace `metadata` support confirmed (the adapter needs `ticket_id`)
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 72
```

- [ ] `human_labels.jsonl` committed — it is ground truth and it is reusable
- [ ] Kappa per rubric line recorded somewhere Day 77 can find it
- [ ] `./m done 72` succeeded
