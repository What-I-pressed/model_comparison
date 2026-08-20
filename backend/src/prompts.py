"""Шаблони промптів: генерація пісні та LLM-суддя."""
from __future__ import annotations

from .weather_client import WeatherSnapshot

SONG_SYSTEM_PROMPT = (
    "Ти — талановитий український пісняр. Твоє завдання — написати коротку, "
    "живу пісеньку про погоду в конкретному місті українською мовою. "
    "Пісня має мати щонайменше 2 куплети (по 4 рядки кожен), римований малюнок "
    "(AABB або ABAB) та стабільний складовий ритм, щоб пісню можна було заспівати. "
    "Використовуй реальні погодні дані, які тобі нададуть, і назву міста. "
    "Відповідай ЛИШЕ текстом пісні, без пояснень, приміток чи заголовків."
)

SONG_USER_TEMPLATE = (
    "Місто: {city}\n"
    "Температура: {temperature_c:.0f}°C (відчувається як {apparent_temperature_c:.0f}°C)\n"
    "Опади: {precipitation_mm:.1f} мм\n"
    "Вітер: {wind_speed_kmh:.0f} км/год\n"
    "Погодні умови: {condition_text}\n\n"
    "Напиши пісеньку про сьогоднішню погоду в цьому місті."
)


def build_song_messages(weather: WeatherSnapshot) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SONG_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": SONG_USER_TEMPLATE.format(
                city=weather.city,
                temperature_c=weather.temperature_c,
                apparent_temperature_c=weather.apparent_temperature_c,
                precipitation_mm=weather.precipitation_mm,
                wind_speed_kmh=weather.wind_speed_kmh,
                condition_text=weather.condition_text,
            ),
        },
    ]


JUDGE_SYSTEM_PROMPT = (
    "Ти — досвідчений музичний редактор та носій української мови. "
    "Оціни надану пісню про погоду за шкалою від 0 до 10 (можна дробово) "
    "за такими критеріями разом: художня якість, емоційність, оригінальність "
    "образів, доречність для конкретного міста. НЕ оцінюй риму, склади чи "
    "точність погодних даних окремо — це рахується іншим кодом.\n\n"
    'Відповідай СТРОГО у форматі JSON без жодного додаткового тексту: '
    '{{"score": <число 0-10>, "comment": "<одне коротке речення українською>"}}'
)

JUDGE_USER_TEMPLATE = "Місто: {city}\n\nТекст пісні:\n{lyrics}"


def build_judge_messages(city: str, lyrics: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": JUDGE_USER_TEMPLATE.format(city=city, lyrics=lyrics)},
    ]
