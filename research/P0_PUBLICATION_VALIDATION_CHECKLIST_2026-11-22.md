---
type: publication_validation_checklist
date: 2026-11-22
lang: ru
status: SENT_TO_PUBLISH
related:
  - research/AI_DISCOVERABILITY_TWO_DOMAIN_RU_BASELINE_2026-11-22.md
  - research/AI_VISIBILITY_BENCHMARK_PLAN_2026-11-22.md
  - research/AI_VISIBILITY_BASELINE_OBSERVATION_TEMPLATE_2026-11-22.md
  - research/PROD_3FILES_ARCHIVE_REVIEW_2026-11-22.md
---

# P0 Publication Validation Checklist — 2026-11-22

**Статус:** `SENT_TO_PUBLISH` (не `LIVE_VALIDATED`).
**Режим:** read-only проверка после публикации. Чеклист не выполняет внешние проверки автоматически и не подтверждает публикацию сам по себе.
**Правило:** HTTP 200 сам по себе недостаточен. Для каждого файла требуется проверка соответствия ожидаемому SHA-256 и/или точному эталонному содержимому, плюс фиксация доказательства.

## 1. Метаданные проверки

| Поле | Значение |
|---|---|
| `check_id` | `P0-PUB-2026-11-22-01` |
| Дата/время проверки (UTC) | `PENDING` |
| Проверяющий | `PENDING` |
| Среда/канал доступа | `PENDING` (указать: браузер/curl/скрипт, без платных сервисов) |
| Источник ожидаемых хешей/эталонов | `PENDING` (ссылка на release manifest / archive review / git commit) |
| Итоговый статус | `SENT_TO_PUBLISH` |
| Основание для итогового статуса | Публикация передана; live-проверка не выполнена. |

## 2. Реестр опубликованных файлов (6 файлов)

Заполнять по факту публикации. `expected_sha256` берётся из согласованного release manifest/архива. `actual_sha256` считается по фактически скачанному содержимому. `content_check_result` = `PASS` только при совпадении хеша/эталона и отсутствии непредвиденных отличий.

| # | Файл / роль | Точный URL | Ожидаемый SHA-256 | Фактический HTTP/доступ | Фактический SHA-256 | Проверка содержимого | Доказательство | Статус |
|---:|---|---|---|---|---|---|---|---|
| 1 | `llms.txt` | `https://www.audio-reclama.ru/llms.txt` | `f022aa294c29ae00bcee36de3d3a107b57f35359ca223d7771df952b62ba2fee` (из `PROD_3FILES_ARCHIVE_REVIEW_2026-11-22.md`; подтвердить актуальность перед live-проверкой) | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` |
| 2 | `robots.txt` | `https://www.audio-reclama.ru/robots.txt` | `32e2f0b757fb41d99de261dd459581e5f0e4a50c3d9b7fe5b96fb248907474bc` (из `PROD_3FILES_ARCHIVE_REVIEW_2026-11-22.md`; подтвердить актуальность) | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` |
| 3 | `sitemap.xml` | `https://www.audio-reclama.ru/sitemap.xml` | `eb66b55edf1be7390068b3ba1a547dd7098850270d781f9fc8cdc02f4173bfc1` (предпочтительный PROD-заголовок) или `2684c609b1610b90fad8601520e97076881d47d557130ac45c9fe7493868b6b8` (эквивалентный набор 874 URL, только XML-комментарий отличается) — зафиксировать, какой именно вариант опубликован | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` |
| 4 | `TBD_PUBLISHED_FILE_4` (подтвердить по publish manifest) | `TBD` | `TBD` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` |
| 5 | `TBD_PUBLISHED_FILE_5` (подтвердить по publish manifest) | `TBD` | `TBD` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` |
| 6 | `TBD_PUBLISHED_FILE_6` (подтвердить по publish manifest) | `TBD` | `TBD` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` |

**Примечание по реестру:** строки 1–3 предзаполнены известными архивными хешами из read-only review 22.11.2026; это не live-подтверждение. Строки 4–6 обязательны к заполнению точными именами/URL/хешами из фактического publish manifest перед началом live-валидации. Нельзя объявлять `LIVE_VALIDATED`, пока все 6 строк не имеют `PASS` по содержимому.

## 3. Две `<head>`-вставки

Проверять на реальных опубликованных страницах. Фиксировать точный URL страницы, где найдена вставка, ожидаемый фрагмент/идентификатор, факт наличия, количество вхождений и отсутствие дубликатов/конфликтов.

| # | Вставка / назначение | URL проверенной страницы | Ожидаемый идентификатор/фрагмент | Присутствует | Количество вхождений | Дубликаты/конфликты | Доказательство | Статус |
|---:|---|---|---|---|---:|---|---|---|
| H1 | `TBD_HEAD_INJECTION_1` (точный тип/назначение подтвердить по publish package) | `TBD` | `TBD` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` |
| H2 | `TBD_HEAD_INJECTION_2` (точный тип/назначение подтвердить по publish package) | `TBD` | `TBD` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` |

**Критерии PASS:** вставка присутствует ровно в ожидаемом месте/количестве; нет дубликата того же `@id`/script/мета-блока; не ломает существующие корректные сущности.

## 4. Связность `Organization → WebSite → Brand`, canonical и `@id`

