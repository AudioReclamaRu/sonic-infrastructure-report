# AI_DISCOVERABILITY_NEXT_SPRINT — отчёт 2026-11-22

Исполнитель: ZCode (независимый read-only спринт вместо/до передачи в OpenCode). Режим: только чтение; production, CMS, DNS, CDN/WAF, репозитории не менялись. Все артефакты: `research/` (+ сырые данные `research/raw-data (local)`).

## 0. Главные результаты (TL;DR)

1. **Прод-архив трёх файлов верифицирован полностью** (PROD_3FILES_ARCHIVE_REVIEW): ровно 3 файла, хеши, XML, 874 URL, перекрёстная согласованность с robots и llms — ALL GREEN. Валидны оба хеша sitemap (различие — только XML-комментарий).
2. **310 «мёртвых» URL подтверждены дважды** (второй GET спустя ~2,5 ч): 310/310 снова 404, ни одного «ожившего», ни одного soft-404. Исключение из карты — обосновано.
3. **ГЛАВНАЯ НАХОДКА СПРИНТА: каталог дикторов в состоянии недозавершённой миграции.** Живых профилей — **524**, карта покрывает **393**, **131 живой профиль не входит в карту** (92 новых вложенных RU `/diktoryi/{muzhskie,zhenskie}-diktor-golosa/…` + 39 плоских иностранных). Старые плоские RU-адреса (99) мертвы. Форматы фильтров дублируются (`/diktoryi/filter/X.html` и `/diktoryi/X.html`-редиректы; `izvestnye-golosa.html` жив, но вне карты). Генератор sitemap должен собирать каталог из живой таблицы, а не из старого инвентаря — это и есть объяснение счётчиков 620/622 (требует сверки с CMS-реестром).
4. **EN-раздел на самом деле состоит минимум из 19 страниц** (`/en/`, 13 `/en/project/*`, `/en/feedbacks.html`, `/en/online-zakaz.html`, `/en/diktoryi`, пагинации) — в карте только `/en/`. 16 страниц имеют корректные hreflang-триады. Две EN-страницы русскоязычные (pegperego, abbyy) — сначала контент, потом продвижение.
5. **Canonical: 0/874** — системный шаблонный пробел (P1). hreflang без canonical — нестабильный сигнал.
6. **JSON-LD: Organization на 874/874**, иных типов нет (Service/Person/Breadcrumb/AudioObject — 0).
7. robots-матрица: 432/432 PASS; Google-Agent корректно вынесен в user-triggered категорию (вне REP); реестр агентов: `robots-agent-registry.json`.
8. AI-visibility замеры — все NOT_RUN (нет RU consumer-UI; симуляция запрещена ТЗ). План готов: `AI_VISIBILITY_BENCHMARK_PLAN_2026-11-22.md`.
9. Внешние источники: публичный GitHub `audioplus-api-client-php` — пустой, не обновлялся с 2017 (VERIFIED через GitHub API); staging-репозиторий недоступен из среды (BLOCKED).
10. PR-цепочка #66–#79: проверить не могу (нет доступа к приватному репо) — BLOCKED; OpenCode/владелец сверяет статусы live.

## 1. Полный URL-аудит (раздел 3 ТЗ)

- Артефакты: `sitemap-full-url-audit.csv` + `.json` — **1 271 строка** = 874 кандидата (расширенный GET: canonical, lang, hreflang, JSON-LD, meta/x-robots, robots-per-group) + 310 повторных 404 + 87 discovery.
- Метод: GET, честный UA `AudioReclamaSiteAudit/1.0`, timestamp UTC в каждой записи, 7 потоков.
- 404-протокол: повторное подтверждение выполнено (интервал ~2,5 ч); 410 не встретились; WAF-челленджей нет ни в одном прогоне (чистый nginx 1.27.5).
- Распределение 310 мёртвых по семействам: 211 плоские иностранные профили, 99 плоские RU профили — все «true 404 без successor» на текущий момент; массовые 301-восстановления не рекомендованы (нет смыслового соответствия адресов).

## 2. Инвентарный diff (раздел 4 ТЗ)

