"""Тонкий клієнт до OpenRouter (/v1/chat/completions).

Використовує "usage accounting" OpenRouter (поле `usage.include=True` у запиті),
яке повертає реальну вартість генерації в доларах у полі `usage.cost` відповіді --
це точніше, ніж рахувати вартість самостійно по прайс-листу, бо OpenRouter
враховує саме те, що реально стягнув з рахунку.

Документація: https://openrouter.ai/docs
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import requests

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


class OpenRouterError(RuntimeError):
    """Помилка виклику OpenRouter API після вичерпання спроб."""


@dataclass(frozen=True)
class CompletionResult:
    model_id: str
    text: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    latency_s: float
    raw_finish_reason: str | None


@dataclass(frozen=True)
class ModelCatalogItem:
    id: str
    display_name: str


class OpenRouterClient:
    def __init__(
        self,
        api_key: str,
        *,
        http_referer: str = "https://github.com/weather-song-arena",
        app_title: str = "Weather Song Arena",
        timeout_s: int = 60,
        max_retries: int = 3,
    ) -> None:
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": http_referer,
            "X-Title": app_title,
        }
        self._timeout_s = timeout_s
        self._max_retries = max_retries

    def complete(
        self,
        model_id: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.9,
        max_tokens: int = 700,
    ) -> CompletionResult:
        """Виконує один chat-completion запит із retry + backoff на transient-помилках."""
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "usage": {"include": True},
        }

        last_error: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            start = time.monotonic()
            try:
                response = requests.post(
                    OPENROUTER_URL,
                    headers=self._headers,
                    json=payload,
                    timeout=self._timeout_s,
                )
                latency_s = time.monotonic() - start

                if response.status_code == 429 or response.status_code >= 500:
                    # rate limit / серверна помилка -> варто повторити
                    wait_s = min(2 ** attempt, 20)
                    logger.warning(
                        "OpenRouter %s повернув %s, спроба %s/%s, чекаю %.1fs",
                        model_id,
                        response.status_code,
                        attempt,
                        self._max_retries,
                        wait_s,
                    )
                    time.sleep(wait_s)
                    continue

                response.raise_for_status()
                data = response.json()

                choice = data["choices"][0]
                usage = data.get("usage", {})
                message = choice.get("message") or {}
                content = message.get("content")
                if not isinstance(content, str) or not content.strip():
                    raise OpenRouterError(
                        f"Модель {model_id} повернула порожній або не-текстовий контент "
                        f"(finish_reason={choice.get('finish_reason')!r})"
                    )

                return CompletionResult(
                    model_id=model_id,
                    text=content.strip(),
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    cost_usd=float(usage.get("cost", 0.0)),
                    latency_s=latency_s,
                    raw_finish_reason=choice.get("finish_reason"),
                )
            except (requests.RequestException, KeyError, IndexError) as exc:
                last_error = exc
                logger.warning(
                    "Помилка запиту до %s (спроба %s/%s): %s",
                    model_id,
                    attempt,
                    self._max_retries,
                    exc,
                )
                time.sleep(min(2 ** attempt, 20))

        raise OpenRouterError(
            f"Не вдалося отримати відповідь від моделі {model_id} після {self._max_retries} спроб"
        ) from last_error

    def list_models(self) -> list[dict]:
        """Повертає каталог доступних моделей з актуальними цінами.

        Корисно звірити перед повним прогоном, щоб id моделей у models_config.yaml
        були актуальними (OpenRouter періодично додає/прибирає моделі).
        """
        response = requests.get(OPENROUTER_MODELS_URL, headers=self._headers, timeout=self._timeout_s)
        response.raise_for_status()
        return response.json().get("data", [])

    def list_text_models(
        self,
        *,
        sort: str = "pricing-low-to-high",
        q: str | None = None,
        context: int | None = None,
        model_authors: str | None = None,
        providers: str | None = None,
        supported_parameters: str | None = None,
    ) -> list[ModelCatalogItem]:
        """Повертає всі текстові моделі OpenRouter.

        Це головний шлях для автоматичного прогону: беремо живий каталог
        OpenRouter, фільтруємо лише text output, і більше не тримаємо ручний
        список моделей як джерело істини.
        """
        params: dict[str, Any] = {"output_modalities": "text", "sort": sort}
        if q:
            params["q"] = q
        if context is not None:
            params["context"] = context
        if model_authors:
            params["model_authors"] = model_authors
        if providers:
            params["providers"] = providers
        if supported_parameters:
            params["supported_parameters"] = supported_parameters

        response = requests.get(
            OPENROUTER_MODELS_URL,
            headers=self._headers,
            params=params,
            timeout=self._timeout_s,
        )
        response.raise_for_status()
        raw_models = response.json().get("data", [])

        items: list[ModelCatalogItem] = []
        seen: set[str] = set()
        for raw in raw_models:
            if not isinstance(raw, dict):
                continue
            model_id = str(raw.get("id", "")).strip()
            if not model_id or model_id in seen:
                continue
            if not _is_text_to_text_model(raw):
                continue
            seen.add(model_id)
            display_name = str(raw.get("name") or model_id).strip()
            items.append(ModelCatalogItem(id=model_id, display_name=display_name))
        return items


def _is_text_to_text_model(raw: dict[str, Any]) -> bool:
    architecture = raw.get("architecture")
    if not isinstance(architecture, dict):
        return False

    modality = str(architecture.get("modality", "")).strip().lower()
    if modality != "text->text":
        return False

    input_modalities = architecture.get("input_modalities")
    output_modalities = architecture.get("output_modalities")

    if isinstance(input_modalities, list):
        if "text" not in {str(item).strip().lower() for item in input_modalities}:
            return False

    if isinstance(output_modalities, list):
        if "text" not in {str(item).strip().lower() for item in output_modalities}:
            return False

    return True
