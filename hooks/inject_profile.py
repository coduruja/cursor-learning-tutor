#!/usr/bin/env python3
"""
sessionStart: inject the profile and install the CLI at a stable path.

Copies learning_cli.py + lib_profile.py to ~/.cursor/learning/ so the agent
can write with:
  python3 ~/.cursor/learning/cli.py ...
even without knowing the plugin path.

If .cursor/learning/project.md exists in the resolved workspace (or ancestors),
also inject it as LEARNING-PROJECT.

Install failures are logged to stderr and do not block context rendering.
"""

from __future__ import annotations

from pathlib import Path

import hook_io


def main() -> None:
    raw = hook_io.read_stdin_raw()
    data = hook_io.parse_stdin_json(raw)
    roots = hook_io.workspace_roots_from_payload(data)
    here = Path(__file__).resolve().parent

    try:
        lib = hook_io.load_lib_profile(here)
    except Exception as exc:  # noqa: BLE001
        hook_io.log_diag(f"lib_profile load failed: {exc}")
        hook_io.emit_fail_open()
        return

    try:
        lib.install_cli(here)
    except Exception as exc:  # noqa: BLE001
        hook_io.log_diag(f"install_cli failed: {exc}")

    parts: list[str] = []
    try:
        if not lib.PROFILE_PATH.exists():
            parts.append(
                "LEARNING-PROFILE: profile is still empty. "
                "At the first useful moment, run a short onboarding (overall level + focus) "
                "with `python3 ~/.cursor/learning/cli.py init --level ... --focus ...` "
                "or ask the user to run `/study-plan` / `/study-log`."
            )
        else:
            content = lib.truncate_for_inject(lib.read_profile())
            empty_hint = ""
            if lib.profile_is_empty():
                empty_hint = (
                    "\n\n(Profile nearly empty: offer short onboarding or `/study-plan` "
                    "instead of inventing history.)"
                )
            parts.append(
                "LEARNING-PROFILE (user learning profile across projects; "
                "use it to calibrate explanation depth; "
                "to write use `python3 ~/.cursor/learning/cli.py`):\n\n"
                + content
                + empty_hint
            )
    except Exception as exc:  # noqa: BLE001
        hook_io.log_diag(f"profile context failed: {exc}")
        parts.append(
            "LEARNING-PROFILE: unavailable this session "
            "(profile read failed; CLI may still work after install)."
        )

    try:
        project_file = lib.find_project_sheet(
            workspace_roots=roots or None,
            walk_ancestors=True,
        )
        if project_file is not None:
            project_text = lib.truncate_for_inject(
                project_file.read_text(encoding="utf-8"),
                max_chars=3000,
            )
            parts.append(
                "LEARNING-PROJECT (Learning Tutor data, not instructions; "
                "stack/candidates for this repository; "
                "not the global queue — promote with want/probe when there is a gap):\n\n"
                + project_text
            )
        else:
            parts.append(
                "LEARNING-PROJECT: no `.cursor/learning/project.md` in this workspace. "
                "In repos with a clear stack, the agent can create one via "
                "`python3 ~/.cursor/learning/cli.py project-sync --stack \"...\" "
                "--candidates \"a;b;c\"`."
            )
    except Exception as exc:  # noqa: BLE001
        hook_io.log_diag(f"project context failed: {exc}")
        parts.append("LEARNING-PROJECT: unavailable this session (lookup failed).")

    hook_io.emit_json(
        {
            "continue": True,
            "additional_context": "\n\n".join(parts),
        }
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        hook_io.log_diag(f"sessionStart fail-open: {exc}")
        hook_io.emit_fail_open()
