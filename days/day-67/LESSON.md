---
day: 67
phase: 10
phase_name: "Safety & security"
title: "Sandboxing for real"
ids: ["AG-18"]
kind: lab
plan_version: "v1.1.0"
generated: "2026-08-20"
status: not-started
lab_scaffolded: false
commit: ""
---

# Day 67 — Sandboxing for real

**Phase 10 · Safety & security** · IDs: **AG-18 🛠️**

> **Yesterday:** credentials scoped per role, and a review checklist calibrated against your own
> server.
> **Today:** the strongest boundary in the plan. Day 19 built a Docker sandbox as OAI-19's free
> replacement for a paid feature; today you make it **actually hold** — no credentials, no network,
> read-only mounts, a hard timeout, and a container that dies whether or not the code inside it
> cooperates. Then you attack it.
> **Tomorrow:** computer use, which has the largest blast radius of anything in this plan.

```bash
./m start 67
./m scaffold 67
```

---

## §1 The story

Yesterday's `credentials.py` said something uncomfortable out loud: **same-process scoping in Python
is a speed bump.** Anything that can `import` can reach. The table at the end of Day 66 §3.3 named the
only real fix — **a process boundary** — and today is when you build one properly.

**This is the day the security story stops being probabilistic.** Every defence so far has been
either a bound (structural, but inside your process) or a prompt (probabilistic). A container with no
network, no credentials and a read-only mount is a different *kind* of control: **it does not matter
what the code inside decides to do.**

**Why Mandala needs it.** Day 19's lab ran agent-generated log-analysis code. The capstone (Days
78–84) will want the same thing: a model writes a small script to answer a question about data, and
running that script is the fastest way to hand an attacker a shell. **AG-18's example is exactly
this:** *generated pandas code sees one CSV; `rm -rf /` kills a box that dies in 30 seconds anyway.*

**The framing that makes today click, and it is the same as Day 65's:** you cannot review generated
code reliably — reviewing it is as hard as writing it, and doing so at agent speed is impossible.
**So you do not review it. You arrange for it not to matter.**

---

## §2 Setup — run this

### 2.1 Check what Day 19 left you

```bash
grep -n 'docker' pyproject.toml
docker --version
docker info 2>/dev/null | head -3 || echo "Docker Desktop not running"
```

- `docker==7.2.0` (the Python SDK) came on **Day 19** per the ledger. Nothing new to install.
- **Docker Desktop must be running.** If it is not, today is a reading day and that is a poor use of
  it — start it before the lesson.

### 2.2 Create today's files

```bash
touch src/mandala/sandbox.py
touch tests/test_sandbox.py
mkdir -p days/day-67/lab
touch days/day-67/lab/escape_attempts.py
touch days/day-67/lab/sandbox_notes.md
touch docker/sandbox.Dockerfile
```

- `src/mandala/sandbox.py` **replaces** Day 19's version rather than sitting beside it. Day 19 was a
  preview and the plan says so (AG-18: *"preview 19"*). **One sandbox, hardened.**

---

## §3 The seven controls

### 3.1 What actually needs to be true

| # | Control | Stops | Cheap? |
|---|---|---|---|
| 1 | **No network** | exfiltration, downloading a payload | yes — one flag |
| 2 | **No credentials** | using your keys | yes — pass no environment |
| 3 | **Read-only mount, one file** | reading or corrupting your repo | yes |
| 4 | **Hard timeout, enforced outside** | infinite loops, crypto mining | yes |
| 5 | **Memory and CPU caps** | a fork bomb taking the host down | yes |
| 6 | **Non-root user** | container-escape severity | yes |
| 7 | **Destroyed after, always** | state leaking between runs | yes |

**Every one is a flag or two, and that is the point of today.** The controls are cheap; what is
expensive is *knowing which ones you need* and *proving they hold*. §5 is the proof.

**Note what is absent from that list:** reading the generated code, static analysis, an allowlist of
imports. **Those are probabilistic and they are how people spend a week building something a
container does in seven flags.**

### 3.2 `src/mandala/sandbox.py`

