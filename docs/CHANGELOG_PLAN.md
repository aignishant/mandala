# 📓 CHANGELOG_PLAN.md

> Append-only. Two kinds of entries live here:
> **(a) plan amendments** (Principle 14) and **(b) completed days** (Principle 1, written by `/done`).
> Newest at the top. Nil reports from the Friday freshness check (Principle 13) belong here too —
> "checked, unchanged" is a real result and writing it down is the whole habit.

---

## 2026-08-20 — nine inconsistencies found while writing Days 15–21 (Principle 14)

All nine are **plan-internal contradictions**, not ecosystem drift. None is silently adapted; the
resolution taken in the affected lesson is stated here so it can be overruled.

1. **OAI-13 references "your AG-13 local index" on Day 15, but AG-13 is slotted to Day 46.**
   On Day 15 the embeddings, `sentence-transformers` and `numpy` do not exist yet (PINS ledger:
   Day 46). A semantic index cannot be built on Day 15 without pulling AG-13 forward by 31 days.
   **Resolution taken:** Day 15 builds "file search" with the *interface* AG-13 will keep —
   `kb.search(query, k) -> list[Chunk]` — over a deliberately naive keyword matcher, and Day 46
   replaces the body without touching the signature. The lesson says this out loud rather than
   pretending the naive matcher is the destination.
   **Amendment proposed:** reword the OAI-13 row to "…and 'file search' as a local index whose
   matcher AG-13 (Day 46) upgrades to embeddings." **Unsigned** — decide before Day 16's gate.

2. **The `mcp` SDK was slotted to Day 53 in the ledger, but OAI-15 mounts an MCP server on Day 16.**
   The plan's own OAI-15 row reads "Day 16, 55". Day 16 is a phase gate whose artifact is a mounted
   MCP server; it cannot be written without the package. **Fixed:** ledger split — `mcp==2.0.0` on
   Day 16 (stdio transport only), `httpx==0.28.1` stays on Day 53 where the streamable-HTTP
   deep-dive needs it. No plan change; the ledger was wrong, not the curriculum.

3. **Part 5's Phase-2 gate sentence under-describes its own gate day.** It reads "SDK Triage agent
   with guardrails + handoff, traced end-to-end; ADR-001" and does not mention MCP — yet the same
   Part 5 Phase-2 body says "plus first MCP mount (OAI-15 intro)", and OAI-15 is slotted to Day 16,
   which *is* the gate day. **Resolution taken:** `days/day-16/LESSON.md` §4 treats the MCP mount as
   gate criteria the day adds (evidence-table rows 8–10) rather than silently rewriting the plan's
   gate sentence. **Amendment proposed:** append "; ticket-DB MCP server mounted with approvals" to
   the Phase-2 gate line in Part 5. **Unsigned** — this changes a gate definition, so it is the
   author's call, not the generator's.

4. **OAI-17's row says the model writes "a small JS program"; OpenAI's hosted code execution has
   historically been Python.** This is a 🅿️ feature we cannot run, so the claim cannot be settled
   by experiment here. **Resolution taken:** `days/day-18/LESSON.md` §3.2 refuses to assert the
   language and instructs the student to read it from the live docs and log one line if the docs
   and the plan disagree. **Open — needs the author to check one doc page and correct the Part-4
   row either way.** A matrix fact that is wrong is worse than one that is vague.

5. **OAI-17's row says "fetch 30 tickets"; the fixture holds eleven.** `tests/fixtures/tickets.json`
   is T-1001…T-1010 (Day 2) plus T-9002 (Day 13). **Resolution taken:** Day 18 scales the batch to
   **8** and says so in the lesson. **Amendment proposed:** reword the OAI-17 example to "fetch a
   batch of tickets" so it does not name a number the fixtures cannot supply. **Unsigned.**

6. **Part 5's Phase-3 body says "OAI-16…OAI-25", but OAI-24 is not in Phase 3.** OAI-24 (Evals
   with the SDK) is slotted to **Day 72**, correctly and consistently, in both Part 4 and
   `docs/TRACEABILITY.md`. Only the Phase-3 range shorthand is misleading — it sweeps in an ID
   that lives eleven weeks later. Cosmetic, but it is the kind of range a reader trusts.
   **Amendment proposed:** write it as "OAI-16…OAI-23, OAI-25". **Unsigned.**

7. **OAI-23 is marked 🛠️ but one of its three named ingredients is paid-only.** The row (Part 4,
   line 190) reads "guardrails (fast checks) + human approvals (slow checks) + tool
   `allowed_callers` in one agent" — but `allowed_callers` belongs to **OAI-17** (line 184), which
   is marked **🅿️+🛠️** because it needs a paid Responses key. So a third of a row advertised as
   buildable cannot be built under Principle 5. **Resolution taken:** `days/day-21/LESSON.md`
   flags it in a ⚠️ block, teaches what `allowed_callers` is, states that it cannot run here, and
   shows Mandala's free superset (`permissions.AGENTS` + `ToolSpec.blast_radius` + Day 18's
   coordinator operation allowlist). **Amendment proposed:** re-mark OAI-23 as **🅿️+🛠️**, matching
   OAI-17's own marking. **Unsigned.**

8. **OAI-21's marker contradicts its own description.** The row (Part 4, line 188) is marked
   **🛠️** — hands-on — but its body calls the day "🅿️ lab-lite: run the reference example, read the
   failure semantics." A row cannot be both the buildable tier and the read-only tier.
   **Resolution taken:** `days/day-20/LESSON.md` builds a modest durable workflow (Temporal is open
   source and self-hosted, so it genuinely is free and buildable) and spends its length on failure
   semantics, saying so in §3's opening. **Amendment proposed:** drop "🅿️" from the row body and
   keep 🛠️, since nothing about OAI-21 requires a paid key. **Unsigned.**

9. **`ddgs` was in `docs/PINS.md`'s version table but absent from its dependency ledger.**
   The ledger's own rule is that every package names the day it is first needed, and `ddgs` is
   first needed by OAI-13. **Fixed:** ledger row `15 | uv add "ddgs==9.15.0"` added. No plan
   change — this was a gap in our own evidence file.

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
    **Re-surfaced 2026-08-20 by Day 16**, which needs it as the MCP reference: `CLAUDE.md` line 5
    still points every future day at this missing file. Restore it, or repoint `CLAUDE.md` at the
    plan's Part 2 Protocol row. **Open — needs the author's decision.**
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

---

## Open verification items (raised by lesson generation, unresolved — check before the day that needs them)

| Item | Raised by | Needed before |
|---|---|---|
| Does raw **token** streaming work through `LitellmModel`/Groq as documented for the Responses API? | Day 17 §8 | Day 17's lab |
| Does the model call produce a **generation** or a **response** span? `model_calls()` matches on `"Generation"`; a mismatch silently reports zero. | Day 14 §8 | **Day 18's round-trip measurement** |
| Is `ModelSettings.parallel_tool_calls` present in 0.22.0? It changes Day 18's naive baseline from ~9 calls to ~4. | Day 18 §8 | Day 18's headline number |
| Does the OAI-17 paid feature emit **JS** or **Python**? The plan says JS. | Day 18 §3.2 | correcting the Part-4 row |
| Does 0.22.0 expose **native HITL tool approval** on `function_tool`, or only on hosted/MCP tools? | Day 21 §8 | AG-20 (Day 50) |
