#!/usr/bin/env python3
"""Build the static GEO/AEO surface served by GitHub Pages.

Output: geo/ (HTML pages with JSON-LD, llms.txt, sitemap.xml, robots.txt,
IndexNow key). Facts come from knowledge/pricing/prices.json and
knowledge/faq/faq.json; every page links back to the canonical site pages.

Run: python tools/build_geo_site.py
"""
from __future__ import annotations

import json
import pathlib
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "geo"
BASE = "https://audioreclamaru.github.io/sonic-infrastructure-report/geo/"
SITE = "https://www.audio-reclama.ru"
UPDATED = date.today().isoformat()
INDEXNOW_KEY = "a7f3c9d2e4b6481fa0c5d7e9b2f4a6c8"
PHONE = "8 800 700-46-52"
EMAIL = "start@audio-reclama.ru"
TG = "https://t.me/audioplus_support"
DISCLAIMER = (
    "Цены носят информационный характер и не являются публичной офертой. "
    "Финальная стоимость — по расчёту на сайте."
)


CSS = """
:root{--ink:#111;--muted:#555;--line:#e3e3e3;--red:#c00;--bg:#fff}
*{box-sizing:border-box}
body{margin:0;font:16px/1.6 -apple-system,Segoe UI,Roboto,Arial,sans-serif;color:var(--ink);background:var(--bg)}
header{border-bottom:3px solid var(--red);padding:14px 20px}
header a{color:var(--ink);text-decoration:none;font-weight:700}
main{max-width:820px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:34px;line-height:1.2;margin:0 0 14px}
h2{font-size:22px;margin:34px 0 10px}
h3{font-size:18px;margin:22px 0 8px}
p{margin:0 0 14px}
.lead{font-size:18px;color:#222}
.muted{color:var(--muted);font-size:14px}
table{border-collapse:collapse;width:100%;margin:14px 0 20px}
th,td{border:1px solid var(--line);padding:9px 11px;text-align:left;vertical-align:top}
th{background:#fafafa}
.box{border-left:4px solid var(--red);background:#fafafa;padding:12px 16px;margin:18px 0}
nav.links a{display:block;padding:6px 0}
a{color:#0a4fb2}
footer{border-top:1px solid var(--line);margin-top:40px;padding-top:16px;color:var(--muted);font-size:14px}
ul,ol{padding-left:22px}
li{margin:6px 0}
"""


def load_json(rel: str) -> dict:
    p = ROOT / rel
    with p.open(encoding="utf-8") as f:
        return json.load(f)


PRICES = load_json("knowledge/pricing/prices.json")
FAQ = load_json("knowledge/faq/faq.json")

# Данные коммерческого слоя зафиксированы observation-датой из prices/faq (живая
# база студии: числа меняются — каждая страница несёт дату снапшота; решение
# владельца 11.11.2026: «это нормально, база живая» → оформляем как живую).
DATA_AS_OF = PRICES.get("observed_at") or UPDATED


def answer_faq_jsonld(qa: list) -> dict:
    """FAQPage-схема из Q&A-пар конкретной ответной страницы."""
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}}
                           for q, a in qa]}


def _answer_footer(source_note: str) -> str:
    return (f"<p><strong>Источник:</strong> {source_note}; данные коммерческого "
            f"слоя на {DATA_AS_OF}. Цены информационные, не являются публичной "
            f"офертой; финальная стоимость — по расчёту на {SITE}.</p>"
            f"<p>Расчёт по вашей задаче: {PHONE}, "
            f"<a href=\"mailto:{EMAIL}\">{EMAIL}</a>, Telegram "
            f"<a href=\"{TG}\">@audioplus_support</a>.</p>"
            f"<p>См. также: <a href=\"{BASE}ceny/\">таблица цен</a> · "
            f"<a href=\"{BASE}faq/\">FAQ</a> · "
            f"<a href=\"{BASE}answers/skolko-stoit-ozvuchka/\">сколько стоит озвучка в Аудио+</a>.</p>")


