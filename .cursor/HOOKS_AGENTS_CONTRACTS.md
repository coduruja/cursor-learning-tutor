# Hooks and Agents — frozen contracts (Phase A)

Status: frozen for branch `cursor/hooks-agents-refactor`.
Source of platform schema: [Cursor Hooks docs](https://cursor.com/docs/hooks)
and [Cursor Subagents docs](https://cursor.com/docs/subagents) (retrieved 2026-07-21).

This file freezes **compatibility constraints**. Later phases may change
implementation, but must preserve these contracts unless this document is
updated first. No runtime behavior was changed in Phase A.

Related docs:

- Ownership map: `LEARNING_TUTOR_RULES_SKILLS_OWNERSHIP.md`
- Diagnosis / plan: `HOOKS_AGENTS_REFACTOR_DIAGNOSIS.md`

---

## 1. Hook registration

Plugin ships:

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [
      { "command": "python3 \"$CURSOR_PLUGIN_ROOT/hooks/inject_profile.py\"" }
    ],
    "afterAgentResponse": [
      { "command": "python3 \"$CURSOR_PLUGIN_ROOT/hooks/capture_learning.py\"" }
    ]
  }
}
```

Constraints:

- `$CURSOR_PLUGIN_ROOT` is required for marketplace/plugin install.
- Commands are fail-open by default (non-zero exit must not break the agent
  loop). This plugin also catches exceptions and prints JSON.
- Cloud agents and Cursor CLI have incomplete lifecycle-hook coverage;
  do not assume these two hooks always run outside the IDE Agent chat.

---

## 2. `sessionStart` — official I/O vs current behavior

### Official schema

Input:

```json
{
  "session_id": "<unique session identifier>",
  "is_background_agent": true,
  "composer_mode": "agent"
}
```

(`composer_mode`: `"agent" | "ask" | "edit"`.)

Output:

```json
{
  "env": { "<key>": "<value>" },
  "additional_context": "<context to add to conversation>"
}
```

Docs state: runs as **fire-and-forget**; the agent loop does not wait for or
enforce a blocking response. Use for session env vars and/or injected context.

### Current plugin behavior (`inject_profile.py`) — Phase C

| Aspect | Behavior |
|---|---|
| Stdin | Parsed as JSON when possible; reads `workspace_roots` when present |
| Side effect | `install_cli` runs in its own try/except; failure logs to stderr and does not block context |
| Project sheet | `find_project_sheet(..., walk_ancestors=True)` after `resolve_project_root` |
| Stdout | `{"continue": true, "additional_context": "..."}` (`continue` kept as fail-open convention) |
| Fail-open | Outer handler + `hook_io.log_diag` on stderr |

Compatibility note: IDE reports exist where `additional_context` is accepted but
not always surfaced to the model (race). Do not remove CLI install as a side
effect of sessionStart solely because injection is best-effort.

---

## 3. `afterAgentResponse` — official I/O vs current behavior

### Official schema

Input:

```json
{
  "text": "<assistant final text>"
}
```

Output: no fields currently documented for this event (observe-only).

### Current plugin behavior (`capture_learning.py`) — Phase C

| Aspect | Behavior |
|---|---|
| Payload parsing | Canonical `text`; temporary compat keys via `hook_io.extract_response_text` |
| Markers | Empty topics skipped with stderr diag; valid markers still applied |
| Persistence | `add_want` per validated topic; per-topic errors do not abort the loop |
| Side effect | `install_cli` isolated from capture errors |
| Stdout | `{"continue": true}` |
| Diagnostics | `learning-tutor: …` on stderr only |

---

## 4. Project-root discovery (implemented)

Shared helpers in `lib_profile.py`:

1. Prefer explicit `cwd` / `--cwd`.
2. Else prefer the first existing absolute path in `workspace_roots`.
3. Else use `Path.cwd()`.
4. Resolve `.cursor/learning/project.md`, with legacy `.cursor/learning-project.md`.
5. Ancestor walk (up to 8) only when `find_project_sheet(..., walk_ancestors=True)`
   — used by sessionStart injection. CLI writes keep `walk_ancestors=False`.

---

## 5. Stable CLI paths and commands

### Paths (public)

| Path | Role |
|---|---|
| `~/.cursor/learning/cli.py` | Stable entrypoint referenced by Rules/Skills |
| `~/.cursor/learning/lib_profile.py` | Library copied next to the CLI |
| `~/.cursor/learning/profile.md` | Global profile (meta, queue, covered) |
| `<project>/.cursor/learning/project.md` | Per-repo sheet (stack, candidates, last probe) |

Install source (plugin tree): `hooks/learning_cli.py`, `hooks/lib_profile.py`
(shim), and `hooks/learning/` (implementation package). `install_cli` copies all
three into `~/.cursor/learning/`.

### Commands (public argv contract)

Do not rename or remove without a migration note in this file:

```text
python3 ~/.cursor/learning/cli.py init [--level ...] [--focus ...]
python3 ~/.cursor/learning/cli.py covered --topic ... [--level ...] [--note ...]
python3 ~/.cursor/learning/cli.py want --topic ... [--note ...]
python3 ~/.cursor/learning/cli.py done --topic ...
python3 ~/.cursor/learning/cli.py show
python3 ~/.cursor/learning/cli.py queue-next
python3 ~/.cursor/learning/cli.py project-show [--cwd ...]
python3 ~/.cursor/learning/cli.py project-sync [--stack ...] [--candidates ...] [--probe-summary ...] [--cwd ...]
python3 ~/.cursor/learning/cli.py project-drop --topic ... [--cwd ...]
```

### Feedback strings (known mismatch — freeze both sides for now)

| Source | Success strings |
|---|---|
| Rule `learning-recording.mdc` | `Saved to profile: …` / `Saved to queue: …` |
| CLI (`add_covered` / `add_want`) | `Saved to profile (covered): …` / `Saved to profile (queue): …` |

Phase A does **not** change either side. Align in a later phase with tests so
agents still recognize “Already in queue” / “Ignored”.

Other stable CLI replies to preserve: `Already in queue:`, `Already covered
recently:`, `Ignored (generic topic / base language):`, `Marked done in queue:`,
`Not found in queue:`.

---

## 6. Marker fallback contract

When the stable CLI is missing, the recording policy may emit:

```text
<!-- LEARNING-WANT topic="TOPIC" note="context" -->
```

Constraints:

- Queue only (`want`).
- No `covered` marker.
- Historical `LEARNING-LOG` must not be reintroduced.
- Hook capture is best-effort; if the hook does not run (CLI/cloud gaps), the
  marker is inert — Rules already say not to claim a save in that case.

---

## 7. Agent `study-researcher` — integration contract (Phase E)

File: `agents/study-researcher.md`  
Delegated from: `skills/study-deep/SKILL.md` (string name `study-researcher`)

### Frontmatter

```yaml
name: study-researcher
description: ...
model: inherit
readonly: true
```

| Field | Verdict |
|---|---|
| `name` | Must stay equal to Skill delegation string |
| `description` | Drives auto-delegation |
| `model: inherit` | Keep; match parent reasoning |
| `readonly: true` | Keep; no file/profile mutation |
| `is_background` | Omit unless deep-study becomes async |

### Behavioral boundary

- Input: topic + level (+ optional project stack context).
- Output: curated track markdown only (≤5 items: starting point, track, signals).
- Must **not** score probes or write `covered` / `want`.
- `study-deep` always hands off to one-topic `study-probe` after the track.

Verified by `scripts/smoke_install.py` (`check_agent`) and
`scripts/test_hooks_agents.py` (`AgentLinkTests`).

---

## 8. What Phase A explicitly did not change

- No edits to `hooks/*.py`, `agents/*.md`, or Skills bodies for behavior.
- No module split of `lib_profile.py`.
- No README / marketplace / feedback-string fixes (tracked for later phases).
- No new automated tests (Phase B).

Exit criterion met: contracts are written; runtime behavior unchanged.

## Phase B harness

```bash
python3 scripts/test_hooks_agents.py
python3 scripts/smoke_install.py
```

## Phase C notes

Adapters are hardened via `hooks/hook_io.py` without splitting `lib_profile.py`.
Empty `LEARNING-WANT` topics are skipped (stderr) so later valid markers still
persist. Project discovery helpers live in `lib_profile` (`resolve_project_root`,
`find_project_sheet`).

## Phase D notes

Implementation lives in `hooks/learning/` (`paths`, `topics`, `sections`,
`context`, `profile`, `project`, `install`). `hooks/lib_profile.py` is a
compatibility shim. Stable install copies the shim + `learning/` package beside
`cli.py`.

## Phase F release

```bash
python3 scripts/verify_release.py
```

Current plugin version: **2.5.0**.
