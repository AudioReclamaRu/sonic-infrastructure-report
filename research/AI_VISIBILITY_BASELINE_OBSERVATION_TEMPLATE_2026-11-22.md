---
type: observation_template
date: 2026-11-22
lang: ru
status: template_not_run
related:
  - research/AI_VISIBILITY_BENCHMARK_PLAN_2026-11-22.md
  - research/P0_PUBLICATION_VALIDATION_CHECKLIST_2026-11-22.md
  - research/AI_DISCOVERABILITY_TWO_DOMAIN_RU_BASELINE_2026-11-22.md
---

# AI Visibility Baseline Observation Template — 2026-11-22

**Статус:** `template_not_run`. Шаблон для фиксации наблюдений; сам по себе не содержит baseline-результатов.
**Режим:** read-only documentation/template. Никакие внешние проверки, платные AI tracker-запуски, автоматические замеры или публикации не выполняются этим артефактом.

## 1. Правила методики

- **RU-first:** первый baseline-срез — Россия, русский язык, реальные consumer UI, где доступно. Расширение на другие рынки/языки — только отдельными помеченными срезами.
- **UI и API раздельно:** `consumer_ui` и `model_api` не смешивать в одной агрегированной метрике. API-ответ не заменяет consumer UI.
- **Платные проверки:** не запускать без отдельного разрешения владельца.
- **Нет симуляции:** не заполнять ответ/источники/статус «по ожиданию». Только фактически наблюдённое.
- **Интерпретация:**
  - отсутствие упоминания бренда в полученном ответе = **результат наблюдения** (фиксировать как есть);
  - отсутствие самого ответа / блокировка / ошибка / не запускался = **не нулевая видимость**, а соответствующий статус наблюдения.
- **Доказательство:** хранить точный prompt, полный оригинальный ответ, все обнаруженные источники/URL, скриншот/лог/экспорт, где это допустимо.
- **GSC/GA4/позиции:** не выдавать за AI-видимость. Этот шаблон фиксирует только наблюдения ответов AI-платформ.

## 2. Таксономия статусов наблюдения

| Статус | Значение | Когда использовать | Можно ли считать нулевой видимостью |
|---|---|---|---|
| `ANSWERED` | Ответ получен и зафиксирован | Платформа вернула ответ, даже если без упоминания бренда/ссылки | Нет; это валидное наблюдение |
| `NO_ANSWER` | Платформа открылась, но содержательного ответа нет | Пустой ответ, отказ без внешней блокировки, «не знаю» как фактический ответ — фиксировать текст | Нет; фиксировать как наблюдение |
| `BLOCKED_REGION` | Недоступно из-за региона/гео-ограничения | Фактическая гео-блокировка/недоступность сервиса | Нет |
| `BLOCKED_AUTH` | Недоступно из-за авторизации/аккаунта/доступа | Требуется логин/подписка/доступ, которого нет в валидной среде | Нет |
| `UNSUPPORTED_PROVIDER` | Платформа/режим не поддерживается в данной среде/рынке | Нет поддержки рынка, языка, режима, интерфейса в допустимой среде | Нет |
| `ERROR` | Техническая ошибка при наблюдении | Таймаут, ошибка UI, сбой запроса, повреждённый экспорт; детали в evidence | Нет |
| `NOT_TESTED` | Наблюдение не выполнялось | Запланировано, но не запускалось | Нет |

## 3. Обязательные поля записи

