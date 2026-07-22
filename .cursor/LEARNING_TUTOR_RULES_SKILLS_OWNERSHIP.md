# Learning Tutor — ownership map

Current state as of **3.0.0**. For *how to choose* between a rule, skill, hook,
and agent when adding something, see `.cursor/rules/authoring-protocols.mdc`.
This file records who owns what today.

## The shape

```text
rules/learning-tutor.mdc      one always-on rule — invariants only
skills/<name>/SKILL.md        one self-contained procedure each
agents/study-researcher.md    isolated-context research
hooks/*.py                    Cursor lifecycle adapters (thin, fail-open)
runtime/learning/             persistence, topic normalization, CLI install
```

One rule is always on. Everything else loads only when it is needed, and
whatever loads is complete on its own.

## Single-owner map

| Concern | Owner |
|---|---|
| Explanation style, transferability gate, evidence law | `rules/learning-tutor.mdc` |
| Explain a concept + queue the gap | `skills/concept-gap-capture` |
| Read-only snapshot, local sheet discovery | `skills/study-plan` |
| Assess one topic; **only** writer of `covered` | `skills/study-probe` |
| Probe scoring detail | `skills/study-probe/references/assessment-rubric.md` |
| Curated track → always hands off to a probe | `skills/study-deep` |
| Manual `init` / `want`, explicit-only | `skills/study-log` |
| Resource research, no writes | `agents/study-researcher.md` |
| Cursor event adapters | `hooks/inject_profile.py`, `hooks/capture_learning.py` |
| Profile/project I/O, aliases, CLI install | `runtime/learning/` (+ `runtime/cli.py`) |

`want` is written by four skills, each spelling out the command itself. That
duplication is deliberate: a skill that outsources its write to something which
may not be in context is a skill that silently does nothing.

## Evidence policy

- Exposure, self-report, or finishing a track ≠ `covered`.
- Only a **one-topic** `study-probe` attests knowledge: **5–10** questions, wait
  for answers, **≥50%** correct → `covered`; otherwise `want`.
- Markers: `LEARNING-WANT` only. There is no covered marker, by design — the
  queue can tolerate a best-effort write, attested knowledge cannot.

## Integration map

```text
concept-gap-capture ──want──► queue
                                │
study-plan ──offers──► study-probe ──covered / want──► profile
      │                      ▲
      └──offers──► study-deep ──always──► study-probe (same topic)
                        │
                        └── study-researcher (research only)

study-log ── want / init ──► profile
          └── "I learned X" ──► study-probe

Cursor sessionStart ──install CLI + best-effort inject──► Agent context
Cursor afterAgentResponse ──LEARNING-WANT markers──► runtime.add_want
```

Public agent path: `python3 ~/.cursor/learning/cli.py …`
Optional inject: `LEARNING-PROFILE` / `LEARNING-PROJECT` — best-effort, so no
skill may treat it as the only source of state.

## Hooks are the bell, runtime is the kitchen

| Event | Job | Constraint |
|---|---|---|
| `sessionStart` | Ensure the CLI exists; emit context | Fire-and-forget, fail-open |
| `afterAgentResponse` | Capture want-only markers | Observe / side-effect only |

Markdown parsing, aliases, and migrations belong in `runtime/learning/`, never
in `hooks/`. Line budgets in `scripts/smoke_install.py` enforce it.

## Runtime rules vs maintainer rules

| | `rules/` | `.cursor/rules/` |
|---|---|---|
| Audience | Plugin users | Contributors to this repo |
| Shipped? | Yes (plugin manifest) | No |
| Purpose | Tutor behavior | How to author this plugin |

## Verify

```bash
python3 scripts/verify_release.py
```
