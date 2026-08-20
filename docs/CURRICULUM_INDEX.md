# 🗂️ CURRICULUM_INDEX.md — the 90-day tracker

> **This file is the map. Read it first, every session.**
> Generated in one bulk pass on **2026-08-20** against master plan **v1.1.0** and the live pins in
> `docs/PINS.md`. Every day below has a written `LESSON.md` and `CHECKLIST.md` **already on disk** —
> the teaching is done up front so you can work through it without needing a model in the loop.
>
> **All code lives in the docs.** Nothing is pre-written in `src/`. Every line you will run is
> written out inside a lesson, with a line-by-line walkthrough, and you create the file yourself.
> Every command — `mkdir`, `touch`, `uv add`, the run command — is given in full.

---

## Start here

**First time?** → [`days/day-00-setup/LESSON.md`](../days/day-00-setup/LESSON.md) — install the
toolchain, create the skeleton, and build the tracker. Half a day. Do it before Day 1.

**Already set up?** →

```bash
./m status
```

---

## The daily rhythm

```bash
./m status              # what's next?
./m start 7             # marks Day 7 in-progress, prints its IDs
./m scaffold 7          # creates days/day-07/lab/
                        # ... read LESSON.md, run its Setup block, write the code ...
./m check               # lint + offline tests. Free. No network.
                        # ... tick the boxes in CHECKLIST.md ...
./m done 7              # refuses if boxes are unticked or check is red;
                        # otherwise commits and updates every tracker file
```

**You never hand-edit this file.** `./m done` and `./m sync` own the Status column below, plus
`docs/TRACEABILITY.md`, `docs/CHANGELOG_PLAN.md`, and each lesson's frontmatter. That automation is
built on Day 0 and explained line by line in
[`days/day-00-setup/TRACKER.md`](../days/day-00-setup/TRACKER.md).

**Status legend:** ⬜ not started · 🟨 in progress · ✅ done · 🎯 phase gate

---

## Setup (before Phase 0)

| Day | Title | IDs | Kind | Status |
|---|---|---|---|---|
| [0](../days/day-00-setup/LESSON.md) | Setup — toolchain, skeleton, and the tracker | — | setup | ⬜ |

---

## Phase map at a glance

| Phase | Days | Theme | Gate artifact |
|---|---|---|---|
| 0 | 1–2 | Foundry | `make check` green, pins committed |
| 1 | 3–8 | Agents from first principles (no frameworks) | naked agent passes a 10-case golden set |
| 2 | 9–16 | OpenAI Agents SDK core | traced Triage agent + ADR-001 |
| 3 | 17–22 | Agents SDK advanced (zero-budget cut) | long-horizon agent in a local Docker sandbox + harness explainer |
| 4 | 23–29 | CrewAI Crews | Mandala-mini passes `crewai test` thresholds |
| 5 | 30–35 | CrewAI Flows | persisted HITL flow; kill mid-run and resume |
| 6 | 36–42 | LangChain 1.x | middleware-hardened `create_agent` + ADR-002 |
| 7 | 43–52 | LangGraph 1.x | durable, interruptible Mandala core + time travel |
| 8 | 53–58 | MCP (2026-07-28) | one stateless `ticket-db` consumed by all four frameworks |
| 9 | 59–64 | The bake-off 🥇 | scorecard + ADR-003 (cold-read signed) |
| 10 | 65–70 | Safety & security | lethal-trifecta separation table + sandbox + computer-use demos |
| 11 | 71–77 | Evals & observability | every behavior has a failing-able test; one trace destination |
| 12 | 78–84 | Capstone build | 20 unseen tickets end-to-end, zero unapproved writes |
| 13 | 85–88 | Deployment & interop (local-first, $0) | 3-replica MCP behind a local LB; A2A partner-sim green |
| 14 | 89–90 | Portfolio & handoff | a stranger runs Mandala from the README in <15 min |

