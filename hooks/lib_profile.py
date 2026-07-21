"""Shared helpers for the Learning Tutor profile (~/.cursor/learning/)."""

from __future__ import annotations

import os
import re
import shutil
import unicodedata
from datetime import date
from pathlib import Path

LEARNING_DIR = Path(os.path.expanduser("~/.cursor/learning"))
PROFILE_PATH = LEARNING_DIR / "profile.md"
CLI_PATH = LEARNING_DIR / "cli.py"
LIB_PATH = LEARNING_DIR / "lib_profile.py"
PROJECT_RELATIVE_PATH = Path(".cursor") / "learning" / "project.md"
LEGACY_PROJECT_RELATIVE_PATH = Path(".cursor") / "learning-project.md"

LEVELS = ("beginner", "intermediate", "advanced")

# Canonical English section titles, with legacy Portuguese aliases for migration.
SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "Meta": ("Meta",),
    "Study queue": ("Study queue", "Fila de estudo"),
    "Covered": ("Covered", "Coberto"),
    "Stack": ("Stack",),
    "Study candidates": ("Study candidates", "Candidatos de estudo"),
    "Last probe": ("Last probe", "Última sondagem"),
}

# Canonical topic aliases (key -> display name). Comparison uses topic_key().
TOPIC_ALIASES: dict[str, str] = {
    "pr": "PR",
    "pull request": "PR",
    "pull requests": "PR",
    "mrs": "MR",
    "merge request": "MR",
    "merge requests": "MR",
    "http": "HTTP",
    "https": "HTTPS",
    "api": "API",
    "apis": "API",
    "ci": "CI",
    "cd": "CD",
    "ci/cd": "CI/CD",
    "docker compose": "Docker Compose",
    "docker-compose": "Docker Compose",
}

GENERIC_TOPICS = frozenset(
    {
        "codigo",
        "código",
        "code",
        "arquivo",
        "file",
        "erro",
        "error",
        "funcao",
        "função",
        "function",
        "bug",
        "coisa",
        "thing",
        "isso",
        "aquilo",
        "modulo",
        "módulo",
        "module",
        "projeto",
        "project",
        "repo",
        "repositorio",
        "repositório",
        "repository",
    }
)

