#!/usr/bin/env python3
"""Structural verification of the Learning Tutor scenario matrix.

Does not run a live Agent chat. It checks that the shipped rule, skills, and
agent still encode the behavior each scenario depends on. `check_architecture`
covers structure; this file covers meaning.

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


def normalize(text: str) -> str:
    """Lowercase, unwrap lines, drop markdown emphasis.

    Checks assert meaning, not formatting: a phrase that got re-wrapped or
    bolded during an edit is still the same instruction.
    """
    return re.sub(r"\s+", " ", text.replace("*", "").replace("`", "")).lower()


def has(text: str, *needles: str) -> bool:
    """True when every needle appears, ignoring wrapping and emphasis."""
    haystack = normalize(text)
    return all(normalize(needle) in haystack for needle in needles)


def has_any(text: str, *needles: str) -> bool:
    haystack = normalize(text)
    return any(normalize(needle) in haystack for needle in needles)


def main() -> int:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    rule = read("rules/learning-tutor.mdc")
    capture = read("skills/concept-gap-capture/SKILL.md")
    plan = read("skills/study-plan/SKILL.md")
    probe = read("skills/study-probe/SKILL.md")
    deep = read("skills/study-deep/SKILL.md")
    log = read("skills/study-log/SKILL.md")
    rubric = read("skills/study-probe/references/assessment-rubric.md")
    researcher = read("agents/study-researcher.md")

    # --- Scenario: ordinary coding turn -----------------------------------
    require(
        has(rule, "alwaysApply: true"),
        "the tutor rule must be always-on so ordinary turns still classify",
    )
    require(
        has_any(rule, "no study write", "do the work"),
        "rule must tell a code task to do the work without a study write",
    )

    # --- Scenario: the tutor explains -------------------------------------
    # Style moved out of the always-on rule (3.1): it only matters once a
    # learning turn is already routed to a skill, so it lives there instead.
    require(
        has(capture, "plain language"),
        "explanation style (plain-language lead) must live in concept-gap-capture",
    )
    require(
        not has(rule, "plain language"),
        "explanation style must not creep back into the always-on rule",
    )

    # --- Scenario: transferability ------------------------------------------
    # Every skill that can write global state inlines the test itself — none
    # may assume the always-on rule still states it (see 3.1 line-budget cut).
    transferability = "Would this still be useful without opening this repository?"
    for name, text in (
        ("concept-gap-capture", capture),
        ("study-plan", plan),
        ("study-log", log),
        ("assessment-rubric.md", rubric),
    ):
        require(
            has(text, transferability),
            f"{name} must inline the transferability test",
        )
    require(
        not has(rule, transferability),
        "the always-on rule must not own the transferability test anymore",
    )
    require(
        has(capture, "LEARNING-PROJECT") and has(capture, "never queued"),
        "concept-gap-capture must forbid auto-queuing project candidates",
    )
    require(
        has(capture, "Symbols, paths, environment variables"),
        "concept-gap-capture must forbid raw symbols/paths as global topics",
    )

    # --- Scenario: evidence -----------------------------------------------
    # The "covered = demonstrated, not exposed" law lives with its only
    # writer (study-probe) and with the skills that route claims away from it.
    require(
        has_any(probe, "never infer mastery from exposure", "only skill that may write covered"),
        "study-probe must own the evidence law: no covered without a probe",
    )
    require(
        has(log, "do not") and has(log, "write") and has(log, "covered")
        and has(log, "study-probe"),
        "study-log must route a learned-claim to study-probe instead of covered",
    )
    require(
        not has(rule, "LEARNING-LOG"),
        "the LEARNING-LOG covered marker is retired and must not reappear",
    )
    for name, text in (
        ("concept-gap-capture", capture),
        ("study-log", log),
        ("study-probe", probe),
    ):
        require(
            "LEARNING-COVERED" not in text,
            f"{name} must not invent a covered marker — covered needs the CLI",
        )

    # --- Scenario: conceptual question ------------------------------------
    require(has(capture, "at most **one**"), "capture must queue at most one topic")
    require(has(capture, "cli.py show"), "capture must check the queue before writing")
    require(has(capture, "cli.py want"), "capture must inline the want CLI")
    require(
        has(capture, "LEARNING-WANT"),
        "capture must keep the want marker fallback for a missing CLI",
    )
    require(
        has(capture, "concept_gap", "repo_question", "agent_task"),
        "capture must classify agent task vs concept gap vs repo question",
    )

    # --- Scenario: probe ---------------------------------------------------
    require(
        has_any(probe[:1400], "exactly one topic", "one topic"),
        "probe must select exactly one topic",
    )
    require(has_any(probe, "5 to 10", "5–10"), "probe must ask 5-10 questions")
    require(has(probe, "50%"), "probe must apply the 50% covered bar")
    require(
        has(probe, "assessment-rubric.md"),
        "probe must load the rubric before scoring",
    )
    require(has(probe, "cli.py covered"), "probe must inline the covered CLI")
    require(
        has(probe, "cli.py want"),
        "probe must inline the want CLI for a failed probe",
    )
    require(has(probe, "project-drop"), "probe must keep project sheet hygiene")

    # --- Scenario: rubric --------------------------------------------------
    require(has_any(rubric, "5 to 10", "5–10"), "rubric must state the 5-10 range")
    require(has(rubric, "50%"), "rubric must state the 50% bar")
    require(
        has(rubric, "without opening this repository"),
        "rubric must keep probes transferable",
    )

    # --- Scenario: curated track ------------------------------------------
    require(
        has(deep, "study-researcher"), "deep must delegate research to the subagent"
    )
    require(has(deep, "at most five"), "deep must cap the track at five resources")
    require(
        has(deep, "always continue") and has(deep, "study-probe"),
        "deep must always continue into a one-topic probe",
    )
    require(
        has(deep, "must not write covered"),
        "deep must state that finishing a track is not covered",
    )
    require(
        has(researcher, "readonly: true"), "study-researcher must stay read-only"
    )
    require(
        has(researcher, "Do not") and has(researcher, "covered"),
        "study-researcher must be forbidden from writing profile state",
    )

    # --- Scenario: manual log ----------------------------------------------
    require(
        has(log, "disable-model-invocation: true"),
        "study-log must stay explicit-only",
    )
    require(
        has(log, "study-probe"),
        "study-log must route a learned-claim to a probe instead of covered",
    )
    require(has(log, "cli.py init"), "study-log must own profile creation")

    # --- Scenario: read-only plan ------------------------------------------
    require(
        has(plan, "read-only") or has(plan, "Read-only"),
        "study-plan must announce itself as read-only",
    )
    require(
        re.search(r"do not run\s+`?init`?", plan, re.I) is not None,
        "study-plan must forbid init/want/covered writes",
    )
    require(
        has(plan, "/study-log"),
        "an empty profile in study-plan must point at /study-log",
    )
    require(has(plan, "cli.py show"), "study-plan must read state from the CLI")

    if errors:
        print("Scenario matrix verification failed:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("Scenario matrix structural checks passed.")
    print("Live Agent confirmation still needed in Cursor for:")
    print("  - active-context panel on ordinary vs learning turns")
    print("  - end-to-end probe scoring with real answers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
