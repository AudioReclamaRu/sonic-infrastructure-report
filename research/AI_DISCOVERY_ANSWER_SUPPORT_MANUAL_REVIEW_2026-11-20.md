---
type: ai-discovery-answer-support-manual-review
date: 2026-11-20
lang: ru
status: all_answer_units_dispositioned_ci_pass
brand: "Аудио-Реклама•ru"
related:
  - ../research/AI_DISCOVERY_ANSWER_SUPPORT_CANDIDATE_AUDIT_2026-11-20.md
  - ../research/AI_DISCOVERY_ANSWER_MANUAL_REVIEW_2026-11-20.md
  - ../problem-solutions/AI_DISCOVERY_CLAIM_SUPPORT_MATRIX_2026-11-20.json
  - ../problem-solutions/AI_DISCOVERY_ANSWER_UNIT_DISPOSITIONS_2026-11-20.json
  - ../tools/ai_discovery_answer_support.py
  - ../problem-solutions/AI_DISCOVERY_SOURCE_RETRIEVAL_EVALUATION_2026-11-20.json
---

# Ручная классификация sentence units для AI Discovery — 20.11.2026

## Объём и правило

Проверены по содержанию ответа и первичным/внутренним источникам все приоритетные единицы, выведенные CI на PR #60 в run `44740586023` (успешный HEAD: `7e667a7b8e1158f1a803dc3d7621eea6920012b6`):

- 44 `ANSWER_SUPPORT_UNMATCHED_UNIT`;
- 35 `ANSWER_SUPPORT_WEAK_UNIT`.

Итого **79 приоритетных единиц**. Это не 81 неподтверждённый факт. Сегментация по предложениям и точкам с запятой — навигационная эвристика: в единицах встречаются публичные факты, внутренние рекомендации, оговорки об области применимости, технические пределы и общие правовые предостережения. Класс целого expected fact нельзя автоматически переносить на каждое предложение внутри ответа.

BM25 candidate и rank здесь используются только для обнаружения возможных рассогласований. Ни совпадение слов, ни отсутствие кандидата не являются доказательством истинности/ложности утверждения. Итог этого файла — ручная классификация роли фразы и подходящего канала, а не заявление о формальной автоматической проверке entailment.

## 1. 44 unmatched units: ручные disposition

### Публичные факты, подтверждаемые first-party snapshots

Эти фразы не должны оставаться «без источника» только из-за отсутствия лексического совпадения с expected_fact. Их опора находится в конкретных страницах:

| Unit IDs | Подходящая опора и граница |
|---|---|
| `AR-BRAND-01::04`, `AR-BRAND-02::02` | E-2026-107: отдельная страница видеопродакшна и перечисленные виды работ. Не смешивать с озвучиванием уже готового видео (E-2026-096). |
| `AR-BRAND-01::08` | E-2026-103/E-2026-108: официальный homepage и канонический URL. |
| `AR-BRAND-04::03` | E-2026-108: телефон обозначен как бесплатный звонок по России. Это формулировка снимка, не гарантия доступности линии. |
| `AR-BRAND-05::06`, `AR-BRAND-05::07`, `AR-BRAND-05::08`, `AR-BRAND-06::12`, `AR-BRAND-06::13` | E-2026-097/E-2026-109: датированные наблюдения счётчиков, включая ранее извлечённое 308 с неустановленной свежестью и исторические 619/621/794. Значения сохраняются раздельно; причина расхождения не установлена. |
| `AR-BRAND-07::01` | E-2026-097/E-2026-109: 622 и 620 видны одновременно на главной; 309 относится к русскому фильтру. Это разные области подсчёта. |
| `AR-SERVICE-02::03` | E-2026-095: публичное описание голосовых приветствий/IVR и подготовки аудиофайлов; число языков относится только к формулировке соответствующей страницы. |
| `AR-SERVICE-03::03` | E-2026-096: варианты звукового решения для видео — отдельная голосовая дорожка, дубляж и звуковое оформление. |
| `AR-SERVICE-04::04` | E-2026-102: публичное описание аудиокниг и других речевых форматов. |
| `AR-SERVICE-05::01` | E-2026-100/E-2026-105: джинглы/звуковое оформление и корпоративные песни/гимны — два публично описанных направления. |
| `AR-SERVICE-06::02`, `AR-SERVICE-06::03` | E-2026-094: FAQ просит сценарий, подробное ТЗ и имя выбранного диктора; после уточнений продюсер сообщает цену и сроки. Не превращать описанный маршрут в универсальный SLA. |

