# Инструкция для ИИ-агента: подключение к инфраструктуре Audio-Reclama

## Быстрый старт (3 минуты)

### 1. Прокси для Telegram

Telegram Bot API заблокирован из корпуса. Используй SOCKS5-прокси через Xray:

```bash
# Прокси работает на:
SOCKS5: 127.0.0.1:10808
HTTP:   127.0.0.1:10809

# Проверь доступность:
curl -x socks5h://127.0.0.1:10808 "https://api.telegram.org/bot<TOKEN>/getMe"
```

Если прокси не работает — перезапусти Xray:
```powershell
$cmd = '"F:\Pill\tmp\opencode\v2ray\xray\xray.exe" -config "F:\Pill\tmp\opencode\v2ray\run\config.json"'
Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd }
```

### 2. Telegram Bot API

**Токен бота:** `F:\Pill\tmp\opencode\tg\bot_token.txt` (не светить!)

**Получить_updates:**
```bash
curl -x socks5h://127.0.0.1:10808 "https://api.telegram.org/bot<TOKEN>/getUpdates?limit=10"
```

**Отправить сообщение:**
```bash
curl -x socks5h://127.0.0.1:10808 \
  -H "Content-Type: application/json" \
  -d '{"chat_id":58308448,"text":"Твоё сообщение"}' \
  "https://api.telegram.org/bot<TOKEN>/sendMessage"
```

**Ключевые chat_id:**
- `58308448` — Игорь (true_tabakov) — владелец

**Готовые скрипты (PowerShell):**
- `F:\Pill\tmp\opencode\tg\getupdates.ps1` — получить обновления
- `F:\Pill\tmp\opencode\tg\publish.ps1 -Draft <путь>` — отправить сообщение

**Формат черновика для publish.ps1:**
```json
{"chat_id":58308448,"text":"Текст сообщения"}
```

### 3. VK (публичные посты)

**Способ 1: RSS-импорт (рекомендуется)**
- RSS-лента: `https://cdn.jsdelivr.net/gh/AudioReclamaRu/sonic-infrastructure-report@main/feed/rss.xml`
- Настройка в сообществе уже выполнена (Интеграции → RSS-импорт)
- Чтобы опубликовать: добавь элемент в `F:\Pill\tmp\opencode\sonic-repo\feed\items.csv`
- Формат строки: `pubDate~~~title~~~description~~~link~~~guid`
- Запусти генерацию: `powershell -File F:\Pill\tmp\opencode\sonic-repo\feed\rss-gen.ps1`
- Запушь в git: `git add feed; git commit -m "feed: ..."; git push`
- VK автоматически подхватит ленту

**Способ 2: VK API напрямую (нужен токен)**
```bash
curl "https://api.vk.com/method/wall.post?owner_id=-18300431&message=Текст&access_token=<TOKEN>&v=5.199"
```

### 4. GitHub API (для аналитики)

**Репо:** `AudioReclamaRu/sonic-infrastructure-report`
**Доступ:** публичный, без токена (60 запросов/час)

```bash
# Последние коммиты
curl "https://api.github.com/repos/AudioReclamaRu/sonic-infrastructure-report/commits?per_page=5"

# Содержимое файла
curl "https://api.github.com/repos/AudioReclamaRu/sonic-infrastructure-report/contents/corpus/state-of-voice-2026.md"

# Поиск по коду
curl "https://api.github.com/search/code?q=repo:AudioReclamaRu/sonic-infrastructure-report+voice"
```

### 5. HN Algolia (для мониторинга новостей)

```bash
# Поиск по заголовкам
curl "https://hn.algolia.com/api/v1/search?query=voice+AI&tags=story&hitsPerPage=10"

# Поиск по URL
curl "https://hn.algolia.com/api/v1/search?query=url:elevenlabs&tags=story"
```

### 6. Доступ к файлам репо

**Локальный путь:** `F:\Pill\tmp\opencode\sonic-repo\`

**Ключевые директории:**
- `evidence/` — проверенные источники (E-2026-XXX.md)
- `corpus/` — таймлайны и состояния рынка
- `entity/` — сущности (компании, люди)
- `reports/signals/` — ежедневные сигналы
- `feed/` — RSS-лента (items.csv, rss-gen.ps1)

**Работа с git:**
```bash
cd F:\Pill\tmp\opencode\sonic-repo
git pull
# ... изменения ...
git add .
git commit -m "описание"
git push origin main
```

## Архитектура

```
ИИ-агент
    ↓
