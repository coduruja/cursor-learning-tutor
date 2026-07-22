# Hooks and Agents refactor diagnosis

Status: planning document for branch `cursor/hooks-agents-refactor`.

This document records the current runtime, its concrete problems, and the
recommended refactor order. It does not replace the stable Rules/Skills
ownership map in `LEARNING_TUTOR_RULES_SKILLS_OWNERSHIP.md`. Frozen
compatibility constraints live in `HOOKS_AGENTS_CONTRACTS.md` (Phase A).

## Scope

In scope:

- `hooks/hooks.json`
- `hooks/inject_profile.py`
- `hooks/capture_learning.py`
- `hooks/learning_cli.py`
- `hooks/lib_profile.py`
- `agents/study-researcher.md`
- verification directly related to Hooks and Agents

Out of scope:

- changing the evidence policy for `covered`
- redesigning Rules or Skills
- changing the public CLI commands without a migration plan
- unrelated repository cleanup

## Current runtime

```text
hooks/hooks.json
├── sessionStart
│   └── inject_profile.py
│       ├── loads lib_profile.py
│       ├── installs cli.py + lib_profile.py in ~/.cursor/learning/
│       ├── reads the global profile
│       ├── searches for the project sheet
│       └── emits LEARNING-PROFILE / LEARNING-PROJECT context
│
└── afterAgentResponse
    └── capture_learning.py
        ├── loads lib_profile.py
        ├── reinstalls the stable CLI
        ├── extracts LEARNING-WANT markers
        └── writes queue entries

rules / skills
└── python3 ~/.cursor/learning/cli.py ...
    └── learning_cli.py
        └── lib_profile.py

skills/study-deep
└── agents/study-researcher.md
    └── curated track returned to the main agent
        └── study-probe
```

The repository currently has one Agent, `study-researcher`. “Agents refactor”
therefore means hardening its contract and integration, not designing an Agent
framework.

## Diagnosis

### 1. `lib_profile.py` has too many reasons to change — mitigated in Phase D

Implementation is split under `hooks/learning/` (`paths`, `topics`, `sections`,
`context`, `profile`, `project`, `install`). `lib_profile.py` remains a thin
compatibility shim for Hooks and the installed CLI.

**Remaining risk:** the shim + package must stay in sync during `install_cli`
copies; covered by the install regression test.

### 2. Library loading is duplicated

`inject_profile.py`, `capture_learning.py`, and `learning_cli.py` each implement
dynamic loading with `importlib`. The CLI also has a second fallback location.

**Root cause:** plugin files and the installed stable CLI must run from different
locations, but there is no single bootstrap contract.

**Risk:** loading and error behavior can drift between entry points.

### 3. Installation, injection, and persistence are coupled

`inject_profile.py` installs the CLI and builds context in the same execution.
`capture_learning.py` repeats installation before parsing markers.

**Root cause:** CLI availability is treated as a side effect of lifecycle Hooks
instead of an explicit installation boundary.

**Risk:** an installation failure can silently degrade context injection or
marker capture. The first interaction may also use the marker fallback before
the stable CLI is available.

The exact timing guarantees of `sessionStart` must be validated against the
target Cursor version before relying on installation as a synchronous
precondition.

### 4. Hook failures are intentionally invisible

Both Hook entry points catch every exception and emit only
`{"continue": true}`.

Fail-open behavior is correct—the tutor must not break the Agent loop—but the
current implementation discards the reason for failure.

**Root cause:** runtime safety and observability were treated as mutually
exclusive.

**Risk:** users see missing profile context or missing queue writes with no
diagnostic evidence.

### 5. Marker parsing accepts invalid input — mitigated in Phase C

The `LEARNING-WANT` regex still matches `topic=""`, but `iter_want_markers`
skips empty topics with a stderr diagnostic and continues with later markers.
`read`/`extract` helpers prefer official `text` and keep temporary compat keys.

**Remaining:** narrowing the public payload contract to `text` only can wait
until compat keys are unused in the wild.

### 6. Project discovery has two path semantics

`inject_profile.py` walks up to eight ancestors looking for a project sheet.
CLI project commands default to the current working directory unless `--cwd` is
provided.

**Root cause:** project discovery is implemented independently by the injection
flow and the project persistence flow.

**Risk:** the injected sheet and the sheet updated by a CLI command may differ.

### 7. Stable CLI deployment can drift

The plugin copies `learning_cli.py` and `lib_profile.py` into
`~/.cursor/learning/`. Those copies form a public runtime boundary used by Rules
and Skills.

**Root cause:** deployment is a raw two-file copy with no version or integrity
check.

**Risk:** an old session or partial copy can run a CLI/library pair different
from the active plugin version.

### 8. Automated checks do not exercise Hooks or the Agent

`check_architecture.py` validates Rules/Skills ownership.
`smoke_install.py` checks manifest paths and can copy the CLI, but does not parse
the Hook commands or execute Hook behavior. `verify_scenarios.py` focuses on the
Rules/Skills evidence policy.

There are no checks for:

- official Hook payload parsing
- marker extraction and invalid markers
- fail-open JSON output
- context injection
- installed CLI behavior
- project path consistency
- Agent frontmatter and the `study-deep` → `study-researcher` link

**Root cause:** the 2.4.0 verification phase intentionally centered on the
Rules/Skills refactor.

