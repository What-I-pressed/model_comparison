import type { WeatherInfo } from "../types";

export function WeatherChip({ weather }: { weather: WeatherInfo }) {
  return (
    <div className="weather-chip">
      <span className="weather-chip__city">{weather.city}</span>
      <span className="weather-chip__temp">{Math.round(weather.temperature_c)}°C</span>
      <span className="weather-chip__cond">{weather.condition_text}</span>
    </div>
  );
}
