"""Клієнт до Open-Meteo -- безкоштовного погодного API без реєстрації/ключа.

Документація: https://open-meteo.com/en/docs
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from .config import City

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Спрощена мапа WMO weather codes -> людський опис українською.
# https://open-meteo.com/en/docs#weathervariables
_WMO_DESCRIPTIONS: dict[int, str] = {
    0: "ясно",
    1: "переважно ясно",
    2: "мінлива хмарність",
    3: "хмарно",
    45: "туман",
    48: "паморозевий туман",
    51: "легка мряка",
    53: "мряка",
    55: "сильна мряка",
    61: "невеликий дощ",
    63: "дощ",
    65: "сильний дощ",
    71: "невеликий сніг",
    73: "сніг",
    75: "сильний снігопад",
    77: "снігова крупа",
    80: "короткочасний дощ",
    81: "дощові зливи",
    82: "сильні зливи",
    85: "снігові заряди",
    86: "сильні снігові заряди",
    95: "гроза",
    96: "гроза з градом",
    99: "сильна гроза з градом",
}


@dataclass(frozen=True)
class WeatherSnapshot:
    city: str
    temperature_c: float
    apparent_temperature_c: float
    wind_speed_kmh: float
    precipitation_mm: float
    weather_code: int
    condition_text: str

    def is_rainy_or_snowy(self) -> bool:
        return self.weather_code >= 51

    def is_windy(self, threshold_kmh: float = 25.0) -> bool:
        return self.wind_speed_kmh >= threshold_kmh

    def is_clear(self) -> bool:
        return self.weather_code <= 1


def fetch_weather(city: City, *, timeout_s: int = 30) -> WeatherSnapshot:
    """Забирає поточну погоду для міста з Open-Meteo.

    Кидає requests.HTTPError, якщо API повернуло помилку.
    """
    params = {
        "latitude": city.latitude,
        "longitude": city.longitude,
        "current": ",".join(
            [
                "temperature_2m",
                "apparent_temperature",
                "wind_speed_10m",
                "precipitation",
                "weather_code",
            ]
        ),
        "timezone": "auto",
    }
    logger.info("Запитую погоду для %s", city.name)
    response = requests.get(OPEN_METEO_URL, params=params, timeout=timeout_s)
    response.raise_for_status()
    data = response.json()["current"]
    code = int(data["weather_code"])
    return WeatherSnapshot(
        city=city.name,
        temperature_c=float(data["temperature_2m"]),
        apparent_temperature_c=float(data["apparent_temperature"]),
        wind_speed_kmh=float(data["wind_speed_10m"]),
        precipitation_mm=float(data["precipitation"]),
        weather_code=code,
        condition_text=_WMO_DESCRIPTIONS.get(code, "невизначені умови"),
    )


def fetch_weather_for_cities(cities: tuple[City, ...], *, timeout_s: int = 30) -> list[WeatherSnapshot]:
    return [fetch_weather(c, timeout_s=timeout_s) for c in cities]
