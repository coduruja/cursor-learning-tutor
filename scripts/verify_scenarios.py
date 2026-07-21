#!/usr/bin/env python3
"""Structural verification of the Learning Tutor scenario matrix.

Does not run a live Agent chat. It checks that rules/Skills encode the
behaviors required by LEARNING_TUTOR_ARCHITECTURE.md scenarios.

Usage (from repo root):
  python3 scripts/verify_scenarios.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def fail(errors: list[str]) -> int:
    print("Scenario matrix verification failed:")
    for err in errors:
        print(f"  - {err}")
    return 1


def main() -> int:
    errors: list[str] = []

    core = read("rules/tutor-core.mdc")
    capture = read("rules/concept-gap-capture.mdc")
    recording = read("rules/learning-recording.mdc")
    boundary = read("rules/project-learning-boundary.mdc")
    study_log = read("skills/study-log/SKILL.md")
    study_plan = read("skills/study-plan/SKILL.md")
    study_probe = read("skills/study-probe/SKILL.md")
    study_deep = read("skills/study-deep/SKILL.md")
    rubric = read("skills/study-probe/references/assessment-rubric.md")

    # Rules-focused expectations
    if "alwaysApply: true" not in core:
        errors.append("tutor-core must be always-on for ordinary coding turns")
    for rule, label in (
        (capture, "concept-gap-capture"),
        (recording, "learning-recording"),
        (boundary, "project-learning-boundary"),
    ):
        if "alwaysApply: false" not in rule:
            errors.append(f"{label} must be Apply Intelligently")

    if "one transferable" not in capture.lower() and "at most **one**" not in capture:
        if "at most **one** main transferable" not in capture:
            # concept-gap-capture says "at most **one** main transferable topic"
            if "at most **one**" not in capture:
                errors.append("concept-gap-capture must limit to one want topic")

    if "one-topic probe" not in recording and "one-topic" not in recording:
        errors.append("learning-recording must require one-topic probe for covered")
    if "LEARNING-LOG" in recording and "retired" not in recording:
        errors.append("learning-recording must retire LEARNING-LOG")
    if "LEARNING-WANT" not in recording:
        errors.append("learning-recording must keep LEARNING-WANT fallback")

    if "Would this still be useful without opening this repository?" not in boundary:
        errors.append("project-learning-boundary must own the transferability test")

    # Skills-focused expectations
    log_fm = study_log.split("---", 2)[1]
    if "disable-model-invocation: true" not in log_fm:
        errors.append("study-log must be explicit-only")
    if "study-probe" not in study_log or "covered" not in study_log.lower():
        errors.append("study-log must route learned-claims to study-probe")
    if "project-learning-boundary" not in study_log:
        errors.append("study-log must apply project-learning-boundary")
    if "cli.py want" in study_log or "cli.py covered" in study_log:
        errors.append("study-log must not duplicate want/covered CLI")

    plan_desc = re.search(r"^description:\s*(.+)$", study_plan, re.M)
    if not plan_desc or "read-only" not in plan_desc.group(1).lower():
        # description may wrap - check first 500 chars of frontmatter
        plan_head = study_plan[:800].lower()
        if "read-only" not in plan_head and "do not use for quizzes" not in plan_head:
            errors.append("study-plan description must be read-only / non-quiz")
    if "Empty profile" in study_plan and "/study-log" not in study_plan:
        errors.append("empty study-plan must point to /study-log")
    if re.search(r"run `?init`?", study_plan) and "Do not" not in study_plan:
        # plan should not run init
        if "do not run `init`" not in study_plan.lower() and "do not run init" not in study_plan.lower():
            if "do not" in study_plan.lower() and "init" in study_plan.lower():
                pass  # likely "do not run init, want, or covered"
            else:
                errors.append("study-plan must not onboard with init")
    if "do not run `init`, `want`, or `covered`" not in study_plan.lower() and \
       "do not run `init`" not in study_plan.lower():
        # Check the actual file wording
        if "do not" not in study_plan.lower() or "init" not in study_plan:
            errors.append("study-plan must forbid init/want/covered writes")

    probe_head = study_probe[:1200].lower()
    if "exactly one" not in probe_head and "one topic" not in probe_head:
        errors.append("study-probe must select exactly one topic")
    if "5 to 10" not in study_probe and "5–10" not in study_probe:
        errors.append("study-probe must require 5-10 questions")
    if "50%" not in study_probe:
        errors.append("study-probe must use the 50% covered bar")
    if "finished studying" not in probe_head and "finished studying" not in study_probe.lower():
        errors.append("study-probe description must include self-attestation triggers")
    if "study-deep" not in study_probe.lower():
        errors.append("study-probe description must mention post-deep handoff")
    if "cli.py want" in study_probe or "cli.py covered" in study_probe:
        errors.append("study-probe must not duplicate want/covered CLI")
    if "project-drop" not in study_probe:
        errors.append("study-probe must keep project-drop")

    if "project-learning-boundary" not in rubric:
        errors.append("rubric must point at project-learning-boundary")
    if "50%" not in rubric:
        errors.append("rubric must state the 50% bar")
    if "5 to 10" not in rubric and "5–10" not in rubric:
        errors.append("rubric must require 5-10 questions")

    if "must **not**\nwrite `covered`" not in study_deep and "must **not** write `covered`" not in study_deep:
        if "must not write `covered`" not in study_deep.lower() and "must **not**" not in study_deep:
            errors.append("study-deep must state track completion is not covered")
    if "study-probe" not in study_deep:
        errors.append("study-deep must hand off to study-probe")
    if "Always continue" not in study_deep and "always continue" not in study_deep.lower():
        errors.append("study-deep must always continue into study-probe")
    if "cli.py want" in study_deep or "cli.py covered" in study_deep:
        errors.append("study-deep must not duplicate want/covered CLI")

    # Ambiguous plan vs probe wording
    if "Do not use for quizzes" not in study_plan and "do not use for quizzes" not in study_plan.lower():
        errors.append("study-plan must exclude quizzes in description")
    if "Do not use for passive profile summaries" not in study_probe and \
       "do not use for passive" not in study_probe.lower():
        errors.append("study-probe must exclude passive summaries in description")

    if errors:
        return fail(errors)

    print("Scenario matrix structural checks passed.")
    print("Live Agent confirmation still needed in Cursor for:")
    print("  - active-context panel on ordinary vs learning turns")
    print("  - end-to-end probe scoring with real answers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
