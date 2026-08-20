"""Синтетичні дані для локального тестування сайту без мережевих викликів.

Використовуються справжні функції метрик (rhyme/syllables/lexical/readability/
weather_accuracy) на прикладних текстах пісень -- єдине, що симулюється, це
ціна генерації та оцінка LLM-судді (бо для них потрібна мережа). Це дозволяє
зібрати робочий results.json і перевірити весь сайт ще до реального прогону
на OpenRouter.

Запуск: `python -m src.main --mode demo` (з кореня backend/).
"""
from __future__ import annotations

import random
from dataclasses import asdict
from datetime import datetime, timezone

from .metrics import (
    lexical_diversity_score,
    price_score,
    readability_score,
    rhyme_score,
    syllable_stability_score,
    weather_accuracy_score,
)
from .pipeline import METRICS_META
from .weather_client import WeatherSnapshot

_DEMO_WEATHER = {
    "Київ": WeatherSnapshot(
        city="Київ",
        temperature_c=3.0,
        apparent_temperature_c=-1.0,
        wind_speed_kmh=18.0,
        precipitation_mm=0.4,
        weather_code=61,
        condition_text="невеликий дощ",
    ),
    "Львів": WeatherSnapshot(
        city="Львів",
        temperature_c=-4.0,
        apparent_temperature_c=-9.0,
        wind_speed_kmh=12.0,
        precipitation_mm=1.2,
        weather_code=73,
        condition_text="сніг",
    ),
}

_BASE_SONGS = {
    "Київ": (
        "Над Києвом хмари низько пливуть,\n"
        "Дощі по каштанах тихо цокотять,\n"
        "У парку алеї вогке несуть,\n"
        "І люди під парасольками мовчать.\n"
        "\n"
        "Три градуси в місті, вітер гуляє,\n"
        "Дніпро потемнів, накрився хвилею,\n"
        "Хтозна, чи сонце завтра засяє,\n"
        "Та Київ вітає осінь новою мрією.\n"
    ),
    "Львів": (
        "Сніжинки кружляють над Личаківською брамою,\n"
        "Морозний Львів вкрився білою піною,\n"
        "Кава гаряча парує над рамою,\n"
        "А місто дзвенить бруківкою й тишиною.\n"
        "\n"
        "Чотири нижче нуля, а на серці тепло,\n"
        "Легкий вітерець колихає ліхтарі,\n"
        "Снігом вкрилось старе рідне небо,\n"
        "Й Львів співає зимові свої пісні.\n"
    ),
}

# (display_name, id, "якість" 0-1 -- визначає ступінь синтетичної деградації тексту,
# орієнтовний множник ціни відносно GPT-4o mini, для реалістичного розкиду в демо)
_MODEL_PROFILES = [
    ("GPT-4o mini", "openai/gpt-4o-mini", 0.78, 1.0),
    ("GPT-4o", "openai/gpt-4o", 0.92, 14.0),
    ("Claude 3.5 Sonnet", "anthropic/claude-3.5-sonnet", 0.95, 11.0),
    ("Gemini 2.0 Flash", "google/gemini-2.0-flash-001", 0.83, 0.6),
    ("Llama 3.3 70B", "meta-llama/llama-3.3-70b-instruct", 0.7, 1.6),
    ("Mistral Large", "mistralai/mistral-large", 0.8, 8.0),
    ("DeepSeek Chat", "deepseek/deepseek-chat", 0.75, 0.5),
    ("Qwen 2.5 72B", "qwen/qwen-2.5-72b-instruct", 0.72, 1.3),
]


def _degrade(text: str, quality: float, rng: random.Random) -> str:
    """Синтетично псує текст обернено пропорційно до "якості" моделі.

    Це лише для демонстрації розкиду метрик на сайті -- реальні тексти
    з'являться після справжнього прогону на OpenRouter.
    """
    lines = text.splitlines()
    out = []
    for line in lines:
        words = line.split()
        if not words:
            out.append(line)
            continue
        # Гірша модель -> частіше повторює останнє слово (псує риму/лексику).
        if rng.random() > quality and len(words) > 2:
            words[-1] = words[rng.randint(0, len(words) - 2)]
        # Гірша модель -> частіше зникає/додається слово (псує стабільність складів).
        if rng.random() > quality + 0.15:
            if rng.random() < 0.5 and len(words) > 3:
                del words[rng.randint(0, len(words) - 1)]
            else:
                words.insert(rng.randint(0, len(words)), words[0])
        out.append(" ".join(words))
    return "\n".join(out)


def generate_demo_results() -> dict:
    rng = random.Random(42)
    entries = []
    costs = []

    raw_entries = []
    for display_name, model_id, quality, price_multiplier in _MODEL_PROFILES:
        for city, weather in _DEMO_WEATHER.items():
            lyrics = _degrade(_BASE_SONGS[city], quality, rng)
            base_tokens = 220
            cost = round(price_multiplier * base_tokens * 0.000002 * rng.uniform(0.9, 1.1), 6)
            judge_raw = max(0.0, min(10.0, rng.gauss(quality * 10, 0.8)))

            metrics = {
                "rhyme": rhyme_score(lyrics),
                "syllable_stability": syllable_stability_score(lyrics),
                "lexical_diversity": lexical_diversity_score(lyrics),
                "readability": readability_score(lyrics),
                "weather_accuracy": weather_accuracy_score(lyrics, weather),
                "llm_judge": max(0.0, min(1.0, judge_raw / 10.0)),
            }
            raw_entries.append(
                {
                    "model_id": model_id,
                    "model_display_name": display_name,
                    "city": city,
                    "lyrics": lyrics,
                    "cost_usd": cost,
                    "latency_s": round(rng.uniform(1.2, 6.5), 2),
                    "weather": asdict(weather),
                    "metrics": metrics,
                    "judge_comment": "Демо-оцінка (без реального виклику LLM-судді).",
                }
            )
            costs.append(cost)

    for e in raw_entries:
        e["metrics"]["price"] = price_score(e["cost_usd"], costs)
        entries.append(e)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "demo",
        "cities": list(_DEMO_WEATHER.keys()),
        "metrics_meta": METRICS_META,
        "entries": entries,
    }
