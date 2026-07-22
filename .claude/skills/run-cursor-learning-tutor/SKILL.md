---
name: run-cursor-learning-tutor
description: Run, drive, and screenshot-equivalent-verify the Learning Tutor Cursor plugin — its sessionStart/afterAgentResponse hooks and its CLI. Use when asked to run this plugin, test its hooks, exercise its CLI, simulate a Cursor session, or check the Live Cursor checklist from scripts/verify_release.py.
---

Learning Tutor is a Cursor plugin with **no window and no server**. Its only
runtime surface is two Hooks (JSON on stdin → JSON on stdout, wired via
`hooks/hooks.json`) plus a small CLI they install to `~/.cursor/learning/`.
Drive it with `.claude/skills/run-cursor-learning-tutor/driver.py`, which
invokes that exact hook/CLI surface with `HOME` redirected to a sandbox — the
real `~/.cursor/learning/profile.md` on the dev machine is never touched.

All paths below are relative to the repo root.

## Prerequisites

Just `python3` on PATH (stdlib only, no deps to install).

```bash
python3 -V
# → Python 3.14.6 (any Python 3.9+ works; the plugin itself only needs 3.x)
```

## Build

None — it's Python source + Markdown rules/skills, nothing to compile.

## Run (agent path)

The driver shares one sandbox `HOME` across calls so profile state persists
between them (default: `$TMPDIR/learning-tutor-driver-sandbox`; override with
`--home` or `$LEARNING_TUTOR_DRIVER_HOME`). It refuses to run if `--home`
ever resolves to your real `$HOME`.

```bash
D=.claude/skills/run-cursor-learning-tutor/driver.py

# 1. sessionStart hook: installs the CLI into the sandbox HOME, returns the
#    additional_context Cursor would inject (LEARNING-PROFILE / LEARNING-PROJECT)
python3 "$D" --fresh session

# 2. Point it at an isolated, EXISTING, empty project dir (must already exist
#    on disk or the hook silently falls back to this repo's own project.md —
#    see Gotchas):
mkdir -p /tmp/some-project
python3 "$D" session --workspace-root /tmp/some-project
# → additional_context says no .cursor/learning/project.md found + how to create one

# 3. afterAgentResponse hook: scans response text for LEARNING-WANT markers
python3 "$D" capture --text 'A PR is a change proposal.<!-- LEARNING-WANT topic="Docker" note="for deploy" -->'
# → {"continue": true}   (queue entry written to the sandbox profile)

# 4. CLI passthrough (installed by step 1/3; auto-installs if missing)
python3 "$D" cli show
python3 "$D" cli want --topic "pull request" --note "alias check"
python3 "$D" cli covered --topic "Closures" --level intermediate --note "reviewed"
python3 "$D" cli done --topic "Docker"

# 5. Per-project sheet (separate file, keyed by --cwd)
python3 "$D" cli project-sync --stack "Next.js;Prisma" --candidates "App Router;Prisma migrations" --cwd /tmp/some-project
python3 "$D" project-show --cwd /tmp/some-project

# 6. Prove the real profile was never touched
python3 "$D" verify-clean
# → prints sha256 of ~/.cursor/learning/profile.md; diff it before/after a session

# 7. Wipe the sandbox
python3 "$D" reset
```

| driver command | what it does |
|---|---|
| `session [--workspace-root DIR]...` | Runs `hooks/inject_profile.py`; installs CLI, prints injected context |
| `capture --text "..."` / `--stdin` | Runs `hooks/capture_learning.py` against response text |
| `cli <args...>` | Passthrough to the installed `~/.cursor/learning/cli.py` |
| `project-show --cwd DIR` | Shortcut for `cli project-show --cwd DIR` |
| `verify-clean` | Hashes the real profile.md; refuses if sandbox == real HOME |
| `reset` | Deletes the sandbox HOME |

## Run (human path)

There is no interactive human path outside the actual Cursor app — install
the plugin from the marketplace (`.cursor-plugin/marketplace.json`) or copy
files per `README.md` → "Direct copy", then open a new Cursor chat so
`sessionStart` installs the CLI for real.

## Test

```bash
python3 scripts/verify_release.py
```

Runs `check_architecture.py`, `smoke_install.py`, `verify_scenarios.py`, and
`test_hooks_agents.py` (23 unittest cases, all using temp-HOME isolation
already) — all PASS as of this writing. It also prints a "Live Cursor
checklist" of things that can't be simulated outside the real app; the driver
above exercises every item on that checklist except the two `/study-deep`
Agent-routing bullets (those need a live Cursor Agent chat).

## Gotchas

- **A nonexistent `--workspace-root` is silently ignored, and the fallback
  walks up to 8 ancestor directories.** `resolve_project_root` only honors
  the first `--workspace-root` entry that *exists on disk*; otherwise it
  falls through to `Path.cwd()` (the repo root, since the driver runs hooks
  with `cwd=ROOT`), and `find_project_sheet(..., walk_ancestors=True)` then
  climbs looking for `.cursor/learning/project.md` — which finds **this
  repo's own** project sheet, not a "no project.md" response. To see the
  genuine "no project.md" response, `mkdir -p` the workspace-root dir first
  (so it's honored) and make sure it has no project.md of its own.
- **The CLI only exists after a hook installs it.** `cli.py` isn't checked
  into the sandbox HOME up front; `driver.py cli ...` runs `session` once
  first if `~/.cursor/learning/cli.py` is missing, mirroring what
  `sessionStart` does for a real fresh Cursor install.
- **Hooks always emit `{"continue": true}` on failure** (fail-open by
  design, see `hooks/hook_io.py:emit_fail_open`) — a broken hook won't show
  up as a nonzero exit or JSON error, only as a stderr line the driver
  forwards. Check stderr, not just the exit code, when something seems off.
- **`covered`/`want` silently no-op on generic topics.** `cli covered --topic code` or `--topic python` prints
  `Ignored (generic topic / base language): ...` and writes nothing —
  `learning/topics.py`'s `GENERIC_TOPICS`/`BASE_LANGUAGES` filters, not a bug.

## Troubleshooting

- **`REFUSING: --home resolves to the real HOME`**: you passed `--home ~` or
  similar. Use a sandbox path (the default is already safe) — this guard
  exists specifically so the real `~/.cursor/learning/profile.md` can't be
  clobbered by accident.
- **`hook did not emit JSON`**: the hook crashed before printing anything
  (rare — both hooks catch all exceptions and fail-open). Check the stderr
  the driver already forwarded for the real traceback line.
