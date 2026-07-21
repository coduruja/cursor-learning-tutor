"""Global and project path helpers."""

from __future__ import annotations

import os
from pathlib import Path

LEARNING_DIR = Path(os.path.expanduser("~/.cursor/learning"))
PROFILE_PATH = LEARNING_DIR / "profile.md"
CLI_PATH = LEARNING_DIR / "cli.py"
LIB_PATH = LEARNING_DIR / "lib_profile.py"
PACKAGE_DIR_NAME = "learning"
PROJECT_RELATIVE_PATH = Path(".cursor") / "learning" / "project.md"
LEGACY_PROJECT_RELATIVE_PATH = Path(".cursor") / "learning-project.md"


def ensure_dir() -> None:
    LEARNING_DIR.mkdir(parents=True, exist_ok=True)


def resolve_project_root(
    cwd: str | Path | None = None,
    workspace_roots: list[str] | None = None,
) -> Path:
    """Resolve the project root used for sheet paths.

    Precedence (HOOKS_AGENTS_CONTRACTS.md §4):
    1. explicit cwd / --cwd
    2. first existing absolute path in workspace_roots
    3. Path.cwd()
    """
    if cwd is not None and str(cwd).strip():
        return Path(cwd).expanduser().resolve()
    for root in workspace_roots or []:
        path = Path(root).expanduser()
        if path.is_absolute() and path.exists():
            return path.resolve()
    return Path.cwd().resolve()


def project_path(
    cwd: str | Path | None = None,
    workspace_roots: list[str] | None = None,
) -> Path:
    root = resolve_project_root(cwd=cwd, workspace_roots=workspace_roots)
    return root / PROJECT_RELATIVE_PATH


def legacy_project_path(
    cwd: str | Path | None = None,
    workspace_roots: list[str] | None = None,
) -> Path:
    root = resolve_project_root(cwd=cwd, workspace_roots=workspace_roots)
    return root / LEGACY_PROJECT_RELATIVE_PATH


def find_project_sheet(
    start: str | Path | None = None,
    *,
    workspace_roots: list[str] | None = None,
    walk_ancestors: bool = False,
    max_ancestors: int = 8,
) -> Path | None:
    """Locate an existing project sheet.

    When walk_ancestors is True (sessionStart injection), search up to
    max_ancestors parents. CLI writes keep walk_ancestors=False.
    """
    cur = resolve_project_root(cwd=start, workspace_roots=workspace_roots)
    steps = max_ancestors if walk_ancestors else 0
    for _ in range(steps + 1):
        for candidate in (
            cur / PROJECT_RELATIVE_PATH,
            cur / LEGACY_PROJECT_RELATIVE_PATH,
        ):
            if candidate.is_file():
                return candidate
        if not walk_ancestors or cur.parent == cur:
            break
        cur = cur.parent
    return None


def rebind_home(home: str | Path) -> None:
    """Point global learning paths at a different HOME (tests / isolation)."""
    global LEARNING_DIR, PROFILE_PATH, CLI_PATH, LIB_PATH
    LEARNING_DIR = Path(home).expanduser() / ".cursor" / "learning"
    PROFILE_PATH = LEARNING_DIR / "profile.md"
    CLI_PATH = LEARNING_DIR / "cli.py"
    LIB_PATH = LEARNING_DIR / "lib_profile.py"
