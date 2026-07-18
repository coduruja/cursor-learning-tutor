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
PROJECT_FILENAME = "learning-project.md"

LEVELS = ("iniciante", "intermediário", "avançado")

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
        "arquivo",
        "erro",
        "funcao",
        "função",
        "bug",
        "coisa",
        "isso",
        "aquilo",
        "modulo",
        "módulo",
        "projeto",
        "repo",
        "repositorio",
        "repositório",
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

HEADER = """# Perfil de Aprendizado (global)

> Mantido pelo Learning Tutor. Edite à mão se quiser; os comandos `/study-log` e os hooks atualizam este arquivo.

## Meta
- Nível geral: {level}
- Foco atual: {focus}

## Fila de estudo

_Vazia._

## Coberto

"""

PROJECT_HEADER = """# Aprendizado do projeto

> Stack e candidatos locais. Fila/coberto ficam no perfil global (`~/.cursor/learning/profile.md`).

## Stack

_Nenhuma._

## Candidatos de estudo

_Vazio._

## Última sondagem

_Nenhuma._

"""


def ensure_dir() -> None:
    LEARNING_DIR.mkdir(parents=True, exist_ok=True)


def ensure_profile(level: str = "não definido", focus: str = "não definido") -> None:
    ensure_dir()
    if PROFILE_PATH.exists():
        return
    PROFILE_PATH.write_text(
        HEADER.format(level=level, focus=focus) + "_Nenhuma entrada ainda._\n",
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
    has_covered = "## Coberto" in text and "### " in _section(text, "Coberto")
    return not has_queue_item and not has_covered


def _section(text: str, title: str) -> str:
    pattern = rf"## {re.escape(title)}\n(.*?)(?=\n## |\Z)"
    m = re.search(pattern, text, flags=re.S)
    return m.group(1) if m else ""


def _replace_section(text: str, title: str, body: str) -> str:
    pattern = rf"(## {re.escape(title)}\n)(.*?)(?=\n## |\Z)"
    body = body.rstrip() + "\n\n"
    if re.search(pattern, text, flags=re.S):
        return re.sub(pattern, rf"\1{body}", text, count=1, flags=re.S)
    return text.rstrip() + f"\n\n## {title}\n{body}"


def _normalize_level(level: str) -> str:
    raw = (level or "").strip().lower()
    aliases = {
        "iniciante": "iniciante",
        "beginner": "iniciante",
        "intermediario": "intermediário",
        "intermediário": "intermediário",
        "intermediate": "intermediário",
        "avancado": "avançado",
        "avançado": "avançado",
        "advanced": "avançado",
    }
    return aliases.get(raw, raw or "intermediário")


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
    focus = (focus or "não definido").strip() or "não definido"
    if PROFILE_PATH.exists() and not profile_is_empty():
        text = read_profile()
        text = re.sub(
            r"(- Nível geral:\s*).*",
            rf"\1{level}",
            text,
            count=1,
        )
        text = re.sub(
            r"(- Foco atual:\s*).*",
            rf"\1{focus}",
            text,
            count=1,
        )
        PROFILE_PATH.write_text(text, encoding="utf-8")
        return f"Atualizei meta: nível={level}, foco={focus}"
    PROFILE_PATH.write_text(
        HEADER.format(level=level, focus=focus) + "_Nenhuma entrada ainda._\n",
        encoding="utf-8",
    )
    return f"Criei perfil: nível={level}, foco={focus}"


def add_covered(topic: str, level: str, note: str = "") -> str:
    topic = normalize_topic_display(topic)
    if not topic:
        raise ValueError("topic vazio")
    if is_noisy_topic(topic):
        return f"Ignorado (tópico genérico/linguagem base): {topic}"
    level = _normalize_level(level)
    note = (note or "").strip()
    ensure_profile()
    text = read_profile()
    entry = f"### {date.today().isoformat()} — {topic}\n- Nível: {level}\n"
    if note:
        entry += f"- Contexto: {note}\n"
    entry += "\n"

    covered = _section(text, "Coberto")
    if covered.strip() in ("", "_Nenhuma entrada ainda._"):
        new_covered = entry
    else:
        new_covered = covered.lstrip("\n")
        if not new_covered.endswith("\n"):
            new_covered += "\n"
        new_covered = entry + new_covered
    text = _replace_section(text, "Coberto", new_covered)
    PROFILE_PATH.write_text(text, encoding="utf-8")
    return f"Salvei no perfil (coberto): {topic} [{level}]"


def add_want(topic: str, note: str = "") -> str:
    topic = normalize_topic_display(topic)
    if not topic:
        raise ValueError("topic vazio")
    if is_noisy_topic(topic):
        return f"Ignorado (tópico genérico/linguagem base): {topic}"
    note = (note or "").strip()
    ensure_profile()
    text = read_profile()
    queue = _section(text, "Fila de estudo")
    if _topic_in_queue(queue, topic):
        return f"Já estava na fila: {topic}"
    covered = _section(text, "Coberto")
    if _topic_in_covered(covered, topic):
        return f"Já coberto recentemente: {topic}"

    line = f"- [ ] {topic}"
    if note:
        line += f" — {note}"
    lines = [ln for ln in queue.splitlines() if ln.strip() and ln.strip() != "_Vazia._"]
    lines.append(line)
    body = "\n".join(lines) + "\n"
    text = _replace_section(text, "Fila de estudo", body)
    PROFILE_PATH.write_text(text, encoding="utf-8")
    return f"Salvei no perfil (fila): {topic}"


def mark_done(topic: str) -> str:
    topic = normalize_topic_display(topic) or topic.strip()
    ensure_profile()
    text = read_profile()
    queue = _section(text, "Fila de estudo")
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
            if m and (topic_key(_queue_item_name(m.group(2))) == key or topic.lower() in m.group(2).lower()):
                lines.append(f"- [x] {m.group(2)}")
                changed = True
            else:
                lines.append(ln)
        if not changed:
            return f"Não achei na fila: {topic}"
        new_queue = "\n".join(lines) + ("\n" if lines else "")
    text = _replace_section(text, "Fila de estudo", new_queue)
    PROFILE_PATH.write_text(text, encoding="utf-8")
    return f"Marquei como feito na fila: {topic}"


def first_open_queue_topic() -> str:
    """Return the first unchecked queue item topic, or empty string."""
    ensure_profile()
    queue = _section(read_profile(), "Fila de estudo")
    for item in re.findall(r"- \[ \]\s+(.+)", queue):
        return _queue_item_name(item)
    return ""


# --- Project learning (.cursor/learning-project.md) ---


def project_path(cwd: str | Path | None = None) -> Path:
    root = Path(cwd) if cwd else Path.cwd()
    return root / ".cursor" / PROJECT_FILENAME


def ensure_project(cwd: str | Path | None = None) -> Path:
    path = project_path(cwd)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(PROJECT_HEADER, encoding="utf-8")
    return path


def read_project(cwd: str | Path | None = None) -> str:
    path = project_path(cwd)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def project_show(cwd: str | Path | None = None) -> str:
    text = read_project(cwd)
    if not text.strip():
        return f"(sem {PROJECT_FILENAME} em {project_path(cwd)})"
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
    probe_summary: optional summary for Última sondagem
    """
    path = ensure_project(cwd)
    text = path.read_text(encoding="utf-8")

    if stack.strip():
        parts = [p.strip() for p in re.split(r"[;,]", stack) if p.strip()]
        # Drop bare base languages from stack list
        parts = [p for p in parts if topic_key(p) not in BASE_LANGUAGES]
        body = "\n".join(f"- {p}" for p in parts) + "\n" if parts else "_Nenhuma._\n"
        text = _replace_section(text, "Stack", body)

    if candidates.strip():
        parts = [p.strip() for p in candidates.split(";") if p.strip()]
        parts = [
            normalize_topic_display(p)
            for p in parts
            if not is_noisy_topic(p)
        ]
        # Dedupe by topic_key preserving order
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
            else "_Vazio._\n"
        )
        text = _replace_section(text, "Candidatos de estudo", body)

    if probe_summary.strip():
        body = (
            f"- Data: {date.today().isoformat()}\n"
            f"- Resumo: {probe_summary.strip()}\n"
        )
        text = _replace_section(text, "Última sondagem", body)

    path.write_text(text, encoding="utf-8")
    return f"Atualizei {path}"


def project_drop_candidate(topic: str, cwd: str | Path | None = None) -> str:
    topic_disp = normalize_topic_display(topic) or topic.strip()
    if not topic_disp:
        raise ValueError("topic vazio")
    path = project_path(cwd)
    if not path.exists():
        return f"Sem arquivo de projeto: {path}"
    text = path.read_text(encoding="utf-8")
    section = _section(text, "Candidatos de estudo")
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
        return f"Candidato não encontrado: {topic_disp}"
    kept = [ln for ln in lines if ln.strip() and not ln.strip().startswith("_")]
    body = "\n".join(kept) + "\n" if kept else "_Vazio._\n"
    text = _replace_section(text, "Candidatos de estudo", body)
    path.write_text(text, encoding="utf-8")
    return f"Removi candidato do projeto: {topic_disp}"


def truncate_for_inject(content: str, max_chars: int = 6000) -> str:
    if len(content) <= max_chars:
        return content
    return content[:800] + "\n...\n" + content[-(max_chars - 800) :]
