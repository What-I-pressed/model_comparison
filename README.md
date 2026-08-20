# Weather Song Arena 🎵🌦️

Порівняння всіх text-моделей OpenRouter у написанні пісень про погоду
українських міст. Python-пайплайн бере реальну погоду з Open-Meteo,
генерує пісні, рахує 7 метрик якості й пише `results.json`; React+TypeScript
сайт на GitHub Pages показує лідерборд із повзунками ваг метрик.

## Структура проєкту

```
weather-song-arena/
├── backend/
│   ├── src/
│   │   ├── config.py            # налаштування, .env, cities/models_config.yaml
│   │   ├── cities_config.yaml   # 5 міст (2 позначені test_set: true)
│   │   ├── models_config.yaml   # fallback-список моделей OpenRouter
│   │   ├── openrouter_client.py # клієнт OpenRouter з usage accounting
│   │   ├── weather_client.py    # клієнт Open-Meteo
│   │   ├── prompts.py           # промпти генерації пісні та LLM-судді
│   │   ├── pipeline.py          # оркестрація повного прогону
│   │   ├── demo_data.py         # синтетичні дані без мережі (для тестування сайту)
│   │   ├── main.py              # CLI: python -m src.main --mode {test|full|demo}
│   │   └── metrics/             # 6 метрик кодом + 1 через LLM-суддю
│   └── tests/                   # юніт-тести метрик, без мережі
└── frontend/                    # React + TypeScript + Vite сайт
    └── src/data/results.json    # результати прогону -- читає сайт
```

## Сім метрик оцінки

| Метрика | Як рахується |
|---|---|
| Рима | Порівняння закінчень рядків (AABB/ABAB), код |
| Стабільність ритму | Коефіцієнт варіації складів у рядках куплету, код |
| Лексичне розмаїття | MATTR (ковзний type-token ratio), код |
| Читабельність | Евристика на довжині слів/рядків, код |
| Ціна генерації | Відносна вартість (`usage.cost` з OpenRouter), код |
| Влучність у погоду | Збіг згаданих явищ/температури з реальними даними Open-Meteo, код |
| Оцінка LLM-суддею | Один виклик до `openai/gpt-4o` з окремим промптом-суддею |

Усі метрики нормалізовані до `0..1`, на сайті кожна має свій повзунок ваги
(0–5), загальний скор — зважене середнє.

## Запуск бекенду

```bash
cd backend
pip install -r requirements.txt --break-system-packages   # або у venv без флагу

# без мережі й без .env -- одразу перевірити сайт на синтетичних даних
python -m src.main --mode demo

# реальний прогін (потрібен .env з OPENROUTER_API_KEY, див. .env.example)
python -m src.main --mode test    # економно: 2 міста
python -m src.main --mode full    # усі 5 міст
```

У режимі `test` прогін іде лише по 2 містах для економії.
Кожен режим перезаписує `frontend/src/data/results.json`.

Юніт-тести метрик (без мережі, без .env):

```bash
cd backend && python -m pytest tests/ -v
```

## Запуск сайту локально

```bash
cd frontend
npm install
npm run dev
```

## Деплой на GitHub Pages

1. Заповни `results.json` реальним прогоном (`--mode full`) і закомить його.
2. Переконайся, що `frontend/vite.config.ts` → `base` відповідає назві
   твого репозиторію (`/назва-репо/`), або `/` для репозиторію-профілю
   (`username.github.io`).
3. У налаштуваннях репозиторію: **Settings → Pages → Source → GitHub
   Actions**.
4. Запуш у `main` — `.github/workflows/deploy.yml` збере
   `frontend` і задеплоїть автоматично.

## Поточний стан

Зараз у `results.json` лежать **демо-дані** (`mode: "demo"`), згенеровані
локально без жодного мережевого виклику. Реальні тексти пісень і ціни
з'являться після того, як ти запустиш `python -m src.main --mode test`
або `full` зі своїм `OPENROUTER_API_KEY` у `.env`.

### Як вибираються моделі

За замовчуванням пайплайн автоматично тягне **всі text-моделі OpenRouter**
через офіційний каталог `/api/v1/models?output_modalities=text`.
Якщо каталог тимчасово недоступний, `backend/src/models_config.yaml`
використовується як fallback.