---

## Phase 0 — Days 1–2 — Foundry

| Day | Title | IDs | Kind | Status |
|---|---|---|---|---|
| [1](../days/day-01/LESSON.md) | Foundry I — the repo, the pins, the three free keys | infra · P4 · P5 | lab | ⬜ |
| [2](../days/day-02/LESSON.md) | Foundry II — CI, quality gates, and the docs machine | infra · P7 · P13 | gate 🎯 | ⬜ |

## Phase 1 — Days 3–8 — Agents from first principles

| Day | Title | IDs | Kind | Status |
|---|---|---|---|---|
| [3](../days/day-03/LESSON.md) | The loop, naked | AG-01, AG-02 | lab | ⬜ |
| [4](../days/day-04/LESSON.md) | Shapes and budgets — structured output & the context window | AG-03, AG-04 | lab | ⬜ |
| [5](../days/day-05/LESSON.md) | ReAct and its ceiling — reacting vs. planning | AG-05, AG-06 | lab | ⬜ |
| [6](../days/day-06/LESSON.md) | Prompts as APIs, and the router that never dies | AG-07, AG-08 | lab | ⬜ |
| [7](../days/day-07/LESSON.md) | Memory that survives the turn | AG-09, AG-12 | lab | ⬜ |
| [8](../days/day-08/LESSON.md) | Two agents, two credentials | AG-10, AG-11 | gate 🎯 | ⬜ |

## Phase 2 — Days 9–16 — OpenAI Agents SDK core

| Day | Title | IDs | Kind | Status |
|---|---|---|---|---|
| [9](../days/day-09/LESSON.md) | First `Agent`, borrowed engine | OAI-01, OAI-02 | lab | ⬜ |
| [10](../days/day-10/LESSON.md) | Tools and the Runner | OAI-03, OAI-04 | lab | ⬜ |
| [11](../days/day-11/LESSON.md) | Contracts and conversations | OAI-05, OAI-06 | lab | ⬜ |
| [12](../days/day-12/LESSON.md) | Context injection and guardrails | OAI-07, OAI-08 | lab | ⬜ |
| [13](../days/day-13/LESSON.md) | Handoffs vs. agents-as-tools | OAI-09, OAI-10 | lab | ⬜ |
| [14](../days/day-14/LESSON.md) | Topologies and traces | OAI-11, OAI-12 | lab | ⬜ |
| [15](../days/day-15/LESSON.md) | Search without a credit card | OAI-13, OAI-14 | lab | ⬜ |
| [16](../days/day-16/LESSON.md) | First MCP mount + ADR-001 | OAI-15 | gate 🎯 | ⬜ |

## Phase 3 — Days 17–22 — OpenAI Agents SDK advanced

| Day | Title | IDs | Kind | Status |
|---|---|---|---|---|
| [17](../days/day-17/LESSON.md) | Streaming, and why users forgive latency they can see | OAI-16, AG-28 | lab | ⬜ |
| [18](../days/day-18/LESSON.md) | Programmatic tool calling & the free coordinator | OAI-17 | lab | ⬜ |
| [19](../days/day-19/LESSON.md) | The harness, the sandbox, and the Docker box you build yourself | OAI-18, OAI-19, OAI-20 | lab | ⬜ |
| [20](../days/day-20/LESSON.md) | Durable runs with Temporal; realtime awareness | OAI-21, OAI-22 | lab | ⬜ |
| [21](../days/day-21/LESSON.md) | Guardrails + approvals composed; AgentKit literacy | OAI-23, OAI-25 | lab | ⬜ |
| [22](../days/day-22/LESSON.md) | Phase-3 gate — long-horizon sandboxed agent + harness explainer | — | gate 🎯 | ⬜ |

## Phase 4 — Days 23–29 — CrewAI Crews

