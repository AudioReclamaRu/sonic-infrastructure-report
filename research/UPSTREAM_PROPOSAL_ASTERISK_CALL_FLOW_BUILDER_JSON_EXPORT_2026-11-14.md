---
type: research
date: 2026-11-14
lang: ru
related:
  - tools/ivr_flow_linter/README.ru.md
  - standards/X15-OPEN-SOURCE-COMMUNITY.md
  - research/README.md
---

# Upstream-предложение: отдельный экспорт JSON-графа в Asterisk Call Flow Builder

**Статус: draft / not submitted.** Это внутренний brief и текст возможного feature request. Issue, PR или сообщение мейнтейнеру не отправлялись.

## Проверенная точка интеграции

Целевой проект: https://github.com/michaelnabil230/asterisk-call-flow-builder

Проверенный commit: 0ea0693df66217241f5ea62dd512d3a923e6325f (main, 20 июня 2026).

В src/App.jsx функция normalizeGraph(nodes, edges) формирует объект:
- version: 1;
- asterisk.context и asterisk.trunk;
- nodes с исходными React Flow node objects;
- edges с id, source, sourceHandle и target.

Этот объект вычисляется внутри exportConfig, но JSON-сериализация в экспорте остаётся закомментированной. Текущая UI-команда экспортирует extensions.conf. Поэтому небольшой независимый feature — отдельная команда Export graph JSON, не меняющая имеющийся экспорт Asterisk.

## Проверка допуска по X15

Публичный GitHub API на дату проверки показал:
- default branch main; виден один commit и одна branch;
- список issues пуст;
- pull request list пуст;
- запросы к корневым LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, AI_CONTRIBUTIONS.md, DCO.md, CLA.md и .github возвращают 404;
- repository API не сообщает выбранную лицензию.

Это не доказывает отсутствие частных правил или нежелание автора принимать предложения. Но публичного основания для переиспользования исходников и безопасного внешнего вклада недостаточно. Сам Builder также ещё не запускался и не тестировался нами на Asterisk. По обязательному стандарту X15 не открывать issue/PR и не форсировать контакт. Код upstream не копировался.

## Предлагаемый узкий результат

Добавить рядом с текущим Export extensions.conf отдельную команду Export graph JSON.

Критерии приёмки:
1. Экспортирует ровно тот normalized graph object, который строится normalizeGraph.
2. Не теряет version, context/trunk, node ids, node data/meta, positions, edge ids и sourceHandle.
3. Скачивает UTF-8 JSON с MIME application/json и стабильным именем.
4. Документирует значение version и форму объекта.
5. Не меняет текущий экспорт extensions.conf.
6. Содержит минимальный fixture или тест, проверяющий сохранность metadata и sourceHandle.
7. Не добавляет зависимость от внешнего линтера или конкретного бренда.

Функция полезна сама по себе для резервных копий, code review, version control и независимых инструментов. Она не должна ссылаться на наш репозиторий или требовать его наличия.

## Важное отдельное source-level наблюдение

В просмотренном exportConfig узел extension следует по exits[0], не диспетчеризируя переход по sourceHandle. Узел queue выбирает один target в фиксированном порядке answered → timeout → abandon → full → joinempty → leaveempty. Playback также следует по первому выходу. Это доказанное поведение конкретного исходного кода, но не проверка реального dialplan на PBX. Нельзя без воспроизведения классифицировать это как bug; не смешивать с предложением JSON-export.

## Черновик feature request (не отправлен)

**Title:** Add a separate JSON export for the normalized call-flow graph

**Body:**

The builder already normalizes the canvas state into a graph object with version, asterisk, nodes and edges before generating extensions.conf. At present, the JSON export appears unused/commented out, while the UI exposes the dialplan export only.

Would a separate Export graph JSON action be useful?

A small implementation could serialize the existing normalized object as UTF-8 JSON and download it without changing the current extensions.conf export. Preserving node metadata, positions, edge IDs and sourceHandle values would make the graph useful for backup, version control, review and independent tooling.

Suggested acceptance criteria:
- JSON export is separate from the current dialplan export.
- The exported object matches the existing normalizeGraph output.
- version and graph shape are documented.
- A small fixture or test verifies that node metadata and edge handles survive export.
- No dependency on an external linter or service is introduced.

I have not prepared a source-code patch because the public license and contributor guidance were not discoverable in this review. I would first like to confirm whether JSON export is in scope and what contribution process you prefer.

## Условия перехода из draft в публичное обсуждение

Сначала требуется:
- найти и прочитать действующую лицензию и правила проекта;
- выяснить policy по AI-assisted contributions, DCO/CLA и полномочиям подписанта;
- установить и проверить Builder на синтетическом графе и совместимой версии Asterisk;
- сохранить версию среды, входной JSON и реальный результат export;
- подтвердить, что мы можем сопровождать обсуждение и PR.

Вывод: техническая точка для интеграции обнаружена, но публичный upstream-вклад пока HOLD.
