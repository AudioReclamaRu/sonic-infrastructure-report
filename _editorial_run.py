#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""voice_watchdog.py — DESKTOP-сторож контура «Культура Голоса».
Второй (локальный) канал доставки риска: работает когда браузер закрыт,
вкладка ГОЛОС не открыта, дашборд не запущен, TG-бот задержал.

Смотрит ровно те же файлы, что dashboard_feed и voice_alert (единый источник):
  state/heartbeat.txt   — свежесть паблишера (dead-man's switch)
  feed/items.csv        — очередь с датами
  tg/tg_published.txt   — уже отправленные guid'ы (дедуп "опубликовано")

Эпизод риска:
  - heartbeat старше HB_STALE_MAX_S (паблишер не пишет циклы), ЛИБО
  - есть пост с датой <= сейчас, который ещё не опубликован (просрочка).

Поведение ПРИ ВХОДЕ в эпизод (один раз на эпизод — дедуп ALERT_DEDUP_S):
  1) системный звук  (winsound.Beep: 880 Гц, 240 мс — входит сразу, без прокси)
  2) Windows-toast    (powershell.exe -WindowStyle Hidden -sta [Windows.UI.Notifications]).
  3) лог в state/voice_watchdog.log.
При спаде риска — сброс дедупа (следующий эпизод снова просигналит).

Полностью НЕЗАВИСИМ от publisher.py / voice_alert.py — ноль пересечений,
не трогает ни их файлы, ни их процессы.

Запуск:
  python voice_watchdog.py            # один проход (для Task Scheduler, каждые ~60с)
  python voice_watchdog.py --loop     # постоянный цикл (каждые 20 с)

Регистрация в планировщике — через скрытый VBS-обёртку (см. §8.9, НЕ голый
powershell.exe). Рекомендуемый Task:
  Имя: SonicVoiceWatchdog  |  Интервал: 1 мин  |  Действие: wscript hidden.vbs
