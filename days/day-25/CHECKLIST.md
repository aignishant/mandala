# Day 25 — CHECKLIST

**IDs covered:** CR-05 🛠️ (hierarchical process & the manager agent), CR-06 🛠️ (tools in CrewAI)

## Demo command

```bash
uv run python days/day-25/lab/toolkit_audit.py            # 0 model calls
uv run python days/day-25/lab/hierarchical_crew.py T-1004
uv run python days/day-25/lab/misdelegation.py            # 5 runs, vague contracts
uv run python days/day-25/lab/misdelegation.py --sharp     # 5 runs, sharp contracts
```

## Setup

- [ ] `./m start 25` and `./m scaffold 25` run
- [ ] No new packages
- [ ] **Audited `crewai_tools` for paid dependencies** — free/paid split written down
- [ ] Picked three catalogue tools and checked what each requires
- [ ] Files created (`crew/tools.py`, three lab files, one test file)

## CR-05 — the hierarchical process

- [ ] Can state the plan's phrase and mean it: **least code, least control**
- [ ] Can name the three levers and what each does **not** control
- [ ] Can recite the three-supervisors table (Day 8 / Day 14 / today)
- [ ] `manager_llm` runs on **Gemini**, workers on Groq — can justify from RATE_BUDGET rule 4
- [ ] `allow_delegation=False` stated explicitly on every worker
- [ ] Read the `verbose` delegation chatter — the only window until Day 28

## The mis-delegation experiment (§3.3) — do not skip

- [ ] `misdelegation.py` run 5× with **vague** contracts: correct **___ / 5**
- [ ] `misdelegation.py --sharp` run 5× with **sharp** contracts: correct **___ / 5**
- [ ] (If quota was tight, RUNS reduced to 3 — **and recorded as such**, not fabricated)
- [ ] Sharp contracts each carry a **"Do NOT"** clause naming the other task's job
- [ ] Matched the observation to the §3.3 table and know which row I landed on
- [ ] If sharp contracts still mis-route: recognised this as a **design** problem — the roles are
      too similar — not a prompt problem

## The tool I did not grant (§3.4)

- [ ] `toolkit_audit.py` run
- [ ] Understood that `agent.tools` is **my own input read back**, not the runtime toolkit
- [ ] **Found where CrewAI exposes the runtime toolkit** (the TODO(me)) and printed it
- [ ] Names of the injected delegation tools recorded: **___________**
- [ ] Confirmed `allow_delegation`'s actual default in 1.15.17: **___**
- [ ] If the default is `True`, logged it in `docs/CHANGELOG_PLAN.md` — different security posture
- [ ] Can defend Mandala's position: delegation is a capability, off unless written down

## CR-06 — tools as permissions

- [ ] Wrappers only — **no tool reimplemented**; `_run` delegates to Day 10's `RAW_TOOLS`
- [ ] `tool.name` matches the `mandala.permissions.TOOLS` key exactly (the join key)
- [ ] `args_schema` bounds every argument (`max_length`, `ge`/`le`)
- [ ] Every description carries negative guidance
- [ ] `draft_reply`'s description **states the approval gate to the model**
- [ ] `tools_for()` **raises** on a missing wrapper — can say why a partial list is worse
- [ ] `kb_search` wrapper written (the TODO(me)) — found the seam past Day 15's `@function_tool`
- [ ] Tool order deterministic (`sorted`)
- [ ] Can state the restated invariant: capabilities = **declared tools + whatever the framework attached**

## Tests that must be able to fail

- [ ] `test_every_wrapper_name_is_in_the_permission_table`
- [ ] `test_tools_for_matches_the_grant_exactly`
- [ ] `test_a_missing_wrapper_raises_rather_than_narrowing_the_grant` — **flip it**, and watch the
      "helpful" version pass while a capability vanishes
- [ ] `test_no_agent_holds_untrusted_input_and_write_ability` — still `[]`
- [ ] `test_every_tool_bounds_its_arguments` (+ TODO(me): read Pydantic metadata properly)
- [ ] `test_every_tool_description_says_what_it_does_not_do`
- [ ] `test_delegation_is_off_unless_deliberately_granted` — **flip it**
- [ ] `test_the_runtime_toolkit_contains_nothing_undeclared` — ships **failing**; this is the day's
      real finding, so close it
- [ ] `ALLOWED_FRAMEWORK_TOOLS` written, with a **reason next to each entry**
- [ ] Every test costs **0 model requests**

## Understanding check — answer out loud

- [ ] Where is my actual leverage over a manager I did not write?
- [ ] Why is "sharp contracts still mis-route" the most valuable outcome?
- [ ] Why is delegation a permissions question rather than a topology detail?
- [ ] Why wrap the Day-10 tools instead of writing CrewAI-native ones?
- [ ] Why must a missing wrapper raise rather than narrow the grant?
- [ ] What is the fourth time the curriculum has said "the safe value is the default"?

## Budget & freshness

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~154, Groq + Gemini)
- [ ] Load genuinely split across two providers — neither free tier exhausted
- [ ] `Process.hierarchical` behaviour with neither `manager_llm` nor `manager_agent` confirmed
- [ ] `BaseTool` required members confirmed for 1.15.17
- [ ] `tasks_output[i].agent` shape confirmed — the whole measurement depends on it
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 25
```

- [ ] Bake-off list updated: supervisor in one keyword gained; router prompt and toolkit visibility lost
- [ ] `verbose=True` turned back off after the experiment
- [ ] `./m done 25` succeeded — trackers updated automatically
