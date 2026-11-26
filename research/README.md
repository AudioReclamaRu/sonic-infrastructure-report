---
type: index
date: 2026-11-21
lang: ru
related:
  - AGENTS.md
  - standards/CHARACTER_VOICE_IDENTITY_AND_CONTINUITY_FRAMEWORK.md
  - problem-solutions/README.md
---

# Research — исследовательские планы и внешние кейсы

Этот каталог хранит исследовательские материалы, которые ещё не стали проверенными внутренними стандартами, завершёнными экспериментами или подтверждёнными услугами. У каждого объекта свой статус и собственные ограничения.

## Аудиодоставка и приёмка

- AUDIO_RECIPIENT_TECHNICAL_PROFILES_2026-11-20.md — срез первичных правил для Google Play Books, ЛитРес, ACX, EBU, отдельных договорных профилей радио/ТВ, российских IVR/АТС (МегаФон, Zadarma, МТС Exolve, MANGO OFFICE, Ростелеком), Twilio, Asterisk и YouTube Content Manager. Разделяет платформенные правила, рекомендации, исторические документы, особенности отдельных API и неизвестные параметры; не является универсальным пресетом или утверждённым стандартом.

## Голос и персонаж

- CHARACTER_VOICE_CONTINUITY_EXTERNAL_CASES_2026-11-14.md — ограниченная подборка внешних публичных кейсов преемственности персонажных голосов: Mickey Mouse, Bugs Bunny, Kermit. Факты источников, осторожные рабочие наблюдения и неизвестные отделены друг от друга. Это не кейсы «Аудио-Реклама•ru».
- Связанный проект: ../standards/CHARACTER_VOICE_IDENTITY_AND_CONTINUITY_FRAMEWORK.md — исследовательская рамка, не утверждённый стандарт.
- Связанный инструмент: ../standards/CHARACTER_VOICE_PASSPORT_TEMPLATE.md — заполняемая форма, не доказательство, что процесс уже применялся в клиентских проектах.
- CHARACTER_VOICE_PASSPORT_SYNTHETIC_WALKTHROUGH_2026-11-14.md — полностью вымышленный tabletop-проход по передаче роли. Проверяет разрешения на старую фонограмму, AI-обучение, цифровую реплику и локализацию; статус HOLD / NOT RUN, не студийный кейс и не реальный тест.
- ../schemas/character-voice-passport.schema.json — проект JSON Schema v0.1 для цифрового паспорта и условной проверки разрешений.
- character-voice-passport.synthetic.json — вымышленная JSON-карточка DRAFT/HOLD для тестирования; реальные голоса и права отсутствуют.

## Выбор голоса и тембр

- VOICE_TIMBRE_AND_CASTING_COMPARISON_PROTOCOL_2026-11-14.md — предложение воспроизводимого сравнения голосов для рекламы, IVR и других задач; разделяет тембр, просодию, техническое качество записи и результаты коммуникации. Это не проведённый тест и не рейтинг голосов.
- VOICE_TIMBRE_CASTING_RATING_SHEET_TEMPLATE.md — пустая анкета для сравнения кандидатов и фиксирования результатов. Не валидированная шкала.

## TTS и аудиотестирование

- RU_TTS_QUALITY_BENCHMARK_PLAN_2026-11-14.md — план воспроизводимого набора тестов русского TTS. Это предложение методики; фактический benchmark и результаты ещё не заявлены.

## Open source

- OPEN_SOURCE_TARGET_AUDIT_PIPER_2026-11-14.md — предварительный аудит OHF-Voice/Piper: социальные правила, лицензия, политика и возможный вклад. Сам по себе аудит не означает, что публичное участие, issue или PR уже состоялись.

## Видимость в ответах ИИ

- AI_VISIBILITY_BENCHMARK_PROTOCOL_2026-11-17.md — протокол повторяемого теста идентичности бренда, корректности услуг, экспертного retrieval и качества цитирования в ChatGPT Search, Google AI Overviews/AI Mode, Copilot, Gemini и Perplexity. Контрольный набор создан, результаты ещё не прогнаны.
- ai-visibility-benchmark-queries-2026-11-17.json — фиксированный RU-набор из 20 запросов с ожидаемыми фактами, источниками и запретами на неподтверждённые утверждения.
- ai-visibility-benchmark-template.csv — журнал «запрос × платформа × запуск».
- AI_VISIBILITY_SCORING_RUBRIC_2026-11-17.md — единые проверяемые критерии оценки 0/1/2/null по восьми осям, generic discovery и критическим ошибкам.
- AI_VISIBILITY_OBSERVATION_RECORD_SCHEMA_2026-11-17.json — JSON Schema первичной записи полного ответа и источников; CSV остаётся компактным индексом.
- ../tools/ai_visibility_evidence.py — офлайн-проверка полных observation records и согласованности ссылок CSV ↔ JSON по уникальному observation_id.