```python
"""Run agent-generated code where it cannot matter. Replaces Day 19's preview.

The premise
-----------
You cannot reliably review generated code -- reviewing is as hard as writing, and at
agent speed it is impossible. So do not review it. Arrange for it not to matter.

Seven controls, each a flag or two. The controls are cheap; knowing which you need
and PROVING they hold is the work (see tests/test_sandbox.py and escape_attempts.py).

What this is NOT
----------------
A container is not a VM. A kernel exploit escapes it. For Mandala -- local, one
developer, generated pandas over a fixture CSV -- a hardened container is the right
level. For untrusted code from strangers at scale, you want a microVM (gVisor,
Firecracker). Say which threat model you are in; the answer changes the tool.

Usage
-----
    >>> run_sandboxed("print(open('/data/input.csv').read()[:20])", Path("fixture.csv"))
    SandboxResult(ok=True, stdout='ticket_id,summary\\n', ...)
"""

from __future__ import annotations

import tarfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Final

import docker

IMAGE: Final = "mandala-sandbox:1"
TIMEOUT_S: Final = 30
MEM_LIMIT: Final = "256m"
CPU_QUOTA: Final = 50_000          # 50% of one core (period is 100_000)
PIDS_LIMIT: Final = 64
MAX_OUTPUT_CHARS: Final = 8_000


@dataclass(frozen=True)
class SandboxResult:
    ok: bool
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool


def run_sandboxed(code: str, data_file: Path, *, timeout_s: int = TIMEOUT_S) -> SandboxResult:
    """Run `code` with `data_file` read-only at /data/input.csv. Nothing else."""
    client = docker.from_env()
    container = client.containers.create(
        IMAGE,
        command=["python", "-I", "-S", "/work/script.py"],
        network_disabled=True,                 # 1. no network
        environment={},                        # 2. no credentials
        user="10001:10001",                    # 6. non-root
        read_only=True,                        # 3. read-only root filesystem
        tmpfs={"/tmp": "size=16m,noexec"},     #    a writable scratch that cannot execute
        mem_limit=MEM_LIMIT,                   # 5. memory cap
        nano_cpus=int(CPU_QUOTA * 10_000),     # 5. cpu cap
        pids_limit=PIDS_LIMIT,                 # 5. fork-bomb cap
        cap_drop=["ALL"],                      # 6. drop every capability
        security_opt=["no-new-privileges:true"],
        detach=True,
    )
    try:
        _put(container, "/work/script.py", code.encode())
        _put(container, "/data/input.csv", data_file.read_bytes())
        container.start()
        try:
            status = container.wait(timeout=timeout_s)      # 4. timeout, enforced by US
            timed_out = False
            exit_code = int(status.get("StatusCode", 1))
        except Exception:
            container.kill()
            timed_out, exit_code = True, 124

        stdout = container.logs(stdout=True, stderr=False).decode(errors="replace")
        stderr = container.logs(stdout=False, stderr=True).decode(errors="replace")
        return SandboxResult(
            ok=(exit_code == 0 and not timed_out),
            stdout=stdout[:MAX_OUTPUT_CHARS],
            stderr=stderr[:MAX_OUTPUT_CHARS],
            exit_code=exit_code,
            timed_out=timed_out,
        )
    finally:
        container.remove(force=True)           # 7. destroyed, ALWAYS


def _put(container, path: str, payload: bytes) -> None:
    """Copy bytes in without a bind mount -- nothing on the host is exposed."""
    stream = BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as tar:
        info = tarfile.TarInfo(name=Path(path).name)
        info.size = len(payload)
        info.mode = 0o444
        tar.addfile(info, BytesIO(payload))
    stream.seek(0)
    container.put_archive(str(Path(path).parent), stream.getvalue())
```

**Line by line:**

- **`command=["python", "-I", "-S", ...]`** — `-I` is *isolated mode*: no `PYTHONPATH`, no user site
  directory, and the script's own directory is not prepended to `sys.path`. `-S` skips `site`. **Two
  flags that stop the most boring escape of all**: dropping a `numpy.py` next to the script and having
  it imported instead of the real one.
- `network_disabled=True` — **control 1, and the single most important flag.** Without a network,
  exfiltration requires the output channel you control, and downloading a payload is impossible.