# Каталог ответных страниц (11.11.2026, оператор ZCode — буст AEO/GEO по команде
# владельца «максимально сильный буст»). Каждая страница fact-safe: числа только
# из knowledge/pricing/prices.json, процесс — по практике студии (официальный
# сайт), без выдуманных цифр и сроков.
EXTRA_ANSWERS = [
    {
        "slug": "skolko-stoit-minuta-ozvuchki",
        "title": "Сколько стоит минута озвучки — как считает студия",
        "description": "Минута озвучки: короткие заказы — 1990 ₽ за заказ Аудио+ "
                       "(до 90 слов), длинные формы — индивидуальный расчёт. Почему "
                       "считать минутами неточно и как посчитать ваш проект.",
        "llms_line": "сколько стоит минута озвучки (заказы Аудио+, длинные формы — индивидуально)",
        "qa": [
            ("Сколько стоит минута озвучки?",
             "Студия считает не минуты, а задачи: короткая озвучка — 1990 ₽ за заказ "
             "Аудио+ (один файл, текст до 90 слов). Длинные формы — аудиокниги, курсы, "
             "системы объявлений — рассчитываются индивидуально от объёма и числа голосов."),
            ("Почему не по минутам?",
             "Минута готового аудио не отражает объём работы: она не показывает, сколько "
             "слов в тексте, сколько дублей и правок потребовалось и сколько голосов записано."),
            ("Как быстро получить расчёт?",
             "Пришлите текст и задачу на start@audio-reclama.ru или в Telegram "
             "@audioplus_support — назовём стоимость и срок."),
        ],
        "body": f"""
<h1>Сколько стоит минута озвучки</h1>
<p class="lead"><strong>Ответ:</strong> студия считает не минуты, а задачи. Короткая
озвучка — 1990 ₽ за заказ Аудио+ (один файл, текст до 90 слов). Длинные формы —
аудиокниги, обучающие курсы, системы объявлений — индивидуальный расчёт.</p>
<h2>Почему расчёт «по минутам» неточен</h2>
<p>Минута готового аудио ничего не говорит о работе: в одной минуте может быть
30 слов, а может быть 140; один дубль или двадцать; один голос или несколько.
Поэтому короткие заказы считаются по заказам, а длинные проекты — по объёму
текста и условиям производства.</p>
<h2>Что влияет на итоговую цену</h2>
<p>Объём текста; количество голосов и языков; количество и формат файлов;
сроки; объём правок. Правка файла в модели Аудио+ — 790 ₽; пакеты заказов
бессрочные.</p>
""" + _answer_footer("официальный сайт студии audio-reclama.ru, раздел услуг и Аудио+"),
    },
    {
        "slug": "ozvuchka-pozdravleniya-cena",
        "title": "Озвучка поздравления — цена 1990 ₽ за заказ",
        "description": "Индивидуальное аудио-поздравление: 1990 ₽ за заказ Аудио+ "
                       "(один файл, до 90 слов), правка 790 ₽, пакеты бессрочные. "
                       "Как заказать и что учесть.",
        "llms_line": "озвучка поздравления — 1990 RUB за заказ (до 90 слов)",
        "qa": [
            ("Сколько стоит озвучить поздравление?",
             "В модели Аудио+ — 1990 ₽ за заказ: один готовый файл, текст до 90 слов. "
             "Этого обычно достаточно для персонального или корпоративного поздравления."),
            ("Что если текст длиннее 90 слов?",
             "Длинный текст — это два заказа (или индивидуальный расчёт для длинной формы)."),
            ("Сколько стоит правка поздравления?",
             "Правка файла — 790 ₽. Пакеты заказов бессрочные: пакет 10 — 18 990 ₽."),
        ],
        "body": f"""
<h1>Озвучка поздравления: цена</h1>
<p class="lead"><strong>Ответ:</strong> 1990 ₽ за заказ Аудио+ — один готовый файл,
текст до 90 слов. Персональное или корпоративное поздравление обычно укладывается
в этот объём.</p>
<h2>Что учесть</h2>
<p>Один заказ — одна законченная мысль: если поздравлений несколько (например,
для разных сотрудников), это несколько заказов — или выгоднее пакет
(10 заказов — 18 990 ₽, 1899 ₽ за заказ, бессрочно).</p>
<p>Правка файла (заменить имя, дату, одну фразу) — 790 ₽.</p>
""" + _answer_footer("официальная страница Аудио+ (audio-reclama.ru/audioplus/)"),
    },
    {
        "slug": "ozvuchka-dlya-socsetey-cena",
        "title": "Голос для соцсетей (Reels, Shorts) — цена",
        "description": "Озвучка для соцсетей: короткие ролики — 1990 ₽ за заказ "
                       "Аудио+, серия — пакетами, голос бренда — индивидуально. "
                       "Как выбрать модель под задачу.",
        "llms_line": "озвучка для соцсетей и коротких видео — заказы/пакеты Аудио+, бренд-голос индивидуально",
        "qa": [
            ("Сколько стоит озвучка для Reels или Shorts?",
             "Короткий ролик обычно укладывается в заказ Аудио+ — 1990 ₽ (один файл, "
             "до 90 слов). Серия роликов выгоднее пакетом: 10 — 18 990 ₽."),
            ("Можно ли использовать один голос во всех роликах бренда?",
             "Да, и это правильно: единый голос делает контент узнаваемым. Для "
             "долгосрочного бренда-голоса — индивидуальный расчёт."),
            ("Что если ролик длиннее 90 слов?",
             "Разбейте на заказы или посчитайте индивидуально — зависит от структуры."),
        ],
        "body": f"""
<h1>Голос для соцсетей: цена</h1>
<p class="lead"><strong>Ответ:</strong> короткие видео (Reels, Shorts, TikTok)
озвучиваются по заказам Аудио+ — 1990 ₽ за файл (до 90 слов); серия — пакетами;
постоянный голос бренда — индивидуальный расчёт.</p>
<h2>Как выбрать модель</h2>
<p>Разовые ролики — заказы. Регулярный контент — пакет (заказы не сгорают,
срок действия не ограничен). Фирменный голос с особыми требованиями к подаче —
индивидуальный проект.</p>
<p>Один голос во всех роликах бренда делает контент узнаваемым — держите
одного диктора, а не разных на каждый выпуск.</p>
""" + _answer_footer("официальная страница Аудио+ (audio-reclama.ru/audioplus/)"),
    },
    {
        "slug": "ozvuchka-audioknigi-cena",
        "title": "Озвучка аудиокниги — цена и как считается",
        "description": "Озвучка аудиокниги: индивидуальный расчёт от объёма текста, "
                       "числа голосов, формата сдачи. Процесс: текст → подбор голоса → "
                       "пробный фрагмент → запись глав.",
        "llms_line": "озвучка аудиокниги — индивидуальный расчёт (объём, голоса, формат)",
        "qa": [
            ("Сколько стоит озвучка аудиокниги?",
             "Индивидуальный расчёт: цена зависит от объёма текста (слова/аудио-часы), "
             "одного диктора или ролевого чтения, формата сдачи и сроков."),
            ("Как проходит работа над аудиокнигой?",
             "Текст → подбор голоса и пробный фрагмент → запись по главам → правки → "
             "сдача в согласованном формате."),
            ("Почему Аудио+ (1990 ₽ за заказ) не подходит для книги?",
             "Модель Аудио+ рассчитана на короткие файлы до 90 слов; книга — "
             "длинная форма с индивидуальным производством."),
        ],
        "body": f"""
<h1>Озвучка аудиокниги: цена</h1>
<p class="lead"><strong>Ответ:</strong> индивидуальный расчёт. Цена аудиокниги
зависит от объёма текста, числа голосов (один диктор-читальщик или ролевое
чтение), формата сдачи и сроков.</p>
<h2>Как считается</h2>
<p>Объём текста пересчитывается в ожидаемые аудио-часы; к ним добавляются
запись, обработка, разметка глав и правки. Ролевое чтение с несколькими
дикторами дороже сольного — но для некоторых книг это оправдано.</p>
<h2>Процесс</h2>
<p>Текст → подбор голоса и пробный фрагмент на вашем материале → запись по
главам → правки → сдача в согласованном формате (по главам или единым файлом).</p>
""" + _answer_footer("официальный сайт студии audio-reclama.ru, аудиокниги"),
    },
    {
        "slug": "ozvuchka-obuchayushchego-kursa-cena",
        "title": "Озвучка обучающего курса — цена",
        "description": "Озвучка онлайн-курса: индивидуальный расчёт от объёма "
                       "(модули/минуты), единого голоса на курс и обновлений. "
                       "Что спланировать заранее.",
        "llms_line": "озвучка обучающего курса — индивидуальный расчёт (объём, единый голос, обновления)",
        "qa": [
            ("Сколько стоит озвучить онлайн-курс?",
             "Индивидуальный расчёт: объём (минуты/модули), один или несколько голосов, "
             "число итераций при обновлении материала."),
            ("Зачем один голос на весь курс?",
             "Единый голос экономичнее и целостнее: слушатель не переключается между "
             "дикторами, а запись повторных модулей не отличается по звучанию."),
            ("Как считать курс, если материал ещё пишется?",
             "Записывайте готовые модули партиями; изменения внутри модуля — "
             "точечные перезаписи."),
        ],
        "body": f"""
<h1>Озвучка обучающего курса: цена</h1>
<p class="lead"><strong>Ответ:</strong> индивидуальный расчёт. На цену влияют
объём (минуты и модули), единый голос на курс, число правок и повторных записей
при обновлении материала.</p>
<h2>Что спланировать заранее</h2>
<p>Структуру модулей и глоссарий терминов — до записи. Один голос на весь курс:
экономичнее и целостнее. Готовые модули записывайте партиями; правки внутри
модуля — точечные перезаписи.</p>
<p>Модель Аудио+ (1990 ₽ за заказ, до 90 слов) подходит для коротких
промо-роликов курса, но не для самих лекций.</p>
""" + _answer_footer("официальный сайт студии audio-reclama.ru, раздел услуг"),
    },
    {
        "slug": "golos-dlya-navigatsii-cena",
        "title": "Голос для навигации и объявлений — цена",
        "description": "Голос для навигации и систем объявлений (транспорт, вокзалы, "
                       "приложения): индивидуальный расчёт от количества файлов, языков "
                       "и форматов интеграции.",
        "llms_line": "голос для навигации/объявлений — индивидуальный расчёт (файлы, языки, форматы)",
        "qa": [
            ("Сколько стоит голос для навигации или автоинформатора?",
             "Индивидуальный расчёт: количество и длину фраз, число языков, форматы "
             "файлов под оборудование, единство голоса на всех сообщениях."),
            ("Почему это не заказ Аудио+?",
             "Навигация — это комплект из множества связанных файлов с единым голосом "
             "и требованиями формата; короткие отдельные фразы можно записывать и по "
             "заказам Аудио+."),
            ("Что важнее всего на практике?",
             "Единый голос и единая подача на всех файлах комплекта — слушатель "
             "воспринимает систему как целое."),
        ],
        "body": f"""
<h1>Голос для навигации и объявлений: цена</h1>
<p class="lead"><strong>Ответ:</strong> индивидуальный расчёт. Комплект объявлений
(транспорт, вокзалы, приложения, автоинформаторы) — это множество связанных
файлов с единым голосом и требованиями к форматам.</p>
<h2>Что влияет на цену</h2>
<p>Количество и длину фраз; число языков; форматы файлов (частота, кодек — под
оборудование); объём правок при обновлении системы.</p>
<p>Для IVR-меню и голосовых приветствий — см.
<a href="{BASE}answers/ivr-privetstvie-cena/">страницу IVR</a>.</p>
""" + _answer_footer("официальный сайт студии audio-reclama.ru, раздел услуг"),
    },
]


