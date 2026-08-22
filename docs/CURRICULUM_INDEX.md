---
name: curriculum-index
plan: mandala
plan_version: "v2.0.0"
generated: "2026-08-22"
days: 90
---

# 📇 Curriculum index — Project Mandala, Days 1–90

Generated from `docs/00_MASTER_PLAN_AGENT_STACKS.md` Part 4 (matrices) ↔ Part 5 (phase map).
Every day cites ≥1 ID; every ID appears in ≥1 day. Regenerate at every phase gate.

**This file is the map, not the progress.** It never carries a status column —
[`TRACKER.md`](TRACKER.md) does, and it is generated from what is actually on disk so it cannot
drift. Edit this file only when the *plan* changes.

**How to read the Kind column:** `setup` = the toolchain and the repo · `lab` = you write and run
code · `concept` = reading plus a written artifact, no new code · `gate` = the phase's
definition-of-done artifact · `capstone` = one component of the final system.

**Run a day:** `./m start N` → read `days/day-NN/LESSON.md` (the hub), then every document in
`parts/` in order → implement the build brief → tick `CHECKLIST.md` → `./m done N`.

---

## Setup — before Phase 0

| Day | Title | IDs | Kind |
|---|---|---|---|
| 0 | Setup — the toolchain, the skeleton, and the driver | — | setup |

Day 0 is not one of the 90. It is the day the workshop gets built:
[`days/day-00-setup/LESSON.md`](../days/day-00-setup/LESSON.md).

---

## Phase map at a glance

| Phase | Days | Theme | Gate artifact |
|---|---|---|---|
| 0 | 1–2 | Foundry | `./m check` green, pins committed, three free keys answering |
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
| 11 | 71–77 | Evals & observability | every behaviour has a failing-able test; one trace destination |
| 12 | 78–84 | Capstone build | 20 unseen tickets end-to-end, zero unapproved writes |
| 13 | 85–88 | Deployment & interop (local-first, $0) | 3-replica MCP behind a local LB; A2A partner-sim green |
| 14 | 89–90 | Portfolio & handoff | a stranger runs Mandala from the README |

---

## Phase 0 · Foundry · Days 1–2

| Day | Title | IDs | Kind |
|---|---|---|---|
| 1 | Foundry I — the repo, the pins, the three free keys | infra | lab |
| 2 | Foundry II — CI, quality gates, and the golden set | infra | gate |

## Phase 1 · Agents from first principles · Days 3–8

| Day | Title | IDs | Kind |
|---|---|---|---|
| 3 | The loop, naked | AG-01, AG-02 | lab |
| 4 | Shapes and budgets — structured output & the context window | AG-03, AG-04 | lab |
| 5 | ReAct and its ceiling — reacting vs. planning | AG-05, AG-06 | lab |
| 6 | Prompts as APIs, and the router that never dies | AG-07, AG-08 | lab |
| 7 | Memory that survives the turn | AG-09, AG-12 | lab |
| 8 | Two agents, two credentials | AG-10, AG-11 | gate |

## Phase 2 · OpenAI Agents SDK core · Days 9–16

| Day | Title | IDs | Kind |
|---|---|---|---|
| 9 | First `Agent`, borrowed engine | OAI-01, OAI-02 | lab |
| 10 | Tools and the Runner | OAI-03, OAI-04 | lab |
| 11 | Contracts and conversations | OAI-05, OAI-06 | lab |
| 12 | Context injection and guardrails | OAI-07, OAI-08 | lab |
| 13 | Handoffs vs. agents-as-tools | OAI-09, OAI-10 | lab |
| 14 | Topologies and traces | OAI-11, OAI-12 | lab |
| 15 | Search without a credit card | OAI-13, OAI-14 | lab |
| 16 | First MCP mount + ADR-001 | OAI-15 | gate |

## Phase 3 · Agents SDK advanced · Days 17–22

| Day | Title | IDs | Kind |
|---|---|---|---|
| 17 | Streaming, and why users forgive latency they can see | OAI-16, AG-28 | lab |
| 18 | Programmatic tool calling & the free coordinator | OAI-17 | lab |
| 19 | The harness, the sandbox, and the Docker box you build yourself | OAI-18, OAI-19, OAI-20 | lab |
| 20 | Durable runs with Temporal; realtime awareness | OAI-21, OAI-22 | lab |
| 21 | Guardrails + approvals composed; AgentKit literacy | OAI-23, OAI-25 | lab |
| 22 | Phase-3 gate — long-horizon sandboxed agent + harness explainer | — | gate |

