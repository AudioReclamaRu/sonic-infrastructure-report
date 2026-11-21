---
type: measurement_report
date: 2026-11-21
lang: ru
status: read_only_goal_dictionary_audit
related:
  - research/AI_DISCOVERABILITY_SERVICE_ROUTE_METRICA_DRILLDOWN_2026-11-21.md
  - research/metrica-goals-inventory-1413317-2026-11-21.json
  - research/metrica-goals-inventory-1413317-2026-11-21.csv
  - research/metrica-goals-observed-21-mapping-2026-11-21.csv
  - research/metrica-goals-commercial-final-2026-11-21.csv
  - research/metrica-goals-control-final-2026-11-21.csv
---

# Аудит словаря целей Яндекс Метрики: counter 1413317

**Дата аудита:** 21 ноября 2026 года.  
**Режим:** read-only. Сайт `https://www.audio-reclama.ru`, счётчик, цели, теги, GTM, CMS, robots/sitemap и публикации не менялись. Реальные тестовые заявки/звонки/сообщения не отправлялись. Платные сервисы и апгрейды не использовались.  
**Первичный источник словаря:** `C:\Users\Muzey\Downloads\yandex-metrica-goals-1413317-20261121-130910.json` (84 450 байт, дата изменения 21.11.2026 13:09:10, UTF-8 BOM).  
**Контекст:** продолжение исследования PR #79 (`ai-discoverability/legacy-answer-disposition-20261121`) и отчёта [AI_DISCOVERABILITY_SERVICE_ROUTE_METRICA_DRILLDOWN_2026-11-21.md](AI_DISCOVERABILITY_SERVICE_ROUTE_METRICA_DRILLDOWN_2026-11-21.md).

## 1. Результат проверки исходного JSON

| Проверка | Факт |
|---|---|
| Файл найден | Да, основной путь существует; других `yandex-metrica-goals-1413317-*.json` в Downloads не найдено. |
| Верхнеуровневые цели (`goals[]`) | **88** |
| Составные цели типа `step` | **7** |
| Вложенные шаги внутри `steps[]` | **16** |
| Именованные записи верхнего уровня + вложенные шаги | **104** |
| Уникальные ID во всех 104 записях | **104** (дубликатов ID нет) |
| Статус верхнеуровневых целей | Все 88 — `Active` |
| Источник верхнеуровневых целей | `user` — 76, `auto` — 12 |
| `is_retargeting` | 0 у всех 88 верхнеуровневых |
| `default_price` | 0 у всех целей, где поле присутствует; **это не доказательство отсутствия выручки**. |

Контрольные ожидания из задания подтверждены фактическим JSON: 88 / 7 / 16 / 104.

### Структура JSON (важно для воспроизводимости)

- Верхнеуровневые записи лежат в `goals[]`.
- Составные цели имеют `type: "step"` и массив `steps[]`, а не `conditions[]` с `goal_id`.
- У вложенных шагов есть собственные `id`, `name`, `type`, `status`, `goal_source`, `is_retargeting`, `prev_goal_id`, `default_price`, `conditions`.
- Цели типа `number` (Page Depth) в этом экспорте имеют `depth` и `conditions: null`.
- Автоцели `contact_data` и `contact_data_sent` имеют `conditions: null`; `form` — `conditions: []`.

### Распределение типов верхнеуровневых целей

`action` — 62; `step` — 7; `number` — 6; `url` — 3; по 1: `messenger`, `file`, `email`, `form`, `phone`, `social`, `payment_system`, `search`, `contact_data`, `contact_data_sent`.

## 2. Сопоставление с прежними измерениями

### 2.1. Десять профессиональных сервисных маршрутов (22.10–17.11.2026)

Прежний отчёт: 118 визитов, 118 уникальных visit ID, 88 визитов хотя бы с одним Goal ID, 21 уникальный Goal ID. **Словарь подтверждён JSON** для всех 21 ID. Частоты по уникальным визитам подтверждаются только ранее сохранённым отчётом/выгрузкой drilldown; исходные строки визитов в этом репозитории локально недоступны, повторный расчёт частот по сырым визитам не выполнялся.