| Поле | Тип | Обязательное | Описание |
|---|---|---:|---|
| `observation_id` | string | Да | Уникальный ID, например `AIVB-2026-11-22-RU-001` |
| `observed_at` | ISO 8601 datetime | Да | Дата и время наблюдения с таймзоной |
| `country` | string | Да | Страна наблюдения, например `RU` |
| `language_locale` | string | Да | Язык/локаль, например `ru-RU` |
| `platform` | string | Да | Платформа: ChatGPT, Gemini, Yandex Alice AI, GigaChat, Perplexity, Copilot и т.д. |
| `product` | string | Да | Конкретный продукт/поверхность: web app, mobile app, browser sidebar, assistant, IDE и т.д. |
| `model_or_version` | string | Да | Модель/версия/режим, если видимы; иначе `UNKNOWN_VISIBLE` |
| `access_mode` | enum | Да | `consumer_ui` или `model_api` |
| `interface` | string | Да | Конкретный интерфейс: desktop web, Android app, iOS app, API endpoint, browser extension |
| `auth_state` | string | Да | `anonymous`, `logged_in`, `subscription`, `enterprise`, `unknown` — без секретов/PII |
| `search_grounding_mode` | string | Да | `on`, `off`, `auto`, `unknown`, `not_applicable`; указать режим поиска/grounding |
| `prompt_exact` | string | Да | Точный текст запроса без перефразирования |
| `answer_full_original` | string | Да* | Полный оригинальный ответ. Для не-`ANSWERED`/`NO_ANSWER` может быть пустым с пояснением в `evidence_notes` |
| `sources_urls` | array[string/object] | Да | Все обнаруженные источники/URL/цитаты; пустой массив допустим, если их нет |
| `brand_mentioned` | boolean/null | Да | `true`/`false`/`null` (null только если ответ не получен) |
| `official_site_linked` | boolean/null | Да | Ссылка на официальный сайт присутствует; `null` если ответ не получен |
| `competitors` | array[object] | Да | Конкуренты/альтернативы, упомянутые в ответе, и их источники |
| `observation_status` | enum | Да | Один из статусов раздела 2 |
| `evidence_notes` | string | Да | Путь к скриншоту/экспорту, ограничения, аномалии, причина статуса |
| `observer` | string | Да | Идентификатор наблюдателя/команды (без персональных данных, если не нужно) |
| `run_id` | string | Нет | Идентификатор среза/кампании |
| `domain_scope` | string | Нет | `main_b2b` (`audio-reclama.ru`) или `audio_plus_b2c` (`audio.plus`) |

`*` Для `ANSWERED` и `NO_ANSWER` поле должно отражать фактический текст/его отсутствие максимально полно.

## 4. Шаблон записи (JSON)

```json
{
  "observation_id": "AIVB-YYYY-MM-DD-RU-001",
  "observed_at": "2026-11-22T00:00:00+03:00",
  "country": "RU",
  "language_locale": "ru-RU",
  "platform": "TBD_PLATFORM",
  "product": "TBD_PRODUCT",
  "model_or_version": "UNKNOWN_VISIBLE",
  "access_mode": "consumer_ui",
  "interface": "desktop web",
  "auth_state": "unknown",
  "search_grounding_mode": "unknown",
  "prompt_exact": "TBD_EXACT_PROMPT",
  "answer_full_original": "",
  "sources_urls": [],
  "brand_mentioned": null,
  "official_site_linked": null,
  "competitors": [
    {
      "name": "",
      "mentioned_as": "",
      "sources_urls": []
    }
  ],
  "observation_status": "NOT_TESTED",
  "evidence_notes": "TBD: screenshot/export path, reason, limitations",
  "observer": "TBD",
  "run_id": "RU-BASELINE-2026-11-22",
  "domain_scope": "main_b2b"
}
```

## 5. Шаблон CSV (заголовок)

```csv
observation_id,observed_at,country,language_locale,platform,product,model_or_version,access_mode,interface,auth_state,search_grounding_mode,prompt_exact,answer_full_original,sources_urls,brand_mentioned,official_site_linked,competitors,observation_status,evidence_notes,observer,run_id,domain_scope
```

Для CSV: `sources_urls` и `competitors` хранить как JSON-строки в ячейке; не терять вложенные URL.

## 6. Минимальный контроль качества перед включением в baseline

- [ ] `prompt_exact` совпадает с фактически отправленным запросом.
- [ ] `answer_full_original` сохранён полностью, без пересказа.
- [ ] Все видимые источники/URL выписаны в `sources_urls`.
- [ ] `brand_mentioned` и `official_site_linked` заполнены по фактическому ответу.
- [ ] Конкуренты и их источники вынесены отдельно.
- [ ] `access_mode` корректно разделяет `consumer_ui` / `model_api`.
- [ ] Статус соответствует таксономии; отсутствие ответа не записано как нулевая видимость.
- [ ] Есть evidence (скриншот/экспорт/лог) или явно указана причина его отсутствия.
- [ ] Не использовались платные проверки без отдельного разрешения.

## 7. Границы использования

- Не использовать этот шаблон для публикации неподтверждённых результатов.
- Не смешивать домены `audio-reclama.ru` и `audio.plus` в одном знаменателе.
- Не делать вывод о «видимости бренда» по одному наблюдению, одному провайдеру или только API-срезу.
- Не включать PII, секреты, cookies, токены или приватные данные аккаунтов в evidence.
