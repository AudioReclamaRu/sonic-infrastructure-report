---
type: ai-discovery-source-retrieval-audit
date: 2026-11-20
lang: ru
status: source_class_aware_baseline_reviewed
brand: "Аудио-Реклама•ru"
related:
  - ../tools/ai_discovery_source_retrieval.py
  - ../problem-solutions/AI_DISCOVERY_CLAIM_SUPPORT_MATRIX_2026-11-20.json
  - ../problem-solutions/AI_DISCOVERY_SOURCE_RETRIEVAL_EVALUATION_2026-11-20.json
  - ../research/AI_DISCOVERY_CLAIM_SOURCE_SEMANTIC_AUDIT_2026-11-20.md
---

# Retrieval первичных источников и внутренней методики — 20.11.2026

## Объём и метод

Проверяется retrieval для 46 запросов фиксированного RU benchmark и 112 expected facts. Кандидатный корпус ограничен **44 уникальными документами**, прямо указанными в claim-support matrix. Используется детерминированный BM25 (k1=1.2, b=0.75), тот же русско-английский токенизатор и лёгкая нормализация слов, что и в answer-pack diagnostic.

Выполнены два взаимно сохраняемых режима:

1. **Global control:** исходный вопрос и каждый expected fact ранжируются по единому корпусу всех 44 mapped sources.
2. **Source-class-aware:** retrieval ограничивается допустимым классом источника, указанным в support_type. Смешанные claims ищутся в двух независимых каналах, а оба результата сохраняются. Никакого искусственного объединения двух рангов в один документ не происходит.

## Классы и routing policy

| Класс | Допустимый корпус | Expected facts |
|---|---|---:|
| first_party_evidence | Датированные first-party snapshots в evidence/ | 45 |
| internal_methodology | Внутренние методики, entity/canon/standards/guides и технические документы | 52 |
| mixed | Оба класса одновременно; каждый канал должен найти свой mapped source | 15 |

Корпус: **19 first-party evidence документов + 25 internal-methodology документов**.

Уровень маршрутизации 46 исходных вопросов: 12 evidence-only, 6 internal-methodology-only, 28 parallel (оба класса).

Для mixed нельзя считать внутренний методический документ заменой публичному evidence или наоборот. Первый подтверждает только то, что действительно зафиксировано в публичном snapshot; второй — внутреннюю методику, позицию или рабочий подход.

## Reviewed baseline: global control

| Метрика | Результат |
|---|---:|
| Запросы с mapped source в top-1 | **15/46** |
| Запросы с mapped source в top-3 | **30/46** |
| Запросы с mapped source в top-5 | **36/46** |
| Expected facts с mapped source в top-1 | **63/112** |
| Expected facts с mapped source в top-3 | **97/112** |
| Expected facts с mapped source в top-5 | **107/112** |
| Expected facts с mapped source в top-10 | **110/112** |
| Все facts одного запроса имеют mapped source в top-3 | **33/46** |
| Все facts одного запроса имеют mapped source в top-5 | **41/46** |
| Все facts одного запроса имеют mapped source в top-10 | **44/46** |
| Pure first-party claims: evidence в top-5 | **44/45** |
| Pure first-party claims: evidence в top-10 | **45/45** |
| Mixed claims: first-party evidence в top-5 (отдельный evidence-rank) | **10/15** |

Global control остаётся диагностикой широкой лексической близости. Высокий ранг в общем корпусе сам по себе не гарантирует, что найден документ правильного epistemic/source class.

## Reviewed baseline: source-class-aware retrieval

| Метрика | Результат |
|---|---:|
| Query-channel checks | **74** |
| Требуемый класс найден в top-1 на уровне channel | **33/74** |
| Требуемый класс найден в top-3 на уровне channel | **59/74** |
| Требуемый класс найден в top-5 на уровне channel | **65/74** |
| Все нужные классы запроса найдены в top-1 | **12/46** |
| Все нужные классы запроса найдены в top-3 | **31/46** |
| Все нужные классы запроса найдены в top-5 | **37/46** |
| Claim-channel checks | **127** (15 mixed дают по два канала) |
| Требуемый класс найден в top-1 на уровне claim-channel | **86/127** |
| Требуемый класс найден в top-3 на уровне claim-channel | **114/127** |
| Требуемый класс найден в top-5 на уровне claim-channel | **123/127** |
| Требуемый класс найден в top-10 на уровне claim-channel | **124/127** |
| Все обязательные классы каждого fact найдены в top-1 | **73/112** |
| Все обязательные классы каждого fact найдены в top-3 | **99/112** |
| Все обязательные классы каждого fact найдены в top-5 | **108/112** |
| Все обязательные классы каждого fact найдены в top-10 | **109/112** |
| Mixed claims: оба класса в top-1 | **4/15** |
| Mixed claims: оба класса в top-3 | **12/15** |
| Mixed claims: оба класса в top-5 | **14/15** |
| Mixed claims: оба класса в top-10 | **14/15** |