"""
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

BASE = r'F:\Pill\tmp\opencode'
REPO = os.path.join(BASE, 'sonic-repo')
FEED = os.path.join(REPO, 'feed')
STATE = os.path.join(REPO, 'state')
TG = os.path.join(BASE, 'tg')

HB_FILE = os.path.join(STATE, 'heartbeat.txt')
ORQ_LOG = os.path.join(STATE, 'orchestrator.log')
ITEMS_CSV = os.path.join(FEED, 'items.csv')
TG_PUB = os.path.join(TG, 'tg_published.txt')
WATCH_LOG = os.path.join(STATE, 'voice_watchdog.log')
WATCH_STATE = os.path.join(STATE, 'voice_watchdog_state.txt')

HB_STALE_MAX_S = 600          # >10 мин без heartbeat = паблишер не отвечает
ALERT_DEDUP_S = 1800          # 30 мин между сигналами (эпизод-дедуп)
CHECK_INTERVAL_S = 20         # шаг цикла (режим --loop)
TOAST_TITLE = '⚠ ГОЛОС: риск-эпизод'
CURL = r'C:\WINDOWS\system32\curl.exe'
CREATE_NO_WINDOW = 0x08000000
BELL_LOUD = (880, 240)        # (Гц, мс) — слышно даже на свернутом окне


def log(msg: str):
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(WATCH_LOG, 'a', encoding='utf-8') as f:
            f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + msg + '\n')
    except OSError:
        pass


def read_lines(path: str):
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return [ln.rstrip('\r\n') for ln in f if ln.strip()]
    except OSError:
        return []


def hb_stale_s() -> float:
    try:
        return time.time() - os.path.getmtime(HB_FILE)
    except OSError:
        return float('inf')          # нет heartbeat = паблишер мёртв/никогда не жил


def load_published():
    return set(read_lines(TG_PUB))


def load_items():
    items = []
    if not os.path.exists(ITEMS_CSV):
        return items
    for row in read_lines(ITEMS_CSV):
        if row.startswith('TITLE~~~') or row.startswith('DESC~~~'):
            continue
        p = row.split('~~~')
        if len(p) < 6:
            continue
        items.append({'date': p[0].strip(), 'guid': p[4].strip(),
                      'title': p[1]})
    return items


def parse_utc(s: str):
    if not s:
        return None
    s = s.strip()
    for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def calc_risk():
    """(наличие_риска, человекочитаемый текст)"""
    now = datetime.now(timezone.utc)

    # 1) паблишер мёртв?
    stale = hb_stale_s()
    if stale > HB_STALE_MAX_S:
        m = 'паблишер не отвечает (' + str(int(stale // 60)) + ' мин без heartbeat)'
        return True, m

    # 2) просроченный неопубликованный пост?
    pub = load_published()
    for it in load_items():
        dt = parse_utc(it.get('date'))
        if dt is None:
            continue
        if dt <= now and it['guid'] not in pub:
            m = 'просрочен пост от ' + it['date'] + ': ' + (it['title'] or it['guid'])[:40]
            return True, m

    return False, ''


def beep():
    """Системный звук — через winsound (Windows), без запуска новых процессов."""
    try:
        import winsound
        winsound.Beep(*BELL_LOUD)
        return True
    except Exception as e:
        log('BEEP_ERR ' + str(e))
        return False


def toast(text: str):
    """Windows-тост через скрытый PowerShell. НЕ трогает publisher/вестерн-рельс."""
    ps = (r'-sta -WindowStyle Hidden -NoProfile -Command ' +
          r"New-BurntToastNotification -Text '" + '; ' + text + r"'" + r"""
        $ErrorActionPreference='SilentlyContinue'
        try {
          [Windows.UI.Notifications.ToastNotificationManager,
           Windows.UI.Notifications, ContentType=WindowsRuntime] > $null
        } catch {}
        $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(
          [Windows.UI.Notifications.ToastTemplateType]::ToastText02)
        $txt = $xml.GetElementsByTagName('text')
        $txt.Item(0).AppendChild($xml.CreateTextNode('⚠ ГОЛОС: риск')) > $null
        $txt.Item(1).AppendChild($xml.CreateTextNode($args[0])) > $null
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier(
          'SonicVoiceWatchdog').Show($toast)
        """)
    try:
        subprocess.Popen(['powershell.exe', '-NoProfile', '-Command', ps],
                         creationflags=CREATE_NO_WINDOW)
        log('TOAST ' + text[:60])
    except Exception as e:
        log('TOAST_ERR ' + str(e))


def read_state():
    try:
        if os.path.exists(WATCH_STATE):
            with open(WATCH_STATE, 'r', encoding='utf-8') as f:
                return float(f.read().strip() or 0)
    except (OSError, ValueError):
        pass
    return 0.0


def write_state(ts):
    try:
        with open(WATCH_STATE, 'w', encoding='utf-8') as f:
            f.write(str(ts))
    except OSError:
        pass


def tick():
    now = time.time()
    risk, msg = calc_risk()
    if not risk:
        write_state(0.0)              # спад → сброс дедупа
        return
    last = read_state()
    if now - last < ALERT_DEDUP_S:
        return                          # уже сигналили в этом эпизоде
    beep()
    toast(msg)
    write_state(now)
    log('RISK ' + msg)


def main():
    if '--loop' in sys.argv:
        while True:
            try:
                tick()
            except Exception as e:
                log('ERR ' + str(e))
            time.sleep(CHECK_INTERVAL_S)
    else:
        tick()


if __name__ == '__main__':
    main()
# --- EDITORIAL CHECK (read-only) ---
import subprocess
print('EDITORIAL_START')
pub = load_published() if os.path.exists(TG_PUB) else set()
print('PUBLISHED_GUIDS='+str(len(pub)))
items = load_items()
now = datetime.now(timezone.utc)
due = []
for it in items:
    d = parse_utc(it.get('date'))
    if d is None: 
        continue
    if d <= now and it.get('guid') not in pub:
        due.append((it.get('date'), it.get('title') or it.get('guid')))
print('TOTAL_ITEMS='+str(len(items)))
print('DUE_UNPUBLISHED='+str(len(due)))
for x in due:
    print('DUE> '+x[0]+' :: '+x[1][:50])
print('EDITORIAL_DONE')