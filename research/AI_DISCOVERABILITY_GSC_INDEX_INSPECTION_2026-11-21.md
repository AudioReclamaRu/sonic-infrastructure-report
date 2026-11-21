---
type: measurement_report
date: 2026-11-21
lang: ru
status: read_only_google_url_inspection_snapshot
related:
  - research/AI_DISCOVERABILITY_COMMERCIAL_ROUTE_REFRESH_2026-11-21.md
  - research/AI_DISCOVERABILITY_RU_BUYER_ANSWER_ROUTE_MAP_2026-11-21.json
  - research/AI_DISCOVERABILITY_TECHNICAL_SEMANTIC_AUDIT_2026-11-19.md
  - https://www.audio-reclama.ru
---

# Проверка индексации коммерческих маршрутов через Google Search Console

**Дата чтения:** 21.11.2026  
**Источник:** URL Inspection API через подключённое Google Search Console property https://www.audio-reclama.ru.  
**Режим:** только чтение; URL Inspection показывает сохранённое состояние Google, не выполняет live crawl и не меняет сайт.

## 1. Результат

Все семь проверенных URL вернули verdict=PASS, robotsTxtState=ALLOWED, indexingState=INDEXING_ALLOWED, pageFetchState=SUCCESSFUL. В каждом случае Google выбрал канонический URL с HTTPS и www, совпадающий с проверяемым адресом.

Это подтверждает, что на момент снимка эти семь страниц разрешены для индексации Google и присутствовали в его индексе. Это не доказывает высокую позицию, AI-цитирование, доступность для всех поисковых роботов, качество ответа ИИ или получение коммерческих обращений.

## 2. Проверенные страницы

| Страница | Google URL verdict | Robots | Fetch | Последний обход Google (UTC) | Google canonical |
|---|---|---|---|---|---|
| Главная | PASS | ALLOWED | SUCCESSFUL | 2026-11-16 10:54:07 | совпадает |
| Радиоролики | PASS | ALLOWED | SUCCESSFUL | 2026-10-30 05:38:02 | совпадает |
| IVR | PASS | ALLOWED | SUCCESSFUL | 2026-11-10 10:54:52 | совпадает |
| Аудиокниги | PASS | ALLOWED | SUCCESSFUL | 2026-11-10 12:13:05 | совпадает |
| Озвучивание видео | PASS | ALLOWED | SUCCESSFUL | 2026-10-20 23:30:38 | совпадает |
| Джинглы / звуковые решения | PASS | ALLOWED | SUCCESSFUL | 2026-11-03 09:18:29 | совпадает |
| Перевод / локализация | PASS | ALLOWED | SUCCESSFUL | 2026-11-15 21:22:15 | совпадает |

Все URL проверялись на свойстве с каноническим www-хостом и все вернули mobile crawl. Поле mobileUsabilityResult.verdict в ответах было VERDICT_UNSPECIFIED; этот результат нельзя трактовать ни как PASS, ни как ошибку mobile usability.

## 3. Что это меняет в приоритетах

1. **Не нужно считать Google indexability блокером для этих семи RU-страниц.** В текущем снимке Google может их обходить и индексировать.
2. **Коммерческое несоответствие и качество ответа остаются отдельной задачей.** Например, у IVR остаётся низкий CTR и запросы на дальних позициях; успешная индексация сама по себе не решает проблему релевантности и понятности предложения.
3. **Аудиокниги остаются самым сильным из десяти проверенных сервисных URL по кликам за 22.10–18.11.2026, но это органический поиск, а не подтверждённые сделки.**
4. **Следующая техническая проверка должна быть бот-специфичной.** Google URL Inspection не доказывает, что OAI-SearchBot или другие AI-роботы получают те же ответы от robots.txt, CDN, WAF и HTML.

## 4. Неизвестное и ограничения

- URL Inspection показывает сохранённое состояние Google. lastCrawlTime — дата последнего обхода Google, а не дата проверки инструмента.
- Наблюдение robotsTxtState=ALLOWED относится к Google URL Inspection. Оно не подтверждает правила доступа для каждого другого user-agent.
- Прямое открытие https://www.audio-reclama.ru/robots.txt, https://www.audio-reclama.ru/llms.txt и https://www.audio-reclama.ru/sitemap.xml через доступный публичный web-reader в этом проходе вернуло ошибку инструмента «not accessible». Это NOT_RETRIEVED_BY_READER, а не доказательство HTTP-блокировки или отсутствия файлов.
- Не проверялись CDN/WAF server logs, фактический User-Agent, HTTP status по каждому роботу, содержимое ответа на OAI-SearchBot, Bingbot, Googlebot и другие AI-поверхности.
- Не проводились form submission, live call, коммерческая покупка или AI prompt collection.

## 5. Вердикт

**Google RU service-page indexability: PASS for 7/7 inspected URLs.**  
**AI crawler access beyond Google: NOT_TESTED.**  
**AI mention/citation visibility: NOT_MEASURED.**  
**Live lead / CRM outcome: NOT_MEASURED.**

Рекомендация — не переписывать robots.txt или sitemap на основании этого результата. Сначала получить текущий файл и бот-специфичную проверку с допустимым read-only способом; любые изменения — только по отдельному разрешению владельца.

Официальный сайт: https://www.audio-reclama.ru
