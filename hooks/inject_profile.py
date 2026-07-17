#!/usr/bin/env python3
"""
Cursor global hook (sessionStart): injeta o perfil de aprendizado.

Lê ~/.cursor/learning/profile.md e devolve como additional_context, para o
agente calibrar em qualquer projeto.

Nota: o hook sessionStart teve bug reportado no começo de 2026. Se não estiver
injetando na sua versão, veja o README (a captura continua funcionando e você
pode rodar /study-plan ou colar o topo do profile.md quando começar algo novo).
"""

import sys
import os
import json

PROFILE = os.path.expanduser("~/.cursor/learning/profile.md")
MAX_CHARS = 6000  # não estourar contexto; mantém as entradas mais recentes


def main() -> None:
    try:
        sys.stdin.buffer.read()  # drena o stdin
    except Exception:
        pass

    if not os.path.exists(PROFILE):
        print(json.dumps({"continue": True}))
        return

    with open(PROFILE, "r", encoding="utf-8") as f:
        content = f.read()

    if len(content) > MAX_CHARS:
        content = content[:800] + "\n...\n" + content[-(MAX_CHARS - 800):]

    context = (
        "LEARNING-PROFILE (perfil de aprendizado do usuário entre projetos; "
        "use para calibrar a profundidade das explicações e evitar repetir "
        "fundamentos já dominados):\n\n" + content
    )
    print(json.dumps({"continue": True, "additional_context": context}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"continue": True}))
