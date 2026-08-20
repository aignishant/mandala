---
day: 19
phase: 3
phase_name: "OpenAI Agents SDK advanced"
title: "The harness, the sandbox, and the Docker box you build yourself"
ids: ["OAI-18", "OAI-19", "OAI-20"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 19 — The harness, the sandbox, and the Docker box you build yourself

**Phase 3 · OpenAI Agents SDK advanced** · IDs: **OAI-18 🅿️**, **OAI-19 🛠️**, **OAI-20 🅿️**

> **Yesterday:** programmatic tool calling 🅿️ — the paid feature where the model writes a program
> that calls your tools — and the free coordinator function tool that got you the same round-trip
> economics for $0.
> **Today:** the other half of that idea. Yesterday you bounded what a plan may *do*; today you bound
> **where code may run**. The paid model-native harness 🅿️ read carefully (OAI-18), the public
> roadmap tracked honestly (OAI-20), and then the day's real work: a **local Docker sandbox** you
> build yourself, with no network, a read-only mount, and a hard timeout (OAI-19 🛠️).
> **Tomorrow:** durable runs with Temporal, plus realtime awareness — what happens when the process
> that owns your agent loop dies mid-job (OAI-21/22).

```bash
./m start 19
./m scaffold 19
```

---

## §1 The story

Yesterday's coordinator was safe for one reason, and it was not cleverness: **it could not execute
anything you had not already written.** Five operations, typed arguments, `isinstance` dispatch. The
model chose *among* your verbs; it never invented one.

That ceiling is real. Ask the coordinator "how many ERROR lines in `app.log` came from the same
tenant within a 5-minute window" and it cannot answer, because you never wrote a `window_join`
operation and you never will — there is an infinite supply of questions like that. The only tool that
answers all of them is the one you have been carefully avoiding for eighteen days:

> **Let the model write actual code, and run it.**

Everybody's instinct here is correct: this is the most dangerous thing an agent can do. Generated
code is not a tool call with a schema in front of it. It is arbitrary control flow, written by a
model that may be reading attacker-influenced text (Day 15), executing on a machine with your SSH
keys, your `.env`, your git history, and a network route to everything you can reach.

So the discipline of the day is not "be careful". It is **build the room before you open the door**:

> **You do not make generated code safe. You make the place it runs cheap to lose.** No network, no
> credentials, one read-only file, a wall clock that kills it, and a container that is destroyed
> whether or not the code finished. Then "the model wrote a `rm -rf /`" is a boring log line.

OpenAI shipped exactly this idea in the **April 2026 release line** as a paid, model-native feature:
a **harness** (Codex-like filesystem tools, configurable memory, sandbox-aware orchestration for
long-horizon file work) with **native sandbox execution** underneath it. That is **OAI-18**, and it
is 🅿️ paid-only — you will read it, not run it, and §3 makes sure you can describe it well enough
that an interviewer believes you have thought about it. **OAI-20** is the roadmap sitting behind it
(code mode, subagents, Python-first with TypeScript later) — a *freshness-check* item, not a thing to
build on.

**OAI-19 is the build**, and it is the honest one: the guarantee the paid sandbox sells you is not
magic, it is six flags on a container, and you can have all six for $0 with Docker on your laptop.
By the end of today you will have a function tool that runs model-written Python in a throwaway
container, and — more importantly — **a battery of six attacks that prove it refuses them**, printed
as a pass/fail table you record in the CHECKLIST.

Two things to hold in your head while you build:

1. **This is a Principle-6 day end to end.** Every design decision today is "name what it can
   destroy, then shrink that". You have been writing `blast_radius` sentences since Day 8; today one
   of them has to be true against a hostile input.
2. **A container is not a virtual machine.** §4.8 is not a disclaimer paragraph you skim — it is the
   difference between an engineer who can be trusted with this and one who cannot. Day 67 (AG-18)
   revisits the same ground with microVMs and will hold you to what you say today.

There is one prerequisite that is not code: **Docker Desktop must be installed and running.** §2
checks it in one command, and if it is not there, §2.3 tells you exactly which two-thirds of today
you can still do — being blocked on a daemon must not cost you a day (Principle 1).

---

## §2 Setup — run this

### 2.1 The package

```bash
uv add "docker==7.2.0"
```

> **New dependency, and the ledger already knows.** `docs/PINS.md` has the Day-19 row —
> `uv add "docker==7.2.0"` *(and install Docker Desktop)* — verified live on 2026-08-20 (released
> 2026-07-09). This is the Python SDK that talks to the local Docker daemon over its socket; it is
> not Docker itself. If `uv add` resolves to something else, pin what you got and log one line
> (Principle 4).

`docker` 7.2.0 is also the package **Day 67 (AG-18)** uses when it redoes this lab with harder
isolation, so it earns its place in `pyproject.toml` twice.

### 2.2 The pre-flight — do this before you write a line

Three commands. Run all three; each one fails differently and the difference is the diagnosis.

```bash
docker version                      # 1. is there a daemon, and can I talk to it?
docker run --rm hello-world         # 2. can I actually start a container?
docker pull python:3.12-slim        # 3. pull today's base image before you need it
```

```bash
uv run python -c "import docker; print(docker.from_env().version()['Version'])"
```

**Line by line:**

- `docker version` prints a **Client** block and a **Server** block. Client-only means the CLI is
  installed but the daemon is not running — start Docker Desktop and wait for the whale to settle.
  This is the single most common way to lose twenty minutes today.
- `docker run --rm hello-world` is the real test, because it exercises the whole path: pull, create,
  start, capture output, remove. If `docker version` is happy and this is not, the problem is
  permissions on the socket or a disk/VM issue, not installation. `--rm` is a preview of today's
  central habit — **the container is garbage the moment it stops.**
- `docker pull python:3.12-slim` **now**, on purpose. The first `run_in_sandbox()` call would
  otherwise block for a minute pulling ~50 MB while you assume your timeout logic is broken. Pull
  once, debug clean.
- The last line proves the *Python* SDK can reach the daemon, which is a different question from
  whether the *CLI* can. `docker.from_env()` reads `DOCKER_HOST`; on Windows with Docker Desktop it
  finds the npipe, on Linux the unix socket. If the CLI works and this raises `DockerException`, you
  have a `DOCKER_HOST` / context mismatch — `docker context ls` is the next command.

Then resolve the image to a **digest**, because §4.3 asks you to pin one:

```bash
docker inspect --format='{{index .RepoDigests 0}}' python:3.12-slim
```

> **`:latest` is a Principle-4 violation, and `:3.12-slim` is a smaller one.** A tag is a mutable
> pointer. `python:3.12-slim` is rebuilt regularly — new patch Python, new libc, new CVE set — so a
> sandbox test that passed in CI last week can fail today with no commit in between, and worse, the
> *inverse*: a test that passes today can be running a different kernel-facing userland tomorrow.
> Pin `python@sha256:...` and the box is byte-identical every time. It is the same rule as
> `model=` on every agent (Day 9): **nothing floats.**

### 2.3 If Docker is not available — what today still is

**Do not skip the day.** Docker is required for exactly one of today's three IDs, and even that one
is two-thirds testable without it. Here is the honest split:

| Today's work | Needs Docker? | If you have no Docker |
|---|---|---|
| §3 OAI-18 🅿️ — the harness, read and understood | no | **do it in full** |
| §3.4 the gate explainer (`docs/explainers/paid-harness-and-sandbox.md`) | no | **do it in full — this is a Phase-3 gate artifact** |
| §3.5 OAI-20 🅿️ — roadmap literacy | no | **do it in full** |
| §4.3 `src/mandala/sandbox.py` — `container_kwargs()`, the pure config half | no | **write it in full** |
| §4.4 the permission-table row for `run_code` | no | **do it in full** |
| §4.3 `run_in_sandbox()` — the half that talks to the daemon | yes | write it; it will raise `SandboxUnavailable` |
| §4.6 `escape_attempts.py` — the six-attack battery | **yes** | write it, run it later, leave the CHECKLIST blanks empty |
| §5 the config tests (every guarantee, one test each) | no | **run them — they are the majority of the suite** |
| §5 the two `@pytest.mark.docker` tests | yes | they **skip**, and the suite stays green |

That table is not a consolation prize; it is the design working. **The reason most of today survives
a missing daemon is that §4.3 puts every safety guarantee into a pure function that returns a dict**
— `container_kwargs()` — and lets `run_in_sandbox()` be a thin, boring caller. Yesterday's coordinator
was testable at 0 requests because its security lived in a Pydantic model; today's sandbox is
testable at 0 *containers* for exactly the same reason. That is not an accident twice; it is the
pattern: **put the guarantee somewhere a test can read it without performing it.**

Get Docker Desktop installed tonight either way, and run the battery before the Day-22 gate — the
gate says *"a long-horizon file-touching agent runs on free models inside the local Docker sandbox"*,
and there is no version of that sentence without a daemon.

### 2.4 The files

```bash
mkdir -p days/day-19/lab data/logs docs/explainers
touch src/mandala/sandbox.py
touch days/day-19/lab/sandbox_demo.py
touch days/day-19/lab/escape_attempts.py
touch tests/test_sandbox.py
```

**Write `data/logs/app.log` yourself** — 40-ish lines of plausible application log, in the shape your
own systems produce. Something like:

```
2026-08-19T09:14:02Z INFO  tenant=acme   request=r-8831 msg="triage ok" ms=142
2026-08-19T09:14:07Z ERROR tenant=acme   request=r-8832 msg="upstream timeout" ms=30011
2026-08-19T09:15:41Z WARN  tenant=globex request=r-8833 msg="retry 1/3" ms=88
2026-08-19T09:16:03Z ERROR tenant=globex request=r-8834 msg="upstream timeout" ms=30004
```

Vary the levels, the tenants and the hours so that "count ERRORs per hour" and "which tenant is
worst" have non-trivial answers. It is a **fixture**, exactly like `tests/fixtures/tickets.json`
(Day 2) and `data/kb/*.md` (Day 15), and for the same reason: **nothing real ever enters this
project.** `data/` is committed; `.mandala/` is not (Day 14).

Finally, confirm the two things today stands on are green before you start:

```bash
uv run pytest tests/test_permissions.py tests/test_coordinator.py -q
```

Day 8's permission table is the boundary today's new capability has to be added to *correctly*, and
Day 18's coordinator is the design you are about to deliberately step outside of. **If either is
red, fix that first.**

---

## §3 OAI-18 🅿️ — the model-native harness, read not run

### 3.1 The SDK grew opinions about three things

Up to now the Agents SDK has been deliberately thin: an agent, a loop, tools, guardrails, handoffs.
Everything *around* the loop was yours. The April 2026 release line changes that, and the honest way
to describe it is not "they added a sandbox" — it is:

> **The SDK grew opinions about the three things every long-horizon agent needs, and shipped one
> answer for each.** A filesystem it can read and write. A memory that survives the context window.
> An execution environment that is safe to be wrong in.

Take them one at a time, and for each one, name what you would otherwise have to build. That last
column is the reason this section exists — it is the difference between "I read the announcement"
and "I know what it replaces".

| The thing an agent needs | What the harness ships 🅿️ | What you build yourself if you don't have it |
|---|---|---|
| **A filesystem** | Codex-like file tools — read, write, patch, list — the model treats a workspace as durable state instead of stuffing everything into the prompt | function tools over a **rooted, normalised path** with traversal checks, an extension allowlist, a size cap per read, and an audit line per write. Day 15's `kb.py` is the read half; you do not have the write half, and the write half is where the bugs live |
| **A memory** | configurable memory the runtime manages across a long run — what to carry forward, what to summarise, what to drop | Day 12's `MemoryStore` plus `session.py`, plus a summarisation policy, plus a decision about what a turn is worth keeping. You have built this. It took a day and it is not as good |
| **An execution environment** | native sandbox execution — generated code runs in an isolated box the platform operates | **§4.** A container, six flags, a host-enforced timeout, guaranteed teardown, and a battery of tests that proves each one |
| **Orchestration that knows about all three** | sandbox-aware, long-horizon runs: the loop understands that work spans many turns and a filesystem persists between them | your own driver: a loop cap (Day 10), a context budget (Day 4), a trace (Day 14), and a resume story — which is **tomorrow's** problem (Temporal, Day 20) |

Read the fourth row twice. **The integration is the product.** Any one of those three you can
approximate in an afternoon; what you cannot approximate cheaply is a loop that knows the filesystem
survives between turns, that memory is being compacted underneath it, and that the code it just
wrote runs somewhere it is allowed to fail. That is what "harness" means, and it is why the word
exists separately from "sandbox".

### 3.2 The shape of it 🅿️

You cannot run any of this — it needs a paid OpenAI key and OpenAI-hosted infrastructure, and this
project has neither, today or on Day 90 (Principle 5). So read the shape the way you read a spec:

```python
# PAID — OpenAI-hosted harness/sandbox surface. Reproduced for STUDY ONLY.
# The exact class and field names in 0.22.0 must be READ from the live docs (see §8);
# this is the SHAPE of the idea, and shapes are what interviews ask about.
agent = Agent(
    name="LongHorizonWorker",
    model="<a paid OpenAI model>",
    tools=[
        # 1. the filesystem the model may treat as durable
        <FilesystemTool>(workspace="/workspace", writable=True),
        # 2. the box the generated code runs in — operated by them, not by you
        <SandboxTool>(image=..., network=..., timeout=...),
    ],
    # 3. what survives when the context window does not
    memory=<MemoryConfig>(strategy=..., max_tokens=...),
)
```

**Line by line:**

- The angle-bracket placeholders are **deliberate, and keep them that way in your notes.** Writing
  down a confident `CodeInterpreterTool(...)` you have never imported is how you end up saying a
  wrong class name out loud in an interview. §8 gives you the doc pages; fill the names in from
  those, and label them "read, not run".
- Notice the **workspace is a parameter, not a fact**. That is the whole filesystem story: the model
  gets a rooted directory, and everything about safety is *which* directory and whether `writable` is
  true. Your §4 mount is the same decision, spelled `mode="ro"`.
- Notice the sandbox tool takes **image, network and timeout** — the same three knobs you are about
  to set on a container. **This is the part worth internalising: the paid feature is not a different
  category of thing. It is these knobs, operated by someone else, at higher quality.**
- Notice `memory=` is configuration, not a tool. The runtime compacts on your behalf between turns.
  Your Day-12 `MemoryStore` is a tool the agent *calls*; theirs is a policy the loop *applies*. **A
  policy the loop applies is strictly better**, because it cannot be forgotten by a model having a
  bad turn — the same argument Day 12 made for guardrails over prompt instructions.
- Notice what is *absent*, same as yesterday's paid feature: **any hook where you inspect the
  generated code before it executes.** The model writes it, their box runs it, you read the result.
  Whatever you think of that, it is a fact about the design, and §3.3 gives it a row.

> ⚠️ **Everything in §3 is read, not verified.** That is precisely what 🅿️ means in this plan. The
> plan's Part 2 describes the April 2026 line as native sandbox execution plus a model-native harness
> — "Codex-like filesystem tools, configurable memory, long-horizon runs" — and notes it is
> **Python-first, TS later**. If the live docs for `openai-agents` **0.22.0** name these things
> differently, or the feature has moved out of preview, that is a Part-2/Part-4 matrix fact: **one
> line in `docs/CHANGELOG_PLAN.md` today** (Principle 14), before you forget which version you
> believed. Do not silently adapt the lesson.

### 3.3 The comparison — theirs, versus the box you are about to build

This is the table the interview is actually about. Come back and re-read it after §4, and notice that
**three rows go to them, and one of those three is not close.**

| | Paid harness + native sandbox 🅿️ | Your Docker box 🛠️ (§4) |
|---|---|---|
| Isolation boundary | operated isolation, hardened by a team whose job it is | **a Linux namespace plus a cgroup, on your laptop.** Shared kernel |
| Who runs the daemon | them | **you.** It is a service on your machine, with a socket |
| Network | policy-configured, off by default | `network_disabled=True` — off. No policy, no exceptions |
| Filesystem the model sees | a managed workspace that **persists across turns** | one directory mounted `ro`, plus a `tmpfs` that dies with the box |
| Memory across a long run | **runtime-managed, configurable** | Day 12's `MemoryStore`, called explicitly, by an agent that may forget |
| Timeout | theirs, enforced platform-side | **yours, enforced host-side** — and the enforcement is the interesting part (§4.3) |
| Teardown | theirs | `finally: container.remove(force=True)`, plus a labelled orphan sweep |
| Credentials inside the box | none by construction | **none because you wrote `environment={}` and then tested it.** One line away from catastrophic |
| Multi-turn file work | first-class: the loop knows the workspace survives | you would have to build it; durability starts tomorrow (Day 20) |
| Start-up cost per call | amortised, warm | ~0.5–2 s cold container start, every single call |
| Reviewability of the generated code | none exposed | **none either — but you hold the string.** Log it, cap it, diff it, refuse it |
| Cost | paid key, metered | **$0** |

**What the paid version genuinely does better** — say all three out loud, because conceding them is
what makes the rest of your answer credible:

1. **The isolation is stronger than a container, and it is not close.** A platform running untrusted
   code for many tenants can put a hypervisor boundary and a hardened, per-tenant kernel underneath
   it, because that *is* the product. You have namespaces and cgroups over a **shared kernel**. §4.8
   is the long version. This is the row where "I built the free version" becomes a lie if you skip
   the sentence.
2. **Memory and the filesystem persist across a long-horizon run, and the loop knows it.** Your
   container is *destroyed on purpose* — which is simultaneously the safety property and the reason a
   twenty-turn refactoring job cannot live in it. Every call starts from nothing.
3. **Somebody else operates it.** No daemon to keep running, no image to re-pull, no disk quietly
   filling with dead containers, no "works on my laptop, fails in CI".

And the two things yours does better, which are not consolation prizes:

> **You can see the code before it runs, and you can prove the box refuses things.** The generated
> program passes through *your* Python as a string on its way in — you can log it, length-cap it,
> refuse it, or put it in an audit line. And because the configuration is a dict your own code built,
> §5 asserts every guarantee without starting anything. **A safety property you can test is worth
> more than a safety property you were told about.**

**And why we cannot simply run theirs — the mechanism, not a preference.** The harness and its native
sandbox are OpenAI-hosted, metered infrastructure reached through a paid key. We reach models through
`LitellmModel` (Day 9) pointed at Groq / Gemini / OpenRouter, which are OpenAI-*compatible on the chat
surface*: a compatible chat endpoint gets you tokens, not infrastructure. And Principle 5 is a project
invariant, not a budget mood — there is no paid key on Day 19 and there will not be one on Day 90. So
OAI-18 is **read, not run**, and the useful realisation is yesterday's again: **the guarantee was
never the paid part.**

### 3.4 🎯 The gate artifact — write the explainer yourself

The **Phase-3 gate (Day 22)** has two halves, and one of them is not code:

> *"A long-horizon file-touching agent runs on free models inside the local Docker sandbox, **plus a
> one-page written explainer of the paid harness/sandbox good enough to give in an interview.**"*

Today is when that page gets drafted, while §3 is fresh. **Create it yourself:**

```bash
$EDITOR docs/explainers/paid-harness-and-sandbox.md
```

**It must be in your words.** I am deliberately not writing it for you, and that is not laziness on
my part or busywork on yours — it is the entire point of the artifact. A gate item is evidence that
*you* can produce the explanation under pressure. An explainer you pasted reads exactly like an
explainer you pasted, and the first follow-up question exposes it. Principle 9: **every phase ends
with a written decision record you could defend to a hiring panel.**

Use these headings, and make sure the page answers the question under each one. One page. If it runs
past two, you are transcribing docs instead of explaining.

| Heading | The question it must answer |
|---|---|
| **What it is, in three sentences** | Filesystem, memory, execution environment — plus the orchestration that knows about all three. Can you say it without the word "basically"? |
| **The problem it solves** | Why does a *long-horizon* run need this and a triage agent does not? What breaks at turn 30 that was fine at turn 3? |
| **What it replaces on my side** | Name your own code: `kb.py`'s rooted reads, `MemoryStore`, `sandbox.py`. Be specific — this paragraph is where your project becomes the evidence |
| **Why I couldn't run it** | Paid Responses-side infrastructure + Principle 5. State the mechanism, not the preference (§3.6 gives you the exact wording) |
| **What I built instead, and what it does not give me** | The Docker box, the six guarantees, and §3.3's three concessions. **If this section has no concessions it is marketing** |
| **The number** | One measured fact from §4.6. "Six escape attempts, six refusals, one control case that succeeded" beats a paragraph of adjectives |
| **What I would change on a paid team** | Would you buy it? Under what conditions? A person who cannot answer this has not really compared |
| **Freshness** | Version and date you read the docs, and the roadmap items you are tracking (§3.5). A dated claim ages honestly; an undated one just rots |

Two rules for the page itself:

- **Every 🅿️ claim must say it is read, not run.** "According to the 0.22.0 docs, read on 2026-08-20"
  is a stronger sentence than a confident assertion, not a weaker one, and an interviewer who knows
  the product will notice which one you chose.
- **Every 🛠️ claim must point at a file or a test.** "No credentials reach the container" is an
  opinion; "`test_no_host_environment_is_forwarded` asserts the env dict is a fixed three-key literal"
  is a fact.

Tick the CHECKLIST box when the file exists and you have read it aloud once. Reading it aloud is the
test — the sentences you stumble over are the ones you have not understood yet.

### 3.5 OAI-20 🅿️ — roadmap literacy: code mode and subagents

The plan's OAI-20 row is four words long and it is deliberately the smallest item in Phase 3:

> *"Publicly announced directions; Python-first, TS later. **Freshness-check item, not a lab.**"*

Two directions are publicly signposted:

- **Code mode** — the agent expresses work as code rather than as a sequence of tool calls. Yesterday
  you built the free half of exactly this argument (a plan, not a program) and today you built the
  place code would run. If code mode lands, **your `run_code` tool is the thing it generalises.**
- **Subagents** — a first-class way for an agent to spawn a scoped child. You already have the manual
  version: Day 13's handoffs and Day 14's supervisor topology, with `topologies.py` holding both.

**The discipline is the lesson, not the features.** Here is the rule, and it is Principle 13 with
teeth:

> **Track a roadmap; never design against it.** A roadmap tells you which of your own abstractions
> are likely to be *replaced*, so you keep the seam clean and the surface small. It does not tell you
> to leave a hole shaped like a feature that does not exist.

What that means concretely, this week:

| Do | Do not |
|---|---|
| Add "code mode / subagents status" to the Friday `/freshness` checklist | Add a `CodeModeAdapter` base class today |
| Keep `run_code` behind one narrow function-tool signature, so swapping the executor is one file | Design a plugin registry for "future execution backends" |
| Note the Python-first / TS-later ordering, because it predicts *when* a TS shop can adopt it | Assume the Python API shape will survive contact with the TS port |
| Record the date you checked, in the explainer | Say "coming soon" in an interview without a date |

**Why the "Python-first, TS later" detail is worth carrying:** it is a specific, checkable fact that
separates someone who read the announcement from someone who tracks the product — and it has a real
consequence, because a TypeScript shop cannot plan around the harness on the same timeline a Python
shop can. Add one line to your Friday freshness pass:

```
- [ ] OAI-20: code mode / subagents — status changed? (checked: YYYY-MM-DD, still roadmap / shipped)
```

If it ever flips to "shipped", that is not a code change — it is an **addendum first, code second**
(Principle 14), exactly like the `langchain` 1.3.x drift already logged in
`docs/03_MASTER_PLAN_ADDENDUM_FRESHNESS_2026-08-20.md`.

---

## §4 OAI-19 🛠️ — the $0 sandbox: build the room, then open the door

### 4.1 The guarantee, written down before any code

Every safety property today is a sentence you can point at a line for. Write these eight down first;
§4.3 implements them in this order, and §5 has a test per row. **If you cannot name the flag, you do
not have the guarantee** — you have a hope.

| # | The guarantee | The flag that provides it | What it stops |
|---|---|---|---|
| 1 | **No network. At all.** | `network_disabled=True` | exfiltration of anything the code found; a prompt-injected "POST this to my server" |
| 2 | **No credentials** | `environment=` an explicit 3-key literal — never `os.environ` | your Gemini / Groq / OpenRouter keys leaving the machine. **This is the trap of the day** |
| 3 | **One directory, read-only** | `volumes={host: {"bind": "/data", "mode": "ro"}}` | the code editing the evidence it was asked to analyse |
| 4 | **Nothing else writable** | `read_only=True` + a small `tmpfs` for `/tmp` | persistence, dropped payloads, a poisoned image layer |
| 5 | **A hard wall clock** | host-side deadline + `container.kill()` | infinite loops, sleeps, and anything that hopes you will wait |
| 6 | **Bounded CPU / memory / processes** | `nano_cpus`, `mem_limit`, `pids_limit` | a fork bomb taking the laptop instead of the container |
| 7 | **No privileges to escalate** | `user="nobody"`, `cap_drop=["ALL"]`, `security_opt=["no-new-privileges"]` | the easy half of container escapes |
| 8 | **It dies either way** | `finally: container.remove(force=True)` + a labelled sweep | a graveyard of containers holding your disk and your mounts |

And one more that is not a container flag at all, because the danger is on the way *back*:

> **9. The output is truncated before it re-enters the model's context.** Day 4's budget, Day 15's
> bounded ingestion. Generated code can `print("A" * 10_000_000)`, and a sandbox that faithfully
> returns ten megabytes into a context window has been used as a denial-of-service against *you*.

### 4.2 The rules of a code-execution tool 🎯

Yesterday's coordinator earned its safety structurally: an allowlist meant the dangerous thing was
*unrepresentable*. Today you are giving that up on purpose, so the safety has to come from somewhere
else. Be precise about where:

> **A code sandbox has no allowlist. Its entire safety budget is spent on the environment, and the
> environment is configuration — which means a one-line diff can remove a guarantee silently.** That
> is why §5 is a test per flag and not a test per feature.

Five rules, each implemented in §4.3 and asserted in §5:

1. **The container never sees the host environment.** Not filtered, not "the safe subset" —
   `environment={...}` is a literal dict of exactly three values you typed. Passing `os.environ`
   through, or `{**os.environ, "FOO": "bar"}`, hands your free-tier keys to model-written code and
   makes every other line of today pointless.
2. **Deny by default at every axis.** No network, no capabilities, no writable filesystem, no root.
   Then add back the single thing the job needs — one read-only mount — and nothing else. A sandbox
   built by *removing* dangers from a permissive base is a list you must keep complete forever
   (Day 18's allowlist-vs-denylist argument, now about a machine instead of a schema).
3. **The timeout is enforced by the host, not requested of the container.** A `signal.alarm` inside
   the generated code is enforced by the code's goodwill, which is exactly the thing you do not have.
   The host sets a deadline, and when it passes the host sends **SIGKILL** — `container.kill()`, not
   `container.stop()`, because `stop()` sends SIGTERM and then *waits politely* for something that
   has already demonstrated it will not stop.
4. **Teardown is in a `finally`, and it is `force=True`.** Every exit path — success, exception,
   timeout, `KeyboardInterrupt` — removes the container. Anything else and your laptop accumulates
   dead boxes, each one still holding a bind mount.
5. **The tool is granted to nobody by default.** §4.4 adds `run_code` to the permission table and
   gives it to **no existing agent**. It is a capability you hand out deliberately, per agent, with a
   reason — and **never to the Researcher**, which has read the open web since Day 15.

Rule 5 has a corollary worth its own line, because it is the one people bargain with:

> **Untrusted input plus code execution is not a "risky combination", it is the whole attack.** The
> Researcher reads attacker-controlled text. If it also held `run_code`, an injected instruction
> would be executing code within one turn. The box would contain it — that is the point of the box —
> but do not build the situation where the box is the *only* thing between you and a bad day.

And the honest limit of all five, stated now rather than in a footnote: **a container is a blast
radius reduction, not a proof of safety.** §4.8.

### 4.3 `src/mandala/sandbox.py`

```python
"""Where model-written code is allowed to run, and nowhere else.

OAI-19. The Agents SDK's native sandbox is paid (OAI-18, LESSON §3, Principle 5), so
we build the guarantee instead of renting it: generated Python runs in a throwaway
Docker container with NO network, NO credentials, ONE read-only mount, a hard
host-enforced timeout, and guaranteed teardown.

THE SAFETY IS THE ENVIRONMENT, NOT THE CODE.
--------------------------------------------
There is no allowlist here -- that was yesterday's coordinator (Day 18), and giving
it up is the whole feature. So every defence is a container flag, ranked by how much
each one actually protects you:

  1. network_disabled + a LITERAL environment dict  <- nothing to steal, nowhere to send it
  2. read_only rootfs + one mount, mode="ro"        <- nothing to corrupt, nothing to keep
  3. host deadline -> SIGKILL, teardown in finally  <- it stops, and it dies
  4. mem / pids / cpu caps, nobody, cap_drop ALL    <- bounds the damage of being wrong
  5. output truncated before the model sees it      <- Day 4's budget, on the way back

container_kwargs() is a PURE FUNCTION returning the dict we hand to Docker, so every
guarantee above is assertable in a unit test with no daemon running at all. That is
deliberate: a safety property you can only observe by performing it is a safety
property CI will quietly stop checking.

Blast radius (Principle 6): everything inside a box with no network, no credentials,
a read-only mount and thirty seconds to live -- and nothing outside it. The residual
risk is a KERNEL escape, not a bug in this file. LESSON §4.8 is the honest version;
Day 67 (AG-18) is where we do better than a shared kernel.

Usage
-----
    >>> from mandala.sandbox import SandboxLimits, container_kwargs
    >>> kw = container_kwargs("print(1)", mount=None, limits=SandboxLimits())
    >>> kw["network_disabled"], kw["read_only"], kw["user"]
    (True, True, 'nobody')
    >>> kw["environment"]
    {'HOME': '/tmp'}
"""

from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents import RunContextWrapper, function_tool

from mandala import permissions
from mandala.context import MandalaContext
from mandala.sdk_tools import tool_error

# TODO(me): replace this tag with the digest you resolved in LESSON §2.2:
#     docker inspect --format='{{index .RepoDigests 0}}' python:3.12-slim
# Why this is the rep: a tag is a mutable pointer and a digest is the box. Today's
# escape battery is a security claim about a specific userland; ":3.12-slim" can be
# rebuilt tomorrow and your claim silently becomes about something else. Resolving it
# is one command; deciding how you will KEEP it current (freshness item? renovate?)
# is the actual work, and there is no free answer. Write down the one you chose.
SANDBOX_IMAGE = "python:3.12-slim"

SANDBOX_LABEL = "mandala.sandbox"       # so orphans are findable, see reap_orphans()
SANDBOX_TOOL_NAME = "run_code"          # must equal the permissions.TOOLS key (Day 15)
MOUNT_PATH = "/data"                    # the only path in the box the job did not create
MAX_CODE_CHARS = 4_000
MAX_OUTPUT_CHARS = 4_000
MAX_OUTPUT_LINES = 200


class SandboxUnavailable(RuntimeError):
    """No usable Docker daemon. An honest failure -- never a fallback to local exec."""


@dataclass(frozen=True)
class SandboxLimits:
    """Every number that bounds the box. Frozen, so nothing widens it at runtime."""

    image: str = SANDBOX_IMAGE
    timeout_s: float = 30.0
    mem_limit: str = "256m"
    pids_limit: int = 64
    nano_cpus: int = 500_000_000        # 0.5 of one core
    tmpfs_size: str = "16m"
    max_output_chars: int = MAX_OUTPUT_CHARS


@dataclass(frozen=True)
class SandboxResult:
    """What the host learned. `ok` is about the CODE; the box is fine either way."""

    ok: bool
    exit_code: int | None
    output: str
    truncated: bool
    duration_s: float
    reason: str = ""                    # "" | "timeout" | "nonzero-exit" | "code-too-long"


def container_kwargs(code: str, *, mount: Path | None, limits: SandboxLimits) -> dict[str, Any]:
    """Every guarantee, in one dict. Pure: no daemon, no I/O, fully unit-testable."""
    if len(code) > MAX_CODE_CHARS:
        raise ValueError(f"code is {len(code)} chars; the cap is {MAX_CODE_CHARS}")

    volumes: dict[str, dict[str, str]] = {}
    if mount is not None:
        volumes[str(Path(mount).resolve())] = {"bind": MOUNT_PATH, "mode": "ro"}

    return {
        "image": limits.image,
        "command": ["python", "-I", "-u", "-B", "-c", code],
        # --- 1. nothing to steal, nowhere to send it -------------------------------
        "network_disabled": True,
        "network_mode": "none",          # belt to the braces above -- confirm in §8
        "environment": {"HOME": "/tmp"},  # A LITERAL. Never os.environ, never **os.environ.
        # --- 2. nothing to corrupt, nothing to keep --------------------------------
        "volumes": volumes,              # exactly one entry, and it is mode="ro"
        "read_only": True,               # the ROOT filesystem, not just the mount
        "tmpfs": {"/tmp": f"rw,noexec,nosuid,nodev,size={limits.tmpfs_size}"},
        "working_dir": "/tmp",
        # --- 3. bounded damage ------------------------------------------------------
        "mem_limit": limits.mem_limit,
        "memswap_limit": limits.mem_limit,   # equal, or swap makes mem_limit advisory
        "pids_limit": limits.pids_limit,
        "nano_cpus": limits.nano_cpus,
        # --- 4. no privileges to escalate -------------------------------------------
        "user": "nobody",
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges"],
        "privileged": False,             # stated, not assumed -- see the line-by-line
        # --- 5. bookkeeping ----------------------------------------------------------
        "labels": {SANDBOX_LABEL: "1"},
        "detach": True,                  # we need the object to wait, kill and remove
        "auto_remove": False,            # teardown is ours, in a finally
        "stdin_open": False,
    }


def _client():
    """One place that touches Docker, so one place raises SandboxUnavailable."""
    try:
        import docker                                    # local import: docker is optional at import time

        client = docker.from_env()
        client.ping()
    except Exception as exc:                             # noqa: BLE001 -- any failure means "no box"
        raise SandboxUnavailable(f"no Docker daemon: {type(exc).__name__}: {exc}") from exc
    return client


def docker_available() -> bool:
    """True if a container could start. Used by tests to skip and by demos to advise."""
    try:
        _client()
    except SandboxUnavailable:
        return False
    return True


def run_in_sandbox(
    code: str, *, mount: Path | None = None, limits: SandboxLimits | None = None
) -> SandboxResult:
    """Run `code` in a throwaway container. Returns; does not raise on bad user code."""
    limits = limits or SandboxLimits()
    kwargs = container_kwargs(code, mount=mount, limits=limits)   # may raise: code too long
    client = _client()                                            # may raise: SandboxUnavailable

    started = time.monotonic()
    container = None
    timed_out = False
    exit_code: int | None = None
    output = ""
    try:
        container = client.containers.run(**kwargs)
        try:
            exit_code = container.wait(timeout=limits.timeout_s).get("StatusCode")
        except Exception:                                # noqa: BLE001 -- see the line-by-line
            if time.monotonic() - started < limits.timeout_s:
                raise                                    # a real docker error, not our deadline
            timed_out = True
        finally:
            with contextlib.suppress(Exception):
                container.kill()                         # SIGKILL. stop() asks politely.
        raw = container.logs(stdout=True, stderr=True, tail=MAX_OUTPUT_LINES)
        output = raw.decode("utf-8", errors="replace")
    finally:
        if container is not None:                        # guarantee 8: it dies either way
            with contextlib.suppress(Exception):
                container.remove(force=True, v=True)

    truncated = len(output) > limits.max_output_chars
    if truncated:
        output = output[: limits.max_output_chars] + "\n... TRUNCATED. Print a summary, not data."

    duration = time.monotonic() - started
    if timed_out:
        return SandboxResult(False, None, output, truncated, duration, reason="timeout")
    return SandboxResult(
        ok=exit_code == 0, exit_code=exit_code, output=output, truncated=truncated,
        duration_s=duration, reason="" if exit_code == 0 else "nonzero-exit",
    )


def reap_orphans(*, older_than_s: float = 300.0) -> int:
    """TODO(me): remove every container labelled mandala.sandbox that outlived its run.

    Why this is the rep: guarantee 8 is a `finally`, and a `finally` does not run when
    the host process is killed -9, when the laptop sleeps mid-wait, or when Docker
    Desktop restarts underneath you. So the teardown story has two halves and you have
    written one. List with client.containers.list(all=True, filters={"label": ...}),
    check each one's age against `older_than_s`, remove(force=True), count them.

    Then answer the harder question this function forces: should the demo call it at
    START-up (cheap and automatic, but it deletes things it did not create) or should
    it be an explicit chore you run (honest, but easy to never run)? There is no free
    answer. Write down which you chose and why -- that sentence is the deliverable.
    """
    raise NotImplementedError


@function_tool(name_override="run_code", failure_error_function=tool_error)
def run_code(ctx: RunContextWrapper[MandalaContext], code: str) -> str:
    """Run a short Python program in a throwaway container and return what it printed.

    The container has NO network and NO credentials. The job's data directory is
    mounted READ-ONLY at /data; nothing you write anywhere survives the call. You get
    about 30 seconds. Print a SUMMARY -- counts, a top-N, one small table -- never the
    raw data: the output is truncated and truncated output is a wasted call.

    Args:
        code: A complete Python program, run as `python -c <code>`. Standard library
            only; there is no network, so there is no pip.
    """
    permissions.check(ctx.context.agent_name, SANDBOX_TOOL_NAME)     # Day 8, first line
    result = run_in_sandbox(code, mount=ctx.context.sandbox_mount)
    print(ctx.context.audit(
        "run_code",
        f"chars={len(code)} exit={result.exit_code} {result.duration_s:.1f}s "
        f"reason={result.reason or 'ok'}",
    ))
    if result.reason == "timeout":
        return f"TIMED OUT and was killed. Partial output:\n{result.output}"
    if not result.ok:
        return f"The program exited {result.exit_code}. Output:\n{result.output}"
    return result.output or "(the program printed nothing)"
```

**Line by line:**

- The docstring **ranks the five defences and says which one is the boundary**, the same shape as
  Day 15's `search.py` and Day 18's `coordinator.py`. Third time: a flat list reads as "we did five
  things"; a ranked list tells the next reader which line they are not allowed to delete. And the
  `Blast radius (Principle 6)` paragraph is in the *module docstring*, not the lesson, because it has
  to be true in six months when nobody is reading the lesson.
- **`container_kwargs()` is pure, and that is the most important design decision in the file.** It
  takes strings and numbers and returns a dict; it never touches a socket. Consequence: §5 asserts
  all nine guarantees with no daemon, CI stays green on a runner without Docker, and §2.3's "you can
  still do most of today" is true. Compare Day 18, where the security lived in a Pydantic model for
  the same reason. **Put the guarantee where a test can read it without performing it.**
- `SANDBOX_IMAGE` is a **`TODO(me)`** and it is the Principle-4 rep. `:latest` would be the flagrant
  version of the mistake; `:3.12-slim` is the polite version of the same mistake. Your escape battery
  is a claim about a specific userland — pin the userland.
- `command=["python", "-I", "-u", "-B", "-c", code]` — a **list, never a string**, so nothing is
  handed to a shell and there is no quoting to get wrong. `-I` is isolated mode (ignores `PYTHON*`
  env vars and the user site directory, so the box behaves identically no matter what leaks in);
  `-u` is unbuffered, which is why you still see partial output from a program that got SIGKILLed;
  `-B` writes no `.pyc`, which matters because the root filesystem is read-only anyway and you would
  rather not find out that way. The rejected alternative was writing the code to a file in a
  writable mount — that needs a writable mount, and guarantee 4 says there isn't one.
- `"environment": {"HOME": "/tmp"}` — **one key. Look at it.** Python needs a writable `HOME` or some
  library will try `/nonexistent`. Everything else is absent because absence is the feature. `-I`
  means even a `PYTHONPATH` that somehow appeared would be ignored. **The failure this prevents is
  `environment=os.environ` or `{**os.environ, ...}`, which hands `GEMINI_API_KEY`, `GROQ_API_KEY` and
  `OPENROUTER_API_KEY` to model-written code and makes every other line here decorative** (§6, the
  trap of the day).
- `network_disabled=True` **and** `network_mode="none"`. Two mechanisms for one guarantee, because
  this is the one where being wrong is unrecoverable: with a network, everything the code reads can
  leave. §8 asks you to confirm the daemon accepts both together in `docker` 7.2.0 — if it rejects
  the combination, keep `network_disabled=True`, delete the other, and **write down which one you
  kept**, because §5's test asserts on this dict.
- `volumes={resolved: {"bind": "/data", "mode": "ro"}}` — `Path.resolve()` because Docker needs an
  absolute host path and a relative one fails in an unhelpful way; `mode="ro"` because the code is
  analysing evidence and **analysis must not be able to edit its evidence**. Exactly one entry, ever:
  a second mount is a second thing to reason about, and today's answer to "can I also mount X" is no.
- `read_only=True` is the **root** filesystem, which is the flag people forget after congratulating
  themselves on `mode="ro"`. Without it the mount is read-only and `/usr`, `/etc` and `/var` are not.
  Python still needs *somewhere* writable, so `tmpfs={"/tmp": ...}` gives it a RAM disk that vanishes
  with the container, sized (`16m`) so a program cannot fill memory by writing files, and `noexec` so
  it cannot write a binary and run it.
- `memswap_limit` equal to `mem_limit` — **the line everybody misses.** Set `mem_limit` alone and the
  container can swap, so your 256 MB cap becomes 256 MB of RAM plus as much swap as the host has, and
  the memory guarantee is advisory. Equal values mean no swap at all.
- `pids_limit=64` is the fork-bomb flag, and it is the one that protects the *host* rather than the
  container. `nano_cpus=500_000_000` is half a core: a busy loop then costs you 50% of one CPU for
  the timeout window instead of every core you own. **Both are "a mistake must be survivable while a
  human is not watching."**
- `user="nobody"`, `cap_drop=["ALL"]`, `security_opt=["no-new-privileges"]` — root-in-container is
  not root-on-host, but it is one kernel bug closer to it. Dropping all capabilities and forbidding
  privilege escalation via setuid closes the easy half of the known escape paths. `privileged=False`
  is stated even though it is the default, because **a security-relevant default that is not written
  down is a default nobody re-reads during review** — the same argument that put `writes=False` on
  every Day-8 `ToolSpec`.
- `detach=True` with `auto_remove=False` — a real trade-off, decided on purpose. `auto_remove=True` is
  tempting (the daemon deletes the container the instant it exits) but it races your `logs()` call:
  the box you want to read from may already be gone. So teardown is **ours**, in a `finally`, with
  `force=True`, and `labels={SANDBOX_LABEL: "1"}` exists so the survivors are findable — **a cleanup
  you cannot enumerate is not cleanup.** The gap this leaves (a host process killed `-9` never runs
  its `finally`) is exactly what `reap_orphans()` is for, which is why that `TODO(me)` is not optional.
- `container.wait(timeout=...)` is a **host-side** wall clock. Nothing inside the box agreed to it,
  which is the entire point: `signal.alarm` in the generated code would be enforced by the goodwill
  of code you did not write. The `except Exception` around it is broad on purpose — docker-py
  surfaces this as a `requests` read-timeout, an implementation detail of a transitive dependency —
  and it **classifies by our own clock, not by the exception type**: under the deadline it re-raises
  (a real Docker error must not be reported as a timeout), over the deadline it is a timeout. Day 10's
  error policy: catch narrowly where you can, and where you cannot, decide with information you own.
- `container.kill()` in an inner `finally`, not `container.stop()`. `stop()` sends SIGTERM and waits
  ten seconds for a graceful exit — from a program that has already proved it will not exit. **SIGKILL
  is the correct signal for something that broke its contract.**
- `logs(..., tail=MAX_OUTPUT_LINES)` — bound at the *source*, before the bytes are in your process,
  then truncate the decoded string again. Two bounds because they stop different things: `tail` stops
  a gigabyte crossing the socket, `max_output_chars` stops a 4001-character line reaching the model.
  (`tail` interleaves stdout and stderr by arrival, so ordering is approximate.) `errors="replace"`
  because **a sandbox that crashes the host process on a weird byte is a sandbox that failed**, and
  the truncation suffix is **advice** — *"Print a summary, not data"* — so the model's next attempt is
  better rather than identical (Day 15).
- `run_in_sandbox` **returns** for bad user code and **raises** only for our own failures
  (`SandboxUnavailable`, code too long). That seam matters: "your program exited 1" is information
  the model should act on, while "there is no Docker daemon" is an operator problem the model can do
  nothing about. Day 10, again.
- `permissions.check(ctx.context.agent_name, SANDBOX_TOOL_NAME)` is the **first line of the tool**,
  before anything is built or started. `agent_name` is Day 12's derived property, read off an
  immutable context — **the identity comes from your code, the code string comes from the model.**
  `PermissionDenied` propagates because `tool_error` re-raises it (Day 10): a security failure must
  never be converted into text the model can read and route around.
- `SANDBOX_TOOL_NAME` is one constant used both here and in `name_override`, so the permission-table
  key and the model-facing name **cannot drift** — Day 15's lesson, where a `name_override` that did
  not match the table was a capability the safety check could not see.
- `ctx.context.sandbox_mount` is a **new field on `MandalaContext`** — Day 12's dependency injection,
  not a module-level constant, so a test can point it at `tmp_path` and the demo can point it at
  `data/logs`. Add exactly one line to `src/mandala/context.py`:

```python
    sandbox_mount: Path | None = None   # the ONE directory run_code mounts, read-only
```

- The tool docstring tells the model **what is absent** — no network, no pip, no persistence — and
  **what shape to return**: a summary, not the data. Day 3's tool-description discipline plus Day 4's
  budget. A model that does not know there is no network will spend a whole call discovering it.
- `ctx.context.audit(...)` logs code length, exit code, duration and reason — **never the code
  itself.** That is a judgement call worth defending: the code is up to 4000 characters of
  model-generated text and putting it in every audit line makes the log unreadable and turns your log
  file into a store of attacker-influenced strings (Day 15). If you want the code, log a hash of it
  and keep the bodies somewhere with a retention policy. Write down whichever you chose.

### 4.4 The permission table learns a capability it gives to nobody

Day 8's table first, agents second — the order Day 15 established and Day 18 repeated. In
`src/mandala/permissions.py`:

```python
    "run_code": ToolSpec(
        name="run_code",
        writes=False,               # nothing it writes survives the container. See below.
        reads_untrusted=True,       # its output is derived from data we did not author
        blast_radius=(
            "arbitrary Python, confined to a container with no network, no credentials, "
            "one read-only mount, 0.5 CPU / 256MB / 64 pids, and ~30s to live; destroyed "
            "afterwards either way. Residual risk is a KERNEL escape, not a bug in "
            "sandbox.py. Granted to no agent that reads untrusted text."
        ),
    ),
```

and a new agent — because the whole point is that **no existing one gets this**:

```python
    "analyst": AgentSpec(
        name="analyst",
        tools=frozenset({"run_code"}),   # this tool and NOTHING else
    ),
```

**Line by line:**

- `writes=False` is a claim you should challenge before accepting: the code can absolutely call
  `open(..., "w")`. It is `False` because **`writes` in Day 8's table has always meant "can cause an
  effect that outlives the call"** — `post_reply` sends an email, `close_ticket` changes state. A
  write to a `tmpfs` that is destroyed thirty seconds later outlives nothing. The day someone adds a
  writable mount, this field flips to `True`, and `trifecta_violations()` starts caring. Write the
  reasoning in the code review, not just the value.
- `reads_untrusted=True` — the honest classification, and the one people get wrong. The *code* is
  ours-ish, but the **output is derived from files we did not author** (a log full of user-supplied
  strings is attacker-influenced text, Day 15). Whatever comes back is untrusted text arriving in a
  context window, so it is labelled that way.
- The `blast_radius` sentence names the residual risk **in the table itself**. Day 8 asked for plain
  English rather than a severity enum precisely so a sentence like *"the residual risk is a kernel
  escape"* could be written down and held against the code later. A `blast_radius` of `"low"` would
  have said nothing.
- `AGENTS["analyst"]` holds **exactly one tool.** Not `get_ticket`, not `kb_search`, and absolutely
  not `web_search`. It is a *dedicated* capability holder: everything it can do, it does in the box.
- **`run_code` is granted to no pre-existing agent, and never to the Researcher.** The Researcher has
  read the open web since Day 15; the combination of "reads attacker-controlled text" and "executes
  code" is not a risky pairing to manage, it is the attack itself. The container would contain it —
  that is what the container is for — but do not build the situation where the container is the only
  thing standing between you and a bad afternoon.
- Run `uv run pytest tests/test_permissions.py -q` now. `trifecta_violations()` must still be `[]`.
  **Sixteen days of that function returning `[]`** is the reason this project can add code execution
  on Day 19 without a two-hour argument.

### 4.5 `days/day-19/lab/sandbox_demo.py` — the honest use case

```python
"""Log analysis: the model writes pandas-free Python, the log is mounted read-only.

This is the plan's OAI-19 example, run for real. The Analyst never sees the log --
its code does, inside the box -- and only a printed summary comes back.

Run:
    uv run python days/day-19/lab/sandbox_demo.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from agents import Agent, Runner

from mandala.context import MandalaContext
from mandala.sandbox import docker_available, run_code
from mandala.sdk import DEFAULT_SETTINGS, make_model
from mandala.tracing import install_local_tracing

LOGS = Path("data/logs")

JOB = (
    "The file /data/app.log is a plain-text application log. Tell me: how many ERROR "
    "lines there are, which tenant has the most ERRORs, and the busiest hour. Write ONE "
    "Python program that reads the file and prints those three numbers, then answer from "
    "what it printed. Do not print the log."
)


def analyst() -> Agent:
    return Agent(
        name="Analyst",
        instructions=(
            "You answer questions about files by writing Python and running it with "
            "run_code. The file is at /data and is READ-ONLY. There is no network and no "
            "pip -- standard library only. Print a small summary, never the raw data. "
            "If the program exits non-zero, read the traceback and fix it once; if it "
            "fails twice, say what went wrong instead of guessing."
        ),
        model=make_model("groq"),
        model_settings=DEFAULT_SETTINGS,
        tools=[run_code],
    )


async def main() -> None:
    if not docker_available():
        raise SystemExit("No Docker daemon. See LESSON §2.2 -- start Docker Desktop.")

    processor = install_local_tracing()
    context = MandalaContext(
        actor="agent:analyst", request_id="req-sandbox-19", sandbox_mount=LOGS
    )
    result = await Runner.run(analyst(), JOB, context=context, max_turns=6)

    print(f"\n--- answer ---\n{result.final_output}")
    processor.force_flush()
    print(f"\ntraces: {processor.directory}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Line by line:**

- **The Analyst is a new agent holding one tool**, matching §4.4's `AgentSpec` exactly. Resist adding
  `kb_search` "so it has context" — every extra tool on the agent that can execute code is a new way
  for untrusted text to reach the thing that runs programs.
- `sandbox_mount=LOGS` is injected on the context (Day 12), so the *demo* decides what is visible and
  the *tool* never chooses. Point it at `data/logs`, not `data/` — **mount the smallest directory
  that answers the question**, which is the file-level version of Principle 6.
- The prompt states the path, the read-only-ness, the absence of pip, and the required answer shape.
  **Four facts that each save a wasted round trip.** And *"fix it once; if it fails twice, say what
  went wrong"* is a retry budget in the prompt matching `max_turns=6` (Day 10) — code-writing agents
  will happily loop forever on a traceback.
- `docker_available()` first, so a missing daemon produces one sentence and a pointer instead of a
  stack trace after the model call has already been spent. **On a free tier, a crash after the request
  costs you the request.**
- `install_local_tracing()` in the demo, never in `sandbox.py` — Day 14's rule. Read the trace after:
  each `run_code` span sits next to a generation span, and the shape tells you whether the model
  wrote one good program or three bad ones.

### 4.6 `days/day-19/lab/escape_attempts.py` — the measurement 🎯

Everything above is a claim. **This file is the evidence, and it is what you record in the CHECKLIST.**

```python
"""Six things the box must refuse, and one it must allow. Costs 0 model requests.

This is pure Docker: no agent, no provider, no key. Run it whenever you touch
sandbox.py, and record the table in days/day-19/CHECKLIST.md.

Run:
    uv run python days/day-19/lab/escape_attempts.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mandala.sandbox import SandboxLimits, docker_available, run_in_sandbox

LOGS = Path("data/logs")
FAST = SandboxLimits(timeout_s=6.0)      # the timeout attempt should not cost 30s


@dataclass(frozen=True)
class Attempt:
    name: str
    expect: str          # "refused" or "allowed"
    code: str


ATTEMPTS = [
    Attempt("control: read the mounted log", "allowed",
            "print(len(open('/data/app.log').read().splitlines()), 'lines')"),
    Attempt("network: fetch a URL", "refused",
            "import urllib.request as u; print(u.urlopen('https://example.com', timeout=4).status)"),
    Attempt("write to the read-only mount", "refused",
            "open('/data/pwned.txt', 'w').write('x'); print('WROTE')"),
    Attempt("write outside the mount", "refused",
            "open('/etc/pwned', 'w').write('x'); print('WROTE')"),
    Attempt("infinite loop", "refused",
            "while True: pass"),
    Attempt("fork bomb", "refused",
            "import os\nwhile True: os.fork()"),
    Attempt("read a credential", "refused",
            "import os\nprint('LEAKED', os.environ['GROQ_API_KEY'])"),
]

# TODO(me): add a seventh attempt of your own, and WRITE DOWN THE EXPECTED RESULT
# BEFORE YOU RUN IT. Candidates: list /proc/1/environ; open('/var/run/docker.sock');
# os.setuid(0); mount a filesystem; spawn a subprocess that outlives the parent.
# Why this is the rep: predicting the verdict is threat modelling; running it and
# accepting whatever happened is not. If your prediction is wrong -- either way --
# that is the most valuable thing you will learn today, so write it down first.


def verdict(attempt: Attempt) -> tuple[str, str]:
    result = run_in_sandbox(attempt.code, mount=LOGS, limits=FAST)
    got = "allowed" if result.ok else "refused"
    detail = result.reason or f"exit={result.exit_code}"
    tail = result.output.strip().splitlines()[-1:] or [""]
    return ("PASS" if got == attempt.expect else "*** FAIL ***"), f"{got:8} {detail:14} {tail[0][:44]}"


def main() -> None:
    if not docker_available():
        raise SystemExit("No Docker daemon. See LESSON §2.2 -- start Docker Desktop.")

    print(f"{'attempt':34} {'expect':9} {'verdict':12} detail")
    print("-" * 100)
    failures = 0
    for attempt in ATTEMPTS:
        mark, detail = verdict(attempt)
        failures += mark != "PASS"
        print(f"{attempt.name:34} {attempt.expect:9} {mark:12} {detail}")
    print("-" * 100)
    print(f"{len(ATTEMPTS) - failures}/{len(ATTEMPTS)} as expected. Record this in the CHECKLIST.")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
```

**Line by line:**

- **The first row is a control case, and it is not padding.** A battery of six refusals passes
  perfectly against a sandbox that is simply broken — a bad image name refuses everything. The
  control proves the box still *works*, which is what makes the other six mean something. **Any
  safety battery without a positive case is measuring nothing.**
- `expect` is a field, not a comment, so the script computes PASS/FAIL instead of making you eyeball
  seven blobs of output. The `TODO(me)` extends the same discipline to your own attempt: **predict,
  then run.**
- The **network** attempt uses a 4-second timeout so a failure surfaces as a fast DNS error rather
  than hanging until the container deadline. If it ever comes back `allowed`, stop and re-read
  `container_kwargs` — you have no sandbox, you have a container.
- **Two write attempts, not one**, because they fail for different reasons: `/data` is refused by
  `mode="ro"`, `/etc` by `read_only=True` on the root filesystem. Delete either flag and exactly one
  row goes red — which is what makes this a *diagnostic* rather than a smoke test.
- The **infinite loop** runs with `FAST` (6 s) so the battery finishes in under a minute, and it
  proves the enforcement is host-side: the code never agreed to stop. The **fork bomb** is the
  `pids_limit` proof and the row that protects the laptop rather than the container — run it once
  with Task Manager open. It should be dull, and *dull is the result*.
- The **credential** attempt asks for `GROQ_API_KEY` by name — a key that genuinely exists in your
  host environment (Day 1). `KeyError` means a non-zero exit, which reads as `refused`. **Change
  `container_kwargs` to pass `os.environ` and this row flips to `allowed` and prints your key**, which
  is the most persuasive thirty seconds available on this topic. Do it once, deliberately, then put
  the line back.
- `raise SystemExit(1 if failures else 0)` — a **non-zero exit on any unexpected verdict**, so this
  file can be wired into CI or a pre-commit hook later and does not depend on someone reading a table.
- **This whole file costs 0 model requests.** No agent, no provider, no key: pure Docker (§7). The
  most important measurement of the day is also the free one, which is not luck — it is what putting
  the guarantees in `container_kwargs()` bought you.

### 4.7 What you should see

```
attempt                            expect    verdict      detail
----------------------------------------------------------------------------------------------------
control: read the mounted log      allowed   PASS         allowed  exit=0         41 lines
network: fetch a URL               refused   PASS         refused  exit=1         urllib.error.URLError
write to the read-only mount       refused   PASS         refused  exit=1         OSError: [Errno 30] Read-o
write outside the mount            refused   PASS         refused  exit=1         OSError: [Errno 30] Read-o
infinite loop                      refused   PASS         refused  timeout        
fork bomb                          refused   PASS         refused  exit=1         BlockingIOError: [Errno 11
read a credential                  refused   PASS         refused  exit=1         KeyError: 'GROQ_API_KEY'
----------------------------------------------------------------------------------------------------
7/7 as expected. Record this in the CHECKLIST.
```

**Read the `detail` column, not just the verdict.** Each refusal has a *mechanism*, and the mechanism
is what you will be asked about: `Errno 30` is the kernel refusing a write to a read-only mount,
`BlockingIOError` is the cgroup pids controller refusing a fork, `timeout` is *your host process*
sending SIGKILL. A row that says `refused` for the wrong reason — say, the network attempt failing
because DNS was slow rather than because there is no interface — is a row that will stop being true.

Two follow-ups worth doing once. **Break one flag and confirm exactly one row goes red** — delete
`read_only=True` and only the `/etc` row flips; that one-to-one mapping between flag and row is the
design, and §5 turns it into tests. Then **check nothing survives**:
`docker ps -a --filter label=mandala.sandbox` must print an empty list after the battery. If it does
not, your `finally` is not running, and that is `reap_orphans()` asking to be written.

### 4.8 What a container is not ⚠️

Say this plainly, because the failure mode of today is overconfidence:

> **A container is a shared-kernel isolation mechanism, not a virtual machine.** Namespaces and
> cgroups are enforced by the *same kernel* the untrusted code is calling into. Container escapes via
> kernel bugs are a real, recurring class of vulnerability. "No network + no credentials + dies in
> 30 s" is a **blast-radius reduction**, not a proof of safety.

Concretely, what today does and does not buy:

| Threat | Today's box |
|---|---|
| Code reads/edits your home directory, `.env`, SSH keys | **stopped** — not mounted |
| Code exfiltrates what it read | **stopped** — no network at all |
| Code steals your free-tier API keys | **stopped** — they are not in the environment |
| Code eats the machine (CPU, RAM, forks) | **bounded** — cgroups, and the box dies |
| Code persists something for later | **stopped** — read-only rootfs, tmpfs, container removed |
| Code reads *the mounted file* it was pointed at | **allowed on purpose** — that is the job. Mount the smallest thing |
| Code exploits a **kernel** vulnerability to reach the host | **not stopped.** Reduced attack surface (no caps, no new privs, non-root), not eliminated |
| Code attacks the **Docker daemon socket** | **not applicable here — and never mount `/var/run/docker.sock`.** That single mount converts this whole file into a root shell on your host |

Where the honest answers are:

- **The paid native sandbox (§3.3)** is stronger because a platform running many tenants' code can
  afford a hypervisor boundary and a hardened per-tenant kernel. That is the one row where they win
  outright.
- **Day 67 (AG-18)** is where this curriculum does better: the plan's row says *"agent-written code
  runs in a disposable microVM with no credentials and minimal network"* — a **microVM**, precisely
  because a container's boundary is a shared kernel. Today's file is the preview; Day 67 is the
  treatment, and it will re-run this exact battery against a stronger boundary.
- Between now and then, the mitigations are boring and effective: **never mount the Docker socket,
  keep the image pinned by digest and current, run the daemon rootless or in Docker Desktop's VM (on
  macOS and Windows you already get a VM boundary for free — say so, it is a real advantage of your
  laptop over a Linux CI box), and keep the mounted directory as small as the question allows.**

---

## §5 The eval that must be able to fail

**One test per guarantee.** Remove any single flag from `container_kwargs()` and exactly one test goes
red — that is the design goal, and it is only achievable because the configuration is a pure function
(§4.3). This is the **flip-it family**: assertions that exist to catch a one-line diff, nothing else.

### `tests/test_sandbox.py`

```python
"""A sandbox is configuration. Configuration rots silently. These tests are the alarm."""

import os

import pytest

from mandala.context import MandalaContext
from mandala.permissions import AGENTS, TOOLS, PermissionDenied, tools_for, trifecta_violations
from mandala.sandbox import (
    MAX_CODE_CHARS, MOUNT_PATH, SANDBOX_LABEL, SANDBOX_TOOL_NAME,
    SandboxLimits, container_kwargs, docker_available, run_in_sandbox,
)

LIMITS = SandboxLimits()
needs_docker = pytest.mark.skipif(not docker_available(), reason="no Docker daemon")
# TODO(me): this marker is now defined here and needed again in tests/test_ag18.py on
# Day 67. Move it to tests/conftest.py the second time you need it, not the third.


def kw(code="print(1)", mount=None):
    return container_kwargs(code, mount=mount, limits=LIMITS)


# --- guarantee 1: no network, no credentials -------------------------------------
def test_the_box_has_no_network():
    """FLIP IT: delete network_disabled and watch this go red. Then re-read §4.8."""
    assert kw()["network_disabled"] is True


def test_no_host_environment_is_forwarded():
    """FLIP IT -- the trap of the day. Change environment to dict(os.environ), watch
    this go red, and then look at exactly what you just handed model-written code.
    """
    env = kw()["environment"]
    assert env == {"HOME": "/tmp"}, "the environment must be a literal, never os.environ"
    for secret in ("GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", "PATH", "HOSTNAME"):
        assert secret not in env
    assert not (set(env) & set(os.environ) - {"HOME"}), "no host key may appear by accident"


# --- guarantees 3 and 4: nothing to corrupt, nothing to keep ----------------------
def test_the_only_mount_is_read_only(tmp_path):
    volumes = kw(mount=tmp_path)["volumes"]
    assert len(volumes) == 1, "exactly one mount, forever"
    (spec,) = volumes.values()
    assert spec == {"bind": MOUNT_PATH, "mode": "ro"}


def test_nothing_is_mounted_when_no_mount_is_asked_for():
    assert kw()["volumes"] == {}


def test_the_root_filesystem_is_read_only_and_tmp_is_ephemeral():
    """mode='ro' on the mount is not enough; /etc must be refused too (§4.6 row 4)."""
    config = kw()
    assert config["read_only"] is True
    assert set(config["tmpfs"]) == {"/tmp"}
    assert "noexec" in config["tmpfs"]["/tmp"] and "size=" in config["tmpfs"]["/tmp"]


# --- guarantee 6: bounded damage ---------------------------------------------------
def test_cpu_memory_and_pids_are_all_capped():
    config = kw()
    assert config["mem_limit"] == LIMITS.mem_limit
    assert config["memswap_limit"] == config["mem_limit"], "swap makes mem_limit advisory"
    assert 0 < config["pids_limit"] <= 128, "a fork bomb must die, not take the laptop"
    assert 0 < config["nano_cpus"] <= 1_000_000_000


# --- guarantee 7: no privileges to escalate ----------------------------------------
def test_the_box_is_unprivileged():
    config = kw()
    assert config["user"] == "nobody"
    assert config["cap_drop"] == ["ALL"]
    assert "no-new-privileges" in config["security_opt"]
    assert config["privileged"] is False


def test_code_is_argv_never_a_shell_string():
    """A string command would be handed to a shell. That is a different lesson entirely."""
    command = kw("print('hi')")["command"]
    assert isinstance(command, list) and command[0] == "python"
    assert command[-1] == "print('hi')"


def test_oversized_code_is_refused_before_a_container_exists():
    with pytest.raises(ValueError):
        kw("x" * (MAX_CODE_CHARS + 1))


def test_the_image_is_pinned_not_latest():
    """Principle 4. Red until you resolve the digest (§2.2) if you enforce '@sha256:'."""
    assert not LIMITS.image.endswith(":latest")


# --- guarantees 8 and 9: it dies either way, and the output is bounded --------------
class _FakeContainer:
    def __init__(self, *, log_bytes=b"ok\n", raise_on_logs=False):
        self._log_bytes, self._raise = log_bytes, raise_on_logs
        self.removed = self.killed = False

    def wait(self, timeout=None):
        return {"StatusCode": 0}

    def logs(self, **_):
        if self._raise:
            raise RuntimeError("daemon went away mid-read")
        return self._log_bytes

    def kill(self):
        self.killed = True

    def remove(self, **_):
        self.removed = True


def _fake_client(monkeypatch, container):
    class _Client:
        class containers:                              # noqa: N801 -- mirrors docker-py's shape
            @staticmethod
            def run(**_):
                return container

    monkeypatch.setattr("mandala.sandbox._client", lambda: _Client())


def test_output_is_truncated_before_it_reaches_the_model(monkeypatch):
    """Day 4's budget. Generated code can print 10 MB; a context window cannot hold it."""
    _fake_client(monkeypatch, _FakeContainer(log_bytes=b"A" * 1_000_000))
    result = run_in_sandbox("print('A'*10**6)")
    assert result.truncated is True
    assert len(result.output) <= LIMITS.max_output_chars + 80


def test_the_container_is_removed_even_when_the_run_raises(monkeypatch):
    """FLIP IT: move remove() out of the finally and this goes red. Teardown is a
    guarantee, not a happy path -- a leaked container still holds its bind mount.
    """
    container = _FakeContainer(raise_on_logs=True)
    _fake_client(monkeypatch, container)
    with pytest.raises(RuntimeError):
        run_in_sandbox("print(1)")
    assert container.removed is True


# --- the permission boundary (Day 8) ------------------------------------------------
def test_run_code_is_in_the_table_with_an_honest_blast_radius():
    spec = TOOLS[SANDBOX_TOOL_NAME]
    assert spec.writes is False
    assert spec.reads_untrusted is True
    assert "kernel" in spec.blast_radius.lower(), "name the residual risk, not just the wins"


def test_run_code_is_never_held_beside_a_tool_that_reads_untrusted_text():
    """The whole grant policy, as one assertion. Give run_code to the Researcher and
    this goes red -- which is the conversation we want to have BEFORE the merge.
    """
    for name, agent in AGENTS.items():
        if SANDBOX_TOOL_NAME in agent.tools:
            others = {t for t in agent.tools if t != SANDBOX_TOOL_NAME}
            leaky = {t for t in others if TOOLS[t].reads_untrusted}
            assert not leaky, f"{name} holds run_code beside untrusted-input tools: {leaky}"


def test_the_researcher_and_resolver_cannot_execute_code():
    assert SANDBOX_TOOL_NAME not in tools_for("researcher")   # reads the open web (Day 15)
    assert SANDBOX_TOOL_NAME not in tools_for("resolver")


def test_the_lethal_trifecta_is_still_empty_after_adding_code_execution():
    assert trifecta_violations() == []          # sixteen days running (Day 8)


def test_a_caller_without_the_grant_is_denied(tmp_path):
    from mandala import permissions
    context = MandalaContext(actor="agent:researcher", request_id="r", sandbox_mount=tmp_path)
    with pytest.raises(PermissionDenied):
        permissions.check(context.agent_name, SANDBOX_TOOL_NAME)


# --- the two that need a daemon -----------------------------------------------------
@needs_docker
def test_the_control_case_really_runs(tmp_path):
    """Without this, every 'refused' below could just mean the box is broken."""
    (tmp_path / "app.log").write_text("ERROR x\nINFO y\n", encoding="utf-8")
    result = run_in_sandbox(
        "print(sum('ERROR' in l for l in open('/data/app.log')))",
        mount=tmp_path, limits=SandboxLimits(timeout_s=20.0),
    )
    assert result.ok and result.output.strip() == "1"


@needs_docker
def test_the_network_is_really_off(tmp_path):
    result = run_in_sandbox(
        "import urllib.request as u; u.urlopen('https://example.com', timeout=4)",
        mount=tmp_path, limits=SandboxLimits(timeout_s=20.0),
    )
    assert not result.ok, "the box reached the network -- stop and re-read §4.3"
```

**Line by line:**

- **Seventeen of the nineteen tests need no Docker and no model requests**, and that is the payoff of
  §4.3's pure `container_kwargs()`. It is also why `@needs_docker` exists: a suite that fails on a CI
  runner without a daemon gets marked `--ignore` by the third person who hits it, and then *none* of
  it runs. **A skipped test still reports; a deleted test does not.** Register the marker in
  `pyproject.toml` (`markers = ["docker: needs a running Docker daemon"]`) so `-W error` stays clean.
- `test_no_host_environment_is_forwarded` is **the flip-it test of the day.** It asserts equality
  against a literal, not `"GROQ_API_KEY" not in env` — an inequality test passes for
  `{**os.environ, "HOME": "/tmp"}` minus three keys, which is exactly the "I filtered the dangerous
  ones" mistake. **Assert the whole environment, because a denylist of secrets is a list you must keep
  complete forever** (Day 18's argument, one layer down).
- `test_the_only_mount_is_read_only` asserts `len(volumes) == 1` *before* asserting the mode. The
  number is the interesting assertion: a second mount added "just for outputs" is how the read-only
  guarantee dies, and it would sail past a test that only checked mode.
- `test_the_root_filesystem_is_read_only_and_tmp_is_ephemeral` exists because `mode="ro"` protects the
  mount and nothing else. Two flags, two tests, and §4.6 has a row for each — **one flag, one row, one
  test** is the property that makes this suite a diagnostic instead of a smoke alarm. Same instinct
  behind asserting `memswap_limit == mem_limit` with the reason in the message: six months from now
  that message is the only explanation anyone will read.
- `test_code_is_argv_never_a_shell_string` guards a mistake that is easy to make while debugging
  (`command=f"python -c '{code}'"`) and impossible to spot in review. A shell in the box is a second
  interpreter with its own escaping rules.
- `_FakeContainer` / `_fake_client` — **the seam that lets teardown and truncation be tested with no
  daemon.** `raise_on_logs=True` simulates the daemon disappearing mid-read, which is the case where
  a `remove()` that lives outside the `finally` silently stops running. Rejected alternative: an
  integration test that greps `docker ps -a`. It would be slower, flakier, and would not fail for the
  right reason.
- `test_run_code_is_never_held_beside_a_tool_that_reads_untrusted_text` is **the grant policy as one
  assertion**, and it is written as a property over `AGENTS` rather than a hard-coded list, so it keeps
  protecting you on Day 40 when there are nine agents. Day 15's rule again: when a design sentence can
  become a test, make it one.
- `test_the_lethal_trifecta_is_still_empty_after_adding_code_execution` — **invariants are worth
  re-asserting exactly when capability grows.** Day 15 said it, Day 18 said it, and today is the
  largest capability increase in the project so far.
- The two `@needs_docker` tests are the smallest possible integration pair: **one positive, one
  negative.** The positive one is not optional — without it, "refused" is indistinguishable from
  "broken", which is the same argument as §4.6's control row.
- **Every test here costs 0 model requests.** No agent is constructed, no provider is called. Today's
  entire security surface is testable for free, and that is a consequence of where the guarantees were
  put, not a happy accident.

---

## §6 Traps

- **Forwarding the host environment into the container** (`environment=os.environ`, or
  `{**os.environ, "HOME": "/tmp"}`). Model-written code now holds `GEMINI_API_KEY`, `GROQ_API_KEY`
  and `OPENROUTER_API_KEY`, and every other guarantee today is decoration. **🎯 The trap of the day**,
  and it arrives disguised as "the code needs `PATH`".
- **Mounting the Docker socket.** `/var/run/docker.sock` inside the box is a root shell on your host —
  the code can start a privileged container mounting `/`. There is never a good reason for it here.
- **`mode="ro"` without `read_only=True`.** The mount is protected and `/etc`, `/usr`, `/var` are not.
  §4.6 has two write rows precisely so you find out which flag you forgot.
- **`mem_limit` without `memswap_limit`.** Docker then allows swap up to double, and your memory cap
  is advisory. One extra line, and nobody notices its absence.
- **Enforcing the timeout inside the container** (`signal.alarm`, a `threading.Timer` in the generated
  code). That is enforcement by the goodwill of code you did not write. The host holds the clock.
- **`container.stop()` instead of `container.kill()`.** `stop()` sends SIGTERM and waits ten seconds
  for a graceful exit from a program that has already demonstrated it will not exit gracefully.
- **Teardown outside a `finally`.** The container survives every path you did not think about —
  exception, timeout, `KeyboardInterrupt` — and each survivor holds a bind mount and disk.
- **`auto_remove=True` plus reading logs.** The daemon may delete the container before your `logs()`
  call lands, so you get a `NotFound` instead of the output, intermittently, on a slow machine.
- **Returning the container's full stdout to the model.** Generated code can print megabytes; a
  faithful sandbox that pipes it into a context window has been used to DoS *you* (Day 4).
- **`:latest`, or any bare tag.** Your escape battery is a security claim about one specific userland.
  A tag is a mutable pointer, so tomorrow the claim is about something else (Principle 4).
- **A battery with no control case.** Six refusals also pass when the image name is wrong and nothing
  runs at all. The positive row is what makes the negative rows evidence.
- **Granting `run_code` to an agent that reads untrusted text.** The Researcher has read the open web
  since Day 15; untrusted input plus code execution is not a risky combination, it is the attack.
- **Believing the container is a VM.** Shared kernel, real escape class, §4.8. Overconfidence here is
  the difference between an engineer you can trust with this and one you cannot.

---

## §7 Request budget

| Activity | Model requests | Notes |
|---|---|---|
| Reading OAI-18/OAI-20 docs, drafting the explainer (§3.4) | **0** | prose, and it is a gate artifact |
| `container_kwargs()` iteration, printing the dict | **0** | a pure function |
| **`escape_attempts.py` — the whole battery, every run** | **0** | pure Docker: no agent, no key |
| All 17 non-Docker tests + the 2 `@needs_docker` tests | **0** | no agent is ever constructed |
| `sandbox_demo.py` × 3 | ~12 (Groq) | ~3–4 calls per run: write code, read output, answer |
| Prompt iteration to stop the model printing the whole log | ~8 (Groq) | budget for it; the first program always over-prints |
| **Total** | **≈ 20, Groq** | log it in `docs/RATE_BUDGET.md` |

**The most important measurement of the day costs zero model requests.** `escape_attempts.py` is the
day's evidence and it never talks to a provider — run it as often as you like, including after every
edit to `container_kwargs()`. That is not luck: it is what putting the guarantees in a pure function
bought you, and it is the same result as Day 18's "the security design is free to test".

Today is the cheapest lab in Phase 3 by a wide margin. If your Groq ceiling is tight, drop
`sandbox_demo.py` to one run and note it — but **never** skip the battery.

---

## §8 Verify before you code

Written **2026-08-20** against `openai-agents` **0.22.0** and `docker` **7.2.0**. §3 is 🅿️: **its API
shape must be *read*, not tested, because there is no key with which to run it.** Quote it as read.

- `https://openai.github.io/openai-agents-python/` — the SDK docs index. **Find the harness / sandbox
  pages for 0.22.0** and record the real class and parameter names in place of §3.2's placeholders.
- `https://openai.github.io/openai-agents-python/ref/tool/` — **confirm in 0.22.0** that
  `function_tool` still takes `name_override` and `failure_error_function` (unchanged since Day 10).
- `https://platform.openai.com/docs/guides/tools` — the hosted execution surface the native sandbox
  sits on. **Confirm whether the harness is still Python-first with TS pending** (OAI-20) and whether
  code mode / subagents have shipped. Record the date you checked.
- `https://docker-py.readthedocs.io/en/7.2.0/containers.html` — **confirm in docker 7.2.0**:
  `network_disabled` and `network_mode="none"` are accepted **together** (if not, keep
  `network_disabled` and fix the §5 assertion); `pids_limit`, `nano_cpus`, `memswap_limit`,
  `security_opt` and `tmpfs` are all `containers.run` parameters; and what `container.wait(timeout=)`
  raises on expiry — §4.3 deliberately classifies by our own clock rather than by that exception type,
  and you should confirm that was necessary.
- `https://docs.docker.com/engine/security/` and `.../security/seccomp/` — the default seccomp and
  capability posture you are building on. **Read what `--cap-drop=ALL` does and does not remove**, and
  what the default seccomp profile already blocks. This is the paragraph behind §4.8.
- **Confirm the `nobody` user exists in your pinned image.** `docker run --rm python:3.12-slim id
  nobody`. If a future image drops it, `user="nobody"` fails at start and every §4.6 row goes red at
  once — a failure mode worth recognising in one second rather than twenty minutes.
- If anything above differs from this lesson: one line in `docs/CHANGELOG_PLAN.md`. If the paid
  harness has moved materially, that is a Part-2/Part-4 matrix fact and needs an addendum before the
  Day-22 gate (Principle 14) — **do not silently adapt.**

---

## §9 Say it in an interview

> "The April 2026 Agents SDK line ships a model-native harness — Codex-style filesystem tools,
> configurable memory, and native sandbox execution for long-horizon file work. I read it rather than
> ran it: it is paid, hosted infrastructure and my project is zero-budget. What I took from reading it
> is that the SDK grew an opinion about the three things every long-horizon agent needs — a filesystem,
> a memory that outlives the context window, and somewhere safe to be wrong — and that **the
> integration is the product**, not any one of the three. So I built the third one myself: a function
> tool that runs model-written Python in a throwaway Docker container. No network, no credentials,
> one directory mounted read-only, a host-enforced 30-second deadline, capped CPU/memory/pids,
> non-root with all capabilities dropped, and teardown in a `finally`. **Six attacks, six refusals,
> plus a control case that succeeds so I know the box isn't just broken** — the table prints and it
> costs zero model requests."

> "The part I would not skip is the honesty. **A container is a shared-kernel isolation mechanism, not
> a VM** — kernel escapes are a real class — so what I built is a blast-radius reduction, not a proof
> of safety, and their native sandbox is genuinely stronger because a multi-tenant platform can afford
> a hypervisor boundary. Two design decisions I would defend anywhere. First, **the container
> configuration is a pure function that returns a dict**, so every guarantee is a unit test with no
> daemon and no key — remove one flag and exactly one test goes red, which matters because a sandbox
> is configuration and configuration rots silently. Second, **the tool is granted to no agent that
> reads untrusted text.** My Researcher reads the open web; code execution plus attacker-controlled
> input is not a combination to manage, it is the attack. And the mistake I actively test against is
> passing `os.environ` into the container — that one line would hand my API keys to model-written code
> and make everything else theatre."

---

## §10 Done when

```bash
./m check
./m done 19
```

- [ ] `escape_attempts.py` prints **7/7**, and the numbers are written in the CHECKLIST.
- [ ] `docs/explainers/paid-harness-and-sandbox.md` exists, in your words — the Day-22 gate needs it.
- [ ] `docker ps -a --filter label=mandala.sandbox` is empty.

Tomorrow: **durability**. Today's container dies on purpose in thirty seconds; tomorrow asks what
happens when the *host* process dies in the middle of a job — Temporal workflows on free models, plus
realtime awareness (OAI-21/22). Today you bounded where code may run; tomorrow you make a run survive
the machine it started on.
