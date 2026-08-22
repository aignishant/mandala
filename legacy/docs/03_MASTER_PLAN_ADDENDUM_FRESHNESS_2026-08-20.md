# 🔎 Master Plan Addendum 03 — Freshness findings, 2026-08-20

> **Trigger:** the bulk generation of all 90 day-docs required a live pin re-verification
> (Principle 4 + Principle 13). Per **Principle 14**, findings are recorded and the plan is
> amended *before* any code is written.
> **Status:** ⏳ **proposed — awaiting your sign-off.** Nothing in `00_MASTER_PLAN_AGENT_STACKS.md`
> has been edited yet. Evidence table: `docs/PINS.md`.
> **Updated 2026-08-20 after Day 1** — the method here was re-run against the live APIs; results
> and two consequences are in **Part 6**. The three sign-off boxes in Part 5 are still yours.

---

## Part 1 — Method

On **2026-08-20** every package in the plan's Part 2 was queried directly against the PyPI JSON
API, and the MCP spec + A2A revisions against GitHub Releases. Raw results are in `docs/PINS.md`.
The plan's own baseline was taken **2026-08-12** — eight days earlier — so most rows were expected
to be, and are, unchanged.

---

## Part 2 — Nil reports (checked, unchanged, no action)

| Pin | Baseline | Live 2026-08-20 | Note |
|---|---|---|---|
| MCP specification | 2026-07-28 | **2026-07-28** | The stateless-core revision is still the current one. All of Phase 8 stands as written. |
| `crewai` / `crewai-tools` | 1.15.x | **1.15.17** | Same minor line; patch moved. Plan said "pin the exact patch" — do that with 1.15.17. |
| `langgraph` | 1.2.x (1.2.9) | **1.2.11** | Same minor line. `DeltaChannel`, node timeouts, graceful shutdown all still current. |
| A2A | v1.0 | **v1.0** (`a2a-sdk` 1.1.2) | Phase 13 stands. |
| Python | 3.12 | **3.12 still the safe intersection** | `crewai` caps at <3.14; `openai-agents` needs ≥3.10. 3.12 is comfortably inside. |
| `openai-agents` | "Apr 2026 line" | **0.22.0** (2026-08-19) | Actively released *yesterday*. Zero-budget stance unchanged: primitives free via LiteLLM, hosted surface paid. |
| Zero-budget model story | Gemini / Groq / OpenRouter `:free` / Ollama | unchanged in shape | 🟡 **Partly closed on Day 1 (2026-08-20).** Groq and OpenRouter limits are now recorded in `docs/RATE_BUDGET.md` §1; Gemini's are console-only and still outstanding (§1a). See Part 6. |

---

## Part 3 — 🚨 The one material finding: LangChain moved 1.2.x → 1.3.x

| | Plan baseline (2026-08-12) | Live (2026-08-20) |
|---|---|---|
| `langchain` | **1.2.x** | **1.3.16** (1.3.15 on 2026-08-11; patch bump seen on Day 1) |
| `langchain-core` | 1.2.x-era | **1.6.0** (released 2026-08-19) |

### Why this is a *minor* material change, not a rewrite

LangChain 1.x carries a **public no-breaking-changes-until-2.0 commitment**. Everything Curriculum D
teaches is a 1.x surface that survives the minor bump:

- `create_agent` (in `langchain.agents`) — still the one blessed agent API (LC-05).
- **Middleware** as the extension story instead of subclassing (LC-07, LC-08).
- Standard **content blocks** on messages (LC-03).
- `stream_events` v3 (LC-09).
- `AgentExecutor` still deprecated, still never used here.

So **no LC-* ID changes meaning.** What changes is the *number you pin* and the *docs page you read*.

### Proposed amendment (one-line edits to `00_MASTER_PLAN_AGENT_STACKS.md` Part 2)

```diff
- | LangChain | `langchain`, `langchain-core` | **1.2.x** — `create_agent` ...
+ | LangChain | `langchain`, `langchain-core` | **1.3.16 / core 1.6.0** (verified 2026-08-20) — `create_agent` ...
```

and a matching row in `docs/CHANGELOG_PLAN.md`. Version bump: **v1.1.0 → v1.1.1** (pin refresh, no
structural change; 90 days, 15 phases, 138 IDs all unchanged).

### Day-doc impact

**None to content.** Days 36–42 were generated against the 1.x surface, and each one carries a
"Verify before you code" section that sends you to the live `docs.langchain.com` page for that
exact API before you type anything. Day 36 additionally carries an explicit instruction to read
the 1.2 → 1.3 release notes and log anything surprising.

---

