---
type: ai-discovery-source-retrieval-audit
date: 2026-11-20
lang: ru
status: source_class_aware_baseline_reviewed
brand: "Аудио-Реклама•ru"
related:
  - ../tools/ai_discovery_source_retrieval.py
  - ../problem-solutions/AI_DISCOVERY_CLAIM_SUPPORT_MATRIX_2026-11-20.json
  - ../research/AI_DISCOVERY_CLAIM_SOURCE_SEMANTIC_AUDIT_2026-11-20.md
---

# Retrieval первичных источников и внутренней методики — 20.11.2026

## Объём и метод

Проверяется retrieval для 46 запросов фиксированного RU benchmark и 112 expected facts. Кандидатный корпус ограничен **44 уникальными документами**, прямо указанными в claim-support matrix. Используется детерминированный BM25 (k1=1.2, b=0.75), тот же русско-английский токенизатор и лёгкая нормализация слов, что и в answer-pack diagnostic.

Выполнены два взаимно сохраняемых режима:

1. **Global control:** исходный вопрос и каждый expected fact ранжируются по единому корпусу всех 44 mapped sources.
2. **Source-class-aware:** retrieval ограничивается допустимым классом источника, указанным в support_type. Смешанные claims ищутся в двух независимых каналах, а оба результата сохраняются. Никакого искусственного объединения двух рангов в один документ не происходит.

## Классы и routing policy

| Класс | Допустимый корпус | Claims |
|---|---|---:|
| first_party_evidence | Датированные first-party snapshots в evidence/ | 44 |
| internal_methodology | Внутренние методики, entity/canon/standards/guides и технические документы | 52 |
| mixed | Оба класса одновременно; каждый канал должен найти свой mapped source | 16 |

Корпус: **18 first-party evidence документов + 26 internal-methodology документов**.

Уровень маршрутизации 46 исходных вопросов: 12 evidence-only, 7 internal-methodology-only, 27 parallel (оба класса).

Для mixed нельзя считать внутренний методический документ заменой публичному evidence или наоборот. Первый подтверждает только то, что действительно зафиксировано в публичном snapshot; второй — внутреннюю методику, позицию или рабочий подход.

## Reviewed baseline: global control

| Метрика | Результат |
|---|---:|
| Запросы с mapped source в top-3 | **31/46** |
| Запросы с mapped source в top-5 | **40/46** |
| Expected facts с mapped source в top-1 | **65/112** |
| Expected facts с mapped source в top-3 | **99/112** |
| Expected facts с mapped source в top-5 | **112/112** |
| Expected facts с mapped source в top-10 | **112/112** |
| Все facts одного запроса имеют mapped source в top-3 | **35/46** |
| Все facts одного запроса имеют mapped source в top-5 | **46/46** |
| Pure first-party claims: snapshot в top-5 | **44/44** |
| Mixed claims: first-party evidence в top-5 (отдельный evidence-rank) | **10/16** |

Global control остаётся полезной диагностикой широкой лексической близости, но сам по себе не гарантирует, что найден документ правильного epistemic/source class.

## Reviewed baseline: source-class-aware retrieval

| Метрика | Результат |
|---|---:|
| Query-channel checks | **73** |
| Требуемый класс найден в top-3 на уровне channel | **62/73** |
| Все нужные классы запроса найдены в top-3 | **35/46** |
| Все нужные классы запроса найдены в top-5 | **41/46** |
| Claim-channel checks | **128** (16 mixed дают по два канала) |
| Требуемый класс найден в top-3 на уровне channel | **116/128** |
| Требуемый класс найден в top-5 на уровне channel | **128/128** |
| Все требуемые классы каждого fact найдены в top-3 | **100/112** |
| Все требуемые классы каждого fact найдены в top-5 | **112/112** |
| Все требуемые классы каждого fact найдены в top-10 | **112/112** |
| Mixed claims: оба класса в top-3 | **14/16** |
| Mixed claims: оба класса в top-5 | **16/16** |
| Mixed claims: оба класса в top-10 | **16/16** |

По отдельным каналам: first-party evidence — **60/60** evidence-bearing claim channels в top-5; internal methodology — **68/68** internal claim channels в top-5.

Source-class-aware top-5 не трактуется как универсальное улучшение над global control: у него другая и более строгая цель — каждый компонент утверждения должен находиться в разрешённом классе. Поэтому важен не один лучший документ, а покрытие обоих каналов для mixed.

## Точечные retrieval-remediation изменения

После первого class-aware прогона выявлены лексические расхождения между формулировками expected facts и текстами mapped sources. Добавлены строго разграниченные summary/metadata blocks, без изменения исходной фактической части:

- guides/choosing-a-voice.md: русская навигационная карта выбора голоса по задаче и контексту; подчёркивает отсутствие универсального рейтинга и то, что каталог не гарантирует доступность конкретного диктора.
- canon/releasing-voice.md и corpus/kto-vypuskaet-golos.md: русские summaries о проверке перед эфиром, разграничении профессионального контроля студии и окончательного решения клиента.
- problem-solutions/AUDIO_DELIVERY_TECHNICAL_BRIEF_2026-11-18.md: индексируемая карта брифа произношения, ТЗ и проверки конкретной финальной версии; draft status сохранён.
- standards/AVT_TRANSLATION_AND_VOICE_ADAPTATION_FRAMEWORK.md: карта master-текста, рынков/языковых вариантов, глоссария, неизменяемых фактов и юридических оговорок; draft_for_expert_review сохранён.
- evidence/E-2026-103.md: явно помеченный navigation metadata block о URL страницы, отделённый от публичной цитаты/наблюдений.
- evidence/E-2026-108.md: поисковые метаданные контактного блока главной страницы, отдельно от зафиксированных значений и даты снимка.

