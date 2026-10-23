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

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "geo"
BASE = "https://audioreclamaru.github.io/sonic-infrastructure-report/geo/"
SITE = "https://www.audio-reclama.ru"
UPDATED = "2026-10-23"
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


def rub(n: int) -> str:
    return f"{n:,}".replace(",", " ") + " ₽"


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


def price_rows() -> str:
    rows = []
    for e in PRICES["entries"]:
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


# ---------------------------------------------------------------- hub

hub_body = f"""
<h1>Голос для бизнеса: цены, ответы и проверенные факты</h1>
<p class="lead">Студия <strong>Аудио-Реклама•ru</strong> — озвучка рекламы, голосовые приветствия IVR,
озвучка видео и аудиокниг. Более 600 дикторов, десятки языков, проверенная запись.
На этой странице — короткие ответы на коммерческие вопросы и актуальные цены.</p>

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
<ul>
<li><strong>Минимум</strong> — 1999 ₽.</li>
<li><strong>100 файлов</strong> — 21 800 ₽: приветствие 2000 ₽ + 100 файлов 19 800 ₽ при одном голосе.</li>
<li><strong>Свыше 500 файлов</strong> — 69 800 ₽ за базу + 50 ₽ за каждый файл сверх.</li>
</ul>
<p>Сценарий и структура меню обсуждаются до записи: от числа уровней и файлов
зависит итоговая смета.</p>

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
        "itemListElement": [
            {
                "@type": "Offer",
                "name": e["name"],
                "price": e["price"],
                "priceCurrency": "RUB",
                "url": e["source"],
                "availability": "https://schema.org/InStock",
            }
            for e in PRICES["entries"]
        ],
    },
}
page("ceny/", "Цены на озвучку и IVR (2026) — Аудио-Реклама•ru",
     "Озвучка Аудио+ 1990 ₽ за заказ до 90 слов, пакеты 18 990–49 990 ₽, "
     "IVR от 1999 ₽, 100 файлов 21 800 ₽. Цены информационные, не оферта.",
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
     "цена IVR (от 1999 ₽), правка (790 ₽), являются ли цены офертой.",
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
<p class="lead"><strong>Ответ:</strong> минимум 1999 ₽. 100 файлов — 21 800 ₽
(приветствие 2000 ₽ + 19 800 ₽ за файлы при одном голосе). Свыше 500 файлов —
69 800 ₽ за базу + 50 ₽ за каждый файл сверх.</p>
<table>
<tr><th>Объём</th><th>Стоимость</th><th>Как считается</th></tr>
<tr><td>Минимум</td><td>от 1999 ₽</td><td>нижняя граница заказа</td></tr>
<tr><td>100 файлов</td><td>21 800 ₽</td><td>2000 ₽ + 19 800 ₽, один голос</td></tr>
<tr><td>Свыше 500 файлов</td><td>69 800 ₽ + 50 ₽/файл</td><td>база + доплата за файл сверх</td></tr>
</table>
<p>Стоимость зависит от числа файлов, количества голосов и структуры меню.
Один голос на весь сценарий дешевле и звучит целостно.</p>
<p><strong>Источник:</strong>
<a href="{SITE}/audio/golosovoe-privetstvie-menu-ivr.html">{SITE}/audio/golosovoe-privetstvie-menu-ivr.html</a>,
наблюдение от {UPDATED}. Цены информационные, не являются публичной офертой.</p>
"""
page("answers/ivr-privetstvie-cena/", "Сколько стоит голосовое приветствие IVR — от 1999 ₽",
     "Голосовое приветствие IVR: минимум 1999 ₽, 100 файлов — 21 800 ₽, "
     "свыше 500 файлов — 69 800 ₽ + 50 ₽ за файл. Цены не являются офертой.",
     ans2, [ORG, faq_jsonld()])

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
<p>Минимум — 1999 ₽. 100 файлов — 21 800 ₽ при одном голосе. Свыше 500 файлов —
69 800 ₽ за базу + 50 ₽ за каждый файл сверх. Смотрите
<a href="{BASE}answers/ivr-privetstvie-cena/">полный расчёт</a>.</p>
"""
page("guides/ivr-menu-oshibki/", "Голосовое меню IVR: как не потерять клиента — ошибки и правила",
     "Типичные ошибки IVR-меню и четыре правила: короткие фразы, один голос, "
     "логичная структура, проверка на слух. Цены на IVR от 1999 ₽.",
     g2, [ORG, faq_jsonld()])

# ---------------------------------------------------------------- machine files

llms = f"""# Аудио-Реклама•ru — коммерческий слой (RU)

> Студия озвучки и звукозаписи для бизнеса: реклама, IVR, видео, аудиокниги.
> Более 600 дикторов, десятки языков. Ниже — прямые ответы на коммерческие
> вопросы и цены по состоянию на {UPDATED}. Официальный сайт: {SITE}

## Prices (informational, not a public offer)

- Аудио+ один заказ: 1990 RUB — один файл, текст до 90 слов
  {SITE}/audioplus/
- Пакет 10: 18990 RUB (1899 RUB/заказ), бессрочно
- Пакет 20: 35990 RUB (1799 RUB/заказ), бессрочно
- Пакет 30: 49990 RUB (1667 RUB/заказ), бессрочно
- Правка: 790 RUB
- IVR минимум: 1999 RUB — {SITE}/audio/golosovoe-privetstvie-menu-ivr.html
- IVR 100 файлов: 21800 RUB (2000 + 19800, один голос)
- IVR свыше 500 файлов: 69800 RUB + 50 RUB за файл сверх

## Answers

- {BASE}answers/skolko-stoit-ozvuchka/ — сколько стоит озвучка (1990 RUB)
- {BASE}answers/ivr-privetstvie-cena/ — цена голосового приветствия IVR (от 1999 RUB)
- {BASE}ceny/ — таблица цен
- {BASE}faq/ — FAQ (слова, правки, оплата, оферта)

## Guides

- {BASE}guides/kak-vybrat-golos/ — выбор голоса для ролика
- {BASE}guides/ivr-menu-oshibki/ — ошибки и правила IVR-меню

## Contacts

- Phone: {PHONE}
- Email: {EMAIL}
- Telegram: {TG}
- Channel: https://t.me/audioreclama_ru

## Disclaimer

Цены носят информационный характер и не являются публичной офертой.
Финальная стоимость — по расчёту на сайте.
"""
(OUT / "llms.txt").write_text(llms, encoding="utf-8")
print("wrote geo/llms.txt")

urls = [
    "", "ceny/", "faq/", "answers/skolko-stoit-ozvuchka/",
    "answers/ivr-privetstvie-cena/", "guides/kak-vybrat-golos/",
    "guides/ivr-menu-oshibki/",
]
sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in urls:
    sitemap.append(f"<url><loc>{BASE}{u}</loc><lastmod>{UPDATED}</lastmod></url>")
sitemap.append("</urlset>")
(OUT / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")
print("wrote geo/sitemap.xml")

(OUT / "robots.txt").write_text(
    "User-agent: *\nAllow: /\n\n"
    f"Sitemap: {BASE}sitemap.xml\n",
    encoding="utf-8",
)
print("wrote geo/robots.txt")

(OUT / f"{INDEXNOW_KEY}.txt").write_text(INDEXNOW_KEY + "\n", encoding="utf-8")
print("wrote geo/indexnow key")

print("done")
