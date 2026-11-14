---
type: research
date: 2026-11-14
lang: ru
related:
  - tools/ivr_flow_linter/README.ru.md
  - problem-solutions/IVR_DESIGN_STANDARD.md
  - standards/X15-OPEN-SOURCE-COMMUNITY.md
  - research/UPSTREAM_PROPOSAL_ASTERISK_CALL_FLOW_BUILDER_JSON_EXPORT_2026-11-14.md
---

# Аудит интеграции IVR-инструментов

**Статус:** source-reviewed interoperability and synthetic contract tests. Не является заявлением о plug-in интеграции, runtime-проверке АТС или одобрении upstream-проектами.

## 1. Слои и их задачи

| Инструмент | Проверенная роль | Интеграционный слой | Граница |
|---|---|---|---|
| Asterisk Call Flow Builder | Визуальное редактирование графа и экспорт extensions.conf | Наблюдаемую модель graph JSON преобразуем в канонический IVR Flow | В штатном UI JSON-экспорт не обнаружен |
| IVR Flow Linter | Статическая проверка графа | Ссылки, fallback, достижимость, терминальные пути и policy | Не проверяет PBX, dialplan или аудио |
| AsteriskLint | Проверка синтаксиса и структуры Asterisk config/dialplan | Отдельный downstream запуск на extensions.conf | Не анализирует замысел canvas-графа |
| MakingChatbots/ivr-tester | Runtime тест звонка с распознаванием prompt и DTMF | Сценарная матрица Scenario/Step | Требует реальных prompt-текстов, телефонов, credentials и transcriber setup |

## 2. Asterisk Call Flow Builder: observed source contract

На commit 0ea0693df66217241f5ea62dd512d3a923e6325f функция normalizeGraph возвращает объект {version: 1, asterisk: {context, trunk}, nodes, edges}. Node сохраняет React Flow поля id/type/position/data, edge — id/source/sourceHandle/target. В просмотренном коде normalized object создаётся при экспорте dialplan, но JSON serialization закомментирована. Публичная кнопка скачивает extensions.conf.

Адаптер interop/acfb_to_flow.py использует fail-closed подмножество узлов start, menu, playback, extension, queue, hangup. Неизвестные типы, сломанные ссылки, повторные исходящие handles и иные версии блокируют преобразование. Позиции и поля, не необходимые статической проверке, отбрасываются. Fixture синтетическая, собрана по структуре публичного исходника; это не экспорт реальной установки.

### Важное предупреждение о семантике dialplan

В проверенном exportConfig:
- extension использует exits[0] без dispatch по sourceHandle;
- queue выбирает один target в фиксированном порядке исходов;
- playback также использует первый выход.

Адаптер сохраняет все объявленные graph edges и предупреждает о случаях, когда экспортёр может свести исходы к одному. Поэтому PASS канонического графа не подтверждает, что текущий extensions.conf сохранил те же ветви. Это source-code observation, не результат звонка на Asterisk.

## 3. MakingChatbots/ivr-tester: observed API contract

Проверенный main commit: 0685d8707896264106796724b4ff29d821bac7a3.

README показывает вызов IvrTester.run({from, to}, scenario). Scenario имеет name и steps; Step содержит whenPrompt, then, silenceAfterPrompt, timeout. whenPrompt — функция-условие распознавания, then — действие. Примеры README используют similarTo(...), press(...), hangUp() и doNothing().

Генератор делает только JSON-план:
- DTMF digit → press(digit);
- timeout → doNothing();
- invalid_input → первый незанятый ключ из 0123456789, если он доступен;
- message continue → doNothing();
- исходы extension/queue, которые нельзя подтвердить только через Step API, отмечаются в manual_routes.

expected_prompt_transcript остаётся null, а runtime_ready равен false. PBX playback token или filename не является доказательством фактической произнесённой фразы. Номера from/to, Twilio credentials и настройки transcriber не создаются и не хранятся.

## 4. AsteriskLint: независимый downstream слой

README AsteriskLint документирует команду:

    asterisklint dialplan-check extensions.conf

Проект описывает проверку конфигурации Asterisk, контекстов, приложений и dialplan. Репозиторий сообщает GPLv3+; код не копируется и пакет не добавляется обязательной зависимостью. Этот этап возможен только после получения конкретного extensions.conf и отдельной установки инструмента.

## 5. Рекомендованный процесс

1. Создать IVR-граф в Asterisk Call Flow Builder.
2. Получить JSON graph object. В проверенном upstream UI отдельная JSON-кнопка пока не обнаружена; без неё штатный export handoff отсутствует.
3. Прогнать acfb_to_flow.py и получить канонический JSON.
4. Прогнать ivr_flow_lint.py.
5. Проверить отдельно, что generated extensions.conf сохраняет все задуманные ветви; существующий source exporter может их не сохранять.
6. При наличии конкретного dialplan запустить AsteriskLint.
7. Заполнить реальный текст prompts после прослушивания и собрать тестовые номера/credentials вне Git.
8. Сформировать IVR Tester Scenario и выполнить runtime call.
9. Вручную проверить телефонный результат и финальное аудио по внутреннему IVR стандарту.

