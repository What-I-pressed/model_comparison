"""Юніт-тести метрик -- усі працюють повністю локально, без мережі.

Запуск: cd backend && python -m pytest tests/ -v
"""
from __future__ import annotations

from src.metrics.lexical_diversity import lexical_diversity_score
from src.metrics.price import price_score
from src.metrics.readability import readability_score
from src.metrics.rhyme import rhyme_score, word_rhyme_similarity
from src.metrics.syllables import count_syllables, syllable_stability_score
from src.metrics.weather_accuracy import weather_accuracy_score
from src.weather_client import WeatherSnapshot

GOOD_SONG = (
    "Над Києвом хмари низько пливуть,\n"
    "Дощі по каштанах тихо цокотять,\n"
    "У парку алеї вогке несуть,\n"
    "І люди під парасольками мовчать.\n"
)

BAD_SONG = (
    "Дощ дощ дощ дощ дощ,\n"
    "Дощ дощ дощ дощ,\n"
    "Дощ дощ дощ дощ дощ дощ дощ дощ дощ,\n"
    "Дощ.\n"
)

KYIV_RAIN = WeatherSnapshot(
    city="Київ",
    temperature_c=3.0,
    apparent_temperature_c=-1.0,
    wind_speed_kmh=18.0,
    precipitation_mm=0.4,
    weather_code=61,
    condition_text="невеликий дощ",
)


def test_count_syllables_basic():
    assert count_syllables("привіт") == 2
    assert count_syllables("а") == 1
    assert count_syllables("") == 0


def test_word_rhyme_similarity_exact_and_none():
    assert word_rhyme_similarity("пливуть", "несуть") > 0.3
    assert word_rhyme_similarity("сонце", "дощ") < 0.3
    assert word_rhyme_similarity("", "щось") == 0.0


def test_rhyme_score_in_range():
    score = rhyme_score(GOOD_SONG)
    assert 0.0 <= score <= 1.0


def test_syllable_stability_perfect_repetition_is_high():
    # Один і той самий рядок, повторений -- ідеально стабільний ритм.
    repeated = "раз два три чотири\nраз два три чотири\n"
    assert syllable_stability_score(repeated) > 0.9


def test_syllable_stability_range():
    assert 0.0 <= syllable_stability_score(GOOD_SONG) <= 1.0
    assert syllable_stability_score("") == 0.0


def test_lexical_diversity_penalizes_repetition():
    assert lexical_diversity_score(BAD_SONG) < lexical_diversity_score(GOOD_SONG)


def test_lexical_diversity_range():
    assert 0.0 <= lexical_diversity_score(GOOD_SONG) <= 1.0
    assert lexical_diversity_score("") == 0.0


def test_readability_short_words_score_higher():
    short = "дощ йде\nвітер дме\n"
    long_words = "паралелепіпедоподібний конденсаційний метеорологічний феномен\n"
    assert readability_score(short) > readability_score(long_words)


def test_price_score_cheapest_gets_max():
    costs = [0.001, 0.01, 0.05]
    assert price_score(0.001, costs) == 1.0
    assert price_score(0.05, costs) == 0.0
    assert 0.0 < price_score(0.01, costs) < 1.0


def test_price_score_single_value_no_crash():
    assert price_score(0.02, [0.02]) == 1.0
    assert price_score(0.02, []) == 1.0


def test_weather_accuracy_rewards_correct_mentions():
    accurate = "У Києві дощить, холодно і сіро,\nтри градуси на термометрі."
    inaccurate = "У Львові сонце і спека, чудове літо!"
    assert weather_accuracy_score(accurate, KYIV_RAIN) > weather_accuracy_score(inaccurate, KYIV_RAIN)


def test_weather_accuracy_range():
    assert 0.0 <= weather_accuracy_score(GOOD_SONG, KYIV_RAIN) <= 1.0
