"""Централізована конфігурація пайплайну.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback for minimal local environments
    def load_dotenv(*_args, **_kwargs) -> bool:  # type: ignore[override]
        return False

from .openrouter_client import OpenRouterClient

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class City:
    name: str
    latitude: float
    longitude: float
    test_set: bool = False


@dataclass(frozen=True)
class ModelSpec:
    id: str
    display_name: str


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str
    judge_model: str
    http_referer: str
    app_title: str
    request_timeout_s: int
    max_retries: int
    cities: tuple[City, ...] = field(default_factory=tuple)
    models: tuple[ModelSpec, ...] = field(default_factory=tuple)

    def cities_for_mode(self, mode: str) -> tuple[City, ...]:
        if mode == "test":
            return tuple(c for c in self.cities if c.test_set)
        if mode == "full":
            return self.cities
        raise ValueError(f"Невідомий режим: {mode!r}, очікується 'test' або 'full'")


def _load_cities(path: Path) -> tuple[City, ...]:
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or []
    return tuple(City(**item) for item in raw)


def _load_models(path: Path) -> tuple[ModelSpec, ...]:
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or []
    return tuple(ModelSpec(**item) for item in raw)


def _discover_models_from_openrouter(
    *,
    api_key: str,
    http_referer: str,
    app_title: str,
    request_timeout_s: int,
    max_retries: int,
) -> tuple[ModelSpec, ...]:
    client = OpenRouterClient(
        api_key=api_key,
        http_referer=http_referer,
        app_title=app_title,
        timeout_s=request_timeout_s,
        max_retries=max_retries,
    )
    raw_models = client.list_text_models()
    models = tuple(ModelSpec(id=item.id, display_name=item.display_name) for item in raw_models)
    logger.info("Підвантажено %d текстових моделей OpenRouter", len(models))
    return models


def load_settings() -> Settings:
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY не знайдено. Створи файл .env у корені проєкту "
            "(дивись .env.example) і встав туди свій ключ з https://openrouter.ai/keys"
        )
    judge_model = os.getenv("JUDGE_MODEL", "openai/gpt-4o")
    http_referer = os.getenv("HTTP_REFERER", "https://github.com/weather-song-arena")
    app_title = os.getenv("APP_TITLE", "Weather Song Arena")
    request_timeout_s = int(os.getenv("REQUEST_TIMEOUT_S", "60"))
    max_retries = int(os.getenv("MAX_RETRIES", "3"))

    try:
        models = _discover_models_from_openrouter(
            api_key=api_key,
            http_referer=http_referer,
            app_title=app_title,
            request_timeout_s=request_timeout_s,
            max_retries=max_retries,
        )
    except Exception as exc:
        logger.warning(
            "Не вдалося автоматично підтягнути каталог OpenRouter (%s); "
            "використовую локальний models_config.yaml",
            exc,
        )
        models = _load_models(BASE_DIR / "models_config.yaml")

    return Settings(
        openrouter_api_key=api_key,
        judge_model=judge_model,
        http_referer=http_referer,
        app_title=app_title,
        request_timeout_s=request_timeout_s,
        max_retries=max_retries,
        cities=_load_cities(BASE_DIR / "cities_config.yaml"),
        models=models,
    )
