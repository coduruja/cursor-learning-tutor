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

You do not need to “turn on” the tutor: the rule uses `alwaysApply: true`.

## What lives where

### Global (`~/.cursor/learning/`)

| File | Role |
|---|---|
| `profile.md` | Meta, **study queue**, and **covered** |
| `cli.py` + `lib_profile.py` | Stable CLI (installed on `sessionStart`) |

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
| `rules/tutor.mdc` | Intent (`concept_gap` / `repo_local` / `agent_task`) + auto-want + calibration |
| `commands/study-log.md` | Explicit recording |
| `commands/study-plan.md` | Snapshot or onboarding if empty |
| `commands/study-probe.md` | Active probe → adjusts covered/want |
| `commands/study-deep.md` | Starts a track via subagent |
| `agents/study-researcher.md` | Curated research in an isolated context |
| `hooks/*` | Injects profile + project, installs CLI, captures backup markers |

## Installation

### Marketplace / Plugins
Install **Learning Tutor** under User. Open a **new chat** afterward — `sessionStart`
copies the CLI to `~/.cursor/learning/`.

### Direct copy (no marketplace)
```bash
mkdir -p ~/.cursor/rules ~/.cursor/agents ~/.cursor/commands ~/.cursor/hooks ~/.cursor/learning
cp rules/tutor.mdc            ~/.cursor/rules/
cp agents/study-researcher.md ~/.cursor/agents/
cp commands/*.md              ~/.cursor/commands/
cp hooks/lib_profile.py hooks/learning_cli.py hooks/capture_learning.py hooks/inject_profile.py ~/.cursor/hooks/
cp hooks/learning_cli.py ~/.cursor/learning/cli.py
cp hooks/lib_profile.py ~/.cursor/learning/lib_profile.py
```
Point a global `hooks.json` at the scripts under `~/.cursor/hooks/`.

### Requirements
- `python3` on PATH (Windows: use `python` in `hooks.json` if needed).

## How recording works

1. **CLI** (preferred): the agent runs `python3 ~/.cursor/learning/cli.py …`
2. **Markers** (backup): `<!-- LEARNING-LOG … -->` / `<!-- LEARNING-WANT … -->`
   read by the `afterAgentResponse` hook

Quick intent map:
- “what is PR / HTTP / Docker?” → queue (`want`) + feedback
- “what does module X do?” → code only, no log
- “implement Y” → execute; log only if a new concept was taught

The CLI normalizes aliases (e.g. `pull request` ↔ `PR`) and ignores generic
topics or bare base languages.

## Caveats
- If the CLI does not exist yet, open a new chat (so `sessionStart` can run)
  or use the direct copy above.
- If `$CURSOR_PLUGIN_ROOT` fails on your Cursor version, use the direct copy.
- Hooks are short local scripts — audit them if you want.
