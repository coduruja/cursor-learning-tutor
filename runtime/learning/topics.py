"""Topic normalization, aliases, and anti-noise filters."""

from __future__ import annotations

import re
import unicodedata

LEVELS = ("beginner", "intermediate", "advanced")

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


def normalize_level(level: str) -> str:
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


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def topic_key(topic: str) -> str:
    """Normalized key for dedupe (aliases collapse to one canonical key)."""
    raw = strip_accents((topic or "").strip().lower())
    raw = re.sub(r"\s+", " ", raw)
    if raw in TOPIC_ALIASES:
        return strip_accents(TOPIC_ALIASES[raw].lower())
    return raw


def normalize_topic_display(topic: str) -> str:
    """Canonical display name when an alias exists; otherwise trimmed original."""
    stripped = (topic or "").strip()
    if not stripped:
        return ""
    key = strip_accents(stripped.lower())
    key = re.sub(r"\s+", " ", key)
    if key in TOPIC_ALIASES:
        return TOPIC_ALIASES[key]
    return stripped


def is_noisy_topic(topic: str) -> bool:
    key = topic_key(topic)
    return key in GENERIC_TOPICS or key in BASE_LANGUAGES


def queue_item_name(item: str) -> str:
    return item.split("—")[0].strip()