## Привлечение внимания и переходов на сайт

- SITE_ATTENTION_EXECUTION_PLAN_2026-11-19.md — план на основе фактических данных Search Console/GA4: какие страницы уже получают внимание, где есть коммерческий спрос, где нет надёжного измерения и какие поверхности развивать.
- ATTENTION_EXECUTION_REGISTER_2026-11-19.csv — приоритетный реестр каналов, публичных присутствий, каталогов и редакционных возможностей; статусы не подразумевают, что профили уже заявлены или изменены.
- OWNER_READY_SITE_ATTENTION_FIXES_2026-11-19.md — подготовленные задания по усилению сайта на случай отдельного разрешения; официальный сайт не редактировался.

- SITE_ATTENTION_BREAKTHROUGHS_2026-11-20.md — новые P0/P1 находки по самостоятельному домену Audio+, GSC URL Inspection англоязычных кейсов, видеоархиву YouTube и карточке AllAdvertising; зафиксированы статусы, ограничения свежести и безопасный план действий.\n- AI_DISCOVERABILITY_EN_INDEXABILITY_P0_EXECUTION_BRIEF_2026-11-21.md — точечная проверка EN URL Inspection, коммерческих GSC сигналов и owner-ready последовательность устранения robots/sitemap/canonical/hreflang барьеров. Состояния Google привязаны к датам последнего обхода; live-изменения сайта не выполнялись.
- ATTENTION_EXECUTION_REGISTER_2026-11-19.csv — обновлён 20.11.2026 новыми точками привлечения внимания и статусами Audio+, YouTube, RUTUBE, AllAdvertising и EN URL Inspection.
- EXTERNAL_PLATFORM_EDITABILITY_REGISTER_2026-11-20.md — мастер-реестр внешних профилей и реальных/предполагаемых прав редактирования; разделяет Metricool, owner-confirmed Dzen/VC.ru, публичные площадки и кандидатов.
- EXTERNAL_PLATFORM_EDITABILITY_REGISTER_2026-11-20.csv — машинно-читаемая таблица тех же поверхностей. Это единственная каноническая CSV-версия.

