#!/usr/bin/env python3
"""
sessionStart adapter: install CLI + inject session context.

Domain rendering lives in runtime (`render_session_context`). This script only
bridges Cursor JSON ↔ runtime and always fails open.
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

    try:
        context = lib.render_session_context(workspace_roots=roots or None)
    except Exception as exc:  # noqa: BLE001
        hook_io.log_diag(f"render_session_context failed: {exc}")
        hook_io.emit_fail_open()
        return

    hook_io.emit_json({"continue": True, "additional_context": context})


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        hook_io.log_diag(f"sessionStart fail-open: {exc}")
        hook_io.emit_fail_open()
