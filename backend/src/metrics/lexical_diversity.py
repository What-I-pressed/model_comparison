"""Лексичне розмаїття -- MATTR (Moving-Average Type-Token Ratio).

Звичайний TTR (унікальні слова / усі слова) сильно залежить від довжини
тексту: короткі пісні штучно отримують вищий скор. MATTR рахує TTR у вікні
фіксованого розміру, що ковзає по тексту, і усереднює -- це робить метрику
чесною для пісень різної довжини. Референс на підхід (лексичне розмаїття
як одна з ключових характеристик складності тексту пісні):
https://medium.com/@ameenbasith2000/breaking-down-lyrics-how-i-built-a-tool-to-analyze-song-complexity-and-enhance-songwriting-d3f8778065e3
"""
from __future__ import annotations

from .text_utils import all_words, clamp01

_WINDOW = 15


def lexical_diversity_score(lyrics: str) -> float:
    words = all_words(lyrics)
    if len(words) < 2:
        return 0.0

    window = min(_WINDOW, len(words))
    if len(words) <= window:
        return clamp01(len(set(words)) / len(words))

    ratios = []
    for i in range(len(words) - window + 1):
        chunk = words[i : i + window]
        ratios.append(len(set(chunk)) / window)
    return clamp01(sum(ratios) / len(ratios))
