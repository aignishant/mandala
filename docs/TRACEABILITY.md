# 🧾 TRACEABILITY.md — 138 IDs ↔ 90 days

> Generated 2026-08-20 from `00_MASTER_PLAN_AGENT_STACKS.md` Part 4 (matrices) ↔ Part 5 (phase map).
> **Rule:** every ID appears in ≥1 day; every day cites ≥1 ID *or* is an explicitly ID-free
> infrastructure/gate/capstone day. Regenerate at every phase gate (`/gate N`).
>
> Legend: 🛠️ hands-on lab · 🅿️ concept/awareness only · 🔁 revisited across frameworks

---

## Curriculum A — Agent foundations (30 IDs)

| ID | Topic | Day(s) | Covered |
|---|---|---|---|
| AG-01 🛠️ | What an agent actually is | 3 | ⬜ |
| AG-02 🛠️ | Tool / function calling | 3 | ⬜ |
| AG-03 🛠️ | Structured output | 4 | ⬜ |
| AG-04 🛠️ | Context window as budget | 4 | ⬜ |
| AG-05 🛠️ | The ReAct pattern & its limits | 5 | ⬜ |
| AG-06 🛠️ | Planning vs. reacting | 5 | ⬜ |
| AG-07 🛠️ | Prompting as interface design | 6 | ⬜ |
| AG-08 🛠️ | Errors, retries, idempotency | 6 | ⬜ |
| AG-09 🛠️ | Conversation state & sessions | 7 | ⬜ |
| AG-10 🛠️ | Multi-agent decomposition | 8 | ⬜ |
| AG-11 🅿️ | Orchestration topologies 🔁 | 8 | ⬜ |
| AG-12 🛠️ | Memory taxonomy 🔁 | 7, 47 | ⬜ |
| AG-13 🛠️ | Retrieval & embeddings (the honest RAG day) | 46 | ⬜ |
| AG-14 🅿️ | Fine-tuning vs. RAG vs. prompting | 46 | ⬜ |
| AG-15 🛠️ | Prompt injection | 65 | ⬜ |
| AG-16 🛠️ | The lethal trifecta | 65 | ⬜ |
| AG-17 🛠️ | Least privilege & credential scoping | 66 | ⬜ |
| AG-18 🛠️ | Sandboxing & execution isolation 🔁 | 67 (preview 19) | ⬜ |
| AG-19 🛠️ | Computer use & browser agents | 68 | ⬜ |
| AG-20 🛠️ | Human-in-the-loop patterns 🔁 | 50, 64 | ⬜ |
| AG-21 🅿️ | Graduated autonomy | 84 | ⬜ |
| AG-22 🛠️ | Evals: the three layers | 71 | ⬜ |
| AG-23 🛠️ | LLM-as-judge, honestly | 72 | ⬜ |
| AG-24 🛠️ | Regression gates in CI | 74 | ⬜ |
| AG-25 🛠️ | Observability & tracing concepts 🔁 | 75 | ⬜ |
| AG-26 🛠️ | Rate-limit & cost engineering | 76 (built 6) | ⬜ |
| AG-27 🛠️ | Durable execution 🔁 | 49 | ⬜ |
| AG-28 🅿️ | Streaming UX | 45 (preview 17) | ⬜ |
| AG-29 🅿️ | The framework-choice question | 59 | ⬜ |
| AG-30 🅿️ | Agent economy: identity, trust, payments | 87 | ⬜ |

## Curriculum B — OpenAI Agents SDK (26 IDs)

