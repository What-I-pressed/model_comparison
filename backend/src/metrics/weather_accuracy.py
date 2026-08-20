"""Влучність пісні у реальні погодні дані міста.

Перевіряємо три речі за ключовими словами (прозоро й без мережі):

  1. чи згадано назву міста (0.2 ваги),
  2. чи згадані погодні явища відповідають фактичному стану неба
     (дощ/сніг/сонце/хмарно/туман/гроза -- 0.4 ваги, з штрафом за
     суперечність, напр. "сонце" коли насправді йде дощ),
  3. чи "температурний регістр" тексту (холодно/тепло) відповідає
     фактичній температурі (0.4 ваги, так само зі штрафом за суперечність).

Якщо пісня взагалі не згадує явищ чи температури явно -- це не карається
на нуль (LLM могла обрати образну, а не пряму мову), а отримує нейтральний
частковий бал.
"""
from __future__ import annotations

from .text_utils import clamp01
from ..weather_client import WeatherSnapshot

_CONDITION_KEYWORDS: dict[str, list[str]] = {
    "rain": ["дощ", "мряк", "злив"],
    "snow": ["сніг", "снігопад", "заметіл", "хуртовин"],
    "clear": ["сонц", "сонячн", "ясно", "безхмарн"],
    "cloudy": ["хмар", "похмур"],
    "fog": ["туман"],
    "storm": ["гроза", "грім", "блискав", "град"],
}

_COLD_WORDS = ["холод", "мороз", "замерз", "крижан", "зимно", "стужа"]
_WARM_WORDS = ["спек", "жарко", "спекотн", "тепло", "тепл"]


def _actual_condition_category(weather_code: int) -> str | None:
    if weather_code in (0, 1):
        return "clear"
    if weather_code in (2, 3):
        return "cloudy"
    if weather_code in (45, 48):
        return "fog"
    if weather_code in (51, 53, 55, 61, 63, 65, 80, 81, 82):
        return "rain"
    if weather_code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if weather_code in (95, 96, 99):
        return "storm"
    return None


def _temperature_bucket(temperature_c: float) -> str:
    if temperature_c < 8:
        return "cold"
    if temperature_c > 20:
        return "warm"
    return "mild"


def weather_accuracy_score(lyrics: str, weather: WeatherSnapshot) -> float:
    text = lyrics.lower()

    # 1. Назва міста (враховуємо, що вона може бути у відмінку, тому
    #    порівнюємо основу слова -- без останньої літери).
    city = weather.city.lower()
    city_stem = city[:-1] if len(city) > 3 else city
    city_component = 1.0 if city_stem in text else 0.0

    # 2. Погодні явища.
    found_categories = {
        cat for cat, kws in _CONDITION_KEYWORDS.items() if any(kw in text for kw in kws)
    }
    actual_category = _actual_condition_category(weather.weather_code)
    if actual_category and actual_category in found_categories:
        condition_component = 1.0
    elif found_categories and actual_category not in found_categories:
        condition_component = 0.0  # згадали явище, яке суперечить реальності
    else:
        condition_component = 0.3  # нічого конкретного не згадано -- нейтрально

    # 3. Температурний регістр.
    bucket = _temperature_bucket(weather.temperature_c)
    found_cold = any(w in text for w in _COLD_WORDS)
    found_warm = any(w in text for w in _WARM_WORDS)

    if bucket == "cold":
        temp_component = 1.0 if found_cold and not found_warm else (0.0 if found_warm else 0.3)
    elif bucket == "warm":
        temp_component = 1.0 if found_warm and not found_cold else (0.0 if found_cold else 0.3)
    else:
        temp_component = 0.5 if found_cold and found_warm else 0.7

    score = 0.2 * city_component + 0.4 * condition_component + 0.4 * temp_component
    return clamp01(score)
