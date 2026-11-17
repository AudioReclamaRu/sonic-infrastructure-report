---
type: tool
date: 2026-11-18
lang: ru
related:
  - research/AI_VISIBILITY_BENCHMARK_PROTOCOL_2026-11-17.md
  - research/ai-visibility-ru-generic-discovery-queries-2026-11-17.json
  - research/ai-visibility-ru-brand-service-queries-2026-11-18.json
  - research/ai-visibility-benchmark-queries-2026-11-17.json
  - tools/AI_VISIBILITY_BENCHMARK.md
---

# AI Visibility Queue Planner

Планировщик превращает отдельный frozen query-module в явную, проверяемую матрицу запуска. Это офлайн-инструмент подготовки: он не обращается к провайдерам, не подтверждает регион и не создаёт наблюдения.

## Подготовить очереди

```bash
python tools/ai_visibility_queue.py generate \
  --module research/ai-visibility-ru-generic-discovery-queries-2026-11-17.json \
  --output research/queues/ru-generic-discovery-queue.csv

python tools/ai_visibility_queue.py generate \
  --module research/ai-visibility-ru-brand-service-queries-2026-11-18.json \
  --output research/queues/ru-brand-service-queue.csv
```

Для текущей первой российской волны ожидается:

- Generic discovery: 29 небрендированных запросов × 12 поверхностей = 348 плановых строк.
- Brand/service verification: 20 брендовых и сервисных запросов × 12 поверхностей = 240 плановых строк.

Второй источник — отдельный исполнимый query-module, построенный из фиксированного benchmark-набора. Нельзя передавать непосредственно файл ai-visibility-benchmark-queries-2026-11-17.json: этот evaluator-файл не содержит обязательных для планировщика полей market и platform_execution_order. Это сохраняет различие между контрольными ответами benchmark и исполнимым определением эксперимента.

## Проверить покрытие

```bash
python tools/ai_visibility_queue.py validate \
  --queue research/queues/ru-generic-discovery-queue.csv \
  --module research/ai-visibility-ru-generic-discovery-queries-2026-11-17.json

python tools/ai_visibility_queue.py validate \
  --queue research/queues/ru-brand-service-queue.csv \
  --module research/ai-visibility-ru-brand-service-queries-2026-11-18.json
```

Проверяются обязательные поля, дубли ID и пар query/platform, допустимые режимы измерения, целостность планового статуса и полное декартово покрытие исходного модуля.

## Безопасность и интерпретация

- Каждая сгенерированная строка начинается с NOT_TESTED; региональная проверка — UNVERIFIED.
- Текущая геолокация пользователя, номинальный список стран провайдера или прокси не доказывают регион реального запуска.
- consumer_ui, model_api и search_results_ui остаются отдельными режимами. В конкретном модуле присутствуют только реально перечисленные поверхности; отсутствие режима не дополняется догадкой.
- Generic discovery проверяется на случайные брендовые подсказки, когда в модуле явно задано brand_in_prompt=false.
- CSV очереди не являются benchmark CSV наблюдений. Не передавать их в ai_visibility_benchmark.py; только фактически полученные ответы с привязанными доказательствами становятся наблюдениями.
- После начала измерений нельзя переписывать frozen query-module: изменения оформляются новой версией.
- Не используются сеть, AI API, платный трекер, кредиты Firecrawl; сайт не читается и не изменяется этим инструментом.

## Тесты

```bash
python -m unittest tools.tests.test_ai_visibility_queue tools.tests.test_ai_visibility_ru_brand_service_queue -v
```
