import type { MetricMeta, ModelAggregate } from "../types";
import { ScoreReadout } from "./ScoreReadout";
import { SongCard } from "./SongCard";

interface LeaderboardProps {
  ranked: ModelAggregate[];
  metrics: MetricMeta[];
  expandedId: string | null;
  onToggle: (modelId: string) => void;
}

export function Leaderboard({ ranked, metrics, expandedId, onToggle }: LeaderboardProps) {
  const maxScore = Math.max(...ranked.map((r) => r.overallScore), 0.0001);

  return (
    <section className="board" aria-label="Таблиця лідерів">
      <div className="board__head">
        <span className="board__head-rank">#</span>
        <span className="board__head-award" aria-hidden="true" />
        <span className="board__head-name">Модель</span>
        <span className="board__head-score">Кількість очок</span>
      </div>
      <ol className="board__rows">
        {ranked.map((agg, i) => {
          const isOpen = expandedId === agg.model_id;
          const pct = (agg.overallScore / maxScore) * 100;
          const placeClass =
            i === 0 ? "board-row--gold" : i === 1 ? "board-row--silver" : i === 2 ? "board-row--bronze" : "";
          return (
            <li key={agg.model_id} className={`board-row ${placeClass}`}>
              <button
                type="button"
                className="board-row__main"
                onClick={() => onToggle(agg.model_id)}
                aria-expanded={isOpen}
              >
                <span className="board-row__rank">{String(i + 1).padStart(2, "0")}</span>
                {i < 3 && (
                  <span className="board-row__award" aria-hidden="true">
                    {i === 0 ? "🏆" : i === 1 ? "🥈" : "🥉"}
                  </span>
                )}
                <span className="board-row__name">{agg.model_display_name}</span>
                <span className="board-row__score">
                  <ScoreReadout value={agg.overallScore} size="lg" />
                </span>
                <span className={`board-row__chevron ${isOpen ? "board-row__chevron--open" : ""}`}>▾</span>
              </button>

              {isOpen && (
                <div className="board-row__detail">
                  <div className="board-row__metric-grid">
                    {metrics.map((m) => (
                      <div className="mini-metric" key={m.key}>
                        <span className="mini-metric__label">{m.label}</span>
                        <div className="mini-metric__bar">
                          <div
                            className="mini-metric__fill"
                            style={{ width: `${Math.round((agg.metricAverages[m.key] ?? 0) * 100)}%` }}
                          />
                        </div>
                        <span className="mini-metric__value">
                          {(agg.metricAverages[m.key] * 10).toFixed(1)}
                        </span>
                      </div>
                    ))}
                  </div>
                  <div className="board-row__songs">
                    {agg.entries.map((entry) => (
                      <SongCard key={`${entry.model_id}-${entry.city}`} entry={entry} metrics={metrics} />
                    ))}
                  </div>
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
