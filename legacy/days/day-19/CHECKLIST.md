# Day 19 — CHECKLIST

**IDs covered:** OAI-18 🅿️ (the model-native harness, docs-level) · OAI-19 🛠️ (the $0 Docker
sandbox) · OAI-20 🅿️ (roadmap literacy: code mode & subagents — a freshness item, not a lab)

## Demo command

```bash
uv run python days/day-19/lab/escape_attempts.py    # THE measurement — 0 model requests
uv run python days/day-19/lab/sandbox_demo.py       # the honest use case: log analysis in the box
docker ps -a --filter label=mandala.sandbox         # must be EMPTY afterwards
```

## Setup

- [ ] `./m start 19` and `./m scaffold 19` run
- [ ] `uv add "docker==7.2.0"` — matches the Day-19 row in `docs/PINS.md`
- [ ] **Docker Desktop running**: `docker version` shows a **Server** block, `docker run --rm
      hello-world` succeeds, `docker pull python:3.12-slim` done, and `docker.from_env()` works
- [ ] Image digest resolved: `python@sha256:` **______________________** (the `TODO(me)`)
- [ ] `data/logs/app.log` written by hand — ~40 lines, varied levels/tenants/hours, fixture only
- [ ] `tests/test_permissions.py` and `tests/test_coordinator.py` green **before** starting
- [ ] Files created (`src/mandala/sandbox.py`, two lab files, `tests/test_sandbox.py`)
- [ ] **No Docker?** §2.3 read — §3 in full, §3.4's explainer, `container_kwargs()`, the permission
      row and 15 of the 17 tests are all still today's work

## OAI-18 🅿️ — the harness (read, not run)

- [ ] Can name the **three things** the SDK grew opinions about: filesystem, memory, execution — and
      **what I would have to build instead** for each (`kb.py`, `MemoryStore`, `sandbox.py`)
- [ ] Can say why **the integration is the product** — a loop that knows all three
- [ ] Read the live 0.22.0 docs and replaced §3.2's `<Placeholders>` with real names
- [ ] Can name **three things the paid version genuinely does better**, without flinching
- [ ] Can say precisely *why* we cannot run it (hosted paid infra + LiteLLM chat-surface + Principle 5)

## OAI-18 🅿️ — the Phase-3 gate artifact