По отдельным каналам:
- first-party evidence: 60 claim-channel checks; mapped evidence в top-5 для **60/60**;
- internal methodology: 67 claim-channel checks; mapped methodology в top-5 для **63/67**, в top-10 для **64/67**.

Source-class-aware top-5 не трактуется как универсальное улучшение над global control: у него другая и более строгая цель — каждый компонент утверждения должен находиться в разрешённом классе. Поэтому важен не один лучший документ, а покрытие обоих каналов для mixed.

## Точечные retrieval-remediation изменения

В корпус добавлены строго разграниченные summary/metadata blocks, не выдаваемые за первичные утверждения страницы:

- guides/choosing-a-voice.md: русская навигационная карта выбора голоса по задаче и контексту; подчёркивает отсутствие универсального рейтинга и то, что каталог не гарантирует доступность конкретного диктора.
- canon/releasing-voice.md и corpus/kto-vypuskaet-golos.md: русские summaries о проверке перед эфиром, разграничении профессионального контроля студии и окончательного решения клиента.
- problem-solutions/AUDIO_DELIVERY_TECHNICAL_BRIEF_2026-11-18.md: индексируемая карта брифа произношения, ТЗ и проверки конкретной финальной версии; draft status сохранён.
- standards/AVT_TRANSLATION_AND_VOICE_ADAPTATION_FRAMEWORK.md: карта master-текста, рынков/языковых вариантов, глоссария, неизменяемых фактов и юридических оговорок; draft_for_expert_review сохранён.
- evidence/E-2026-103.md: явно помеченный navigation metadata block о URL страницы, отделённый от публичной цитаты/наблюдений.
- evidence/E-2026-108.md: поисковые метаданные контактного блока главной страницы, отдельно от зафиксированных значений и даты снимка.

Ни один retrieval summary не считается новым first-party claim и не повышает внутреннюю методику до публичного evidence.

## Остаточные пересечения и их интерпретация

- **AR-BRAND-01 / AR-BRAND-02 — identity и перечень услуг.** Entity record агрегирует описание; отдельные snapshots подтверждают каждую публичную страницу/услугу. Для видеопродакшна нужен E-107, для озвучивания видео — E-096, для озвучивания презентаций — E-112.
- **AR-BRAND-03 — канонический URL.** Naming standard задаёт внутреннее правило бренда/адреса; E-2026-103 и E-2026-108 фиксируют официальный homepage в dated snapshots. Navigation metadata не цитируются как текст самой страницы.
- **AR-BRAND-05/06/07 — счётчики каталога.** E-097 и E-109 фиксируют 622 и 620 одновременно на главной, 62 языка и 309 в русском фильтре; E-104 объясняет область каталожной страницы. Старое значение 308 с неустановленной свежестью не объясняет расхождение и остаётся отдельным наблюдением.
- **AR-PROBLEM-20 — формат файла IVR.** E-094 подтверждает опубликованные FAQ-примеры; technical brief и IVR standard объясняют ограничения, но не заменяют спецификацию принимающей АТС.
- **AR-PROBLEM-22 / AR-PROBLEM-23 — творческий бриф и права.** Внутренняя библиотека даёт рекомендации; E-100/E-105 подтверждают публичное наличие направлений, но не полный рабочий процесс и не объём прав на стороннее произведение.

Эти случаи не следует устранять механическим удалением внутренних документов, повышением их до first-party evidence или расширением claims сверх источников.

## Claim-source review и baseline integrity

Начальная ручная проверка исправила 21 слишком широкую/неподходящую привязку. Последующие классификационные/источниковые корректировки довели cumulative corrected_claim_mappings до **24**. В отдельных sentence units source class может отличаться от класса целого expected fact; для них нужен отдельный unit-level disposition, а не дублирование обоих каналов на каждой части предложения.

Reviewed snapshot: problem-solutions/AI_DISCOVERY_SOURCE_RETRIEVAL_EVALUATION_2026-11-20.json (schema v2). Он фиксирует список и классы 44 mapped docs, параметры global BM25 control, class-aware routing policy, query-level и claim-level ranks/candidates и раздельные метрики.

Валидатор пересчитывает baseline из текущих source texts, benchmark и claim-support matrix; любой drift corpus/method/metrics требует явного human-reviewed snapshot update. Тесты включают corpus и claim counts, классовые разбиения, parallel retrieval для mixed, fail-closed при несовпадении support_type и mapped source classes, а также stale/unreviewed snapshot rejection.

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