| Проверка | Ожидание | Фактический результат | Доказательство | Статус |
|---|---|---|---|---|
| `Organization` присутствует и имеет стабильный `@id` | Один канонический `@id`, корректное имя/URL бренда | `PENDING` | `PENDING` | `PENDING` |
| `WebSite` присутствует и ссылается на `Organization` | `publisher`/связь на ожидаемый `@id` Organization | `PENDING` | `PENDING` | `PENDING` |
| `Brand`/brand-сигналы согласованы | Нет конфликтующих имён/URL/идентификаторов | `PENDING` | `PENDING` | `PENDING` |
| `@id` графа согласован между вставками/страницами | Один и тот же сущностный `@id` не дублируется с разными значениями | `PENDING` | `PENDING` | `PENDING` |
| `canonical` на проверенных страницах | Самоссылка или ожидаемый канонический URL, без конфликтов с sitemap/redirect | `PENDING` | `PENDING` | `PENDING` |
| Наличие дубликатов сущностей | Дубликаты отсутствуют или задокументированы как допустимые | `PENDING` | `PENDING` | `PENDING` |

## 5. Проверка `robots.txt` для AI/поисковых ботов

Проверять фактическое поведение опубликованного `robots.txt` (и при необходимости CDN/WAF-поведение отдельно фиксировать; этот чеклист не подменяет CDN/WAF-аудит).

| User-Agent | Ожидание | Фактическое правило/поведение | Доказательство | Статус |
|---|---|---|---|---|
| `OAI-SearchBot` | Не заблокирован на целевых публичных страницах, если иное не утверждено владельцем | `PENDING` | `PENDING` | `PENDING` |
| `GPTBot` | Согласно утверждённой политике владельца; факт зафиксировать явно | `PENDING` | `PENDING` | `PENDING` |
| `ChatGPT-User` | Не заблокирован для user-triggered fetch на целевых страницах, если иное не утверждено | `PENDING` | `PENDING` | `PENDING` |
| `Google-Extended` | Согласно утверждённой политике; факт зафиксировать явно | `PENDING` | `PENDING` | `PENDING` |
| `PerplexityBot` | Согласно утверждённой политике; факт зафиксировать явно | `PENDING` | `PENDING` | `PENDING` |
| `ClaudeBot` | Согласно утверждённой политике; факт зафиксировать явно | `PENDING` | `PENDING` | `PENDING` |
| `Googlebot` | Не заблокирован на индексируемых целевых страницах | `PENDING` | `PENDING` | `PENDING` |

**Примечание:** «Ожидание» для отдельных ботов должно быть сверено с актуальным owner-approved policy перед валидацией. Чеклист фиксирует факт, а не навязывает политику.

## 6. Sitemap, canonical и фактическая доступность целевых страниц

| Проверка | Цель/URL | Ожидание | Фактический результат | Доказательство | Статус |
|---|---|---|---|---|---|
| Sitemap доступен | `https://www.audio-reclama.ru/sitemap.xml` | HTTP 200, валидный XML, ожидаемый хеш/эталон | `PENDING` | `PENDING` | `PENDING` |
| Sitemap `loc` согласованы с canonical | Выборка целевых URL | `loc` = канонический URL, без redirect/404 | `PENDING` | `PENDING` | `PENDING` |
| Canonical не конфликтует с sitemap/robots | Целевые страницы | Нет противоречий `noindex`/canonical/robots/sitemap | `PENDING` | `PENDING` | `PENDING` |
| Фактическая доступность целевых страниц | Все целевые URL из секций 2–4 | Доступны, ожидаемый контент, нет неожиданных redirect/блокировок | `PENDING` | `PENDING` | `PENDING` |
| Content-type/encoding | Файлы из реестра | Корректный MIME/charset, без битого контента | `PENDING` | `PENDING` | `PENDING` |

## 7. Итоговый статус

| Статус | Условие | Текущее состояние |
|---|---|---|
| `SENT_TO_PUBLISH` | Пакет передан на публикацию; live-проверка не завершена или есть незакрытые пункты | **ТЕКУЩИЙ** |
| `LIVE_VALIDATED` | Все 6 файлов подтверждены по URL + SHA-256/эталону + содержимому; обе `<head>`-вставки проверены без дубликатов; связность Organization/WebSite/Brand/@id/canonical подтверждена; robots-проверки зафиксированы; sitemap/canonical/доступность подтверждены; доказательства приложены; незакрытых P0-пунктов нет | `NOT_ACHIEVED` |

### Незакрытые проверки / блокеры

- [ ] Подтверждён фактический publish manifest на 6 файлов (строки 4–6).
- [ ] Подтверждены точные 2 `<head>`-вставки и страницы проверки.
- [ ] Выполнена live-проверка URL/HTTP/контента/хешей.
- [ ] Подтверждена связность `Organization → WebSite → Brand` и `@id`.
- [ ] Подтверждены robots-политики для перечисленных ботов по owner-approved policy.
- [ ] Подтверждена согласованность sitemap/canonical/доступности.
- [ ] Собраны доказательства (скриншоты/логи/хеши/даты) в разрешённом хранилище.

**Запрет:** не переводить статус в `LIVE_VALIDATED` до закрытия всех P0-пунктов и наличия доказательств.
