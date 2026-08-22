# 💸 Master Plan Addendum 02 — Zero-Budget Amendment (Free-Tier-Only Models)

> **Validated against the live ecosystem on 2026-08-12** (Gemini AI Studio free-tier docs/limits,
> Groq free developer tier, OpenRouter `:free` roster + limits, LangSmith free tier).
> Trigger: **constraint change** — no paid API key or subscription exists for this project.
> Per Principle 14, the plan is amended first. Status: **already merged** into
> `00_MASTER_PLAN_AGENT_STACKS.md` → **v1.1.0**; this file is the record and the rationale.
>
> ⚠️ Interpretation note: the third available key was described as an "open ode api key" — this
> addendum assumes **OpenRouter**. If it is something else, amend §2 accordingly.

---

## Part 1 — ✅ What survives unchanged (most of the plan)

| Claim | Verified? | Evidence / note |
|---|---|---|
| CrewAI runs fully free on Gemini/Groq/OpenRouter | ✅ | LiteLLM-native provider strings (`gemini/…`, `groq/…`, `openrouter/…`). |
| LangChain 1.x / LangGraph 1.x run fully free | ✅ | `langchain-google-genai`, `langchain-groq`; OpenRouter via OpenAI-compatible `base_url`. Open-source local `langgraph dev` server for deployment days. |
| Agents SDK **primitives** run fully free | ✅ | `openai-agents[litellm]` → `model="litellm/…"`; agents, tools, handoffs, guardrails, sessions, structured output all work. Trace upload to OpenAI must be disabled (no key). |
| MCP, A2A curricula unaffected | ✅ | Protocols + SDKs are open source; model calls behind them go through the free router. |
| Evals/observability unaffected | ✅ | LangSmith free Developer tier (mind the monthly trace quota); OTel + console exporters are free. |
| Structure: 90 days, 15 phases, 6 curricula, 138 IDs | ✅ | **No structural change.** Everything below is rewritten rows and one hardened principle. |

---

## Part 2 — 🔑 The three keys and what they're for (merged as plan §2.1)

| Provider | Free-tier shape (order-of-magnitude, 2026-08; **record live values Day 1**) | Role |
|---|---|---|
| **Gemini (AI Studio)** | Free tier now covers the **Flash / Flash-Lite** line (Pro effectively paid-only after the Dec-2025 quota cuts); roughly ~10–30 RPM, few-hundred→~1.5k req/day by model; 1M-token context; **free-tier data may train Google models → fixtures only, never real data** | Daily workhorse |
| **Groq** | Genuinely free, no card; open models (Llama-3.3-70B-class) on LPU; very high req/day, tight tokens/min; OpenAI-compatible endpoint | Fast dev loop, tool-calling drills, second opinion |
| **OpenRouter** | `:free` roster (rotating — e.g. DeepSeek-R1-class reasoning); ~20 RPM, ~50 req/day without a top-up; roster **rotates without notice** | Model diversity, eval judges, reasoning 2nd opinion |
| *(optional)* Ollama | Local, keyless, unlimited, lower quality | Outage/fallback branch |
| *(embeddings)* sentence-transformers | Local, keyless | AG-13 RAG day at $0 |

**New standing rules (now in plan §2.1):** judge ≠ judged provider · one shared fallback router
(Gemini→Groq→OpenRouter→Ollama) with 429 backoff, built Day 6, reused everywhere · every lab
declares its request budget · live limits recorded in `docs/RATE_BUDGET.md`, re-verified every
Friday (`/freshness`).

---

## Part 3 — 🚨 Rows that changed (the paid-only surface, made honest)

The only curriculum materially touched is **B (OpenAI Agents SDK)** — its primitives are free, but
its hosted/platform surface requires a paid OpenAI key. Rule applied: **paid feature → 🅿️ docs-level
mastery + a free replacement lab wherever one exists.** You still learn the concepts (interviews ask
about them); you just never need a card.

