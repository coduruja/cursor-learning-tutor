#!/usr/bin/env python3
"""Release verification for Learning Tutor (Phase F).

Runs the automated matrix (architecture, install smoke, scenarios, hooks/agents
harness). Prints the remaining live Cursor checklist that cannot be simulated
here.

Usage (from repo root):
  python3 scripts/verify_release.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKS = (
    ("architecture", ["python3", "scripts/check_architecture.py"]),
    ("smoke_install", ["python3", "scripts/smoke_install.py"]),
    ("scenarios", ["python3", "scripts/verify_scenarios.py"]),
    ("hooks_agents", ["python3", "scripts/test_hooks_agents.py"]),
)

LIVE_CHECKLIST = """
Live Cursor checklist (manual — open a new Agent chat after plugin install):

  [ ] Fresh session, no ~/.cursor/learning/profile.md
      → sessionStart installs CLI; LEARNING-PROFILE empty onboarding hint
  [ ] Session with global profile + .cursor/learning/project.md
      → LEARNING-PROFILE and LEARNING-PROJECT appear in context
  [ ] Valid LEARNING-WANT marker when CLI is missing
      → queue entry written; fail-open JSON
  [ ] Invalid empty-topic LEARNING-WANT
      → stderr skip; no bogus queue line; later valid markers still work
  [ ] /study-deep <topic>
      → study-researcher returns a ≤5-item track
      → study-deep always continues into one-topic study-probe
      → researcher does not write want/covered
""".strip()


def run_check(name: str, cmd: list[str]) -> bool:
    print(f"\n=== {name} ===")
    result = subprocess.run(cmd, cwd=ROOT, check=False)
    if result.returncode != 0:
        print(f"FAIL: {name} (exit {result.returncode})")
        return False
    print(f"PASS: {name}")
    return True


def main() -> int:
    print("Learning Tutor release verification")
    print(f"repo: {ROOT}")
    ok = True
    for name, cmd in CHECKS:
        if not run_check(name, cmd):
            ok = False
    print("\n" + "=" * 60)
    if ok:
        print("Automated matrix: PASS")
    else:
        print("Automated matrix: FAIL")
        return 1
    print()
    print(LIVE_CHECKLIST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
