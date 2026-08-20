# Day 3 — CHECKLIST

**IDs covered:** AG-01 🛠️ (the agent loop), AG-02 🛠️ (tool / function calling)

## Demo command

```bash
cd days/day-03/lab
uv run python demo.py "What severity is ticket T-1001?"
cd ../../..
```

Expected: the printed transcript shows **assistant calls `get_ticket` → tool answers → assistant
replies "high"**. If the severity appears with no tool call in between, the agent hallucinated it.

## Setup

- [ ] `./m start 3` and `./m scaffold 3` run
- [ ] `./m check` was green before you started (Day 2's work still holds)
- [ ] Today's files created (`tools.py`, `naked_agent.py`, `demo.py`, `src/mandala/loop.py`, `tests/test_naked_agent.py`)
- [ ] **No new packages installed** — `openai` from Day 1 is all today needs

## Code

- [ ] `tools.py` — `get_ticket` + `search_tickets`, both **read-only**
- [ ] `TICKETS_PATH` anchored to `__file__`, not to the working directory
- [ ] Tools return an **error dict**, they do not raise
- [ ] Every tool schema has a real `description`, and every argument has one too
- [ ] `get_ticket`'s description contains an explicit **"do NOT use this when…"** line
- [ ] `additionalProperties: False` on both parameter schemas
- [ ] `naked_agent.py` — `SYSTEM_PROMPT` forbids inventing ticket ids/contents
- [ ] The loop appends the **assistant message before** the tool message
- [ ] `exclude_none=True` on `model_dump()`
- [ ] `tool_call_id` copied from the call being answered
- [ ] Tool content is `json.dumps(...)`, a string
- [ ] Loops over **all** of `message.tool_calls`, not just the first
- [ ] Tool dispatch wrapped in `try/except` returning an error value
- [ ] `max_turns` ≤ 6 and exceeding it **raises**
- [ ] Model id imported from `mandala.models` — no string literals
- [ ] `demo.py` prints every turn including tool messages
- [ ] `src/mandala/loop.py` — `run_loop()` takes client/tools/schemas/model as **parameters**

## Watch it break — actually run these

- [ ] Removed `tools=` → observed the model **invent** a ticket
- [ ] Broke `tool_call_id` → observed the 400 / confusion
- [ ] `max_turns=1` → observed the `RuntimeError`
- [ ] (Optional) Gave both tools the same vague description → observed bad tool choice, then fixed it with the negative-guidance line

## Tests that must be able to fail

- [ ] `test_agent_uses_the_tool_rather_than_inventing` — green
- [ ] `test_agent_refuses_unknown_tickets` — **was red first**; went green by fixing the *system prompt*, not the code
- [ ] `test_loop_gives_up_rather_than_spinning` — fake client written by you; no network
- [ ] Cassettes recorded (`-m live`), then the suite replays with **0 requests**
- [ ] `grep -ril "gsk_\|sk-\|AIza" tests/fixtures/cassettes/` prints **nothing**

## ID coverage

- [ ] **AG-01** — the loop exists, is capped, and `demo.py` shows all four beats
- [ ] **AG-02** — two tool schemas written by hand; at least one description rewritten to fix behaviour

## Understanding check — answer out loud

- [ ] Why does the model never execute anything, and why does that matter for security?
- [ ] What breaks if you append the tool message *before* the assistant message?
- [ ] Why does a tool return `{"error": ...}` instead of raising?
- [ ] Why is `search_tickets` deliberately a dumb substring match?
- [ ] What is `exclude_none=True` protecting you from?
- [ ] Why is `message.tool_calls or []` such a common idiom in agent code?

## Budget

- [ ] Actual request count logged in `docs/RATE_BUDGET.md` (declared: ~35, Groq)

## Freshness

- [ ] Checked the live function-calling docs for message-shape drift (§11)
- [ ] Anything that differed is logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 3
```

- [ ] `./m done 3` succeeded — trackers updated automatically
