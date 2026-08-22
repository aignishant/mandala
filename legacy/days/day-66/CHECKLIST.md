# Day 66 — CHECKLIST

**IDs covered:** AG-17 🛠️ (least privilege & credential scoping), MCP-15 🅿️ (third-party server
review)

## Demo command

```bash
uv run python days/day-66/lab/ambient_audit.py              # 0 requests — run FIRST
uv run python days/day-66/lab/review_a_server.py --snapshot # 0 requests
uv run pytest tests/test_credentials.py tests/test_mcp_review.py -v
cat docs/MCP_REVIEW.md
```

## Setup

- [ ] `./m start 66` and `./m scaffold 66` run
- [ ] No new packages
- [ ] Files created (`credentials.py`, two tests, two lab files, `docs/MCP_REVIEW.md`)

## AG-17 — the audit, first

- [ ] `ambient_audit.py` run **before** designing anything
- [ ] Number recorded: __ of __ modules touch credentials
- [ ] Each one classified: **needs a key**, or **just has access to one**
- [ ] Checked for direct `os.environ` reads outside `config.py`
- [ ] At least one unnecessary reach found — or recorded that there were none

## Credential scoping

- [ ] `ROLE_KEYS` written — **"which it MAY", not "which it uses"**
- [ ] classifier gets **one** key, and the cheapest provider
- [ ] judge's key set is **disjoint** from the judged roles'
- [ ] poster gets **nothing** — profiled before Day 82 builds it
- [ ] router's all-three grant is the **named exception**
- [ ] Unknown role → `NotGranted`, fail closed
- [ ] Construction sites actually use `grant(...)`
- [ ] **The "what this does NOT fix" paragraph written in the module docstring**
- [ ] Four-row control table filled, and a defensible stopping point chosen **and justified**

## MCP-15 — the review

- [ ] Can state the reframing: a server puts **text in your model's context** and **tools in your
      agent's hands**
- [ ] `docs/MCP_REVIEW.md` written, all six sections
- [ ] **Section 3 (the prompt surface) present** — the part a generic dependency review omits
- [ ] Elicitation and Apps both covered (Days 56, 57)
- [ ] Sampling → refuse, and the Day-58 shim referenced
- [ ] Section 6 (ongoing) covers snapshots and the Friday check

## `review_a_server.py`

- [ ] Extends Day 57's `capability_probe.py` rather than duplicating it
- [ ] **Every tool description printed in full**, flagged or not
- [ ] `SUSPICIOUS` understood as a **tripwire, not a filter**
- [ ] Surface digest computed
- [ ] `--snapshot` written under `docs/mcp_snapshots/` and committed
- [ ] **Run twice, digests compared** — stable ordering confirmed, or canonical sorting added
- [ ] **Run against your own server first**, and its false-positive rate noted

## Tests that must be able to fail

- [ ] `test_the_classifier_gets_one_cheap_key`
- [ ] `test_the_judge_cannot_reach_the_judged_provider` — **flip it:** add groq, see red
- [ ] `test_the_poster_needs_no_model_key`
- [ ] `test_an_unknown_role_is_refused`
- [ ] `test_only_the_router_holds_every_key` — the named-exception test
- [ ] `test_every_agent_in_the_permission_table_has_a_credential_grant` — cross-file with Day 65
- [ ] `test_the_module_is_honest_about_its_limits`
- [ ] `test_a_snapshot_exists`
- [ ] `test_our_own_descriptions_do_not_trip_our_own_tripwire`
- [ ] `test_no_tool_takes_an_unbounded_free_text_argument`
- [ ] `test_the_review_checklist_covers_the_prompt_surface`
- [ ] All tests cost **0 model requests**

## Understanding check — answer out loud

- [ ] What is ambient authority, and where does Mandala have it?
- [ ] Why is same-process scoping a speed bump rather than a control?
- [ ] Why must exceptions to least privilege be named?
- [ ] Why is an MCP server's *description* the most under-reviewed part of it?
- [ ] What makes a surface snapshot diffable, and which spec property enables it?
- [ ] Why review your own server before someone else's?

## Budget & freshness

- [ ] Logged in `docs/RATE_BUDGET.md`: **0 requests**
- [ ] Noted again in §2: analysis is free, behaviour is expensive
- [ ] `tools/list` ordering stability confirmed **by experiment**
- [ ] Registry provenance/signature availability — answered, and the checklist adjusted if "no"
- [ ] Any reviewed server added to the Friday freshness check
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 66
```

- [ ] `docs/MCP_REVIEW.md` and the snapshot staged — both are Day-70 gate inputs
- [ ] `./m done 66` succeeded — trackers updated automatically
