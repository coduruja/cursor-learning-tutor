"""Learning Tutor library package (profile, project sheet, install)."""

from __future__ import annotations

from learning.context import render_session_context, truncate_for_inject
from learning.install import install_cli
from learning.markers import WANT_RE, iter_want_markers
from learning.paths import (
    CLI_PATH,
    LEARNING_DIR,
    LEGACY_PROJECT_RELATIVE_PATH,
    LIB_PATH,
    PROFILE_PATH,
    PROJECT_RELATIVE_PATH,
    ensure_dir,
    find_project_sheet,
    legacy_project_path,
    project_path,
    resolve_project_root,
)
from learning.profile import (
    add_covered,
    add_want,
    ensure_profile,
    first_open_queue_topic,
    init_profile,
    mark_done,
    profile_is_empty,
    read_profile,
)
from learning.project import (
    ensure_project,
    project_drop_candidate,
    project_show,
    project_sync,
    read_project,
)
from learning.topics import (
    BASE_LANGUAGES,
    GENERIC_TOPICS,
    LEVELS,
    TOPIC_ALIASES,
    is_noisy_topic,
    normalize_topic_display,
    topic_key,
)

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
    "WANT_RE",
    "init_profile",
    "install_cli",
    "is_noisy_topic",
    "iter_want_markers",
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
    "render_session_context",
    "resolve_project_root",
    "topic_key",
    "truncate_for_inject",
]
