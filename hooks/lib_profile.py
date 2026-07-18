"""Shared helpers for the Learning Tutor profile (~/.cursor/learning/)."""

from __future__ import annotations

import os
import re
import shutil
from datetime import date
from pathlib import Path

LEARNING_DIR = Path(os.path.expanduser("~/.cursor/learning"))
PROFILE_PATH = LEARNING_DIR / "profile.md"
CLI_PATH = LEARNING_DIR / "cli.py"
LIB_PATH = LEARNING_DIR / "lib_profile.py"

LEVELS = ("iniciante", "intermediário", "avançado")

HEADER = """# Perfil de Aprendizado (global)

> Mantido pelo Learning Tutor. Edite à mão se quiser; os comandos `/study-log` e os hooks atualizam este arquivo.

## Meta
- Nível geral: {level}
- Foco atual: {focus}

## Fila de estudo

_Vazia._

## Coberto

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
    topic = topic.strip()
    if not topic:
        raise ValueError("topic vazio")
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
    topic = topic.strip()
    if not topic:
        raise ValueError("topic vazio")
    note = (note or "").strip()
    ensure_profile()
    text = read_profile()
    queue = _section(text, "Fila de estudo")
    # Avoid duplicates (case-insensitive)
    existing = re.findall(r"- \[[ x]\]\s+(.+)", queue)
    for item in existing:
        name = item.split("—")[0].strip()
        if name.lower() == topic.lower():
            return f"Já estava na fila: {topic}"

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
    topic = topic.strip()
    ensure_profile()
    text = read_profile()
    queue = _section(text, "Fila de estudo")

    def repl(match: re.Match[str]) -> str:
        name = match.group(2).split("—")[0].strip()
        if name.lower() == topic.lower():
            return f"- [x] {match.group(2)}"
        return match.group(0)

    new_queue, n = re.subn(
        r"- \[([ x])\]\s+(.+)",
        repl,
        queue,
    )
    if n == 0 or new_queue == queue:
        # try partial match
        changed = False
        lines = []
        for ln in queue.splitlines():
            m = re.match(r"- \[([ x])\]\s+(.+)", ln)
            if m and topic.lower() in m.group(2).lower():
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


def truncate_for_inject(content: str, max_chars: int = 6000) -> str:
    if len(content) <= max_chars:
        return content
    return content[:800] + "\n...\n" + content[-(max_chars - 800) :]
