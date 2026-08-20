"""Оцінка ціни генерації -- відносна в межах одного прогону.

Ціна береться з `usage.cost` OpenRouter (справжня стягнута сума, не оцінка
по прайс-листу -- див. openrouter_client.py). Скор рахується лінійним
min-max масштабуванням: найдешевша генерація в прогоні отримує 1.0,
найдорожча -- 0.0. Це навмисно відносна метрика (не абсолютна), бо мета --
порівняти моделі між собою в конкретному прогоні, а не дати універсальну
шкалу "дорого/дешево" для будь-якого бюджету.
"""
from __future__ import annotations

from .text_utils import clamp01


def price_score(cost_usd: float, all_costs_usd: list[float]) -> float:
    if not all_costs_usd:
        return 1.0
    min_cost, max_cost = min(all_costs_usd), max(all_costs_usd)
    if max_cost == min_cost:
        return 1.0
    return clamp01(1.0 - (cost_usd - min_cost) / (max_cost - min_cost))
