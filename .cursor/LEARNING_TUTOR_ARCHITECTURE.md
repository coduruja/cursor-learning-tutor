# Learning Tutor — architecture pocket map

Current state as of **2.4.0**. Rules/Skills split and evidence policy are
implemented. Full history: git / merged PR #1.

This file is a short ownership map for further work (hooks, agents). Detailed
workflow text lives in `rules/` and `skills/`.

## Rule vs Skill vs Reference

| **Rule** | **Skill** | **Reference** |
|---|---|---|
| Short policy (“always / never”) | Multi-step study task | Detail loaded only when a Skill needs it |
| Shared across flows | Owned by one workflow | e.g. probe rubric |

- **Rule** ≈ write always like this  
- **Skill** ≈ run this study task end-to-end  
- **Reference** ≈ read only when probing  

Persistence → Rule (`learning-recording`). Probe scoring → Skill reference.

## Evidence policy

- Exposure / self-report / finishing a track ≠ `covered`.
- Only a **one-topic** `study-probe` attests knowledge: **5–10** questions,
  wait for answers, **≥50%** correct → `covered`; else `want`.
- Markers: `LEARNING-WANT` only (no covered marker).

## Single-owner map

| Concern | Owner |
|---|---|
| Persist `want` / `covered` (CLI, markers, feedback) | `rules/learning-recording.mdc` |
| Transferability (local vs global) | `rules/project-learning-boundary.mdc` |
| Auto-`want` on conceptual questions | `rules/concept-gap-capture.mdc` |
| Routing + calibration | `rules/tutor-core.mdc` (only always-on rule) |
| Probe scoring | `skills/study-probe` + `references/assessment-rubric.md` |
| Snapshot / missing-sheet sync | `skills/study-plan` (read-only; no profile writes) |
| Init + manual `want` | `skills/study-log` (explicit only; “I learned X” → probe) |
| Deep research track | `skills/study-deep` → always hands off to probe |
| Research subagent | `agents/study-researcher.md` |

## Integration map

```text
concept_gap (rule) ──want──► queue
                │
                ▼
         study-plan ──offers──► study-probe ──covered/want──► profile
                │                      ▲
                └──offers──► study-deep ──always──► study-probe (same topic)

study-log ── want / init ──► profile
          └── “I learned X” ──► study-probe

self-attestation (“I understand…”, “finished studying…”) ──► study-probe
```

Shared: CLI at `~/.cursor/learning/cli.py` (`sessionStart`); optional
`LEARNING-PROFILE` / `LEARNING-PROJECT`; global profile vs project sheet.

## Runtime rules vs maintainer rules

| | `rules/` | `.cursor/rules/` |
|---|---|---|
| Audience | Plugin users | Contributors to this repo |
| Shipped? | Yes (plugin manifest) | No |
| Purpose | Tutor behavior | Dev conventions here |

Ask: *who should feel this rule?* Tutor behavior → `rules/`. Editing this
repo only → `.cursor/rules/`. Do not mix (maintainer noise ships to users;
tutor rules in `.cursor/rules/` vanish outside this repo).

Maintainer rules: optional; add only when the same editing mistakes recur.

## Hooks / agents (next)

Current shape (to refactor):

- `sessionStart` → `hooks/inject_profile.py` (install CLI + inject profile)
- `afterAgentResponse` → `hooks/capture_learning.py` (want markers only)
- `hooks/learning_cli.py` → thin argparse over `hooks/lib_profile.py` (~god module)
- `agents/study-researcher.md` → used by `study-deep`

## Verify

```bash
python3 scripts/check_architecture.py
python3 scripts/smoke_install.py
python3 scripts/verify_scenarios.py
```
