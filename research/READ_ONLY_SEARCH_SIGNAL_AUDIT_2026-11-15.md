---
type: doc
date: 2026-11-15
lang: ru
related:
  - evidence/E-2026-048.md
  - research/READ_ONLY_SEARCH_SIGNAL_AUDIT_2026-11-14.md
  - problem-solutions/MEASUREMENT_PROTOCOL.md
  - strategy/SITE_TRAFFIC_GROWTH_MANDATE_2026-11-15.md
  - strategy/ATTENTION_ACQUISITION_SYSTEM.md
---
# Поисковый сигнал Audio-Reclama.ru: live read-only срез от 2026-11-15

**Статус:** подтверждённые наблюдения, выводы по правилам роботов и приоритизированные возможности.  
**Дата:** 2026-11-15.  
**Граница:** проверялись только общедоступные страницы и исходный HTML. Сайт, sitemap, robots.txt, метаданные и публикационные механизмы не изменялись. Это не полный crawl всех 1 186 URL и не отчёт о поисковой эффективности.

Подробные источники и доказательственные границы: [E-2026-048](../evidence/E-2026-048.md). Предыдущий срез: [2026-11-14](READ_ONLY_SEARCH_SIGNAL_AUDIT_2026-11-14.md).

## 1. Что изменилось и что подтвердилось