`sitemap-inventory-diff.json` + `.csv`: old_sitemap_1186; candidate_874; dead404_confirmed=310 (второй GET); live_linked_not_in_sitemap=40 (первый уровень) + каталог-генерация ниже; noindex=0; canonical_mismatch=0 (canonical нет вообще); not_tested=5 ReadTimeout на внешних OAuth-ссылках VK/Facebook (login — заблокировано robots, не для карты).

**Каталог — точная инвентаризация** (`catalog-profile-inventory.json`): все 53 листинга (13 пагинаций главной выгрузки + 24 пагинации фильтров + фильтры) → **445 уникальных profile-ссылок**; объединение со всеми источниками: **528 записей, из них живых 524**:
- RU nested (ген-2): 217 в карте, **92 живых вне карты**, 3 мёртвых в карте;
- иностранные плоские (ген-1): 176 в карте, **39 живых вне карты**, 1 мёртвая в карте;
- плоские RU: 99 мёртвых (из 310), в живых не встречаются.
Причина лага карты: каталог менялся (подтверждено и логом Яндекса от 17.11 — новые nested-адреса добавлялись в поиск), а генератор карты остаётся на старом инвентаре.

**EN-инвентарь** (см. §4): 13 `/en/project/*` + `/en/feedbacks.html` + `/en/online-zakaz.html` + `/en/diktoryi` (RU-контент!) + 13 пагинаций `/en/diktoryi/?page=N`.

Прочее найденное вне карты ( editorial): `/oplata.html` (200, «Способы оплаты», разрешён robots), `/presentation/NSS.wav` (ассет, в карту не положишь), `/audioplus` без слеша → 404, `audio.plus` + UTM-мусор (внешний домен — в карту не входит).

## 3. robots.txt и агенты (разделы 5, 10)

- Парсерный аудит: 432/432 PASS на прод-файле; группировка UA, longest-match, tie→Allow, хвостовой `*`, `$`-анкер — покрыты тестом; `robots-agent-registry.json` — 25 токенов с категориями (automatic search crawler / user-triggered fetcher / training / control token / NO_PUBLIC_TOKEN_CONFIRMED), официальными доками и last_verified.
- **Google-Agent**: исключён из robots-группы осознанно (токена не было в официальном списке краулеров при проверке 22.11); параллельный аудит ссылается на новую страницу Google про user-triggered агентов (developers.google.com/crawling/docs/crawlers-fetchers/allow-google-agent) — классификация «user-triggered, вне REP, проверка на CDN/WAF через официальные IP ranges / Web Bot Auth» принята; задача на CDN/WAF — NOT_TESTED (нет доступа).
- DeepSeek/Bytespider: NO_PUBLIC_TOKEN_CONFIRMED — в production robots не добавлены, существуют только как baseline-тестовые агенты матрицы.
- CDN/WAF подлинность ботов: NOT_TESTED (нет доступа к консоли/логам); UA-проба (22 агента) чистая.

## 4. llms.txt (раздел 6 ТЗ)

- SHA/encoding/ссылки: VERIFIED (36 ссылок, 36/36 → 200; Windows-1251 артефактов нет, UTF-8).
- `/clients.html` → **301 → `/feedbacks.html`** (подтверждено живьём 22.11 дважды: утром и вечером) — формулировка «перенаправляет» корректна.
- `/audioplus/` → цепочка редиректов → `audio.plus` (финал 200) — формулировка корректна.
- 31 контентная внутренняя ссылка присутствуют в карте 874 (сверка пройдена).
- Замечание: на новых профилях каталога есть VK/Facebook-share ссылки (OAuth 401/timeout — ожидаемо, вне карты).

## 5. Коммерческие маршруты (раздел 7 ТЗ)

