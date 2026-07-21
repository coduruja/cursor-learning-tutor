# Changelog

## 2.2.0
- Project copy, rules, commands, agents, CLI messages, and docs are English.
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
