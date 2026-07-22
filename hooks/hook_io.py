#!/usr/bin/env python3
"""Shared Hook adapter helpers (JSON I/O, diagnostics, lib loading).

Used by inject_profile.py and capture_learning.py. Not installed to
~/.cursor/learning — those entry points load this module from the plugin tree.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def log_diag(message: str) -> None:
    """Best-effort diagnostic for maintainers; never written to Agent context."""
    print(f"learning-tutor: {message}", file=sys.stderr)


def load_lib_profile(source_dir: Path | None = None):
    here = Path(source_dir) if source_dir else Path(__file__).resolve().parent
    path = here / "lib_profile.py"
    spec = importlib.util.spec_from_file_location("lib_profile", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_stdin_raw() -> bytes:
    try:
        return sys.stdin.buffer.read()
    except Exception as exc:  # noqa: BLE001
        log_diag(f"stdin read failed: {exc}")
        return b""


def parse_stdin_json(raw: bytes) -> dict[str, Any] | None:
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception as exc:  # noqa: BLE001
        log_diag(f"stdin JSON parse failed: {exc}")
        return None
    return data if isinstance(data, dict) else None


def extract_response_text(data: dict[str, Any] | None, raw: bytes) -> str:
    """Prefer official afterAgentResponse `text`; keep temporary compat keys."""
    if data is None:
        return raw.decode("utf-8", errors="replace")
    chunks: list[str] = []
    for key in ("text", "response", "content", "message", "output"):
        val = data.get(key)
        if isinstance(val, str):
            chunks.append(val)
    if chunks:
        return "\n".join(chunks)
    return raw.decode("utf-8", errors="replace")


def workspace_roots_from_payload(data: dict[str, Any] | None) -> list[str]:
    if not data:
        return []
    roots = data.get("workspace_roots")
    if not isinstance(roots, list):
        return []
    return [r for r in roots if isinstance(r, str) and r.strip()]


def emit_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload))


def emit_fail_open(extra: dict[str, Any] | None = None) -> None:
    payload: dict[str, Any] = {"continue": True}
    if extra:
        payload.update(extra)
    emit_json(payload)
