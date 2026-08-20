import { useMemo, useState } from "react";
import rawResults from "./data/results.json";
import type { MetricKey, ResultsData, WeightMap } from "./types";
import { DEFAULT_WEIGHTS, aggregateByModel, rankModels } from "./lib/scoring";
import { WeightSliders } from "./components/WeightSliders";
import { Leaderboard } from "./components/Leaderboard";
import { WeatherChip } from "./components/WeatherChip";

const data = rawResults as ResultsData;

const MODE_LABEL: Record<ResultsData["mode"], string> = {
  demo: "ДЕМО-ДАНІ",
  test: "ТЕСТОВИЙ ПРОГІН (2 міста)",
  full: "ПОВНИЙ ПРОГІН",
};

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString("uk-UA", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

export default function App() {
  const [weights, setWeights] = useState<WeightMap>(DEFAULT_WEIGHTS);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const metricKeys = useMemo(() => data.metrics_meta.map((m) => m.key), []);
  const aggregates = useMemo(() => aggregateByModel(data), []);
  const ranked = useMemo(() => rankModels(aggregates, weights, metricKeys), [aggregates, weights, metricKeys]);

  const cityWeatherChips = useMemo(() => {
    const seen = new Map<string, (typeof data.entries)[number]>();
    for (const entry of data.entries) {
      if (!seen.has(entry.city)) seen.set(entry.city, entry);
    }
    return Array.from(seen.values());
  }, []);

  const handleWeightChange = (key: MetricKey, value: number) => {
    setWeights((prev) => ({ ...prev, [key]: value }));
  };

  const handleReset = () => setWeights(DEFAULT_WEIGHTS);

  const handleToggle = (modelId: string) => {
    setExpandedId((prev) => (prev === modelId ? null : modelId));
  };

  return (
    <div className="page">
      <header className="hero">
        <div className="hero__badge-row">
          {/* <span className="hero__badge">{MODE_LABEL[data.mode]}</span> */}
          <span className="hero__timestamp">оновлено {formatTimestamp(data.generated_at)}</span>
        </div>
        <h1 className="hero__title">
          Арена
          <br />
          погодних пісень
        </h1>
        <p className="hero__subtitle">
          {data.entries.length ? new Set(data.entries.map((e) => e.model_id)).size : 0} мовних моделей пишуть
          пісні про погоду українських міст за реальними даними Open-Meteo. Ви можете налаштувати найважливіші метрики саме для Вас у сппеціальній панелі ваг та вибрати те, що підходить саме Вам.
        </p>
        <div className="hero__chips">
          {cityWeatherChips.map((e) => (
            <WeatherChip key={e.city} weather={e.weather} />
          ))}
        </div>
      </header>

      <main className="layout">
        <WeightSliders
          metrics={data.metrics_meta}
          weights={weights}
          onChange={handleWeightChange}
          onReset={handleReset}
        />
        <Leaderboard ranked={ranked} metrics={data.metrics_meta} expandedId={expandedId} onToggle={handleToggle} />
      </main>

      <footer className="footer">
        <p>
          Weather Song Arena · тексти генеруються моделями через OpenRouter, погода — з Open-Meteo, оцінка —
          локальні метрики (рима, ритм, лексика, читабельність, влучність у погоду) + один виклик LLM-судді.
        </p>
      </footer>
    </div>
  );
}