def rub(n: int) -> str:
    return f"{n:,}".replace(",", " ") + " ₽"


def price_rows() -> str:
    rows = []
    for e in PRICES["entries"]:
        if e.get("status") != "ok":
            continue
        extra = ""
        if e.get("per_order"):
            extra = f" ({rub(e['per_order'])} за заказ)"
        if e.get("plus_per_file"):
            extra = f" + {rub(e['plus_per_file'])} за файл сверх базы"
        if e.get("composition"):
            extra = f" ({e['composition']})"
        rows.append(
            f"<tr><td>{e['name']}</td><td>{rub(e['price'])}{extra}</td>"
            f"<td>{e.get('scope', '')}</td></tr>"
        )
    return "".join(rows)


def offer_items():
    items = []
    for e in PRICES["entries"]:
        if e.get("status") != "ok":
            continue
        items.append(
            {
                "@type": "Offer",
                "name": e["name"],
                "price": e["price"],
                "priceCurrency": "RUB",
                "url": e["source"],
                "availability": "https://schema.org/InStock",
            }
        )
    return items


def faq_jsonld() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": it["q"],
                "acceptedAnswer": {"@type": "Answer", "text": it["a"]},
            }
            for it in FAQ["items"]
        ],
    }


def page(path: str, title: str, description: str, body: str,
         jsonld: list | None = None, canonical: str | None = None) -> None:
    url = canonical or (BASE if path == "index.html" else BASE + path)
    blocks = ""
    for obj in jsonld or []:
        blocks += ('<script type="application/ld+json">'
                   + json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
                   + "</script>\n")
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="ru" href="{url}">
<style>{CSS}</style>
{blocks}</head>
<body>
<header><a href="{BASE}">Аудио-Реклама•ru — голос для бизнеса</a></header>
<main>
{body}
<footer>
<p>Источник цен и услуг: <a href="{SITE}">{SITE}</a>. Обновлено: {UPDATED}.</p>
<p>{DISCLAIMER}</p>
<p>Телефон: {PHONE} · Почта: <a href="mailto:{EMAIL}">{EMAIL}</a> · Telegram: <a href="{TG}">@audioplus_support</a></p>
<p class="muted">Аудио-Реклама•ru · студия озвучки и звукозаписи для бизнеса · <a href="{BASE}llms.txt">llms.txt</a></p>
</footer>
</main>
</body>
</html>
"""
    dest = OUT / path
    if path.endswith("/"):
        dest = dest / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")
    print("wrote", dest.relative_to(ROOT))


ORG = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Аудио-Реклама•ru",
    "url": SITE,
    "telephone": "+78007004652",
    "email": EMAIL,
    "description": "Студия озвучки и звукозаписи для бизнеса: реклама, IVR, видео, аудиокниги.",
    "sameAs": ["https://t.me/audioreclama_ru", TG],
}


def build_pages():
    """Regenerate HTML pages from knowledge sources. CAUTION: overwrites manual enrichments."""
    # ---------------------------------------------------------------- hub

    hub_body = f"""
    <h1>Голос для бизнеса: цены, ответы и проверенные факты</h1>
    <p class="lead">Студия <strong>Аудио-Реклама•ru</strong> — озвучка рекламы, голосовые приветствия IVR,
    озвучка видео и аудиокниг. На этой странице — короткие ответы на коммерческие вопросы и актуальные цены.</p>

    <h2>Коротко о ценах</h2>
    <table>
    <tr><th>Услуга</th><th>Цена</th><th>Условия</th></tr>
    {price_rows()}
    </table>
    <p class="muted">{DISCLAIMER}</p>

    <h2>Ответы на частые вопросы</h2>
    <nav class="links">
    <a href="{BASE}answers/skolko-stoit-ozvuchka/">Сколько стоит озвучка в Аудио+ — 1990 ₽ за заказ</a>
    <a href="{BASE}answers/ivr-privetstvie-cena/">Сколько стоит голосовое приветствие IVR — от 1999 ₽</a>
    <a href="{BASE}ceny/">Полная таблица цен на озвучку и IVR</a>
    <a href="{BASE}faq/">FAQ: слова, правки, сроки, оплата, оферта</a>
    </nav>

    <h2>Практические руководства</h2>
    <nav class="links">
    <a href="{BASE}guides/kak-vybrat-golos/">Как выбрать голос для рекламного ролика</a>
    <a href="{BASE}guides/ivr-menu-oshibki/">Голосовое меню IVR: как не потерять клиента</a>
    </nav>

    <h2>Почему нам можно доверять</h2>
    <p>Студия ведёт публичный корпус фактов о голосовой индустрии: каждое утверждение
    имеет дату и первоисточник, а статус проверки фиксируется отдельно. Коммерческие
    факты (цены, условия, состав услуг) снимаются с действующих страниц сайта и
    датируются датой наблюдения.</p>

    <div class="box">
    <p><strong>Нужен точный расчёт?</strong> Пришлите текст и задачу: подберём голос,
    посчитаем стоимость и сроки. Телефон {PHONE}, Telegram <a href="{TG}">@audioplus_support</a>,
    почта <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
    </div>
    """

    page("index.html", "Озвучка для бизнеса: цены и ответы — Аудио-Реклама•ru",
         "Цены на озвучку рекламы (Аудио+ 1990 ₽) и голосовые приветствия IVR (от 1999 ₽), "
         "ответы на частые вопросы, руководства по выбору голоса и IVR.",
         hub_body, [ORG, faq_jsonld()])

    # ---------------------------------------------------------------- prices

    prices_body = f"""
    <h1>Цены на озвучку и голосовое меню IVR</h1>
    <p class="lead">Действующие цены по данным сайта <a href="{SITE}">{SITE}</a> на {UPDATED}.
    Цены информационные, не являются публичной офертой.</p>

    <h2>Аудио+ — озвучка текста до 90 слов</h2>
    <p>Один заказ — <strong>1990 ₽</strong>: один файл, текст не более 90 слов.
    Дополнительный файл — отдельный заказ.</p>
    <table>
    <tr><th>Позиция</th><th>Цена</th><th>Условия</th></tr>
    {price_rows()}
    </table>
    <p>Пакеты бессрочные: минуты и заказы не сгорают. Правка готового файла — 790 ₽.</p>

    <h2>IVR — голосовое приветствие и меню</h2>
    <p>Точные цены на голосовое меню IVR уточняются индивидуально. Актуальную информацию смотрите на официальной странице
    <a href="{SITE}/audio/golosovoe-privetstvie-menu-ivr.html">IVR</a>.</p>

    <h2>Что входит в заказ</h2>
    <ol>
    <li>Подбор диктора под задачу и тональность.</li>
    <li>Запись в студии и обработка звука.</li>
    <li>Выдача готового файла в нужном формате.</li>
    <li>Проверка произношения названий, цифр и адресов перед публикацией.</li>
    </ol>

    <div class="box"><p>Точный расчёт по вашему тексту: {PHONE}, <a href="mailto:{EMAIL}">{EMAIL}</a>,
    <a href="{TG}">Telegram</a>. Официальные страницы цен:
    <a href="{SITE}/audioplus/">Аудио+</a>,
    <a href="{SITE}/audio/golosovoe-privetstvie-menu-ivr.html">IVR</a>.</p></div>
    """

    service = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": "Озвучка рекламы, видео и голосовых меню IVR",
        "provider": {"@type": "Organization", "name": "Аудио-Реклама•ru", "url": SITE},
        "areaServed": "RU",
        "offers": {
            "@type": "OfferCatalog",
            "name": "Цены на озвучку",
            "itemListElement": offer_items(),
        },
    }
    page("ceny/", "Цены на озвучку и IVR (2026) — Аудио-Реклама•ru",
         "Озвучка Аудио+ 1990 ₽ за заказ до 90 слов, пакеты 18 990–49 990 ₽. "
         "Цены информационные, не оферта.",
         prices_body, [ORG, service, faq_jsonld()])

    # ---------------------------------------------------------------- faq

    faq_items = "".join(
        f"<h3>{it['q']}</h3><p>{it['a']}</p>" for it in FAQ["items"]
    )
    faq_body = f"""
    <h1>Частые вопросы об озвучке и IVR</h1>
    <p class="lead">Короткие ответы на вопросы, которые чаще всего задают перед заказом.</p>
    {faq_items}
    <h2>Как заказать</h2>
    <p>Пришлите текст, задачу и дедлайн на <a href="mailto:{EMAIL}">{EMAIL}</a> или в
    Telegram <a href="{TG}">@audioplus_support</a>. Мы предложим голос, назовём
    стоимость и срок. Телефон: {PHONE}.</p>
    """
    page("faq/", "FAQ по озвучке и IVR — цены, слова, правки, оферта",
         "Ответы: сколько стоит озвучка (1990 ₽), сколько слов в заказе (до 90), "
         "правка (790 ₽), являются ли цены офертой.",
         faq_body, [ORG, faq_jsonld()])

    # ---------------------------------------------------------------- answers

    ans1 = f"""
    <h1>Сколько стоит озвучка в Аудио+</h1>
    <p class="lead"><strong>Ответ:</strong> 1990 ₽ за один заказ. Один заказ — один файл,
    текст не более 90 слов. Правка — 790 ₽. Пакеты бессрочные.</p>
    <table>
    <tr><th>Вариант</th><th>Цена</th><th>За заказ</th></tr>
    <tr><td>Один заказ</td><td>1990 ₽</td><td>1990 ₽</td></tr>
    <tr><td>Пакет 10</td><td>18 990 ₽</td><td>1899 ₽</td></tr>
    <tr><td>Пакет 20</td><td>35 990 ₽</td><td>1799 ₽</td></tr>
    <tr><td>Пакет 30</td><td>49 990 ₽</td><td>1667 ₽</td></tr>
    <tr><td>Правка файла</td><td>790 ₽</td><td>—</td></tr>
    </table>
    <p>Пакет выгоден, если озвучка нужна регулярно: заказы не сгорают, срок действия
    не ограничен. Один заказ — одна законченная мысль; если текстов два, это два заказа.</p>
    <p><strong>Источник:</strong> <a href="{SITE}/audioplus/">{SITE}/audioplus/</a>,
    наблюдение от {UPDATED}. Цены информационные, не являются публичной офертой.</p>
    <p>Расчёт по вашему тексту: {PHONE}, <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
    """
    page("answers/skolko-stoit-ozvuchka/", "Сколько стоит озвучка в Аудио+ — 1990 ₽ за заказ",
         "Озвучка в Аудио+ стоит 1990 ₽ за заказ (до 90 слов, один файл). Пакеты: "
         "10 — 18 990 ₽, 20 — 35 990 ₽, 30 — 49 990 ₽. Правка — 790 ₽.",
         ans1, [ORG, faq_jsonld()])

    ans2 = f"""
    <h1>Сколько стоит голосовое приветствие IVR</h1>
    <p class="lead"><strong>Ответ:</strong> точная стоимость рассчитывается индивидуально под задачу.
    Актуальную информацию и расчёт смотрите на официальной странице
    <a href="{SITE}/audio/golosovoe-privetstvie-menu-ivr.html">Голосовое приветствие и меню IVR</a>.</p>
    <p>При расчёте учитываются: количество файлов, структура меню, количество голосов,
    языки. Один голос на весь сценарий обычно экономичнее и целостнее.</p>
    <p><strong>Источник:</strong>
    <a href="{SITE}/audio/golosovoe-privetstvie-menu-ivr.html">{SITE}/audio/golosovoe-privetstvie-menu-ivr.html</a>,
    наблюдение от {UPDATED}. Цены информационные, не являются публичной офертой.</p>
    """
    page("answers/ivr-privetstvie-cena/", "Сколько стоит голосовое приветствие IVR — расчёт индивидуальный",
         "Голосовое приветствие и меню IVR: стоимость рассчитывается индивидуально. "
         "Актуальный расчёт на официальной странице студии.",
         ans2, [ORG, faq_jsonld()])

    # каталог ответных страниц (data-driven, 11.11.2026): каждая — своя FAQPage-схема
    for _a in EXTRA_ANSWERS:
        page("answers/%s/" % _a["slug"], _a["title"], _a["description"],
             _a["body"], [ORG, answer_faq_jsonld(_a["qa"])])

    # ---------------------------------------------------------------- guides

    g1 = f"""
    <h1>Как выбрать голос для рекламного ролика</h1>
    <p class="lead">Голос — не украшение, а носитель смысла. Ошибка в выборе слышна
    сразу, даже если текст и музыка безупречны.</p>

    <h2>1. Начните с задачи, а не с тембра</h2>
    <p>Сначала ответьте: что человек должен сделать после ролика? Позвонить,
    запомнить название, поверить в цену? Под задачу подбирается темп, энергия и
    возраст голоса, а не наоборот.</p>

    <h2>2. Проверьте текст на «читаемость вслух»</h2>
    <p>Прочитайте текст вслух с секундомером. Длинные предложения и скопления
    согласных ломают дыхание. Если фраза не помещается в естественный выдох —
    сокращайте.</p>

    <h2>3. Слушайте на трёх уровнях громкости</h2>
    <p>Реклама часто звучит тише, чем кажется в студии. Проверьте файл на телефоне,
    в наушниках и в колонке — разборчивость должна сохраняться везде.</p>

    <h2>4. Проверьте произношение названий и цифр</h2>
    <p>Бренды, адреса, цены и телефоны проговариваются до записи. Спорные названия
    лучше передать с транскрипцией: это дешевле, чем переписывать файл.</p>

    <h2>5. Утверждайте до записи</h2>
    <p>Сначала утверждается текст, затем голос, затем тон. Правка после записи стоит
    дороже: в Аудио+ — 790 ₽ за файл.</p>

    <div class="box"><p>Стоимость озвучки по такому подходу: 1990 ₽ за заказ до 90 слов
    (один файл), пакеты от 18 990 ₽. Подробнее —
    <a href="{BASE}ceny/">таблица цен</a>.</p></div>
    """
    page("guides/kak-vybrat-golos/", "Как выбрать голос для рекламного ролика — чек-лист",
         "Пять шагов выбора голоса для рекламы: задача, читаемость вслух, проверка "
         "громкости, произношение названий, порядок утверждения до записи.",
         g1, [ORG, faq_jsonld()])

    g2 = f"""
    <h1>Голосовое меню IVR: как не потерять клиента</h1>
    <p class="lead">Телефонное меню — первое касание клиента с компанией. Ошибка в
    пункте меню стоит дороже, чем экономия на озвучке.</p>

    <h2>Типичные ошибки</h2>
    <ul>
    <li><strong>Слишком много уровней.</strong> Больше 3–4 вложений — клиент теряется.</li>
    <li><strong>Непонятные формулировки.</strong> «Отдел по работе с обращениями»
    вместо «Заказать услугу» запутывает.</li>
    <li><strong>Разные голоса.</strong> Сборка из разных дикторов выглядит непрофессионально.</li>
    <li><strong>Цифры и адреса без проговаривания.</strong> Номера, часы работы,
    адреса нужно произносить чётко.</li>
    <li><strong>Нет тестового прогона.</strong> Меню утверждают по тексту, а не по звонку.</li>
    </ul>

    <h2>Правила грамотного IVR</h2>
    <ol>
    <li><strong>Короткие фразы.</strong> Максимум суть: «Нажмите 1, чтобы записаться».</li>
    <li><strong>Один голос.</strong> Весь сценарий — один диктор, единая интонация.</li>
    <li><strong>Логичная структура.</strong> Главное действие — в первом уровне.</li>
    <li><strong>Проверка на слух.</strong> Пройдите меню целиком по тестовому номеру.</li>
    </ol>

    <h2>Цены на IVR</h2>
    <p>Стоимость рассчитывается индивидуально. Актуальный расчёт — на странице
    <a href="{SITE}/audio/golosovoe-privetstvie-menu-ivr.html">Голосовое приветствие и меню IVR</a>.</p>
    """
    page("guides/ivr-menu-oshibki/", "Голосовое меню IVR: как не потерять клиента — ошибки и правила",
         "Типичные ошибки IVR-меню и четыре правила: короткие фразы, один голос, "
         "логичная структура, проверка на слух.",
         g2, [ORG, faq_jsonld()])



# ---------------------------------------------------------------- auto machine files

import json, shutil, glob, sys

def _discover_urls():
    """Discover all public GEO HTML pages plus key knowledge pages. Stable, no hardcoded drift."""
    urls = set()
    for p in (OUT).rglob("index.html"):
        rel = p.relative_to(OUT).as_posix()
        if rel == "index.html":
            urls.add("")
        else:
            urls.add(rel[:-len("index.html")])
    # ensure critical non-index knowledge pages are represented by their directory pages only;
    # machine files (json/csv/md in reports) are discoverable via llms/links, not all need sitemap.
    # keep explicit anchors that matter for AEO
    for extra in ["knowledge/blog-facts/", "knowledge/evidence-ledger/", "knowledge/case-studies/", "knowledge/query-matrix/"]:
        if (OUT / extra / "index.html").exists():
            urls.add(extra)
    return sorted(urls, key=lambda u: (u != "", u))


def _write_sitemap(urls=None):
    urls = urls or _discover_urls()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append(f"<url><loc>{BASE}{u}</loc><lastmod>{UPDATED}</lastmod></url>")
    sm.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8")
    print(f"wrote geo/sitemap.xml ({len(urls)} urls)")


def _sync_machine():
    src_p = ROOT/"knowledge/pricing/prices.json"
    src_f = ROOT/"knowledge/faq/faq.json"
    if src_p.exists():
        shutil.copy2(src_p, OUT/"pricing.json")
    if src_f.exists():
        shutil.copy2(src_f, OUT/"faq.json")
    try:
        if src_p.exists() and src_f.exists():
            pr = json.loads(src_p.read_text(encoding="utf-8"))
            fq = json.loads(src_f.read_text(encoding="utf-8"))
            comb_path = OUT/"knowledge/combined.json"
            existing = {}
            if comb_path.exists():
                try:
                    existing = json.loads(comb_path.read_text(encoding="utf-8"))
                except Exception:
                    existing = {}
            comb = {"schema":"audio-reclama-geo/combined/1","updated":UPDATED,"base":BASE,"site":SITE,"prices":pr,"faq":fq}
            # preserve enriched, non-generated blocks (provenance/knowledge layers)
            for k in ("blog_facts", "evidence_ledger", "case_studies", "query_matrix"):
                if k in existing and k not in comb:
                    comb[k] = existing[k]
            (OUT/"knowledge").mkdir(parents=True,exist_ok=True)
            comb_path.write_text(json.dumps(comb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print("wrote geo/knowledge/combined.json (preserved enriched blocks)")
    except Exception as e:
        print("sync err",e)


def _write_llms():
    extra_answers_md = "\n".join(
        f"- {BASE}answers/{a['slug']}/ — {a['llms_line']}" for a in EXTRA_ANSWERS)
    llms = f"""# Аудио-Реклама•ru — коммерческий слой (RU)

