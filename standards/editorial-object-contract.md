# CULEUR OF VOICE — EDITORIAL OBJECT CONTRACT v1.0

Статус: активный стандарт (implementation: editorial_object.py, feed/image_gen.py,
feed/concepts.json). Live-контур publisher.py НЕ перезапускался при внедрении:
новый слой включается аддитивно — только для концептов, несущих `event_object`.
Legacy-слоты без `event_object` сохраняют прежнее поведение гейта и рендера.

## Принцип

> Культура Голоса видит событие как объект и превращает этот объект
> в цельную публикацию.

Запрещено генерировать cover независимо от editorial meaning.

```
         EVENT OBJECT
              │
      ┌───────┴────────┐
      ↓                ↓
   ARTICLE          COVER
      │                │
  causal chain    visual object
      │                │
      └───────┬────────┘
              ↓
       SAME CHANGE
```

## 1. EVENT OBJECT

Перед написанием текста формируется объект события:

```json
{
  "subject":     "...",
  "action":      "...",
  "before":      "...",
  "after":       "...",
  "mechanism":   "...",
  "consequence": "...",
  "evidence":    "...",
  "object_type": "SPLIT"
}
```

Обязательный минимум (в контракте от владельца проекта, 30.09.2026):

- `after` — что стало сейчас;
- `mechanism` — за счёт чего произошло изменение;
- `evidence` — на чём основано;
- `object_type` — из словаря ниже.

Валидация: `editorial_object.validate_event_object()`.
Отсутствие `after` или `mechanism` → `REJECT: INCOMPLETE_EVENT_OBJECT:<field>`.
Incorrect `object_type` → `REJECT: UNKNOWN_OBJECT_TYPE:<value>`.

## 2. OBJECT TYPE

`object_type` выбирается из ФАКТА изменения, а не из темы статьи.
«voice», «AI», «startup» — не object_type.

```
TRANSFORMATION   было → стало
EMERGENCE        возникло то, чего раньше не было
SHIFT            существующее явление сместилось
CONFLICT         столкнулись две силы / модели
SPLIT            одно стало несколькими
CONVERGENCE      разное сошлось в одно
THRESHOLD        достигнута граница / появился новый порог
REVERSAL         привычное отношение перевернулось
INFRASTRUCTURE   появилась новая система / слой
ABSENCE          важно исчезновение / непоявление
DEMONSTRATION    есть конкретная демонстрация, которую можно показать
```

## 3. ARTICLE

Текст строится вокруг одной причинной дуги:

1. Что произошло.
2. Что именно изменилось.
3. Как это работает / почему произошло (mechanism).
4. Что было раньше (before).
5. Что теперь становится возможным (consequence).
6. Какое следствие следует из изменения.

Запрещено: перечисление несвязанных фактов; повтор заголовка пятью способами;
финал без следствия; рекламный вывод без доказанного изменения (evidence);
filler-фразы; «это важный шаг»; «это может изменить индустрию» без объяснения
механизма.

## 4. COVER

Cover строится НЕ из title. Cover строится из:

```
object_type + before + after + change
```

Главный вопрос: «Как показать изменение без текста?» Если ответ невозможен →
`COVER_REJECT`.

Механика: `feed/image_gen.py::_render_by_object_type(eo, seed, attempt)` —
детерминированный рендер перехода (не темы) для каждого object_type.
Форма-буфер (silhouette) используется только для незнакомых типов —
так рендер не превращается в иллюстрацию отрасли.

## 5. COVER SEMANTIC TEST

Проверка (детерминированные прокси — `editorial_object.cover_semantic`):

- A. Виден ли переход? (smoke-test, человек)
- B. Видно ли, ЧТО изменилось? (smoke-test, человек)
- C. Один главный объект? (smoke-test, человек)
- D. Не символ отрасли? (прокси: тематические слова без маркеров изменения)
- E. Не повторяет банально тему статьи? → `REJECT: TOPIC_ILLUSTRATION`
  (visual_object = только отраслевые слова: голос/звук/микрофон/нейросеть..., ни
  одного маркера изменения)
- F. Визуальный объект совпадает с EVENT OBJECT? → `REJECT: SEMANTIC_MISMATCH`
  (нет ни маркера изменения нужного типа, ни отраслевого заполнения)

Человеческие A/B/C/D выполняются на эталонных кейсах и при ревью каждой
обложки; пайплайн не заменяет их визуальным судом.

## 6. TEXT/COVER CONSISTENCY

ARTICLE и COVER обязаны ссылаться на один EVENT OBJECT.
`editorial_object.text_cover_match()` сверяет `object_type` статьи и события.
Запрещено: article=transformation + cover=microphone; article=split + generic
silhouette; article=absence + explosion.

## 7. OUTPUT

Перед публикацией сохраняется (журнал `state/editorial.jsonl`):

```
event_object
article_structure
object_type
cover_concept (visual_object)
cover_path
```

И журнал проверки:

```
EDITORIAL_OBJECT   PASS/REJECT
COVER_SEMANTIC     PASS/REJECT
TEXT_COVER_MATCH   PASS/REJECT
```

DoD публикации для режима A (концепт с `event_object`):
в `state/editorial.jsonl` строка с `"editorial_object": "PASS"`,
`"cover_semantic": "PASS"`, `"text_cover_match": "PASS"`.

## 8. ЭТАЛОННЫЕ ЖИВЫЕ КЕЙСЫ (правило обучения)

Система не учится на старых публикациях. Обучение — только через живые случаи,
где человек вручную фиксирует: событие → настоящий объект → почему такая обложка
правильная → почему три другие неправильные (см. standards/editorial-object-cases.md).
После пяти кейсов система учится редакционному различению, а не стилю картинки.
CASE 01 (SPLIT, kast-kharakterov-2026-09-27) — заполнен и зафиксирован.