## Phase 4 · CrewAI Crews · Days 23–29

| Day | Title | IDs | Kind |
|---|---|---|---|
| 23 | Scaffold, roles, and the YAML question | CR-01, CR-02 | lab |
| 24 | Tasks are the unit of work; the sequential process | CR-03, CR-04 | lab |
| 25 | The manager that mis-delegates; tools as permissions | CR-05, CR-06 | lab |
| 26 | Structured task output and the memory system | CR-07, CR-08 | lab |
| 27 | Knowledge sources and task guardrails | CR-09, CR-10 | lab |
| 28 | `crewai test`, `crewai train`, and crew observability | CR-11, CR-12 | lab |
| 29 | Mandala-mini — the Phase-4 gate crew | CR-13 | gate |

## Phase 5 · CrewAI Flows · Days 30–35

| Day | Title | IDs | Kind |
|---|---|---|---|
| 30 | Flows: `@start`, `@listen`, and typed state | CR-14, CR-15 | lab |
| 31 | Routers, and crews inside flows | CR-16, CR-17 | lab |
| 32 | Persistence and checkpoint restore | CR-18 | lab |
| 33 | HITL in flows + conversational flows | CR-19 | lab |
| 34 | The declarative FlowDefinition DSL + the enterprise map | CR-20, CR-21 | lab |
| 35 | Mandala-flow — the Phase-5 gate | CR-22 | gate |

## Phase 6 · LangChain 1.x · Days 36–42

| Day | Title | IDs | Kind |
|---|---|---|---|
| 36 | The 1.x mental model and the provider abstraction | LC-01, LC-02 | lab |
| 37 | Messages, content blocks, and schema-first tools | LC-03, LC-04 | lab |
| 38 | `create_agent` and structured output, fourth time around | LC-05, LC-06 | lab |
| 39 | Middleware — the 1.x extension story | LC-07, LC-08 | lab |
| 40 | Streaming v3 and short-term memory | LC-09, LC-10 | lab |
| 41 | RAG scoped honestly, and Deep Agents | LC-11, LC-12 | concept |
| 42 | The LangChain↔LangGraph seam + ADR-002 | LC-13, LC-14 | gate |

## Phase 7 · LangGraph 1.x · Days 43–52

| Day | Title | IDs | Kind |
|---|---|---|---|
| 43 | Graph thinking: state, nodes, edges, reducers | LG-01, LG-02 | lab |
| 44 | Conditional edges, `Command`, and the Send API | LG-03, LG-04 | lab |
| 45 | Streaming a graph; `create_agent` as a node | LG-05, LG-15, AG-28 | lab |
| 46 | The one honest RAG day | AG-13, AG-14 | lab |
| 47 | Checkpointers and the Store | LG-06, LG-07, AG-12 | lab |
| 48 | Subgraphs, supervisors, and swarms | LG-11, LG-12, LG-13 | lab |
| 49 | Durable execution and in-graph retry policy | LG-08, LG-14, AG-27 | lab |
| 50 | Interrupts — HITL as a runtime feature | LG-09, AG-20 | lab |
| 51 | Time travel, forking, and the Functional API | LG-10, LG-16 | lab |
| 52 | Phase-7 gate — the durable Mandala core | LG-23 | gate |

## Phase 8 · MCP · Days 53–58

| Day | Title | IDs | Kind |
|---|---|---|---|
| 53 | Why MCP, and what the stateless core changed | MCP-01, MCP-02, MCP-12 | lab |
| 54 | Tools, resources, prompts — build `ticket-db` | MCP-03, MCP-04 | lab |
| 55 | One server, four clients | MCP-05, OAI-15 | lab |
| 56 | Auth in 2026, and Elicitation | MCP-06, MCP-07 | lab |
| 57 | Tasks, Apps, and the extensions framework | MCP-08, MCP-09, MCP-10 | lab |
| 58 | Deprecation drill, agent-over-MCP, and the freshness habit | MCP-11, MCP-13, MCP-16 | gate |

## Phase 9 · The bake-off 🥇 · Days 59–64