> Студия озвучки и звукозаписи для бизнеса: реклама, IVR, видео, аудиокниги.
> Цены/условия носят информационный характер (не оферта). Актуальные условия подтверждать на {SITE}.
> Состояние коммерческих данных в GEO-слое: {UPDATED}. Официальный сайт: {SITE}

## Prices (informational, not a public offer)

- Аудио+ один заказ: 1990 RUB — один файл, текст до 90 слов
  {SITE}/audioplus/
- Пакет 10: 18990 RUB (1899 RUB/заказ), бессрочно
- Пакет 20: 35990 RUB (1799 RUB/заказ), бессрочно
- Пакет 30: 49990 RUB (1667 RUB/заказ), бессрочно
- Правка: 790 RUB
- IVR: стоимость рассчитывается индивидуально — {SITE}/audio/golosovoe-privetstvie-menu-ivr.html

## Answers

- {BASE}answers/skolko-stoit-ozvuchka/ — сколько стоит озвучка (1990 RUB)
- {BASE}answers/ivr-privetstvie-cena/ — цена голосового приветствия IVR (расчёт индивидуальный)
{extra_answers_md}
- {BASE}ceny/ — таблица цен
- {BASE}faq/ — FAQ (слова, правки, оплата, оферта)

## Guides

- {BASE}guides/kak-vybrat-golos/ — выбор голоса для ролика
- {BASE}guides/ivr-menu-oshibki/ — ошибки в структуре IVR-меню