| Goal ID | Частота (distinct visits, из прежнего отчёта) | JSON: имя | JSON: тип/условие | Уровень | Класс аудита | Примечание |
|---:|---:|---|---|---|---|---|
| 225259037 | 54 | Микроконверсии Scroll_Tracking_25 | action; exact `Scroll_Tracking_25` | top | behavioral_microconversion | совпадает |
| 225259042 | 47 | Микроконверсии Engagement_Timer_30s | action; exact `Engagement_Timer_30s` | top | behavioral_microconversion | совпадает |
| 225259038 | 39 | Микроконверсии Scroll_Tracking_50 | action; exact `Scroll_Tracking_50` | top | behavioral_microconversion | совпадает |
| 225259039 | 36 | Микроконверсии Scroll_Tracking_75 | action; exact `Scroll_Tracking_75` | top | behavioral_microconversion | совпадает |
| 225259043 | 26 | Микроконверсии Engagement_Timer_60s | action; exact `Engagement_Timer_60s` | top | behavioral_microconversion | совпадает |
| 225259041 | 22 | Микроконверсии Scroll_Tracking_100 | action; exact `Scroll_Tracking_100` | top | behavioral_microconversion | совпадает |
| 225259052 | 17 | Микроконверсии Page_Depth_3 | number; depth=3, conditions=null | top | behavioral_microconversion | семантически совпадает; в JSON depth отдельным полем |
| 157243354 | 10 | Меню. Клик. Экспорт | action; exact `export` | top | navigation_action | совпадает |
| 225259053 | 7 | Микроконверсии Page_Depth_5 | number; depth=5, conditions=null | top | behavioral_microconversion | семантически совпадает |
| 51362815 | 6 | Посещение страниц Дикторы | url; contain `https://www.audio-reclama.ru/diktoryi/` | top | navigation_or_pageview | совпадает по смыслу; drilldown сократил URL в тексте |
| 225259044 | 5 | Микроконверсии Engagement_Timer_90s | action; exact `Engagement_Timer_90s` | top | behavioral_microconversion | совпадает |
| 31170907 | 4 | Пользователь перешёл на страницу быстрого заказа | url; contain `/online-zakaz.html` | step_1 в 31170904 «Быстрый заказ» | funnel_step | совпадает по условию; **уточнение:** это вложенный шаг составной воронки, а не отдельная верхнеуровневая цель |
| 225259069 | 4 | Микроконверсии Contact_Page | url; contain `https://www.audio-reclama.ru/online-zakaz.html` | top | navigation_or_pageview | совпадает по смыслу; drilldown сократил URL |
| 53657743 | 3 | Кнопка "заказать" в шапке | action; exact `click_order_button` | top | cta_click | совпадает |
| 225259054 | 3 | Микроконверсии Page_Depth_7 | number; depth=7, conditions=null | top | behavioral_microconversion | семантически совпадает |
| 196138342 | 1 | Автоцель: скачивание файла | file; `all_files` | top | file_download | совпадает |
| 225259046 | 1 | Микроконверсии Engagement_Timer_120s | action; exact `Engagement_Timer_120s` | top | behavioral_microconversion | совпадает |
| 225259048 | 1 | Микроконверсии Engagement_Timer_200s | action; exact `Engagement_Timer_200s` | top | behavioral_microconversion | совпадает |
| 225259055 | 1 | Микроконверсии Page_Depth_10 | number; depth=10, conditions=null | top | behavioral_microconversion | семантически совпадает |
| 225259056 | 1 | Микроконверсии Page_Depth_12 | number; depth=12, conditions=null | top | behavioral_microconversion | семантически совпадает |
| 225259057 | 1 | Микроконверсии Page_Depth_15 | number; depth=15, conditions=null | top | behavioral_microconversion | семантически совпадает |