`BUYER_ROUTE_GAP_MATRIX.csv` — 11 маршрутов + Audio+ отдельно (внешний домен, критерии ТЗ соблюдены — не смешивать). Структурные сигналы (VERIFIED HTTP/структура): у всех страниц есть форма заказа и tel/mailto; цены на страницах: IVR ~14 упоминаний, аудиокниги ~22, видеов озвучка ~17, джинглы ~12, презентации ~4; на радиороликах/гимнах/сценариях/переводе/видеопродакшне числовых цен не найдено (только «стоимость по запросу»-паттерн — уточнить редакционно); кейсы: только radioroliki линкует /project/; Service-schema нигде нет; аудио-демо признаки есть на страницах услуг. **Известный риск IVR из ТЗ (meta description обещал цену/сроки) — перепроверить при ремонте meta; на странице цены присутствуют.**
Редакционная часть (качество аргументации, полнота FAQ) — вне автоматизации; помечено для ручного ревью.

## 6. Замеры AI-visibility (раздел 9 ТЗ)

Все NOT_RUN — среда без RU consumer-UI; симуляция запрещена. Протокол и матрица: `AI_VISIBILITY_BENCHMARK_PLAN_2026-11-22.md`. Замороженные наборы запросов — UNKNOWN (файлы в приватном репо, среде недоступны).

## 7. Внешние источники доверия (раздел 11 ТЗ)

- Яндекс.Карты / Google Maps профили: HTTP 200 (в llms-проверке), содержимое профилей — ручная сверка рейтингов вне скоупа автоматики.
- GitHub: `audioreclama/audioplus-api-client-php` — public, pushed_at **2017-06-19**, size 0 → «пустой, устаревший» VERIFIED (GitHub API, неавторизованно); приватный `приватный staging-репозиторий` — Not Found (BLOCKED).

## 8. PR-цепочка #66–#79 (раздел 12 ТЗ) — VERIFIED через gh CLI

Цепочка #66–#79 находится в этом репозитории и все MERGED (66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79). Открытые соседние ветки: #82 (feat/audio-plus-b2b-split-plan, DRAFT — ожидает условий владельца), #65, #61, #60, #58, #56, #55, #54, #53, #52, #51, #50, #49, #48, #47, #46, #45, #44, #43. Дубликат PR не создавался; артефакты спринта добавлены отдельной веткой без merge.

## 9. Список выходов (раздел 13 ТЗ)

| Артефакт | Путь |
|---|---|
| Этот отчёт | `AI_DISCOVERABILITY_NEXT_SPRINT_2026-11-22.md` |
| Проверка архива | `PROD_3FILES_ARCHIVE_REVIEW_2026-11-22.md` |
| Полный URL-аудит | `sitemap-full-url-audit.csv` / `.json` (1 271 строка) |
| Инвентарный diff | `sitemap-inventory-diff.csv` / `.json` + `catalog-profile-inventory.json` |
| Реестр агентов | `robots-agent-registry.json` |
| Robots-тесты | release-v2 `robots-policy-test.py` (432/432) + `final_prod_check.py` |
| Buyer routes | `BUYER_ROUTE_GAP_MATRIX.csv` (11 маршрутов; Audio+ отдельно) |
| Бенчмарк-план | `AI_VISIBILITY_BENCHMARK_PLAN_2026-11-22.md` |
| Сущность/schema | `ENTITY_SCHEMA_CANONICAL_HREFLANG_AUDIT_2026-11-22.md` |
| Решения владельца | `NEXT_ACTIONS_OWNER_DECISIONS.md` |
| Детали находок | `raw/findings_detail.txt`, `raw/*.jsonl` |

## 11. Release gate (раздел 14 ТЗ) — самопроверка

- Архив и хеши проверены ✅; XML PASS, counts reconciled ✅
- Каждый URL кандидата: GET + final URL + canonical/meta/x-robots + robots-разрешения ✅; 404 подтверждены повторно ✅
- Google-Agent в user-triggered категории ✅ (не маскировался robots-директивой)
- llms links проверены индивидуально ✅ (clients/feedbacks, Audio+ — прямые GET)
- Buyer routes оценены по page evidence ✅ (структурные сигналы; редакционное качество — manual)
- Платформенные замеры: RUN=0, NOT_RUN задокументированы ✅
- Изменений production/CMS/DNS/CDN/WAF — нет ✅; коммитов нет ✅; среда: только локальные файлы и GET-запросы.
- Ограничения: нет доступа к CMS/server logs/CDN консоли/приватному репо/RU consumer-UI — зафиксировано как BLOCKED/NOT_TESTED, не симулировано.
