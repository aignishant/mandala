# Day 8 — CHECKLIST 🎯 Phase-1 gate

**IDs covered:** AG-10 🛠️ (multi-agent decomposition), AG-11 🅿️ 🔁 (orchestration topologies)

## Demo command

```bash
cd days/day-08/lab
uv run python two_agent_demo.py T-1001
uv run python two_agent_demo.py T-9001      # the injected ticket
cd ../../..
uv run pytest tests/test_golden_set.py -v   # the gate: 10/10
uv run pytest tests/test_permissions.py -v  # 0 requests
```

## Setup

- [ ] `./m start 8` and `./m scaffold 8` run
- [ ] No new packages
- [ ] Files created (`src/mandala/permissions.py`, `agents.py`, `lab/two_agent_demo.py`, `lab/golden_run.py`, two test files, `docs/adr/gate-phase-1.md`)
- [ ] `T-9001` (the injected ticket) added to `tests/fixtures/tickets.json`, clearly marked as an injection test case
- [ ] Day-2 fixture tests updated for 11 tickets (or the injection case kept in a separate file)

## AG-10 — decomposition

- [ ] Can state the **three real reasons** to split, and the three bad ones
- [ ] `permissions.py` — `ToolSpec` with `writes`, `reads_untrusted`, `blast_radius`
- [ ] Every tool has an honest **prose** blast-radius statement
- [ ] `draft_reply` and `post_reply` are **separate tools** (drafting is free, posting is not)
- [ ] `AgentSpec` with `tools: frozenset`, `sees_untrusted_text`, `requires_approval_for_writes`
- [ ] `check()` raises `PermissionDenied` and names what *was* granted
- [ ] `trifecta_violations()` implemented and returns `[]`
- [ ] `Brief` is a Pydantic schema — the **only** channel between the two agents
- [ ] `findings` bounded (`max_length=5`) and forbids verbatim ticket text
- [ ] `recommended_action` is a `Literal` — recommendation, not authority
- [ ] Both prompts are `Prompt` objects (Day 6), versioned
- [ ] `dispatch()` checks permission **before** the registry lookup
- [ ] `PermissionDenied` **raises**; ordinary tool errors still return an error dict — and you can explain why they differ
- [ ] `post_reply` raises `AssertionError` — it must not run before Day 21
- [ ] `research()` and `resolve()` written by **you**

## The demonstration

- [ ] Ran against T-1001 — brief produced, draft produced
- [ ] Leakage check printed `none`
- [ ] Ran against **T-9001** and watched the injection land on nothing
- [ ] Printed the `PermissionDenied` refusal (demonstrating the negative)

## AG-11 — topologies (🅿️)

- [ ] Can name all four and say who decides the next step in each
- [ ] Can name the weakness of each
- [ ] Filled in the framework/topology grid with which day covers what
- [ ] Built the **pipeline**, and can say why not the supervisor today

## Tests that must be able to fail

- [ ] `test_no_agent_holds_the_lethal_trifecta` — grant the researcher `post_reply` and confirm it goes **red**
- [ ] `test_researcher_has_no_write_tools`
- [ ] `test_resolver_has_no_read_tools_for_untrusted_text`
- [ ] `test_agent_tool_sets_do_not_overlap`
- [ ] `test_cross_agent_tool_use_is_denied` (4 cases)
- [ ] `test_every_tool_declares_a_blast_radius`
- [ ] `test_permission_check_happens_before_registry_lookup`
- [ ] `test_golden_ticket[T-1001 … T-1010]` — **10/10**
- [ ] Golden-set rules assert what is *wrong*, not what merely *differs* (T-1003 has no severity rule)
- [ ] Cassettes recorded; the suite replays offline

## 🎯 Phase-1 gate

- [ ] Golden set 10/10
- [ ] `grep -rn "crewai\|langchain\|langgraph\|openai_agents" src/ days/` returns **nothing** (still naked)
- [ ] Every model call goes through `mandala.router`
- [ ] Separation proven by test **and** by demo
- [ ] **Whiteboard test passed** — all six items drawn from memory in 5 minutes
- [ ] `/freshness` run this week, result logged (nil reports count)
- [ ] `docs/adr/gate-phase-1.md` written from the ADR template
- [ ] `git tag phase-1-complete`

## Understanding check — answer out loud

- [ ] When do you split one agent into two? (permissions / context / failure domains)
- [ ] Why is decomposition a *security* control before it is a capability one?
- [ ] What exactly would go wrong if the Resolver received the raw ticket body?
- [ ] Why does `PermissionDenied` raise while a tool error returns a value?
- [ ] Why check permission before the registry lookup?
- [ ] Which four days re-implement the four topologies, in which frameworks?

## Budget

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~82)

## Commit

```bash
./m check
./m done 8
```

- [ ] `./m done 8` succeeded — trackers updated automatically
- [ ] `./m status` shows Phase 1 at 6/6