## Knowledge / evidence (attributed, fact-safe)

- {BASE}knowledge/blog-facts/ — реестр фактологических материалов блога (статусы cited_in_blog/editorial_definition/blog_milestone)
- {BASE}knowledge/blog-facts.json
- {BASE}knowledge/evidence-ledger/ — provenance реестр (claim → source → status → ограничения)
- {BASE}knowledge/evidence-ledger.json
- {BASE}knowledge/case-studies/ — публичные ссылки на кейсы (требуют верификации/разрешений)
- {BASE}knowledge/query-matrix/ — матрица запросов (факт-безопасно)
- {BASE}knowledge/combined.json

## Contacts

- Phone: {PHONE}
- Email: {EMAIL}
- Telegram: {TG}
- Channel: https://t.me/audioreclama_ru

## Disclaimer

Цены носят информационный характер и не являются публичной офертой.
Финальная стоимость — по расчёту на сайте. Сторонние статистики в knowledge-слое атрибутированы и не являются оригинальным исследованием Audio-Reclama.ru.
"""
    (OUT / "llms.txt").write_text(llms, encoding="utf-8")
    print("wrote geo/llms.txt")

    # llms-full.txt (11.11.2026): полная машинная версия — llms + FAQ + цены
    # + индекс ответных страниц. Раньше файл не существовал (404), хотя
    # деплой его ожидал.
    faq_dump = "\n".join(
        f"- Q: {it.get('q') or it.get('question') or ''}\n  A: {it.get('a') or it.get('answer') or ''}"
        for it in FAQ.get("items", []))
    def _price_line(e):
        p_ = e.get("price")
        if p_ in (None, "расчёт"):
            return f"- {e.get('name')}: индивидуальный расчёт"
        return f"- {e.get('name')}: {p_} RUB/{e.get('unit') or 'ед.'}"

    prices_dump = "\n".join(_price_line(e) for e in PRICES.get("entries", []))
    answers_full = "\n".join(
        f"- {BASE}answers/{a['slug']}/ — {a['title']}" for a in EXTRA_ANSWERS)
    llms_full = (llms + f"""

