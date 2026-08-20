# 📌 PINS.md — live-verified version table

> **Verified against PyPI / GitHub Releases on 2026-08-20** by the bulk day-generation pass.
> This file is the *evidence*; `pyproject.toml` is the *enforcement*. They must agree.
> Re-verified every Friday by `/freshness` (Principle 13). Changes are logged in
> `docs/CHANGELOG_PLAN.md`; **material** changes get an addendum first (Principle 14).

## Core stack

| Package | Live version (2026-08-20) | Released | Plan baseline (2026-08-12) | Verdict |
|---|---|---|---|---|
| `openai-agents` | **0.22.0** | 2026-08-19 | "April 2026 release line" | ✅ consistent — pin exact |
| `openai` | **3.3.1** | 2026-08-19 | — | ✅ pin exact |
| `crewai` | **1.15.17** | 2026-08-20 | 1.15.x (1.15.6 seen) | ✅ same minor, newer patch |
| `crewai-tools` | **1.15.17** | 2026-08-20 | 1.15.x | ✅ |
| `langchain` | **1.3.15** | 2026-08-11 | **1.2.x** | ⚠️ **MINOR DRIFT** → see `03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md` |
| `langchain-core` | **1.6.0** | 2026-08-19 | 1.2.x-era core | ⚠️ same drift |
| `langgraph` | **1.2.11** | 2026-08-11 | 1.2.x (1.2.9) | ✅ same minor, newer patch |
| `langsmith` | **0.11.1** | 2026-08-19 | — | ✅ |
| `langchain-google-genai` | **4.3.4** | 2026-08-14 | — | ✅ |
| `langchain-groq` | **1.1.3** | 2026-06-10 | — | ✅ |
| `langchain-openai` | **1.6.0** | 2026-08-19 | — | ✅ (used only for OpenRouter `base_url`) |
| `litellm` | **1.97.0** | 2026-08 | — | ✅ |
| `mcp` (Python SDK) | **2.0.0** | 2026-07-28 | spec 2026-07-28 | ✅ SDK major matches the spec revision |
| `a2a-sdk` | **1.1.2** | 2026-07-22 | A2A v1.0 | ✅ |
| `sentence-transformers` | **6.0.0** | 2026-08-18 | local embeddings | ✅ |

## Spec / protocol

| Spec | Live revision | Plan baseline | Verdict |
|---|---|---|---|
| MCP specification | **2026-07-28** | 2026-07-28 | ✅ unchanged — stateless core still current |
| A2A | **v1.0** (`a2a-sdk` 1.1.2) | v1.0 | ✅ |

## Supporting tools

| Tool | Live version | Note |
|---|---|---|
| `uv` | **0.12.5** (2026-08-14) | environment + workspace manager |
| `ruff` | **0.16.3** (2026-08-13) | lint + format |
| `pytest` | **9.1.1** (2026-06-19) | test runner |
| `ddgs` | **9.15.0** (2026-08-16) | free search backend for OAI-13 |
| `docker` (Python SDK) | **7.2.0** (2026-07-09) | drives the Day-19/67 sandbox |
| `fastapi` | **0.141.1** (2026-07-29) | Day-85 service wrapper |
| `opentelemetry-sdk` | **1.44.0** (2026-07-16) | neutral trace layer (Principle 8) |
| `temporalio` | **1.31.0** (2026-07-29) | Day-20 durable-run lab (self-hosted, free) |
| `chromadb` | **1.5.9** (2026-05-05) | optional; Day 46 prefers a plain numpy index |

## Python

**3.12.** Every package above accepts it (`openai-agents` needs ≥3.10, `crewai` needs
≥3.10,<3.14, LangChain needs ≥3.10). 3.12 remains the safe intersection.

## How to re-verify (copy/paste)

```bash
for p in openai-agents openai crewai crewai-tools langchain langchain-core \
         langgraph langsmith litellm mcp a2a-sdk sentence-transformers; do
  curl -s "https://pypi.org/pypi/$p/json" \
    | python -c "import sys,json;d=json.load(sys.stdin);print('$p', d['info']['version'])"
done
```

> ⚠️ **Model IDs are NOT pinned here.** Free-tier model rosters rotate without notice
> (especially OpenRouter `:free`). Model pins live in `src/mandala/models.py` as named
> constants and are re-checked by `/freshness`. `docs/RATE_BUDGET.md` holds the live limits.