BASE_LANGUAGES = frozenset(
    {
        "python",
        "javascript",
        "js",
        "typescript",
        "ts",
        "java",
        "go",
        "golang",
        "rust",
        "ruby",
        "php",
        "c",
        "c++",
        "csharp",
        "c#",
        "swift",
        "kotlin",
        "html",
        "css",
        "sql",
        "bash",
        "shell",
    }
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

EMPTY_COVERED = ("", "_None yet._", "_Nenhuma entrada ainda._")
EMPTY_QUEUE = ("", "_Empty._", "_Vazia._")
EMPTY_LIST = ("", "_None._", "_Empty._", "_Nenhuma._", "_Vazio._")


def ensure_dir() -> None:
    LEARNING_DIR.mkdir(parents=True, exist_ok=True)


def ensure_profile(level: str = "undefined", focus: str = "undefined") -> None:
    ensure_dir()
    if PROFILE_PATH.exists():
        return
    PROFILE_PATH.write_text(
        HEADER.format(level=level, focus=focus) + "_None yet._\n",
        encoding="utf-8",
    )


def install_cli(source_dir: Path | None = None) -> None:
    """Copy CLI + lib to a stable path so the agent can always call them."""
    ensure_dir()
    here = Path(source_dir) if source_dir else Path(__file__).resolve().parent
    for name, dest in (("lib_profile.py", LIB_PATH), ("learning_cli.py", CLI_PATH)):
        src = here / name
        if src.exists():
            shutil.copy2(src, dest)


def read_profile() -> str:
    if not PROFILE_PATH.exists():
        return ""
    return PROFILE_PATH.read_text(encoding="utf-8")


def profile_is_empty() -> bool:
    text = read_profile()
    if not text.strip():
        return True
    has_queue_item = bool(re.search(r"- \[[ x]\]", text))
    covered = _section(text, "Covered")
    has_covered = bool(covered.strip()) and "### " in covered
    return not has_queue_item and not has_covered


def _section(text: str, title: str) -> str:
    for alias in SECTION_ALIASES.get(title, (title,)):
        pattern = rf"## {re.escape(alias)}\n(.*?)(?=\n## |\Z)"
        m = re.search(pattern, text, flags=re.S)
        if m:
            return m.group(1)
    return ""


def _replace_section(text: str, title: str, body: str) -> str:
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


def _normalize_level(level: str) -> str:
    raw = (level or "").strip().lower()
    aliases = {
        "beginner": "beginner",
        "iniciante": "beginner",
        "intermediate": "intermediate",
        "intermediario": "intermediate",
        "intermediário": "intermediate",
        "advanced": "advanced",
        "avancado": "advanced",
        "avançado": "advanced",
    }
    return aliases.get(raw, raw or "intermediate")


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def topic_key(topic: str) -> str:
    """Normalized key for dedupe (aliases collapse to one canonical key)."""
    raw = _strip_accents((topic or "").strip().lower())
    raw = re.sub(r"\s+", " ", raw)
    if raw in TOPIC_ALIASES:
        return _strip_accents(TOPIC_ALIASES[raw].lower())
    return raw


def normalize_topic_display(topic: str) -> str:
    """Canonical display name when an alias exists; otherwise trimmed original."""
    stripped = (topic or "").strip()
    if not stripped:
        return ""
    key = _strip_accents(stripped.lower())
    key = re.sub(r"\s+", " ", key)
    if key in TOPIC_ALIASES:
        return TOPIC_ALIASES[key]
    return stripped


def is_noisy_topic(topic: str) -> bool:
    key = topic_key(topic)
    return key in GENERIC_TOPICS or key in BASE_LANGUAGES


def _queue_item_name(item: str) -> str:
    return item.split("—")[0].strip()


def _topic_in_queue(queue: str, topic: str) -> bool:
    key = topic_key(topic)
    for item in re.findall(r"- \[[ x]\]\s+(.+)", queue):
        if topic_key(_queue_item_name(item)) == key:
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
    ensure_dir()
    level = _normalize_level(level)
    focus = (focus or "undefined").strip() or "undefined"
    if PROFILE_PATH.exists() and not profile_is_empty():
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
        PROFILE_PATH.write_text(text, encoding="utf-8")
        return f"Updated meta: level={level}, focus={focus}"
    PROFILE_PATH.write_text(
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
    level = _normalize_level(level)
    note = (note or "").strip()
    ensure_profile()
    text = read_profile()
    entry = f"### {date.today().isoformat()} — {topic}\n- Level: {level}\n"
    if note:
        entry += f"- Context: {note}\n"
    entry += "\n"

    covered = _section(text, "Covered")
    if covered.strip() in EMPTY_COVERED:
        new_covered = entry
    else:
        new_covered = covered.lstrip("\n")
        if not new_covered.endswith("\n"):
            new_covered += "\n"
        new_covered = entry + new_covered
    text = _replace_section(text, "Covered", new_covered)
    PROFILE_PATH.write_text(text, encoding="utf-8")
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
    queue = _section(text, "Study queue")
    if _topic_in_queue(queue, topic):
        return f"Already in queue: {topic}"
    covered = _section(text, "Covered")
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
    text = _replace_section(text, "Study queue", body)
    PROFILE_PATH.write_text(text, encoding="utf-8")
    return f"Saved to profile (queue): {topic}"


def mark_done(topic: str) -> str:
    topic = normalize_topic_display(topic) or topic.strip()
    ensure_profile()
    text = read_profile()
    queue = _section(text, "Study queue")
    key = topic_key(topic)

    def repl(match: re.Match[str]) -> str:
        name = _queue_item_name(match.group(2))
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
            m = re.match(r"- \[([ x])\]\s+(.+)", ln)
            if m and (
                topic_key(_queue_item_name(m.group(2))) == key
                or topic.lower() in m.group(2).lower()
            ):
                lines.append(f"- [x] {m.group(2)}")
                changed = True
            else:
                lines.append(ln)
        if not changed:
            return f"Not found in queue: {topic}"
        new_queue = "\n".join(lines) + ("\n" if lines else "")
    text = _replace_section(text, "Study queue", new_queue)
    PROFILE_PATH.write_text(text, encoding="utf-8")
    return f"Marked done in queue: {topic}"


def first_open_queue_topic() -> str:
    """Return the first unchecked queue item topic, or empty string."""
    ensure_profile()
    queue = _section(read_profile(), "Study queue")
    for item in re.findall(r"- \[ \]\s+(.+)", queue):
        return _queue_item_name(item)
    return ""


# --- Project learning (.cursor/learning/project.md) ---


def resolve_project_root(
    cwd: str | Path | None = None,
    workspace_roots: list[str] | None = None,
) -> Path:
    """Resolve the project root used for sheet paths.

    Precedence (HOOKS_AGENTS_CONTRACTS.md §4):
    1. explicit cwd / --cwd
    2. first existing absolute path in workspace_roots
    3. Path.cwd()
    """
    if cwd is not None and str(cwd).strip():
        return Path(cwd).expanduser().resolve()
    for root in workspace_roots or []:
        path = Path(root).expanduser()
        if path.is_absolute() and path.exists():
            return path.resolve()
    return Path.cwd().resolve()


def project_path(
    cwd: str | Path | None = None,
    workspace_roots: list[str] | None = None,
) -> Path:
    root = resolve_project_root(cwd=cwd, workspace_roots=workspace_roots)
    return root / PROJECT_RELATIVE_PATH


def legacy_project_path(
    cwd: str | Path | None = None,
    workspace_roots: list[str] | None = None,
) -> Path:
    root = resolve_project_root(cwd=cwd, workspace_roots=workspace_roots)
    return root / LEGACY_PROJECT_RELATIVE_PATH


def find_project_sheet(
    start: str | Path | None = None,
    *,
    workspace_roots: list[str] | None = None,
    walk_ancestors: bool = False,
    max_ancestors: int = 8,
) -> Path | None:
    """Locate an existing project sheet.

    When walk_ancestors is True (sessionStart injection), search up to
    max_ancestors parents. CLI writes keep walk_ancestors=False.
    """
    cur = resolve_project_root(cwd=start, workspace_roots=workspace_roots)
    steps = max_ancestors if walk_ancestors else 0
    for _ in range(steps + 1):
        for candidate in (
            cur / PROJECT_RELATIVE_PATH,
            cur / LEGACY_PROJECT_RELATIVE_PATH,
        ):
            if candidate.is_file():
                return candidate
        if not walk_ancestors or cur.parent == cur:
            break
        cur = cur.parent
    return None


def _existing_project_path(cwd: str | Path | None = None) -> Path:
    path = project_path(cwd)
    if path.exists():
        return path
    legacy_path = legacy_project_path(cwd)
    return legacy_path if legacy_path.exists() else path


def ensure_project(cwd: str | Path | None = None) -> Path:
    path = project_path(cwd)
    path.parent.mkdir(parents=True, exist_ok=True)
    legacy_path = legacy_project_path(cwd)
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
    path = project_path(cwd)
    if not path.exists() and legacy_project_path(cwd).exists():
        path = ensure_project(cwd)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def project_show(cwd: str | Path | None = None) -> str:
    text = read_project(cwd)
    if not text.strip():
        return f"(no project sheet at {project_path(cwd)})"
    return text


def _parse_list_items(section_body: str) -> list[str]:
    items: list[str] = []
    for ln in section_body.splitlines():
        stripped = ln.strip()
        if not stripped or stripped.startswith("_"):
            continue
        m = re.match(r"- \[[ x]\]\s+(.+)", stripped)
        if m:
            items.append(_queue_item_name(m.group(1)))
            continue
        m = re.match(r"-\s+(.+)", stripped)
        if m:
            items.append(m.group(1).strip())
    return items


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
        text = _replace_section(text, "Stack", body)

    if candidates.strip():
        parts = [p.strip() for p in candidates.split(";") if p.strip()]
        parts = [
            normalize_topic_display(p)
            for p in parts
            if not is_noisy_topic(p)
        ]
        seen: set[str] = set()
        unique: list[str] = []
        for p in parts:
            k = topic_key(p)
            if k in seen:
                continue
            seen.add(k)
            unique.append(p)
        body = (
            "\n".join(f"- [ ] {p}" for p in unique) + "\n"
            if unique
            else "_Empty._\n"
        )
        text = _replace_section(text, "Study candidates", body)

    if probe_summary.strip():
        body = (
            f"- Date: {date.today().isoformat()}\n"
            f"- Summary: {probe_summary.strip()}\n"
        )
        text = _replace_section(text, "Last probe", body)

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
    section = _section(text, "Study candidates")
    key = topic_key(topic_disp)
    lines: list[str] = []
    removed = False
    for ln in section.splitlines():
        m = re.match(r"- \[[ x]\]\s+(.+)", ln.strip())
        if m and topic_key(_queue_item_name(m.group(1))) == key:
            removed = True
            continue
        m2 = re.match(r"-\s+(.+)", ln.strip())
        if m2 and not ln.strip().startswith("- [") and topic_key(m2.group(1)) == key:
            removed = True
            continue
        lines.append(ln)
    if not removed:
        return f"Candidate not found: {topic_disp}"
    kept = [ln for ln in lines if ln.strip() and not ln.strip().startswith("_")]
    body = "\n".join(kept) + "\n" if kept else "_Empty._\n"
    text = _replace_section(text, "Study candidates", body)
    path.write_text(text, encoding="utf-8")
    return f"Removed project candidate: {topic_disp}"


def truncate_for_inject(content: str, max_chars: int = 6000) -> str:
    if len(content) <= max_chars:
        return content
    return content[:800] + "\n...\n" + content[-(max_chars - 800) :]
