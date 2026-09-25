# feed/ — редакционный слой публикаций (TG-first)

Это **издательский контур** канала: расписание, редакционные концепты, обложки.
Публикация выполняется автономным лупом `publisher.py --loop` (TG-first,
идемпотентность по `guid`), а не руками.

## Файлы

| Файл | Роль |
|---|---|
| `items.csv` | Расписание. Строка: `pubDate~~~title~~~desc~~~source~~~guid~~~img` (6 полей, RFC822-дата, `\n` = перенос абзаца, col5=guid, col6=имя обложки `images/<name>.png`) |
| `concepts.json` | Редакционные концепты: `{guid: {headline, win, visual_object, cover_prompt}}` — **гейт публикации** (см. ниже) |
| `image_gen.py` | Version-aware генератор обложек (RED FIELD, арт-директор). CLI: `--verify / --rebuild / --force / --guid` |
| `images/manifest.json` | Единственный источник истины по обложкам (см. контракт ниже) |
| `tests/` | Тесты контракта генератора (`test_image_gen_versioning.py`) |

## Редакционный гейт (обязательный слой концептов)

Пост публикуется **только** если в `concepts.json` заполнены все четыре поля:

- `headline` — что изменилось (сдвиг, а не объект; заголовок не называет предмет)
- `win` — почему это важно для читателя
- `visual_object` — что запомнится через неделю (конкретный предмет кадра)
- `cover_prompt` — как снять именно этот предмет

Если поля не заполнены — REJECT: guid замораживается в
`state/rejected.txt` (не потребляет дневной лимит TG, не спамит циклами).
Как только концепт заполнен — заморозка снимается автоматически.

Заголовок поста = `headline`. Тело начинается с `win`, дальше — текст из
`items.csv`. Рекламных хвостов (CTA, контакты, хэштеги) в постах нет.

## Обложки: version-aware RED FIELD (арт-директор)

- `DESIGN_VERSION` в `image_gen.py` — текущая версия визуального языка.
- `images/manifest.json`: `{guid: {design_version, asset_hash, generated_at, path, visual_object?}}`.
- `path` — **POSIX-стиль** (`feed/images/<name>.png`, `/`, не `\`).
- `ASSET_HASH = SHA256(CONTENT_ID + ":" + DESIGN_VERSION)` — без seed; изменение
  визуального языка = bump `DESIGN_VERSION` = автоматический перевыпуск всех
  обложек, устаревшие PNG уходят в `images/backup-red-field/`.
- PNG не может оставаться актуальным только по факту существования файла —
  нужен манифест (version + hash), совпадающий с кодом.
- У каждой новости, которая прошла гейт, — **один визуальный объект**
  (`visual_object` из концепта): красный — акцент, а не заливка.
- Уникальность: новый кадр сравнивается dHash с последними 20 обложками; если
  слишком похож — авто-твист кадра (до 6 попыток).
- На картинке нет текста: чёрное поле, сигнал, предмет.

CLI (проверки перед рестартом / после правок):
```
python feed/image_gen.py --verify     # stale=0 + exit 0 — всё актуально
python feed/image_gen.py --rebuild    # перевыпуск только устаревших
tools/check-covers.ps1                # unittest + --verify (CI)
```

## RSS (VK, осталось как зеркало)

`rss-gen.ps1` собирает `rss.xml` из `items.csv` для VK RSS-импорта.
Правило прежнее: руками в `rss.xml` не править — только `items.csv`,
затем `powershell -File feed/rss-gen.ps1` + коммит + push.
- raw: https://raw.githubusercontent.com/AudioReclamaRu/sonic-infrastructure-report/main/feed/rss.xml
- jsDelivr (кэш до ~24ч): https://cdn.jsdelivr.net/gh/AudioReclamaRu/sonic-infrastructure-report@main/feed/rss.xml