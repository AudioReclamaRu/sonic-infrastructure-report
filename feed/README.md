# feed/ — RSS-лента для автоимпорта в VK (и другие синдкаторы)

Правило: лента генерируется из `items.csv` скриптом `rss-gen.ps1` и коммитится.
Ничего руками в `rss.xml` не править — только `items.csv` (строки: `pubDate~~~title~~~description~~~link~~~guid`, новое сверху, RFC822-даты).

Доступные URL (после push):
- raw: https://raw.githubusercontent.com/AudioReclamaRu/sonic-infrastructure-report/main/feed/rss.xml
- jsDelivr: https://cdn.jsdelivr.net/gh/AudioReclamaRu/sonic-infrastructure-report@main/feed/rss.xml

ВК: Управление сообществом → Интеграции → RSS-импорт → вставить URL → тип публикации.