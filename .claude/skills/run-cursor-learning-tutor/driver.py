#!/usr/bin/env python3
"""Driver for the Learning Tutor Cursor plugin.

This plugin has no window and no server — its only runtime surface is two
Cursor Hooks (JSON on stdin -> JSON on stdout) plus a small CLI they install.
This driver invokes that exact surface as a real Cursor session would, but
with HOME redirected to a sandbox directory, so nothing ever touches the
real ~/.cursor/learning/profile.md on the machine running this driver.

Usage (from repo root):
  python3 .claude/skills/run-cursor-learning-tutor/driver.py session
  python3 .claude/skills/run-cursor-learning-tutor/driver.py session --workspace-root <path>
  python3 .claude/skills/run-cursor-learning-tutor/driver.py capture --text '...<!-- LEARNING-WANT topic="Docker" -->'
  python3 .claude/skills/run-cursor-learning-tutor/driver.py cli show
  python3 .claude/skills/run-cursor-learning-tutor/driver.py cli want --topic Docker --note "for deploy"
  python3 .claude/skills/run-cursor-learning-tutor/driver.py project-show --cwd <project-dir>
  python3 .claude/skills/run-cursor-learning-tutor/driver.py verify-clean

All subcommands share one sandbox HOME so state (profile.md, installed CLI)
persists across calls. Default sandbox: $TMPDIR/learning-tutor-driver-sandbox
(override with --home or LEARNING_TUTOR_DRIVER_HOME). Use --fresh to wipe it
first.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HOOKS = ROOT / "hooks"
DEFAULT_SANDBOX = Path(tempfile.gettempdir()) / "learning-tutor-driver-sandbox"
REAL_PROFILE = Path(os.path.expanduser("~/.cursor/learning/profile.md"))


def _hash(path: Path) -> str:
    if not path.is_file():
        return "(absent)"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_hook(script: Path, home: Path, payload: dict) -> dict:
    env = dict(os.environ)
    env["HOME"] = str(home)
    result = subprocess.run(
        ["python3", str(script)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=ROOT,
        env=env,
        check=False,
    )
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    if result.returncode != 0:
        print(f"hook exited {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"hook did not emit JSON: {result.stdout!r}", file=sys.stderr)
        sys.exit(1)


def cmd_session(args: argparse.Namespace) -> None:
    home = Path(args.home)
    payload: dict = {}
    if args.workspace_root:
        payload["workspace_roots"] = args.workspace_root
    cwd_note = f" (cwd={args.cwd})" if args.cwd else ""
    print(f"HOME={home}{cwd_note}", file=sys.stderr)
    out = run_hook(HOOKS / "inject_profile.py", home, payload)
    print(json.dumps(out, indent=2, ensure_ascii=False))


def cmd_capture(args: argparse.Namespace) -> None:
    home = Path(args.home)
    text = args.text
    if args.stdin:
        text = sys.stdin.read()
    out = run_hook(HOOKS / "capture_learning.py", home, {"text": text or ""})
    print(json.dumps(out, indent=2, ensure_ascii=False))


def cmd_cli(args: argparse.Namespace) -> None:
    home = Path(args.home)
    cli_path = home / ".cursor" / "learning" / "cli.py"
    if not cli_path.is_file():
        # Same install step sessionStart performs; do it once up front.
        run_hook(HOOKS / "inject_profile.py", home, {})
    env = dict(os.environ)
    env["HOME"] = str(home)
    result = subprocess.run(
        ["python3", str(cli_path), *args.cli_args],
        cwd=ROOT,
        env=env,
        check=False,
    )
    sys.exit(result.returncode)


def cmd_project_show(args: argparse.Namespace) -> None:
    args.cli_args = ["project-show", "--cwd", args.cwd]
    cmd_cli(args)


def cmd_verify_clean(args: argparse.Namespace) -> None:
    home = Path(args.home)
    print(f"sandbox HOME:      {home}")
    print(f"real HOME profile: {REAL_PROFILE}")
    if home.resolve() == Path(os.path.expanduser("~")).resolve():
        print("REFUSING: sandbox --home resolves to the real HOME.", file=sys.stderr)
        sys.exit(1)
    print(f"real profile sha256: {_hash(REAL_PROFILE)}")
    print("(compare this hash before/after a driver session to confirm it never changed)")


def cmd_reset(args: argparse.Namespace) -> None:
    home = Path(args.home)
    if home.resolve() == Path(os.path.expanduser("~")).resolve():
        print("REFUSING: --home resolves to the real HOME.", file=sys.stderr)
        sys.exit(1)
    shutil.rmtree(home, ignore_errors=True)
    print(f"removed {home}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--home",
        default=os.environ.get("LEARNING_TUTOR_DRIVER_HOME", str(DEFAULT_SANDBOX)),
        help="Sandbox HOME (default: %(default)s)",
    )
    parser.add_argument("--fresh", action="store_true", help="Wipe the sandbox HOME before running")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_session = sub.add_parser("session", help="Run the sessionStart hook (installs CLI, injects context)")
    p_session.add_argument("--workspace-root", action="append", help="Repeatable; simulates Cursor's workspace_roots")
    p_session.add_argument("--cwd", default="", help="Informational only (hook itself has no OS cwd concept)")
    p_session.set_defaults(func=cmd_session)

    p_capture = sub.add_parser("capture", help="Run the afterAgentResponse hook against response text")
    p_capture.add_argument("--text", default="", help="Response text to scan for LEARNING-WANT markers")
    p_capture.add_argument("--stdin", action="store_true", help="Read text from stdin instead of --text")
    p_capture.set_defaults(func=cmd_capture)

    p_cli = sub.add_parser("cli", help="Passthrough to the installed learning CLI, e.g. `cli show`")
    p_cli.add_argument("cli_args", nargs=argparse.REMAINDER)
    p_cli.set_defaults(func=cmd_cli)

    p_proj = sub.add_parser("project-show", help="Shortcut for `cli project-show --cwd <dir>`")
    p_proj.add_argument("--cwd", required=True)
    p_proj.set_defaults(func=cmd_project_show)

    p_verify = sub.add_parser("verify-clean", help="Print real-profile hash + refuse if sandbox == real HOME")
    p_verify.set_defaults(func=cmd_verify_clean)

    p_reset = sub.add_parser("reset", help="Delete the sandbox HOME")
    p_reset.set_defaults(func=cmd_reset)

    args = parser.parse_args()
    home = Path(args.home)
    if home.resolve() == Path(os.path.expanduser("~")).resolve():
        print("REFUSING: --home resolves to the real HOME. Pick a sandbox path.", file=sys.stderr)
        sys.exit(1)
    if args.fresh:
        shutil.rmtree(home, ignore_errors=True)
    home.mkdir(parents=True, exist_ok=True)
    args.func(args)


if __name__ == "__main__":
    main()