Успешный статический шаг не заменяет последующий слой.

## 6. Тесты и ограничения

Synthetic fixture и unit tests покрывают структуру преобразования, fallback, неизвестные типы, дублирующие handle, warning по exporter behavior, DTMF/timeout/invalid-input mapping, пустые prompt transcripts и блокировку циклов.

Они не включают:
- реальную установку Asterisk Call Flow Builder;
- запуск Asterisk PBX и проверку generated extensions.conf;
- Twilio или другой провайдер телефонии;
- звонок на тестовый номер;
- реальные аудиозаписи, транскрипции или прослушивание.

## 7. Точные источники и снимки

- Asterisk Call Flow Builder source: https://github.com/michaelnabil230/asterisk-call-flow-builder/blob/0ea0693df66217241f5ea62dd512d3a923e6325f/src/App.jsx
- Asterisk Call Flow Builder README: https://github.com/michaelnabil230/asterisk-call-flow-builder/blob/main/README.md
- IVR Tester README: https://github.com/MakingChatbots/ivr-tester/blob/main/README.md
- IVR Tester Step interface: https://github.com/MakingChatbots/ivr-tester/blob/0685d8707896264106796724b4ff29d821bac7a3/packages/ivr-tester/src/configuration/scenario/Step.ts
- IVR Tester scenario validation: https://github.com/MakingChatbots/ivr-tester/blob/0685d8707896264106796724b4ff29d821bac7a3/packages/ivr-tester/src/configuration/scenario/validateAndEnrichScenario.ts
- AsteriskLint README: https://github.com/ossobv/asterisklint/blob/master/README.rst
- Official Asterisk dialplan documentation: https://docs.asterisk.org/Configuration/Dialplan/

## 8. Решение по upstream

По Asterisk Builder публичный GitHub API на дату проверки: нет LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, AI_CONTRIBUTIONS, DCO/CLA или .github в ожидаемых корневых путях; issues и PR lists пусты; виден один commit. Это не доказывает частные правила, но не позволяет подтвердить публичный путь к вкладу. Поскольку реальный запуск Builder и Asterisk также не выполнен, публичная отправка issue/PR приостановлена по X15.

Для IVR Tester отдельно необходимо пройти полную социальную/AI-policy/CLA проверку и проверить его текущий rewrite/release branch, прежде чем делать contribution. Локальный handoff не требует изменения upstream API.


## 9. Сохранение источника и параметров

Адаптер добавляет provenance на уровне всего потока и interop_source на уровне исходных узлов. Он переносит только явно разрешённые поля по типу узла: start prompt/timeout, menu playback/retries/options, playback sound, extension/ringSeconds/playback, queue name/strategy/timeout, а также позиции canvas. Неизвестные поля исходной модели намеренно не копируются. Это ограничивает утечку секретов, но означает, что преобразование не является lossless round-trip; исходный ACFB graph JSON следует хранить отдельно. Схема канонического JSON документирует provenance/interoperability metadata.

## 10. Попытка запуска реального upstream-приложения (2026-11-14)

Проведён отдельный smoke test публичного upstream main в изолированном StackBlitz WebContainer — без fork, upstream write или правок исходников:

- импорт публичного GitHub repository завершился; npm install успешно установил 33 packages;
- Vite 8.0.16 сообщил ready in 9131 ms;
- браузерный агент увидел страницу Asterisk Call Flow Builder, интерактивный React Flow canvas и предзагруженный граф Acme Support; ошибок терминала/консоли в первом сеансе не сообщил;
- при отдельной попытке повторно открыть preview URL после завершения первого browser run сервер уже не слушал порт 5173 (Unable to connect to port 5173). Поэтому live React Fiber/useState не удалось прочитать и фактический normalizeGraph JSON не извлечён;
- этот результат доказывает, что приложение и его зависимости запускались в одном временном WebContainer-сеансе. Он **не доказывает локальный Windows self-host, сохранение runtime между сеансами или реальную интеграцию с Asterisk**.

Ограничения рабочей shell-среды этого исследования:
- Node.js v22.16.0 и npm 10.9.2 присутствуют;
- git ls-remote не смог разрешить github.com (DNS/network недоступен в контейнерной shell);
- Asterisk и Docker CLI отсутствуют.

Итоговый статус: **PARTIAL / NOT E2E**. Нет live graph capture, generated-dialplan runtime test, PBX или telephone call. Для следующего достоверного шага нужен один устойчивый self-host-сеанс, в котором JSON извлекается до остановки dev server, затем — отдельная совместимая Asterisk PBX.