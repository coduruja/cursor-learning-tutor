#!/usr/bin/env python3
"""Architecture checks for Learning Tutor rules and skills.

Enforces the 3.0 structure:

  * exactly one always-on rule, under budget, owning the invariants;
  * skills that are self-contained (no delegation to a rule that may not load);
  * disjoint skill triggers, so the model is never asked to pick arbitrarily;
  * a single writer for `covered`.

Usage (from repo root):
  python3 scripts/check_architecture.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "rules"
SKILLS = ROOT / "skills"

ALWAYS_ON_RULE = "learning-tutor.mdc"
# Deliberately tight: the rule holds only turn classification and routing.
# Transferability, evidence law, and CLI mechanics live in the skills that
# actually use them — see .cursor/rules/authoring-protocols.mdc. Raise this
# only if routing itself grows, never to make room for policy prose.
ALWAYS_ON_LINE_BUDGET = 35

TRANSFERABILITY_PHRASE = "would this still be useful without opening this repository"
TRANSFERABILITY_OWNERS = {
    ROOT / "skills" / "concept-gap-capture" / "SKILL.md",
    ROOT / "skills" / "study-plan" / "SKILL.md",
    ROOT / "skills" / "study-log" / "SKILL.md",
    ROOT / "skills" / "study-probe" / "references" / "assessment-rubric.md",
}

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
CLI_WANT_RE = re.compile(r"cli\.py\s+want\b")
CLI_COVERED_RE = re.compile(r"cli\.py\s+covered\b")
CLI_INIT_RE = re.compile(r"cli\.py\s+init\b")

# Which skill owns which write. Self-containment means the owner spells the
# command out; non-owners must not carry it at all.
WANT_WRITERS = {"concept-gap-capture", "study-log", "study-probe", "study-deep"}
COVERED_WRITERS = {"study-probe"}
INIT_WRITERS = {"study-log"}

# A phrase must appear in at most one skill description, or the model has to
# guess which skill a request belongs to.
DISJOINT_TRIGGERS = {
    "conceptual gap": "concept-gap-capture",
    "quizzed": "study-probe",
    "curated": "study-deep",
    "progress snapshot": "study-plan",
    "/study-log": "study-log",
}

# Delegation to something that loads probabilistically. The 2.x architecture
# was built on these; they are what made the skills hollow.
FORBIDDEN_INDIRECTION = (
    "recording policy",
    "project-learning-boundary",
    "learning-recording",
    "tutor-core",
    "learning-explanations",
    "do not duplicate the cli",
)

EXPECTED_SKILLS = {
    "concept-gap-capture",
    "study-deep",
    "study-log",
    "study-plan",
    "study-probe",
}


def frontmatter(text: str) -> str | None:
    match = FRONTMATTER_RE.match(text)
    return match.group(1) if match else None


def normalize(text: str) -> str:
    """Collapse whitespace so a phrase re-wrapped across lines still matches."""
    return re.sub(r"\s+", " ", text).lower()


KEY_RE = re.compile(r"^[A-Za-z][\w-]*:")
NEGATIVE_LEAD = ("not for", "never ", "do not ", "not to ")


def description_of(fm: str) -> str:
    """The description value, unwrapped onto a single line."""
    lines = fm.splitlines()
    collected: list[str] = []
    capturing = False
    for line in lines:
        if KEY_RE.match(line):
            if capturing:
                break
            if line.startswith("description:"):
                capturing = True
                rest = line[len("description:") :].strip()
                if rest and rest not in {">-", ">", "|", "|-"}:
                    collected.append(rest)
            continue
        if capturing:
            collected.append(line.strip())
    return " ".join(part for part in collected if part)


def positive_description(fm: str) -> str:
    """Description with its exclusion clauses removed.

    A description says both what a skill is for and what it is not for. Only
    the positive half is a routing trigger — "Not for curated tracks" must not
    make a skill look like it owns curated tracks.
    """
    text = description_of(fm)
    keep = [
        sentence
        for sentence in re.split(r"(?<=[.;])\s+", text)
        if not sentence.strip().lower().startswith(NEGATIVE_LEAD)
    ]
    return " ".join(keep).lower()


def check_rules() -> list[str]:
    """One always-on rule, valid frontmatter, within the context budget."""
    errors: list[str] = []
    found = sorted(p.name for p in RULES.glob("*.mdc"))
    if found != [ALWAYS_ON_RULE]:
        errors.append(
            f"rules/ must contain exactly one rule ({ALWAYS_ON_RULE}), found: "
            f"{', '.join(found) or '(none)'}. Procedures belong in skills/; "
            f"a second always-on rule creates a competing baseline."
        )
        return errors

    path = RULES / ALWAYS_ON_RULE
    text = path.read_text(encoding="utf-8")
    fm = frontmatter(text)
    if fm is None:
        errors.append(f"rules/{ALWAYS_ON_RULE}: missing YAML frontmatter")
        return errors
    if "description:" not in fm:
        errors.append(f"rules/{ALWAYS_ON_RULE}: frontmatter missing description")
    if not re.search(r"alwaysApply:\s*true", fm):
        errors.append(
            f"rules/{ALWAYS_ON_RULE}: must be alwaysApply: true — the shipped "
            f"invariants cannot load probabilistically"
        )
    lines = len(text.splitlines())
    if lines > ALWAYS_ON_LINE_BUDGET:
        errors.append(
            f"rules/{ALWAYS_ON_RULE}: {lines} lines exceeds the always-on "
            f"budget of {ALWAYS_ON_LINE_BUDGET}; move procedure into a skill"
        )
    if TRANSFERABILITY_PHRASE in normalize(text):
        errors.append(
            f"rules/{ALWAYS_ON_RULE}: the transferability test is owned by "
            f"the skills that gate on it, not the always-on rule — inline it "
            f"in the relevant skill instead"
        )
    return errors


def check_transferability_ownership() -> list[str]:
    """The transferability test must be inlined in every skill that gates on
    it, since it decides whether that skill is allowed to write global state.
    """
    errors: list[str] = []
    for path in sorted(TRANSFERABILITY_OWNERS):
        if not path.is_file():
            errors.append(f"{path.relative_to(ROOT)}: expected file is missing")
            continue
        text = normalize(path.read_text(encoding="utf-8"))
        if TRANSFERABILITY_PHRASE not in text:
            errors.append(
                f"{path.relative_to(ROOT)}: must inline the transferability "
                f"test — it cannot assume the always-on rule still states it"
            )
    return errors


def skill_paths() -> dict[str, Path]:
    return {
        d.name: d / "SKILL.md"
        for d in sorted(SKILLS.iterdir())
        if d.is_dir() and (d / "SKILL.md").is_file()
    }


def check_skill_frontmatter(skills: dict[str, Path]) -> list[str]:
    """name matches the directory; description states use and non-use."""
    errors: list[str] = []
    if set(skills) != EXPECTED_SKILLS:
        missing = EXPECTED_SKILLS - set(skills)
        extra = set(skills) - EXPECTED_SKILLS
        if missing:
            errors.append(f"missing skills: {', '.join(sorted(missing))}")
        if extra:
            errors.append(f"unregistered skills: {', '.join(sorted(extra))}")
    for name, path in skills.items():
        text = path.read_text(encoding="utf-8")
        fm = frontmatter(text)
        rel = path.relative_to(ROOT)
        if fm is None:
            errors.append(f"{rel}: missing YAML frontmatter")
            continue
        if f"name: {name}" not in fm:
            errors.append(f"{rel}: frontmatter name must match directory ({name})")
        if "description:" not in fm:
            errors.append(f"{rel}: frontmatter missing description")
            continue
        lowered = fm.lower()
        if "not for" not in lowered and "never" not in lowered:
            errors.append(
                f"{rel}: description must exclude what it is NOT for, or it "
                f"will compete with a sibling skill for the same request"
            )
    return errors


def check_disjoint_triggers(skills: dict[str, Path]) -> list[str]:
    """No trigger phrase may match two skill descriptions."""
    errors: list[str] = []
    descriptions = {}
    for name, path in skills.items():
        fm = frontmatter(path.read_text(encoding="utf-8")) or ""
        descriptions[name] = positive_description(fm)
    for phrase, owner in DISJOINT_TRIGGERS.items():
        matches = [n for n, fm in descriptions.items() if phrase in fm]
        if matches != [owner]:
            errors.append(
                f"trigger {phrase!r} must appear in exactly one skill "
                f"description ({owner}), found: {', '.join(matches) or '(none)'}"
            )
    return errors


def check_self_containment(skills: dict[str, Path]) -> list[str]:
    """Skills spell out their own commands and delegate no policy by name."""
    errors: list[str] = []
    for name, path in skills.items():
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        lowered = text.lower()
        for phrase in FORBIDDEN_INDIRECTION:
            if phrase in lowered:
                errors.append(
                    f"{rel}: delegates to {phrase!r}; skills must be "
                    f"self-contained — inline the command it needs"
                )
        for regex, owners, label in (
            (CLI_WANT_RE, WANT_WRITERS, "cli.py want"),
            (CLI_COVERED_RE, COVERED_WRITERS, "cli.py covered"),
            (CLI_INIT_RE, INIT_WRITERS, "cli.py init"),
        ):
            present = bool(regex.search(text))
            if name in owners and not present:
                errors.append(f"{rel}: must inline `{label}` rather than delegate")
            if name not in owners and present:
                errors.append(
                    f"{rel}: must not contain `{label}` — owned by "
                    f"{', '.join(sorted(owners))}"
                )
    return errors


def check_references(skills: dict[str, Path]) -> list[str]:
    """Every referenced bundled file exists."""
    errors: list[str] = []
    link_re = re.compile(r"\]\((references/[^)]+)\)")
    for name, path in skills.items():
        text = path.read_text(encoding="utf-8")
        for rel_link in link_re.findall(text):
            target = path.parent / rel_link
            if not target.is_file():
                errors.append(
                    f"{path.relative_to(ROOT)}: broken reference {rel_link}"
                )
    return errors


def main() -> int:
    skills = skill_paths()
    errors: list[str] = []
    errors.extend(check_rules())
    errors.extend(check_transferability_ownership())
    errors.extend(check_skill_frontmatter(skills))
    errors.extend(check_disjoint_triggers(skills))
    errors.extend(check_self_containment(skills))
    errors.extend(check_references(skills))
    if errors:
        print("Architecture checks failed:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(
        "Architecture checks passed (single always-on rule, self-contained "
        "skills, disjoint triggers, single covered writer)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
