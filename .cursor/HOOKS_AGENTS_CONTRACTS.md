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

### Current plugin behavior (`inject_profile.py`)

| Aspect | Current | Contract decision |
|---|---|---|
| Stdin | Read and discarded | Keep until Phase C; later may use `session_id` / mode |
| Side effect | Copies `learning_cli.py` → `~/.cursor/learning/cli.py` and `lib_profile.py` → `~/.cursor/learning/lib_profile.py` | **Must remain**: Rules/Skills call the stable CLI path |
| Project sheet | Walk up to 8 parents from `os.getcwd()` for `.cursor/learning/project.md` (or legacy `.cursor/learning-project.md`) | See §4 |
| Stdout | `{"continue": true, "additional_context": "..."}` | `additional_context` is the supported field; `continue` is **not** in the official sessionStart output — treat as harmless extra until adapters are hardened |
| Fail-open | On any exception, print `{"continue": true}` | Keep fail-open; Phase C may add stderr diagnostics |

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

### Current plugin behavior (`capture_learning.py`)

| Aspect | Current | Contract decision |
|---|---|---|
| Payload parsing | Prefer top-level string keys `text`, then also `response`, `content`, `message`, `output` | **Canonical field is `text`**; extra keys are temporary compatibility, not a public contract |
| Markers | Regex `LEARNING-WANT topic="..." note="..."` | Only `want` markers; **no** covered marker; `LEARNING-LOG` retired |
| Persistence | `lib.add_want(...)` | Marker path writes queue only |
| Side effect | Re-runs `install_cli()` | Keep until install boundary is explicit |
| Stdout | `{"continue": true}` | Not in official schema; keep fail-open shape until Phase C |
| Empty topic | Regex allows `topic=""`; `add_want` raises; exception swallowed | Documented defect; fix in Phase B/C with tests |

---

## 4. Project-root discovery (single intended behavior)

Today there are **two** semantics:

| Entry | Behavior |
|---|---|
| `inject_profile._find_project_file` | Walk up to 8 ancestors from `getcwd()` |
| CLI `project-*` via `lib_profile.project_path(cwd)` | Use `--cwd` if given, else **only** `Path.cwd()` — no ancestor walk |

**Frozen target behavior** (implement in Phase C; do not change callers yet):

1. Prefer explicit `--cwd` when provided (CLI).
2. Else prefer the first absolute path from Hook stdin `workspace_roots` when
   present (common envelope on many events; sessionStart event-specific schema
   currently omits it — verify at Phase B with real payloads).
3. Else use `Path.cwd()`.
4. From that root, resolve `.cursor/learning/project.md`, with legacy
   `.cursor/learning-project.md` as read/migrate fallback.
5. **Ancestor walk (up to 8)** remains allowed for **injection lookup only**
   until Phase C unifies helpers; CLI writes must continue to target the
   resolved project root, not a surprise parent, unless `--cwd` says so.

Until Phase C ships a shared helper, treat any mismatch between injected sheet
and CLI `project-show` as a known risk, not undefined behavior.

---

## 5. Stable CLI paths and commands

### Paths (public)

| Path | Role |
|---|---|
| `~/.cursor/learning/cli.py` | Stable entrypoint referenced by Rules/Skills |
| `~/.cursor/learning/lib_profile.py` | Library copied next to the CLI |
| `~/.cursor/learning/profile.md` | Global profile (meta, queue, covered) |
| `<project>/.cursor/learning/project.md` | Per-repo sheet (stack, candidates, last probe) |

Install source (plugin tree): `hooks/learning_cli.py` + `hooks/lib_profile.py`.

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

## 7. Agent `study-researcher` — frontmatter validation

File: `agents/study-researcher.md`  
Delegated from: `skills/study-deep/SKILL.md` (string name `study-researcher`)

### Frontmatter (current)

```yaml
name: study-researcher
description: ...
model: inherit
readonly: true
```

### Validation against Subagents docs (2026-07-21)

| Field | Supported? | Verdict |
|---|---|---|
| `name` | Yes | Keep; must stay equal to Skill delegation string |
| `description` | Yes | Keep; drives auto-delegation |
| `model: inherit` | Yes (default) | Keep; research should match parent reasoning |
| `readonly: true` | Yes | Keep; researcher must not edit files or mutate profile |
| `is_background` | Supported, unused | Omit unless deep-study becomes async |

**Phase A decision:** do **not** change Agent frontmatter. Earlier suspicion that
`model` / `readonly` were undocumented is **resolved** — they are official.
Phase E may still tighten body I/O wording and add smoke checks; renaming
`name` requires a coordinated Skill update.

### Behavioral boundary (frozen)

- Input: topic + level (+ optional project stack context).
- Output: curated track markdown only (≤5 items).
- Must **not** score probes or write `covered` / `want`.
- `study-deep` always hands off to one-topic `study-probe` after the track.

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

These exercises document current Hook/CLI/Agent behavior (including known
defects such as empty `LEARNING-WANT` topics) without changing runtime code.
