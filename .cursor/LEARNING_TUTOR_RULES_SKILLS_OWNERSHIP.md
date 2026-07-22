# Learning Tutor — ownership map

Current state as of **2.6.0**. Rules/Skills evidence policy landed in 2.4.0.
Hooks still mix Cursor adapters with the persistence library; the next cut is
planned in `HOOKS_RUNTIME_REFACTOR.md`.

This file is the short ownership map for the tutoring architecture. Detailed
workflow text lives in `rules/` and `skills/`.

## Rule vs Skill vs Reference vs Hook vs Runtime

| **Rule** | **Skill** | **Reference** | **Hook** | **Runtime** |
|---|---|---|---|---|
| Short policy (“always / never”) | Multi-step study task | Detail loaded only when a Skill needs it | Cursor lifecycle adapter (JSON in/out) | Deterministic persistence / CLI |
| Shared across flows | Owned by one workflow | e.g. probe rubric | Thin; fail-open | Owns profile/project files |

- **Rule** ≈ write always like this  
- **Skill** ≈ run this study task end-to-end  
- **Reference** ≈ read only when probing  
- **Hook** ≈ when Cursor rings the bell (`sessionStart`, `afterAgentResponse`)  
- **Runtime** ≈ the kitchen (read/write profile, normalize topics, install CLI)

Persistence **policy** → Rule (`learning-recording`).  
Persistence **mechanics** → Runtime under `runtime/learning/`.  
Probe scoring → Skill reference.

## Evidence policy

- Exposure / self-report / finishing a track ≠ `covered`.
- Only a **one-topic** `study-probe` attests knowledge: **5–10** questions,
  wait for answers, **≥50%** correct → `covered`; else `want`.
- Markers: `LEARNING-WANT` only (no covered marker).

## Single-owner map

| Concern | Owner |
|---|---|
| Persist `want` / `covered` (CLI, markers, feedback) | `rules/learning-recording.mdc` (policy) |
| Transferability (local vs global) | `rules/project-learning-boundary.mdc` |
| Auto-`want` on conceptual questions | `rules/concept-gap-capture.mdc` |
| Routing + calibration | `rules/tutor-core.mdc` (only always-on rule) |
| Probe scoring | `skills/study-probe` + `references/assessment-rubric.md` |
| Snapshot / missing-sheet sync | `skills/study-plan` (read-only; no profile writes) |
| Init + manual `want` | `skills/study-log` (explicit only; “I learned X” → probe) |
| Deep research track | `skills/study-deep` → always hands off to probe |
| Research subagent | `agents/study-researcher.md` (research only; no probe writes) |
| Cursor event adapters | `hooks/inject_profile.py`, `hooks/capture_learning.py` |
| Profile/project I/O + CLI install | `runtime/learning/` (+ `runtime/cli.py`) |

## Integration map

```text
concept_gap (rule) ──want──► queue
                │
                ▼
         study-plan ──offers──► study-probe ──covered/want──► profile
                │                      ▲
                └──offers──► study-deep ──always──► study-probe (same topic)
                                   │
                                   └── study-researcher (research only)

study-log ── want / init ──► profile
          └── “I learned X” ──► study-probe

self-attestation (“I understand…”, “finished studying…”) ──► study-probe

Cursor sessionStart ──install CLI + best-effort inject──► Agent context
Cursor afterAgentResponse ──LEARNING-WANT markers──► runtime.add_want
```

Public Agent path: `python3 ~/.cursor/learning/cli.py …`  
Optional inject: `LEARNING-PROFILE` / `LEARNING-PROJECT` (best-effort; do not
treat inject alone as the only calibration source).

## How to think about Hooks (correct framing)

Hooks are **not** the Learning Tutor product. They are the Cursor harness plug:

| Event | Intended job | Must stay thin |
|---|---|---|
| `sessionStart` | Ensure stable CLI exists; optionally emit context | Yes — fire-and-forget |
| `afterAgentResponse` | Capture want-only markers when CLI was missing | Yes — observe / side-effect |

Industry pattern (Claude Code playbooks, OpenAI Agents lifecycle hooks,
LangChain middleware, harness papers): **hooks/middleware observe or gate the
loop; application services own domain state.** Putting markdown parsers,
aliases, and migrations inside the hook folder confuses “bell” with “kitchen.”

Today the kitchen lives at `runtime/learning/`. Hooks only adapt Cursor events
and call into that runtime (see `HOOKS_RUNTIME_REFACTOR.md`).

## Runtime rules vs maintainer rules

| | `rules/` | `.cursor/rules/` |
|---|---|---|
| Audience | Plugin users | Contributors to this repo |
| Shipped? | Yes (plugin manifest) | No |
| Purpose | Tutor behavior | Dev conventions here |

Ask: *who should feel this rule?* Tutor behavior → `rules/`. Editing this
repo only → `.cursor/rules/`. Do not mix.

## Verify

```bash
python3 scripts/verify_release.py
```
