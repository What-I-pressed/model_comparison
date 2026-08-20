export type MetricKey =
  | "rhyme"
  | "syllable_stability"
  | "lexical_diversity"
  | "readability"
  | "price"
  | "weather_accuracy"
  | "llm_judge";

export interface MetricMeta {
  key: MetricKey;
  label: string;
  description: string;
}

export interface WeatherInfo {
  city: string;
  temperature_c: number;
  apparent_temperature_c: number;
  wind_speed_kmh: number;
  precipitation_mm: number;
  weather_code: number;
  condition_text: string;
}

export interface SongEntry {
  model_id: string;
  model_display_name: string;
  city: string;
  lyrics: string;
  cost_usd: number;
  latency_s: number;
  weather: WeatherInfo;
  metrics: Record<MetricKey, number>;
  judge_comment: string;
}

export interface ResultsData {
  generated_at: string;
  mode: "test" | "full" | "demo";
  cities: string[];
  metrics_meta: MetricMeta[];
  entries: SongEntry[];
}

export interface ModelAggregate {
  model_id: string;
  model_display_name: string;
  overallScore: number; // 0..1, зважений
  metricAverages: Record<MetricKey, number>; // 0..1, середнє по містах
  totalCostUsd: number;
  entries: SongEntry[];
}

export type WeightMap = Record<MetricKey, number>;