| ID | Was | Now |
|---|---|---|
| OAI-01 | First agent on OpenAI models | First agent via `openai-agents[litellm]` on Groq; `tracing_disabled=True`. |
| OAI-02 🛠️→🅿️ | Responses API hands-on | Concept: know Responses vs. Chat-Completions shapes; your calls ride the compatible endpoints. |
| OAI-12 | Tracing incl. OpenAI dashboard | Export to console/OTel/LangSmith free tier; skip the OpenAI dashboard (needs paid key). |
| OAI-13 | Hosted web/file search lab | Hosted tools 🅿️; free lab: search **function tool** on a free backend (`ddgs`-style) + AG-13 local index as "file search". |
| OAI-14 🅿️ | (already concept) | Explicitly marked paid-only; free equivalents land Days 67–68. |
| OAI-17 | Programmatic Tool Calling lab | Paid feature 🅿️ + free analog: a hand-built **coordinator function tool** with the same round-trip economics — great compare/contrast answer. |
| OAI-18 🛠️→🅿️ | Harness hands-on | Docs-level mastery + one-page written explainer (new Phase-3 gate item). |
| OAI-19 | SDK-native sandbox lab | Same guarantee built free: **local Docker sandbox** (no network, read-only mount, hard timeout, destroyed after) driven by a function tool. AG-18 for $0. |
| OAI-22 🅿️ | (already concept) | Unchanged — realtime/voice needs OpenAI; stays awareness. |
| Phase 3 gate | "runs inside the sandboxed harness" | "runs on free models inside the local Docker sandbox + harness explainer". |

Elsewhere (small):

| ID / section | Change |
|---|---|
| Principle 5 | Cost guardrails → **zero-budget guardrails**: the budget currency is rate limits, not dollars. |
| AG-13 | Embeddings pinned to local `sentence-transformers` (no API). |
| AG-26 🅿️→🛠️ | Cost engineering → **rate-limit & cost engineering**: request budgeting, 429 backoff, caching, provider rotation — now a hands-on day because on $0 it's load-bearing. |
| Phase 1 | Naked agent uses the plain `openai` client with `base_url` → Groq/Gemini compatible endpoints; Day 6 builds the shared fallback router. |
| Phase 9 | Bake-off matrix gains a **free-tier friendliness** column. |
| LG-20 | LangGraph deployment via local `langgraph dev` + self-hosted container; managed Platform 🅿️ only. |
| Phase 13 | Deployment is **local-first Docker Compose** (MCP ×3 replicas behind local nginx proves the stateless story); clouds 🅿️, free hosts optional. |
| Part 10 checklist | New item: record live limits into `docs/RATE_BUDGET.md` on Day 1. |

📌 **Effort math:** ±0 days. The paid labs' time is fully absorbed by their free replacement labs,
which are arguably *better* teaching (you build the guarantee instead of renting it).

---

## Part 4 — 🎁 What the constraint buys you (not spin — real curriculum upgrades)

1. **Multi-provider fluency is now forced.** Running four frameworks across three providers daily is
   exactly the vendor-neutrality story the plan's Part 0 thesis needed evidence for.
2. **429s become a first-class teacher.** Free tiers guarantee you'll hit rate limits, so AG-08
   retries and the AG-26 router get exercised by reality, not by simulation.
3. **A sharper interview line:** "I built the sandbox/search/coordination layers myself on a $0
   budget, and I can tell you precisely what the paid hosted versions buy over mine."

## Part 5 — 🚫 Newly excluded (decisions, not blind spots)

| Topic | Why |
|---|---|
| OpenAI hosted tools, harness/sandbox, Responses extras, realtime — *hands-on* | Paid key required; 🅿️ + free replacements per Part 3. |
| Managed clouds (LangGraph Platform cloud, CrewAI AMP runs, paid observability tiers) | Literacy rows only; local-first everywhere. |
| Any provider requiring a card "just to verify" | Violates the constraint; note it and move on. |

---

*Merge checklist: [x] rows merged into `00_MASTER_PLAN_AGENT_STACKS.md` · [x] version bumped
1.0.0 → 1.1.0 · [x] `CLAUDE.md` zero-budget rules updated in the Claude Code guide ·
[ ] log in `docs/CHANGELOG_PLAN.md` on repo creation · [ ] create `docs/RATE_BUDGET.md` on Day 1.*
