# Day 67 — CHECKLIST

**IDs covered:** AG-18 🛠️ (sandboxing & execution isolation) · *replaces Day 19's preview*

## Demo command

```bash
uv run python days/day-67/lab/escape_attempts.py   # 0 model requests — 12 attacks
uv run pytest tests/test_sandbox.py -m sandbox -v
```

Expected: twelve CONTAINED lines, each failing for the reason you predicted.

## Setup

- [ ] `./m start 67` and `./m scaffold 67` run
- [ ] Docker Desktop **running** before starting
- [ ] `docker==7.2.0` confirmed from Day 19
- [ ] **Base image digest pinned** in the Dockerfile *and* in `docs/PINS.md`, with a changelog line
- [ ] **`sandbox` pytest marker added to `pyproject.toml`** before writing tests
- [ ] `./m check` confirmed to **skip** sandbox tests by default
- [ ] Files created (`sandbox.py`, tests, `escape_attempts.py`, `sandbox_notes.md`, Dockerfile)

## The seven controls

- [ ] 1. `network_disabled=True`
- [ ] 2. `environment={}` — **explicitly empty**, not omitted, and can say why that matters
- [ ] 3. `read_only=True` + `tmpfs` with **`noexec`**
- [ ] 4. Timeout enforced **by the caller**, with `kill()` — and can say why an inside timeout is a
      suggestion
- [ ] 5. `mem_limit`, cpu cap, **and `pids_limit`** — and can say what pids stops that the others do not
- [ ] 6. Non-root uid, `cap_drop=["ALL"]`, `no-new-privileges`
- [ ] 7. `remove(force=True)` in a **`finally`**
- [ ] `python -I -S` used, and can say which escape it blocks
- [ ] **`put_archive` used instead of a bind mount**, and can say why it is strictly stronger
- [ ] Output bounded by `MAX_OUTPUT_CHARS`

## The image

- [ ] Base image **digest-pinned**, not tag-pinned
- [ ] Only `pandas` installed — every package is a capability
- [ ] `chmod 555 /work /data` — script cannot be replaced mid-run
- [ ] `USER 10001:10001`
- [ ] `ENTRYPOINT []`
- [ ] Image added to `docs/PINS.md` and the Friday freshness check

## Attacking it

- [ ] All twelve attempts run
- [ ] **Predicted which control stops which attempt, before running**
- [ ] Each failure checked for the **right reason** — not just a non-zero exit
- [ ] `write-tmp-then-exec` contained → `noexec` confirmed
- [ ] `import-shadowing` contained → `-I` and `chmod 555` confirmed
- [ ] `become-root` contained → `cap_drop` confirmed applied
- [ ] `huge-output` recorded as **bounded**, not prevented — distinction noted

## Tests that must be able to fail

- [ ] `test_ordinary_code_works` — the negative-space test
- [ ] `test_no_network`
- [ ] `test_no_credentials_are_visible` — **flip it:** pass `os.environ`, see red
- [ ] `test_the_data_file_is_read_only`
- [ ] `test_the_host_repo_is_not_reachable`
- [ ] `test_an_infinite_loop_is_killed_from_outside` — asserts **both** flags
- [ ] `test_a_fork_bomb_is_capped`
- [ ] `test_output_is_bounded`
- [ ] `test_the_container_does_not_survive`
- [ ] `test_a_crash_still_cleans_up` — the `finally` test
- [ ] `test_the_limits_are_actually_small`
- [ ] `test_the_module_names_its_threat_model`

## `sandbox_notes.md`

- [ ] Attempt table filled, including the "right reason" column
- [ ] **Prevented vs. bounded** list written
- [ ] "What a container does not stop" written
- [ ] Threat model named, and what would move you to a microVM
- [ ] **Day 19 vs. today table filled honestly** — what did the preview actually lack?
- [ ] The surprise recorded

## Understanding check — answer out loud

- [ ] Why not review the generated code?
- [ ] Why is a copied file stronger than a read-only bind mount?
- [ ] Why must the timeout live outside the container?
- [ ] What does `pids_limit` stop that memory and CPU caps do not?
- [ ] Which attacks were prevented and which were merely bounded?
- [ ] When is a hardened container the wrong tool?

## Budget & freshness

- [ ] Logged in `docs/RATE_BUDGET.md`: **0 requests**
- [ ] Rule stated in §2: **days that produce controls cost nothing**
- [ ] `container.wait(timeout=)` raise-vs-return behaviour confirmed for `docker==7.2.0`
- [ ] `nano_cpus` vs. `cpu_quota` parameter confirmed
- [ ] Base image digest recorded and added to the Friday check
- [ ] Any drift logged in `docs/CHANGELOG_PLAN.md`

## Commit

```bash
./m check
./m done 67
```

- [ ] Day 19's sandbox **replaced**, not left beside the new one
- [ ] `./m done 67` succeeded — trackers updated automatically
