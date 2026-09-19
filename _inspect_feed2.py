# -*- coding: utf-8 -*-
import sys, os, re, datetime, email.utils
sys.stdout.reconfigure(encoding='utf-8')
R = r'F:\Pill\tmp\opencode\sonic-repo'
ITEMS = os.path.join(R, 'feed', 'items.csv')
TG_PUB = rF'F:\Pill\tmp\opencode\tg\tg_published.txt'

def rows_split(path):
    with open(path, encoding='utf-8') as f:
        raw = f.read()
    return [r for r in raw.split('\n') if r.strip('\r')]

def parse_date(s):
    return email.utils.parsedate_to_datetime(s)

now = datetime.datetime.now(datetime.timezone.utc)
print('NOW_UTC=' + now.isoformat())

items = rows_split(ITEMS)
print('ITEMS_LINES=' + str(len(items)))

pub = set()
if os.path.exists(TG_PUB):
    pub = set(l.strip() for l in rows_split(TG_PUB))
print('TG_PUBLISHED_GUIDS=' + str(len(pub)))

rows = []
for ln in items:
    parts = ln.split('~~~')
    if len(parts) < 4:
        continue
    title, date_s, guid = parts[1], parts[0], parts[3] if len(parts) > 3 else ''
    try:
        dt = parse_date(date_s)
        ok = True
    except Exception:
        dt, ok = None, False
    st = 'BAD_DATE' if not ok else ('DUE??' if dt <= now else ('FUT' if dt > now else '?'))
    pub_flag = 'PUB' if guid in pub else '--'
    rows.append((dt, date_s[:29], title[:45], st, pub_flag, guid))
rows.sort(key=lambda r: (r[0] is not None, r[0] or datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)))

print('=== SORTED ===')
for dt, d, t, st, pf, g in rows:
    extra = ' <-- OVERDUE_UNPUBLISHED' if st == 'DUE??' and pf == '--' else (' <-- PUB' if pf=='PUB' else '')
    print('%-30s %-8s %-4s %s%s' % (d, st, pf, t, extra))

# last published
pubrows = [r for r in rows if r[4] == 'PUB']
if pubrows:
    last = max(pubrows, key=lambda r: r[0])
    print('LAST_PUB_DATE=' + last[1] + ' TITLE=' + last[2] + ' GUID=' + last[5])
overdue = [r for r in rows if r[3] == 'DUE??' and r[4] == '--']
print('OVERDUE_UNPUBLISHED_CNT=' + str(len(overdue)))
next_fut = [r for r in rows if r[3] == 'FUT']
if next_fut:
    nf = min(next_fut, key=lambda r: r[0])
    print('NEXT_FUT=' + nf[1] + ' TITLE=' + nf[2])
now_st = 'NOW in feed window?' if any(r[4]=='PUB' for r in rows) else 'no pub'