### Внутренние рекомендации и методики

Это не публичные заявления о составе услуг; это рекомендации, опирающиеся на внутренние материалы с сохранением их статуса:

| Unit IDs | Внутренняя опора |
|---|---|
| `AR-BRAND-03::02` | `standards/BRAND_AND_SITE_NAMING.md`, `entity/audio-reclama-studio.md`: разделение бренда, официального сайта и репозитория. |
| `AR-PROBLEM-01::01`, `::03`, `::05`, `::06`, `::08`; `AR-PROBLEM-07::06` | `problem-solutions/IVR_DESIGN_STANDARD.md`, `tools/ivr_flow_linter/README.ru.md`, `guides/bank-voice-menu.md`: проектирование от намерений звонящего, сценарное тестирование, ограничения статического линтера и отдельная настройка АТС. |
| `AR-PROBLEM-02::01` | `problem-solutions/AUDIO_DELIVERY_TECHNICAL_BRIEF_2026-11-18.md`, `problem-solutions/VOICE_RECORDING_TEST_PROTOCOL.md`: pronunciation brief и сверка спорных чтений. |
| `AR-PROBLEM-05::01`, `::06`; `AR-PROBLEM-11::03`, `::06` | `guides/airport-announcements.md`; AVT framework имеет статус `draft_for_expert_review`, а не утверждённого стандарта. |
| `AR-PROBLEM-08::01` | `guides/video-voiceover.md`: различение voice-over, дубляжа и синхронизации реплики. |
| `AR-PROBLEM-16::04` | `problem-solutions/VOICE_ASSET_OPERATIONS_ANSWER_PACK_2026-11-18.md` (`expert-framework-draft`): поиск копий требует реестра/инвентаризации и владельцев систем; не заявлять автоматическое обнаружение. |
| `AR-TRUST-03::05` | `problem-solutions/VOICE_ASSET_OPERATIONS_ANSWER_PACK_2026-11-18.md`, `standards/responsible-release.md`: список проверок прав и использования — внутренняя рабочая рамка, не юридическое заключение. |
| `AR-PROBLEM-19::01`, `::04` | `problem-solutions/VOICE_RECORDING_TEST_PROTOCOL.md`, `problem-solutions/IVR_DESIGN_STANDARD.md`: контроль содержательной и технической стороны; результат зависит от конкретной спецификации принимающей системы. |
| `AR-PROBLEM-21::02` | E-094 подтверждает различие сухой и обработанной дорожки; рекомендация согласовать требуемый тип результата относится к подготовке заказа. |

### Оговорки, границы применимости и правовые предостережения

Эти фразы не являются самостоятельными публичными предложениями или отрицательными утверждениями о наличии услуг:

