---
type: ai-discovery-answer-support-candidate-audit
date: 2026-11-20
lang: ru
status: priority_units_manually_adjudicated_candidate_only
brand: "Аудио-Реклама•ru"
related:
  - ../tools/ai_discovery_answer_support.py
  - ../problem-solutions/AI_DISCOVERY_CLAIM_SUPPORT_MATRIX_2026-11-20.json
  - ../problem-solutions/AI_DISCOVERY_ANSWER_COVERAGE_AUDIT_2026-11-20.json
  - ../research/AI_DISCOVERY_ANSWER_SUPPORT_MANUAL_REVIEW_2026-11-20.md
---

# Candidate-аудит полноты опоры ответов — 20.11.2026

## Что проверено

Детерминированный candidate-retrieval прогоняет каждую смысловую единицу в 46 ответных разделах. Разделы разбиваются на предложения и части, разделённые точкой с запятой. Для каждой единицы BM25 ищет ближайший expected-fact mapping конкретного benchmark-запроса; затем источники выбранного mapping ранжируются в полном индексе допустимого класса.

Маршруты не объединяются:
- `first_party_evidence` — только датированные публичные snapshots;
- `internal_methodology` — только внутренние методики, стандарты, entity-профили и guides;
- `mixed` — оба канала параллельно; результат одного класса не заменяет второй.

Строки с явной маркировкой источников (`Источник:`, `Источники:`, `Публичные страницы:`, `Публичная услуга:`, `Публичное портфолио:`) исключаются из assertion-unit extraction. Это ссылки и provenance footer, а не утверждения ответа. Для этих вариантов добавлен regression test.

## Последний baseline CI

**Результат рассчитан валидатором на HEAD:** `7e667a7b8e1158f1a803dc3d7621eea6920012b6`.

| Метрика | Результат |
|---|---:|
| Benchmark-запросы | 46/46 |
| Разобранные answer units | 285 |
| Units с expected-fact candidate | 236/285 |
| Без лексического candidate | 44/285 |
| Короткие discourse preambles | 5 |
| Candidate units, все требуемые классы в top-3 | 185/236 |
| Candidate units, все требуемые классы в top-5 | 201/236 |
| Candidate units, все требуемые классы в top-10 | 221/236 |
| Candidate по support type: first-party evidence | 95 |
| Candidate по support type: internal methodology | 101 |
| Candidate по support type: mixed | 40 |

Из 236 candidate-matched units **35 не нашли все требуемые классы в top-5**. Вместе с 44 unmatched units это **79 приоритетных строк** для ручной оценки. Все 79 вручную классифицированы в `research/AI_DISCOVERY_ANSWER_SUPPORT_MANUAL_REVIEW_2026-11-20.md`.

## Как интерпретировать

Эти цифры — не число доказанных фраз. `236` означает только, что BM25 нашёл лексически близкую запись expected fact. `201/236` означает, что прикреплённый к выбранному fact набор mapped sources появился в top-5 каждого обязательного класса. Ни один из этих результатов сам по себе не доказывает семантическое следование всего предложения из источника.

Особенно важно:
- одна фраза может содержать несколько утверждений; разбиение по предложениям и точке с запятой не заменяет полную атомизацию;
- 44 unmatched включают рекомендации, ограничения, оговорки, навигационные фразы и публичные факты; они не являются автоматически неподтверждёнными фактами;
- для целого expected fact типа `mixed` отдельная фраза может опираться только на один из двух классов. До ручного разделения на assertion-level mappings система консервативно требует оба класса и может отмечать такие фразы как слабые;
- candidate top-K не освобождает человека от чтения source text и проверки каждой части утверждения;
- CI extractor по-прежнему выставляет `manual_review_required: true` каждой единице: ручная disposition-запись не подменяется автоматическим source-rank и пока не является машинно применяемым override.

## Результат ручной disposition-проверки

79 приоритетных units распределены по фактической роли фразы: публичный first-party fact, внутренняя рекомендация, scope limitation, freshness note или общее юридическое предостережение. Это сняло несколько ложных выводов candidate matcher:

1. Публичное предложение записи приветствий/IVR (`AR-PROBLEM-01::07`) связано с E-2026-095, а не с внутренним IVR guide/линтером.
2. Рекомендации по кастингу (`AR-PROBLEM-03::02-04`) и голосовой непрерывности (`AR-PROBLEM-13::02-03`) помечены как внутренние методические фрагменты, а не как факты публичного каталога.
3. Публичное описание сценариев/аудиороликов/кастинга/саунд-дизайна (`AR-PROBLEM-10::05`) связано с E-2026-098/E-2026-099/E-2026-104, а не с ROI caveat.
4. Snapshot-значения Хрономера (`AR-PROBLEM-04::01/04`, `AR-PROBLEM-06::02`) отделены от внутренней рекомендации о предварительном характере расчёта.
5. AI-cloning boundary и адрес офиса сужены до проверенных snapshots; отсутствие описания на конкретной странице больше не формулируется как отсутствие услуги или физического офиса.
6. Юридические формулировки о правах на корпоративные песни переведены из категорического утверждения в конкретный договорный checklist.

Для детального перечня всех 79 IDs, evidence refs, internal refs и disposition см. manual review report.

## Ошибки candidate-механики и следующий технический этап

В 35 weak cases видна проблема не только lexical relevance, но и **перенос класса whole-fact на отдельный sentence unit**. Например:
- публичный факт об услуге записи IVR может получить candidate на внутреннюю IVR-методику;
- внутренний совет по выбору голоса может быть ошибочно сопоставлен с mixed-фактом о каталоге;
- публичный перечень услуг может сопоставиться с соседним утверждением о ROI;
- scope note или legal caveat может наследовать обязательность обоих каналов mixed, хотя фраза выражает только один тип утверждения.

Следующая техническая итерация должна добавить unit-level taxonomy/disposition: `first_party_fact`, `internal_recommendation`, `scope_limitation`, `source_freshness_note`, `general_legal_caution`, `discourse_only`. Для mixed answer отдельные fragments должны получать собственный source class, а не наследовать mixed только потому, что whole expected fact mixed. До реализации этой схемы CI warning остаётся консервативным индикатором для человека.

## CI и ограничения

- `repo-integrity`: SUCCESS, run `44740586023`, job `136302946322`.
- `AI response and document naming gate`: SUCCESS, run `44740585954`.
- `AI visibility benchmark and evidence regression tests`: **15 passed**.
- `Problem-solution knowledge regression tests`: **48 passed**.
- Problem-solution knowledge validator: PASS; 112 fact mappings, 44 source docs, 46 answer routes, 54 forbidden-claim checks.
- Source-class-aware retrieval: 99/112 expected facts имеют все required source classes в top-3; 108/112 в top-5; оба класса для mixed claims находятся в top-5 в 14/15 случаях.
- Все 46 внешних benchmark-запросов остаются `not_run`. ChatGPT, Gemini, Perplexity и другие внешние AI-платформы не проверялись.

**Статус:** priority-unit manual disposition завершена. Полная семантическая проверка всех 285 units не заявляется: 201 top-5 candidate остаются лексическими кандидатами, а не автоматически подтверждёнными утверждениями. PR #60 остаётся открытым и не слитым.