| Day | Title | IDs | Kind | Status |
|---|---|---|---|---|
| [23](../days/day-23/LESSON.md) | Scaffold, roles, and the YAML question | CR-01, CR-02 | lab | ⬜ |
| [24](../days/day-24/LESSON.md) | Tasks are the unit of work; the sequential process | CR-03, CR-04 | lab | ⬜ |
| [25](../days/day-25/LESSON.md) | The manager that mis-delegates; tools as permissions | CR-05, CR-06 | lab | ⬜ |
| [26](../days/day-26/LESSON.md) | Structured task output and the memory system | CR-07, CR-08 | lab | ⬜ |
| [27](../days/day-27/LESSON.md) | Knowledge sources and task guardrails | CR-09, CR-10 | lab | ⬜ |
| [28](../days/day-28/LESSON.md) | `crewai test`, `crewai train`, and crew observability | CR-11, CR-12 | lab | ⬜ |
| [29](../days/day-29/LESSON.md) | Mandala-mini — the Phase-4 gate crew | CR-13 | gate 🎯 | ⬜ |

## Phase 5 — Days 30–35 — CrewAI Flows

| Day | Title | IDs | Kind | Status |
|---|---|---|---|---|
| [30](../days/day-30/LESSON.md) | Flows: `@start`, `@listen`, and typed state | CR-14, CR-15 | lab | ⬜ |
| [31](../days/day-31/LESSON.md) | Routers, and crews inside flows | CR-16, CR-17 | lab | ⬜ |
| [32](../days/day-32/LESSON.md) | Persistence and checkpoint restore | CR-18 | lab | ⬜ |
| [33](../days/day-33/LESSON.md) | HITL in flows + conversational flows | CR-19 | lab | ⬜ |
| [34](../days/day-34/LESSON.md) | The declarative FlowDefinition DSL + the enterprise map | CR-20, CR-21 | lab | ⬜ |
| [35](../days/day-35/LESSON.md) | Mandala-flow — the Phase-5 gate | CR-22 | gate 🎯 | ⬜ |

## Phase 6 — Days 36–42 — LangChain 1.x

| Day | Title | IDs | Kind | Status |
|---|---|---|---|---|
| [36](../days/day-36/LESSON.md) | The 1.x mental model and the provider abstraction | LC-01, LC-02 | lab | ⬜ |
| [37](../days/day-37/LESSON.md) | Messages, content blocks, and schema-first tools | LC-03, LC-04 | lab | ⬜ |
| [38](../days/day-38/LESSON.md) | `create_agent` and structured output, fourth time around | LC-05, LC-06 | lab | ⬜ |
| [39](../days/day-39/LESSON.md) | Middleware — the 1.x extension story | LC-07, LC-08 | lab | ⬜ |
| [40](../days/day-40/LESSON.md) | Streaming v3 and short-term memory | LC-09, LC-10 | lab | ⬜ |
| [41](../days/day-41/LESSON.md) | RAG scoped honestly, and Deep Agents | LC-11, LC-12 | concept | ⬜ |
| [42](../days/day-42/LESSON.md) | The LangChain↔LangGraph seam + ADR-002 | LC-13, LC-14 | gate 🎯 | ⬜ |

## Phase 7 — Days 43–52 — LangGraph 1.x

