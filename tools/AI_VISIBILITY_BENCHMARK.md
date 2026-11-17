---
type: tool
date: 2026-11-17
lang: ru
related:
  - research/AI_VISIBILITY_BENCHMARK_PROTOCOL_2026-11-17.md
  - research/ai-visibility-benchmark-template.csv
  - research/AI_VISIBILITY_SCORING_RUBRIC_2026-11-17.md
  - research/AI_VISIBILITY_OBSERVATION_RECORD_SCHEMA_2026-11-17.json
---

# Локальный валидатор и агрегатор AI Visibility Benchmark

Утилита работает офлайн с CSV наблюдений. Она не обращается к ИИ-платформам, не использует API, кредиты, прокси или сетевые запросы.

## Запуск

Из корня репозитория:

    python tools/ai_visibility_benchmark.py validate research/ai-visibility-benchmark-template.csv
    python tools/ai_visibility_benchmark.py summarize research/ai-visibility-benchmark-template.csv --output reports/ai-visibility-summary.json
    python tools/ai_visibility_evidence.py validate-record path/to/observation.json
    python tools/ai_visibility_evidence.py validate-batch path/to/records/ --csv path/to/benchmark-run.csv --queue path/to/execution-queue.csv --run-id RUN-ID
    # Repeat --queue for each additional planned queue
    python -m unittest tools.tests.test_ai_visibility_benchmark tools.tests.test_ai_visibility_evidence -v

Перед запуском используйте копию CSV с фактическими наблюдениями. Каждую отвеченную строку связывайте через observation_id с полным JSON observation record; excerpt в CSV не является первичным доказательством. Пустой шаблон с одной строкой заголовков допустим и даёт ноль наблюдений.

## Что обеспечивает

- Проверяет обязательные поля, допустимые статусы, режим измерения и уникальность наблюдения.
- Для каждой отвеченной строки требует уникальный observation_id, связанный с отдельной полной записью ответа и источников.
- Отдельный валидатор проверяет полный JSON-ответ, UTC-время, статусы, оценки, источники и соответствие CSV ↔ JSON по observation_id и полным метаданным запроса/платформы/рынка.
- Финализация паспорта запуска повторно проверяет run_id, все первичные записи, точное соответствие каждой записи одной из замороженных очередей, CSV ↔ JSON и региональную аттестацию; без этих связей `FINALIZED` не создаётся.
- Опция `--queue` дополнительно требует точного совпадения каждого JSON observation с заранее запланированной ячейкой: текст запроса, query_id, intent, платформа, поверхность, режим, страна и языки. Она не переводит `UNVERIFIED` в `VERIFIED`: подтверждение региона остаётся отдельным доказательством. Для `VERIFIED` первичная запись должна содержать `market.region_attestation_id` и `market.region_attestation_sha256`, точно совпадающие с паспортом запуска.
- Принимает баллы только от 0 до 2; заблокированные, недоступные, неподдерживаемые и непрогнанные строки не могут содержать оценки или hit-флаг.
- Группирует строго по запуску, стране, локали, языку запроса, платформе, поверхности, consumer UI/API и интенту.
- Считает долю generic discovery только по строкам, где результат явно отмечен true или false.
- Не превращает блокировку, отсутствие ответа или отсутствие данных в нулевую видимость.
- Считает средние по каждой оценочной оси только по заполненным значениям отвеченных строк; критические ошибки выводит отдельно.

## Ограничения

Утилита проверяет структуру и арифметику, но не подтверждает достоверность ответов, регион, модель, цитаты или корректность ручной оценки. Эти сведения должен внести оператор по протоколу benchmark. Никаких наблюдений она сама не создаёт.
