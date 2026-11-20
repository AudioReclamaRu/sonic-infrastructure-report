---
type: ai-discovery-answer-support-candidate-audit
date: 2026-11-20
lang: ru
status: unit_level_dispositions_applied_ci_pass
brand: "Аудио-Реклама•ru"
related:
  - ../tools/ai_discovery_answer_support.py
  - ../problem-solutions/AI_DISCOVERY_CLAIM_SUPPORT_MATRIX_2026-11-20.json
  - ../problem-solutions/AI_DISCOVERY_ANSWER_COVERAGE_AUDIT_2026-11-20.json
  - ../problem-solutions/AI_DISCOVERY_ANSWER_UNIT_DISPOSITIONS_2026-11-20.json
  - ../research/AI_DISCOVERY_ANSWER_SUPPORT_MANUAL_REVIEW_2026-11-20.md
---

# Candidate-аудит полноты опоры ответов — 20.11.2026

## Что проверяется

Детерминированный retrieval разбивает 46 ответных маршрутов на sentence/semicolon units. Первоначальный candidate matcher подбирает ближайший expected fact по BM25, но теперь **не переносит автоматически support type целого fact на фразу**, если для точной пары `unit_id + answer_text` есть ручное disposition.

Добавлен asset `AI_DISCOVERY_ANSWER_UNIT_DISPOSITIONS_2026-11-20.json`. Он задаёт для приоритетных фрагментов:
- тип самой фразы;
- собственный список требуемых классов источников;
- конкретные mapped source refs;
- дату и краткое обоснование ручной классификации.

Движок проверяет точное совпадение ID, текста, маршрута и heading; существование каждого source ref в mapped corpus; соответствие классов реальным путям; допустимость классов для категории. Старый или изменившийся unit ID/text приводит к fail-closed ошибке, а не к применению устаревшей ручной привязки.

## Unit-level taxonomy

| Категория | Правило источников |
|---|---|
| `first_party_fact` | Только датированные first-party evidence |
| `internal_recommendation` | Только internal methodology |
| `scope_limitation` | Явно выбранный класс или оба класса — по содержанию ограничения |
| `source_freshness_note` | Обязателен first-party snapshot; внутренний журнал может добавлять контекст |
| `mixed_assertion` | Одновременно first-party evidence и internal methodology |
| `general_legal_caution` | Общее предостережение без утверждения о компании; источниковый retrieval не требуется |
| `discourse_only` | Навигационный/дискурсивный фрагмент без самостоятельного факта; retrieval не требуется |

Для неразмеченных units прежний BM25 whole-fact routing сохраняется как fallback. Поэтому система не притворяется, что все 285 фраз уже вручную разобраны.

## Последний CI baseline

**CI HEAD:** `7de3279fa57cbd00fd3f7b1aa0959ae9afecdc7b`.

| Метрика | Результат |
|---|---:|
| Benchmark queries | 46 |
| Parsed answer units | 285 |
| Units with lexical expected-fact candidate | 236 |
| Units without lexical expected-fact candidate | 44 |
| Short discourse preambles | 5 |
| Candidate units, required classes in top-3 | 200/236 |
| Candidate units, required classes in top-5 | 217/236 |
| Candidate units, required classes in top-10 | 228/236 |
| Manually dispositioned priority units | **79/79** |
| Unclassified priority units | **0** |
| Manual dispositions with retrieval channels | 76 |
| Manual dispositions without retrieval | 3 |
| Manually dispositioned units with source rank below top-5 | 26 |

Категории 79 disposition records: 17 `first_party_fact`, 31 `internal_recommendation`, 16 `scope_limitation`, 11 `source_freshness_note`, 2 `general_legal_caution`, 1 `mixed_assertion`, 1 `discourse_only`.

44 units без lexical expected-fact candidate не объявляются неподтверждёнными: у них есть отдельная ручная привязка. 35 weak whole-fact candidates тоже получили собственный unit-level класс и источники. Поэтому **unclassified priority = 0**. При этом 26 manually dispositioned units всё ещё имеют mapped source ниже top-5 по lexical ranking. Их привязка не отбрасывается автоматически: низкий BM25 rank не опровергает содержательную релевантность, но показывает, где vocabulary/source summary нуждается в дальнейшем улучшении.

## Как работает fallback и что сохраняется

- Для вручную разобранного unit effective `required_source_classes` берутся из disposition, а исходный `candidate_fact_support_type` остаётся в диагностике отдельно.
- Для unit без disposition система сохраняет прежний candidate fact, его support type и ранги.
- Для mixed unit оба канала остаются раздельными; first-party source не засчитывается вместо internal methodology и наоборот.
- Для general legal caution/discourse unit система не выдумывает источник и не делает вид, что такой фрагмент является публичным фактом о студии.
- Все 285 units остаются в поле человеческого контроля; ручное disposition закрывает только точные 79 фрагментов.

## Регрессионные проверки и CI

Добавлены тесты:
1. unit-level disposition может заменить whole-fact `mixed` на точный `first_party_evidence` канал, сохранив исходный candidate support type как отдельную диагностику;
2. общий legal caution может явно обходиться без retrieval и без фиктивного source ref;
3. устаревший exact answer text приводит к fail-closed ошибке.

CI на HEAD `7de3279fa57cbd00fd3f7b1aa0959ae9afecdc7b`:
- `repo-integrity`: SUCCESS, run `44742896731`;
- `AI response and document naming gate`: SUCCESS, run `44742896776`;
- `AI visibility benchmark and evidence regression tests`: **15 passed**;
- `Problem-solution knowledge regression tests`: **51 passed**;
- Problem-solution knowledge validator: PASS; 112 fact mappings, 44 source documents, 46 reviewed answer texts and 54 forbidden-claim checks.

## Ограничения

- BM25 rank — лексическая диагностика, не semantic entailment и не доказательство корректности ответа.
- Точный manual disposition действует только на конкретную пару unit ID и текст. При редактуре answer pack схема требует повторного рассмотрения соответствующей записи.
- Для остальных 206 units disposition ещё не задан; top-K кандидат не становится автоматически семантически проверенным.
- Все 46 внешних benchmark prompts остаются `not_run`; ChatGPT, Gemini, Perplexity и другие платформы не тестировались.

**Итог:** source class теперь назначается уровню фразы там, где есть проверенная ручная классификация. Whole-fact fallback сохранён для неразмеченных фрагментов; 79 текущих предупреждений имеют явный disposition, 0 приоритетных units остаются неразобранными.
