#!/usr/bin/env python3
"""Stable Learning Tutor CLI.

Typical usage (stable path after the first sessionStart):
  python3 ~/.cursor/learning/cli.py covered --topic "Closures" --level intermediate --note "..."
  python3 ~/.cursor/learning/cli.py want --topic "Docker" --note "for deploy"
  python3 ~/.cursor/learning/cli.py done --topic "Docker"
  python3 ~/.cursor/learning/cli.py init --level intermediate --focus "backend"
  python3 ~/.cursor/learning/cli.py show
  python3 ~/.cursor/learning/cli.py project-show
  python3 ~/.cursor/learning/cli.py project-sync --stack "Next.js;Prisma" --candidates "App Router;Prisma migrations"
  python3 ~/.cursor/learning/cli.py project-drop --topic "App Router"
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def _load_lib():
    here = Path(__file__).resolve().parent
    candidates = [
        here / "lib_profile.py",
        here.parent / "hooks" / "lib_profile.py",
        Path.home() / ".cursor" / "learning" / "lib_profile.py",
    ]
    for path in candidates:
        if path.exists():
            spec = importlib.util.spec_from_file_location("lib_profile", path)
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            return mod
    raise SystemExit("lib_profile.py not found. Reinstall the Learning Tutor plugin.")


def main() -> None:
    lib = _load_lib()
    parser = argparse.ArgumentParser(prog="learning-cli", description="Learning Tutor profile CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Create/update profile meta")
    p_init.add_argument("--level", default="intermediate")
    p_init.add_argument("--focus", default="undefined")

    p_cov = sub.add_parser("covered", help="Record a covered/learned topic")
    p_cov.add_argument("--topic", required=True)
    p_cov.add_argument("--level", default="intermediate")
    p_cov.add_argument("--note", default="")

    p_want = sub.add_parser("want", help="Add a topic to the study queue")
    p_want.add_argument("--topic", required=True)
    p_want.add_argument("--note", default="")

    p_done = sub.add_parser("done", help="Mark a queue item as done")
    p_done.add_argument("--topic", required=True)

    sub.add_parser("show", help="Show the profile")
    sub.add_parser("queue-next", help="Show the first open queue item")

    p_ps = sub.add_parser("project-show", help="Show .cursor/learning/project.md")
    p_ps.add_argument("--cwd", default="", help="Project root (default: cwd)")

    p_sync = sub.add_parser("project-sync", help="Update project stack/candidates/probe")
    p_sync.add_argument("--stack", default="", help="Items separated by ; or ,")
    p_sync.add_argument("--candidates", default="", help="Candidates separated by ;")
    p_sync.add_argument("--probe-summary", default="", help="Last probe summary")
    p_sync.add_argument("--cwd", default="", help="Project root (default: cwd)")

    p_drop = sub.add_parser("project-drop", help="Remove a project candidate")
    p_drop.add_argument("--topic", required=True)
    p_drop.add_argument("--cwd", default="", help="Project root (default: cwd)")

    args = parser.parse_args()
    cwd = args.cwd if getattr(args, "cwd", "") else None

    if args.cmd == "init":
        print(lib.init_profile(args.level, args.focus))
    elif args.cmd == "covered":
        print(lib.add_covered(args.topic, args.level, args.note))
    elif args.cmd == "want":
        print(lib.add_want(args.topic, args.note))
    elif args.cmd == "done":
        print(lib.mark_done(args.topic))
    elif args.cmd == "show":
        lib.ensure_profile()
        print(lib.read_profile())
    elif args.cmd == "queue-next":
        topic = lib.first_open_queue_topic()
        print(topic if topic else "(empty queue)")
    elif args.cmd == "project-show":
        print(lib.project_show(cwd))
    elif args.cmd == "project-sync":
        print(
            lib.project_sync(
                stack=args.stack,
                candidates=args.candidates,
                probe_summary=args.probe_summary,
                cwd=cwd,
            )
        )
    elif args.cmd == "project-drop":
        print(lib.project_drop_candidate(args.topic, cwd))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 — CLI must never crash the agent awkwardly
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