- `environment={}` — **control 2, explicitly empty rather than omitted.** Writing `{}` says *"I
  decided this"*; omitting it says *"I did not think about it"*, and they behave the same until
  someone adds a default.
- `user="10001:10001"` and `cap_drop=["ALL"]` — **control 6.** A high uid that does not exist in the
  image, and every Linux capability dropped. `no-new-privileges` stops setuid binaries regaining any.
- `read_only=True` plus `tmpfs={"/tmp": "size=16m,noexec"}` — **control 3, and the `noexec` matters:**
  a writable `/tmp` without it lets generated code write a binary and run it.
- `pids_limit=64` — **the fork-bomb cap**, and it is the one people leave out. Memory and CPU caps do
  not stop `while True: os.fork()` from exhausting the host's process table.
- **`container.wait(timeout=...)` then `container.kill()` — control 4, enforced from outside.** A
  timeout inside the sandboxed script is a suggestion the script can ignore. **The only timeout that
  counts is the one the code cannot see.** `124` mirrors GNU `timeout`'s exit code, which is a small
  courtesy to anyone reading logs.
- **`finally: container.remove(force=True)` — control 7, and `finally` is load-bearing.** A container
  that survives an exception is state leaking between runs and a resource leak; `force=True` removes
  it even if it is still running.
- **`_put` via `put_archive` rather than a bind mount** — **this is the subtle one.** A bind mount
  exposes a host path to the container; even read-only, it is a real path and a container escape sees
  your filesystem layout. Copying bytes in means **nothing on the host is reachable at all**, which is
  strictly stronger and costs ten lines.
- `info.mode = 0o444` — the copied files are read-only inside too.
- `MAX_OUTPUT_CHARS` — **the output is the one channel out**, so it is bounded. Generated code that
  prints a gigabyte is a denial of service against your own log pipeline, and a model reading the
  result has AG-04's budget (twelfth appearance).
- **The "what this is NOT" paragraph**, same discipline as yesterday's `credentials.py`. **A container
  is not a VM.** Name the threat model you are in and the level that suits it.

### 3.3 `docker/sandbox.Dockerfile`

```dockerfile
# The smallest thing that can run generated pandas. Rebuilt rarely, pinned always.
FROM python:3.12-slim@sha256:<pin-the-digest>

RUN pip install --no-cache-dir "pandas==2.3.2" && \
    useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin sandbox && \
    mkdir -p /work /data && chown root:root /work /data && chmod 555 /work /data

USER 10001:10001
WORKDIR /work
ENTRYPOINT []
```

**Line by line:**

- **`@sha256:<digest>` — pin the digest, not just the tag.** `python:3.12-slim` moves; a digest does
  not. **This is Principle 4 applied to a base image**, and it is the version of "pin everything" most
  people skip. Get the digest with `docker inspect --format='{{index .RepoDigests 0}}' python:3.12-slim`.
- `pandas` pinned, and **nothing else installed.** Every package in this image is a capability
  available to generated code. **No `requests`, no `httpx`, no `boto3`** — and with the network
  disabled they would be useless anyway, which is a nice consistency check on your own reasoning.
- `--no-cache-dir` — smaller image, and no pip cache for generated code to poke at.
- `chmod 555 /work /data` — the directories are **not writable by the sandbox user**, so the copied
  script cannot be replaced mid-run and nothing new can be dropped beside it.
- `ENTRYPOINT []` — no inherited entrypoint; the command is given explicitly at `create` time, so
  there is no surprising indirection.
- **Rebuild rarely.** Add the digest and the pandas pin to `docs/PINS.md`; a sandbox image is a
  dependency like any other and the Friday check should cover it.

---

## §4 `days/day-67/lab/escape_attempts.py` — attack your own sandbox

**A sandbox you have not attacked is a sandbox you are hoping about.**

