---
type: research-report
date: 2026-11-19
lang: ru
status: source-backed-live-audit
related:
  - research/AI_DISCOVERABILITY_LANGUAGE_ROADMAP_2026-11-19.md
  - research/AI_VISIBILITY_BENCHMARK_PROTOCOL_2026-11-17.md
  - llms.txt
---

# AI Discoverability «Аудио-Реклама•ru»: технический и смысловой аудит

**Дата live-среза:** 19.11.2026  
**Объект:** официальный сайт, публичная база знаний GitHub, поисковые и AI-поверхности  
**Цель:** найти барьеры между реальной глобальной производственной способностью студии и тем, что роботы, поисковые системы, AI-ассистенты и покупатели способны обнаружить, понять, проверить и использовать для выбора поставщика.

## 0. Главный вывод

Самый большой разрыв сейчас — не отсутствие ещё одного файла llms.txt и не недостаток переводов в Git. У «Аудио-Реклама•ru» уже есть международные проекты, англоязычные страницы кейсов, многоязычные каталоги дикторов, переводческое направление и глобальная производственная сеть. Но это знание плохо собрано в доступную языковую карту сайта: поисковая карта содержит только главную страницу /en/, английская главная ведёт на ряд русскоязычных страниц услуг, а публичные страницы английских кейсов не включены в sitemap.

Второй разрыв — сущность компании кодируется разными именами. Видимая идентичность, Open Graph и существующий Organization JSON-LD не совпадают по написанию. Для машин это лишняя неоднозначность при entity resolution.

Третий разрыв — измерение. Подключённая Search Console уже принадлежит владельцу сайта, но AI-специфический отчёт Google и AI Performance в Bing не входят в текущий API-коннектор OpenSEO. При этом GA4 web stream создан 17 ноября 2026 года, его default URI указан без www, а в подключённом периоде не возвращается полезная выборка трафика. Поэтому пока нельзя построить достоверную воронку «AI-цитата → переход → обращение».

**Ключевая поправка по возможностям:** владелец 19.11.2026 подтвердил, что производство возможно для любой языковой группы в любой точке мира благодаря международной сети связей и исполнителей. Это глобальная производственная способность. Она не означает наличие офисов или филиалов во всех странах. Языковые волны в настоящем документе — порядок развития AI-discovery-контента и измерений, а не предел производственной доступности.

## 1. Классификация доказательств

- **LIVE-OBSERVED:** факт проверен по публичному HTML, robots.txt или sitemap на 19.11.2026.
- **OWNER-CONFIRMED:** владелец прямо подтвердил способность или внутренний факт 19.11.2026; это не следует выдавать за независимую проверку.
- **PLATFORM-DOCUMENTED:** правило из официальной документации поисковой или AI-платформы.
- **INFERENCE:** техническое или смысловое следствие, выведенное из наблюдений; это не лог сервера и не доказательство конкретного факта индексации.
- **RECOMMENDATION:** предлагаемый способ устранения. Любое изменение официального сайта требует отдельного разрешения; сайт в данном рабочем контуре остаётся read-only.

## 2. P0 / P1 — проблемы, которые сильнее всего влияют на обнаружение и выбор

### P0-A. Англоязычная карта сайта неполная

