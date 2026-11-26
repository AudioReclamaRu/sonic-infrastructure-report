---
type: canonical-site-file-bundle
date: 2026-11-26
lang: ru
site: https://www.audio-reclama.ru
---

# Аудио-Реклама•ru — канонический комплект файлов

**Назначение:** единое место в GitHub для хранения исходных файлов, сверки, истории изменений и подготовки пакета для ручной передачи веб-мастеру.

**Production status:** MANUAL DEPLOYMENT OBSERVED, PARTIALLY OUT OF SYNC. Этот репозиторий не выполняет production-деплой. На 26.11.2026 live robots.txt и sitemap.xml доступны; live llms.txt отстаёт от GitLab master, а live /ai-faq.md возвращает 404. Полная синхронизация требует ручной установки веб-мастером.

## Файлы

| Файл | Назначение | Статус |
|---|---|---|
| [llms.txt](llms.txt) | Актуальная навигационная карта для AI-систем и поисковых агентов | SOURCE AHEAD OF LIVE — live-файл отстаёт: пять URL с завершающим slash и отсутствующая ссылка на FAQ; ручная синхронизация нужна |
| [robots.txt](robots.txt) | Политика обхода поисковых и AI-агентов | LIVE VERIFIED 26.11.2026 — семантически совпадает с GitLab master; публичные HTML-страницы разрешены, query-URL закрыты |
| [sitemap.xml](sitemap.xml) | Машинная карта публичных URL сайта | LIVE VERIFIED 26.11.2026 — 874 URL; URL set полностью совпадает с GitLab master; полный HTTP recrawl не повторялся |
| [ai-faq.md](ai-faq.md) | FAQ из 21 вопроса по услугам, кейсам, дикторам, правам и маршрутам заказа | SOURCE PRESENT / LIVE 404 — необходимо установить вместе с обновлённым llms.txt |
| [organization.jsonld](organization.jsonld) | Отдельная копия Organization JSON-LD, встроенной в шаблон сайта | SOURCE SNAPSHOT из GitLab master |

## Происхождение и контроль

- Источник файлов — приватный проект GitLab, ID `29409891`, пространство имён `audioreclama`.
- Проверенный GitLab `master` на 26.11.2026: `50d1c12aa925fc9a03dbf53c296544c6bce56432`.
- Текущий Organization JSON-LD извлечён из `themes/classic/views/layouts/skeleton.php`; исходная версия шаблона в GitLab — `01485d7aee4b710d5b8730837029b6667ed8aa2f`. Сам блок уже находится в шаблоне GitLab. Отдельный JSON здесь — удобный review/handoff companion, а не вторая автоматическая разметка сайта.
- `llms.txt` в GitLab master содержит канонический homepage URL без завершающего slash и ссылку на `/ai-faq.md`. Live llms.txt (Last-Modified 25.11.2026 23:10:55 GMT) отстаёт по этим шести строковым различиям. Live FAQ URL возвращает HTTP 404; исходник FAQ добавлен в этот комплект для атомарной ручной публикации.
- `robots.txt` live (Last-Modified 25.11.2026 23:10:55 GMT) семантически совпадает с GitLab master: `Disallow: /*?` ограничивает URL с query-параметрами, а не все публичные страницы. В нём нет site-wide `Disallow: /*`. Не считать robots.txt механизмом контроля доступа.
- `sitemap.xml` live endpoint (Last-Modified 25.11.2026 23:10:55 GMT) возвращает 874 URL. Его URL set полностью совпадает с GitLab master и текущим GitHub-кандидатом; дублей и расхождений нет. В XML сохранён комментарий REVIEW-ONLY с аудитом от 22.11.2026 (1 186 URL: 876 HTTP 200, 310 HTTP 404, 2 redirects). Текущие HTTP-статусы каждого из 874 URL заново не проверялись.

## Порядок ручной передачи

1. Веб-мастер получает этот комплект как согласованный source snapshot; root robots.txt и sitemap.xml уже подтверждены в live, но полное состояние сервера и 874 URL повторно не сканировалось.
2. `robots.txt` не требует замены по текущей сверке; сохранить его текущие группы агентов и исключения.
3. `sitemap.xml` сохранить как текущий 874-URL набор; отдельное исправление CMS-генератора — следующая задача, но текущий URL set совпадает с live.
4. Установить свежий `llms.txt` вместе с `ai-faq.md`, чтобы не создавать ссылку на отсутствующий публичный файл.
5. Organization JSON-LD сравнивается с текущим шаблоном; изменения в PHP-шаблон вносятся отдельно и вручную веб-мастером.

Не копировать этот каталог автоматически в document root, не включать его в GitHub Pages artifact, не создавать deploy pipeline и не сообщать, что сайт обновлён, пока уполномоченный веб-мастер не выполнит ручную публикацию.
