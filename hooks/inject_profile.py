#!/usr/bin/env python3
"""
sessionStart: injeta o perfil e instala a CLI em caminho estável.

Copia learning_cli.py + lib_profile.py para ~/.cursor/learning/ para o agente
poder gravar com:
  python3 ~/.cursor/learning/cli.py ...
mesmo sem saber o path do plugin.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_lib():
    here = Path(__file__).resolve().parent
    path = here / "lib_profile.py"
    spec = importlib.util.spec_from_file_location("lib_profile", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    try:
        sys.stdin.buffer.read()
    except Exception:
        pass

    lib = _load_lib()
    lib.install_cli(Path(__file__).resolve().parent)

    if not lib.PROFILE_PATH.exists():
        context = (
            "LEARNING-PROFILE: perfil ainda vazio. "
            "No primeiro momento útil, faça onboarding curto (nível geral + foco) "
            "com `python3 ~/.cursor/learning/cli.py init --level ... --focus ...` "
            "ou peça ao usuário para rodar `/study-plan` / `/study-log`."
        )
        print(json.dumps({"continue": True, "additional_context": context}))
        return

    content = lib.truncate_for_inject(lib.read_profile())
    empty_hint = ""
    if lib.profile_is_empty():
        empty_hint = (
            "\n\n(Perfil quase vazio: ofereça onboarding curto ou `/study-plan` "
            "em vez de inventar histórico.)"
        )
    context = (
        "LEARNING-PROFILE (perfil de aprendizado do usuário entre projetos; "
        "use para calibrar a profundidade das explicações; "
        "para gravar use `python3 ~/.cursor/learning/cli.py`):\n\n"
        + content
        + empty_hint
    )
    print(json.dumps({"continue": True, "additional_context": context}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"continue": True}))