**LIVE-OBSERVED:** текущий sitemap содержит 1 186 URL. В нём обнаружена одна страница с путём /en/ — английская главная. В sitemap не обнаружены /en/project/* и /en/online-zakaz.html. При этом английская главная содержит ссылки на английские кейсы, включая ABBYY, Braun, Vnukovo, Globus Group, Renaissance Credit и другие, а также на английскую форму заказа.

**Почему это важно:** sitemap — дополнительный маршрут обнаружения, не гарантия индексации. Но при отсутствии записи в sitemap поисковый робот сильнее зависит от внутренних ссылок и уже известных URL. Сейчас потенциально ценные англоязычные страницы кейсов не представлены в sitemap, несмотря на существование русско-английских пар страниц и ссылок с главной.

**RECOMMENDATION:** включать в sitemap все канонические, индексируемые, реально существующие языковые страницы: EN service pages, EN project pages, EN order/contact routes и будущие локализованные посадочные страницы. Не включать параметры, дубли, закрытые формы и страницы без самостоятельной ценности. Добавлять lastmod только при реальном изменении основного содержимого. Google документирует, что priority и changefreq игнорируются, а lastmod использует при условии достоверности.

**Проверка после изменения:** сопоставить sitemap с crawl inventory; проверить несколько URL через Google URL Inspection и Bing URL Inspection; убедиться, что sitemap URL совпадает с self-canonical URL и даёт 200.

### P0-B. Английский вход не ведёт к полному англоязычному пути покупателя

**LIVE-OBSERVED:** на /en/ HTML имеет lang="en", а сама страница действительно содержит английский текст. Однако ссылки с англоязычной главной на страницы рекламного аудио, IVR, перевода, дикторов и аудиокниг ведут преимущественно на русскоязычные URL. Английские кейсы и английская форма заказа существуют как отдельные URL, но не включены в sitemap.

**Смысловой эффект:** международный покупатель может понять отдельный кейс, но не получает непрерывный путь «потребность → конкретная услуга → доказательство → технический бриф → обращение» на своём языке. AI-система тоже вынуждена собирать сведения из смешанных языковых источников и может неверно классифицировать область предложения как преимущественно русскоязычную.

**RECOMMENDATION:** создать полноценные native-language service routes, начиная с английского, затем Wave A (испанский, бразильский португальский, арабский) и следующие AI-значимые языки. Это не механический перевод меню: каждая страница должна отвечать на конкретный buyer intent и вести к релевантному кейсу, брифу и форме. Существующая русская страница остаётся первичным коммерческим источником до появления её локализованной версии.

### P0-C. Неверное имя организации в уже работающем JSON-LD

**LIVE-OBSERVED:** в HTML главной, английской главной, английского кейса Внуково, страницы перевода и страницы IVR найден один и тот же Organization JSON-LD. Его поле name содержит неканоническое кириллическое написание с точкой вместо символа •. В английском Open Graph также используется латинская доменная форма вместо утверждённого имени компании.

**Почему важно:** это не отсутствие structured data; разметка уже есть. Проблема — противоречивая идентичность одного и того же объекта на разных машинно-читаемых и социальных поверхностях. Это создаёт неоднозначность для entity matching и внешних графов знаний.

**RECOMMENDATION:** на официальном сайте (после отдельного разрешения) выровнять Organization name строго к «Аудио-Реклама•ru», url к https://www.audio-reclama.ru, добавить постоянный @id вида https://www.audio-reclama.ru/#organization; проверять, чтобы описание и sameAs отражали одну и ту же компанию. sameAs оставлять только для подтверждённых официальных профилей, а не для похожих страниц, неясных старых каналов или каталогов. Не добавлять несуществующие адреса и офисы.

**Важно:** Google прямо говорит, что специальной Schema.org-разметки для AI Overviews/AI Mode нет. Organization markup полезен как ясное описание сущности и поддержка поисковой интерпретации, но не является самостоятельным рычагом ранжирования или гарантией AI-цитаты.

### P1-A. Open Graph URL и имя сайта расходятся на английских страницах

**LIVE-OBSERVED:**
- На RU- и EN-главной выводятся два значения og:url для корневой страницы: одно с завершающим слешем, другое без него. Каноническая запись корневого URL — https://www.audio-reclama.ru.
- На английской главной один из og:url указывает на русскую главную.
- На английском кейсе Внуково один og:url указывает на RU-страницу кейса, а второй — на главную.
- На EN-страницах og:site_name использует латинскую доменную форму вместо канонического имени, тогда как на RU-главной есть каноническое имя.

**RECOMMENDATION:** один og:url на страницу и его точное совпадение с каноническим URL этой страницы; один og:site_name со значением «Аудио-Реклама•ru». Open Graph не заменяет canonical и сам по себе не решает Google-индексацию, но используется внешними системами при разборе ссылок и формировании превью.

### P1-B. На пяти проверенных HTML-страницах не найден явный canonical link

**LIVE-OBSERVED:** при разборе raw HTML head пяти страниц — RU home, EN home, EN case Vnukovo, EN order и RU IVR/language category — тег link rel="canonical" не обнаружен. Это ограниченное выборочное наблюдение, а не полный аудит всех 1 186 URL и не проверка HTTP Link headers.

**RECOMMENDATION:** сделать единый URL policy: HTTPS, host www.audio-reclama.ru, понятная политика trailing slash для корня и путей, один canonical URL для каждой страницы. Каждая локализованная версия должна canonicalize на саму себя, а не на страницу другого языка. Языковые альтернативы связываются через reciprocal hreflang; canonical и hreflang решают разные задачи.

### P1-C. Английские Title, Description и H1 не отражают всю бизнес-категорию

**LIVE-OBSERVED:** английская главная использует общий title о media production, H1 The trusted business sound recording solutions и description, сосредоточенное на рекламном контенте для телевидения и радио, быстром ответе и коротких сроках. Это не отражает всю представленную на сайте область: IVR, автоматические объявления, многоязычный голос, перевод/локализация, видеоозвучивание, аудиокниги, джинглы, корпоративные песни и другие направления.

**RECOMMENDATION:** переписать Title, H1 и description на конкретный ясный английский профиль: business audio and voice production studio, работа по миру, любая языковая группа, перечень основных задач. Не использовать «full-cycle» как обещание, что любой проект включает все этапы. Не обещать срок без подтверждённой SLA.

### P1-D. Каталоги языков не равны локализованным коммерческим страницам

**LIVE-OBSERVED:** sitemap содержит 61 уникальный slug вида /diktoryi/filter/language-…/ и 304 варианта языковых/категорийных URL. Однако проверенная страница арабских дикторов имеет lang="ru", русский title и русское описание. Это страница каталога с фильтром по языку, а не арабская коммерческая посадочная страница.

**Смысловой эффект:** AI может увидеть список дикторов и назвать наличие голосов, но не обязательно поймёт, что студия может решать задачу целиком: локализовать сценарий, организовать подбор носителя или исполнителя, запись, продакшн, проверку и сдачу файла заказчику в любой языковой группе.

**RECOMMENDATION:** оставить каталоги голосов как отдельный proof/selection layer. Создать native-language service landing pages для приоритетных языков и задач. В каждой странице описывать полный пользовательский сценарий и глобальную сеть производства, не выдавая каталог голосов за полный каталог услуг или локальный офис.

### P1-E. Устаревшие и поэтически-общие описания не объясняют коммерческую ценность

**LIVE-OBSERVED:** английский description ограничен ТВ/радиорекламой и общими обещаниями индивидуального подхода/быстрого ответа. Русский description главной — образный слоган об искусстве звука, но не прямое объяснение, кому и что делает студия.

**RECOMMENDATION:** оставить брендовый слоган как творческий слой, но дополнить его прямым фактическим абзацем: кто компания, какие задачи решает, как устроена глобальная языковая сеть, какие deliverables доступны, где проходит граница между голосовой записью и системной настройкой. Уникальная экспертиза и конкретные доказательства важнее красивых общих формулировок.

## 3. Robots.txt и доступ краулеров: что действительно установлено

Текущий robots.txt содержит группу User-agent: *, в том числе:
- Disallow: /en/*
- Allow: /en/
- Disallow: /*?
- разрешения для ряда assets/CSS/JS и ссылка на sitemap.

**Уточнение по результатам Google Search Console URL Inspection от 20.11.2026 — прежний вывод нельзя считать подтверждённым.** В последней сохранённой инспекции Google фиксирует `ROBOTS_TXT_STATE_DISALLOWED` и `PAGE_FETCH_STATE_BLOCKED_ROBOTS_TXT` для английских URL:
- `/en/`: URL остаётся в индексе, несмотря на блокировку; последняя дата обхода 17.11.2026.
- `/en/project/vnukovo.html`: блокировка robots.txt при последнем обходе 16.11.2026.
- `/en/project/abbyy.html`: блокировка при последнем обходе 11.11.2026.
- `/en/project/braun.html`: блокировка при последнем обходе 11.11.2026.
- `/en/project/renessans-credit.html`: URL неизвестен Google; это отдельный статус, не доказательство robots-блокировки.
- `/en/online-zakaz.html`: запрос URL Inspection завершился timeout; статус не установлен.

**Важное ограничение доказательства:** Search Console сообщает состояние на момент последнего зафиксированного обхода URL, а не выполняет в этом ответе свежий live-тест текущего robots.txt. В HTML/robots-снимке 19.11.2026 записана пара `Disallow: /en/*` + `Allow: /en/` в группе `User-agent: *`. По опубликованной Google спецификации trailing wildcard и приоритет наиболее специфичного правила должны быть разобраны точно; одна эта пара без полного актуального файла и проверки эффективной группы не объясняет расхождение с историческими URL Inspection. Текущий live robots.txt в этой проверке повторно получить не удалось.

**Вывод на 20.11.2026:** существует подтверждённый исторический факт, что Google не смог обойти несколько важных EN-кейсов из-за robots.txt. Нельзя утверждать, что блокировка остаётся активной сегодня, пока не проверен текущий файл и не выполнен свежий URL Inspection. Нельзя и считать английский раздел доступным: текущий снимок GSC этого не доказывает. Это P0-проверка перед любыми изменениями sitemap или международного контента.

**Следующая проверка:** получить полный актуальный `robots.txt`; проверить все `User-agent` groups и порядок правил; выполнить live URL Inspection для корня и каждой EN-страницы; отдельно проверить `Googlebot`, `OAI-SearchBot`, `Bingbot` и другие search crawlers. Только после этого готовить минимальное изменение, если блокировка подтверждается.

### Минимальная bot policy для международного AI Search

Разделять роботов по их назначению; не смешивать поиск, пользовательский fetch и обучение:

| User-agent | Для чего нужен | Действие, если цель — AI Search |
|---|---|---|
| Googlebot | Google Search, включая AI Overviews/AI Mode links | Не блокировать публичные сервисные и кейс-страницы |
| Bingbot | Bing Search и поддерживаемые Copilot/AI surfaces | Не блокировать публичные сервисные и кейс-страницы |
| OAI-SearchBot | Поисковое обнаружение и ссылки в ChatGPT Search | Разрешить, если нужна обнаруживаемость в ChatGPT Search |
| ChatGPT-User | Fetch по запросу пользователя, не автоматический crawler для Search | Решить отдельно от OAI-SearchBot |
| GPTBot | Возможное использование контента для обучения моделей OpenAI | Отдельное решение о training; не путать с поисковой видимостью |
| Claude-SearchBot | Индексация/поиск Anthropic | Разрешить для Claude search visibility |
| Claude-User | Пользовательский fetch в Claude | Решить отдельно |
| ClaudeBot | Сбор для возможного обучения моделей Anthropic | Отдельное решение |
| PerplexityBot | Поисковый crawler Perplexity | Разрешить для видимости в поиске Perplexity |
| Perplexity-User | Пользовательские действия в Perplexity | Решить отдельно |

Google-Extended — не отдельный HTTP user-agent. Это robots token для контроля использования контента в некоторых Google AI системах; он не заменяет Googlebot и не управляет обычной индексацией Google Search.

**WAF/CDN не менее важен, чем robots.txt.** Даже корректный Allow не помогает, если firewall блокирует IP crawler. Проверять официальные опубликованные IP ranges конкретных платформ, WAF challenges, rate limits и реальные server/CDN logs. Не разрешать ботов только по подделываемой строке User-Agent без проверки IP/подписи. Сбор логов пока не выполнялся, поэтому фактическая доля успешно прошедших AI-кроулеров неизвестна.

**Правило для будущих точечных групп:** Google выбирает наиболее специфичную user-agent group и не смешивает её автоматически с User-agent: *. Если будут добавлены отдельные группы для AI bots, надо не потерять необходимые общие Allow/Disallow правила, sitemap и ресурсные исключения. Ошибочная короткая группа может непреднамеренно обойти существующую политику или закрыть нужный путь.

## 4. Многоязычная структура: правильная модель

### 4.1 Одна организация, а не отдельные «бренды по языкам»

- Одна организация: «Аудио-Реклама•ru».
- Один устойчивый идентификатор Organization в JSON-LD.
- Языковые версии — разные читательские интерфейсы и входы к той же сущности.
- Локальные страницы не означают офис или юридическое лицо в конкретной стране.
- Глобальная производственная способность подтверждена владельцем; языковые волны определяют, в каком порядке мы делаем AI-discovery-контент и измерения.

### 4.2 URL, lang, canonical, hreflang

Для каждого действительно локализованного материала:
1. отдельный стабильный URL;
2. корректный html lang по основному языку видимого контента;
3. self-canonical на собственный URL;
4. reciprocal hreflang только между эквивалентными страницами;
5. понятная ссылка-переключатель языка, доступная без JS;
6. страница включена в sitemap, если она canonical, индексируема и содержит самостоятельную ценность.

Google поддерживает language code ISO 639-1 и необязательный region ISO 3166-1 alpha-2. es-419 не поддерживается как значение Google hreflang; использовать es, es-ES, es-MX, es-AR и другие действительные языково-страновые пары по реальному содержимому. x-default лучше всего указывать на нейтральный language selector или понятную fallback-страницу. Не ставить hreflang на неэквивалентные страницы и не забывать обратные ссылки.

### 4.3 Язык страницы должен соответствовать содержимому

Фильтр «арабские дикторы» со страницей на русском не становится арабской посадочной страницей от одного slug. Для арабской версии нужны арабские H1, summary, body, CTA и FAQ, корректный direction RTL, доступные поля формы, транслитерация и поддержка записи имён/чисел. То же правило для испанского, португальского, турецкого, немецкого, французского, японского, корейского, китайского и остальных языков.

### 4.4 Продакшн не ограничен списком AI-языков

Список AI-значимых языков определяет приоритет локализации интерфейсов, контента и benchmark. Он не ограничивает студию: производство организуется для любой языковой группы мира через глобальную сеть связей. Не путать язык запроса, язык страницы, язык диктора, страну пользователя, locale интерфейса и рынок исполнения.

## 5. Семантическая архитектура, нужная для AI answers

Для каждой важной услуги нужен прямой ответ на естественный вопрос покупателя, затем:
- задача клиента и ситуации, в которых услуга нужна;
- состав работ и конкретный output;
- что требуется от заказчика;
- workflow: brief → текст/адаптация → casting → запись → обработка → QC → delivery;
- технические входы и ограничения получающей системы;
- границы ответственности (например, аудиофайлы IVR ≠ настройка PBX);
- применимые языки/локали и как организуется работа по всему миру;
- rights, usage territory, term and approvals;
- реальные проекты/образцы с корректными оговорками;
- понятный CTA и маршрут к коммерческому брифу.

Отдельные buyer intents, которые нельзя сваливать в одну страницу:
- audio/radio commercial production;
- multilingual announcement systems for airports, transport and public venues;
- IVR/telephone greeting voice prompts;
- video voice-over and localization;
- audiobook production;
- jingles, sonic identity and corporate songs;
- presentation/e-learning voice;
- translation and multimedia localization.

### Принцип direct answer

Начало страницы должно отвечать в одном-двух абзацах: что именно предлагается, кому, какой deliverable получает покупатель и какую часть работ выполняет студия. Далее — evidence, process, comparison, FAQ and CTA. Не писать страницу только ради перестановки ключевых слов или машинного цитирования.

### Что усиливает доказательность

- детальная карточка проекта с датой/периодом, задачей, deliverables, языками, способом производства и ролью студии;
- разрешённый аудиопример и/или короткий видеопример;
- текстовая расшифровка audio demo и метаданные (язык, locale, акцент, тип задачи, формат);
- подтверждённые права на голос, музыку и клиентские материалы;
- методика контроля качества и примеры проверки;
- ссылки на независимые партнёрские/клиентские подтверждения там, где они реально существуют.

Не превращать логотип клиента или упоминание проекта на собственном сайте в независимый endorsement, KPI или отзыв. Не использовать аудио/логотипы без прав.

## 6. Entity graph и структурированные данные

### Что уже есть

Organization JSON-LD действительно присутствует в live HTML выборочных страниц. Он содержит sameAs с Facebook, VK, Instagram и двумя YouTube channel URLs. Поэтому правильная задача — не «добавить JSON-LD любой ценой», а исправить entity consistency, идентичность и точность связей.

### Что рекомендуется

- единый @id: https://www.audio-reclama.ru/#organization;
- name: только «Аудио-Реклама•ru»;
- url: только корневой canonical https://www.audio-reclama.ru;
- logo: стабильный публичный файл с точным официальным логотипом;
- description: фактологический профиль услуг и глобальной производственной способности;
- email и telephone: по актуальному видимому первоисточнику;
- sameAs: только действительно управляемые/официальные профили, идентичность которых проверена;
- knowsAbout: только реальные направления — business audio production, radio/audio ads, IVR prompts, multilingual announcements, voice-over, audiobooks, jingles, corporate songs, localization и т.д.;
- Service/OfferCatalog — только соответствующие видимым страницам услуги, без выдуманных цен, адресов или офисов.

Не создавать фиктивные LocalBusiness адреса в разных странах. Использовать Organization, потому что глобальная сеть исполнителей не равна филиальной сети.

Google прямо указывает, что специальной AI schema не требуется и structured data должен соответствовать видимому содержимому. Разметка поддерживает ясность и disambiguation, но не гарантирует rich results, индексацию или AI citations.

## 7. Content delivery и media: возможный недоиспользованный актив

Сайт содержит audio players и публичные голосовые примеры. Для AI retrieval это одновременно актив и риск: аудио само по себе не передаёт поисковому роботу весь смысл, особенно если на странице мало контекста.

Для каждого выбранного demo:
- заголовок с задачей/типом материала;
- язык + locale + dialect/accent, если это допустимо публично;
- нейтральное описание образца;
- доступный текстовый transcript;
- атрибутированный голос/исполнитель только с разрешением;
- технические метаданные (формат, длительность, mono/stereo, sample rate — только если проверены);
- лицензия/условия использования и кнопка прослушивания;
- ссылка на соответствующую услугу и кейс.

Нельзя превращать технические параметры demo в универсальную спецификацию для всех заказов. Эта категория пока не прошла полный постраничный аудит: это направление для следующего конкретного content pass.

## 8. Measurement — недостающий контур обратной связи

### 8.1 Уже подключено

**Search Console:** подключено свойство https://www.audio-reclama.ru, permission level = siteOwner, без необходимости переподключения. Это хороший источник для обычного Google Search, URL Inspection и AI Performance UI.

**GA4:** выбран property properties/564827393 (display name с неканонической хостовой формой). Measurement Health показал один web stream, чей default URI не содержит префикс www, созданный 17.11.2026. Stream имеет 3 key events: qualify_lead, close_convert_lead, purchase; настройки enhanced measurement включены. За диапазон 21.08–17.11.2026 отчёты source/medium и organic overview через API не вернули строк/метрик. Поскольку stream создан в конце диапазона, это не доказательство отсутствия трафика — это отсутствие пригодного baseline из данного отчёта. Перед настройкой атрибуции нужно сверить hostname потока с каноническим сайтом.

### 8.2 Что нужно включить в постоянную измерительную модель

1. **Google Search Console Generative AI Performance:** отчёт доступен сайтам worldwide с 31.08.2026; показывает AI Overviews/AI Mode impressions по страницам, странам и устройствам. Текущий OpenSEO GSC tool этого отдельного отчёта не предоставляет — его надо читать в интерфейсе Search Console.
2. **Search generative AI control:** проверить в Search Console Settings, что контент и ссылки включены в AI Overviews/AI Mode/соответствующие AI Search experiences.
3. **Bing Webmaster Tools AI Performance:** добавить сайт и проверять cited pages, grounding queries, timeline. Topics Portfolio (beta) позволяет смотреть тематические кластеры; Bing описывает также intent/topic/citation-share previews. Это важный независимый взгляд на Copilot и связанные Bing AI surfaces.
4. **GA4 attribution:** проверить фактическую отправку событий, canonical hostname с www, формы и event definitions. Новый stream не даёт ретроспективного AI referral baseline. Добавить channel/source reporting; OpenAI указывает utm_source=chatgpt.com для переходов с ChatGPT Search, что можно использовать как один источник атрибуции. Остальные системы могут отправлять другие referrer/UTM patterns.
5. **AI observation benchmark:** продолжать country × locale × platform × surface × intent matrix. Consumer UI и model API — разные измерительные серии. Фиксировать полный ответ, точные prompt/model/version, sources, date/time, region/auth/search state; blocked/unsupported/error не считать отсутствием бренда.
6. **Цели benchmark:** бренд mention, own-site citation, third-party citation, entity correctness, service accuracy, recommendation context, competitor substitution, false claims and next-step usefulness. Хранить denominator и статус на каждом cell.

### 8.3 Ограничения текущей измерительной системы

- OpenSEO AI Visibility Tracker не настроен и ответов/запусков нет; не считать это низкой видимостью.
- DataForSEO/OpenSEO не покрывает все страны, платформы и consumer UI; ограничение провайдера не равно ограничению рынка.
- Нет подтверждённого live RU consumer UI baseline по всем 12 платформам.
- Bing Webmaster AI Performance пока не подключён в рабочий контур.
- OpenSEO API не раскрывает новый Search Console Generative AI Performance report.

Не покупать AI checks/tracker/API credits ради искусственного заполнения таблиц. Сначала использовать бесплатные first-party performance surfaces и настоящие UI наблюдения в валидном регионе.

## 9. Внешние источники и подтверждение сущности

AI-система может лучше разбирать компанию, если та же самая сущность подтверждается не только собственным доменом. Но массовые каталоги и ссылки — не самоцель.

Приоритет:
1. точные официальные профили компании и consistent naming;
2. независимые customer/vendor/partner references с реальным вкладом и правами;
3. отраслевые awards/списки поставщиков/портфолио, если запись публична и корректна;
4. earned expert citations and interviews;
5. тематические каталоги после проверки индексации, editorial quality, географии, free/paid terms and ownership.

В live JSON-LD уже присутствуют пять sameAs URL, но их надо проверить на текущую официальность и владельца. Не добавлять в schema профили только потому, что они похожи по имени. Не выдавать listing presence за verified ownership. Не платить и не рассылать массовые заявки.

## 10. Приоритетный план действий

| Приоритет | Действие | Почему | Контур |
|---|---|---|---|
| P0 | Развернуть полноценную англоязычную карту услуг и кейсов; включить их в sitemap | Сейчас в sitemap только EN homepage, а маршруты услуг часто ведут на RU | Сайт, требует разрешения |
| P0 | Исправить Organization name / OG identity | Текущий JSON-LD использует неправильное имя с точкой; EN OG использует доменный вариант | Сайт, требует разрешения |
| P0 | Согласовать canonical и Open Graph URL policy | Sample raw HTML не содержит canonical link, EN og:url местами указывает на RU counterpart/root | Сайт, требует разрешения |
| P1 | Упростить robots rules и проверить все AI crawler paths через bot-specific tests | Удалить лишнюю пару /en/* + /en/, не заявляя о текущей блокировке Google; отдельно проверить WAF/IP | Сайт/CDN, требует разрешения |
| P1 | Проверить Search Console AI controls и GenAI Performance; добавить Bing AI Performance | Первый прямой first-party measurement реальных AI citations | UI/интеграции владельца |
| P1 | Стабилизировать GA4 attribution, www hostname and lead events | Без данных нельзя различить citations, visits and qualified leads | Analytics |
| P1 | Ввести entity graph single ID, verified sameAs and service mapping | Уменьшить ambiguity и несогласованность бренда | Repo first; site after approval |
| P1 | Создать 4–6 сильных buyer-intent pages на EN и первой локализованной волне | Устранить language/service journey gap вместо перевода всех URL | Сайт/Git drafts |
| P2 | Создать native pages: ES, pt-BR, AR, TR, DE, FR, JA, KO, ZH; далее остальные AI-significant languages | Приоритет по фактическому AI use / рынкам / citation gaps | Git drafts → site with permission |
| P2 | Добавить proof-rich audio demos, transcripts, rights and case metadata | Превратить реальный производственный актив в машинно читаемое доказательство | Repo/site after rights review |
| P2 | Проверить sameAs, external citations and independent case corroboration | Подтвердить entity outside the company website | Read-only research |
| P2 | Расширять benchmark только по реальным наблюдениям | Показать, какие модели/языки/интенты называют и цитируют бренд | Verified UI measurement |

## 11. Что не следует делать

- Не считать llms.txt обязательным условием AI indexing: Google прямо пишет, что дополнительные AI-файлы и особая разметка не нужны для появления в AI features.
- Не подменять индексацию количеством коммитов или файлов в Git; Git-репозиторий не установлен на официальном домене.
- Не считать Organization JSON-LD машинным «магнитом» или гарантией AI recommendation.
- Не переводить все 1 186 URL без intent map, качества и проверки эквивалентности.
- Не создавать сотни doorway pages из одинакового текста с заменой языка/страны.
- Не смешивать voice file production с PBX setup, call routing, CRM/SIP and deployment.
- Не показывать language directory page на русском как полноценную Arabic/Spanish/Portuguese landing page.
- Не строить claims на динамических counters, которые расходятся между блоками сайта.
- Не придумывать offices, branches, HQ или local employees.
- Не закупать citations, каталоги и AI trackers без явного решения владельца.

## 12. Источники live-среза и platform guidance

### Официальный сайт — наблюдения 19.11.2026
- robots.txt: https://www.audio-reclama.ru/robots.txt
- sitemap.xml: https://www.audio-reclama.ru/sitemap.xml
- EN homepage: https://www.audio-reclama.ru/en/
- EN order: https://www.audio-reclama.ru/en/online-zakaz.html
- EN Vnukovo case: https://www.audio-reclama.ru/en/project/vnukovo.html
- EN ABBYY case: https://www.audio-reclama.ru/en/project/abbyy.html
- RU translation/localization service: https://www.audio-reclama.ru/perevodchiki/
- RU IVR service: https://www.audio-reclama.ru/audio/golosovoe-privetstvie-menu-ivr.html
- Arabic voice directory sample: https://www.audio-reclama.ru/diktoryi/filter/language-arabic/

### Поисковые и AI-платформы — официальные документы
- Google AI Features and your website: https://developers.google.com/search/docs/appearance/ai-features
- Google AI optimization guide: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- Google robots.txt specification: https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec
- Google localized versions / hreflang: https://developers.google.com/search/docs/specialty/international/localized-versions
- Google sitemap guidance: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- Google Organization structured data: https://developers.google.com/search/docs/appearance/structured-data/organization
- Google Search Console Generative AI Performance: https://support.google.com/webmasters/answer/16984139
- Google Search generative AI control: https://support.google.com/webmasters/answer/16908024
- OpenAI crawler overview: https://developers.openai.com/api/docs/bots
- Anthropic crawler overview: https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler
- Perplexity crawlers: https://docs.perplexity.ai/docs/resources/perplexity-crawlers
- Bing Webmaster Tools AI Performance: https://www.bing.com/webmasters/help/ai-performance-9f8e7d6c
- Bing Webmaster Topics Portfolio beta (13.10.2026): https://blogs.bing.com/webmaster/2026/10/introducing-topics-portfolio-beta-in-ai-performance/

## 13. Ограничения настоящего аудита

Это глубокий анализ ключевых доступных поверхностей, но не полный 1 186-URL technical crawl, не Search Console URL Inspection для каждой страницы, не WAF/server-log review, не проверка всех языковых профилей и не owner-approved live site patch. Там, где измерение не выполнялось, в тексте дано «не проверено», а не отрицательный вердикт. Все предложения по правке официального сайта требуют отдельного разрешения и остаются вне Git-изменений.
