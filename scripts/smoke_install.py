#!/usr/bin/env python3
"""Local install / packaging smoke for Learning Tutor.

Verifies the plugin manifest paths, rule activation modes, Skill packages, and
optionally installs the stable CLI under ~/.cursor/learning (same files
sessionStart would copy).

Usage (from repo root):
  python3 scripts/smoke_install.py
  python3 scripts/smoke_install.py --install-cli
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def load_plugin() -> dict:
    path = ROOT / ".cursor-plugin" / "plugin.json"
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def check_manifest_paths(plugin: dict) -> None:
    for key in ("rules", "agents", "skills", "hooks"):
        rel = plugin.get(key)
        if not rel:
            fail(f"plugin.json missing {key}")
        path = (ROOT / rel).resolve()
        if not path.exists():
            fail(f"plugin.json {key}={rel} does not exist")
    print(f"OK manifest paths (v{plugin.get('version', '?')})")


def check_rules() -> None:
    rules_dir = ROOT / "rules"
    always = []
    intelligent = []
    for path in sorted(rules_dir.glob("*.mdc")):
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        if not match:
            fail(f"{path.name}: missing frontmatter")
        fm = match.group(1)
        if re.search(r"alwaysApply:\s*true", fm):
            always.append(path.name)
        else:
            intelligent.append(path.name)
    if always != ["tutor-core.mdc"]:
        fail(f"expected only tutor-core always-on, found {always}")
    expected_intelligent = {
        "concept-gap-capture.mdc",
        "learning-recording.mdc",
        "project-learning-boundary.mdc",
    }
    if set(intelligent) != expected_intelligent:
        fail(f"unexpected intelligent rules: {intelligent}")
    print("OK rules context map:")
    print(f"  always-on: {', '.join(always)}")
    print(f"  intelligent: {', '.join(intelligent)}")
    print("  ordinary coding turn → expect tutor-core only (others by intent)")
    print("  learning turn → core + matching intelligent rule(s)")


def check_skills() -> None:
    skills = ROOT / "skills"
    required = ["study-log", "study-plan", "study-probe", "study-deep"]
    for name in required:
        skill = skills / name / "SKILL.md"
        if not skill.is_file():
            fail(f"missing {skill.relative_to(ROOT)}")
    rubric = skills / "study-probe" / "references" / "assessment-rubric.md"
    if not rubric.is_file():
        fail(f"missing {rubric.relative_to(ROOT)}")
    print(f"OK skills packages: {', '.join(required)}")


def install_cli() -> None:
    dest = Path.home() / ".cursor" / "learning"
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("learning_cli.py", "lib_profile.py"):
        src = ROOT / "hooks" / name
        if not src.is_file():
            fail(f"missing {src.relative_to(ROOT)}")
        target = dest / ("cli.py" if name == "learning_cli.py" else name)
        shutil.copy2(src, target)
        print(f"OK installed {target}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--install-cli",
        action="store_true",
        help="Copy hooks CLI into ~/.cursor/learning/",
    )
    args = parser.parse_args()
    plugin = load_plugin()
    check_manifest_paths(plugin)
    check_rules()
    check_skills()
    if args.install_cli:
        install_cli()
    print("Smoke install checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
