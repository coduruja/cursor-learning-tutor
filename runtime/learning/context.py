"""Bounded context rendering for sessionStart injection."""

from __future__ import annotations


def truncate_for_inject(content: str, max_chars: int = 6000) -> str:
    if len(content) <= max_chars:
        return content
    return content[:800] + "\n...\n" + content[-(max_chars - 800) :]
