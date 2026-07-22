#!/usr/bin/env python3
"""
afterAgentResponse adapter: capture LEARNING-WANT markers (want-only fallback).

Marker parsing and profile writes live in runtime. Covered knowledge is never
written from markers — only from one-topic probe evidence via the CLI.
"""

from __future__ import annotations

from pathlib import Path

import hook_io


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

    for topic, note in lib.iter_want_markers(text):
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
