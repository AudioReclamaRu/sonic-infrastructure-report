---
type: ai-discovery-answer-support-candidate-audit
date: 2026-11-20
lang: ru
status: full_unit_level_dispositions_ci_pass
brand: "Аудио-Реклама•ru"
related:
  - ../tools/ai_discovery_answer_support.py
  - ../problem-solutions/AI_DISCOVERY_CLAIM_SUPPORT_MATRIX_2026-11-20.json
  - ../problem-solutions/AI_DISCOVERY_ANSWER_COVERAGE_AUDIT_2026-11-20.json
  - ../problem-solutions/AI_DISCOVERY_ANSWER_UNIT_DISPOSITIONS_2026-11-20.json
  - ../research/AI_DISCOVERY_ANSWER_SUPPORT_MANUAL_REVIEW_2026-11-20.md
---

# Unit-level answer support audit — 20.11.2026

## Что проверяется

Детерминированный retrieval разбивает 46 ответных маршрутов на **285 sentence/semicolon units**. Для каждого фрагмента определяется собственная категория и допустимый источник. Если есть точный ручной disposition по `unit_id + answer_text`, retrieval использует именно его, а не автоматически наследует `support_type` целого expected fact.

Полный asset: `problem-solutions/AI_DISCOVERY_ANSWER_UNIT_DISPOSITIONS_2026-11-20.json`. Каждая запись содержит:
- точный unit ID, benchmark query ID, файл и heading;
- исходный текст фразы;
- category и subtype, если применимо;
- требуемые source classes и конкретные mapped refs;
- дату, статус и обоснование ручной классификации.

Валидатор сверяет текст, маршрут, файл и heading; проверяет существование source refs в claim-support corpus, реальный source class каждого пути и правила категории. При заявленном полном покрытии любой пропуск или text drift приводит к fail-closed ошибке.

## Unit-level taxonomy и результаты разметки

| Категория | Количество | Правило маршрутизации |
|---|---:|---|
| `first_party_fact` | 77 | Только first-party evidence |
| `internal_recommendation` | 115 | Только internal methodology |
| `scope_limitation` | 58 | Явно выбранный класс/классы, подтверждающие границу |
| `source_freshness_note` | 22 | Обязателен first-party snapshot; внутренний журнал может добавлять контекст |
| `mixed_assertion` | 3 | Оба класса одновременно |
| `general_legal_caution` | 4 | Общее предостережение без company-specific fact; retrieval не требуется |
| `discourse_only` | 6 | Короткий ответ/дискурсивный фрагмент без самостоятельного факта; retrieval не требуется |
| **Итого** | **285** | Полное покрытие извлечённых answer units |

Из 285 единиц **275** имеют source retrieval channels; **10** не требуют выдавать себя за утверждения о компании или искать к ним фиктивные источники.

79 прежних приоритетных предупреждений (44 unmatched и 35 weak) сохранены и встроены в этот полный слой. Ещё 206 единиц получили отдельную ручную классификацию и источниковые границы.

## Последний CI baseline

**HEAD:** `f0416131adfc1c7e222e582d5f99718b03e1e33d`.

| Метрика | Результат |
|---|---:|
| Benchmark queries | 46 |
| Parsed answer units | **285** |
| Units с lexical expected-fact candidate | 236 |
| Units без lexical expected-fact candidate | 44 |
| Короткие discourse preambles | 5 |
| Manual dispositions | **285/285** |
| Units, которым требуется retrieval | **275** |
| Units без retrieval channel | **10** |
| Unclassified priority units | **0** |
| Manual dispositions с mapped source ниже top-5 | **52** |

После применения unit-level source classes retrieval находит:
- все требуемые классы в top-3 для **165** candidate units;
- все требуемые классы в top-5 для **189** candidate units;
- все требуемые классы в top-10 для **211** candidate units.

Отдельные counts отражают лексическое ранжирование mapped refs. Они не доказывают, что источник семантически следует из всей фразы. 52 низкоранговых назначения остаются в диагностике как vocabulary/retrieval weak spots; сами по себе они не отменяют ручную привязку.

## Как работает fallback и что сохраняется

- Для вручную размеченного unit effective `required_source_classes` берутся из exact disposition.
- Исходный expected-fact candidate, его support type и source ranks сохраняются отдельно для диагностики.
- Для единицы без disposition прежний whole-fact BM25 fallback остаётся доступен, но complete-coverage asset на текущем branch требует disposition для всех 285 извлечённых units.
- Mixed unit требует оба канала; публичное evidence не заменяется внутренней методикой и наоборот.
- General legal caution и discourse-only фрагменты не получают фиктивных source refs.
- Изменение текста, ID, файла или heading делает старое disposition недействительным и останавливает validation.

## CI и регрессионные проверки

На HEAD `f0416131adfc1c7e222e582d5f99718b03e1e33d`:
- `repo-integrity`: SUCCESS, run `44746429192`;
- `AI response and document naming gate`: SUCCESS, run `44746429128`;
- `AI visibility benchmark and evidence regression tests`: **15 passed**;
- `Problem-solution knowledge regression tests`: **52 passed**;
- Problem-solution knowledge validator: PASS; 112 fact mappings, 44 source documents, 46 reviewed answer texts and 54 forbidden-claim checks.

Проверяются override whole-fact classes на unit-level classes, mixed retrieval, legal/discourse no-retrieval, source-class/ref mismatches, exact text drift и неполнота asset, заявленного как полный.

## Ограничения

- BM25 — лексическая диагностика, не semantic entailment и не proof of truth.
- Ручная классификация охватывает точные фразы в текущих answer packs; при их редактуре записи должны быть повторно проверены.
- Top-K — навигационный сигнал. Даже высокий rank не заменяет чтение источника и смысловую оценку.
- Все **46 внешних benchmark prompts остаются `not_run`**. ChatGPT, Gemini, Perplexity и другие платформы не тестировались.

**Итог:** unit-level source classes назначены всем 285 извлечённым фрагментам, 0 фрагментов остались без disposition. Полная семантическая проверка коммерческими AI-платформами не выполнялась.
