"""Stable CLI deployment into ~/.cursor/learning/."""

from __future__ import annotations

import shutil
from pathlib import Path

from learning import paths


def install_cli(source_dir: Path | None = None) -> None:
    """Copy CLI + lib package to a stable path so the agent can always call them."""
    paths.ensure_dir()
    here = Path(source_dir) if source_dir else Path(__file__).resolve().parents[1]

    cli_src = here / "learning_cli.py"
    if cli_src.exists():
        shutil.copy2(cli_src, paths.CLI_PATH)

    shim_src = here / "lib_profile.py"
    if shim_src.exists():
        shutil.copy2(shim_src, paths.LIB_PATH)

    package_src = here / "learning"
    if package_src.is_dir():
        dest = paths.LEARNING_DIR / "learning"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(package_src, dest)
