# Changelog

## 2.6.0
- Hook vs Runtime packaging: domain code lives under `runtime/learning/` with
  `runtime/cli.py`; hooks are thin adapters plus a `lib_profile` shim.
- Adapters call `render_session_context` / `iter_want_markers` + `add_want`;
  `hooks.json` sets timeouts (sessionStart 10s, afterAgentResponse 5s).
- Calibration fallback: Rules/Skills load profile via `cli.py show` when
  session inject is missing (no product feature cuts).

## 2.5.0
- Refactor Hooks/Agents runtime: shared `hook_io` adapters, validated
  `LEARNING-WANT` markers, stderr diagnostics, unified project-root discovery.
- Split `lib_profile.py` into `hooks/learning/` (`paths`, `topics`, `sections`,
  `context`, `profile`, `project`, `install`) with a compatibility shim; stable
  install copies the package beside `cli.py`.
- Harden `study-researcher` ↔ `study-deep` contract (research-only boundary;
  always hand off to one-topic probe).
- Release checks: `scripts/test_hooks_agents.py` and `scripts/verify_release.py`.

## 2.4.0
- Split the always-on tutor rule into `tutor-core` plus intelligent rules for
  concept capture, recording, and project-learning boundary.
- Evidence policy: only a one-topic `study-probe` (5–10 questions, ≥50% correct)
  can write `covered`; self-report and teaching exposure do not.
- Skills ownership: `study-plan` is read-only; `study-log` owns init/want and
  routes “I learned X” to probe; `study-deep` always hands off to probe.
- Recording contract: `want`/`covered` CLI and want-only marker fallback live
  only in `learning-recording`; `LEARNING-LOG` covered markers are retired.
- Architecture checks under `scripts/` for CLI/gate ownership, frontmatter,
  install smoke, and scenario-matrix structure.

## 2.3.0
- Replace legacy commands with Agent Skills under `skills/<name>/SKILL.md`.
- `study-log` remains explicit-only; plan, probe, and deep-study workflows can
  auto-activate from specific user intent.
- `study-probe` uses an on-demand assessment rubric for evidence and
  transferability instead of treating exposure as understanding.
- Plugin manifest now discovers `skills/` and no longer declares `commands/`.

## 2.2.0
- Project copy, rules, workflows, agents, CLI messages, and docs are English.
- Canonical levels: `beginner` / `intermediate` / `advanced` (Portuguese aliases still accepted).
- Profile/project section titles are English; legacy Portuguese headings are still read and rewritten on update.

## 2.1.1
- Move the local sheet to `.cursor/learning/project.md`, under its own namespace.
- Header explicitly marks the sheet as Learning Tutor data, not a rule, prompt, or instruction.
- CLI automatically migrates the legacy path `.cursor/learning-project.md`.

## 2.1.0
- Intent classification in the rule: `concept_gap` → auto-`want`; `repo_local` /
  `agent_task` without polluting the queue.
- Hybrid model: `.cursor/learning-project.md` (stack + candidates + probe)
  + global profile (queue/covered).
- CLI: `project-show`, `project-sync`, `project-drop`, `queue-next`;
  topic normalization/dedupe (aliases, anti-noise).
- `sessionStart` injects `LEARNING-PROJECT` when the file exists.
- New `/study-probe` command (quiz → covered/want).
- `/study-deep` without a topic uses the first open queue item.
- `/study-plan` includes project stack/candidates.

## 2.0.0
- Profile with **Meta**, **Study queue**, and **Covered**.
- Stable CLI at `~/.cursor/learning/cli.py` (installed on `sessionStart`).
- New `/study-log` command for explicit recording.
- `/study-plan` onboards when the profile is empty.
- Visible feedback (`Saved to profile: …`) and `LEARNING-WANT` markers.
- Hooks share `lib_profile.py` (less fragile).

## 1.0.0
- First release. Packages: tutor rule (`alwaysApply`), `study-researcher`
  subagent, `/study-plan` and `/study-deep` commands, and profile
  capture + injection hooks.