- AI_DISCOVERY_AUDIO_PLUS_ROUTE_BOUNDARY_AUDIT_2026-11-21.md — read-only audit of legacy GEO answer artifacts that blur Audio+ short-order pricing with the studio's corporate radio-production route. Deployment/indexation of the old static URLs is UNVERIFIED; no HTML was modified.
- AI_DISCOVERABILITY_GSC_INDEX_INSPECTION_2026-11-21.md — read-only Google URL Inspection of seven RU service/home URLs: 7/7 PASS, robots allowed, indexing allowed, successful fetch and matching www canonical. This is Google indexability only; OAI-SearchBot/Bingbot access and AI citations remain NOT_TESTED.
- AI_DISCOVERABILITY_RU_BUYER_ANSWER_ROUTE_MAP_2026-11-21.json — machine-readable crosswalk from existing frozen RU generic/price benchmark IDs to the correct official service source, buyer guide, evidence and commercial boundary. Route map only; the prompts remain NOT_RUN and no AI answers are claimed.
- AI_DISCOVERABILITY_COMMERCIAL_ROUTE_REFRESH_2026-11-21.md — read-only refresh of ten professional service routes in connected GSC for 2026-10-22—2026-11-18. Reprioritizes audiobook production from page/query evidence, keeps radio and IVR as follow-up routes, and explicitly separates Google organic signals from AI citation, leads and revenue.
- AI_DISCOVERABILITY_MEASUREMENT_EXECUTION_BRIEF_2026-11-20.md — первый исполнимый цикл AI-Discoverability: фактический RU GSC query→page срез, очередь Alice AI/GigaChat, SoV в Яндекс Вебмастере, обязательная региональная аттестация и запрет на подмену RU-измерений US/en трекером.
- ALICE_AI_EXPORT_SOURCE_ANALYSIS_2026-11-20.md — read-only разбор 177 строк пользовательской выгрузки источников Алисы AI: доля присутствия по этому файлу, распределение собственных URL, смещение в справочные/дикторские запросы, примеры маршрутизации к статьям вместо коммерческих страниц и следующие проверки. Не является полным корпусом ответов или официальным SoV.
- ALICE_SKILL_ORDER_CHANNEL_TRIAGE_2026-11-26.md — триаж owner-supplied гипотезы о навыке Алисы для Audio+, IndexNow и карточках компаний. Разделяет каталог навыков, Алиса AI SoV и поисковую разметку; фиксирует, что внешние каналы запрещены текущим PUBLISHING_AUTHORITY без нового распоряжения владельца. Навык не создавался, уведомления не отправлялись.
- PR_CY_MCP_READONLY_CONNECTION_2026-11-26.md — проверенное после рестарта read-only MCP-подключение PR-CY и первый срез лимитов, проектных ключей, GSC-вью и Метрики с датой выборки, периодом и источником. Пустые вью помечены `NOT_VERIFIED`, а не нулями; платные и мутирующие инструменты не вызывались.
- OFFICIAL_SITE_TEXT_FIX_STATUS_2026-11-26.md — owner-supplied статус орфографических исправлений, расхождения production и CMS-задач. Поздняя проверка владельца противоречит более ранней: изменения остаются в ветках на ревью, MR не слиты и не опубликованы, pipeline и проверки на сайте нет; `OWNER_CONFIRMATION_REQUIRED`, production `UNCHANGED`.
- RELAY_DZEN_CORPUS_TASK_STATUS_2026-11-26.md — owner-supplied статус задания на выгрузку публичного архива Дзена; повторная проверка: 597 комментариев, ACK и SHA нет. Добавлена read-only справка Agent Mesh: сообщение и задача координатора существуют, но исполнителя, экспорта и принятия результата нет; корпус не скопирован и не проанализирован.
- GSC_CARTOON_VOICEOVER_SERVICE_ROUTE_2026-11-26.md — owner-supplied связка «информационный спрос → услуга»: метрики статьи о мультфильмах за 23.08—23.11.2026 и уже существующий контекстный переход на страницу «Озвучка видео». Дублирующую посадочную страницу и дополнительную ссылку не требуется; данные не проверены ассистентом и не являются AI-цитированиями или лидами.
- AI_COMMERCIAL_PROMPT_COVERAGE_MAP_2026-11-20.md — связь RU Google Search Console query→page данных по четырём коммерческим страницам с неизменёнными generic/brand-service AI benchmark-модулями; обосновывает отдельные ценовые prompts для IVR, видео и аудиокниг. GSC — поисковый сигнал, не AI-видимость.
- ai-visibility-ru-commercial-price-extension-2026-11-20.json — отдельный аддитивный набор из трёх небрендированных RU price-intent вопросов. Не изменяет 29-вопросный generic baseline; все вопросы пока NOT_RUN.
- AI_SERVICE_ANSWER_SURFACE_AUDIT_2026-11-20.md — read-only разбор четырёх коммерческих страниц как источников ответов ИИ: видимые доказательства, границы услуг, не подтверждённые цены/сроки/технические обещания, GSC-приоритеты и осторожность из-за возраста HTML-crawl.
- AI_EXTERNAL_ENTITY_AND_CITATION_SURFACE_AUDIT_2026-11-20.md — Bing AI Performance как дополнительная native citation-аналитика; сравнение с Alice SoV/GSC/consumer UI; факт-чек публичных профилей AllAdvertising и Cinematch; независимое подтверждение проекта с золотом WOW Awards 2018. Bing пока не подключён, профили не редактировались.

## Поисковая видимость и качество обхода

- READ_ONLY_SEARCH_SIGNAL_AUDIT_2026-11-14.md — выборочный live-аудит sitemap, коммерческих страниц и каталога дикторов. Зафиксированы 1 186 уникальных URL, 2 подтверждённых 404-профиля в sitemap, один redirecting URL и несогласованные публичные счётчики каталога; это не полный crawl и не отчёт Search Console/Яндекс Вебмастера.

## Правила использования

- Не превращать исследовательскую гипотезу в факт.
- Не выдавать внешний случай за клиентский кейс студии.
- Не заявлять тест или benchmark завершённым, пока не сохранены исходные данные, метод, версии, условия и результат.
- При переходе проекта в стандарт, инструмент или эксперимент связать документы и обновить статусы, не удаляя исходную историю.