| ID | Topic | Day(s) | Covered |
|---|---|---|---|
| OAI-01 🛠️ | Install, project shape, first `Agent` | 9 | ⬜ |
| OAI-02 🅿️ | The Responses API underneath | 9 | ⬜ |
| OAI-03 🛠️ | Function tools & the `@tool` decorator | 10 | ⬜ |
| OAI-04 🛠️ | Runner deep-dive & the agent loop | 10 | ⬜ |
| OAI-05 🛠️ | Structured outputs (`output_type`) | 11 | ⬜ |
| OAI-06 🛠️ | Sessions & memory | 11 | ⬜ |
| OAI-07 🛠️ | Context objects & dependency injection | 12 | ⬜ |
| OAI-08 🛠️ | Guardrails: input & output | 12 | ⬜ |
| OAI-09 🛠️ | Handoffs | 13 | ⬜ |
| OAI-10 🛠️ | Agents-as-tools vs. handoffs | 13 | ⬜ |
| OAI-11 🛠️ | Multi-agent patterns in the SDK 🔁 | 14 | ⬜ |
| OAI-12 🛠️ | Tracing | 14 | ⬜ |
| OAI-13 🛠️ | Web & file search, the free way | 15 | ⬜ |
| OAI-14 🅿️ | Hosted tools: code interpreter & computer use | 15 | ⬜ |
| OAI-15 🛠️ | MCP in the Agents SDK 🔁 | 16, 55 | ⬜ |
| OAI-16 🛠️ | Streaming & events | 17 | ⬜ |
| OAI-17 🅿️+🛠️ | Programmatic Tool Calling + free coordinator | 18 | ⬜ |
| OAI-18 🅿️ | The model-native harness (Apr 2026) | 19 | ⬜ |
| OAI-19 🛠️ | Sandbox execution — the $0 lab | 19 | ⬜ |
| OAI-20 🅿️ | Roadmap literacy: code mode & subagents | 19 | ⬜ |
| OAI-21 🛠️ | Long-horizon & durable runs (Temporal) | 20 | ⬜ |
| OAI-22 🅿️ | Realtime & voice agents | 20 | ⬜ |
| OAI-23 🛠️ | Guardrail + approval composition | 21 | ⬜ |
| OAI-24 🛠️ | Evals with the SDK | 72 | ⬜ |
| OAI-25 🅿️ | AgentKit & the platform layer | 21 | ⬜ |
| OAI-26 🛠️ | Deploying an Agents SDK service | 85 | ⬜ |

## Curriculum C — CrewAI (22 IDs)

| ID | Topic | Day(s) | Covered |
|---|---|---|---|
| CR-01 🛠️ | Install, scaffold, YAML vs. code | 23 | ⬜ |
| CR-02 🛠️ | Agents: role, goal, backstory | 23 | ⬜ |
| CR-03 🛠️ | Tasks: description, expected_output, context | 24 | ⬜ |
| CR-04 🛠️ | Sequential process | 24 | ⬜ |
| CR-05 🛠️ | Hierarchical process & the manager agent | 25 | ⬜ |
| CR-06 🛠️ | Tools in CrewAI | 25 | ⬜ |
| CR-07 🛠️ | Structured task output 🔁 | 26 | ⬜ |
| CR-08 🛠️ | Memory system | 26 | ⬜ |
| CR-09 🛠️ | Knowledge sources | 27 | ⬜ |
| CR-10 🛠️ | Guardrails & task validation | 27 | ⬜ |
| CR-11 🛠️ | Testing & training crews | 28 (revisit 77) | ⬜ |
| CR-12 🛠️ | Crew observability | 28 (revisit 75) | ⬜ |
| CR-13 🛠️ | Crews checkpoint: Mandala-mini | 29 | ⬜ |
| CR-14 🛠️ | Flows: @start / @listen | 30 | ⬜ |
| CR-15 🛠️ | Flow state (structured) 🔁 | 30 | ⬜ |
| CR-16 🛠️ | @router & conditional logic | 31 | ⬜ |
| CR-17 🛠️ | Crews inside Flows | 31 | ⬜ |
| CR-18 🛠️ | Persistence & checkpoints | 32 | ⬜ |
| CR-19 🛠️ | HITL in Flows + conversational flows | 33 | ⬜ |
| CR-20 🛠️ | Declarative FlowDefinition DSL | 34 | ⬜ |
| CR-21 🅿️ | Enterprise map: AMP, Crew Studio, ACP | 34 | ⬜ |
| CR-22 🛠️ | Flows checkpoint: Mandala-flow | 35 | ⬜ |

