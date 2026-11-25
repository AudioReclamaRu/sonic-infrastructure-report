---
type: owner_decision_register
date: 2026-11-22
lang: ru
status: awaiting_owner_and_operator_actions
related:
  - research/AI_DISCOVERABILITY_TWO_DOMAIN_RU_BASELINE_2026-11-22.md
  - research/AUDIO_PLUS_AI_DISCOVERABILITY_PLAYBOOK_2026-11-22.md
# NEXT_ACTIONS_OWNER_DECISIONS — 2026-11-22

## Owner-approved AI demo-use decision — 22.11.2026

- AI search and user-requested retrieval remain allowed for Audio+ demo media through the explicit allow-list in the candidate `robots.txt`.
- AI model-training and broad corpus collection from `/tools/media/demo/` are disallowed until written, file-specific rights clearance. The default wildcard policy also denies the demo path to unclassified crawlers.
- `Google-Extended` combines Gemini training and grounding controls. Disallowing the demo path excludes those audio files from both uses, while ordinary Google Search remains accessible via `Googlebot`.
- `Google-Agent` is a user-triggered fetcher outside robots.txt/REP control; its matrix status is `NOT_APPLICABLE`. robots.txt is not access control and does not guarantee behavior by unknown or non-compliant fetchers.
- Search/retrieval permission does not convert `RIGHTS_UNVERIFIED` into `PUBLIC_CLEARED`, and does not authorize model training, transcripts, or republication.

## P0 — Audio+ privacy, rights and current product facts (before any AI/public rollout)

1. **NDA/client media containment.** The owner has confirmed an active confidentiality/access issue in the Audio+ client-media area. Close anonymous access server-side, remove public references, check origin/CDN/caches/old URLs, preserve and review access logs, and assess search-index removals only after containment. Exact incident evidence and asset inventory remain in the restricted private deployment record; do not copy client filenames, URLs, hashes, audio or identities into this public research repository.
2. **Demo media rights review.** A subset of demo assets has unverified provenance/licensing. Treat every uncleared asset as `RIGHTS_UNVERIFIED`; keep it out of public demos, transcripts, AudioObject and machine-readable feeds until written, use-specific clearance is recorded. Filename similarities are review flags, not proof of infringement.
3. **Current Audio+ offer/product reconciliation.** The official homepage snapshot shows 90 words, one file/one complete thought, ₽1,990 base order and ₽790 corrections, while the publicly available offer page (crawled in the last month; text apparently published about 10.4 years ago) says buyer must be an individual, excludes legal entities/IP, requires 100% prepayment, gives one version, disallows post-payment text changes and rework, and describes a simple non-exclusive license. Resolve this public UI/offer conflict and update both documents/workflow before price, eligibility, revision or rights claims appear in llms/schema/FAQ/AI answers. **Offer clause 3.14** allows publication of an order result unless the buyer opts out; reconcile this with all NDA orders, check persisted checkbox state, and enforce a hard per-order publication prohibition wherever NDA/confidentiality applies. Do not treat a general opt-out as overriding NDA.
4. **Separate Audio+ measurement.** The connected Search Console property currently covers only the main www host; Audio+ is not a selected property. Decide whether to add and verify a dedicated Audio+ GSC/GA4 measurement setup. Do not infer Audio+ performance from the studio property.
5. **GA4 stream validation.** The connected GA4 property has a web stream created 17.11.2026, but the read-only reports returned no page/organic rows for the checked intervals. Verify that the measurement ID is actually firing on the live www and apex paths, that consent/tag triggers work, and that key events arrive in DebugView/realtime before using sessionKeyEventRate as a business-value score.


Только вопросы, требующие решения/действий владельца. Группировка по impact/risk. Не-blocking для утреннего деплоя трёх файлов (кроме п.1 — он определяет следующий релиз sitemap).

## P1 — сразу после публикации (до следующего релиза sitemap)

1. **Sitemap v3 — источник истины.** Карта 874 основана на старом инвентаре; краул показал 131 живой непокрытый профиль (92 nested RU + 39 иностранных), EN-раздел из ~16 страниц вне карты, `/oplata.html` и фильтр `izvestnye-golosa.html` тоже вне. Решение: (а) чинить CMS-генератор по спецификации (стратегическое, уже согласовано) и/или (б) собрать разовый статический v3 из проверенного краула. Требуется: сверка 524 живых профилей с реестром CMS (объяснит и счётчики 620/622).
2. **Canonical-шаблон (0/874).** Self-canonical + canonical для алиасов форматов (filter .html ↔ без .html, slash/no-slash). Шаблонная правка в CMS.
3. **Деиндексация калькуляторов** (одобрено): снять внутренние ссылки на `/kalkulyator-tsen.html` и `-new.html`, затем «Удаление страниц из поиска» в Яндекс.Вебмастере и Removals в GSC.

