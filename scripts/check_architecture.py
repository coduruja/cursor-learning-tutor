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
BOUNDARY = RULES / "project-learning-boundary.mdc"

CLI_WRITE_RE = re.compile(r"cli\.py\s+(want|covered)\b")
GATE_PHRASE = "Would this still be useful without opening this repository?"


def iter_text_files(*dirs: Path):
    for base in dirs:
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".mdc"}:
                yield path


def check_cli_writes() -> list[str]:
    """No cli.py want/covered outside rules/learning-recording.mdc."""
    errors = []
    for path in iter_text_files(RULES, SKILLS):
        if path.resolve() == RECORDING.resolve():
            continue
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            if CLI_WRITE_RE.search(line):
                rel = path.relative_to(ROOT)
                errors.append(
                    f"{rel}:{i}: cli.py want/covered must live only in "
                    f"rules/learning-recording.mdc"
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


def main() -> int:
    errors: list[str] = []
    errors.extend(check_cli_writes())
    errors.extend(check_transferability_gate())
    if errors:
        print("Architecture checks failed:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("Architecture checks passed (CLI write + transferability gate).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
