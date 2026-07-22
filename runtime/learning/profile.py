"""Global learning profile persistence (queue, covered, meta)."""

from __future__ import annotations

import re
from datetime import date

from learning import paths
from learning.sections import replace_section, section
from learning.topics import (
    is_noisy_topic,
    normalize_level,
    normalize_topic_display,
    queue_item_name,
    topic_key,
)

HEADER = """# Learning profile (global)

> Maintained by Learning Tutor. Edit by hand if you want; `/study-log` and hooks update this file.

## Meta
- Overall level: {level}
- Current focus: {focus}

## Study queue

_Empty._

## Covered

"""

EMPTY_COVERED = ("", "_None yet._", "_Nenhuma entrada ainda._")


def ensure_profile(level: str = "undefined", focus: str = "undefined") -> None:
    paths.ensure_dir()
    if paths.PROFILE_PATH.exists():
        return
    paths.PROFILE_PATH.write_text(
        HEADER.format(level=level, focus=focus) + "_None yet._\n",
        encoding="utf-8",
    )


def read_profile() -> str:
    if not paths.PROFILE_PATH.exists():
        return ""
    return paths.PROFILE_PATH.read_text(encoding="utf-8")


def profile_is_empty() -> bool:
    text = read_profile()
    if not text.strip():
        return True
    has_queue_item = bool(re.search(r"- \[[ x]\]", text))
    covered = section(text, "Covered")
    has_covered = bool(covered.strip()) and "### " in covered
    return not has_queue_item and not has_covered


def _topic_in_queue(queue: str, topic: str) -> bool:
    key = topic_key(topic)
    for item in re.findall(r"- \[[ x]\]\s+(.+)", queue):
        if topic_key(queue_item_name(item)) == key:
            return True
    return False


def _topic_in_covered(covered: str, topic: str, recent_n: int = 20) -> bool:
    key = topic_key(topic)
    headings = re.findall(r"###\s+[^\n—]+—\s*(.+)", covered)
    for heading in headings[:recent_n]:
        if topic_key(heading.strip()) == key:
            return True
    return False


def init_profile(level: str, focus: str) -> str:
    paths.ensure_dir()
    level = normalize_level(level)
    focus = (focus or "undefined").strip() or "undefined"
    if paths.PROFILE_PATH.exists() and not profile_is_empty():
        text = read_profile()
        text = re.sub(
            r"(- (?:Overall level|Nível geral):\s*).*",
            rf"- Overall level: {level}",
            text,
            count=1,
        )
        text = re.sub(
            r"(- (?:Current focus|Foco atual):\s*).*",
            rf"- Current focus: {focus}",
            text,
            count=1,
        )
        paths.PROFILE_PATH.write_text(text, encoding="utf-8")
        return f"Updated meta: level={level}, focus={focus}"
    paths.PROFILE_PATH.write_text(
        HEADER.format(level=level, focus=focus) + "_None yet._\n",
        encoding="utf-8",
    )
    return f"Created profile: level={level}, focus={focus}"


def add_covered(topic: str, level: str, note: str = "") -> str:
    topic = normalize_topic_display(topic)
    if not topic:
        raise ValueError("empty topic")
    if is_noisy_topic(topic):
        return f"Ignored (generic topic / base language): {topic}"
    level = normalize_level(level)
    note = (note or "").strip()
    ensure_profile()
    text = read_profile()
    entry = f"### {date.today().isoformat()} — {topic}\n- Level: {level}\n"
    if note:
        entry += f"- Context: {note}\n"
    entry += "\n"

    covered = section(text, "Covered")
    if covered.strip() in EMPTY_COVERED:
        new_covered = entry
    else:
        new_covered = covered.lstrip("\n")
        if not new_covered.endswith("\n"):
            new_covered += "\n"
        new_covered = entry + new_covered
    text = replace_section(text, "Covered", new_covered)
    paths.PROFILE_PATH.write_text(text, encoding="utf-8")
    return f"Saved to profile (covered): {topic} [{level}]"


def add_want(topic: str, note: str = "") -> str:
    topic = normalize_topic_display(topic)
    if not topic:
        raise ValueError("empty topic")
    if is_noisy_topic(topic):
        return f"Ignored (generic topic / base language): {topic}"
    note = (note or "").strip()
    ensure_profile()
    text = read_profile()
    queue = section(text, "Study queue")
    if _topic_in_queue(queue, topic):
        return f"Already in queue: {topic}"
    covered = section(text, "Covered")
    if _topic_in_covered(covered, topic):
        return f"Already covered recently: {topic}"

    line = f"- [ ] {topic}"
    if note:
        line += f" — {note}"
    lines = [
        ln
        for ln in queue.splitlines()
        if ln.strip() and ln.strip() not in ("_Empty._", "_Vazia._")
    ]
    lines.append(line)
    body = "\n".join(lines) + "\n"
    text = replace_section(text, "Study queue", body)
    paths.PROFILE_PATH.write_text(text, encoding="utf-8")
    return f"Saved to profile (queue): {topic}"


def mark_done(topic: str) -> str:
    topic = normalize_topic_display(topic) or topic.strip()
    ensure_profile()
    text = read_profile()
    queue = section(text, "Study queue")
    key = topic_key(topic)

    def repl(match: re.Match[str]) -> str:
        name = queue_item_name(match.group(2))
        if topic_key(name) == key:
            return f"- [x] {match.group(2)}"
        return match.group(0)

    new_queue, _n = re.subn(
        r"- \[([ x])\]\s+(.+)",
        repl,
        queue,
    )
    if new_queue == queue:
        changed = False
        lines = []
        for ln in queue.splitlines():
            match = re.match(r"- \[([ x])\]\s+(.+)", ln)
            if match and (
                topic_key(queue_item_name(match.group(2))) == key
                or topic.lower() in match.group(2).lower()
            ):
                lines.append(f"- [x] {match.group(2)}")
                changed = True
            else:
                lines.append(ln)
        if not changed:
            return f"Not found in queue: {topic}"
        new_queue = "\n".join(lines) + ("\n" if lines else "")
    text = replace_section(text, "Study queue", new_queue)
    paths.PROFILE_PATH.write_text(text, encoding="utf-8")
    return f"Marked done in queue: {topic}"


def first_open_queue_topic() -> str:
    """Return the first unchecked queue item topic, or empty string."""
    ensure_profile()
    queue = section(read_profile(), "Study queue")
    for item in re.findall(r"- \[ \]\s+(.+)", queue):
        return queue_item_name(item)
    return ""