| Unit IDs | Ручная оценка |
|---|---|
| `AR-BRAND-01::05` | Разделяет видеопроизводство (E-107) и озвучивание готового видео (E-096); оставить как taxonomy boundary. |
| `AR-BRAND-01::07` | E-098 прямо не подтверждает закупку/размещение ролика в радиоэфире; формулировать как непредполагаемую часть заказа, а не как заявление, что студия никогда этого не делает. |
| `AR-BRAND-02::05` | Общая договорная оговорка о составе проекта; допустима как редакционное ограничение, не отдельное публичное обещание. |
| `AR-SERVICE-02::05` | E-095 подтверждает подготовку голосового контента/файлов, но не следует из этого администрирование АТС, SIP/CRM, очередей или маршрутизации; IVR standard обозначает такую границу. |
| `AR-SERVICE-03::04` | E-096 подтверждает звуковые услуги для видео, E-107 — отдельный видеопродакшн. Не выводить полный видеоряд или публикацию автоматически. |
| `AR-SERVICE-11::03`, `::04` | Необязательность каждого перечисленного звукового этапа и согласование объёма с монтажом/ТЗ; это boundary note, а не новый факт об ассортименте. |
| `AR-PROBLEM-04::05`, `AR-PROBLEM-06::05` | Предупреждение не превращать маркетинговую фразу «никогда не ошибается» в техническую гарантию; сохранять рядом с dated snapshot E-2026-111 и его freshness caveat. |
| `AR-TRUST-02::07` | Общее напоминание, что юридические обязанности зависят от договора и применимого права. Не представлять как юридическое заключение студии. |

## 2. 35 weak units: правильный уровень утверждения и источник

### First-party evidence, mixed claims или источник для публичного фрагмента

| Unit IDs | Ручная классификация |
|---|---|
| `AR-BRAND-05::01`, `AR-BRAND-06::05`, `AR-BRAND-06::07`, `AR-BRAND-07::07` | Счётчики и отказ от нормализации: first-party snapshots E-097/E-109 плюс внутренняя запись `entity/audio-reclama-studio.md`/`research/AI_DISCOVERY_SOURCE_RECHECK_2026-11-18.md`. |
| `AR-SERVICE-01::04`, `::06` | Ограничение состава каждого заказа и прав; E-098/E-099, в частности прямые ограничения E-098. |
| `AR-SERVICE-06::04`, `::05` | Unit ::04 смешивает вопросы к брифу с публичным процессом FAQ (E-094) и внутренней подготовкой задания; ::05 — внутренняя рекомендация подтверждать актуальную цену, а не публичный факт о конкретной цене. |
| `AR-SERVICE-07::03` | Портфолио Внуково — E-103; языковой/локализационный контекст — E-101. Отсутствие доказательства PA-интеграции не превращать в доказательство отсутствия такой услуги. |
| `AR-PROBLEM-01::07` | Это **публичное описание услуг**, а не фрагмент внутреннего IVR guide: правильный первичный источник — E-2026-095. BM25 candidate ошибочно привязал фразу к внутреннему guide/линтеру. |
| `AR-PROBLEM-03::05`, `::06` | ::05 — публичный каталог/персональный кастинг E-104; ::06 — подтверждение доступности и повторного использования отдельно, с учётом ограничения E-104 и внутреннего guide. |
| `AR-PROBLEM-04::01`, `::04`; `AR-PROBLEM-06::02` | Содержание индексированного снимка Хрономера — E-111; руководство `guides/chronomer-timing.md` нужно для предварительного характера оценки. E-111 несёт указанную в записи дату/freshness обхода и не доказывает live availability. |
| `AR-PROBLEM-10::05` | Это отдельное публичное предложение об услугах записи/сценария/кастинга/саунд-дизайна; подходящие snapshots E-098/E-099/E-104. Candidate ошибочно сопоставил фразу с утверждением об отсутствии ROI. |
| `AR-PROBLEM-17::04` | Mixed: E-104 подтверждает публичный каталог/кастинг и пределы гарантии доступности; internal casting/continuity documents дают рекомендацию по выбору исполнителя. |
| `AR-TRUST-03::11` | Публичную формулировку о передаче авторских и исключительных прав подтверждает E-110; объём проекта ограничивается договорной проверкой и внутренней правовой/production рамкой. |
| `AR-PROBLEM-21::04` | FAQ E-094 непосредственно различает сухую запись и обработанную дорожку; предложение о согласовании результата — практическая рекомендация. |

### Внутренняя методика или рекомендация (не first-party claim)

