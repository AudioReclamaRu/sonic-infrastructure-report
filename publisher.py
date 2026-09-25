# publisher.py - autonomous TG-only publishing loop (Python remake of post-orchestrator.ps1).
# Decision 16.09.2026: channel lives in TG; Dzen auto-posts via TG<->Dzen link; FB/VK/IG off.
# Idempotent by guid. Daily per-platform caps. Re-reads items.csv every cycle (no restart needed).
#
# Usage:
#   python publisher.py --loop                 (continuous, watchdog keeps it alive)
#   python publisher.py --once                 (single cycle, exits)
#   python publisher.py --once --tg-cap 4
#
# Outputs: register.csv, calendar.html, state/heartbeat.txt, state/orchestrator.log,
#          state/quota-<date>.json, tg/tg_state.txt, state/tg.log
import argparse
import json
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

BASE = r'F:\Pill\tmp\opencode'
REPO = os.path.join(BASE, 'sonic-repo')
FEED = os.path.join(REPO, 'feed')
STATE = os.path.join(REPO, 'state')
TG_DIR = os.path.join(BASE, 'tg')
ITEMS_CSV = os.path.join(FEED, 'items.csv')
REGISTRY = os.path.join(REPO, 'register.csv')
CALENDAR = os.path.join(REPO, 'calendar.html')
HEARTBEAT = os.path.join(STATE, 'heartbeat.txt')
ORQ_LOG = os.path.join(STATE, 'orchestrator.log')
PID_FILE = os.path.join(STATE, 'orchestrator.pid')
TG_TRACKER = os.path.join(TG_DIR, 'tg_published.txt')
TG_STATE_FILE = os.path.join(TG_DIR, 'tg_state.txt')
TG_LOG = os.path.join(STATE, 'tg.log')
REJECTED_FILE = os.path.join(STATE, 'rejected.txt')
ENV_FILE = os.path.join(TG_DIR, 'env.txt')
CHANNEL_FILE = os.path.join(TG_DIR, 'feed_channel.txt')
IMG_DIR = os.path.join(FEED, 'images')
CONCEPTS_FILE = os.path.join(FEED, 'concepts.json')
CURL = r'C:\WINDOWS\system32\curl.exe'
CREATE_NO_WINDOW = 0x08000000


def invoke_curl(args: list):
    """Run curl.exe hidden (Invoke-Curl pattern); ok=True when exit code 0."""
    try:
        p = subprocess.run([CURL] + args, capture_output=True, timeout=90,
                           creationflags=CREATE_NO_WINDOW)
        out = (p.stdout or b'').decode('utf-8', errors='replace').strip()
        return p.returncode == 0, out
    except subprocess.TimeoutExpired:
        return False, 'TIMEOUT'
    except Exception as e:
        return False, 'CURL_ERR ' + str(e)


def olog(msg: str):
    os.makedirs(STATE, exist_ok=True)
    with open(ORQ_LOG, 'a', encoding='utf-8') as f:
        f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + msg + '\n')


def read_lines(path: str):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8-sig') as f:
        return [ln.rstrip('\r\n') for ln in f if ln.strip()]


def add_unique(path: str, line: str):
    cur = set(read_lines(path))
    if line in cur:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def load_env():
    env = {}
    if os.path.exists(ENV_FILE):
        for ln in read_lines(ENV_FILE):
            if '=' in ln:
                k, v = ln.split('=', 1)
                env[k.strip()] = v.strip()
    return env


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


REQ_CONCEPT_FIELDS = ('headline', 'win', 'visual_object', 'cover_prompt')


def load_concepts():
    """Editorial concepts: guid -> {headline, win, visual_object, cover_prompt}."""
    if not os.path.exists(CONCEPTS_FILE):
        return {}
    try:
        with open(CONCEPTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def concept_gate(guid: str, concepts: dict):
    """Return list of REQUIRED fields missing for guid (empty = publishable)."""
    c = concepts.get(guid) or {}
    missing = [k for k in REQ_CONCEPT_FIELDS if not (c.get(k) or '').strip()]
    return missing


def unset_line(path: str, line: str):
    """Remove `line` from a line-set file (used to release a rejected guid)."""
    if not os.path.exists(path):
        return
    cur = read_lines(path)
    nxt = [ln for ln in cur if ln != line]
    if len(nxt) != len(cur):
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(nxt) + '\n')


