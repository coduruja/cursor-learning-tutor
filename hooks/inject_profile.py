#!/usr/bin/env python3
"""
sessionStart: injeta o perfil e instala a CLI em caminho estável.

Copia learning_cli.py + lib_profile.py para ~/.cursor/learning/ para o agente
poder gravar com:
  python3 ~/.cursor/learning/cli.py ...
mesmo sem saber o path do plugin.

Se existir .cursor/learning-project.md no cwd (ou ancestors), injeta também
como LEARNING-PROJECT.
"""

from __future__ import annotations

import importlib.util
import json
import os
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


def _find_project_file(start: Path) -> Path | None:
    """Walk up from start looking for .cursor/learning-project.md."""
    cur = start.resolve()
    for _ in range(8):
        candidate = cur / ".cursor" / "learning-project.md"
        if candidate.is_file():
            return candidate
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def main() -> None:
    try:
        sys.stdin.buffer.read()
    except Exception:
        pass

    lib = _load_lib()
    lib.install_cli(Path(__file__).resolve().parent)

    parts: list[str] = []

    if not lib.PROFILE_PATH.exists():
        parts.append(
            "LEARNING-PROFILE: perfil ainda vazio. "
            "No primeiro momento útil, faça onboarding curto (nível geral + foco) "
            "com `python3 ~/.cursor/learning/cli.py init --level ... --focus ...` "
            "ou peça ao usuário para rodar `/study-plan` / `/study-log`."
        )
    else:
        content = lib.truncate_for_inject(lib.read_profile())
        empty_hint = ""
        if lib.profile_is_empty():
            empty_hint = (
                "\n\n(Perfil quase vazio: ofereça onboarding curto ou `/study-plan` "
                "em vez de inventar histórico.)"
            )
        parts.append(
            "LEARNING-PROFILE (perfil de aprendizado do usuário entre projetos; "
            "use para calibrar a profundidade das explicações; "
            "para gravar use `python3 ~/.cursor/learning/cli.py`):\n\n"
            + content
            + empty_hint
        )

    cwd = Path(os.getcwd())
    project_file = _find_project_file(cwd)
    if project_file is not None:
        project_text = lib.truncate_for_inject(
            project_file.read_text(encoding="utf-8"),
            max_chars=3000,
        )
        parts.append(
            "LEARNING-PROJECT (stack/candidatos deste repositório; "
            "não é a fila global — promova com want/probe quando houver lacuna):\n\n"
            + project_text
        )
    else:
        parts.append(
            "LEARNING-PROJECT: nenhum `.cursor/learning-project.md` neste workspace. "
            "Em repos com stack clara, o agente pode criar via "
            "`python3 ~/.cursor/learning/cli.py project-sync --stack \"...\" --candidates \"a;b;c\"`."
        )

    print(json.dumps({"continue": True, "additional_context": "\n\n".join(parts)}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"continue": True}))