- [ ] **`docs/explainers/paid-harness-and-sandbox.md` created — in my own words**
- [ ] All eight headings answered (what it is / problem / what it replaces / why I couldn't run it /
      what I built instead + concessions / the number / what I'd change on a paid team / freshness)
- [ ] Every 🅿️ claim says **read, not run** with a version and date; every 🛠️ claim points at a file
      or a test
- [ ] Fits on one page, and I have **read it aloud once** without stumbling

## OAI-20 🅿️ — roadmap literacy

- [ ] Can name the two directions: **code mode** and **subagents**; Python-first, TS later
- [ ] Can say the rule: **track a roadmap, never design against it**
- [ ] Freshness line added to the Friday `/freshness` pass, with today's date
- [ ] Have NOT added an adapter/registry/base class for a feature that does not exist

## OAI-19 🛠️ — the nine guarantees (§4.1)

- [ ] 1. `network_disabled=True` — no network at all
- [ ] 2. `environment` is a **literal dict**, never `os.environ`, never `{**os.environ, ...}`
- [ ] 3. exactly **one** volume, `{"bind": "/data", "mode": "ro"}`
- [ ] 4. `read_only=True` on the root fs + a sized `noexec` `tmpfs` for `/tmp`
- [ ] 5. host-side deadline → `container.kill()` (SIGKILL, **not** `stop()`)
- [ ] 6. `mem_limit` **and** `memswap_limit`, `pids_limit`, `nano_cpus`
- [ ] 7. `user="nobody"`, `cap_drop=["ALL"]`, `security_opt=["no-new-privileges"]`
- [ ] 8. teardown in a `finally` with `force=True`, plus the `mandala.sandbox` label
- [ ] 9. output truncated **before** it re-enters the model's context (Day 4)

## OAI-19 🛠️ — built

- [ ] `container_kwargs()` is **pure** — can say why that is the most important decision in the file
- [ ] Image pinned by digest, not `:latest`, not a bare tag — can say why (Principle 4)
- [ ] `command` is an **argv list**, never a shell string; `-I -u -B` understood
- [ ] `reap_orphans()` written (the `TODO(me)`) — and I wrote down **start-up vs. explicit chore**
- [ ] `sandbox_mount` added to `MandalaContext` (Day 12's DI, not a module constant)
- [ ] `run_code` calls `permissions.check()` on its **first line**; `audit()` logs length/exit/
      duration but **not** the code body, and I wrote down why
- [ ] `run_in_sandbox` *returns* for bad user code, *raises* for `SandboxUnavailable` (Day 10)

## The permission table (§4.4) — table first, agent second

- [ ] `"run_code"` in `permissions.TOOLS`, `writes=False`, `reads_untrusted=True`
- [ ] `blast_radius` names the **residual kernel-escape risk**, not just the wins
- [ ] Can defend `writes=False` against the obvious objection ("the code can call `open(..,'w')`")
- [ ] New `AGENTS["analyst"]` holds **`run_code` and nothing else**
- [ ] **Granted to no pre-existing agent — and never to the Researcher** (untrusted web, Day 15)
- [ ] `uv run pytest tests/test_permissions.py -q` green; `trifecta_violations()` still `[]`

## The measurement (§4.6) — the deliverable, 0 model requests

- [ ] control: read the mounted log → expected **allowed**, got: **______**
- [ ] network: fetch a URL → expected **refused**, got: **______**
- [ ] write to the read-only mount → expected **refused**, got: **______**
- [ ] write outside the mount (`/etc`) → expected **refused**, got: **______**
- [ ] infinite loop (timeout) → expected **refused**, got: **______**
- [ ] fork bomb (pids) → expected **refused**, got: **______**
- [ ] read `GROQ_API_KEY` → expected **refused**, got: **______**
- [ ] my own 7th attempt (`TODO(me)`): **____________________** predicted **______** got **______**
- [ ] **Score: ___ / ___ as expected**
- [ ] Read the `detail` column — can name the *mechanism* of each refusal (Errno 30, BlockingIOError…)
- [ ] Broke **one** flag and confirmed **exactly one** row went red, then put it back
- [ ] `docker ps -a --filter label=mandala.sandbox` empty after the run

## Honesty about the boundary (§4.8)

- [ ] Can say it plainly: **a container is not a VM; kernel escapes are a real class** — and can name
      what is stopped vs. **bounded** vs. **not stopped**
- [ ] Can say **never mount `/var/run/docker.sock`**, and why it converts this into a root shell
- [ ] Know where this gets better: **Day 67 (AG-18)**, microVM, same battery, stronger boundary

## Tests that must be able to fail

- [ ] `test_the_box_has_no_network` — **flip it:** delete `network_disabled`
- [ ] `test_no_host_environment_is_forwarded` — **the flip-it test of the day**; asserts the whole
      dict, not "key not in env"
- [ ] `test_the_only_mount_is_read_only` — asserts `len(volumes) == 1` *first*
- [ ] `test_nothing_is_mounted_when_no_mount_is_asked_for`
- [ ] `test_the_root_filesystem_is_read_only_and_tmp_is_ephemeral`
- [ ] `test_cpu_memory_and_pids_are_all_capped` — including `memswap_limit == mem_limit`
- [ ] `test_the_box_is_unprivileged` — user, `cap_drop`, `no-new-privileges`, `privileged`
- [ ] `test_code_is_argv_never_a_shell_string`
- [ ] `test_oversized_code_is_refused_before_a_container_exists`
- [ ] `test_the_image_is_pinned_not_latest`
- [ ] `test_output_is_truncated_before_it_reaches_the_model` — fake client, 1 MB of logs
- [ ] `test_the_container_is_removed_even_when_the_run_raises` — **flip it:** move `remove()` out of
      the `finally`
- [ ] `test_run_code_is_in_the_table_with_an_honest_blast_radius`
- [ ] `test_run_code_is_never_held_beside_a_tool_that_reads_untrusted_text` — the grant policy
- [ ] `test_the_researcher_and_resolver_cannot_execute_code`
- [ ] `test_the_lethal_trifecta_is_still_empty_after_adding_code_execution`
- [ ] `test_a_caller_without_the_grant_is_denied`
- [ ] `@needs_docker test_the_control_case_really_runs` — the positive case
- [ ] `@needs_docker test_the_network_is_really_off`
- [ ] `docker` marker registered in `pyproject.toml`; suite green **with and without** a daemon
- [ ] **Every test costs 0 model requests**

## Understanding check — answer out loud

- [ ] Why is `container_kwargs()` being a *pure function* a security decision, not a style one?
- [ ] Why must the timeout be enforced by the host, and why `kill()` rather than `stop()`?
- [ ] Why `memswap_limit`, and what silently breaks without it?
- [ ] Why is a battery of six refusals worthless without the control case?
- [ ] Why does `run_code` get `writes=False` when the code can obviously call `open(..., "w")`?
- [ ] Why must the Researcher never hold `run_code`, given the box would contain it anyway?
- [ ] Why is `:latest` a Principle-4 violation *for a security claim* specifically?
- [ ] What exactly does the paid native sandbox do better, and where does mine win?

## Budget & freshness

- [ ] Model requests logged in `docs/RATE_BUDGET.md` (declared: **~20, Groq**)
- [ ] Noted that `escape_attempts.py` and all 19 tests cost **0** — pure Docker, no provider
- [ ] `docker` 7.2.0: confirmed `network_disabled` + `network_mode="none"` are accepted together
      (or recorded which one I kept: ______________)
- [ ] `docker` 7.2.0: confirmed `pids_limit`, `nano_cpus`, `memswap_limit`, `tmpfs`, `security_opt`,
      and what `container.wait(timeout=)` raises on expiry
- [ ] Confirmed `nobody` exists in the pinned image (`docker run --rm python:3.12-slim id nobody`)
- [ ] `function_tool(name_override=, failure_error_function=)` confirmed in `openai-agents` 0.22.0
- [ ] Harness/sandbox API shape **read** from the live docs (cannot be tested — no key)
- [ ] OAI-20 status checked and dated; any drift logged in `docs/CHANGELOG_PLAN.md` (Principle 14)

## Commit

```bash
./m check
./m done 19
```

- [ ] `./m done 19` succeeded — trackers updated automatically
- [ ] Tomorrow is durable runs (Temporal) + realtime awareness — `uv add "temporalio==1.31.0"` is the
      Day-20 ledger row