**Проверка drilldown:** названия, типы и смысл условий подтверждены. Уточнения: 31170907 — вложенный шаг; Page Depth цели в JSON используют `depth`+`conditions:null`; URL-цели 51362815/225259069 в JSON содержат полные https URL, в drilldown они были сокращены в тексте. Классификация «микроконверсии / не заявка» подтверждена.

### 2.2. Контрольная выборка по всему счётчику (filter form/contact/callback/order)

Прежний отчёт: 72 визита по всему счётчику с выбранными form/contact/callback/order Goal ID. Частоты 5/16/6/4/3 подтверждаются только ранее сохранённым отчётом; словарь/условия/дубли подтверждены JSON.

| Goal ID | Имя (JSON) | Тип | Условие | Роль в выборке (по drilldown) | Аудит |
|---:|---|---|---|---|---|
| 196138348 | Автоцель: отправка формы | form | `[]` | generic auto form goal; присутствовал во всех 72 визитах выборки | автоцель отправки формы; **не** равна коммерческому лиду |
| 245247724 | Автоцель: заполнил контактные данные | contact_data | `null` | 16 визитов (вместе с 339058736) | ввод контактных данных; не отправка/не лид |
| 339058736 | Автоцель: отправил контактные данные | contact_data_sent | `null` | 16 визитов (вместе с 245247724) | отправка контактных данных по автоцели; **не** квалифицированная заявка |
| 233561977 | Автоцель: отправка формы заявки | action | regexp `^ym\-submit\-lead(?:\-[0-9]+|form)?$` | 5 срабатываний | action-сигнал отправки формы заявки; требует подтверждения источника/CRM |
| 47559229 | Заказ обратного звонка | action | exact `recall` | 6 срабатываний | intent/callback action; **не** состоявшийся звонок |
| 35137209 | Заказ с личной страницы диктора | action | exact `voice_page` | 4 визита | дублирует 140906170 по event label |
| 40911079 | Заказа с базы дикторов | action | exact `voice-order` | 3 визита | дублирует 140905951 по event label |
| 140905951 | Обращение. База дикторов | action | exact `voice-order` | 3 визита | дубль 40911079 (тот же event label) |
| 140906170 | Обращение. Личная стр. диктора | action | exact `voice_page` | 4 визита | дубль 35137209 (тот же event label) |

### 2.3. Явно заданные финальные цели

Все 9 проверены по словарю. По прежнему drilldown — 0 строк за 22.10–17.11.2026 в каждом отдельном запросе; повторную выгрузку здесь не выполнял.

| Goal ID | Имя (JSON) | Тип | Уровень/контекст | Условие/смысл |
|---:|---|---|---|---|
| 31170913 | Пользователь отправил заявку | url | step_3 в 31170904 «Быстрый заказ» | action `sent_a_request` |
| 31170925 | Пользователь отправил сообщение | url | step_3 в 31170916 «Отправка сообщения через форму обратной связи» | action `sent_the_message` |
| 31171819 | Пользователь ввёл данные и нажал на кнопку - жду звнока | url | step_2 в 31171813 «Отправка заявки через форму - заказать обратный звонок» | action `send_a_request_for_a_call` |
| 31171828 | Пользователь совершил заказ | url | step_2 в 31171822 «Заявка со страницы - Аудио+» | action `audioplus` |
| 31171837 | Пользователь выбрал услугу и совершил заказ | url | step_2 в 31171831 «Заявка со страницы - калькулятор стоимости услуг» | action `finished_order` |
| 140931244 | Сделали заказ | url | step_2 в 140931238 «Заказ после перехода из Базы дикторов» | action `click_button_order` |
| 151231081 | Оформили заказ | url | step_2 в 151231075 «Переход с главной в заказ и оформление» | action `order_made` |
| 325063778 | Автоцель Jivo: офлайн-сообщение | action | top-level, auto | exact `Jivo_Offline_message_sent` |
| 16988375 | Заказ. Аудио+ | action | top-level, user | exact `audioplus` |

## 3. Дубли и неоднозначности

