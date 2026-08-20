"""Оцінка LLM-суддею -- єдина метрика, що потребує мережевого виклику.

Суддя оцінює художню якість/емоційність/доречність (0-10), ми нормалізуємо
до [0, 1]. Це навмисно окремий, ізольований виклик з власним промптом
(prompts.build_judge_messages), щоб не змішувати суб'єктивну LLM-оцінку з
об'єктивними, порахованими кодом метриками (рима/склади/лексика/читабельність).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from ..openrouter_client import OpenRouterClient
from ..prompts import build_judge_messages
from .text_utils import clamp01

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JudgeVerdict:
    score: float
    raw_score: float
    comment: str


def _normalize_judge_json(text: str) -> str:
    cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    # Деякі моделі люблять обгортати відповідь ще однією парою фігурних дужок.
    # Пробуємо кілька безпечних кандидатів, не втрачаючи оригінал для логу.
    candidates = [cleaned]
    if cleaned.startswith("{{") and cleaned.endswith("}}"):
        candidates.append(cleaned[1:-1].strip())

    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first != -1 and last != -1 and last > first:
        candidate = cleaned[first : last + 1].strip()
        if candidate not in candidates:
            candidates.append(candidate)
        if candidate.startswith("{{") and candidate.endswith("}}"):
            inner = candidate[1:-1].strip()
            if inner not in candidates:
                candidates.append(inner)

    for candidate in candidates:
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            continue

    return cleaned


def parse_judge_response(text: str) -> tuple[float, str]:
    parsed = json.loads(_normalize_judge_json(text))
    raw_score = float(parsed["score"])
    comment = str(parsed.get("comment", "")).strip()
    return raw_score, comment


def llm_judge_score(
    client: OpenRouterClient,
    judge_model: str,
    city: str,
    lyrics: str,
) -> JudgeVerdict:
    messages = build_judge_messages(city, lyrics)
    result = client.complete(judge_model, messages, temperature=0.2, max_tokens=200)

    try:
        raw_score, comment = parse_judge_response(result.text)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.warning("Не вдалося розпарсити відповідь судді (%s): %r", exc, result.text)
        raw_score = 0.0
        comment = "Не вдалося розпарсити відповідь судді."

    return JudgeVerdict(score=clamp01(raw_score / 10.0), raw_score=raw_score, comment=comment)