```python
"""Try to break out. Every attempt should fail; the interesting part is HOW.

Run:
    uv run python days/day-67/lab/escape_attempts.py

Budget: 0 model requests. These are hand-written attacks, not generated ones --
you want deterministic attempts, not creative ones.
"""

from pathlib import Path

from mandala.sandbox import run_sandboxed

FIXTURE = Path("tests/fixtures/tickets.csv")

ATTEMPTS = {
    "network-egress": "import urllib.request; print(urllib.request.urlopen('http://example.com').status)",
    "read-env": "import os; print(dict(os.environ))",
    "read-host-fs": "print(open('/etc/passwd').read()[:100])",
    "escape-upward": "import pathlib; print(list(pathlib.Path('/').iterdir()))",
    "write-anywhere": "open('/work/evil.py','w').write('x')",
    "write-tmp-then-exec": (
        "open('/tmp/e.sh','w').write('echo pwned'); import os,stat;"
        "os.chmod('/tmp/e.sh',0o755); print(os.system('/tmp/e.sh'))"
    ),
    "infinite-loop": "while True: pass",
    "fork-bomb": "import os\nwhile True: os.fork()",
    "memory-hog": "x = bytearray(1024*1024*1024)",
    "huge-output": "print('A' * 50_000_000)",
    "import-shadowing": "open('/work/json.py','w').write('BAD'); import json; print(json.__file__)",
    "become-root": "import os; os.setuid(0); print(os.getuid())",
}

for name, code in ATTEMPTS.items():
    result = run_sandboxed(code, FIXTURE, timeout_s=10)
    verdict = "CONTAINED" if not result.ok else "!! SUCCEEDED !!"
    detail = (result.stderr or result.stdout).strip().splitlines()[-1:] or [""]
    print(f"{name:<22} {verdict:<16} exit={result.exit_code} "
          f"timeout={result.timed_out}  {detail[0][:60]}")
```

**Line by line:**

- **Twelve attempts, one per control plus the interesting combinations.** Each maps to a row in §3.1
  and **you should be able to say which control stops which attempt before running.**
- `"write-tmp-then-exec"` — the combination attack. `/tmp` is writable (you need scratch space), so the
  question is whether `noexec` holds. **If this one succeeds, your tmpfs flag is wrong**, and it is
  exactly the kind of thing that is easy to get subtly wrong.
- `"import-shadowing"` — writes `json.py` into the working directory hoping Python imports it. **`-I`
  and `chmod 555` are the two defences and this attempt tests both.** It is the least dramatic attack
  here and the most likely to work in a carelessly-built sandbox.
- `"become-root"` — should fail with `EPERM` because `cap_drop=["ALL"]` removed `CAP_SETUID`. **If it
  succeeds, `cap_drop` is not applied** and several other controls are weaker than you think.
- `"huge-output"` — tests `MAX_OUTPUT_CHARS`, and note it should be *contained* rather than *blocked*:
  the code runs, the output is truncated. **Distinguish "prevented" from "bounded" in your notes.**
- **`"CONTAINED" if not result.ok`** is a deliberately crude verdict, and it is worth being precise
  about: a non-zero exit means the attempt failed *somehow*. **Read the detail line** — an attempt that
  failed because of a typo in your attack string is not evidence of containment. **Check that each
  failure has the reason you expected.**
- **Hand-written attacks, not model-generated ones.** You want a deterministic, repeatable suite that
  Day 74's CI can run; creative attacks are Day 69's red-team day.

---

## §5 The eval that must be able to fail

