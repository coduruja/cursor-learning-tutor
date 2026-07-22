# Learning Tutor (Cursor Plugin)

A lightweight tutor: calibrates explanations to your level, captures conceptual
gaps into a queue, keeps per-project stack/candidates, and only deepens research
when you ask.

## Quick use

| Action | How |
|---|---|
| Normal chat | Classifies intent; “what is X?” → explain + automatic `want` |
| Manual record | `/study-log` |
| Snapshot / onboarding | `/study-plan` |
| Probe (quiz) | `/study-probe` |
| Curated track | `/study-deep <topic>` (no topic → first queue item) |

You do not need to “turn on” the tutor: `rules/tutor-core.mdc` uses
`alwaysApply: true`.

## What lives where

### Global (`~/.cursor/learning/`)

| File | Role |
|---|---|
| `profile.md` | Meta, **study queue**, and **covered** |
| `cli.py` + `lib_profile.py` + `learning/` | Stable CLI (installed on `sessionStart`) |

### Per project (hybrid)

| File | Role |
|---|---|
| `.cursor/learning/project.md` | Learning Tutor data: stack, local **candidates**, last probe |

Project candidates become global queue items only via a conceptual question,
`/study-probe`, or an explicit request.
The header marks the file as **data**, not a rule or instruction for other agents.

```bash
python3 ~/.cursor/learning/cli.py show
python3 ~/.cursor/learning/cli.py covered --topic "Closures" --level intermediate
python3 ~/.cursor/learning/cli.py want --topic "Docker" --note "for deploy"
python3 ~/.cursor/learning/cli.py project-show
python3 ~/.cursor/learning/cli.py project-sync --stack "Next.js;Prisma" --candidates "App Router;Prisma migrations"
```

## What ships in the plugin

| Component | Role |
|---|---|
| `rules/tutor-core.mdc` | Always-on: coding vs learning, Skill routing |
| `rules/concept-gap-capture.mdc` | Auto-`want` on conceptual questions |
| `rules/learning-recording.mdc` | Persist `want` / `covered` (CLI + markers) |
| `rules/project-learning-boundary.mdc` | Transferable vs repo-local learning |
| `skills/learning-explanations/` | Learner-friendly explanation style (no profile I/O) |
| `skills/study-log/` | Explicit `init` / `want`; “I learned X” → probe |
| `skills/study-plan/` | Read-only snapshot / next steps |
| `skills/study-probe/` | One-topic evidence-based assessment |
| `skills/study-deep/` | Curated track → always hands off to probe |
| `agents/study-researcher.md` | Research/curation only (readonly) |
| `hooks/*` | Inject profile/project, install CLI, capture want markers |

Skills can be invoked explicitly with `/study-*`. Cursor may also apply
`study-plan`, `study-probe`, and `study-deep` automatically when the request
matches their descriptions. `study-log` is intentionally explicit-only.

## Installation

### Marketplace / Plugins
Install **Learning Tutor** under User. Open a **new chat** afterward — `sessionStart`
copies the CLI to `~/.cursor/learning/`.

### Direct copy (no marketplace)
Prefer the marketplace path. If you must copy by hand:

```bash
mkdir -p ~/.cursor/rules ~/.cursor/agents ~/.cursor/skills ~/.cursor/hooks ~/.cursor/learning
cp rules/*.mdc               ~/.cursor/rules/
cp agents/study-researcher.md ~/.cursor/agents/
cp -R skills/*                ~/.cursor/skills/
cp hooks/*.py                 ~/.cursor/hooks/
cp hooks/hooks.json           ~/.cursor/hooks/hooks.json   # edit paths if needed
cp runtime/cli.py             ~/.cursor/learning/cli.py
cp hooks/lib_profile.py       ~/.cursor/learning/lib_profile.py
cp -R runtime/learning        ~/.cursor/learning/learning
```

Plugin installs use `$CURSOR_PLUGIN_ROOT` in `hooks/hooks.json`. A manual
`hooks.json` must point at the copied scripts.

### Requirements
- `python3` on PATH (Windows: use `python` in `hooks.json` if needed).

## How recording works

1. **CLI** (preferred): the agent runs `python3 ~/.cursor/learning/cli.py …`
2. **Markers** (backup for queue only): `<!-- LEARNING-WANT … -->` read by the
   `afterAgentResponse` hook when the CLI is missing. There is no covered
   marker — `covered` requires one-topic probe evidence via the CLI.

Quick intent map:
- “what is PR / HTTP / Docker?” → queue (`want`) + feedback
- “what does module X do?” → code only, no log
- “I learned X” / “I understand X” → one-topic `/study-probe` (not auto-`covered`)
- “implement Y” → execute; do not infer `covered` from teaching alone

The CLI normalizes aliases (e.g. `pull request` ↔ `PR`) and ignores generic
topics or bare base languages.

## Maintainer verification

```bash
python3 scripts/verify_release.py
```

## Caveats
- If the CLI does not exist yet, open a new chat (so `sessionStart` can run)
  or use the direct copy above.
- If `$CURSOR_PLUGIN_ROOT` fails on your Cursor version, use the direct copy.
- Hooks are short local scripts — audit them if you want.
