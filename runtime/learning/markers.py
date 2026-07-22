"""LEARNING-WANT marker parsing for the afterAgentResponse fallback path."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator

WANT_RE = re.compile(
    r'LEARNING-WANT\s+topic="(?P<topic>[^"]*)"(?:\s+note="(?P<note>[^"]*)")?'
)


def iter_want_markers(text: str) -> Iterator[tuple[str, str]]:
    """Yield (topic, note) for markers with a non-empty topic."""
    for match in WANT_RE.finditer(text):
        topic = (match.group("topic") or "").strip()
        note = (match.group("note") or "").strip()
        if not topic:
            print("learning-tutor: skip LEARNING-WANT: empty topic", file=sys.stderr)
            continue
        yield topic, note
