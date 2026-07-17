#!/usr/bin/env python3
"""
Cursor global hook (afterAgentResponse): captura entradas de aprendizado.

Lê o JSON do hook via stdin, procura o marcador <!-- LEARNING-LOG ... --> que a
User Rule instrui o agente a emitir, e adiciona uma entrada ao perfil global.
Roda como script na sua máquina (fora do sandbox do agente), então escreve num
arquivo do seu home, valendo para todos os projetos.
"""

import sys
import os
import re
import json
from datetime import date

PROFILE = os.path.expanduser("~/.cursor/learning/profile.md")

MARKER_RE = re.compile(
    r'LEARNING-LOG\s+topic="(?P<topic>[^"]*)"\s+level="(?P<level>[^"]*)"'
    r'(?:\s+note="(?P<note>[^"]*)")?'
)


def read_stdin_text() -> str:
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    try:
        data = json.loads(raw)
    except Exception:
        return raw
    if isinstance(data, dict):
        for key in ("text", "response", "content", "message", "output"):
            val = data.get(key)
            if isinstance(val, str) and "LEARNING-LOG" in val:
                return val
    return raw


def append_entry(topic: str, level: str, note: str) -> None:
    os.makedirs(os.path.dirname(PROFILE), exist_ok=True)
    header_needed = not os.path.exists(PROFILE)
    with open(PROFILE, "a", encoding="utf-8") as f:
        if header_needed:
            f.write(
                "# Perfil de Aprendizado (global)\n\n"
                "> Mantido automaticamente pelo hook capture_learning.py.\n\n"
                "## Log de Aprendizado\n\n"
            )
        line = f"### {date.today().isoformat()} — {topic}\n"
        line += f"- Nível: {level}\n"
        if note:
            line += f"- Contexto: {note}\n"
        line += "\n"
        f.write(line)


def main() -> None:
    text = read_stdin_text()
    m = MARKER_RE.search(text)
    if m:
        append_entry(
            m.group("topic").strip(),
            m.group("level").strip(),
            (m.group("note") or "").strip(),
        )
    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Um hook nunca deve travar o agente.
        print(json.dumps({"continue": True}))
