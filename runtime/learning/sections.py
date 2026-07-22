"""Markdown section read/replace helpers for profile and project sheets."""

from __future__ import annotations

import re

# Canonical English section titles, with legacy Portuguese aliases for migration.
SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "Meta": ("Meta",),
    "Study queue": ("Study queue", "Fila de estudo"),
    "Covered": ("Covered", "Coberto"),
    "Stack": ("Stack",),
    "Study candidates": ("Study candidates", "Candidatos de estudo"),
    "Last probe": ("Last probe", "Última sondagem"),
}


def section(text: str, title: str) -> str:
    for alias in SECTION_ALIASES.get(title, (title,)):
        pattern = rf"## {re.escape(alias)}\n(.*?)(?=\n## |\Z)"
        match = re.search(pattern, text, flags=re.S)
        if match:
            return match.group(1)
    return ""


def replace_section(text: str, title: str, body: str) -> str:
    body = body.rstrip() + "\n\n"
    for alias in SECTION_ALIASES.get(title, (title,)):
        pattern = rf"(## {re.escape(alias)}\n)(.*?)(?=\n## |\Z)"
        if re.search(pattern, text, flags=re.S):
            # Normalize heading to the canonical English title on write.
            return re.sub(
                pattern,
                rf"## {title}\n{body}",
                text,
                count=1,
                flags=re.S,
            )
    return text.rstrip() + f"\n\n## {title}\n{body}"
