"""Stable CLI deployment into ~/.cursor/learning/."""

from __future__ import annotations

import shutil
from pathlib import Path

from learning import paths


def resolve_runtime_root(source_dir: Path | None = None) -> Path:
    """Locate the runtime tree (cli.py + learning/).

    Accepts:
    - runtime/ itself
    - hooks/ (legacy call site; resolves sibling runtime/)
    - None → directory containing this package (runtime/)
    """
    if source_dir is None:
        return Path(__file__).resolve().parents[1]
    src = Path(source_dir).resolve()
    if (src / "learning").is_dir() and (
        (src / "cli.py").is_file() or (src / "learning_cli.py").is_file()
    ):
        return src
    sibling = src.parent / "runtime"
    if (sibling / "learning").is_dir():
        return sibling
    return src


def install_cli(source_dir: Path | None = None) -> None:
    """Copy CLI + lib package to a stable path so the agent can always call them."""
    paths.ensure_dir()
    root = resolve_runtime_root(source_dir)

    cli_src = root / "cli.py"
    if not cli_src.is_file():
        cli_src = root / "learning_cli.py"
    if cli_src.is_file():
        shutil.copy2(cli_src, paths.CLI_PATH)

    # Prefer runtime-local shim if present; else hooks/lib_profile.py next to caller.
    shim_src = root / "lib_profile.py"
    if not shim_src.is_file():
        hooks_shim = root.parent / "hooks" / "lib_profile.py"
        if hooks_shim.is_file():
            shim_src = hooks_shim
    if shim_src.is_file():
        shutil.copy2(shim_src, paths.LIB_PATH)

    package_src = root / "learning"
    if package_src.is_dir():
        dest = paths.LEARNING_DIR / "learning"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(package_src, dest)