def parse_date(s: str):
    return parsedate_to_datetime(s)


def quota_file(day: str):
    return os.path.join(STATE, 'quota-' + day + '.json')


def load_quota(day: str):
    qf = quota_file(day)
    if os.path.exists(qf):
        try:
            with open(qf, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {'ts': day, 'tg': 0, 'fb': 0, 'vk': 0, 'ig': 0}


def save_quota(day: str, q):
    with open(quota_file(day), 'w', encoding='utf-8') as f:
        json.dump(q, f, separators=(',', ':'))


def inc_quota(day: str):
    q = load_quota(day)
    q['tg'] = int(q.get('tg', 0)) + 1
    save_quota(day, q)
    olog('QUOTA inc tg => tg=' + str(q['tg']) + ' fb=' + str(q.get('fb', 0)) +
         ' vk=' + str(q.get('vk', 0)) + ' ig=' + str(q.get('ig', 0)))


def build_registry(items):
    tg = set(read_lines(TG_TRACKER))
    lines = ['GUID~~~TITLE~~~DATE~~~TG~~~FB~~~IG~~~VK']
    for it in items:
        g = it['guid']
        lines.append(g + '~~~' + it['title'] + '~~~' + it['date'] + '~~~' +
                     ('DONE' if g in tg else '--') + '~~~--~~~--~~~--')
    with open(REGISTRY, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def html_escape(s: str) -> str:
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace('"', '&quot;'))


def build_calendar(items):
    tg = set(read_lines(TG_TRACKER))
    now = datetime.now().astimezone()
    rows = []
    for it in sorted(items, key=lambda x: parse_date(x['date'])):
        dt = parse_date(it['date'])
        g = it['guid']
        is_today = (dt.date() == now.date())
        is_future = (dt > now)
        cls = ' class="today"' if is_today else (' class="future"' if is_future else '')
        t1 = '<span class="tg ok">TG</span>' if g in tg else '<span class="tg no">-</span>'
        dt_s = dt.astimezone().strftime('%d.%m.%y %H:%M')
        rows.append('<tr{0}><td>{1}</td><td>{2}</td><td>{3}</td><td>-</td><td>-</td><td>-</td></tr>'
                    .format(cls, dt_s, html_escape(it['title']), t1))
    rows_html = '\n'.join(rows)
    tpl = ('<!DOCTYPE html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
           '<title>AudioReclama publish calendar</title>\n<style>\n'
           'body{background:#0d1117;color:#c9d1d9;font-family:Segoe UI,Arial,sans-serif;margin:0;padding:24px}\n'
           'h1{font-size:18px;color:#f0f6fc}\n'
           'table{border-collapse:collapse;width:100%;margin-top:12px}\n'
           'td,th{border:1px solid #30363d;padding:6px 10px;font-size:13px;text-align:left}\n'
           'tr.today td{background:#1f6feb22}\ntr.future td{opacity:.55}\n'
           '.ok{color:#3fb950;font-weight:600}\n.no{color:#484f58}\n'
           '.fb.ok{color:#58a6ff}.ig.ok{color:#f778ba}.vk.ok{color:#e3b341}.tg.ok{color:#3fb950}\n'
           '.foot{color:#484f58;font-size:11px;margin-top:10px}\n</style>\n</head>\n<body>\n'
           '<h1>AudioReclama - publish calendar</h1>\n<table>\n<tr><th>Date</th><th>Post</th>'
           '<th>TG</th><th>FB</th><th>IG</th><th>VK</th></tr>\n'
           + rows_html + '\n</table>\n</body>\n</html>\n')
    with open(CALENDAR, 'w', encoding='utf-8') as f:
        f.write(tpl)


def trunc_at(s: str, mx: int) -> str:
    if len(s) <= mx:
        return s
    cut = s[:mx]
    url_at = max(cut.rfind('http://'), cut.rfind('https://'))
    if url_at >= 0:
        url_end = cut.find(' ', url_at)
        if url_end < 0 or url_end > mx - 3:
            before = cut[:url_at]
            sp = before.rfind(' ')
            if sp >= 0:
                return before[:sp]
            return before
    if url_at >= 0 and url_at < mx * 0.4:
        return cut
    last = cut.rfind('.')
    if last > mx * 0.6:
        return cut[:last + 1]
    sp = cut.rfind(' ')
    if sp > mx * 0.6:
        return cut[:sp]
    return cut


def ensure_cover(guid: str, img_name: str, img_path: str):
    """Version-aware idempotency (standards/red-field-visual.md): a PNG is kept
    only when its ASSET_HASH matches DESIGN_VERSION; otherwise regenerate."""
    try:
        import sys
        gen_dir = FEED
        if gen_dir not in sys.path:
            sys.path.insert(0, gen_dir)
        import image_gen
        path = image_gen.ensure_asset(guid)
        olog('COVER_ENSURED ' + img_name + ' conflict=' + image_gen.conflict_of(guid))
        return path
    except Exception as e:
        olog('COVER_GEN_ERR ' + img_name + ' :: ' + str(e))
        return img_path


def tg_chat(env):
    chat = None
    if os.path.exists(CHANNEL_FILE):
        for ln in read_lines(CHANNEL_FILE):
            if not ln.startswith('#'):
                chat = ln.strip()
                break
    if not chat:
        raise RuntimeError('No chat target: pass -Chat or write id to tg/feed_channel.txt')
    return chat


def publish_one(guid: str, item: dict, env: dict, chat: str, concepts: dict):
    token_file = env.get('BOT_TOKEN_FILE', '')
    if not token_file or not os.path.exists(token_file):
        raise RuntimeError('BOT_TOKEN_FILE missing: ' + token_file)
    token = open(token_file, 'r', encoding='utf-8').read().strip()
    proxy = env.get('PROXY', 'socks5h://127.0.0.1:10808')
    api = env.get('API', 'https://api.telegram.org')
    base = api + '/bot' + token

    concept = concepts.get(guid) or {}
    title = (concept.get('headline') or item['title']).strip()
    win = (concept.get('win') or '').strip()
    desc = item['desc'].replace('\\n', '\n\n')
    link = item['src']
    img_path = os.path.join(IMG_DIR, item['img'] + '.png')

    img_path = ensure_cover(item['guid'], item['img'], img_path)

    footer = '\n\nИсточник: ' + link
    # Editorial order: headline comes first, then WHY (win), then the story.
    body_src = (win + '\n\n' + desc).strip() if win else desc
    max_body = 1024 - len(title) - len(footer)
    body = trunc_at(body_src, max_body)
    caption = title + '\n\n' + body + footer

    if os.path.exists(img_path):
        fd, payload = tempfile.mkstemp(suffix='.txt', prefix='tg_photo_')
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(caption)
        try:
            ok, out = invoke_curl([
                '--max-time', '60', '-s', '-x', proxy,
                '-F', 'chat_id=' + chat,
                '-F', 'caption=<' + payload + ';type=text/plain;charset=utf-8',
                '-F', 'photo=@' + img_path + ';type=image/png',
                base + '/sendPhoto'])
        finally:
            try:
                os.remove(payload)
            except OSError:
                pass
    else:
        fd, payload = tempfile.mkstemp(suffix='.txt', prefix='tg_msg_')
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(caption)
        try:
            ok, out = invoke_curl([
                '--max-time', '60', '-s', '-x', proxy,
                '-F', 'chat_id=' + chat,
                '-F', 'text=<' + payload + ';type=text/plain;charset=utf-8',
                base + '/sendMessage'])
        finally:
            try:
                os.remove(payload)
            except OSError:
                pass

    try:
        o = json.loads(out)
    except Exception:
        o = {}
    if ok and o.get('ok'):
        mid = str(o['result']['message_id'])
        title_s = o['result'].get('chat', {}).get('title', '')
        print('SENT guid=' + guid + ' msg=' + mid + ' chat=' + title_s)
        add_unique(TG_TRACKER, guid)
        with open(TG_STATE_FILE, 'a', encoding='utf-8') as f:
            f.write(guid + '\t' + mid + '\t' + chat + '\n')
        with open(TG_LOG, 'a', encoding='utf-8') as f:
            f.write('published ' + guid + ' ' + datetime.now().strftime('%Y-%m-%d') + '\n')
        return 'OK'
    else:
        print('FAIL guid=' + guid + ' -> ' + str(o))
        return 'FAIL'


def run_cycle(tg_cap: int):
    now = datetime.now().astimezone()
    items = load_items()
    build_registry(items)
    build_calendar(items)

    due = []
    for it in items:
        try:
            dt = parse_date(it['date'])
        except Exception:
            continue
        if dt <= now:
            due.append({'g': it['guid'], 'd': dt, 'it': it})
    due.sort(key=lambda x: x['d'])

    day = now.strftime('%Y-%m-%d')
    quota = load_quota(day)
    used = int(quota.get('tg', 0))
    slots = max(0, tg_cap - used)
    concepts = load_concepts()
    done = set(read_lines(TG_TRACKER))
    rejected = set(read_lines(REJECTED_FILE))
    if slots == 0:
        olog('CAP tg (' + str(used) + '/' + str(tg_cap) + ')')
        summ = ['tg=0/0']
    else:
        # 1) Editorial gate (frozen until concept filled; does NOT consume slots):
        #    freeze due items missing concept fields, release ones now complete.
        for it in due:
            g = it['g']
            miss = concept_gate(g, concepts)
            if miss and g not in done and g not in rejected:
                olog('REJECT ' + g + ' missing=' + ','.join(miss))
                add_unique(REJECTED_FILE, g)
                rejected = set(read_lines(REJECTED_FILE))
            elif not miss and g in rejected:
                unset_line(REJECTED_FILE, g)
                rejected = set(read_lines(REJECTED_FILE))
        rej_frozen = len([g for g in rejected if g in set(x['g'] for x in due)])
        # 2) Only fully-concepted items consume the daily cap.
        cands = [x for x in due if x['g'] not in done and x['g'] not in rejected][:slots]
        env = load_env()
        chat = tg_chat(env)
        ok = fail = 0
        for c in cands:
            it = next((y for y in items if y['guid'] == c['g']), None)
            if it is None:
                continue
            try:
                st = publish_one(c['g'], it, env, chat, concepts)
            except Exception as e:
                olog('WATCHDOG_ERR publish ' + c['g'] + ' :: ' + str(e))
                st = 'FAIL'
            if st == 'OK':
                ok += 1
            elif st == 'FAIL':
                fail += 1
            time.sleep(2)
        summ = ['tg=' + str(ok) + '/' + str(fail) +
                ('' if rej_frozen == 0 else ' frozen=' + str(rej_frozen))]

    with open(HEARTBEAT, 'w', encoding='utf-8') as f:
        f.write(now.astimezone().isoformat(timespec='seconds') + '\n')
    olog('CYCLE ' + now.strftime('%Y-%m-%d %H:%M:%S') + ' :: ' + ' '.join(summ))
    print('CYCLE ' + now.strftime('%Y-%m-%d %H:%M:%S') + ' :: ' + ' '.join(summ))
    print('CYCLE_DONE')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--once', action='store_true')
    ap.add_argument('--loop', action='store_true')
    ap.add_argument('--tg-cap', type=int, default=4)
    ap.add_argument('--interval', type=int, default=300)
    args = ap.parse_args()

    if args.loop:
        os.makedirs(STATE, exist_ok=True)
        with open(PID_FILE, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()) + '\n')
        while True:
            try:
                run_cycle(args.tg_cap)
            except Exception as e:
                olog('WATCHDOG_ERR ' + str(e))
                print('WATCHDOG_ERR ' + str(e))
            time.sleep(args.interval)
    else:
        run_cycle(args.tg_cap)


if __name__ == '__main__':
    main()