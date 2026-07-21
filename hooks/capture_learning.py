#!/usr/bin/env python3
"""
afterAgentResponse: capture LEARNING-WANT markers (want-only fallback).

Reads hook JSON from stdin, finds want markers the recording policy instructs
the agent to emit when the CLI is unavailable, and updates
~/.cursor/learning/profile.md.

Covered knowledge is never written from markers — only from one-topic probe
evidence via the CLI.
"""

from __future__ import annotations

import re
from pathlib import Path

import hook_io

WANT_RE = re.compile(
    r'LEARNING-WANT\s+topic="(?P<topic>[^"]*)"(?:\s+note="(?P<note>[^"]*)")?'
)


def iter_want_markers(text: str):
    """Yield (topic, note) for markers with a non-empty topic."""
    for match in WANT_RE.finditer(text):
        topic = (match.group("topic") or "").strip()
        note = (match.group("note") or "").strip()
        if not topic:
            hook_io.log_diag("skip LEARNING-WANT: empty topic")
            continue
        yield topic, note


def main() -> None:
    here = Path(__file__).resolve().parent
    raw = hook_io.read_stdin_raw()
    data = hook_io.parse_stdin_json(raw)
    text = hook_io.extract_response_text(data, raw)

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

    for topic, note in iter_want_markers(text):
        try:
            lib.add_want(topic, note)
        except Exception as exc:  # noqa: BLE001
            hook_io.log_diag(f"add_want failed for {topic!r}: {exc}")

    hook_io.emit_fail_open()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        hook_io.log_diag(f"afterAgentResponse fail-open: {exc}")
        hook_io.emit_fail_open()