## P1 — коммерческая видимость и измерение двух доменов

1. **Три существующих RU buyer guides (не создавать новые дубли).** Согласовать owner/editorial review для `guides/audio-advertising-production.ru.md`, `guides/multilingual-ivr-voice-production.ru.md` и `guides/audiobook-production.ru.md`. Уточнить состав услуг, права, цены, сроки, языковые claims и scope integration; после правок обновить freshness/related sources. Ни один guide пока не опубликован на сайте.
2. **Радиоролики — сниппет и первый экран.** RU GSC за 19.08–19.11: 857 impressions, 3 clicks, average position 10.5; отдельные коммерческие запросы («заказать радиоролик», «заказать аудиоролик») показываются около первой страницы, но CTR низкий. Решить, допускается ли owner-approved title/meta/first-screen diff; не добавлять цену, SLA, размещение или медиаплан без доказательств.
3. **IVR — намерение и граница услуги.** RU GSC: 580 impressions, 4 clicks, average position 27.5; запросы смешивают приветствия, запись меню, цены и телефонию. Подтвердить, что guide/страница чётко отделяют производство файлов от PBX/SIP/CRM/call-routing setup. Любые технические интеграции отражать только при наличии отдельного scope.
4. **Аудиокниги — ценовые вопросы.** RU GSC: 1,012 impressions, 30 clicks, average position 30.2; заметен устойчивый cluster «цена/стоимость». Согласовать подробное объяснение факторов сметы (формат, текст, роли, музыка, права, структура файлов) без превращения информационных примеров старой страницы в универсальный тариф.
5. **GA4 instrumentation health.** За проверенные периоды connected property вернул 0 organic landing-page rows и 0 all-channel page-performance rows. Это не означает ноль посетителей. Назначить технического владельца для теста Measurement ID `G-HK65BQZPR0` на реальных страницах, consent/tag firing, DebugView/realtime и доменных переходов; затем повторить read-only отчёт.
6. **Отдельная аналитика Audio+.** Подтвердить необходимость и подключить отдельный Search Console property и GA4 stream/property для `audio.plus`; не использовать показатели основного B2B-домена как данные Audio+.
7. **RU AI visibility benchmark.** Все фиксированные RU consumer prompts остаются NOT_RUN; OpenSEO не принимает российский market code, и US/en tracker не является заменой. Требуется валидная, аттестованная российская consumer-UI среда. Не запускать платные проверки и не публиковать mention/citation rates до измерений.

## P2 — редакционные/шаблонные решения

4. **x-default язык**: сейчас EN на всех 16 hreflang-страницах (включая главную). Для RU-первого бизнеса рассмотреть x-default → RU. Решение редакционное.
5. **EN-страницы с русским телом**: `/en/project/pegperego.html`, `/en/project/abbyy.html` (русские заголовки), `/en/diktoryi` (полностью русский). Перевести или убрать из EN-навигации/закрыть от индексации до перевода.
6. **Organization JSON-LD**: нормализовать `name`/`sameAs` к `Аудио-Реклама•ru` (юридических лиц в бренд не смешивать); Service-разметку добавлять только после контентной доработки маршрутов (см. BUYER_ROUTE_GAP_MATRIX).
7. **Хрономер/Страницемер** (`/chronomer-stranitcemer.html`): остаются открытыми и в llms.txt — подтвердить или вывести (выведем тем же конвейером, что калькуляторы).

## P3 — ресурсы и окружение

8. **RU consumer-UI для AI-бенчмарка** (аккаунты/машина с российской региональной средой) — без этого все замеры остаются NOT_RUN.
9. **Доступ на выбор**: серверные логи (наблюдаемость ботов), консоль CDN/WAF (allow-list по официальным IP), приватный репозиторий (сверка PR #66–#79). Любой из трёх открывает соответствующий блок спринта.
10. **Публичный GitHub** `audioplus-api-client-php` (пуст, 2017): архивировать/удалить/возобновить — отдельное решение; ничего не публиковать без одобрения.
