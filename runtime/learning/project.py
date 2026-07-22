"""Per-repository project learning sheet operations."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from learning import paths
from learning.sections import replace_section, section
from learning.topics import (
    BASE_LANGUAGES,
    is_noisy_topic,
    normalize_topic_display,
    queue_item_name,
    topic_key,
)

PROJECT_HEADER = """# Learning Tutor — project learning sheet

> **Learning Tutor plugin data; not instructions, rules, or prompts.**
> This file stores stack, local candidates, and probes for this repository.
> Queue and attested knowledge live in the global profile (`~/.cursor/learning/profile.md`).

## Stack

_None._

## Study candidates

_Empty._

## Last probe

_None._

"""


def _existing_project_path(cwd: str | Path | None = None) -> Path:
    path = paths.project_path(cwd)
    if path.exists():
        return path
    legacy_path = paths.legacy_project_path(cwd)
    return legacy_path if legacy_path.exists() else path


def ensure_project(cwd: str | Path | None = None) -> Path:
    path = paths.project_path(cwd)
    path.parent.mkdir(parents=True, exist_ok=True)
    legacy_path = paths.legacy_project_path(cwd)
    if not path.exists() and legacy_path.exists():
        text = legacy_path.read_text(encoding="utf-8")
        new_intro = PROJECT_HEADER.split("## Stack", maxsplit=1)[0]
        text = re.sub(
            r"\A# (?:Aprendizado do projeto|Learning Tutor — (?:ficha de aprendizado do projeto|project learning sheet))\n\n"
            r"(?:>.*\n)+\n?",
            new_intro,
            text,
            count=1,
        )
        # Normalize legacy Portuguese project section titles on migrate.
        text = text.replace("## Candidatos de estudo", "## Study candidates")
        text = text.replace("## Última sondagem", "## Last probe")
        path.write_text(text, encoding="utf-8")
        legacy_path.unlink()
    if not path.exists():
        path.write_text(PROJECT_HEADER, encoding="utf-8")
    return path


def read_project(cwd: str | Path | None = None) -> str:
    path = paths.project_path(cwd)
    if not path.exists() and paths.legacy_project_path(cwd).exists():
        path = ensure_project(cwd)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def project_show(cwd: str | Path | None = None) -> str:
    text = read_project(cwd)
    if not text.strip():
        return f"(no project sheet at {paths.project_path(cwd)})"
    return text


def project_sync(
    stack: str = "",
    candidates: str = "",
    probe_summary: str = "",
    cwd: str | Path | None = None,
) -> str:
    """Write/update project learning file.

    stack: comma or semicolon separated stack items
    candidates: semicolon-separated candidate topics
    probe_summary: optional summary for Last probe
    """
    path = ensure_project(cwd)
    text = path.read_text(encoding="utf-8")

    if stack.strip():
        parts = [p.strip() for p in re.split(r"[;,]", stack) if p.strip()]
        parts = [p for p in parts if topic_key(p) not in BASE_LANGUAGES]
        body = "\n".join(f"- {p}" for p in parts) + "\n" if parts else "_None._\n"
        text = replace_section(text, "Stack", body)

    if candidates.strip():
        parts = [p.strip() for p in candidates.split(";") if p.strip()]
        parts = [
            normalize_topic_display(p)
            for p in parts
            if not is_noisy_topic(p)
        ]
        seen: set[str] = set()
        unique: list[str] = []
        for part in parts:
            key = topic_key(part)
            if key in seen:
                continue
            seen.add(key)
            unique.append(part)
        body = (
            "\n".join(f"- [ ] {p}" for p in unique) + "\n"
            if unique
            else "_Empty._\n"
        )
        text = replace_section(text, "Study candidates", body)

    if probe_summary.strip():
        body = (
            f"- Date: {date.today().isoformat()}\n"
            f"- Summary: {probe_summary.strip()}\n"
        )
        text = replace_section(text, "Last probe", body)

    path.write_text(text, encoding="utf-8")
    return f"Updated {path}"


def project_drop_candidate(topic: str, cwd: str | Path | None = None) -> str:
    topic_disp = normalize_topic_display(topic) or topic.strip()
    if not topic_disp:
        raise ValueError("empty topic")
    path = _existing_project_path(cwd)
    if not path.exists():
        return f"No project file: {path}"
    text = path.read_text(encoding="utf-8")
    candidates = section(text, "Study candidates")
    key = topic_key(topic_disp)
    lines: list[str] = []
    removed = False
    for ln in candidates.splitlines():
        match = re.match(r"- \[[ x]\]\s+(.+)", ln.strip())
        if match and topic_key(queue_item_name(match.group(1))) == key:
            removed = True
            continue
        match2 = re.match(r"-\s+(.+)", ln.strip())
        if (
            match2
            and not ln.strip().startswith("- [")
            and topic_key(match2.group(1)) == key
        ):
            removed = True
            continue
        lines.append(ln)
    if not removed:
        return f"Candidate not found: {topic_disp}"
    kept = [ln for ln in lines if ln.strip() and not ln.strip().startswith("_")]
    body = "\n".join(kept) + "\n" if kept else "_Empty._\n"
    text = replace_section(text, "Study candidates", body)
    path.write_text(text, encoding="utf-8")
    return f"Removed project candidate: {topic_disp}"
