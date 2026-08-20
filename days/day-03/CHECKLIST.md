# Day 3 — CHECKLIST

**IDs covered:** AG-01 🛠️ (the agent loop), AG-02 🛠️ (tool / function calling)

## Demo command

```bash
uv run python days/day-03/lab/demo.py "What severity is ticket T-1001?"
```

Expected: the printed transcript shows **assistant asks for `get_ticket` → tool answers → assistant
replies "high"**. If the severity appears without a tool call, the agent hallucinated it.

## Definition of done

- [ ] `days/day-03/lab/naked_agent.py` — the loop, typed by hand, no framework imports
- [ ] `days/day-03/lab/tools.py` — `get_ticket` + `search_tickets`, both **read-only**
- [ ] `days/day-03/lab/demo.py` — prints every turn including tool messages
- [ ] `src/mandala/loop.py` — the loop promoted to reusable form (`run(messages, tools, model, max_turns)`)
- [ ] Model id comes from `mandala.models`, never a string literal
- [ ] `max_turns` capped at ≤ 6, and exceeding it raises rather than looping
- [ ] Ran on **Groq**, not Gemini

## The three "watch it break" experiments

- [ ] Removed `tools=` → observed the model **invent** a ticket
- [ ] Broke `tool_call_id` → observed the error / confusion
- [ ] Set `max_turns=1` → observed the `RuntimeError`

## Tests that must be able to fail

- [ ] `test_agent_uses_the_tool_rather_than_inventing` — asserts a real `get_ticket` call happened
- [ ] `test_agent_refuses_unknown_tickets` — **was red first**; went green by fixing the *system prompt*
- [ ] Both cassettes recorded; `make check` passes them offline

## ID coverage

- [ ] **AG-01** — the loop exists, is capped, and `demo.py` shows all four beats
- [ ] **AG-02** — at least one tool schema written by hand; description rewritten at least once to fix behaviour

## Freshness

- [ ] Checked the live function-calling docs for message-shape drift (§8)
- [ ] Anything that differed is logged in `docs/CHANGELOG_PLAN.md`

## Commit

- [ ] Committed — `day-03: AG-01, AG-02 — the naked agent loop with function calling`
- [ ] `LESSON.md` frontmatter: `status: done`, `commit: <sha>`
- [ ] `docs/CURRICULUM_INDEX.md` Day 3 row set to ✅
- [ ] `docs/TRACEABILITY.md` AG-01, AG-02 marked covered