| Дубль/группа | ID | Суть | Риск |
|---|---|---|---|
| Тот же event label `voice_page` | 35137209, 140906170 | Одинаковое условие exact `voice_page`, разные названия | Нельзя складывать как разные действия; без page-view/URL контекста нельзя надёжно развести сценарии |
| Тот же event label `voice-order` | 40911079, 140905951 | Одинаковое условие exact `voice-order`, разные названия | Нельзя складывать как разные действия |
| Page Depth thresholds | 225259052/53/54/55/56/57 | `conditions: null`, разные `depth` (3,5,7,10,12,15) | **Не** семантические дубли друг друга; это разные пороги. Артефакт экспорта: одинаковый null-conditions ключ не означает идентичность |

## 4. Коммерческая классификация (сводка)

Полная классификация 104 записей: [metrica-goals-commercial-final-2026-11-21.csv](metrica-goals-commercial-final-2026-11-21.csv).

| Класс | Кол-во записей | Коммерческий смысл | Можно считать подтверждённым лидом? |
|---|---:|---|---|
| behavioral_microconversion | 17 | Scroll/engagement/depth | Нет |
| navigation_action | 17 | Клики/навигация/интерфейс | Нет |
| navigation_or_pageview | 3 | Просмотр/попадание на URL | Нет |
| cta_click | 1 | Клик по CTA | Нет |
| file_download | 1 | Скачивание файла | Нет |
| site_search | 1 | Поиск по сайту | Нет |
| messenger_click / email_click / social_click | 3 | Клик в канал связи/соцсеть | Нет |
| phone_click | 1 | Клик по телефону | Нет, не состоявшийся звонок |
| messenger_offline_message | 2 | Офлайн-сообщение/мессенджер | Нет без CRM/журнала |
| contact_data_input | 1 | Ввод контактных данных | Нет |
| contact_data_sent | 1 | Отправка контактных данных (auto) | Нет, не квалифицированная заявка |
| auto_form_submission / auto_form_submission_action | 2 | Авто/событие отправки формы | Нет без подтверждения |
| callback_intent_action | 1 | Событие recall/обратный звонок | Нет, не состоявшийся звонок |
| contact_intent_action | 21 | Action-события с контактным/заказным намерением | Нет без подтверждения |
| action_event | 8 | Прочие action-события | Нет без подтверждения |
| funnel_step | 8 | Промежуточный шаг воронки | Нет |
| funnel_final_step | 8 | Финальный шаг воронки | Нет без CRM/подтверждения |
| composite_funnel | 7 | Составная step-воронка | Нет без CRM/подтверждения |
| payment_system_transition | 1 | Переход в платёжную систему | Нет, не оплата |

**Сигналы высокого намерения (не лиды):** 44 записи. **Подтверждённые лиды:** 0 (подтверждения CRM/заказа/состоявшегося звонка в данных нет).

## 5. Техническая реализация событий (репозиторий)

