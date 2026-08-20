# 📓 CHANGELOG_PLAN.md

> Append-only. Two kinds of entries live here:
> **(a) plan amendments** (Principle 14) and **(b) completed days** (Principle 1, written by `/done`).
> Newest at the top. Nil reports from the Friday freshness check (Principle 13) belong here too —
> "checked, unchanged" is a real result and writing it down is the whole habit.

---

## 2026-08-20 — bulk generation of all 90 day-docs

- **Added** `docs/CURRICULUM_INDEX.md` — the 90-day tracker and session entry point.
- **Added** `docs/PINS.md` — live-verified version table (PyPI + GitHub Releases, 2026-08-20).
- **Added** `docs/TRACEABILITY.md` — 138 IDs ↔ 90 days, generated from Part 4 ↔ Part 5.
- **Added** `docs/RATE_BUDGET.md` — empty template; **fill on Day 1** from provider consoles.
- **Added** `docs/adr/ADR-TEMPLATE.md`.
- **Added** `days/day-01/` … `days/day-90/`, each with `LESSON.md` + `CHECKLIST.md`.
  Lab scaffolds are intentionally deferred to `/day NN`.
- **Freshness check run** (results in `docs/PINS.md`):
  - MCP spec — **checked, unchanged** (2026-07-28 still current).
  - `crewai` 1.15.6 → **1.15.17** — patch drift, no action beyond pinning the exact patch.
  - `langgraph` 1.2.9 → **1.2.11** — patch drift, no action.
  - `openai-agents` → **0.22.0** (2026-08-19) — consistent with the plan's "Apr 2026 line".
  - `a2a-sdk` **1.1.2**, `mcp` **2.0.0**, `sentence-transformers` **6.0.0**, `litellm` **1.97.0**.
  - ⚠️ `langchain` **1.2.x → 1.3.15** / `langchain-core` **1.6.0** — **material minor drift**,
    amendment proposed in `docs/03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md`. **Unsigned.**
  - ⚠️ `docs/01_MASTER_PLAN_ADDENDUM_GAPS.md` is **referenced but absent**. Logged in the same
    addendum; resolution is Day 53's first task.
  - ⛔ Free-tier **rate limits not verified** — they require your provider consoles. Day-1 task.

---

## 2026-08-12 — v1.1.0 — ZERO-BUDGET amendment merged

Free tiers only (Gemini · Groq · OpenRouter `:free` · optional local Ollama). No paid key anywhere.
Rows merged from `02_MASTER_PLAN_ADDENDUM_ZERO_BUDGET.md`. Structure unchanged: 90 days, 15 phases,
6 curricula, 138 IDs.

## 2026-08-12 — v1.0.0 — initial multi-framework plan

`00_MASTER_PLAN_AGENT_STACKS.md` created and validated against the live ecosystem.

---

## Completed days

<!-- /done appends one line per day here, newest at the bottom of this section.
     Format: YYYY-MM-DD — Day NN complete — IDs: ... — <sha> — <one-line summary> -->

*(nothing yet — Day 1 is waiting)*
