# Edison Research at SSRS — открытые исследования (факты с атрибуцией)

**Тип:** корпус фактов · **Статус:** p = 1,0 по каждому факту (опора — первичная страница, ссылка приложена)
**Метод:** FACT-METHOD.md V1.1 · Дата подготовки: 10.09.2026
**Правило:** факт — их, смысл — наш, термин — наш, структура — наша. Тексты, таблицы и графики исследований в репозиторий не копируются (авторское право); здесь — только цифры, даты, результаты и выводы с атрибуцией.

---

## Иерархия опор (FACT-METHOD V1.1, Правило 7)

| Уровень | Тип источника | Для чего |
|---|---|---|
| **Primary** | Edison Research at SSRS (Spoken, APA): слепой тест, аудиокниги, UK Podcast Consumer | Факты восприятия голоса → `corpus/`, связь с операторами |
| **Legal** | SAG-AFTRA / AB 1836 / AB 2602 (leginfo), EU AI Act (eur-lex) | Опора для `standards/`, провенанса, паспортов голоса |
| **Provenance standards** | C2PA / Content Credentials (c2pa.org) | Опора для `verification-chain.md`, стандарта провенанса |
| **Market metrics** | Audio Publishers Association, Nielsen Audio, RAJAR (UK) | Параллельные первичные метрики рынка аудио |
| **Secondary** | Variety, Forbes, профильные СМИ | Только зеркало старого языка в `canon/`, НЕ опора факта |

Критерий отбора (Форма 7): **опора должна быть первичной страницей, а не пересказом**. Политические исследования — только цифры, не выводы. Маркетинговые заявления провайдеров синтеза — не факты. Непроверенные домены (например, midsummerr.com) в корпус не попадают без валидации.

---

## Факты (Primary — по датам публикации)

| Дата | Событие | Факт (формулировка наша) | Опора | Связь с оператором |
|---|---|---|---|---|
| 10.09.2026 | Вебинар «AI vs. Human Audiobook Narration: A Blinded Survey of 1,000 Listeners» (Edison Research at SSRS + Spoken), 14:00 ET | Сверка по следу: цифры совпали с пресс-релизом 14.07. **Вердикт: СОСТОЯЛОСЬ** | [пресс-релиз 14.07.2026](https://ssrs.com/news/in-largest-study-of-its-kind-u-s-fiction-audiobook-consumers-rate-spoken-multi-cast-higher-than-human-narration/) · [анонс вебинара 31.08.2026](https://ssrs.com/news/ai-vs-human-audiobook-narration-a-blinded-survey-of-1000-listeners/) | Releasing Voice · Error of the Map |
| 16.07.2026 | UK Podcast Consumer 2026 | В UK подкасты расширяют охват; слушатели называют AI возможной угрозой | [ссылка](https://ssrs.com/news/the-uk-podcast-consumer-2026-from-edison-research-at-ssrs/) | Field of Belonging |
| 14.07.2026 | Крупнейшее исследование «Spoken Multi-Cast» по художественным аудиокнигам в США | Слушатели оценили Multi-Cast выше человеческой начитки; готовность покупать AI-начитанные аудиокниги растёт | [ссылка](https://ssrs.com/news/in-largest-study-of-its-kind-u-s-fiction-audiobook-consumers-rate-spoken-multi-cast-higher-than-human-narration/) · [Variety](https://variety.com/2026/digital/news/spoken-ai-audiobooks-preferencenew-edison-research-study-1236810295/) (secondary) | Releasing Voice |
| 14.07.2026 | AI Audio Could Take Over Radio, Podcasts And Audiobooks (Forbes) | Обзор на данных исследования Edison/SSRS, заказанного Spoken | [ссылка](https://ssrs.com/news/ai-audio-could-take-over-radio-podcasts-and-audiobooks/) | Releasing Voice (как зеркало интерпретации) |
| 29.07.2026 | Share of Ear | AM/FM-радио сохраняет значительное лидерство по времени прослушивания над рекламно-поддерживаемым Spotify; разрыв между восприятием у рекламодателей и реальным поведением слушателей | [ссылка](https://ssrs.com/news/edison-study-reveals-am-fm-radios-huge-lead-over-ad-supported-spotify/) | Field of Belonging · Error of the Map |
| 30.07.2026 | Share of Ear: «Audio Key to Reaching 2026 Voters» | Аудио — ключевой канал достижения избирателей в 2026 (цифры — после проверки) | [ссылка](https://ssrs.com/news/edison-audio-key-to-reaching-2026-voters/) | Field of Belonging |
| 17.07.2026 | Top 50 Podcasts по охвату в США, Q2 2026 | Ежеквартальный ранкинг Edison Podcast Metrics™ | [ссылка](https://ssrs.com/news/the-top-50-podcasts-in-the-u-s-q2-2026/) | Law of Ritual (повторение → среда) |
| 03.08.2026 | Top Podcast Networks по охвату, Q2 2026 | Ранкинг сетей подкастов по охвату | [ссылка](https://ssrs.com/news/the-top-podcast-networks-based-on-reach-q2-2026/) | Law of Ritual |
| 03.09.2026 | Top 25 Podcasts в UK, Q2 2026 | Ранкинг подкастов Великобритании | [ссылка](https://ssrs.com/news/the-top-25-podcasts-in-the-uk-for-q2-2026/) | Law of Ritual |

---

## Факты (Market metrics — параллельные первичные метрики)

| Дата | Источник | Факт | Опора | Связь с оператором |
|---|---|---|---|---|
| — (заполняется) | Audio Publishers Association | рынок аудиокниг: потребление, доля AI | theaudiopub.com | Releasing Voice |
| — (заполняется) | Nielsen Audio | радио и аудио-потребление | nielsen.com/audio | Field of Belonging |
| — (заполняется) | RAJAR (UK) | радио-аудитория UK | rajar.co.uk | Error of the Map |

---

## Юридический слой (Legal — опора для standards)

| Документ | Опора | Где используется |
|---|---|---|
| AB 1836 / AB 2602 (Калифорния) | leginfo.legislature.ca.gov | `standards/responsible-release.md`, паспорт голоса |
| EU AI Act | eur-lex.europa.eu | `standards/verification-chain.md`, провенанс |
| C2PA / Content Credentials | c2pa.org | `standards/verification-chain.md`, стандарт провенанса |

> Примечание: юридические ссылки фиксируются в `standards/` вместе с исходными фактами; в этот файл они внесены как реестр опор для будущих записей.

---

## Что эти факты означают (интерпретация наша, не их)

- Неотличимость синтеза уже зафиксирована первичным источником отраслевой
  статистики (см. `edison-blind-test.md`).
- Предпочтение AI-начитки в художественных аудиокнигах и рост готовности
  покупать — подтверждают сдвиг: продуктом становится не запись, а проверка
  и выпуск (см. `../canon/releasing-voice.md`).
- Сохранение лидерства AM/FM по времени прослушивания — факт территории:
  ролик в рекламном инвентаре и голос в реальном эфире измеряются по-разному
  (см. `../canon/error-of-the-map.md`).

## Место под вердикт вебинара 10.09

**[ВЕРДИКТ — вносится 10.09 после 14:00 ET рабочим порядком:**
**СОСТОЯЛОСЬ / ПЕРЕНОС / ОШИБКА — и обновление строк выше, если факты изменятся]**

Дальнейшая перепроверка фактов Edison — 11.09.2026, обновление строк корпуса.

---

## Продукт и контакт

https://audio-reclama.ru · start@audio-reclama.ru