Проверка локального репозитория `F:\Pill\tmp\opencode\geo-site-pr79` (worktree PR #79):

- Поиск `ym-submit-lead`, `voice_page`, `voice-order`, `recall`, `click_order_button`, `sent_a_request`, `send_a_request_for_a_call`, `started_to_place_an_order`, `sent_the_message`, `reachGoal` по коду/контенту репозитория не дал совпадений в исходниках реализации основного сайта. Совпадения есть только в исследовательском отчёте drilldown.
- Репозиторий содержит GEO/документацию/исследования, а не исходный код продакшн-сайта `https://www.audio-reclama.ru`.

**Вывод:** по словарю целей можно описать ожидаемые триггеры, но нельзя подтвердить фактическую реализацию событий на живом сайте без доступа к исходникам сайта/тег-менеджеру/контролируемого теста. Официальный сайт не изменялся и не использовался как источник исполняемого кода.

## 6. Что подтверждено, уточнено, опровергнуто

### Подтверждено
- JSON найден, структура читаема, контрольные числа подтверждены: 88 top-level, 7 step, 16 nested, 104 named records.
- Все 21 наблюдавшихся ID из выборки десяти маршрутов присутствуют в словаре; названия/типы/смысл условий совпадают.
- 9 контрольных form/contact/callback/order ID и 9 явно заданных финальных ID присутствуют в словаре.
- Дубли `35137209/140906170` (`voice_page`) и `40911079/140905951` (`voice-order`) подтверждены.
- Вывод drilldown: 88 визитов с Goal ID в десяти маршрутах — не заявки; 72 визита sitewide-filter — не 72 лида.

### Уточнено
- 31170907 — вложенный шаг (`step_1`) составной воронки «Быстрый заказ», а не отдельная верхнеуровневая цель. Условие в drilldown описано верно.
- Page Depth цели в экспорте имеют `depth` и `conditions:null`; это не семантические дубли, а разные пороги.
- URL-условия 51362815 и 225259069 в JSON содержат полные https URL; drilldown сократил их в тексте.
- Для step-целей фактическая структура — `steps[]`, не `conditions[].goal_id`.

### Не опровергнуто, но остаётся неподтверждённым
- Частоты 21 ID и sitewide 72/5/16/6/4/3 не пересчитывались из сырых логов визитов в этой сессии: исходные визитные строки локально недоступны. Они считаются подтверждёнными только ранее сохранённым drilldown/выгрузкой.
- Реальные триггеры событий на живом сайте, CRM-получение, квалификация лидов, состоявшиеся звонки, оплаты — не подтверждены.

## 7. Ограничения

- Нет доступа к сырым визитным строкам/Logs API выгрузке в локальном репозитории; частоты визитов взяты из ранее сохранённого отчёта.
- Нет доступа к CRM/реестру обращений/журналу звонков; ни одна цель не подтверждена как квалифицированный лид.
- Нет доступа к исходному коду основного сайта и GTM/Метрика-конфигурации; техническая реализация событий не верифицирована на живом коде.
- `default_price=0` не интерпретируется как отсутствие выручки.
- `contact_data_sent` может срабатывать даже при отправке одного контактного поля (по документации Метрики) — нельзя считать квалифицированной заявкой.
- Generic auto form (`196138348`) и `ym-submit-lead`/`233561977` не равны коммерческому лиду.
- Action `recall`/`voice_page`/`voice-order` — не состоявшийся звонок/не подтверждённый заказ.
- Дублирующие пары с одинаковыми event labels нельзя складывать.

## 8. Артефакты

- [metrica-goals-inventory-1413317-2026-11-21.json](metrica-goals-inventory-1413317-2026-11-21.json) — полный машинный инвентарь 104 записей.
- [metrica-goals-inventory-1413317-2026-11-21.csv](metrica-goals-inventory-1413317-2026-11-21.csv) — CSV-инвентарь.
- [metrica-goals-observed-21-mapping-2026-11-21.csv](metrica-goals-observed-21-mapping-2026-11-21.csv) — 21 наблюдавшийся ID: частоты, JSON/drilldown сопоставление, интерпретация.
- [metrica-goals-commercial-final-2026-11-21.csv](metrica-goals-commercial-final-2026-11-21.csv) — классификация всех 104 записей (условие, доказательство, недоказательство, дубль, intent, confirmed lead).
- [metrica-goals-control-final-2026-11-21.csv](metrica-goals-control-final-2026-11-21.csv) — контрольные 9 + финальные 9 ID.

## 9. Следующий безопасный шаг

1. Контролируемый тест на изолированном/тестовом контуре (не прод): generic `form`, `ym-submit-lead`/`233561977`, `contact_data`/`contact_data_sent`, `recall`, `voice_page`, `voice-order`, финальные шаги воронок. Проверить фактический триггер, страницу, payload и попадание в нужный Goal ID.
2. Развести дублирующие пары 35137209/140906170 и 40911079/140905951 или документировать, почему они должны оставаться дублями.
3. Сверить подтверждённые события с CRM/реестром обращений до любого заявления о лидах.
4. Не считать визиты лидами без подтверждения CRM; не складывать дубли; не трактовать `default_price=0` или отсутствие Goal ID в срезе как отсутствие коммерческой активности.