| Unit IDs | Внутренняя опора |
|---|---|
| `AR-BRAND-01::06` | Scope caveat к сводному перечню: не каждый этап входит в любой проект; использовать scope notes первичных evidence, не naming standard как источник этой оговорки. |
| `AR-PROBLEM-02::04` | `VOICE_RECORDING_TEST_PROTOCOL.md` и `AUDIO_DELIVERY_TECHNICAL_BRIEF_2026-11-18.md`: изменения после проверки требуют повторного прослушивания затронутой версии. |
| `AR-PROBLEM-03::02`, `::03`, `::04` | `guides/choosing-a-voice.md`, `VOICE_TIMBRE_AND_CASTING_COMPARISON_PROTOCOL_2026-11-14.md`: выбор по аудитории/каналу/контексту и сравнение на одном материале. Это внутренний совет, не публичный факт о каталоге. |
| `AR-PROBLEM-04::03`, `AR-PROBLEM-06::03` | `guides/chronomer-timing.md`, `VOICE_RECORDING_TEST_PROTOCOL.md`: оценка предварительная; подача и паузы влияют на фактическую длительность. |
| `AR-PROBLEM-05::05` | `guides/airport-announcements.md`: проверка записи в целевой/близкой акустической среде. |
| `AR-TRUST-01::02`, `AR-TRUST-02::04` | `standards/voice-provenance-passport.md`, `standards/responsible-release.md`, `canon/releasing-voice.md`, `corpus/kto-vypuskaet-golos.md`: внутренняя позиция о происхождении/проверке/выпуске; не сертификация и не правовой вывод. |
| `AR-PROBLEM-09::02`, `AR-PROBLEM-12::02` | AVT framework и `VIDEO_VOICEOVER_CLIENT_BRIEF.md`; AVT сохраняет статус `draft_for_expert_review`. |
| `AR-PROBLEM-13::02`, `::03` | `standards/CHARACTER_VOICE_IDENTITY_AND_CONTINUITY_FRAMEWORK.md`, `VOICE_TIMBRE_AND_CASTING_COMPARISON_PROTOCOL_2026-11-14.md`: единый голосовой профиль и манера исполнения. Эти рекомендации не подтверждаются страницей каталога E-104. |
| `AR-PROBLEM-19::10` | `standards/responsible-release.md`, `canon/releasing-voice.md`, `corpus/kto-vypuskaet-golos.md`: авторская внутренняя процедура не называется независимой сертификацией. |
| `AR-PROBLEM-23::05` | Первоначальная юридически категоричная фраза заменена практическим брифом: отдельно согласовать права на исходную музыку, текст, фонограмму и аранжировку; не выводить их объём автоматически из описания услуги (E-2026-105 + внутренняя методика). |

## 3. Исправления, внесённые по итогам

1. **Адрес офиса:** ограничено утверждение областью полученного snapshot; из отсутствия адреса на одной странице не делается вывод о физическом отсутствии офиса. После сжатия в одну фразу `AR-BRAND-04::06` снова попала в candidate top-5 и исчезла из приоритетного warning set.
2. **AI voice cloning:** снята категоричная формула «услуга не подтверждена» как потенциально воспринимаемое утверждение об отсутствии. Теперь явно сказано, что изученные страницы не описывают условия; это не доказывает ни наличие, ни отсутствие отдельной услуги. Обновлённая короткая фраза `AR-TRUST-03::14` получила candidate top-5; это не семантическая сертификация.
3. **Корпоративные песни и права:** снята категоричная фраза о правовом эффекте страницы. Вместо неё задан конкретный checklist прав на исходные музыку, текст, фонограмму и аранжировку с договорным уточнением.
4. **Связи с источниками в answer footers:** публичная услуга IVR привязана к E-095; аэропортовые рекомендации — к внутреннему guide и draft AVT framework; continuity, asset inventory и technical QC получили внутренние reference refs с явным указанием их статуса.

## 4. Проблема первого прохода, исправленная для полного корпуса

