#!/usr/bin/env python3
"""Local install / packaging smoke for Learning Tutor.

Verifies the plugin manifest paths, rule activation modes, Skill packages,
hooks.json script resolution, the study-researcher Agent contract, and
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
    required = [
        "study-log",
        "study-plan",
        "study-probe",
        "study-deep",
        "learning-explanations",
    ]
    for name in required:
        skill = skills / name / "SKILL.md"
        if not skill.is_file():
            fail(f"missing {skill.relative_to(ROOT)}")
    rubric = skills / "study-probe" / "references" / "assessment-rubric.md"
    if not rubric.is_file():
        fail(f"missing {rubric.relative_to(ROOT)}")
    print(f"OK skills packages: {', '.join(required)}")


ADAPTER_SCRIPTS = ("inject_profile.py", "capture_learning.py")
ADAPTER_LINE_BUDGET = {
    "inject_profile.py": 60,
    "capture_learning.py": 55,
    "hook_io.py": 120,
}
HOOK_TIMEOUTS = {
    "sessionStart": 10,
    "afterAgentResponse": 5,
}


def check_hooks_json(plugin: dict) -> None:
    rel = plugin.get("hooks")
    hooks_path = (ROOT / rel).resolve()
    if not hooks_path.is_file():
        fail(f"hooks path is not a file: {rel}")
    data = json.loads(hooks_path.read_text(encoding="utf-8"))
    if data.get("version") != 1:
        fail(f"hooks.json version must be 1, found {data.get('version')}")
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        fail("hooks.json missing hooks object")
    expected_events = ("sessionStart", "afterAgentResponse")
    referenced: set[str] = set()
    for event in expected_events:
        entries = hooks.get(event)
        if not isinstance(entries, list) or not entries:
            fail(f"hooks.json missing {event} entries")
        for entry in entries:
            command = entry.get("command", "")
            if not isinstance(command, str) or not command.strip():
                fail(f"hooks.json {event} entry missing command")
            timeout = entry.get("timeout")
            expected_timeout = HOOK_TIMEOUTS[event]
            if timeout != expected_timeout:
                fail(
                    f"hooks.json {event} timeout must be {expected_timeout}, "
                    f"found {timeout!r}"
                )
            for match in re.finditer(
                r"\$CURSOR_PLUGIN_ROOT/(hooks/[^\"'\s]+)", command
            ):
                rel_script = match.group(1)
                script = (ROOT / rel_script).resolve()
                if not script.is_file():
                    fail(f"hooks.json {event} references missing {rel_script}")
                name = Path(rel_script).name
                referenced.add(name)
                if name not in ADAPTER_SCRIPTS:
                    fail(
                        f"hooks.json {event} must reference only adapters "
                        f"{ADAPTER_SCRIPTS}, found {name}"
                    )
    for name in ADAPTER_SCRIPTS:
        if name not in referenced:
            fail(f"hooks.json must reference adapter {name}")
    required_scripts = {
        "inject_profile.py",
        "capture_learning.py",
        "lib_profile.py",
        "hook_io.py",
    }
    present = {p.name for p in (ROOT / "hooks").glob("*.py")}
    missing = sorted(required_scripts - present)
    if missing:
        fail(f"hooks/ missing scripts: {', '.join(missing)}")
    learning_pkg = ROOT / "runtime" / "learning" / "__init__.py"
    if not learning_pkg.is_file():
        fail("missing runtime/learning package")
    if not (ROOT / "runtime" / "cli.py").is_file():
        fail("missing runtime/cli.py")
    for name, budget in ADAPTER_LINE_BUDGET.items():
        path = ROOT / "hooks" / name
        lines = len(path.read_text(encoding="utf-8").splitlines())
        if lines > budget:
            fail(f"{name} exceeds adapter line budget ({lines} > {budget})")
    print(
        "OK hooks.json "
        f"(events: {', '.join(expected_events)}; adapters only; "
        f"timeouts ok; line budgets ok; runtime/learning package)"
    )


def check_agent() -> None:
    agent = ROOT / "agents" / "study-researcher.md"
    if not agent.is_file():
        fail("missing agents/study-researcher.md")
    text = agent.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        fail("study-researcher.md missing YAML frontmatter")
    fm = match.group(1)
    if not re.search(r"(?m)^name:\s*study-researcher\s*$", fm):
        fail("study-researcher.md frontmatter name must be study-researcher")
    if "description:" not in fm:
        fail("study-researcher.md frontmatter missing description")
    if not re.search(r"(?m)^model:\s*inherit\s*$", fm):
        fail("study-researcher.md frontmatter model must be inherit")
    if not re.search(r"(?m)^readonly:\s*true\s*$", fm):
        fail("study-researcher.md frontmatter readonly must be true")
    body = text[match.end() :]
    for needle in (
        "Boundary (non-negotiable)",
        "Expected input (from `study-deep`)",
        "Output format",
        "Do **not** run a probe",
        "Do **not** write `covered`",
    ):
        if needle not in body:
            fail(f"study-researcher.md missing contract phrase: {needle}")
    deep = ROOT / "skills" / "study-deep" / "SKILL.md"
    deep_text = deep.read_text(encoding="utf-8")
    if "study-researcher" not in deep_text:
        fail("skills/study-deep/SKILL.md must reference study-researcher")
    for needle in (
        "research/curation only",
        "study-probe",
        "write `covered`",
    ):
        if needle not in deep_text:
            fail(f"study-deep/SKILL.md missing handoff phrase: {needle}")
    print("OK agent study-researcher (frontmatter + I/O boundary + study-deep link)")


def install_cli() -> None:
    dest = Path.home() / ".cursor" / "learning"
    dest.mkdir(parents=True, exist_ok=True)
    cli_src = ROOT / "runtime" / "cli.py"
    shim_src = ROOT / "hooks" / "lib_profile.py"
    package_src = ROOT / "runtime" / "learning"
    if not cli_src.is_file():
        fail(f"missing {cli_src.relative_to(ROOT)}")
    if not shim_src.is_file():
        fail(f"missing {shim_src.relative_to(ROOT)}")
    if not package_src.is_dir():
        fail("missing runtime/learning package")
    shutil.copy2(cli_src, dest / "cli.py")
    print(f"OK installed {dest / 'cli.py'}")
    shutil.copy2(shim_src, dest / "lib_profile.py")
    print(f"OK installed {dest / 'lib_profile.py'}")
    package_dest = dest / "learning"
    if package_dest.exists():
        shutil.rmtree(package_dest)
    shutil.copytree(package_src, package_dest)
    print(f"OK installed {package_dest}")


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
    check_hooks_json(plugin)
    check_agent()
    if args.install_cli:
        install_cli()
    print("Smoke install checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