## Part 4 — ⚠️ Known gap: `01_MASTER_PLAN_ADDENDUM_GAPS.md` is missing

`CLAUDE.md` and `00_MASTER_PLAN_AGENT_STACKS.md` both name
**`docs/01_MASTER_PLAN_ADDENDUM_GAPS.md` Part 2** as the standing MCP 2026-07-28 reference
analysis. **That file does not exist in this repo.**

**Effect on the generated days:** the MCP content in Days 53–58 was written from the master plan's
own Part 2 row + the `MCP-01…MCP-16` matrix, which do carry the load-bearing facts (stateless core,
no `initialize`, `Mcp-Method`/`Mcp-Name` headers, extensions framework, Elicitation, Tasks, Apps,
EMA, the Roots/Sampling/Logging deprecation window, AAIF governance). Nothing was invented to fill
the hole.

**Action for you (pick one):**
1. Copy `01_MASTER_PLAN_ADDENDUM_GAPS.md` in from the previous plan's repo (Part 10 kickoff item
   already says to "carry over" it), **or**
2. Amend `CLAUDE.md` + the plan to stop referencing it and name `docs/PINS.md` +
   the MCP spec page as the standing reference instead.

Until then, **Day 53's first task is to resolve this**, and it says so.

---

## Part 5 — Sign-off

- [ ] I accept the LangChain pin refresh (1.2.x → **1.3.16** / core 1.6.0) — bump plan to **v1.1.1**
      · *Day 1 re-verified the number; the acceptance is still yours.*
- [ ] I resolved the `01_MASTER_PLAN_ADDENDUM_GAPS.md` gap (option 1 or 2 above)
      · *Still open. Nothing was written to fill it — see Part 4.*
- [ ] I recorded live free-tier limits into `docs/RATE_BUDGET.md` (Day 1)
      · *Two of three done (Groq, OpenRouter). Gemini needs one console read — `RATE_BUDGET.md` §1a.*

*Once signed, log all three in `docs/CHANGELOG_PLAN.md` and edit Part 2 of the master plan.*

---

## Part 6 — Day-1 execution report (2026-08-20)

The Day-1 lab re-ran this addendum's method rather than trusting it. What came back:

**Pins.** 13 of 15 packages unchanged from the table in `docs/PINS.md`: `openai` 3.3.1,
`python-dotenv` 1.2.3, `openai-agents` 0.22.0, `crewai`/`crewai-tools` 1.15.17, `langchain-core`
1.6.0, `langgraph` 1.2.11, `langsmith` 0.11.1, `litellm` 1.97.0, `mcp` 2.0.0, `a2a-sdk` 1.1.2,
`sentence-transformers` 6.0.0, `ruff` 0.16.3, `pytest` 9.1.1. **One patch bump:** `langchain`
1.3.15 → **1.3.16**. Patch row of Principle 14 — pinned and logged, no new addendum.

**Model pins are now real** (`src/mandala/models.py`), each read from a live `GET /models` roster
and confirmed with one real completion:

| Constant | Provider | Pin |
|---|---|---|
| `WORKHORSE` | Gemini | `gemini-3.7-flash` |
| `FAST_LOOP` | Groq | `openai/gpt-oss-20b` |
| `JUDGE` | OpenRouter | `nvidia/nemotron-3-super-120b-a12b:free` |
| `OFFLINE` | Ollama | *(unset — not installed; optional per plan §2.1)* |

**A `:free` id died inside the hour.** `z-ai/glm-5.2:free` was pinned as `JUDGE`, then returned
`429 upstream_429` from OpenRouter's shared upstream pool on two consecutive attempts and was
replaced. This is the first live evidence for `RATE_BUDGET.md` standing rule 5, and it is exactly
the failure the Day-6 router exists to absorb.

**One documentation fact changed under us.** `ai.google.dev/gemini-api/docs/rate-limits` **no longer
publishes free-tier RPM/RPD/TPM**; it now says limits "can be viewed in Google AI Studio". So the
Gemini row in `RATE_BUDGET.md` cannot be closed from a public source at all — it needs an
authenticated console read. Recorded here because a future freshness run will otherwise re-discover
it and assume the doc is broken.

**Two plan-internal fixes were needed to make Day 1 runnable**, both logged in
`docs/CHANGELOG_PLAN.md` and both overrulable:

1. `ruff` and `pytest` moved from the Day-2 ledger row to **Day 1** — Day 1's own demo command is
   `uv run pytest`, and its closing step is `./m check`, which runs both.
2. `[tool.ruff.format] exclude = ["**/*.md"]` — ruff 0.16 formats Python blocks inside Markdown and
   wanted to rewrite the aligned-comment listings in 30 `LESSON.md` files.

