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
| `uv` | **0.12.5** (2026-08-14) | environment manager. Installed on Day 0. |
| `ruff` | **0.16.3** (2026-08-13) | lint + format |
| `pytest` | **9.1.1** (2026-06-19) | test runner |
| `ddgs` | **9.15.0** (2026-08-16) | free search backend for OAI-13 |
| `docker` (Python SDK) | **7.2.0** (2026-07-09) | drives the Day-19/67 sandbox |
| `fastapi` | **0.141.1** (2026-07-29) | Day-85 service wrapper |
| `opentelemetry-sdk` | **1.44.0** (2026-07-16) | neutral trace layer (Principle 8) |
| `temporalio` | **1.31.0** (2026-07-29) | Day-20 durable-run lab (self-hosted, free) |
| `chromadb` | **1.5.9** (2026-05-05) | optional; Day 46 prefers a plain numpy index |

---

## 📆 Dependency ledger — what to `uv add`, and on which day

> `pyproject.toml` starts with `dependencies = []`. Each package is added **on the day it is first
> needed**, with its exact version, so you always know why every dependency exists.
> Copy these lines from the lesson that owns them — they are repeated there.

| Day | Command |
|---|---|
| 1 | `uv add "openai==3.3.1" "python-dotenv==1.2.3"` |
| 2 | `uv add --dev "ruff==0.16.3" "pytest==9.1.1" "pytest-recording==0.13.4" "vcrpy==8.3.0" "pre-commit==4.6.2"` |
| 4 | `uv add "pydantic==2.13.4"` |
| 6 | `uv add "tenacity==9.1.4"` |
| 9 | `uv add "openai-agents[litellm]==0.22.0"` |
| 17 | `uv add "rich==15.0.0"` |
| 19 | `uv add "docker==7.2.0"` *(and install Docker Desktop)* |
| 20 | `uv add "temporalio==1.31.0"` |
| 23 | `uv add "crewai==1.15.17" "crewai-tools==1.15.17"` |
| 36 | `uv add "langchain==1.3.15" "langchain-core==1.6.0" "langchain-google-genai==4.3.4" "langchain-groq==1.1.3" "langchain-openai==1.6.0"` |
| 41 | `uv add "deepagents==0.7.7"` |
| 43 | `uv add "langgraph==1.2.11"` |
| 46 | `uv add "sentence-transformers==6.0.0" "numpy==2.5.2"` |
| 47 | `uv add "langgraph-checkpoint-sqlite==3.1.1"` |
| 53 | `uv add "mcp==2.0.0" "httpx==0.28.1"` |
| 68 | `uv add "playwright==1.62.0"` |
| 73 | `uv add "langsmith==0.11.1"` |
| 75 | `uv add "opentelemetry-sdk==1.44.0" "opentelemetry-exporter-otlp==1.44.0"` |
| 85 | `uv add "fastapi==0.141.1" "uvicorn==0.52.4"` |
| 87 | `uv add "a2a-sdk==1.1.2"` |

⚠️ **Verify each version on the day you add it.** These were live on 2026-08-20; a patch bump is
routine (pin the new patch, log one line). A **minor or major** bump means: stop, read the release
notes, write an addendum — *then* pin. That is Principle 14.

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