**Risk:** the next structural refactor has no regression harness.

### 9. The Agent contract is only partially explicit — mitigated in Phase E

`study-researcher` and `study-deep` now share an explicit pass-in / expect-back
contract and a research-only boundary. Smoke/harness checks assert frontmatter,
name linkage, and key boundary phrases.

**Remaining:** live delegation still needs a manual Cursor check in Phase F.

## Refactor principles

1. Preserve behavior before changing structure.
2. Add regression coverage before splitting `lib_profile.py`.
3. Keep Hook entry points thin and fail-open.
4. Log diagnostics without writing them into Agent context.
5. Keep `~/.cursor/learning/cli.py` as the stable public path.
6. Use one implementation for project-root discovery.
7. Give each persistence concern one module owner.
8. Keep the single Agent focused on research; assessment remains with
   `study-probe`.

## Proposed target boundaries

Names are provisional; responsibilities are the important part.

```text
hooks/
├── hooks.json
├── inject_profile.py          # sessionStart adapter only
├── capture_learning.py        # afterAgentResponse adapter only
├── learning_cli.py            # argparse adapter only
└── learning/
    ├── loader.py              # one bootstrap/import contract
    ├── paths.py               # global and project paths
    ├── topics.py              # normalization and anti-noise
    ├── profile.py             # global profile, queue, covered, migration
    ├── project.py             # project sheet operations
    ├── context.py             # bounded context rendering
    └── install.py             # stable CLI deployment
```

This structure is a planning target, not approval to create every module.
Extraction should happen only where tests demonstrate an independent boundary.

`agents/study-researcher.md` remains a single Agent file, with:

- supported frontmatter only
- explicit required input
- stable output contract
- explicit no-assessment boundary
- a checked reference from `study-deep`

## Refactor plan

### Phase A — Freeze contracts — **done**

Deliverable: `.cursor/HOOKS_AGENTS_CONTRACTS.md`

- Documented Hook input/output expectations from the supported Cursor schema.
- Recorded stable CLI commands and paths as compatibility constraints.
- Defined one intended project-root discovery behavior (implement in Phase C).
- Validated Agent frontmatter: `model: inherit` and `readonly: true` are
  supported; left unchanged.

Exit: contracts are written and no runtime behavior has changed.

### Phase B — Build a regression harness — **done**

Deliverables:

- `scripts/test_hooks_agents.py` — WANT parsing, official `text` payload,
  fail-open hooks, temp-HOME profile/project rendering, Agent link
- `scripts/smoke_install.py` — parses `hooks.json`, resolves hook scripts,
  checks `study-researcher` frontmatter + `study-deep` reference

Exit: current intended behavior is executable and failures are reproducible.

### Phase C — Harden adapters without structural extraction — **done**

Deliverables:

- `hooks/hook_io.py` — shared stdin/JSON helpers, stderr diagnostics, lib loader
- Hardened `inject_profile.py` / `capture_learning.py` (validate markers; isolate
  install vs context errors)
- `lib_profile.resolve_project_root` / `find_project_sheet` (contracts §4)

Exit: malformed inputs and runtime failures are observable and isolated.

### Phase D — Extract `lib_profile.py` incrementally — **done**

Deliverable: `hooks/learning/` package with shim `hooks/lib_profile.py`.

| Module | Responsibility |
|---|---|
| `paths.py` | Global/project paths + root discovery |
| `topics.py` | Normalization, aliases, anti-noise |
| `sections.py` | Markdown section read/replace |
| `context.py` | Inject truncation |
| `profile.py` | Global profile / queue / covered |
| `project.py` | Project sheet operations |
| `install.py` | Stable CLI + package copy to `~/.cursor/learning/` |

`lib_profile.py` remains a compatibility re-export. `install_cli` copies the
shim, `cli.py`, and the `learning/` package.

Exit: entry points are thin and no module has unrelated persistence,
installation, and rendering responsibilities.

### Phase E — Harden the Agent integration — **done**

- Kept supported frontmatter (`model: inherit`, `readonly: true`).
- Aligned Agent I/O wording with `study-deep` (pass-in / expect-back).
- Explicit research-only boundary: no probe, no `want`/`covered` writes.
- Strengthened smoke + harness checks for name link and contract phrases.

Exit: delegation has one documented and verified contract.

### Phase F — Release verification

- Run architecture, install, scenario, Hook, CLI, and Agent checks.
- Test a fresh session with no global profile.
- Test a session with global and project context.
- Test valid and invalid `LEARNING-WANT` markers.
- Test `study-deep` → researcher → one-topic probe.
- Update version and changelog only after live verification.

Exit: no silent Hook failure in the tested paths and no Rules/Skills policy
regression.

## Decisions still required

1. Whether Hook diagnostics should use stderr only or also a local log file.
2. Whether the installed runtime should remain flat or become a copied package.
3. Whether installation should use a version stamp or content comparison.
4. Which Cursor versions and operating systems this refactor must support.
5. ~~Whether project discovery should trust Hook workspace metadata, current
   working directory, or both with a documented precedence.~~
   **Decided in Phase A** — see `HOOKS_AGENTS_CONTRACTS.md` §4
   (`--cwd` → `workspace_roots` when present → `cwd`; ancestor walk only for
   injection until Phase C unifies helpers).

Remaining decisions should be made after Phase B exposes the current behavior;
they should not block the initial regression tests.
