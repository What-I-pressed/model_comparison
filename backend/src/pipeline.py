"""Оркестрація повного прогону: погода -> генерація пісень -> метрики -> results.json.

Для кожної пари (модель, місто):
  1. беремо вже завантажену погоду міста,
  2. просимо модель написати пісню (prompts.build_song_messages),
  3. рахуємо 6 об'єктивних метрик кодом (без мережі),
  4. рахуємо 7-му метрику -- окремим викликом до LLM-судді.

Ціна (`price`) рахується відносно ПІСЛЯ того, як зібрані всі результати
одного прогону, бо це відносна метрика (найдешевша генерація = 1.0).
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Callable

from .config import ModelSpec, Settings
from .metrics import (
    lexical_diversity_score,
    price_score,
    readability_score,
    rhyme_score,
    syllable_stability_score,
    weather_accuracy_score,
)
from .metrics.llm_judge import llm_judge_score
from .openrouter_client import OpenRouterClient
from .prompts import build_song_messages
from .weather_client import WeatherSnapshot, fetch_weather_for_cities

logger = logging.getLogger(__name__)

METRICS_META = [
    {"key": "rhyme", "label": "Рима", "description": "Наскільки добре римуються рядки в куплетах."},
    {
        "key": "syllable_stability",
        "label": "Стабільність ритму",
        "description": "Наскільки однакова кількість складів у відповідних рядках куплету.",
    },
    {
        "key": "lexical_diversity",
        "label": "Лексичне розмаїття",
        "description": "Різноманітність словника (MATTR), а не повтори одних і тих самих слів.",
    },
    {"key": "readability", "label": "Читабельність", "description": "Наскільки легко читати/співати текст."},
    {"key": "price", "label": "Ціна генерації", "description": "Відносна вартість генерації в межах прогону"},
    {
        "key": "weather_accuracy",
        "label": "Влучність у погоду",
        "description": "Чи відповідає зміст пісні реальним погодним даним міста.",
    },
    {"key": "llm_judge", "label": "Оцінка LLM-суддею", "description": "Художня якість очима LLM-судді (0-10 -> 0-1)."},
]


@dataclass
class SongEntry:
    model_id: str
    model_display_name: str
    city: str
    lyrics: str
    cost_usd: float
    latency_s: float
    weather: dict
    metrics: dict
    judge_comment: str


ResultSnapshot = dict
SnapshotWriter = Callable[[ResultSnapshot], None]


def _generate_one(
    client: OpenRouterClient,
    model: ModelSpec,
    weather: WeatherSnapshot,
) -> tuple[SongEntry, float]:
    """Генерує пісню й рахує всі метрики, крім (відносної) ціни.

    Повертає запис і "сирий" cost_usd окремо, щоб pipeline міг після збору
    всіх результатів порахувати відносний price_score по всьому прогону.
    """
    messages = build_song_messages(weather)
    result = client.complete(model.id, messages)
    lyrics = result.text

    verdict = llm_judge_score(client, judge_model="openai/gpt-4o", city=weather.city, lyrics=lyrics)

    metrics = {
        "rhyme": rhyme_score(lyrics),
        "syllable_stability": syllable_stability_score(lyrics),
        "lexical_diversity": lexical_diversity_score(lyrics),
        "readability": readability_score(lyrics),
        "weather_accuracy": weather_accuracy_score(lyrics, weather),
        "llm_judge": verdict.score,
        # price додається пізніше, коли відомі всі ціни прогону
    }

    entry = SongEntry(
        model_id=model.id,
        model_display_name=model.display_name,
        city=weather.city,
        lyrics=lyrics,
        cost_usd=result.cost_usd,
        latency_s=result.latency_s,
        weather=asdict(weather),
        metrics=metrics,
        judge_comment=verdict.comment,
    )
    return entry, result.cost_usd


def _build_results_payload(
    *,
    mode: str,
    cities: list[str],
    entries: list[SongEntry],
    costs: list[float],
    completed_models: int,
    total_models: int,
) -> dict:
    for entry in entries:
        entry.metrics["price"] = price_score(entry.cost_usd, costs)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "cities": cities,
        "metrics_meta": METRICS_META,
        "progress": {
            "completed_models": completed_models,
            "total_models": total_models,
            "completed_entries": len(entries),
            "total_entries": total_models * len(cities),
        },
        "entries": [asdict(e) for e in entries],
    }


def run_pipeline(settings: Settings, mode: str, *, on_progress: SnapshotWriter | None = None) -> dict:
    """Виконує повний прогін і повертає структуру, готову для запису в results.json."""
    client = OpenRouterClient(
        api_key=settings.openrouter_api_key,
        http_referer=settings.http_referer,
        app_title=settings.app_title,
        timeout_s=settings.request_timeout_s,
        max_retries=settings.max_retries,
    )

    cities = settings.cities_for_mode(mode)
    if not cities:
        raise RuntimeError(f"Жодного міста не знайдено для режиму {mode!r}")

    logger.info("Запитую погоду для %d міст...", len(cities))
    weather_by_city = {w.city: w for w in fetch_weather_for_cities(cities, timeout_s=settings.request_timeout_s)}

    entries: list[SongEntry] = []
    costs: list[float] = []

    total_models = len(settings.models)
    total = total_models * len(cities)
    done = 0
    completed_models = 0
    for model in settings.models:
        for city in cities:
            weather = weather_by_city[city.name]
            logger.info("[%d/%d] %s x %s", done + 1, total, model.display_name, city.name)
            try:
                entry, cost = _generate_one(client, model, weather)
            except Exception:
                logger.exception("Пропускаю %s x %s через помилку", model.display_name, city.name)
                done += 1
                continue
            entries.append(entry)
            costs.append(cost)
            done += 1

        completed_models += 1
        snapshot = _build_results_payload(
            mode=mode,
            cities=[c.name for c in cities],
            entries=entries,
            costs=costs,
            completed_models=completed_models,
            total_models=total_models,
        )
        if on_progress is not None:
            on_progress(snapshot)

    return _build_results_payload(
        mode=mode,
        cities=[c.name for c in cities],
        entries=entries,
        costs=costs,
        completed_models=completed_models,
        total_models=total_models,
    )
