"""Читабельність тексту пісні.

Класичні формули на кшталт Flesch Reading Ease каліброві під англійську
(де середнє слово ~1.5 склади) і не мають валідованого аналога для
української, тож тут -- прозора власна евристика на тих самих двох
складових, що лежать в основі більшості формул читабельності:

  1. середня довжина слова в складах (коротші слова -> легше сприймати),
  2. середня довжина рядка в словах (коротші рядки -> легше заспівати).

Обидва фактори нормалізуються до [0, 1] відносно "розумних" меж для пісенного
тексту та комбінуються з вагами 60/40 (довжина слова важливіша для
"заспіваності", ніж довжина рядка). Результат: 1.0 -- дуже легкий,
"розмовний" текст; 0.0 -- важкий, перевантажений довгими словами.
"""
from __future__ import annotations

from .syllables import count_syllables
from .text_utils import all_words, clamp01, split_lines, words_in_line

# Орієнтовні "комфортні" межі для пісенного тексту -- підібрані вручну,
# не з валідованого дослідження. За потреби легко відкалібрувати.
_SYLLABLES_PER_WORD_COMFORT_MAX = 3.5  # вище -- текст відчутно важчає
_WORDS_PER_LINE_COMFORT_MAX = 9.0  # вище -- рядок важко заспівати на диханні


def readability_score(lyrics: str) -> float:
    words = all_words(lyrics)
    lines = split_lines(lyrics)
    if not words or not lines:
        return 0.0

    avg_syllables_per_word = sum(count_syllables(w) for w in words) / len(words)
    avg_words_per_line = sum(len(words_in_line(line)) for line in lines) / len(lines)

    word_penalty = clamp01(avg_syllables_per_word / _SYLLABLES_PER_WORD_COMFORT_MAX)
    line_penalty = clamp01(avg_words_per_line / _WORDS_PER_LINE_COMFORT_MAX)

    difficulty = 0.6 * word_penalty + 0.4 * line_penalty
    return clamp01(1.0 - difficulty)