| Day | Title | IDs | Kind | Status |
|---|---|---|---|---|
| [43](../days/day-43/LESSON.md) | Graph thinking: state, nodes, edges, reducers | LG-01, LG-02 | lab | ⬜ |
| [44](../days/day-44/LESSON.md) | Conditional edges, `Command`, and the Send API | LG-03, LG-04 | lab | ⬜ |
| [45](../days/day-45/LESSON.md) | Streaming a graph; `create_agent` as a node | LG-05, LG-15, AG-28 | lab | ⬜ |
| [46](../days/day-46/LESSON.md) | The one honest RAG day | AG-13, AG-14 | lab | ⬜ |
| [47](../days/day-47/LESSON.md) | Checkpointers and the Store | LG-06, LG-07, AG-12 | lab | ⬜ |
| [48](../days/day-48/LESSON.md) | Subgraphs, supervisors, and swarms | LG-11, LG-12, LG-13 | lab | ⬜ |
| [49](../days/day-49/LESSON.md) | Durable execution and in-graph retry policy | LG-08, LG-14, AG-27 | lab | ⬜ |
| [50](../days/day-50/LESSON.md) | Interrupts — HITL as a runtime feature | LG-09, AG-20 | lab | ⬜ |
| [51](../days/day-51/LESSON.md) | Time travel, forking, and the Functional API | LG-10, LG-16 | lab | ⬜ |
| [52](../days/day-52/LESSON.md) | Phase-7 gate — the durable Mandala core | LG-23 | gate 🎯 | ⬜ |

## Phase 8 — Days 53–58 — MCP (2026-07-28 spec)

| Day | Title | IDs | Kind | Status |
|---|---|---|---|---|
| [53](../days/day-53/LESSON.md) | Why MCP, and what the stateless core changed | MCP-01, MCP-02, MCP-12 | lab | ⬜ |
| [54](../days/day-54/LESSON.md) | Tools, resources, prompts — build `ticket-db` | MCP-03, MCP-04 | lab | ⬜ |
| [55](../days/day-55/LESSON.md) | One server, four clients | MCP-05, OAI-15 | lab | ⬜ |
| [56](../days/day-56/LESSON.md) | Auth in 2026, and Elicitation | MCP-06, MCP-07 | lab | ⬜ |
| [57](../days/day-57/LESSON.md) | Tasks, Apps, and the extensions framework | MCP-08, MCP-09, MCP-10 | lab | ⬜ |
| [58](../days/day-58/LESSON.md) | Deprecation drill, agent-over-MCP, and the freshness habit | MCP-11, MCP-13, MCP-16 | gate 🎯 | ⬜ |

## Phase 9 — Days 59–64 — The bake-off 🥇

| Day | Title | IDs | Kind | Status |
|---|---|---|---|---|
| [59](../days/day-59/LESSON.md) | Bake-off I — the slice on the Agents SDK | AG-29 | lab | ⬜ |
| [60](../days/day-60/LESSON.md) | Bake-off II — the slice on CrewAI | — | lab | ⬜ |
| [61](../days/day-61/LESSON.md) | Bake-off III — the slice on LangChain | — | lab | ⬜ |
| [62](../days/day-62/LESSON.md) | Bake-off IV — the slice on LangGraph | — | lab | ⬜ |
| [63](../days/day-63/LESSON.md) | The scorecard | — | concept | ⬜ |
| [64](../days/day-64/LESSON.md) | ADR-003 — capstone architecture + approval-gate design | LG-24, AG-20 | gate 🎯 | ⬜ |

## Phase 10 — Days 65–70 — Safety & security

| Day | Title | IDs | Kind | Status |
|---|---|---|---|---|
| [65](../days/day-65/LESSON.md) | Prompt injection and the lethal trifecta | AG-15, AG-16 | lab | ⬜ |
| [66](../days/day-66/LESSON.md) | Least privilege, credential scoping, third-party MCP review | AG-17, MCP-15 | lab | ⬜ |
| [67](../days/day-67/LESSON.md) | Sandboxing for real | AG-18 | lab | ⬜ |
| [68](../days/day-68/LESSON.md) | Computer use, on a leash | AG-19 | lab | ⬜ |
| [69](../days/day-69/LESSON.md) | Red team day | — | lab | ⬜ |
| [70](../days/day-70/LESSON.md) | Fixes, and the permission table | — | gate 🎯 | ⬜ |

## Phase 11 — Days 71–77 — Evals & observability

