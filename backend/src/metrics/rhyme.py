"""Оцінка якості рими.

Підхід: для кожного куплету дивимось на останні слова рядків і перевіряємо
дві найпоширеніші схеми рими -- суміжну (AABB: 0-1, 2-3, ...) та перехресну
(ABAB: 0-2, 1-3, ...). Обираємо ту схему, яка дає вищу середню "співзвучність"
закінчень, бо автор міг використати будь-яку з них.

Співзвучність двох слів рахуємо як частку спільного закінчення (суфікса)
серед останніх 4 літер слова -- це проста, але доволі надійна евристика для
рими в українській мові, де римуються переважно останні 1-3 склади.
"""
from __future__ import annotations

from .text_utils import clamp01, last_word, split_stanzas

_TAIL_LEN = 4


def _common_suffix_len(a: str, b: str) -> int:
    n = 0
    for ca, cb in zip(reversed(a), reversed(b)):
        if ca != cb:
            break
        n += 1
    return n


def word_rhyme_similarity(word_a: str, word_b: str) -> float:
    """0..1 -- наскільки схоже звучать закінчення двох слів."""
    if not word_a or not word_b:
        return 0.0
    if word_a == word_b:
        # Однакове слово -- це не справжня рима, а повтор; не караємо повністю,
        # але й не даємо максимум, щоб не заохочувати "рими" копіюванням слова.
        return 0.6
    tail_a, tail_b = word_a[-_TAIL_LEN:], word_b[-_TAIL_LEN:]
    common = _common_suffix_len(tail_a, tail_b)
    return clamp01(common / max(len(tail_a), len(tail_b)))


def _pair_score(endings: list[str], pairs: list[tuple[int, int]]) -> float | None:
    sims = []
    for i, j in pairs:
        if i < len(endings) and j < len(endings):
            sims.append(word_rhyme_similarity(endings[i], endings[j]))
    if not sims:
        return None
    return sum(sims) / len(sims)


def _stanza_rhyme_score(lines: list[str]) -> float | None:
    endings = [last_word(line) or "" for line in lines]
    endings = [e for e in endings if e]
    if len(endings) < 2:
        return None

    n = len(endings)
    aabb_pairs = [(i, i + 1) for i in range(0, n - 1, 2)]
    abab_pairs = [(i, i + 2) for i in range(0, n - 2, 1) if i % 2 == 0]

    candidates = [s for s in (_pair_score(endings, aabb_pairs), _pair_score(endings, abab_pairs)) if s is not None]
    if not candidates:
        return None
    return max(candidates)


def rhyme_score(lyrics: str) -> float:
    """0..1 -- усереднена якість рими по всіх куплетах пісні."""
    stanzas = split_stanzas(lyrics)
    scores = [s for s in (_stanza_rhyme_score(st) for st in stanzas) if s is not None]
    if not scores:
        return 0.0
    return sum(scores) / len(scores)