## Curriculum D — LangChain 1.x (14 IDs)

| ID | Topic | Day(s) | Covered |
|---|---|---|---|
| LC-01 🛠️ | 1.x mental model & package layout | 36 | ⬜ |
| LC-02 🛠️ | Chat models & the provider abstraction | 36 | ⬜ |
| LC-03 🛠️ | Messages & standard content blocks | 37 | ⬜ |
| LC-04 🛠️ | Tools (`@tool`) & runtime injection | 37 | ⬜ |
| LC-05 🛠️ | `create_agent` 🔁 | 38 | ⬜ |
| LC-06 🛠️ | Structured output in 1.x 🔁 | 38 | ⬜ |
| LC-07 🛠️ | Middleware: the 1.x extension story | 39 | ⬜ |
| LC-08 🛠️ | Built-in middleware tour | 39 | ⬜ |
| LC-09 🛠️ | Streaming (`stream_events` v3) | 40 | ⬜ |
| LC-10 🛠️ | Short-term memory & threads | 40 | ⬜ |
| LC-11 🅿️ | RAG in 1.x, scoped honestly | 41 | ⬜ |
| LC-12 🅿️ | Deep Agents (`deepagents`) | 41 | ⬜ |
| LC-13 🛠️ | LangChain↔LangGraph seam | 42 | ⬜ |
| LC-14 🛠️ | LangChain checkpoint | 42 | ⬜ |

## Curriculum E — LangGraph 1.x (24 IDs)

| ID | Topic | Day(s) | Covered |
|---|---|---|---|
| LG-01 🛠️ | Graph thinking: state, nodes, edges | 43 | ⬜ |
| LG-02 🛠️ | State schemas & reducers | 43 | ⬜ |
| LG-03 🛠️ | Conditional edges & `Command` 🔁 | 44 | ⬜ |
| LG-04 🛠️ | The Send API & map-reduce | 44 | ⬜ |
| LG-05 🛠️ | Streaming modes | 45 | ⬜ |
| LG-06 🛠️ | Checkpointers = persistence | 47 | ⬜ |
| LG-07 🛠️ | Long-term memory (Store) | 47 | ⬜ |
| LG-08 🛠️ | Durable execution semantics | 49 | ⬜ |
| LG-09 🛠️ | Interrupts: HITL as a runtime feature | 50 | ⬜ |
| LG-10 🛠️ | Time travel & forking | 51 | ⬜ |
| LG-11 🛠️ | Subgraphs | 48 | ⬜ |
| LG-12 🛠️ | Multi-agent: supervisor pattern 🔁 | 48 | ⬜ |
| LG-13 🅿️ | Multi-agent: swarm/peer patterns | 48 | ⬜ |
| LG-14 🛠️ | Tool-error & retry policies in-graph | 49 | ⬜ |
| LG-15 🛠️ | `create_agent` nodes (prebuilt is dead) | 45 | ⬜ |
| LG-16 🛠️ | Functional API | 51 | ⬜ |
| LG-17 🛠️ | LangSmith tracing & debugging | 75 | ⬜ |
| LG-18 🛠️ | Evals in LangSmith | 73 | ⬜ |
| LG-19 🅿️ | LangSmith platform literacy | 76 | ⬜ |
| LG-20 🛠️ | LangGraph Server, the $0 way | 86 | ⬜ |
| LG-21 🛠️ | Scaling stateful graphs | 86 | ⬜ |
| LG-22 🛠️ | Caching & latency | 76 | ⬜ |
| LG-23 🛠️ | LangGraph checkpoint artifact | 52 | ⬜ |
| LG-24 🛠️ | Capstone orchestration decision record | 64 | ⬜ |