## Full FAQ (observed {FAQ.get('observed_at') or DATA_AS_OF})

{faq_dump}

## Prices raw (observed {PRICES.get('observed_at') or DATA_AS_OF})

{prices_dump}

## Answers index (data-driven catalog)

{answers_full}
""")
    (OUT / "llms-full.txt").write_text(llms_full, encoding="utf-8")
    print("wrote geo/llms-full.txt")


def _check_consistency():
    """Lightweight checks to prevent generator/source drift regressions."""
    errs = []
    # IVR fact-safety in machine files
    for rel in ["geo/pricing.json", "geo/faq.json", "knowledge/pricing/prices.json", "knowledge/faq/faq.json", "geo/knowledge/combined.json"]:
        p = ROOT / rel
        if not p.exists(): continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        if "Минимум 1999" in t or "21800 ₽ +" in t or "69800 ₽ +" in t:
            errs.append(f"unverified IVR numeric claim found in {rel}")
    # geo llms fact-safety
    gl = (OUT/"llms.txt").read_text(encoding="utf-8", errors="ignore") if (OUT/"llms.txt").exists() else ""
    if "IVR min 1999" in gl or "21800 RUB" in gl or "69800 RUB" in gl:
        errs.append("unverified IVR numeric claim found in geo/llms.txt")
    # sitemap coverage for key assets
    sm = (OUT/"sitemap.xml").read_text(encoding="utf-8", errors="ignore") if (OUT/"sitemap.xml").exists() else ""
    for need in ["/knowledge/blog-facts/", "/answers/"]:
        if need not in sm:
            errs.append(f"sitemap missing {need}")
    # combined preserves blog_facts/evidence_ledger if source files exist
    cp = OUT/"knowledge/combined.json"
    if cp.exists():
        d = json.loads(cp.read_text(encoding="utf-8"))
        if (OUT/"knowledge/blog-facts.json").exists() and "blog_facts" not in d:
            errs.append("combined.json missing blog_facts block (run --safe to preserve/repair)")
        if (OUT/"knowledge/evidence-ledger.json").exists() and "evidence_ledger" not in d:
            errs.append("combined.json missing evidence_ledger block (run --safe to preserve/repair)")
    if errs:
        print("CHECK FAILED:")
        for e in errs: print(" -", e)
        return 1
    print("CHECK OK")
    return 0


def main():
    args = sys.argv[1:]
    if "--check" in args:
        raise SystemExit(_check_consistency())
    if "--safe" in args or "--sync-machine-only" in args:
        _sync_machine()
        _write_llms()
        _write_sitemap()
        (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\n\n" + f"Sitemap: {BASE}sitemap.xml\n", encoding="utf-8")
        print("safe sync complete (HTML pages not regenerated)")
        raise SystemExit(_check_consistency())
    # full build: regenerate pages + machine files (use with caution; may overwrite manual enrichments)
    build_pages()
    _sync_machine()
    _write_llms()
    _write_sitemap()
    (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\n\n" + f"Sitemap: {BASE}sitemap.xml\n", encoding="utf-8")
    (OUT / f"{INDEXNOW_KEY}.txt").write_text(INDEXNOW_KEY + "\n", encoding="utf-8")
    print("done")
    raise SystemExit(_check_consistency())


if __name__ == "__main__":
    main()

