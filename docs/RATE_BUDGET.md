# ⏱️ RATE_BUDGET.md — the real budget

> **On this project the currency is not dollars. It is requests per minute and requests per day.**
> (Principle 5.) Everything below must be copied from your **live provider consoles** — not from a
> blog post, not from this file's placeholders, not from a model's memory. Free-tier numbers change
> without notice and free model rosters rotate.
>
> **Status: 🔴 EMPTY — fill this on Day 1.** Re-verify every Friday with `/freshness`.

---

## 1. Live limits (fill me)

| Provider | Env var | Model ID you pinned | RPM | RPD | TPM | Verified on | Console URL |
|---|---|---|---|---|---|---|---|
| Gemini (AI Studio) | `GEMINI_API_KEY` | *(e.g. the current free Flash line)* | ? | ? | ? | ⬜ | aistudio.google.com |
| Groq | `GROQ_API_KEY` | *(e.g. a Llama-3.3-70B-class open model)* | ? | ? | ? | ⬜ | console.groq.com |
| OpenRouter | `OPENROUTER_API_KEY` | *(a `:free` model — perishable!)* | ? | ? | ? | ⬜ | openrouter.ai |
| Ollama (optional) | — | *(local model)* | ∞ | ∞ | ∞ | ⬜ | localhost:11434 |
| Embeddings | — | `sentence-transformers` (local) | ∞ | ∞ | ∞ | n/a | local, no API |

**How to verify without burning quota:** send exactly one tiny request per provider and read the
rate-limit response headers (most OpenAI-compatible endpoints return `x-ratelimit-*`). Log the
numbers here. One request each, not a loop.

---

## 2. Standing rules that fall out of these numbers

1. **Judge ≠ judged.** An eval judge (AG-23) always runs on a *different provider* than the agent
   under test. If Gemini triages, OpenRouter judges.
2. **Every model call goes through the shared router** (`src/mandala/router.py`, built Day 6):
   Gemini → Groq → OpenRouter → Ollama, with 429-aware exponential backoff and jitter.
3. **Every lab declares its request budget up front** and logs actual usage. If a lab's declared
   budget exceeds ~10% of your daily RPD on any provider, split the lab.
4. **Groq is for many small calls. Gemini is for few large ones.** Groq's constraint is tokens per
   minute; Gemini's is requests per day. Route by shape, not by preference.
5. **OpenRouter `:free` pins are perishable.** Treat every `:free` model id as best-effort — the
   router must survive it disappearing mid-run.
6. ⚠️ **Gemini free-tier prompts may be used to train Google models.** Fixtures only. Never send
   real customer data, real credentials, or anything you would not publish.

---

## 3. Daily budget ledger (optional but recommended)

Append one line per lab day. This is how you notice quota creep before it bites you at 11pm.

| Date | Day | Declared budget | Actual requests | 429s hit | Notes |
|---|---|---|---|---|---|
| | | | | | |

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
