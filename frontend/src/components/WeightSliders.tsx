import type { MetricKey, MetricMeta, WeightMap } from "../types";
import { DEFAULT_WEIGHTS } from "../lib/scoring";

interface WeightSlidersProps {
  metrics: MetricMeta[];
  weights: WeightMap;
  onChange: (key: MetricKey, value: number) => void;
  onReset: () => void;
}

export function WeightSliders({ metrics, weights, onChange, onReset }: WeightSlidersProps) {
  return (
    <section className="control-panel" aria-label="Ваги метрик">
      <div className="control-panel__header">
        <div>
          <h2 className="control-panel__title">Панель ваг</h2>
          <p className="control-panel__hint">Тут можна налаштувати, які характеристики для тебе найважливіші.</p>
        </div>
        <button type="button" className="control-panel__reset" onClick={onReset}>
          Скинути до рівних ваг
        </button>
      </div>
      <div className="control-panel__grid">
        {metrics.map((m) => (
          <div className="weight-row" key={m.key}>
            <div className="weight-row__label-line">
              <label htmlFor={`weight-${m.key}`} className="weight-row__label">
                {m.label}
              </label>
              <span className="weight-row__value">{weights[m.key] ?? DEFAULT_WEIGHTS[m.key]}</span>
            </div>
            <input
              id={`weight-${m.key}`}
              type="range"
              min={0}
              max={5}
              step={1}
              value={weights[m.key] ?? DEFAULT_WEIGHTS[m.key]}
              onChange={(e) => onChange(m.key, Number(e.target.value))}
              className="weight-row__slider"
            />
            <p className="weight-row__desc">{m.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