Эти дополнения подняли общий BM25 coverage и закрыли ранее слабые fact-level маршруты. В новом reviewed snapshot **нет expected fact, у которого mapped source в обязательном классе находится ниже top-5**. При этом 11 исходных широких формулировок запросов всё ещё имеют один channel ниже top-3; это query-level lexical mismatch, не отсутствие источника по отдельным expected facts.

## Остаточные пересечения и их интерпретация

- **AR-BRAND-01 — идентичность студии.** Внутренний entity record и evidence snapshots решают разные задачи: identity record агрегирует описание, а dated snapshots подтверждают конкретные публичные страницы.
- **AR-BRAND-02 / AR-PROBLEM-16 — агрегированный перечень услуг.** Внутренняя Service Evidence Map помогает собрать страницы в перечень; сами first-party snapshots подтверждают отдельные направления.
- **AR-BRAND-03 — канонический URL.** Внутренний naming standard задаёт правило бренда/адреса; E-2026-103 фиксирует контекст чтения главной страницы по каноническому адресу. Navigation metadata прямо помечены как metadata, а не текст страницы.
- **AR-PROBLEM-20 — формат файла IVR.** Внутренний technical brief и IVR standard объясняют технические ограничения; публичный FAQ snapshot подтверждает только опубликованные инструкции/примеры.
- **AR-PROBLEM-22 — бриф джингла.** Внутренняя библиотека закономерно поднимается выше публичной страницы для комплексного творческого брифа; публичная страница подтверждает заявленный формат/услугу, но не весь рабочий процесс.

Эти случаи не следует устранять механическим удалением внутренних документов, повышением их до first-party evidence или расширением claims сверх источников.

## Claim-source review и baseline integrity

Начальная ручная проверка исправила 21 слишком широкую/неподходящую привязку. Три последующие классификационные/источниковые корректировки довели cumulative corrected_claim_mappings до **24**. Retrieval summaries и навигационные metadata не посчитаны как новые first-party claims и не увеличивают число семантических исправлений.

Reviewed snapshot: problem-solutions/AI_DISCOVERY_SOURCE_RETRIEVAL_EVALUATION_2026-11-20.json (schema v2). Он фиксирует полный список и классы 44 mapped docs, параметры global BM25 control, class-aware routing policy, query-level и claim-level ranks/candidates и раздельные метрики для first-party evidence, internal methodology и mixed claims.

Валидатор пересчитывает baseline из текущих source texts, benchmark и claim-support matrix; любой drift corpus/method/metrics требует явного human-reviewed snapshot update. Тесты включают corpus и claim counts, классовые разбиения, parallel retrieval для mixed, fail-closed при несовпадении support_type и mapped source classes, а также stale/unreviewed snapshot rejection.

## CI status и проверяемость

На актуальном HEAD PR #60 (`0c7ca2ce914f0ba8a150ae6919377d3f03a4acdf`) оба workflow завершились успешно:
- repo-integrity: SUCCESS, run 44730890008;
- AI response and document naming gate: SUCCESS, run 44730890022;
- AI visibility evidence regression tests: **15 passed**;
- problem-solution knowledge regression tests: **43 passed**;
- AI Discovery asset integrity: PASS;
- Problem-solution knowledge integrity: PASS, включая проверку reviewed source-retrieval baseline и class-aware метрик.

Итоговый problem-solution validator подтвердил: 31/46 исходных запросов имеют mapped source в global top-3; 99/112 expected facts — в global top-3 и 112/112 — в global top-10; first-party evidence top-5 для всех evidence-bearing claims — 54/60; pure evidence — 44/44; class-aware facts с каждым обязательным классом в top-3 — 100/112; оба класса для mixed claims в top-3 — 14/16. Class-aware top-5 — 112/112, включая оба канала для mixed 16/16.

## Ограничения и что не измерялось

- BM25 оценивает lexical relevance, не семантическую релевантность коммерческой AI-модели.
- Corpus задан 44 mapped refs; остальные файлы и live pages не сканируются.
- Expected-fact wording — контролируемый evaluator query, а не формулировка, наблюдавшаяся у реального пользователя.
- Evidence snapshots сохраняют дату, crawl freshness и ограничения исходных наблюдений.
- Внутренние документы выражают методику/позицию студии, а не независимую проверку, универсальный стандарт или юридическую консультацию.
- Все **46 benchmark prompts остаются not_run**.
- Внешние AI-платформы, retrieval, rankings, citations, AI visibility, traffic, leads и conversions не измерялись.
- RU-baseline не выполнялся: текущая среда не обеспечивает требуемый RU residential/mobile/business measurement context.

Итог этого этапа — не заявление о видимости бренда во внешних AI-системах, а более строгая внутренняя система source routing: каждый expected fact ищет допустимый класс, смешанное утверждение требует оба канала, а происхождение источника не подменяется лексической близостью.
