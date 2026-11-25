---
type: benchmark_plan
date: 2026-11-22
lang: ru
status: protocol_only_not_run
related:
  - research/AI_VISIBILITY_BENCHMARK_PROTOCOL_2026-11-17.md
  - research/AI_VISIBILITY_AUDIO_PLUS_B2C_PROMPT_MODULE_DRAFT_2026-11-22.md
# AI_VISIBILITY_BENCHMARK_PLAN_2026-11-22

Подготовлено: ZCode, независимый read-only спринт. Статус измерений: **все платформы NOT_RUN из среды аудита** — принципиально: замеры требуют настоящих consumer-UI сессий (по возможности из РФ для Яндекс Алисы/GigaChat), которых у данной среды нет. ТЗ запрещает симуляцию — этот документ фиксирует протокол, а не результаты.

## 1. Заморозка запросных наборов — VERIFIED / FROZEN

Оба исходных набора найдены и проверены непосредственно в `main` и в ветке этого PR (содержимое совпадает, Git blob SHA-1 одинаков):

| Набор | Назначение | Промпты | SHA-256 UTF-8 файла | Git blob SHA-1 |
|---|---|---:|---|---|
| `research/ai-visibility-ru-generic-discovery-queries-2026-11-17.json` | Нейтральный RU discovery baseline | 29 | `37a19e2bc698163a95cf78677b9ed12975476f74dac3153c4b94a7791f5b59ba` | `79f3cf13a2a3426a0d0d9e3d0e9260cd178e4179` |
| `research/ai-visibility-ru-commercial-price-extension-2026-11-20.json` | Отдельное ценовое расширение, не смешивать с основным baseline | 3 | `d58aac31cf472c31bc0586454d36bf129e788fe04729b57b726c1907a4d4ca9f` | `234c367f7952d758ee8c743ef57190d416532524` |

Состав подтверждён по ID: базовый набор — `RU-GEN-*` (29 записей); ценовое расширение — `RU-COST-*` (3 записи). Оба JSON сохраняют `status=not_run` у всего набора. Это замороженные входные данные, а не результаты AI-наблюдений.

**Решение:** не копировать, не генерировать заново и не редактировать запросы в рамках этого спринта. Использовать точные файлы по указанным путям; любые изменения оформлять отдельной версией с новым хешем и явным diff. Сами AI-прогоны остаются `NOT_RUN` до подтверждённой consumer-UI сессии в нужном рынке. Не подменять российскую региональную среду US/en, NL или model API.

## 2. Платформенная матрица

| Платформа | Поверхность | Статус | Причина |
|---|---|---|---|
| ChatGPT Search | consumer web | NOT_RUN | нет аутентифицированной consumer-сессии |
| Perplexity | consumer web | NOT_RUN | то же |
| Claude (web/search) | consumer web | NOT_RUN | то же |
| Mistral Le Chat / Search | consumer web | NOT_RUN | то же |
| DeepSeek | consumer web + direct URL fetch | NOT_RUN (план отдельного поднабора) | то же |
| Google AI Overviews / AI Mode | consumer web (регион-зависимо) | NOT_RUN | то же |
| Bing Copilot | consumer web | NOT_RUN | то же |
| Yandex Алиса / GigaChat | RU consumer UI | NOT_RUN — RU consumer UI unavailable | подмена региона VPN/proxy запрещена ТЗ |
| GSC impressions/clicks | кабинет | NOT_RUN | допускается как отдельный канал, НЕ приравнивается к AI-цитированию |

## 3. Классы промптов

- **A brand-aware**: пользователь знает название («Аудио-Реклама•ru»). Метрика: корректность фактов о компании, ссылки.
- **B brand-blind commercial discovery**: описание задачи без названия студии («записать голосовое приветствие для АТС», «заказать озвучку аудиокниги», «студия озвучки видео на 11 языках»). Метрика: присутствие/позиция/цитирование.
- **C shortlist/procurement**: сравнение поставщиков с запросом источников и условий. Метрика: попадание в shortlist, качество evidence.

## 4. Протокол фиксации каждой попытки (обязательные поля)

exact prompt; платформа/product surface/model label; дата-время (UTC+локаль); фактический регион и язык UI; включён ли web search; присутствие компании; тип упоминания (рекомендация / перечисление / цитирование); позиция; точные citation URLs; конкурентные имена; фактические ошибки/устаревшие цены/неверная атрибуция услуг; повторный запуск и вариативность. Минимум 2 повтора на промпт; никаких агрегатов до фиксации sample size и repeat count (термин «share of voice» запрещён до этого условия).

## 5. Анти-фальсификация

- NOT_RUN ≠ 0. Никаких «оценок вероятного результата».
- Прямой fetch URL (DeepSeek direct) ≠ самостоятельное обнаружение — учитывается отдельным классом.
- Реферальные хиты ≠ лиды; crawl бота ≠ цитирование.
- Все сырые выгрузки ответов сохраняются (screenshot/copy) с timestamp.

## 5A. Два домена — два отдельных prompt scope

| Scope | Сущность | Prompt class | Status |
|---|---|---|---|
| Main site | «Аудио-Реклама•ru» — профессиональная студия | RU B2B discovery / service / procurement | Frozen RU sets remain NOT_RUN |
| Audio+ | Отдельный короткий self-service продукт | RU B2C product discovery / terms / rights / route choice | Separate draft module: `AI_VISIBILITY_AUDIO_PLUS_B2C_PROMPT_MODULE_DRAFT_2026-11-22.md`; 8 prompts, NOT FROZEN, NOT RUN |

Do not merge the Audio+ module into the studio's B2B denominators. The module is not frozen because the accessible offer snapshot and product-page snapshot disagree about buyer eligibility and post-payment revisions, and current terms require owner confirmation. It contains no NDA asset URLs or client material.

The connected OpenSEO tracker for the studio is configured for US/en but `configured=false` and has no runs. A Russian OpenSEO/DataForSEO market project was rejected because the provider does not support the Russian location code. No US/en or Netherlands observation is a substitute for RU. The connected GSC property is the main `www` site only; no Audio+ property is connected. No paid tracker or prompt-research call has been run.

## 6. Что уже VERIFIED (вход, не результаты бенчмарка)

- Техническая досягаемость агентов: 22 UA → 200 на HTML; MP3 демо качается всеми проверенными агентами (CDN/WAF-проба 22.11) — precondition для цитирования, не самоцитирование.
- robots/llms/sitemap согласованы (см. PROD_3FILES_ARCHIVE_REVIEW).
