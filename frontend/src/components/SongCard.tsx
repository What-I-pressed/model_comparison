import type { MetricMeta, SongEntry } from "../types";
import { WeatherChip } from "./WeatherChip";

interface SongCardProps {
  entry: SongEntry;
  metrics: MetricMeta[];
}

export function SongCard({ entry, metrics }: SongCardProps) {
  return (
    <article className="song-card">
      <header className="song-card__header">
        <WeatherChip weather={entry.weather} />
        <span className="song-card__cost">${entry.cost_usd.toFixed(4)} · {entry.latency_s.toFixed(1)}с</span>
      </header>
      <pre className="song-card__lyrics">{entry.lyrics}</pre>
      <div className="song-card__metrics">
        {metrics.map((m) => (
          <div className="song-card__metric" key={m.key}>
            <span className="song-card__metric-label">{m.label}</span>
            <div className="song-card__metric-bar">
              <div
                className="song-card__metric-fill"
                style={{ width: `${Math.round((entry.metrics[m.key] ?? 0) * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
      {entry.judge_comment && <p className="song-card__comment">« {entry.judge_comment} »</p>}
    </article>
  );
}