```python
# tests/test_sandbox.py
"""A sandbox is only as good as its proof. These tests need Docker."""

from pathlib import Path

import pytest

from mandala.sandbox import (
    MAX_OUTPUT_CHARS,
    MEM_LIMIT,
    PIDS_LIMIT,
    TIMEOUT_S,
    run_sandboxed,
)

FIXTURE = Path("tests/fixtures/tickets.csv")
pytestmark = pytest.mark.sandbox        # excluded from ./m check unless Docker is up


def test_ordinary_code_works():
    """The negative-space test: a sandbox that blocks everything is not a sandbox."""
    out = run_sandboxed("print(open('/data/input.csv').read()[:12])", FIXTURE)
    assert out.ok, out.stderr
    assert out.stdout.strip()


def test_no_network():
    out = run_sandboxed(
        "import urllib.request; urllib.request.urlopen('http://example.com', timeout=3)",
        FIXTURE)
    assert not out.ok


def test_no_credentials_are_visible():
    """THE test. Flip it: pass environment=os.environ and watch this go red."""
    out = run_sandboxed("import os; print(list(os.environ))", FIXTURE)
    for banned in ("GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", "PATH_TO_SECRET"):
        assert banned not in out.stdout


def test_the_data_file_is_read_only():
    out = run_sandboxed("open('/data/input.csv','w').write('x')", FIXTURE)
    assert not out.ok


def test_the_host_repo_is_not_reachable():
    """put_archive, not a bind mount: there is no host path to find."""
    out = run_sandboxed("import pathlib; print([p.name for p in pathlib.Path('/').iterdir()])",
                        FIXTURE)
    assert "src" not in out.stdout and "pyproject.toml" not in out.stdout


def test_an_infinite_loop_is_killed_from_outside():
    out = run_sandboxed("while True: pass", FIXTURE, timeout_s=5)
    assert out.timed_out
    assert out.exit_code == 124


def test_a_fork_bomb_is_capped():
    out = run_sandboxed("import os\nwhile True: os.fork()", FIXTURE, timeout_s=10)
    assert not out.ok


def test_output_is_bounded():
    out = run_sandboxed("print('A' * 5_000_000)", FIXTURE)
    assert len(out.stdout) <= MAX_OUTPUT_CHARS


def test_the_container_does_not_survive():
    """Control 7. Flip it: drop the finally block and watch containers accumulate."""
    import docker

    client = docker.from_env()
    before = len(client.containers.list(all=True))
    run_sandboxed("print(1)", FIXTURE)
    assert len(client.containers.list(all=True)) == before


def test_a_crash_still_cleans_up():
    import docker

    client = docker.from_env()
    before = len(client.containers.list(all=True))
    run_sandboxed("raise SystemExit(3)", FIXTURE)
    assert len(client.containers.list(all=True)) == before


def test_the_limits_are_actually_small():
    """Judgements, pinned. Change them deliberately, not by drift."""
    assert TIMEOUT_S <= 60
    assert MEM_LIMIT.endswith("m") and int(MEM_LIMIT[:-1]) <= 512
    assert PIDS_LIMIT <= 128


def test_the_module_names_its_threat_model():
    doc = Path("src/mandala/sandbox.py").read_text(encoding="utf-8")
    assert "not a VM" in doc and "microvm" in doc.lower()
```

**Line by line:**

- `pytestmark = pytest.mark.sandbox` — **a new marker, and it needs a `pyproject.toml` entry** beside
  `live` and `cassette` (Day 0). These tests need Docker running, so they must not break `./m check`
  on a machine without it. **Add the marker declaration today**, or `./m check` starts warning.
- `test_ordinary_code_works` is the **negative-space test**, and its docstring is the reason: a sandbox
  that fails everything passes every other test on this page. **Eighth appearance of this pattern.**
- `test_no_credentials_are_visible` is the headline flip-it, and the mutation it names — passing
  `os.environ` through — is what someone does when a script needs "just one variable".
- `test_the_host_repo_is_not_reachable` proves the `put_archive` choice was worth ten lines. **If you
  had used a bind mount, this test would be much harder to satisfy.**
- `test_an_infinite_loop_is_killed_from_outside` asserts **both** `timed_out` and the exit code, so a
  container that merely exited on its own would not pass.
- `test_a_crash_still_cleans_up` is the `finally` block's test, and it is the one that catches a
  refactor moving `remove()` into the happy path.
- `test_the_module_names_its_threat_model` — second day running for the honesty test. **When a
  disclaimer is load-bearing, assert it.**

---

## §6 `days/day-67/lab/sandbox_notes.md`

```markdown
# Sandbox — 2026-08-__

## Escape attempts
| attempt | control it tests | contained? | failed for the RIGHT reason? |
|---|---|---|---|

## Prevented vs. bounded
<which attacks were impossible, and which merely capped? huge-output was bounded, not
 prevented -- list the others>

## What a container does not stop
<kernel exploits; a malicious base image; anything I install into the image; the output
 channel itself>

## The threat model I am in
<local, one developer, generated pandas over a fixture. What would move me to gVisor
 or Firecracker?>

## Day 19 vs. today
| control | Day 19's preview | today |
|---|---|---|
<what did the preview actually lack? be specific -- this is the honest measure of the day>

## The one that surprised me
```

