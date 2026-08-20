"""CLI: python -m src.main --mode {test|full|demo}

  test  -- реальний прогін на 2 містах (Київ, Львів) -- економний, для перевірки.
  full  -- реальний прогін на всіх 5 містах.
  demo  -- без мережі й без .env: синтетичні дані для перевірки сайту.

Результат завжди пишеться у ../frontend/src/data/results.json, звідки його
читає React-сайт.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

RESULTS_PATH = Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "data" / "results.json"


def _write_results(data: dict) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = RESULTS_PATH.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(RESULTS_PATH)


def main() -> None:
    parser = argparse.ArgumentParser(description="Weather Song Arena -- пайплайн генерації та оцінки")
    parser.add_argument("--mode", choices=["test", "full", "demo"], default="test")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.mode == "demo":
        from .demo_data import generate_demo_results

        data = generate_demo_results()
    else:
        from .config import load_settings
        from .pipeline import run_pipeline

        settings = load_settings()
        data = run_pipeline(settings, args.mode, on_progress=_write_results)

    _write_results(data)
    print(f"Записано {len(data['entries'])} записів у {RESULTS_PATH}")


if __name__ == "__main__":
    main()
