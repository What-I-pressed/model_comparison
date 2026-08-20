"""Спільні текстові утиліти, якими користуються всі метрики.

Усе працює локально, без мережі та без важких NLP-бібліотек -- для
української мови немає надійних готових пакетів рівня spaCy з ліцензією
"з коробки", тож ми свідомо йдемо шляхом простих, прозорих евристик,
які легко пояснити і перевірити вручну.
"""
from __future__ import annotations

import re

UK_VOWELS = set("аеєиіїоуюя")

_WORD_RE = re.compile(r"[а-щьюяєіїґ'’-]+", re.IGNORECASE)


def split_lines(lyrics: str) -> list[str]:
    """Розбиває текст пісні на непорожні рядки (порожні рядки = межі куплетів)."""
    return [line.strip() for line in lyrics.splitlines() if line.strip()]


def split_stanzas(lyrics: str) -> list[list[str]]:
    """Розбиває пісню на куплети за порожніми рядками."""
    stanzas: list[list[str]] = []
    current: list[str] = []
    for raw_line in lyrics.splitlines():
        line = raw_line.strip()
        if line:
            current.append(line)
        elif current:
            stanzas.append(current)
            current = []
    if current:
        stanzas.append(current)
    return stanzas


def words_in_line(line: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(line)]


def all_words(lyrics: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(lyrics)]


def last_word(line: str) -> str | None:
    words = words_in_line(line)
    return words[-1] if words else None


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
