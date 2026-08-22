# ⏱️ RATE_BUDGET.md — the real budget

> **On this project the currency is not dollars. It is requests per minute and requests per day.**
> (Principle 5.) Everything below must be copied from your **live provider consoles** — not from a
> blog post, not from this file's placeholders, not from a model's memory. Free-tier numbers change
> without notice and free model rosters rotate.
>
> **Status: 🟡 PARTIAL — filled on Day 1 (2026-08-20).** Groq and OpenRouter are recorded;
> Gemini's free-tier numbers are **console-only** and still need one manual read (see §1a).
> Re-verify every Friday with `/freshness`.

---

## 1. Live limits — verified 2026-08-20

| Provider | Env var | Model ID you pinned | RPM | RPD | TPM | Verified on | Console URL |
|---|---|---|---|---|---|---|---|
| Gemini (AI Studio) | `GEMINI_API_KEY` | `gemini-3.7-flash` | ⬜ *(console)* | ⬜ *(console)* | ⬜ *(console)* | 2026-08-20 — key + model **live-verified**, limits **not yet read** | aistudio.google.com/rate-limit |
| Groq | `GROQ_API_KEY` | `openai/gpt-oss-20b` | *(not in headers)* | **1000** | **8000** | 2026-08-20 ✅ from `x-ratelimit-*` headers | console.groq.com/settings/limits |
| OpenRouter | `OPENROUTER_API_KEY` | `nvidia/nemotron-3-super-120b-a12b:free` | **20** | **50** | *(not published)* | 2026-08-20 ✅ docs + `GET /v1/key` (`is_free_tier: true`, `usage: 0`) | openrouter.ai/settings/credits |
| Ollama (optional) | — | *(not installed)* | ∞ | ∞ | ∞ | 2026-08-20 — `localhost:11434` not answering; optional per plan §2.1 | localhost:11434 |
| Embeddings | — | `sentence-transformers` (local) | ∞ | ∞ | ∞ | n/a | local, no API |

**Evidence.**

- **Groq** returns real numbers on every completion. Captured on 2026-08-20 for `openai/gpt-oss-20b`:
  `x-ratelimit-limit-requests: 1000`, `x-ratelimit-limit-tokens: 8000`,
  `x-ratelimit-reset-requests: 4m19.2s`. RPM is *not* in the headers — read it from the console.
  **8000 TPM is the binding constraint**, not the request count: one 8k-token prompt exhausts a
  whole minute. Route few-large-context work to Gemini (rule 4 below).
- **OpenRouter** `:free` variants: **20 RPM** and **50 RPD** while the account has never purchased
  $10 of credits (1000 RPD after). `GET /api/v1/key` on 2026-08-20 returned `is_free_tier: true`,
  `usage: 0` → **50 RPD applies.** No `x-ratelimit-*` headers are returned on completions.
- **Gemini** returns no `x-ratelimit-*` headers, and Google **no longer publishes free-tier numbers
  in the public docs** — `ai.google.dev/gemini-api/docs/rate-limits` now says limits "can be viewed
  in Google AI Studio". See §1a.

### 1a. ⬜ Outstanding — one manual read

Open **https://aistudio.google.com/rate-limit**, find the row for `gemini-3.7-flash`, and write the
RPM / RPD / TPM into the Gemini row above. This is the one number on this page that cannot be
fetched programmatically without the console session.

### 1b. Notes on the pinned models

- `openai/gpt-oss-20b` (Groq) is a **reasoning** model: at `max_tokens=5` it spends the whole budget
  thinking and returns `content=''`. Give it headroom, or check `reasoning` before trusting an empty
  reply. Day 1's `verify_keys.py` output shows exactly this (`groq ok reply=''`).
- `nvidia/nemotron-3-super-120b-a12b:free` also emits reasoning into `content` when truncated.
- **`z-ai/glm-5.2:free` was the first JUDGE pick and was dropped the same day** — it returned
  `429 upstream_429` from OpenRouter's shared pool on two consecutive tries. A textbook
  demonstration of standing rule 5: a `:free` id is best-effort, not a guarantee.

---

## 2. Standing rules that fall out of these numbers

1. **Judge ≠ judged.** An eval judge (AG-23) always runs on a *different provider* than the agent
   under test. If Gemini triages, OpenRouter judges.
2. **Every model call goes through the shared router** (`src/mandala/router.py`, built Day 6):
   Gemini → Groq → OpenRouter → Ollama, with 429-aware exponential backoff and jitter.
3. **Every lab declares its request budget up front** and logs actual usage. If a lab's declared
   budget exceeds ~10% of your daily RPD on any provider, split the lab. With the numbers verified
   on 2026-08-20 that threshold is **5 requests on OpenRouter** (50 RPD) and **100 on Groq**
   (1000 RPD). OpenRouter is the scarce one by two orders of magnitude — which is why it is the
   *judge*, called once per eval case, and never the loop.
4. **Groq is for many small calls. Gemini is for few large ones.** Groq's binding constraint is
   **8000 tokens per minute**, not its 1000 requests per day: a single 8k-token prompt spends a
   whole minute of budget, while 100 short tool-calling turns barely register. Gemini's constraint
   is requests per day. Route by *shape* — many-small to Groq, few-large to Gemini — not by
   preference.
5. **OpenRouter `:free` pins are perishable.** Treat every `:free` model id as best-effort — the
   router must survive it disappearing mid-run.
6. ⚠️ **Gemini free-tier prompts may be used to train Google models.** Fixtures only. Never send
   real customer data, real credentials, or anything you would not publish.
7. **An empty `content` is not a failure.** Both `openai/gpt-oss-20b` (Groq) and
   `nvidia/nemotron-3-super-120b-a12b:free` (OpenRouter) are reasoning models: give them a
   `max_tokens` too small and the whole budget goes to reasoning, leaving `content=''` and a
   `finish_reason` of `length`. Check `finish_reason` before concluding the call broke — Day 1
   saw exactly this (`groq ok reply=''`).

---

## 3. Daily budget ledger (optional but recommended)

Append one line per lab day. This is how you notice quota creep before it bites you at 11pm.

| Date | Day | Declared budget | Actual requests | 429s hit | Notes |
|---|---|---|---|---|---|
| 2026-08-20 | 1 | 3 (one per provider) | **9** — Gemini 2, Groq 4, OpenRouter 5 | 2 (both `z-ai/glm-5.2:free`, upstream shared pool) | Over the declared 3 because the first JUDGE pin was dead and had to be re-chosen: 3 candidate probes on OpenRouter, 1 extra Groq call to capture the `x-ratelimit-*` headers, plus one clean re-run of `verify_keys.py`. Roster listing (`GET /models`) is free and not counted. |

---

## 4. Escalation ladder when you run out mid-lab

1. **Wait.** RPM limits reset in ~60s. Most 429s are minute-scoped, not day-scoped.
2. **Fall to the next provider** — that's what the router is for. Note in the ledger which
   provider actually answered; that fact is also a trace field (AG-26).
3. **Switch to cassettes.** Every lab from Day 4 onward records real responses to
   `tests/fixtures/cassettes/` so tests replay offline at zero cost. Re-run against cassettes.
4. **Fall to Ollama.** Lower quality, unlimited. Fine for "does the wiring work" checks;
   not fine for eval scoring.
5. **Stop and finish tomorrow.** A day that burned its quota still produced a commit if you
   committed the code and the cassette. That counts (Principle 1).
