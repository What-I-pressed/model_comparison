import type { MetricKey, ModelAggregate, ResultsData, WeightMap } from "../types";

// Шкала повзунків 0..5, стартове положення -- посередині (3), щоб можна
// було легко підняти або опустити важливість метрики в обидва боки.
export const DEFAULT_WEIGHTS: WeightMap = {
  rhyme: 3,
  syllable_stability: 3,
  lexical_diversity: 3,
  readability: 3,
  price: 3,
  weather_accuracy: 3,
  llm_judge: 3,
};

/** Групує записи по моделі й усереднює кожну метрику по містах (0..1). */
export function aggregateByModel(data: ResultsData): ModelAggregate[] {
  const byModel = new Map<string, ModelAggregate>();

  for (const entry of data.entries) {
    let agg = byModel.get(entry.model_id);
    if (!agg) {
      agg = {
        model_id: entry.model_id,
        model_display_name: entry.model_display_name,
        overallScore: 0,
        metricAverages: {} as Record<MetricKey, number>,
        totalCostUsd: 0,
        entries: [],
      };
      byModel.set(entry.model_id, agg);
    }
    agg.entries.push(entry);
    agg.totalCostUsd += entry.cost_usd;
  }

  for (const agg of byModel.values()) {
    const sums: Partial<Record<MetricKey, number>> = {};
    for (const meta of data.metrics_meta) {
      sums[meta.key] = 0;
    }
    for (const entry of agg.entries) {
      for (const meta of data.metrics_meta) {
        sums[meta.key]! += entry.metrics[meta.key] ?? 0;
      }
    }
    for (const meta of data.metrics_meta) {
      agg.metricAverages[meta.key] = sums[meta.key]! / agg.entries.length;
    }
  }

  return Array.from(byModel.values());
}

/** Рахує зважений загальний скор (0..1) для моделі за поточними вагами повзунків. */
export function weightedScore(
  metricAverages: Record<MetricKey, number>,
  weights: WeightMap,
  metricKeys: MetricKey[],
): number {
  let weightSum = 0;
  let scoreSum = 0;
  for (const key of metricKeys) {
    const w = weights[key] ?? 0;
    weightSum += w;
    scoreSum += w * (metricAverages[key] ?? 0);
  }
  if (weightSum === 0) return 0;
  return scoreSum / weightSum;
}

export function rankModels(
  aggregates: ModelAggregate[],
  weights: WeightMap,
  metricKeys: MetricKey[],
): ModelAggregate[] {
  const withScores = aggregates.map((agg) => ({
    ...agg,
    overallScore: weightedScore(agg.metricAverages, weights, metricKeys),
  }));
  return withScores.sort((a, b) => b.overallScore - a.overallScore);
}