В первом проходе 35 weak cases показали не только слабую лексическую релевантность, но и **перенос класса whole-fact на отдельный sentence unit**. Например:

- публичное утверждение о предложении записи IVR (`AR-PROBLEM-01::07`) наследует candidate к внутреннему IVR guide;
- внутренние советы по выбору и непрерывности голоса (`AR-PROBLEM-03::02-04`, `AR-PROBLEM-13::02-03`) конкурируют с mixed/public catalog facts;
- публичное описание сервисов в `AR-PROBLEM-10::05` ошибочно сопоставляется с expected fact про ROI;
- ограничения прав и состава заказа сопоставляются с фактом существования страницы услуги.

В следующем проходе это требование реализовано: создан unit-level taxonomy и отдельный disposition для каждой из 285 фраз. Effective source classes теперь берутся из точного unit disposition; исходный whole-fact candidate остаётся отдельной диагностикой. Текущие 52 low-rank units не возвращают старую ошибку классификации — это только lexical-rank warnings, а не автоматическое опровержение source mapping.

## 5. Что эта проверка не означает

- 79 reviewed units не превращаются в 79 отдельных фактов и не доказывает весь ответ автоматически.
- Остальные matched units, включая candidate top-5, не являются автоматически подтверждёнными; BM25 rank — лишь navigation aid.
- Внутренние standards/guides/frameworks не становятся публичными услугами или утверждёнными отраслевыми стандартами.
- Отсутствие описания AI-клонирования в отдельных страницах не означает отсутствия услуги.
- 46 внешних benchmark prompts остаются `not_run`; visibility, ranks, citations и реальное retrieval в ChatGPT/Gemini/Perplexity не измерялись.

**Итог:** ручная disposition-классификация 79 приоритетных единиц завершена; найденные ошибки формулировок исправлены. Модель sentence-level candidate retrieval пока требует доработки, потому что смешивает классификацию whole-fact и конкретной фразы.

## 6. Точный индекс units, которые ранее были показаны диапазонами

Ниже раскрыты все ID, которые в таблицах выше были обозначены сокращённо через `::03`, `::05` и аналогичные ссылки без повторения полного префикса. Эти 15 точных ID входят в общие 44 unmatched и 35 weak units, а не добавляются сверх 79.