| Область | Наблюдение 15.11.2026 | Приоритет |
|---|---|---|
| Sitemap | 1 186 URL, 1 186 уникальных; 0 lastmod; changefreq=daily у всех | контроль качества источника |
| Мёртвые профили | 2 URL HTTP 404 всё ещё включены в sitemap | **P0** |
| Старый URL отзывов | /clients.html остаётся в sitemap, но запрос открывает /feedbacks.html | **P0** |
| Английская версия | /en/ есть в sitemap; 3 проверенных English project pages — HTTP 200 и есть внутренние ссылки, но sitemap их не содержит | **P1** |
| Robots / English | Disallow: /en/* и Allow: /en/; по longest-match правилу Google вложенные /en/... попадают под более длинный Disallow | **P1, если английские кейсы должны получать поисковый трафик** |
| Главная | Description по-прежнему говорит об «искусстве звука», но не объясняет конкретное предложение студии | **P1/P2 opportunity** |
| IVR | Description заявляет 1 000 ₽ и 1 день, но тело страницы эти условия не показывает | **P1 — требуется подтверждение владельца** |
| Canonical | В четырёх выбранных шаблонах не найден rel=canonical | **P2 — проверить политику, не объявлять site-wide defect** |
| Измерение | Search Console / Яндекс Вебмастер / GA4 data не представлены в этом срезе | baseline UNKNOWN |

### P0 — очистить sitemap от URL, не ведущих на самостоятельные индексируемые страницы

Подтверждено, что:
- https://www.audio-reclama.ru/diktoryi/zhenskie-diktor-golosa/russian-diktor-natalia-belenkaia.html возвращает HTTP 404;
- https://www.audio-reclama.ru/diktoryi/inostrannye-diktor-golosa/bulgarian-diktor-yavor.html возвращает HTTP 404;
- оба адреса всё ещё находятся в sitemap;
- https://www.audio-reclama.ru/clients.html всё ещё находится в sitemap, но разрешается в контент https://www.audio-reclama.ru/feedbacks.html.

**Что поручить администратору сайта:**
1. Удалить подтверждённые 404 URL из sitemap. Если профили удалены навсегда и нет близкой замены — оставить 404/410, не перенаправлять на главную «для спасения SEO».
2. Если у профиля есть реальная актуальная замена, использовать релевантный постоянный redirect и оставить в sitemap только конечный предпочтительный URL.
3. Удалить /clients.html из sitemap и включать /feedbacks.html как конечный URL.
4. Провести полный проверочный обход всех URL sitemap: конечный HTTP-код, число редиректов, canonical, robots/noindex, внутренние ссылки. Сохранить точный список исключений.

Критерий проверки: ни один URL в sitemap не должен вести на 404 или на промежуточный redirect; все адреса должны быть предпочтительными URL, которые действительно предназначены для результатов поиска. Это соответствует официальным рекомендациям Google по содержимому sitemap: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap.

### P1 — решить судьбу английских кейсов и устранить противоречие robots/sitemap

Три проверенные страницы существуют и возвращают HTTP 200:
- https://www.audio-reclama.ru/en/project/globus-group.html
- https://www.audio-reclama.ru/en/project/braun.html
- https://www.audio-reclama.ru/en/project/vnukovo.html

Английская главная /en/ содержит ссылки на English project pages. При этом:
- sitemap содержит только одну страницу с префиксом /en/ — саму /en/;
- robots.txt запрещает /en/*, разрешая только /en/;
- согласно опубликованной Google спецификации, наиболее длинное совпадающее правило имеет приоритет; для вложенного URL /en/project/... более длинным совпадением является Disallow: /en/*. Источник: https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec.

**Решение зависит от намерения владельца:**

Если English pages должны привлекать поисковый трафик:
1. Разрешить обход реальных English landing/project pages в robots.txt, не открывая случайно технические, корзинные или служебные URL.
2. Добавить в sitemap только те английские страницы, которые имеют уникальное полезное содержание и предназначены для индексации.
3. Согласовать self-canonical на английские URL и hreflang RU/EN для парных страниц; проверить x-default отдельно.
4. Проверить English link graph: страницы услуг, кейсы, каталог, контакты и пути заказа должны связываться без возврата на русские URL, если есть полноценная английская версия.

Если английский раздел намеренно не должен получать поисковый трафик, нужно убрать противоречие между внутренними ссылками/публичной подачей и crawl policy: явно зафиксировать назначение раздела, не создавать видимость indexable-section и не включать его страницы в sitemap.

Нельзя объявлять, что Google уже не индексирует эти страницы. HTTP 200 и robots rule показывают доступность сервера и потенциальное правило обхода; реальное состояние индекса нужно проверить в Search Console.

### P1 — подтвердить цену и срок на странице IVR

Текущий meta description страницы https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html заявляет:
- цена от 1 000 ₽;
- срок готовности — 1 день.

В видимой части страницы эти значения не обнаружены. Это не доказывает, что условия неверны, но поисковый сниппет обещает конкретные условия, которые посетитель не может подтвердить по основному тексту.

**Нужно решение владельца услуги:**
- если цена и срок действительно действуют для соответствующего стандартного предложения — добавить ясные условия и ограничения в видимый текст страницы;
- если расчёт индивидуальный или сроки зависят от задачи — заменить метаописание на точное описание услуги без неподтверждённых цен/сроков;
- синхронизировать метаданные, видимую страницу, внутреннюю коммерческую базу и ответы менеджеров.

Я не менял метаданные и не трактовал старую цифру как действующий прайс.

### P1/P2 — сделать сниппет главной страницы конкретным

Текущая главная:
- Title: «Аудио-Реклама•ru — Флагман деловой звукозаписи»
- Description: «Искусство звука и утончённость идей даруют вашему бренду исключительную привлекательность.»

Description эмоционально звучит, но не объясняет поисковому пользователю, какие задачи решает студия. В видимой навигации и на сайте присутствуют рекламные аудиоролики, запись дикторов, IVR, перевод/локализация и видеопродакшн.

**Редакционная гипотеза для владельца/администратора (не опубликована):**
«Аудио-Реклама•ru — студия аудиопродакшна: рекламные аудиоролики, подбор и запись дикторов, голосовые меню IVR, перевод и локализация, озвучивание видео. Послушайте примеры и отправьте задачу.»

Перед использованием проверить реальный актуальный набор услуг, географию, языки и желаемый tone of voice. Не обещать все услуги в одном description, если это не соответствует текущему коммерческому предложению.

### P2 — проверить canonical-политику на шаблонах

В raw HTML четырёх выборочных страниц не обнаружен rel=canonical:
- главная;
- каталог дикторов;
- IVR;
- английская главная.

Это не самостоятельное доказательство ошибки: Google может выбирать canonical самостоятельно, а rel=canonical не является обязательным тегом для каждой страницы. Но на сайте есть несколько языков, конечные URL после redirects и большой каталог. Поэтому нужно:
1. проверить выбранный Google canonical в Search Console;
2. определить один предпочтительный URL на каждую страницу (https, www, path/slash);
3. для индексируемых canonical pages, где это соответствует архитектуре, добавить self-referential canonical;
4. синхронизировать canonical, sitemap и hreflang. Для языковых страниц canonical должен вести на версию соответствующего языка или лучший доступный эквивалент.

Официальная рекомендация Google: https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls.

### P2 — обновлять sitemap от фактической базы контента

В текущем XML нет lastmod, зато всем URL назначен changefreq=daily. Не придумывать lastmod. Лучший путь — не ручное сканирование списка внешним генератором, а генерация sitemap из реестра активных и индексируемых страниц CMS:
- включать только опубликованные страницы с самостоятельной ценностью;
- исключать deleted/404, redirects, закрытые query pages и дубликаты;
- указывать lastmod только при достоверной дате значимого изменения;
- не полагаться на changefreq как на гарантию частоты обхода.

## 2. Что делать дальше в growth-контуре

1. Администратор подтверждает судьбу двух 404-профилей и старого /clients.html.
2. Владелец подтверждает судьбу английского раздела: поисковый канал или только вспомогательная языковая поверхность.
3. Владелец подтверждает реальные IVR price/time terms.
4. После доступности Search Console / GA4 / Яндекс Вебмастера фиксируется baseline: branded/non-branded clicks, impressions, CTR, avg position, sessions, engagement, enquiries/conversions.
5. Затем проверяется реальный эффект исправлений и приоритизируются новые входные страницы.

## 3. Ограничения

- Сайт проверялся только на чтение; патчи не применялись.
- Полный обход всех 1 186 URL не проведён; индивидуально перепроверены две 404-страницы, один redirecting URL и три английские страницы.
- Не проверены Google Search Console, Яндекс Вебмастер, GA4, CRM, логи сервера, Core Web Vitals и фактический индексный статус страниц.
- При отсутствии доступа baseline и поисковая эффективность остаются UNKNOWN.
- Никакого прироста трафика не заявляется.

## 4. Источники

- Live sitemap: https://www.audio-reclama.ru/sitemap.xml
- Live robots: https://www.audio-reclama.ru/robots.txt
- Home: https://www.audio-reclama.ru/
- Narrator catalog: https://www.audio-reclama.ru/diktoryi/
- IVR service page: https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html
- English home: https://www.audio-reclama.ru/en/
- English projects: https://www.audio-reclama.ru/en/project/globus-group.html, https://www.audio-reclama.ru/en/project/braun.html, https://www.audio-reclama.ru/en/project/vnukovo.html
- Google robots.txt specification: https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec
- Google sitemap guidance: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- Google canonical guidance: https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls

## Footer

«Аудио-Реклама•ru»  
Audio-Reclama.ru  
https://audio-reclama.ru
