#!/usr/bin/env python3
"""Architecture checks for Learning Tutor rules and skills.

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
RECORDING = RULES / "learning-recording.mdc"
TUTOR_CORE = RULES / "tutor-core.mdc"
BOUNDARY = RULES / "project-learning-boundary.mdc"

CLI_WANT_RE = re.compile(r"cli\.py\s+want\b")
CLI_COVERED_RE = re.compile(r"cli\.py\s+covered\b")
GATE_PHRASE = "Would this still be useful without opening this repository?"
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def iter_text_files(*dirs: Path):
    for base in dirs:
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".mdc"}:
                yield path


def check_cli_writes() -> list[str]:
    """covered CLI only in learning-recording; want also allowed in tutor-core."""
    errors = []
    for path in iter_text_files(RULES, SKILLS):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        for i, line in enumerate(text.splitlines(), 1):
            if CLI_COVERED_RE.search(line) and path.resolve() != RECORDING.resolve():
                errors.append(
                    f"{rel}:{i}: cli.py covered must live only in "
                    f"rules/learning-recording.mdc"
                )
            if CLI_WANT_RE.search(line):
                allowed = {
                    RECORDING.resolve(),
                    TUTOR_CORE.resolve(),
                }
                if path.resolve() not in allowed:
                    errors.append(
                        f"{rel}:{i}: cli.py want must live only in "
                        f"rules/learning-recording.mdc or rules/tutor-core.mdc"
                    )
    return errors


def check_transferability_gate() -> list[str]:
    """No full transferability gate outside project-learning-boundary.mdc."""
    errors = []
    for path in iter_text_files(RULES, SKILLS):
        if path.resolve() == BOUNDARY.resolve():
            continue
        text = path.read_text(encoding="utf-8")
        if GATE_PHRASE in text:
            rel = path.relative_to(ROOT)
            errors.append(
                f"{rel}: full transferability gate must live only in "
                f"rules/project-learning-boundary.mdc"
            )
    return errors


def check_mdc_frontmatter() -> list[str]:
    """Valid .mdc frontmatter and exactly one alwaysApply: true (tutor-core)."""
    errors = []
    always_apply_true: list[Path] = []
    for path in sorted(RULES.glob("*.mdc")):
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        if not match:
            errors.append(f"{path.relative_to(ROOT)}: missing YAML frontmatter")
            continue
        fm = match.group(1)
        if "description:" not in fm:
            errors.append(
                f"{path.relative_to(ROOT)}: frontmatter missing description"
            )
        if "alwaysApply:" not in fm:
            errors.append(
                f"{path.relative_to(ROOT)}: frontmatter missing alwaysApply"
            )
        if re.search(r"alwaysApply:\s*true", fm):
            always_apply_true.append(path)
    if len(always_apply_true) != 1:
        names = ", ".join(p.name for p in always_apply_true) or "(none)"
        errors.append(
            f"expected exactly one alwaysApply: true runtime rule, found "
            f"{len(always_apply_true)}: {names}"
        )
    elif always_apply_true[0].name != "tutor-core.mdc":
        errors.append(
            f"alwaysApply: true must be tutor-core.mdc, found "
            f"{always_apply_true[0].name}"
        )
    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(check_cli_writes())
    errors.extend(check_transferability_gate())
    errors.extend(check_mdc_frontmatter())
    if errors:
        print("Architecture checks failed:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(
        "Architecture checks passed "
        "(CLI write, transferability gate, rule frontmatter)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