## Curriculum F — Protocols & interop (16 + 6 IDs)

| ID | Topic | Day(s) | Covered |
|---|---|---|---|
| MCP-01 🛠️ | Why MCP: the N×M problem | 53 | ⬜ |
| MCP-02 🛠️ | The 2026-07-28 stateless core | 53 | ⬜ |
| MCP-03 🛠️ | Tools, resources, prompts | 54 | ⬜ |
| MCP-04 🛠️ | Build Mandala's first MCP server | 54 | ⬜ |
| MCP-05 🛠️ | Client integration ×4 🔁 | 55 | ⬜ |
| MCP-06 🛠️ | Auth in 2026 | 56 | ⬜ |
| MCP-07 🛠️ | Elicitation | 56 | ⬜ |
| MCP-08 🛠️ | Tasks extension | 57 | ⬜ |
| MCP-09 🅿️ | MCP Apps extension | 57 | ⬜ |
| MCP-10 🅿️ | Extensions framework + EMA | 57 | ⬜ |
| MCP-11 🛠️ | Deprecation lifecycle lab | 58 | ⬜ |
| MCP-12 🅿️ | Governance & registry | 53 | ⬜ |
| MCP-13 🛠️ | Serving an *agent* over MCP | 58 | ⬜ |
| MCP-14 🛠️ | Stateless MCP at scale | 85 | ⬜ |
| MCP-15 🅿️ | Security review of third-party servers | 66 | ⬜ |
| MCP-16 🛠️ | MCP freshness drill | 58 | ⬜ |
| INT-01 🛠️ | A2A v1.0: signed Agent Cards | 87 | ⬜ |
| INT-02 🛠️ | A2A tasks & messages | 87 | ⬜ |
| INT-03 🅿️ | MCP vs. A2A, crisply | 87 | ⬜ |
| INT-04 🅿️ | AP2 mandates | 88 | ⬜ |
| INT-05 🅿️ | x402 / Trusted Agent Protocol | 88 | ⬜ |
| INT-06 🛠️ | Interop capstone wiring | 88 | ⬜ |

---

## ID-free days (deliberate, not gaps)

| Day(s) | Why no ID |
|---|---|
| 1–2 | Phase-0 foundry: repo, pins, keys, CI. Serves Principles 4, 5, 7, 13. |
| 22 | Phase-3 gate day: assemble + write the harness explainer. |
| 60–63 | Bake-off reruns of already-taught IDs + the scorecard write-up. |
| 69–70 | Red-team day and the fix/publish day (they *attack* AG-15…AG-19). |
| 77 | Phase-11 consolidation buffer. |
| 78–83 | Capstone assembly of everything already taught. |
| 89–90 | Portfolio and retrospective. |

**Total distinct IDs: 138.** Every one is slotted.

---

## Deliberate repetition map (Part 6 of the plan)

| Recurring build | OAI | CrewAI | LangChain | LangGraph |
|---|---|---|---|---|
| `TriageResult` structured output | Day 11 (OAI-05) | Day 26 (CR-07) | Day 38 (LC-06) | Day 43 (LG-01/02 state) |
| Severity router | Day 13 (OAI-09 handoff) | Day 31 (CR-16 @router) | Day 39 (LC-07 middleware) | Day 44 (LG-03 Command) |
| Supervisor topology | Day 14 (OAI-11) | Day 25 (CR-05) | — (delegates to LG) | Day 48 (LG-12) |
| Human approval gate | Day 21 (OAI-23) | Day 33 (CR-19) | Day 39 (LC-08 HITL mw) | Day 50 (LG-09 interrupt) |
| MCP `ticket-db` mount | Day 16 / 55 | Day 55 | Day 55 | Day 55 |

If you can narrate this table out loud, you can answer almost any framework question in an interview.