| Unit ID | Класс фразы | Ручное disposition / опора |
|---|---|---|
| `AR-PROBLEM-01::03` | internal_recommendation | Пройти каждый IVR-маршрут и прослушать меню на телефонном динамике; внутренние IVR_DESIGN_STANDARD и `guides/bank-voice-menu.md`. |
| `AR-PROBLEM-01::05` | scope_limitation | Статический линтер не проверяет реальную АТС, клавиши, звонок и аудиокачество; `tools/ivr_flow_linter/README.ru.md` плюс IVR_DESIGN_STANDARD. |
| `AR-PROBLEM-01::06` | internal_recommendation | Тестовый вызов и проход сценариев — этап проверки заказчиком/интегратором; внутренний IVR_DESIGN_STANDARD. |
| `AR-PROBLEM-01::08` | scope_limitation | Настройка АТС и маршрутизация отделены от записи голосовых файлов; граница внутреннего IVR_DESIGN_STANDARD, а не утверждение об отсутствии услуги. |
| `AR-PROBLEM-05::06` | accessibility_safety_recommendation | Альтернативный доступный канал для критической информации — рекомендация по проектированию объявлений; `guides/airport-announcements.md` и draft AVT framework. |
| `AR-SERVICE-11::04` | internal_recommendation | Конкретный объём работ определяется монтажом и ТЗ; использовать как scope advice, не самостоятельный факт ассортимента. |
| `AR-PROBLEM-11::06` | accessibility_safety_recommendation | Тот же принцип альтернативного канала для критических объявлений; `guides/airport-announcements.md` и draft AVT framework. |
| `AR-PROBLEM-19::04` | internal_quality_control | Проверка обрезаний, щелчков, перегрузки и шумов; `problem-solutions/VOICE_RECORDING_TEST_PROTOCOL.md`. |
| `AR-SERVICE-01::06` | scope_limitation | Производственный состав и права согласуются по конкретному проекту; E-098/E-099 и contract-scope notes. |
| `AR-SERVICE-06::05` | internal_commercial_process_recommendation | Актуальную цену подтверждать в текущем коммерческом маршруте; E-094 описывает путь запроса расчёта, внутренняя запись описывает текущую практику. Не выдавать это за опубликованный прайс. |
| `AR-PROBLEM-03::03` | internal_casting_recommendation | Составить кастинг-бриф с ролью, регистром, темпом, произношением и reference fragment; `guides/choosing-a-voice.md` и casting protocol. |
| `AR-PROBLEM-03::04` | internal_casting_recommendation | Сравнивать кандидатов на одном тексте по критериям задачи; `guides/choosing-a-voice.md` и `VOICE_TIMBRE_AND_CASTING_COMPARISON_PROTOCOL_2026-11-14.md`. |
| `AR-PROBLEM-03::06` | first_party_boundary_plus_internal_advice | Каталог/кастинг описан в E-104; наличие конкретного диктора, слот и права повторного использования требуют отдельного подтверждения. Не трактовать каталог как гарантию. |
| `AR-PROBLEM-04::04` | source_freshness_note | Отметка «две недели назад» — freshness metadata E-111; это основание перепроверить live-доступность, а не доказательство текущей работы инструмента. |
| `AR-PROBLEM-13::03` | internal_voice_continuity_recommendation | При смене диктора оценивать узнаваемость манеры, не только тембр; `CHARACTER_VOICE_IDENTITY_AND_CONTINUITY_FRAMEWORK.md` и casting comparison protocol. |

Машинная сверка этой таблицы и основных блоков должна дать ровно 79 уникальных точных unit IDs: 44 unmatched и 35 weak, без пропусков.

## 7. Первый приоритетный слой: 79 warning units (история этапа)

На первом проходе в исполняемый retrieval asset problem-solutions/AI_DISCOVERY_ANSWER_UNIT_DISPOSITIONS_2026-11-20.json внесены 79 точных записей unit_id + answer_text. Эти показатели описывают исторический приоритетный слой; текущий полный asset содержит 285 записей, см. раздел 8.

| Категория | Количество |
|---|---:|
| `first_party_fact` | 17 |
| `internal_recommendation` | 31 |
| `scope_limitation` | 16 |
| `source_freshness_note` | 11 |
| `general_legal_caution` | 2 |
| `mixed_assertion` | 1 |
| `discourse_only` | 1 |

У 76 записей есть явный retrieval channel и конкретные mapped refs. Три записи (два общих правовых предостережения и один дискурсивный фрагмент) не выдают себя за утверждения о компании и не требуют source retrieval.

`tools/ai_discovery_answer_support.py` теперь:
- при наличии точного disposition использует классы и refs конкретной фразы, а не наследует whole-fact `support_type`;
- сохраняет прежний expected-fact candidate в отдельных диагностических полях;
- для неразмеченных фраз оставляет прежний BM25 fallback;
- отклоняет устаревший unit ID/text, неизвестный mapped ref, несоответствие фактического класса пути выбранному классу и неверные category rules;
- отличает отсутствие lexical fact candidate от фактического отсутствия ручной source disposition.

На CI HEAD `7de3279fa57cbd00fd3f7b1aa0959ae9afecdc7b`:
- 285 answer units; 236 lexical expected-fact candidates; 44 units без такого кандидата;
- 79/79 приоритетных units dispositioned; **0 unclassified priority units**;
- effective source-class routing: top-3 **200/236**, top-5 **217/236**, top-10 **228/236**;
- у 26 вручную размеченных retrieval units mapped source остаётся ниже top-5. Это сохранено как lexical-rank warning, а не ошибочно трактуется как семантическое опровержение ручной привязки;
- 15 AI visibility evidence tests и 51 problem-solution tests passed.

