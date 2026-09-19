import sys, os, time
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

R = r'F:\Pill\tmp\opencode\sonic-repo'
sys.path.insert(0, R)
try:
    import voice_watchdog as wd
    print('IMPORT_WD=OK')
    print('WD_BASE=' + wd.BASE)
    print('WD_REPO=' + wd.REPO)
    print('WD_FEED=' + wd.FEED)
    print('WD_STATE=' + wd.STATE)
    print('WD_HB_FILE=' + wd.HB_FILE)
    print('WD_ITEMS_CSV=' + wd.ITEMS_CSV)
    print('WD_WATCH_LOG=' + wd.WATCH_LOG)
    print('WD_WATCH_STATE=' + wd.WATCH_STATE)
except Exception as e:
    print('IMPORT_WD_ERR=' + str(e))

print('NOW=' + datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT'))

import publisher as pub_mod
print('PUB_BASE=' + pub_mod.BASE)
print('PUB_REPO=' + pub_mod.REPO)
print('PUB_HB=' + pub_mod.HB_FILE)
print('PUB_ITEMS=' + pub_mod.ITEMS_CSV)
print('PUB_TG=' + pub_mod.TG_TRACKER)
print('PUB_PID=' + pub_mod.PID_FILE)

hb = os.path.join(R, 'state', 'heartbeat.txt')
print('HB_FILE_EXISTS=' + str(os.path.exists(hb)))
if os.path.exists(hb):
    age = time.time() - os.path.getmtime(hb)
    print('HB_AGE_S=' + str(int(age)))
    try:
        with open(hb, encoding='utf-8') as f:
            print('HB_CONTENT=' + f.read().strip()[:100])
    except Exception as e:
        print('HB_READ_ERR=' + str(e))
else:
    print('HB_MISSING=YES (паблишер не пишет = риск!)')

items_csv = os.path.join(R, 'feed', 'items.csv')
print('ITEMS_EXISTS=' + str(os.path.exists(items_csv)))

def parse_utc(s):
    s = s.strip()
    for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None

pub = set()
pubfile = os.path.join(R, 'tg', 'tg_published.txt')
if os.path.exists(pubfile):
    with open(pubfile, encoding='utf-8') as f:
        for ln in f:
            s = ln.strip()
            if s:
                pub.add(s)
print('PUBLISHED_COUNT=' + str(len(pub)))

now = datetime.now(timezone.utc)
punctual = 0
due = []
total = 0
if os.path.exists(items_csv):
    for ln in open(items_csv, encoding='utf-8'):
        s = ln.strip()
        if not s or s.startswith('TITLE') or s.startswith('DESC'):
            continue
        parts = s.split('~~~')
        if len(parts) < 4:
            continue
        total += 1
        dt = parse_utc(parts[0])
        guid = parts[3].strip() if len(parts) > 3 else ''
        title = parts[1][:40] if len(parts) > 1 else ''
        if dt is None:
            due.append(('NODATE', parts[1][:40] if len(parts) > 1 else '', guid)); continue
        if dt <= now:
            if guid in pub:
                punctual += 1
            else:
                due.append((dt.strftime('%Y-%m-%d %H:%M:%S'), title, guid))
print('ITEMS_TOTAL=' + str(total))
print('DUE_UNPUBLISHED=' + str(len(due)))
for d, t, g in due:
    print('  DUE> ' + d + ' | ' + t + ' | ' + g)
