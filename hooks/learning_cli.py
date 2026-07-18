#!/usr/bin/env python3
"""CLI estável do Learning Tutor.

Uso típico (caminho estável após o primeiro sessionStart):
  python3 ~/.cursor/learning/cli.py covered --topic "Closures" --level intermediário --note "..."
  python3 ~/.cursor/learning/cli.py want --topic "Docker" --note "pro deploy"
  python3 ~/.cursor/learning/cli.py done --topic "Docker"
  python3 ~/.cursor/learning/cli.py init --level intermediário --focus "backend"
  python3 ~/.cursor/learning/cli.py show
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def _load_lib():
    here = Path(__file__).resolve().parent
    candidates = [
        here / "lib_profile.py",
        Path.home() / ".cursor" / "learning" / "lib_profile.py",
    ]
    for path in candidates:
        if path.exists():
            spec = importlib.util.spec_from_file_location("lib_profile", path)
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            return mod
    raise SystemExit("lib_profile.py não encontrado. Reinstale o plugin Learning Tutor.")


def main() -> None:
    lib = _load_lib()
    parser = argparse.ArgumentParser(prog="learning-cli", description="Learning Tutor profile CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Cria/atualiza meta do perfil")
    p_init.add_argument("--level", default="intermediário")
    p_init.add_argument("--focus", default="não definido")

    p_cov = sub.add_parser("covered", help="Registra tópico coberto/aprendido")
    p_cov.add_argument("--topic", required=True)
    p_cov.add_argument("--level", default="intermediário")
    p_cov.add_argument("--note", default="")

    p_want = sub.add_parser("want", help="Adiciona tópico à fila de estudo")
    p_want.add_argument("--topic", required=True)
    p_want.add_argument("--note", default="")

    p_done = sub.add_parser("done", help="Marca item da fila como feito")
    p_done.add_argument("--topic", required=True)

    sub.add_parser("show", help="Mostra o perfil")

    args = parser.parse_args()
    if args.cmd == "init":
        print(lib.init_profile(args.level, args.focus))
    elif args.cmd == "covered":
        print(lib.add_covered(args.topic, args.level, args.note))
    elif args.cmd == "want":
        print(lib.add_want(args.topic, args.note))
    elif args.cmd == "done":
        print(lib.mark_done(args.topic))
    elif args.cmd == "show":
        lib.ensure_profile()
        print(lib.read_profile())


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 — CLI must never crash the agent awkwardly
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)
