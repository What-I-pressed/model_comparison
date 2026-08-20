"""Кількість складів та стабільність складового малюнка (ритму).

Для української мови кількість складів у слові дорівнює кількості голосних
звуків -- надійних open-source hyphenation-словників для uk немає (pyphen
не має словника uk_UA), тож рахуємо голосні напряму. Це стандартний і
точний спосіб для слов'янських мов, бо голосна = ядро складу.

Стабільність ритму рахуємо так: пісню, яку можна заспівати, зазвичай легко
розбити на пари/четвірки рядків з майже однаковою кількістю складів
(як у куплеті AABB чи ABAB). Тому для кожного куплету дивимось на
коефіцієнт варіації (CV = stdev / mean) довжини рядків у складах:
чим він менший -- тим стабільніший ритм. Скор = 1 - CV, обрізаний до [0, 1].
"""
from __future__ import annotations

import statistics

from .text_utils import UK_VOWELS, split_stanzas, words_in_line, clamp01


def count_syllables(word: str) -> int:
    """Кількість складів у слові = кількість голосних літер."""
    return sum(1 for ch in word.lower() if ch in UK_VOWELS)


def count_syllables_in_line(line: str) -> int:
    return sum(count_syllables(w) for w in words_in_line(line))


def syllable_stability_score(lyrics: str) -> float:
    """0..1, де 1 -- ідеально стабільний складовий малюнок по всій пісні."""
    stanzas = split_stanzas(lyrics)
    if not stanzas:
        return 0.0

    stanza_scores: list[float] = []
    for stanza in stanzas:
        counts = [count_syllables_in_line(line) for line in stanza]
        counts = [c for c in counts if c > 0]
        if len(counts) < 2:
            continue
        mean = statistics.mean(counts)
        if mean == 0:
            continue
        stdev = statistics.pstdev(counts)
        cv = stdev / mean
        stanza_scores.append(clamp01(1.0 - cv))

    if not stanza_scores:
        return 0.0
    return sum(stanza_scores) / len(stanza_scores)
