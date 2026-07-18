#!/usr/bin/env python3
"""
afterAgentResponse: captura marcadores LEARNING-LOG / LEARNING-WANT.

Lê o JSON do hook via stdin, procura os marcadores que a rule instrui o agente
a emitir, e atualiza ~/.cursor/learning/profile.md.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

LOG_RE = re.compile(
    r'LEARNING-LOG\s+topic="(?P<topic>[^"]*)"\s+level="(?P<level>[^"]*)"'
    r'(?:\s+note="(?P<note>[^"]*)")?'
)
WANT_RE = re.compile(
    r'LEARNING-WANT\s+topic="(?P<topic>[^"]*)"(?:\s+note="(?P<note>[^"]*)")?'
)


def _load_lib():
    here = Path(__file__).resolve().parent
    path = here / "lib_profile.py"
    spec = importlib.util.spec_from_file_location("lib_profile", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def read_stdin_text() -> str:
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    try:
        data = json.loads(raw)
    except Exception:
        return raw
    if isinstance(data, dict):
        chunks = []
        for key in ("text", "response", "content", "message", "output"):
            val = data.get(key)
            if isinstance(val, str):
                chunks.append(val)
        if chunks:
            return "\n".join(chunks)
    return raw


def main() -> None:
    lib = _load_lib()
    lib.install_cli(Path(__file__).resolve().parent)
    text = read_stdin_text()
    for m in LOG_RE.finditer(text):
        lib.add_covered(
            m.group("topic").strip(),
            m.group("level").strip(),
            (m.group("note") or "").strip(),
        )
    for m in WANT_RE.finditer(text):
        lib.add_want(m.group("topic").strip(), (m.group("note") or "").strip())
    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"continue": True}))
