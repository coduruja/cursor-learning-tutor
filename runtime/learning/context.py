"""Bounded context rendering for sessionStart injection."""

from __future__ import annotations

import sys
from pathlib import Path

from learning.paths import PROFILE_PATH, find_project_sheet
from learning.profile import profile_is_empty, read_profile


def truncate_for_inject(content: str, max_chars: int = 6000) -> str:
    if len(content) <= max_chars:
        return content
    return content[:800] + "\n...\n" + content[-(max_chars - 800) :]


def _diag(message: str) -> None:
    print(f"learning-tutor: {message}", file=sys.stderr)


def render_session_context(workspace_roots: list[str] | None = None) -> str:
    """Build LEARNING-PROFILE + LEARNING-PROJECT additional_context text."""
    parts: list[str] = []
    try:
        if not PROFILE_PATH.exists():
            parts.append(
                "LEARNING-PROFILE: profile is still empty. "
                "At the first useful moment, run a short onboarding (overall level + focus) "
                "with `python3 ~/.cursor/learning/cli.py init --level ... --focus ...` "
                "or ask the user to run `/study-plan` / `/study-log`."
            )
        else:
            content = truncate_for_inject(read_profile())
            empty_hint = ""
            if profile_is_empty():
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
        _diag(f"profile context failed: {exc}")
        parts.append(
            "LEARNING-PROFILE: unavailable this session "
            "(profile read failed; CLI may still work after install)."
        )

    try:
        project_file = find_project_sheet(
            workspace_roots=workspace_roots or None,
            walk_ancestors=True,
        )
        if project_file is not None:
            project_text = truncate_for_inject(
                Path(project_file).read_text(encoding="utf-8"),
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
        _diag(f"project context failed: {exc}")
        parts.append("LEARNING-PROJECT: unavailable this session (lookup failed).")

    return "\n\n".join(parts)