[SOCKS5 127.0.0.1:10808] ← Xray (VMess WS)
    ↓
Telegram Bot API ←→ Бот @Saturn_trade_bot
    ↓
Чаты пользователей

GitHub API (напрямую) ← Репозиторий
HN Algolia (напрямую) ← Мониторинг новостей
VK API (напрямую, нужен токен) ← Сообщество
VK RSS (автоимпорт) ← feed/rss.xml
```

## Автоматизация публикаций

### Ежедневный цикл
1. Собрать сигналы (HN, GitHub, прямые URL)
2. Проверить источники (evidence)
3. Обновить таймлайн (corpus)
4. Сгенерировать RSS (если есть новый сильный сигнал)
5. Запушить в git
6. VK автоматически опубликует

### Правило публикации
- Публиковать только сильные, полностью готовые материалы
- Не плодить поштучно — копить и выбирать лучшее
- Максимум 1-2 сильных поста в неделю

## Траблшутинг

### Прокси не работает
```powershell
# Проверь статус Xray
Get-Process xray
Test-NetConnection -ComputerName 127.0.0.1 -Port 10808

# Перезапусти если нужно
Stop-Process -Name xray -Force
$cmd = '"F:\Pill\tmp\opencode\v2ray\xray\xray.exe" -config "F:\Pill\tmp\opencode\v2ray\run\config.json"'
Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd }
```

### Telegram API отвечает ошибкой
1. Проверь прокси: `curl -x socks5h://127.0.0.1:10808 "https://api.telegram.org/bot<TOKEN>/getMe"`
2. Если прокси работает, но API не отвечает — проверь токен в `tg/bot_token.txt`
3. Если токен неверный — попроси владельца сгенерировать новый через @BotFather

### VK не публикует из RSS
1. Проверь URL ленты: `curl "https://cdn.jsdelivr.net/gh/AudioReclamaRu/sonic-infrastructure-report@main/feed/rss.xml"`
2. Проверь формат items.csv (разделитель `~~~`)
3. Убедись что rss.xml сгенерирован и запушен

### GitHub API лимит
- Лимит: 60 запросов/час без токена
- Проверь: `curl "https://api.github.com/rate_limit"`
- Для увеличения лимита нужен персональный токен

## Контакты

- **Владелец:** Игорь (true_tabakov)
- **Бот:** @Saturn_trade_bot
- **Сайт:** https://www.audio-reclama.ru/
- **Репо:** https://github.com/AudioReclamaRu/sonic-infrastructure-report

## Важные замечания

1. **Не свети токен бота** — хранится в `tg/bot_token.txt`
2. **Для Russian-сервисов** (VK, Дзен) — отключай прокси, работай напрямую
3. **Для заблокированных сервисов** (Telegram) — используй прокси
4. **Коммить только готовое** — не пушь черновики в основную ветку
5. **Следи за лимитами** — GitHub API (60/час), VK API (требует токен)
## Signal engine tools (tooling/ folder)
- **tools/search-web.ps1** - web search via DuckDuckGo HTML (no API key, works when websearch MCP is 403). Usage:
  powershell -File tools/search-web.ps1 -Query "UMG ElevenLabs AI voice" -Out results.json [-Max 5]
  Falls back to SOCKS5 proxy (127.0.0.1:10808) when direct calls are blocked or empty.
- **tools/signal-scan.ps1** - daily market scan: HN Algolia (5 queries, points>=10, recency<=14d) + 3 DDG web queries.
  Output: reports/scans/scans-<date>.md + F:\Pill\tmp\opencode\tg\scan\<date>.json (used by the bot /digest).
  Run daily (scheduled task). Tested: ~27 items/day.
- **tg/digest-tg.ps1** - builds a TG digest message from the latest scan and sends to a chat:
  powershell -File tg/digest-tg.ps1 -Chat 58308448 -Limit 8
- **Web search status:** websearch MCP => 403 (provider-side). USE DuckDuckGo fallback instead.
- **Operator rule:** if DuckDuckGo returns 0 results, retry; if still 0, try via proxy; wait ~5s between queries (rate limit).