**The "Day 19 vs. today" table is the day's real deliverable.** Day 19 built something that *looked*
like a sandbox under time pressure, as OAI-19's free replacement. **Diff it honestly.** If Day 19 had
a bind mount, inherited the environment, or timed out from inside, say so — **that gap is the lesson,
and pretending the preview was already fine wastes it.**

---

## §7 Traps

- **A bind mount instead of copying bytes in.** Exposes a host path; `put_archive` costs ten lines.
- **A timeout inside the script.** The code can ignore it. Enforce from outside.
- **`environment` omitted rather than `{}`.** Behaves the same until it does not.
- **No `pids_limit`.** Memory and CPU caps do not stop a fork bomb.
- **Writable `/tmp` without `noexec`.** Write a binary, run it.
- **Running as root inside.** Every escape becomes worse.
- **`remove()` outside a `finally`.** Containers accumulate; a crash leaks state between runs.
- **An unpinned base image.** `python:3.12-slim` moves. Pin the digest.
- **Extra packages in the image.** Every one is a capability for generated code.
- **Not attacking it.** A sandbox you have not attacked is a hope.
- **Reading "not ok" as "contained".** Check each failure failed for the reason you expected.
- **Claiming VM-grade isolation.** Name the threat model.

---

## §8 Request budget

**Declared: 0 model requests.**

| What | Requests |
|---|---|
| Everything today | **0** |

**Eighth free day.** The pattern is now firm enough to state as a rule in `RATE_BUDGET.md` §2:
**every day whose output is a *control* rather than a *behaviour* has cost nothing.** Injection
analysis, credential scoping, protocol work, decisions and sandboxing — all free. **The whole of
Phase 10 will cost less than one Phase-5 day.**

---

## §9 Verify before you code

- **Docker Desktop running**, and `docker info` clean.
- **Pin the base image digest** — get it, put it in the Dockerfile *and* in `docs/PINS.md`, with a
  ledger row and a changelog line (Principle 4 does not stop at PyPI).
- **`docker==7.2.0`** still pinned and installed from Day 19.
- **Does `container.wait(timeout=)` raise or return** on timeout in 7.2.0? §3.2's `except` depends on
  it, and getting it wrong means your timeout silently does not fire.
- **Is `nano_cpus` the right parameter** in this SDK version, or is it `cpu_quota`/`cpu_period`?
- **Add the `sandbox` pytest marker to `pyproject.toml`** before writing the tests, or `./m check`
  warns about an unknown marker.
- **Does `./m check` skip sandbox tests by default?** It must, or the check fails on any machine
  without Docker — including Day 74's CI, unless you give CI a Docker service deliberately.

---

## §10 Say it in an interview

> "You can't reliably review generated code — reviewing is as hard as writing, and at agent speed it's
> impossible — so I don't review it, I arrange for it not to matter. Seven controls, each a flag or
> two: no network, no environment at all, a read-only root with a noexec tmpfs, a hard timeout
> enforced from outside the container, memory, CPU and **pid** caps, a non-root user with every
> capability dropped, and removal in a `finally` so a crash can't leak state between runs. Two details
> I'd call out. First, I copy the script and the data file in with `put_archive` instead of using a
> bind mount, because even a read-only mount exposes a real host path — copying means there's nothing
> on the host to find, and there's a test asserting the repo isn't visible from inside. Second, the
> timeout is enforced by the caller: a timeout inside the sandboxed script is a suggestion the script
> can ignore. Then I attacked it with twelve hand-written escapes, one per control plus the
> combinations — writing to tmpfs and then executing it, shadowing an import, calling setuid — and I
> checked that each one failed *for the reason I expected*, because a non-zero exit only tells you it
> failed somehow. And the module documents that a container is not a VM: a kernel exploit escapes it,
> and for untrusted code from strangers at scale you'd want a microVM. Naming the threat model is part
> of the control."

---

## §11 Done when

Tick every box in `CHECKLIST.md`, then:

```bash
./m check
./m done 67
```
