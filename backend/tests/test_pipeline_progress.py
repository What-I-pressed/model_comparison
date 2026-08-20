from __future__ import annotations

from datetime import datetime, timezone

from src.config import City, ModelSpec, Settings
from src.pipeline import run_pipeline
from src.weather_client import WeatherSnapshot


def test_run_pipeline_emits_progress_after_each_model(monkeypatch):
    settings = Settings(
        openrouter_api_key="test",
        judge_model="openai/gpt-4o",
        http_referer="https://github.com/weather-song-arena",
        app_title="Weather Song Arena",
        request_timeout_s=1,
        max_retries=1,
        cities=(
            City(name="Київ", latitude=50.4501, longitude=30.5234, test_set=True),
            City(name="Львів", latitude=49.8397, longitude=24.0297, test_set=True),
        ),
        models=(
            ModelSpec(id="model-a", display_name="Model A"),
            ModelSpec(id="model-b", display_name="Model B"),
        ),
    )

    weather = [
        WeatherSnapshot(
            city="Київ",
            temperature_c=3.0,
            apparent_temperature_c=-1.0,
            wind_speed_kmh=18.0,
            precipitation_mm=0.4,
            weather_code=61,
            condition_text="невеликий дощ",
        ),
        WeatherSnapshot(
            city="Львів",
            temperature_c=-4.0,
            apparent_temperature_c=-9.0,
            wind_speed_kmh=12.0,
            precipitation_mm=1.2,
            weather_code=73,
            condition_text="сніг",
        ),
    ]

    monkeypatch.setattr("src.pipeline.fetch_weather_for_cities", lambda *_args, **_kwargs: weather)

    def fake_generate_one(_client, model, city_weather):
        return (
            __import__("src.pipeline", fromlist=["SongEntry"]).SongEntry(
                model_id=model.id,
                model_display_name=model.display_name,
                city=city_weather.city,
                lyrics=f"{model.display_name} / {city_weather.city}",
                cost_usd=0.1 if model.id == "model-a" else 0.2,
                latency_s=1.0,
                weather={
                    "city": city_weather.city,
                    "temperature_c": city_weather.temperature_c,
                    "apparent_temperature_c": city_weather.apparent_temperature_c,
                    "wind_speed_kmh": city_weather.wind_speed_kmh,
                    "precipitation_mm": city_weather.precipitation_mm,
                    "weather_code": city_weather.weather_code,
                    "condition_text": city_weather.condition_text,
                },
                metrics={
                    "rhyme": 0.5,
                    "syllable_stability": 0.5,
                    "lexical_diversity": 0.5,
                    "readability": 0.5,
                    "weather_accuracy": 0.5,
                    "llm_judge": 0.5,
                },
                judge_comment="ok",
            ),
            0.1 if model.id == "model-a" else 0.2,
        )

    monkeypatch.setattr("src.pipeline._generate_one", fake_generate_one)
    monkeypatch.setattr("src.pipeline.OpenRouterClient", lambda **_kwargs: object())

    snapshots: list[dict] = []

    result = run_pipeline(settings, "test", on_progress=snapshots.append)

    assert [snap["progress"]["completed_models"] for snap in snapshots] == [1, 2]
    assert [len(snap["entries"]) for snap in snapshots] == [2, 4]
    assert result["progress"]["completed_models"] == 2
    assert result["progress"]["completed_entries"] == 4
    assert result["generated_at"]
    assert isinstance(datetime.fromisoformat(result["generated_at"]), datetime)
    assert result["generated_at"].endswith("+00:00")