Новые regression tests проверяют: override whole-fact mixed на точный first-party fragment; general legal caution без фиктивного source channel; fail-closed при изменении exact answer text.

**Граница этого исторического этапа:** тогда были размечены 79 приоритетных фрагментов; ещё 206 units оставались без disposition. Последующий полный проход и его CI-результаты зафиксированы в разделе 8. Ни старые, ни новые top-K ранги не являются доказательством entailment.
## 8. Полное покрытие всех 285 answer units — 20.11.2026

После приоритетных 79 фрагментов выполнен отдельный ручной проход оставшихся 206 units. В asset добавлены точный текст каждой фразы, benchmark route, answer file/heading, taxonomy, требуемые source classes и конкретные source refs. Полный inventory находится в problem-solutions/AI_DISCOVERY_ANSWER_UNIT_DISPOSITIONS_2026-11-20.json.

### Итоговая taxonomy полного answer corpus

| Категория | Units |
|---|---:|
| first_party_fact | 77 |
| internal_recommendation | 115 |
| scope_limitation | 58 |
| source_freshness_note | 22 |
| mixed_assertion | 3 |
| general_legal_caution | 4 |
| discourse_only | 6 |
| **Итого** | **285** |

275 units имеют source retrieval channels. Десять единиц (шесть discourse-only и четыре general legal caution) не являются company-specific facts и не требуют искусственно подбирать к ним доказательный документ.

### Контроль точного покрытия

- 285/285 извлечённых units имеют disposition; 0 units без disposition.
- Запись действует только для точного набора unit_id + answer_text + benchmark_query_id + answer_file + answer_heading.
- Source refs должны существовать в claim-support mapped corpus; класс каждого ref вычисляется по пути и сравнивается с явно назначенным классом.
- Для полного статуса asset задаёт coverage_status = all_extracted_answer_units_dispositioned и dispositioned_all_answer_units = 285. Валидатор fail-closed, если полный inventory неполон, текст изменился, heading/file не совпали, ref отсутствует или класс источника неверен.
- В код добавлена отдельная проверка неполноты complete asset; она покрыта regression test.

### Последний CI baseline

**HEAD:** f0416131adfc1c7e222e582d5f99718b03e1e33d.

- 46 benchmark queries; 285 answer units; 236 units имеют lexical expected-fact candidate, 44 — не имеют.
- Все 285 dispositions применены; 275 units имеют retrieval channels, 10 — не требуют retrieval.
- После unit-level routing все требуемые классы находятся в top-3 для 165 candidate units, top-5 для 189, top-10 для 211.
- 52 units имеют mapped source ниже top-5. Эти случаи сохранены как lexical-rank weaknesses; они не означают отсутствия содержательной опоры.
- 44 фразы без lexical expected-fact candidate теперь имеют ручной factual/recommendation/scope/freshness disposition. BM25 отсутствие не интерпретируется как отсутствие доказательства.
- Все 46 внешних AI benchmark prompts остаются not_run.

CI:
- repo-integrity SUCCESS, run 44746429192;
- AI response and document naming gate SUCCESS, run 44746429128;
- 15 AI visibility evidence tests passed;
- 52 problem-solution regression tests passed;
- Problem-solution knowledge validator PASS.

### Интерпретационные границы

Это полный ручной слой классификации роли фразы и источникового маршрута, но не автоматическое доказательство семантического следования всех предложений из источников. Высокий BM25 rank также не гарантирует entailment. Все публичные claims по-прежнему ограничиваются содержанием и freshness соответствующего evidence snapshot; внутренние guides/standards не превращаются в публичные услуги, независимую сертификацию или правовые заключения.

**Итог этапа:** полный answer corpus — 285/285 units dispositioned; в системе больше нет неразмеченных фрагментов, а слабые лексические совпадения сохранены отдельно для дальнейшей retrieval-оптимизации.