| Day | Title | IDs | Kind |
|---|---|---|---|
| 59 | Bake-off I — the slice on the Agents SDK | AG-29 | lab |
| 60 | Bake-off II — the slice on CrewAI | — | lab |
| 61 | Bake-off III — the slice on LangChain | — | lab |
| 62 | Bake-off IV — the slice on LangGraph | — | lab |
| 63 | The scorecard | — | concept |
| 64 | ADR-003 — capstone architecture + approval-gate design | LG-24, AG-20 | gate |

## Phase 10 · Safety & security · Days 65–70

| Day | Title | IDs | Kind |
|---|---|---|---|
| 65 | Prompt injection and the lethal trifecta | AG-15, AG-16 | lab |
| 66 | Least privilege, credential scoping, third-party MCP review | AG-17, MCP-15 | lab |
| 67 | Sandboxing for real | AG-18 | lab |
| 68 | Computer use, on a leash | AG-19 | lab |
| 69 | Red team day | — | lab |
| 70 | Fixes, and the permission table | — | gate |

## Phase 11 · Evals & observability · Days 71–77

| Day | Title | IDs | Kind |
|---|---|---|---|
| 71 | The three layers of evals | AG-22 | lab |
| 72 | LLM-as-judge, honestly + SDK trace grading | AG-23, OAI-24 | lab |
| 73 | Datasets and experiments in LangSmith | LG-18 | lab |
| 74 | The CI regression gate | AG-24 | lab |
| 75 | Tracing everything | AG-25, LG-17 | lab |
| 76 | Rate limits are the budget; caching and tiering | AG-26, LG-19, LG-22 | lab |
| 77 | Consolidation + Phase-11 gate | — | gate |

## Phase 12 · Capstone build · Days 78–84

| Day | Title | IDs | Kind |
|---|---|---|---|
| 78 | Capstone I — the intake channel | — | capstone |
| 79 | Capstone II — the triage spine | — | capstone |
| 80 | Capstone III — the research organ | — | capstone |
| 81 | Capstone IV — resolution drafting with citations | — | capstone |
| 82 | Capstone V — the durable approval gate and the first external write | — | capstone |
| 83 | Capstone VI — reporting and end-to-end assembly | — | capstone |
| 84 | Graduated autonomy review + Phase-12 gate | AG-21 | gate |

## Phase 13 · Deployment & interop · Days 85–88

| Day | Title | IDs | Kind |
|---|---|---|---|
| 85 | Shipping the services — FastAPI + stateless MCP at scale | OAI-26, MCP-14 | lab |
| 86 | LangGraph Server the $0 way; scaling stateful graphs | LG-20, LG-21 | lab |
| 87 | A2A v1.0 — signed cards, peer tasks, the agent economy | INT-01, INT-02, INT-03, AG-30 | lab |
| 88 | AP2, x402, and the interop capstone | INT-04, INT-05, INT-06 | gate |

## Phase 14 · Portfolio & handoff · Days 89–90

| Day | Title | IDs | Kind |
|---|---|---|---|
| 89 | README-as-portfolio | — | capstone |
| 90 | Retrospective, and the standing habit | — | gate |

---

## Companion docs

| File | What it is |
|---|---|
| [`00_MASTER_PLAN_AGENT_STACKS.md`](00_MASTER_PLAN_AGENT_STACKS.md) | The plan. The single source of truth. **v2.0.0.** |
| [Part 11 — the depth contract](00_MASTER_PLAN_AGENT_STACKS.md#part-11--the-depth-contract-doc-architecture-v200) | How every day must be written. Read before writing one. |
| [`TRACKER.md`](TRACKER.md) | Generated progress: written / complete / legacy, and the part count per day. |
| [`02_MASTER_PLAN_ADDENDUM_ZERO_BUDGET.md`](02_MASTER_PLAN_ADDENDUM_ZERO_BUDGET.md) | Why everything runs on $0 and what that changed. |
| [`03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md`](03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md) | Live pin drift as of 2026-08-20. |
| [`PINS.md`](PINS.md) | Live-verified version table (evidence for `pyproject.toml`). |
| [`RATE_BUDGET.md`](RATE_BUDGET.md) | Live free-tier limits. **Fill on Day 1.** |
| [`TRACEABILITY.md`](TRACEABILITY.md) | All 138 IDs ↔ their days. Regenerated at each phase gate (plan Part 7). |
| [`CHANGELOG_PLAN.md`](CHANGELOG_PLAN.md) | Append-only log: plan amendments, newest first. |
| [`adr/`](adr/) | Architecture decision records (ADR-001…003 + gate records). |
