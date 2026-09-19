#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""voice_alert.py — редакционный сторож контура «Культура Голоса».
Отдельный процесс (НЕ publisher.py, тот не трогаем). Читает те же файлы,
которые пишет orchestrator:
  - state/heartbeat.txt   (dead-man's switch, обновляем паблишером)
  - state/orchestrator.log (лог для контекста, но алерт считаем только по heartbeat)
  - feed/items.csv        (очередь с датами)
  - tg/tg_published.txt   (уже опубликованные guid)
Отправляет в TG-канал ровно ОДИН алерт при входе в «риск-эпизод»:
  - паблишер не писал heartbeat дольше порога, ЛИБО
  - есть прошедший due-пост, который не опубликован.
Дедупликация: повторный алерт не раньше чем через ALERT_DEDUP_S (30 мин).
Релиз канала доставки — ТОТ ЖЕ, что у publisher (curl.exe + socks5h + sendMessage):
работает там, где requests/pytgcurllib падает (проверено: 10 живых постов в TG).

Запуск:
  python voice_alert.py            # один проход (для планировщика)
  python voice_alert.py --loop     # цикл каждые 20 с (для сторожевого процесса)
"""
import os
import subprocess
import tempfile
import time
from datetime import datetime, timezone

# ---------- пути (бери из publisher.py, не дублируй иначе) ----------
BASE = r'F:\Pill\tmp\opencode'
REPO = os.path.join(BASE, 'sonic-repo')
FEED = os.path.join(REPO, 'feed')
STATE = os.path.join(REPO, 'state')
TG = os.path.join(BASE, 'tg')
HEARTBEAT = os.path.join(STATE, 'heartbeat.txt')
ORQ_LOG = os.path.join(STATE, 'orchestrator.log')
ITEMS_CSV = os.path.join(FEED, 'items.csv')
TG_TRACKER = os.path.join(TG, 'tg_published.txt')
ENV_FILE = os.path.join(TG, 'env.txt')
CHANNEL_FILE = os.path.join(TG, 'feed_channel.txt')
ALERT_STATE = os.path.join(STATE, 'voice_alert_state.txt')
ALERT_DEDUP_S = 1800                 # 30 мин между пиками
HB_STALE_MAX_S = 600                 # >10 мин без heartbeat = паблишер не отвечает

CURL = r'C:\WINDOWS\system32\curl.exe'
CREATE_NO_WINDOW = 0x08000000
PROXY = 'socks5h://127.0.0.1:10808'
API = 'https://api.telegram.org'


def read_lines(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return [ln.rstrip('\r\n') for ln in f if ln.strip()]
    except OSError:
        return []


def load_env():
    env = {}
    if os.path.exists(ENV_FILE):
        for ln in read_lines(ENV_FILE):
            if '=' in ln:
                k, v = ln.split('=', 1)
                env[k.strip()] = v.strip()
    return env


def tg_chat():
    for ln in read_lines(CHANNEL_FILE):
        if not ln.startswith('#') and ln.strip():
            return ln.strip()
    return None


def bot_token(env):
    tok_file = env.get('BOT_TOKEN_FILE', '')
    if not tok_file or not os.path.exists(tok_file):
        return None
    try:
        with open(tok_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except OSError:
        return None


def invoke_curl(args):
    try:
        p = subprocess.run([CURL] + args, capture_output=True, timeout=90,
                           creationflags=CREATE_NO_WINDOW)
        out = (p.stdout or b'').decode('utf-8', errors='replace').strip()
        return p.returncode == 0, out
    except subprocess.TimeoutExpired:
        return False, 'TIMEOUT'
    except Exception as e:
        return False, 'CURL_ERR ' + str(e)


def send_tg(env, chat, text):
    token = bot_token(env)
    if not token or not chat:
        return False, 'no token/chat'
    fd, payload = tempfile.mkstemp(suffix='.txt', prefix='voice_alert_')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(text)
    try:
        return invoke_curl([
            '--max-time', '60', '-s', '-x', PROXY,
            '-F', 'chat_id=' + chat,
            '-F', 'text=<' + payload + ';type=text/plain;charset=utf-8',
            API + '/bot' + token + '/sendMessage'])
    finally:
        try:
            os.remove(payload)
        except OSError:
            pass


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
        items.append({'date': p[0].strip(), 'title': p[1], 'desc': p[2],
                      'src': p[3], 'guid': p[4], 'img': p[5]})
    return items


def parse_dt(s):
    if not s:
        return None
    s = s.strip()
    for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def read_alert_state():
    try:
        with open(ALERT_STATE, 'r', encoding='utf-8') as f:
            v = f.read().strip()
        return float(v) if v else 0.0
    except Exception:
        return 0.0


def write_alert_state(ts):
    os.makedirs(STATE, exist_ok=True)
    with open(ALERT_STATE, 'w', encoding='utf-8') as f:
        f.write(str(ts))


def hb_timestamp():
    """Mtime heartbeat.txt = время последнего цикла паблишера."""
    try:
        return os.path.getmtime(HEARTBEAT)
    except OSError:
        return 0.0


def calc_risk(now_ts):
    """Проверка риска. Возвращает (risk_msgs, chat_txt_or_None)."""
    risk = []

    # 1) паблишер жив?
    hb = hb_timestamp()
    if hb <= 0:
        risk.append('нет heartbeat-файла')
    else:
        stale = now_ts - hb
        if stale > HB_STALE_MAX_S:
            risk.append('паблишер молчит +' + str(int(stale // 60)) + ' мин')

    # 2) есть просроченный неопубликованный пост?
    published = set(read_lines(TG_TRACKER))
    now = datetime.now(timezone.utc)
    for it in load_items():
        dt = parse_dt(it.get('date'))
        if dt is None:
            continue
        if dt <= now and it['guid'] not in published:
            risk.append('ПРОСРОЧЕН ' + it.get('title', it['guid'])[:40])

    if not risk:
        return [], None
    txt = ('\u26A0 ГОЛОС: риск-эпизод\n' +
           ' · '.join(risk) +
           '\nВремя: ' + datetime.now().strftime('%d.%m %H:%M') +
           '\nДашборд: http://127.0.0.1:8765/ (вкладка ГОЛОС)')
    return risk, txt


def tick():
    now = time.time()
    risk, txt = calc_risk(now)
    if not risk:
        return
    last = read_alert_state()
    if now - last < ALERT_DEDUP_S:
        return
    env = load_env()
    chat = tg_chat()
    ok, out = send_tg(env, chat, txt)
    if ok:
        write_alert_state(now)
        print(datetime.now().isoformat() + ' ALERT OK chat=' + str(chat))
    else:
        print(datetime.now().isoformat() + ' ALERT FAIL ' + out[:120])


def main():
    if '--loop' in sys.argv:
        while True:
            try:
                tick()
            except Exception as e:
                print(datetime.now().isoformat() + ' ALERT_ERR ' + str(e))
            time.sleep(20)
    else:
        tick()


if __name__ == '__main__':
    main()
