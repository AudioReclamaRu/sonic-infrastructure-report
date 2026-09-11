# feed/ — RSS-лента для автоимпорта в VK (и другие синдкаторы)

Правило: лента генерируется из `items.csv` скриптом `rss-gen.ps1` и коммитится.
Ничего руками в `rss.xml` не править — только `items.csv` (строки: `pubDate~~~title~~~description~~~link~~~guid~~~image`, новое сверху, RFC822-даты, `\n` = перенос абзаца, col5=имя обложки `images/<name>.png`).
Если у поста нет обложки — пустая колонка 6, enclosure не добавляется.

Сборка: `powershell -File feed/image-gen.ps1 -ItemsCsv feed/items.csv` → `powershell -File feed/rss-gen.ps1`, затем коммит + push.

Доступные URL (после push):
- raw: https://raw.githubusercontent.com/AudioReclamaRu/sonic-infrastructure-report/main/feed/rss.xml
- jsDelivr: https://cdn.jsdelivr.net/gh/AudioReclamaRu/sonic-infrastructure-report@main/feed/rss.xml

ВК: Управление сообществом → Интеграции → RSS-импорт → вставить URL → тип публикации.
jsDelivr: новый коммит инвалидирует кэш автоматически (обычно в течение минут, worst case 12ч); для проверки версии — raw.githubusercontent.

## Слоты ленты (на 2026-09-16)

Evidence-слой (проверяемость):
- 11.09 voice-scams-trust — голосовой фишинг +1210%, доверие живому голосу (E-2026-016)
- 11.09 rynok-dve-storony — ИИ на объём, люди на доверие (E-2026-016/017)
- 10.09 umg-elevenlabs — UMG×ElevenLabs: первая лицензия (E-2026-016)
- 10.09 edison-verdict — вердикт СОСТОЯЛОСЬ, цифры слепого теста (corpus/edison-blind-test.md)
- 04.09 fitoussi-human-preference — рационально предпочитать живое (E-2026-017)

Конверсионный слой (потребность → компетенция → решение → контакт):
- 12.09 kto-proveril-golos — проверка голоса до эфира (corpus/kto-vypuskaet-golos.md)
- 13.09 golos-banka — IVR-меню: что проверить перед эфиром (guides/bank-voice-menu.md)
- 14.09 vybor-diktora — 5 правил выбора диктора (guides/choosing-a-voice.md)
- 15.09 ozvuchka-video — финальная версия ролика (guides/video-voiceover.md)
- 16.09 obyavleniya-aeroporta — перевод или смысл (guides/airport-announcements.md)

Каждый конверсионный пост закрывается конкретным бесплатным действием (проверка/тест-фрагмент/хронометраж) на start@audio-reclama.ru + 8-800-700-46-52.