| Day | Title | IDs | Kind | Status |
|---|---|---|---|---|
| [71](../days/day-71/LESSON.md) | The three layers of evals | AG-22 | lab | ⬜ |
| [72](../days/day-72/LESSON.md) | LLM-as-judge, honestly + SDK trace grading | AG-23, OAI-24 | lab | ⬜ |
| [73](../days/day-73/LESSON.md) | Datasets and experiments in LangSmith | LG-18 | lab | ⬜ |
| [74](../days/day-74/LESSON.md) | The CI regression gate | AG-24 | lab | ⬜ |
| [75](../days/day-75/LESSON.md) | Tracing everything | AG-25, LG-17 | lab | ⬜ |
| [76](../days/day-76/LESSON.md) | Rate limits are the budget; caching and tiering | AG-26, LG-19, LG-22 | lab | ⬜ |
| [77](../days/day-77/LESSON.md) | Consolidation + Phase-11 gate | — | gate 🎯 | ⬜ |

## Phase 12 — Days 78–84 — Capstone build

| Day | Title | IDs | Kind | Status |
|---|---|---|---|---|
| [78](../days/day-78/LESSON.md) | Capstone I — the intake channel | — | capstone | ⬜ |
| [79](../days/day-79/LESSON.md) | Capstone II — the triage spine | — | capstone | ⬜ |
| [80](../days/day-80/LESSON.md) | Capstone III — the research organ | — | capstone | ⬜ |
| [81](../days/day-81/LESSON.md) | Capstone IV — resolution drafting with citations | — | capstone | ⬜ |
| [82](../days/day-82/LESSON.md) | Capstone V — the durable approval gate and the first external write | — | capstone | ⬜ |
| [83](../days/day-83/LESSON.md) | Capstone VI — reporting and end-to-end assembly | — | capstone | ⬜ |
| [84](../days/day-84/LESSON.md) | Graduated autonomy review + Phase-12 gate | AG-21 | gate 🎯 | ⬜ |

## Phase 13 — Days 85–88 — Deployment & interop

| Day | Title | IDs | Kind | Status |
|---|---|---|---|---|
| [85](../days/day-85/LESSON.md) | Shipping the services — FastAPI + stateless MCP at scale | OAI-26, MCP-14 | lab | ⬜ |
| [86](../days/day-86/LESSON.md) | LangGraph Server the $0 way; scaling stateful graphs | LG-20, LG-21 | lab | ⬜ |
| [87](../days/day-87/LESSON.md) | A2A v1.0 — signed cards, peer tasks, the agent economy | INT-01, INT-02, INT-03, AG-30 | lab | ⬜ |
| [88](../days/day-88/LESSON.md) | AP2, x402, and the interop capstone | INT-04, INT-05, INT-06 | gate 🎯 | ⬜ |

## Phase 14 — Days 89–90 — Portfolio & handoff

| Day | Title | IDs | Kind | Status |
|---|---|---|---|---|
| [89](../days/day-89/LESSON.md) | README-as-portfolio | — | capstone | ⬜ |
| [90](../days/day-90/LESSON.md) | Retrospective, and the standing habit | — | gate 🎯 | ⬜ |

---

## Companion docs

| File | What it is |
|---|---|
| `00_MASTER_PLAN_AGENT_STACKS.md` | The plan. The single source of truth. |
| `02_MASTER_PLAN_ADDENDUM_ZERO_BUDGET.md` | Why everything runs on $0 and what that changed. |
| `03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md` | ⏳ **Needs your sign-off** — live pin drift + a missing-file gap. |
| `PINS.md` | Live-verified version table (evidence for `pyproject.toml`). |
| `RATE_BUDGET.md` | Live free-tier limits. **Fill on Day 1.** |
| `TRACEABILITY.md` | All 138 IDs ↔ their days. Regenerated at each gate. |
| `CHANGELOG_PLAN.md` | Append-only log: plan amendments + completed days. |
| `adr/` | Architecture decision records (ADR-001…003 + gate records). |
