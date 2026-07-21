"""Compatibility shim for Learning Tutor profile helpers.

Public import path for Hooks and the installed CLI:
  hooks/lib_profile.py
  ~/.cursor/learning/lib_profile.py

Implementation lives in the sibling `learning` package. This module re-exports
the stable API so older loaders keep working.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from learning import (  # noqa: E402
    BASE_LANGUAGES,
    CLI_PATH,
    GENERIC_TOPICS,
    LEARNING_DIR,
    LEGACY_PROJECT_RELATIVE_PATH,
    LEVELS,
    LIB_PATH,
    PROFILE_PATH,
    PROJECT_RELATIVE_PATH,
    TOPIC_ALIASES,
    add_covered,
    add_want,
    ensure_dir,
    ensure_profile,
    ensure_project,
    find_project_sheet,
    first_open_queue_topic,
    init_profile,
    install_cli,
    is_noisy_topic,
    legacy_project_path,
    mark_done,
    normalize_topic_display,
    profile_is_empty,
    project_drop_candidate,
    project_path,
    project_show,
    project_sync,
    read_profile,
    read_project,
    resolve_project_root,
    topic_key,
    truncate_for_inject,
)
from learning import paths as _paths  # noqa: E402

__all__ = [
    "BASE_LANGUAGES",
    "CLI_PATH",
    "GENERIC_TOPICS",
    "LEARNING_DIR",
    "LEGACY_PROJECT_RELATIVE_PATH",
    "LEVELS",
    "LIB_PATH",
    "PROFILE_PATH",
    "PROJECT_RELATIVE_PATH",
    "TOPIC_ALIASES",
    "add_covered",
    "add_want",
    "ensure_dir",
    "ensure_profile",
    "ensure_project",
    "find_project_sheet",
    "first_open_queue_topic",
    "init_profile",
    "install_cli",
    "is_noisy_topic",
    "legacy_project_path",
    "mark_done",
    "normalize_topic_display",
    "profile_is_empty",
    "project_drop_candidate",
    "project_path",
    "project_show",
    "project_sync",
    "read_profile",
    "read_project",
    "resolve_project_root",
    "topic_key",
    "truncate_for_inject",
]


def rebind_home(home: str | Path) -> None:
    """Tests: point paths at a temporary HOME and refresh shim aliases."""
    _paths.rebind_home(home)
    global LEARNING_DIR, PROFILE_PATH, CLI_PATH, LIB_PATH
    LEARNING_DIR = _paths.LEARNING_DIR
    PROFILE_PATH = _paths.PROFILE_PATH
    CLI_PATH = _paths.CLI_PATH
    LIB_PATH = _paths.LIB_PATH
